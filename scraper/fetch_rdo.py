"""
Estrazione delle RDO aperte al mercato dalla vetrina pubblica del MePA.

La vetrina (vetrina_bandi.html?filter=RDO) e' un'applicazione AngularJS dietro un
WAF FortiWeb: la lista non e' nell'HTML, arriva da una chiamata XHR. L'endpoint,
individuato ispezionando il traffico reale del portale il 06/08/2026, e':

    POST /publicservices/vetrineservices/getAltriBandiRdoAperte

con un corpo JSON che dichiara lo strumento (RDO APERTE, id 15), la paginazione
e l'ordinamento; risponde {result:{exitCode:"200"}, payload:{elencoBandi:[...]}}.
Non richiede autenticazione, ma il WAF pretende una sessione browser valida:
per questo si carica prima la pagina con Playwright e poi si chiama il servizio
con page.request, che eredita cookie e impronta della sessione.

Tre livelli, dal piu' diretto al piu' difensivo:
  1. chiamata diretta all'endpoint noto, pagina per pagina;
  2. intercettazione della XHR che la pagina fa da sola, se l'endpoint e' cambiato
     (la richiesta scoperta viene salvata in data/endpoint.json);
  3. lettura dello scope Angular dal DOM.

Se tutti e tre falliscono salva HTML e screenshot in data/ per la diagnosi.

Campi che la vetrina espone davvero (verificati sul traffico reale): idBando,
numeroRdo, titoloBando, riassuntoBando (Beni/Servizi/Lavori), valore,
enteCommittente, descrizioneEnte, dataPubblicazione, dataScadenzaBando,
categorieMerceologiche. NON espone il CPV ne' una descrizione estesa:
il classificatore lavora quindi su titolo + categoria + natura.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

RADICE = Path(__file__).resolve().parent.parent
DATA = RADICE / "data"
DATA.mkdir(exist_ok=True)

BASE = "https://www.acquistinretepa.it"
VETRINA = os.environ.get(
    "MEPA_VETRINA_URL", f"{BASE}/opencms/opencms/vetrina_bandi.html?filter=RDO"
)
ENDPOINT = os.environ.get(
    "MEPA_ENDPOINT", f"{BASE}/publicservices/vetrineservices/getAltriBandiRdoAperte"
)
SCHEDA = f"{BASE}/opencms/opencms/scheda_altri_bandi.html?idBando={{id}}"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)

TIMEOUT = int(os.environ.get("MEPA_TIMEOUT_MS", "60000"))
MAX_PAGINE = int(os.environ.get("MEPA_MAX_PAGINE", "40"))
ITEM_PAGINA = int(os.environ.get("MEPA_ITEM_PAGINA", "200"))
HEADLESS = os.environ.get("MEPA_HEADFUL", "") != "1"


def log(*a):
    print("[mepa]", *a, flush=True)


def corpo_richiesta(pagina, item_pagina=ITEM_PAGINA):
    """Il payload che il portale invia davvero. Ogni campo serve: il servizio
    valida l'intera struttura e risponde 400 se ne manca uno."""
    return {
        "isArchive": False,
        "strumento": [{"label": "RDO APERTE", "totale": 18, "id": 15}],
        "stato": [],
        "categoria": [],
        "mostra": "",
        "idt": "",
        "dataPubblicazione": None,
        "tempo": {"dataDa": "", "dataA": ""},
        "paginazione": {"pagina": pagina, "itemPagina": item_pagina},
        "orderBy": {"campo": "dataPubblicazione", "verso": "desc"},
        "dataPubbDa": None,
        "dataPubbA": None,
        "dataScadenzaDa": None,
        "dataScadenzaA": None,
        "categoriaPort": [],
        "tipoContratto": [],
        "listTipoContratto": [],
    }


# ---------------------------------------------------------------------------
# Riconoscimento del payload
# ---------------------------------------------------------------------------

CHIAVI_ITEM = ("titoloBando", "dataScadenzaBando", "numeroRdo", "idBando")


def estrai_lista(obj, _prof=0):
    """Cerca ricorsivamente, dentro un JSON, la prima lista di bandi."""
    if _prof > 6:
        return None
    if isinstance(obj, list):
        if obj and isinstance(obj[0], dict) and any(k in obj[0] for k in CHIAVI_ITEM):
            return obj
        for el in obj[:5]:
            trovata = estrai_lista(el, _prof + 1)
            if trovata:
                return trovata
        return None
    if isinstance(obj, dict):
        for chiave in ("elencoBandi", "bandi", "results", "risultati", "content",
                       "items", "list", "data", "elenco", "payload"):
            if chiave in obj:
                trovata = estrai_lista(obj[chiave], _prof + 1)
                if trovata:
                    return trovata
        for v in obj.values():
            trovata = estrai_lista(v, _prof + 1)
            if trovata:
                return trovata
    return None


