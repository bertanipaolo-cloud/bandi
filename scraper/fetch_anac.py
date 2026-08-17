"""
Estrattore ANAC — Piattaforma di Pubblicita' a Valore Legale (PVL).

E' la fonte a valore legale: dal 2024 ogni bando, avviso ed esito italiano passa
di qui. A differenza del MePA copre anche il pezzo che ci interessa davvero, le
**indagini di mercato sotto soglia**: l'avviso con cui una stazione appaltante
cerca gli operatori da invitare a una procedura negoziata. E' il momento in cui
si entra in partita, prima che la gara esista.

L'endpoint (trovato l'11 agosto 2026 leggendo il traffico della ricerca avanzata):

    GET https://pubblicitalegale.anticorruzione.it/api/v0/avvisi-full-text-specializzata
        ?page=0&pageSize=100
        &dataPubblicazioneStart=GG/MM/AAAA&dataPubblicazioneEnd=GG/MM/AAAA
        &cpv=79340,79341,...            (3-8 cifre, piu' codici separati da virgola)
        &sortField=dataPubblicazione&sortDirection=desc
        &operatore=AND

GET semplice, nessuna autenticazione, nessun WAF: al contrario del MePA non
serve un browser. Risponde
    {"content":[...], "count": <totale>, "firstPaginationToken":..., ...}

Il filtro CPV lato server e' quello che rende sostenibile la scala nazionale:
sui prefissi dei quattro settori restano poche centinaia di pubblicazioni a
settimana invece di decine di migliaia.

Attenzione: nella risposta il campo `cpv` e' l'**etichetta** ("Servizi di
organizzazione di eventi"), non il codice numerico. Il codice lo conosciamo
solo come filtro inviato, quindi i record escono con `cpv_filtrato_a_monte`
e il cancello CPV locale li lascia passare (vedi classify.stato_cpv).

Uso:
    python3 scraper/fetch_anac.py --giorni 7
    python3 scraper/fetch_anac.py --da 01/08/2026 --a 11/08/2026
    python3 scraper/fetch_anac.py --giorni 30 --out data/anac_grezzi.json
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dictionaries import SETTORI  # noqa: E402

BASE = "https://pubblicitalegale.anticorruzione.it"
ENDPOINT = f"{BASE}/api/v0/avvisi-full-text-specializzata"

RADICE = Path(__file__).resolve().parent.parent
DEFAULT_OUT = RADICE / "data" / "anac_grezzi.json"

PAGE_SIZE = 100
# L'API accetta piu' CPV separati da virgola. Si spezza in gruppi per non
# costruire URL chilometrici e per isolare l'errore se un prefisso e' malformato.
CPV_PER_CHIAMATA = 12
PAUSA = 0.7          # cortesia verso il server fra una pagina e l'altra
TENTATIVI = 3

# ---------------------------------------------------------------------------
# Dalla "tipologia" ANAC al momento del ciclo di acquisto. E' la distinzione
# che conta: una manifestazione d'interesse si gioca, un esito si studia.
# ---------------------------------------------------------------------------
MOMENTI = {
    "INDAGINI_DI_MERCATO_SOTTO_SOGLIA": "manifestazione",
    "CONSULTAZIONI_PRELIMINARI_DI_MERCATO": "manifestazione",
    "AVVISI_DI_PREINFORMAZIONE": "preavviso",
    "BANDI": "gara",
    "RISULTATI": "esito",
    "MODIFICHE_CONTRATTUALI": "modifica",
    "AVVISI_DI_PROROGA": "modifica",
}

ETICHETTE_MOMENTO = {
    "manifestazione": "Manifestazione d'interesse",
    "preavviso": "Preavviso",
    "gara": "Gara aperta",
    "esito": "Esito",
    "modifica": "Modifica contrattuale",
    "altro": "Altro avviso",
}

# Su quale sezione del portale sta la scheda leggibile.
ROTTE = {"gara": "bandi", "esito": "esiti"}


def gruppi_cpv():
    """Prefissi CPV di tutti i settori, in gruppi da mandare all'API."""
    prefissi = sorted({p for s in SETTORI.values() for p in s.get("cpv_query", [])})
    return [prefissi[i:i + CPV_PER_CHIAMATA]
            for i in range(0, len(prefissi), CPV_PER_CHIAMATA)]


