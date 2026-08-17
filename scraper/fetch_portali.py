"""
Estrattore per la rete dei "Portale Appalti" (Maggioli / DigitalPA).

Centinaia di enti italiani usano lo stesso software, con gli stessi indirizzi:

    https://<dominio-ente>/PortaleAppalti/it/ppgare_avvisi_lista.wp   avvisi
    https://<dominio-ente>/PortaleAppalti/it/ppgare_bandi_lista.wp    bandi

Le pagine sono **HTML servito dal server**: niente Angular, niente WAF, niente
Playwright. Ogni record e' una sequenza di coppie etichetta/valore
("Stazione appaltante :", "Tipologia :", "Titolo :", …) uguali su tutte le
installazioni anche quando cambia il tema grafico. Per questo il parser lavora
sul **testo**, non sui selettori CSS: e' l'unica cosa che regge la varieta' dei
temi.

## Perche' serve, se c'e' gia' ANAC

ANAC copre tutto cio' che ha un CIG e passa dalla pubblicita' legale. Il portale
dell'ente pubblica anche quello che li' non arriva, ed e' proprio la parte che
ci interessa:

  - gli **avvisi di richiesta preventivi** che precedono un affidamento diretto
    ("avviso rivolto all'acquisizione di preventivi al fine di procedere ad
    affidamento diretto"): il pre-affidamento vero e proprio;
  - gli **elenchi/albi di operatori qualificati** sempre aperti, con scadenze a
    due o tre anni. Non sono gare: sono la lista da cui l'ente pesca quando
    affida per chiamata. Iscriversi e' il vero lavoro di acquisizione.

## Come si popola la lista dei portali

Non a mano. Ogni record ANAC porta `documenti_di_gara_link`, che punta al
portale della stazione appaltante. Girando i link degli avvisi che rientrano
nei nostri CPV si ottiene, gratis, l'elenco degli enti che **comprano davvero**
i nostri servizi: la watchlist si costruisce da se' e si aggiorna a ogni run.

Uso:
    python3 scraper/fetch_portali.py --scopri          # aggiorna data/portali.json da ANAC
    python3 scraper/fetch_portali.py                   # scarica gli avvisi dai portali noti
    python3 scraper/fetch_portali.py --max-portali 40
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
DATA = RADICE / "data"
REGISTRO = DATA / "portali.json"
GREZZI_ANAC = DATA / "anac_grezzi.json"
DEFAULT_OUT = DATA / "portali_grezzi.json"

PERCORSO_AVVISI = "it/ppgare_avvisi_lista.wp"
MARCATORE = "/PortaleAppalti/"

PAUSA = 1.0
TENTATIVI = 2
TIMEOUT = 45

# Etichette del form-record, nell'ordine in cui il portale le stampa.
ETICHETTE = {
    "stazione appaltante": "ente",
    "tipologia": "tipologia",
    "titolo": "titolo",
    "avviso per": "natura",
    "data pubblicazione": "pubblicazione",
    "data scadenza": "scadenza",
    "riferimento procedura": "riferimento",
    "stato": "stato",
}

# Tipologia dichiarata dal portale -> momento del ciclo di acquisto.
MOMENTI = {
    "manifestazione di interesse": "manifestazione",
    "indagine di mercato": "manifestazione",
    "avviso esplorativo": "manifestazione",
    "avviso di preinformazione": "preavviso",
    "avviso di gara": "gara",
    "bando di gara": "gara",
}

# Un avviso di sola "acquisizione preventivi" non dichiara la tipologia giusta:
# il portale lo marca "Altro". Si riconosce dal titolo.
SPIE_MANIFESTAZIONE = [
    "manifestazione di interesse", "manifestazioni di interesse",
    "indagine di mercato", "indagine esplorativa", "avviso esplorativo",
    "procedura esplorativa", "raccolta di proposte",
    "acquisizione di preventivi", "richiesta di preventivi",
    "individuazione di operatori", "selezione di operatori",
    "formazione di un elenco", "elenco di operatori", "albo fornitori",
    "elenco di soggetti qualificati", "operatori economici da invitare",
]


SEPARATORE = "\x00"


def _testo(html):
    """
    HTML -> una riga per elemento, senza dipendenze esterne.

    I tag diventano un separatore esplicito; gli a-capo del sorgente **dentro**
    un elemento no. Serve: nel markup del portale un titolo lungo e' spezzato su
    piu' righe dentro la stessa cella, e va ricomposto in una riga sola.
    """
    html = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", SEPARATORE, html)
    html = re.sub(r"<[^>]+>", SEPARATORE, html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&quot;", '"'),
                 ("&lt;", "<"), ("&gt;", ">"), ("&#39;", "'"), ("&apos;", "'")):
        html = html.replace(a, b)
    righe = [" ".join(pezzo.split()) for pezzo in html.split(SEPARATORE)]
    return [r for r in righe if r]


def _data_iso(valore):
    """'19/06/2026' -> '2026-06-19'."""
    if not valore:
        return None
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", valore)
    if not m:
        return None
    g, mm, a = m.groups()
    try:
        return date(int(a), int(mm), int(g)).isoformat()
    except ValueError:
        return None


def _momento(tipologia, titolo):
    t = (tipologia or "").strip().lower()
    for chiave, valore in MOMENTI.items():
        if chiave in t:
            return valore
    testo = (titolo or "").lower()
    if any(s in testo for s in SPIE_MANIFESTAZIONE):
        return "manifestazione"
    return "gara"


def analizza(html, base_url, ente_ripiego=None):
    """
    Estrae i record dalla pagina degli avvisi.

    Lavora sul testo perche' le etichette sono l'unica cosa stabile fra
    installazioni con temi diversi. Un record inizia a "Stazione appaltante :"
    e finisce alla successiva o a "Visualizza scheda".
    """
    righe = _testo(html)
    record = []
    corrente = None

    def chiudi():
        nonlocal corrente
        if corrente and corrente.get("titolo"):
            record.append(corrente)
        corrente = None

    i = 0
    while i < len(righe):
        riga = righe[i]
        etichetta = riga.rstrip(":").strip().lower()
        if etichetta in ETICHETTE:
            campo = ETICHETTE[etichetta]
            if campo == "ente":
                chiudi()
                corrente = {}
            valore = righe[i + 1].strip() if i + 1 < len(righe) else ""
            # Se dopo l'etichetta c'e' un'altra etichetta, il campo e' vuoto.
            if valore.rstrip(":").strip().lower() in ETICHETTE:
                valore = ""
            if corrente is not None:
                corrente.setdefault(campo, valore)
            i += 2
            continue
        i += 1
    chiudi()

    fuori = []
    for r in record:
        titolo = " ".join((r.get("titolo") or "").split())
        if not titolo:
            continue
        if (r.get("stato") or "").strip().lower().startswith("scadut"):
            continue
        scadenza = _data_iso(r.get("scadenza"))
        momento = _momento(r.get("tipologia"), titolo)
        riferimento = (r.get("riferimento") or "").strip()
        ente = " ".join((r.get("ente") or ente_ripiego or "").split())
        fuori.append({
            "id": f"portale:{urllib.parse.urlparse(base_url).netloc}:{riferimento or titolo[:60]}",
            "fonte": "Portale Appalti",
            "numero": riferimento or None,
            "titolo": titolo[:220],
            "descrizione": titolo,
            "ente": ente or None,
            "stazione_appaltante": ente or None,
            "categorie": [c for c in [(r.get("tipologia") or "").strip()] if c],
            "cpv": [],
            "tipo": (r.get("natura") or "").strip().lower() or None,
            "momento": momento,
            "momento_etichetta": {
                "manifestazione": "Manifestazione d'interesse",
                "preavviso": "Preavviso",
                "gara": "Gara aperta",
            }.get(momento, "Avviso"),
            "valore": None,
            "pubblicazione": _data_iso(r.get("pubblicazione")),
            "scadenza": scadenza,
            "url": urllib.parse.urljoin(base_url, PERCORSO_AVVISI),
            "link_gara": urllib.parse.urljoin(base_url, PERCORSO_AVVISI),
            "strumento": "Portale Appalti",
            "tag": [],
        })
    return fuori


# ---------------------------------------------------------------------------
# Registro dei portali, ricavato dai link di gara che ANAC gia' ci da'.
# ---------------------------------------------------------------------------

def scopri_portali(percorso_anac=GREZZI_ANAC):
    p = Path(percorso_anac)
    if not p.exists():
        print(f"[portali] manca {p}: eseguire prima scraper/fetch_anac.py", file=sys.stderr)
        return {}
    trovati = {}
    for r in json.loads(p.read_text(encoding="utf-8")):
        link = r.get("link_gara") or ""
        if MARCATORE not in link:
            continue
        pezzo = link.split(MARCATORE)[0]
        base = f"{pezzo}{MARCATORE}"
        trovati.setdefault(base, {"base": base, "enti": set()})
        if r.get("ente"):
            trovati[base]["enti"].add(r["ente"])
    return {b: {"base": b, "enti": sorted(v["enti"])} for b, v in trovati.items()}


def carica_registro():
    if REGISTRO.exists():
        try:
            return json.loads(REGISTRO.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"portali": [], "aggiornato": None}


def salva_registro(registro):
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")


def aggiorna_registro():
    registro = carica_registro()
    noti = {p["base"]: p for p in registro.get("portali", [])}
    for base, info in scopri_portali().items():
        voce = noti.setdefault(base, {"base": base, "enti": [], "visto": None})
        voce["enti"] = sorted(set(voce.get("enti", [])) | set(info["enti"]))
    registro["portali"] = sorted(noti.values(), key=lambda p: p["base"])
    registro["aggiornato"] = datetime.now().date().isoformat()
    salva_registro(registro)
    return registro


def _scarica(url):
    for tentativo in range(1, TENTATIVI + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (radar-appalti 4x4)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "it-IT,it;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as e:
            if tentativo == TENTATIVI:
                raise
            time.sleep(2)
    return ""


def main():
    ap = argparse.ArgumentParser(
        description="Scarica gli avvisi dalla rete dei Portale Appalti.")
    ap.add_argument("--scopri", action="store_true",
                    help="aggiorna il registro dei portali dai link di gara ANAC")
    ap.add_argument("--max-portali", type=int, default=60,
                    help="quanti portali interrogare in un run (default 60)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    registro = aggiorna_registro() if args.scopri else carica_registro()
    portali = registro.get("portali", [])
    if args.scopri:
        print(f"[portali] registro: {len(portali)} portali noti", file=sys.stderr)

    if not portali:
        print("[portali] nessun portale nel registro: lanciare prima --scopri "
              "dopo un'estrazione ANAC", file=sys.stderr)
        Path(args.out).write_text("[]", encoding="utf-8")
        return 0

    record = []
    falliti = []
    for voce in portali[:args.max_portali]:
        base = voce["base"]
        url = urllib.parse.urljoin(base, PERCORSO_AVVISI)
        try:
            html = _scarica(url)
        except Exception as e:  # noqa: BLE001 - un portale giu' non ferma il run
            falliti.append((base, f"{type(e).__name__}: {e}"))
            continue
        trovati = analizza(html, base, ente_ripiego=(voce.get("enti") or [None])[0])
        record.extend(trovati)
        voce["visto"] = datetime.now().date().isoformat()
        voce["ultimi_avvisi"] = len(trovati)
        time.sleep(PAUSA)

    salva_registro(registro)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    manifestazioni = sum(1 for r in record if r["momento"] == "manifestazione")
    print(f"[portali] {len(record)} avvisi da {min(len(portali), args.max_portali)} portali "
          f"({manifestazioni} manifestazioni d'interesse) → {out}", file=sys.stderr)
    if falliti:
        print(f"[portali] {len(falliti)} portali non raggiunti:", file=sys.stderr)
        for base, errore in falliti[:5]:
            print(f"          {base} — {errore}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