# ---------------------------------------------------------------------------
# Normalizzazione dei record
# ---------------------------------------------------------------------------

def _data_iso(v):
    """Le date arrivano come epoch ms, ISO o dd/MM/yyyy. Ritorna 'YYYY-MM-DD'."""
    if v in (None, "", 0):
        return None
    if isinstance(v, (int, float)) or (isinstance(v, str) and re.fullmatch(r"\d{10,13}", v)):
        n = int(v)
        if n > 10_000_000_000:  # millisecondi
            n //= 1000
        try:
            return datetime.fromtimestamp(n, tz=timezone.utc).date().isoformat()
        except (ValueError, OSError, OverflowError):
            return None
    s = str(v).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", s)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return None


def _valore(v):
    """'1.234,56' o '1234.56' o numero -> float. None se non interpretabile."""
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v))
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _categorie(item):
    out = []
    for chiave in ("categorieMerceologiche", "categoriaRDO", "categoria", "categoriaPortale"):
        val = item.get(chiave)
        if isinstance(val, list):
            for c in val:
                if isinstance(c, dict):
                    d = (c.get("descrizione") or c.get("descrizioneCategoriaIniziativa")
                         or c.get("nome") or c.get("label"))
                    if d:
                        out.append(str(d).strip())
                elif c:
                    out.append(str(c).strip())
        elif isinstance(val, str) and val.strip():
            out.append(val.strip())
    return sorted(set(out))


def _identificativo(item):
    for chiave in ("idBando", "id", "idIniziativa", "idRdo", "cdSigef", "codiceSigef"):
        v = item.get(chiave)
        if v not in (None, ""):
            return str(v)
    return None


def normalizza_item(item):
    idb = _identificativo(item)
    numero = (item.get("numeroRdo") or item.get("numeroBando")
              or item.get("numeroAvviso") or item.get("cdSigef"))
    cpv = []
    for chiave in ("cpv", "codiceCpv", "cpvPrincipale", "listaCpv"):
        v = item.get(chiave)
        if isinstance(v, list):
            cpv += [str(x.get("codice") if isinstance(x, dict) else x) for x in v]
        elif v:
            cpv.append(str(v))

    tag = []
    for chiave in ("tags", "labels", "etichette", "tag"):
        v = item.get(chiave)
        if isinstance(v, list):
            tag += [str(x.get("label") if isinstance(x, dict) else x) for x in v]

    return {
        "id": idb,
        "numero": str(numero) if numero else None,
        "titolo": (item.get("titoloBando") or item.get("titolo")
                   or item.get("titoloRDO") or "").strip(),
        "descrizione": (item.get("dsFornitura") or item.get("descrizioneBando")
                        or item.get("descrizione") or item.get("oggetto") or "").strip(),
        "ente": (item.get("descrizioneEnte") or item.get("enteCommittente") or "").strip(),
        "stazione_appaltante": (item.get("stazioneAppaltante") or "").strip(),
        "categorie": _categorie(item),
        "cpv": [c for c in cpv if c and c.lower() != "none"],
        "valore": _valore(item.get("valore") or item.get("importo")
                          or item.get("baseAsta") or item.get("valoreLotto")),
        "pubblicazione": _data_iso(item.get("dataPubblicazione") or item.get("dataInizio")),
        "scadenza": _data_iso(item.get("dataScadenzaBando") or item.get("dataScadenza")
                              or item.get("dataFine")),
        "strumento": (item.get("strumento") or "RDO").strip(),
        # riassuntoBando vale "Beni" / "Servizi" / "Lavori": e' l'unico
        # discriminante di natura che la vetrina espone.
        "tipo": (item.get("riassuntoBando") or "").strip(),
        "tag": [t for t in tag if t and t.lower() != "none"],
        "url": SCHEDA.format(id=idb) if idb else VETRINA,
    }


def _dedup(items):
    visti, out = set(), []
    for it in items:
        chiave = _identificativo(it) or json.dumps(it, sort_keys=True)[:200]
        if chiave in visti:
            continue
        visti.add(chiave)
        out.append(it)
    return out


# ---------------------------------------------------------------------------
# Raccolta
# ---------------------------------------------------------------------------