def _chiama(params):
    url = ENDPOINT + "?" + urllib.parse.urlencode(params, safe=",/")
    ultimo = None
    for tentativo in range(1, TENTATIVI + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (radar-appalti 4x4)",
                "Accept": "application/json",
                "Accept-Language": "it-IT,it;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            ultimo = e
            if tentativo < TENTATIVI:
                time.sleep(2 * tentativo)
    raise RuntimeError(f"ANAC non raggiungibile dopo {TENTATIVI} tentativi: {ultimo}\nURL: {url}")


# ---------------------------------------------------------------------------
# Normalizzazione: dalla struttura a template/sezioni al record piatto che il
# resto della pipeline (classify, run, dashboard) gia' conosce.
# ---------------------------------------------------------------------------

def _sezione(template, prefisso):
    for s in template.get("sections") or []:
        if str(s.get("name", "")).startswith(prefisso):
            return s
    return {}


def _data_iso(valore):
    """'2026-08-31T23:59:00.000+00:00' -> '2026-08-31'."""
    if not valore:
        return None
    testo = str(valore)
    try:
        return datetime.fromisoformat(testo.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return testo[:10] if len(testo) >= 10 else None


def _primo_non_vuoto(*valori):
    for v in valori:
        if v not in (None, "", []):
            return v
    return None


def normalizza_avviso(avviso):
    """Un avviso PVL -> record del radar. Ritorna None se la struttura non regge."""
    templates = avviso.get("templates") or []
    if not templates:
        return None
    template = templates[0].get("template") or {}
    metadata = template.get("metadata") or {}

    committente = _sezione(template, "SEZ. A").get("fields") or {}
    generali = _sezione(template, "SEZ. B").get("fields") or {}
    oggetto = _sezione(template, "SEZ. C")
    items = oggetto.get("items") or []
    primo = items[0] if items else {}

    soggetti = committente.get("soggetti_sa") or []
    ente = soggetti[0].get("denominazione_amministrazione") if soggetti else None
    cf_ente = soggetti[0].get("codice_fiscale") if soggetti else None

    tipologia = avviso.get("tipologia")
    momento = MOMENTI.get(tipologia, "altro")

    descrizione = _primo_non_vuoto(metadata.get("descrizione"), primo.get("descrizione")) or ""
    titolo = _primo_non_vuoto(metadata.get("titolo"), primo.get("descrizione"), descrizione) or "(senza titolo)"
    titolo = " ".join(str(titolo).split())
    if len(titolo) > 220:
        titolo = titolo[:217].rstrip() + "…"

    # Il valore: la stima a base d'asta su tutti i lotti; sugli esiti conta
    # invece quanto e' stato effettivamente aggiudicato.
    stimati = [i.get("valore_complessivo_stimato") for i in items
               if isinstance(i.get("valore_complessivo_stimato"), (int, float))]
    vinti = [i.get("valore_offerta_vincente") for i in items
             if isinstance(i.get("valore_offerta_vincente"), (int, float))]
    valore = sum(stimati) if stimati else None
    valore_aggiudicato = sum(vinti) if vinti else None

    aggiudicatari = []
    for i in items:
        for a in i.get("aggiudicatari") or []:
            for s in a.get("soggetti") or []:
                aggiudicatari.append({
                    "nome": s.get("denominazione"),
                    "codice_fiscale": s.get("codice_fiscale"),
                    "importo": a.get("importo"),
                })

    scadenza = _primo_non_vuoto(
        _data_iso(avviso.get("dataScadenza")),
        _data_iso(primo.get("termine_invito")),
        _data_iso(primo.get("termine_ricezione_offerte")),
    )

    etichette_cpv = [i.get("cpv") for i in items if i.get("cpv")]
    luoghi = [i.get("luogo_nuts") or i.get("luogo_istat") for i in items
              if i.get("luogo_nuts") or i.get("luogo_istat")]

    id_avviso = avviso.get("idAvviso")
    rotta = ROTTE.get(momento, "avvisi")

    return {
        "id": f"anac:{id_avviso}",
        "fonte": "ANAC",
        "numero": _primo_non_vuoto(*[i.get("cig") for i in items]),
        "titolo": titolo,
        "descrizione": " ".join(str(descrizione).split())[:1200],
        "ente": ente,
        "codice_fiscale_ente": cf_ente,
        "stazione_appaltante": ente,
        # Le etichette CPV di ANAC sono testo leggibile e discriminante: entrano
        # fra le "categorie" cosi' il punteggio le usa come faceva col MePA.
        "categorie": etichette_cpv,
        "cpv": [],
        "cpv_etichetta": etichette_cpv[0] if etichette_cpv else None,
        "cpv_filtrato_a_monte": True,
        "tipo": (primo.get("natura_principale") or "").lower() or None,
        "tipologia_anac": tipologia,
        "codice_scheda": avviso.get("codiceScheda"),
        "momento": momento,
        "momento_etichetta": ETICHETTE_MOMENTO.get(momento, "Altro avviso"),
        "valore": valore,
        "valore_aggiudicato": valore_aggiudicato,
        "aggiudicatari": aggiudicatari,
        "luogo": luoghi[0] if luoghi else None,
        "pubblicazione": _data_iso(avviso.get("dataPubblicazione")),
        "scadenza": scadenza,
        "url": f"{BASE}/{rotta}/{id_avviso}" if id_avviso else BASE,
        "link_gara": _primo_non_vuoto(primo.get("documenti_di_gara_link"),
                                      generali.get("documenti_di_gara_link")),
        "strumento": "PVL ANAC",
        "tag": [],
    }


def scarica(da, a, verbose=True):
    """Tutti gli avvisi nella finestra, per tutti i gruppi CPV, deduplicati."""
    per_id = {}
    gruppi = gruppi_cpv()
    for n, gruppo in enumerate(gruppi, 1):
        pagina = 0
        totale = None
        while True:
            params = {
                "page": pagina,
                "pageSize": PAGE_SIZE,
                "dataPubblicazioneStart": da,
                "dataPubblicazioneEnd": a,
                "cpv": ",".join(gruppo),
                "sortField": "dataPubblicazione",
                "sortDirection": "desc",
                "operatore": "AND",
            }
            risposta = _chiama(params)
            contenuto = risposta.get("content") or []
            if totale is None:
                totale = int(risposta.get("count") or 0)
                if verbose:
                    print(f"[anac] gruppo {n}/{len(gruppi)} "
                          f"({gruppo[0]}…{gruppo[-1]}): {totale} avvisi", file=sys.stderr)
            for avviso in contenuto:
                record = normalizza_avviso(avviso)
                if record:
                    per_id[record["id"]] = record
            pagina += 1
            if not contenuto or pagina * PAGE_SIZE >= totale or pagina > 60:
                break
            time.sleep(PAUSA)
    return list(per_id.values())


def finestra(giorni):
    fine = date.today()
    inizio = fine - timedelta(days=giorni)
    fmt = "%d/%m/%Y"
    return inizio.strftime(fmt), fine.strftime(fmt)


def main():
    ap = argparse.ArgumentParser(description="Estrae gli avvisi ANAC PVL sui CPV dei quattro settori.")
    ap.add_argument("--giorni", type=int, default=7,
                    help="finestra a ritroso da oggi (default 7)")
    ap.add_argument("--da", help="data inizio GG/MM/AAAA (ha la precedenza su --giorni)")
    ap.add_argument("--a", help="data fine GG/MM/AAAA")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    if args.da:
        da, a = args.da, (args.a or date.today().strftime("%d/%m/%Y"))
    else:
        da, a = finestra(args.giorni)

    print(f"[anac] finestra {da} → {a}", file=sys.stderr)
    record = scarica(da, a)

    conteggi = {}
    for r in record:
        conteggi[r["momento"]] = conteggi.get(r["momento"], 0) + 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    riepilogo = " · ".join(f"{ETICHETTE_MOMENTO.get(k, k)}: {v}"
                           for k, v in sorted(conteggi.items(), key=lambda x: -x[1]))
    print(f"[anac] {len(record)} avvisi → {out}", file=sys.stderr)
    print(f"[anac] {riepilogo}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