class Interceptor:
    """Livello 2: registra la XHR che la pagina fa da sola, se serve."""

    def __init__(self):
        self.payloads = []
        self.items = []

    def __call__(self, response):
        try:
            if "json" not in (response.headers or {}).get("content-type", "").lower():
                return
            corpo = response.json()
        except Exception:
            return
        lista = estrai_lista(corpo)
        if not lista:
            return
        req = response.request
        self.payloads.append({"url": response.url, "method": req.method,
                              "post_data": req.post_data, "n_items": len(lista)})
        self.items.extend(lista)


def _scarica_pagina(page, pagina):
    r = page.request.fetch(
        ENDPOINT, method="POST",
        data=json.dumps(corpo_richiesta(pagina)),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=TIMEOUT,
    )
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status}")
    corpo = r.json()
    esito = (corpo.get("result") or {}).get("exitCode")
    if esito and str(esito) not in ("200", "0"):
        raise RuntimeError(f"exitCode {esito}: {(corpo.get('result') or {}).get('text')}")
    return estrai_lista(corpo) or []


def raccogli():
    intercettore = Interceptor()
    diagnostica = {"quando": datetime.now(timezone.utc).isoformat(), "fasi": []}
    grezzi = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        ctx = browser.new_context(
            user_agent=UA, locale="it-IT", timezone_id="Europe/Rome",
            viewport={"width": 1440, "height": 900},
            extra_http_headers={"Accept-Language": "it-IT,it;q=0.9,en;q=0.6"},
        )
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = ctx.new_page()
        page.on("response", intercettore)

        log("apro la vetrina per ottenere la sessione...")
        page.goto(VETRINA, wait_until="domcontentloaded", timeout=TIMEOUT)
        try:
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
        except Exception:
            log("networkidle non raggiunto, proseguo")
        page.wait_for_timeout(2000)

        # --- livello 1: chiamata diretta all'endpoint noto ------------------
        try:
            for pagina in range(1, MAX_PAGINE + 1):
                lista = _scarica_pagina(page, pagina)
                if not lista:
                    break
                grezzi.extend(lista)
                log(f"pagina {pagina}: {len(lista)} bandi (totale {len(_dedup(grezzi))})")
                if len(lista) < ITEM_PAGINA:
                    break
                time.sleep(0.5)
            diagnostica["fasi"].append({"fase": "endpoint_diretto", "items": len(_dedup(grezzi))})
        except Exception as e:
            log(f"chiamata diretta fallita ({type(e).__name__}: {e})")
            diagnostica["fasi"].append({"fase": "endpoint_diretto", "errore": str(e)[:300]})

        # --- livello 2: quello che la pagina ha caricato da sola ------------
        if not grezzi and intercettore.items:
            log(f"uso la XHR intercettata: {len(intercettore.items)} bandi")
            grezzi = list(intercettore.items)
            if intercettore.payloads:
                (DATA / "endpoint.json").write_text(
                    json.dumps(max(intercettore.payloads, key=lambda x: x["n_items"]),
                               indent=2, ensure_ascii=False), encoding="utf-8")
            diagnostica["fasi"].append({"fase": "xhr_intercettata", "items": len(grezzi)})

        # --- livello 3: scope Angular --------------------------------------
        if not grezzi:
            log("provo a leggere lo scope Angular")
            try:
                dati = page.evaluate(
                    """() => {
                        if (!window.angular) return null;
                        for (const n of document.querySelectorAll('[ng-controller],body,div')) {
                            let s; try { s = angular.element(n).scope(); } catch (e) { continue; }
                            for (const c of [s, s && s.model]) {
                                if (c && Array.isArray(c.elencoBandi) && c.elencoBandi.length)
                                    return c.elencoBandi;
                            }
                        }
                        return null;
                    }"""
                )
                if dati:
                    grezzi = dati
                    log(f"scope Angular: {len(dati)} bandi")
            except Exception as e:
                log(f"lettura scope fallita: {e}")
            diagnostica["fasi"].append({"fase": "scope_angular", "items": len(grezzi)})

        if not grezzi:
            (DATA / "pagina_fallita.html").write_text(page.content(), encoding="utf-8")
            page.screenshot(path=str(DATA / "pagina_fallita.png"), full_page=True)
            log("ATTENZIONE: nessun dato estratto. Salvati HTML e screenshot in data/")

        ctx.close()
        browser.close()

    normalizzati = [normalizza_item(i) for i in _dedup(grezzi)]
    normalizzati = [r for r in normalizzati if r["titolo"]]
    diagnostica["totale_normalizzati"] = len(normalizzati)
    (DATA / "diagnostica.json").write_text(
        json.dumps(diagnostica, indent=2, ensure_ascii=False), encoding="utf-8")
    return normalizzati


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    records = raccogli()
    out = DATA / "rdo_grezze.json"
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"scritti {len(records)} bandi in {out}")
    if not records:
        sys.exit(2)
