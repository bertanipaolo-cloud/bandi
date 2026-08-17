"""
Orchestratore della pipeline: grezzi -> classificati -> dashboard + digest.

  python3 scraper/run.py            # usa data/rdo_grezze.json
  python3 scraper/run.py --demo     # genera un set dimostrativo per vedere la dashboard

Produce:
  docs/index.html      dashboard self-contained (pubblicata da GitHub Pages)
  docs/data.json       stessi dati in formato macchina, per l'hub 4x4
  data/storico.json    memoria dei bandi gia' visti (serve a marcare le novita')
  data/digest.html     corpo dell'email settimanale
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROMA = ZoneInfo("Europe/Rome")

sys.path.insert(0, str(Path(__file__).parent))

from classify import filtra, SOGLIA_MINIMA  # noqa: E402
from dictionaries import SETTORI, SOCIETA  # noqa: E402
from dashboard import scrivi_dashboard  # noqa: E402
from digest import scrivi_digest  # noqa: E402

RADICE = Path(__file__).resolve().parent.parent
DATA = RADICE / "data"
DOCS = RADICE / "docs"
DOCS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

# Diverse stazioni appaltanti compilano il campo "valore" con un prezzo
# unitario invece che con la base d'asta: si trovano RDO da 0,69 o 6,44 euro.
# Sotto questa soglia l'importo si mostra ma non entra nei totali.
IMPORTO_MINIMO_ATTENDIBILE = 1000

STORICO = DATA / "storico.json"
GREZZE = DATA / "rdo_grezze.json"
GREZZI_ANAC = DATA / "anac_grezzi.json"
GREZZI_PORTALI = DATA / "portali_grezzi.json"

# Gli esiti non sono opportunita': non si partecipa a una gara gia' aggiudicata.
# Servono all'altra meta' del lavoro — capire chi compra cosa, da chi e a quanto,
# per bussare prima che il contratto in corso scada. Vanno tenuti separati.
MOMENTI_OPPORTUNITA = {"manifestazione", "preavviso", "gara", None}


MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def adesso():
    """Ora di Roma: il container gira in UTC, le scadenze sono italiane."""
    return datetime.now(ROMA)


def oggi():
    return adesso().date()


def quando_leggibile(dt):
    return f"{dt.day} {MESI[dt.month - 1]} {dt.year}, ore {dt:%H:%M}"


def carica_storico():
    if STORICO.exists():
        try:
            return json.loads(STORICO.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"visti": {}, "run": []}


def giorni_a(scadenza):
    if not scadenza:
        return None
    try:
        d = date.fromisoformat(scadenza)
    except ValueError:
        return None
    return (d - oggi()).days


def carica_sorgenti(percorsi):
    """
    Unisce i record grezzi delle fonti disponibili.

    Ogni fonte porta il suo campo `fonte` e, se ce l'ha, il suo `momento`.
    Il MePA espone solo RDO gia' aperte al mercato: sono gare, per definizione.
    """
    records = []
    presenti = []
    for p in percorsi:
        p = Path(p)
        if not p.exists():
            continue
        try:
            dati = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            print(f"[run] {p.name} illeggibile: {e}", file=sys.stderr)
            continue
        for r in dati:
            r.setdefault("fonte", "MePA")
            r.setdefault("momento", "gara")
            r.setdefault("momento_etichetta", "Gara aperta")
        records.extend(dati)
        presenti.append(f"{p.name}: {len(dati)}")
    if presenti:
        print(f"[run] sorgenti — {' · '.join(presenti)}", file=sys.stderr)
    return records


def elabora(records, storico):
    classificati_tenuti, tutti = filtra(records)

    # Gli esiti escono subito dal flusso delle opportunita'.
    esiti = [r for r in classificati_tenuti if r.get("momento") == "esito"]
    tenuti = [r for r in classificati_tenuti if r.get("momento") in MOMENTI_OPPORTUNITA]

    visti = storico.get("visti", {})
    oggi_iso = oggi().isoformat()

    for r in esiti:
        r["chiave"] = r.get("id") or r.get("titolo", "")[:80]
        r["nuovo"] = r["chiave"] not in visti

    for r in tenuti:
        chiave = r.get("id") or r.get("numero") or r.get("titolo")[:80]
        r["chiave"] = chiave
        primo = visti.get(chiave, {}).get("primo_avvistamento")
        r["nuovo"] = primo is None
        r["primo_avvistamento"] = primo or oggi_iso
        r["giorni_alla_scadenza"] = giorni_a(r.get("scadenza"))
        r["valore_sospetto"] = (r.get("valore") is not None
                                and r["valore"] < IMPORTO_MINIMO_ATTENDIBILE)
        r["scaduto"] = (r["giorni_alla_scadenza"] is not None
                        and r["giorni_alla_scadenza"] < 0)
        visti[chiave] = {
            "primo_avvistamento": r["primo_avvistamento"],
            "ultimo_avvistamento": oggi_iso,
            "titolo": r["titolo"][:160],
            "settore": r["settore"],
            "punteggio": r["punteggio"],
            "scadenza": r.get("scadenza"),
        }

    attivi = [r for r in tenuti if not r["scaduto"]]
    attivi.sort(key=lambda r: (
        0 if r["nuovo"] else 1,
        -(r["punteggio"]),
        r.get("giorni_alla_scadenza") if r.get("giorni_alla_scadenza") is not None else 999,
    ))

    for r in esiti:
        visti.setdefault(r["chiave"], {
            "primo_avvistamento": oggi_iso,
            "titolo": r["titolo"][:160],
            "settore": r["settore"],
            "punteggio": r["punteggio"],
        })["ultimo_avvistamento"] = oggi_iso
    esiti.sort(key=lambda r: (0 if r["nuovo"] else 1,
                              -(r.get("valore_aggiudicato") or r.get("valore") or 0)))

    storico["visti"] = visti
    storico.setdefault("run", []).append({
        "quando": datetime.now(timezone.utc).isoformat(),
        "esaminati": len(records),
        "pertinenti": len(tenuti),
        "attivi": len(attivi),
        "nuovi": sum(1 for r in attivi if r["nuovo"]),
        "esiti": len(esiti),
    })
    storico["run"] = storico["run"][-52:]  # un anno di run settimanali
    return attivi, tenuti, tutti, esiti


def statistiche(attivi, esaminati, esiti=()):
    per_societa = {}
    for chiave, s in SOCIETA.items():
        sel = [r for r in attivi if r.get("societa") == chiave]
        valori = [r["valore"] for r in sel
                  if r.get("valore") and not r.get("valore_sospetto")]
        per_societa[chiave] = {
            "etichetta": s["etichetta"],
            "descrizione": s["descrizione"],
            "colore": s["colore"],
            "totale": len(sel),
            "nuovi": sum(1 for r in sel if r["nuovo"]),
            "manifestazioni": sum(1 for r in sel if r.get("momento") == "manifestazione"),
            "valore_totale": round(sum(valori), 2) if valori else 0,
        }

    per_momento = {}
    for r in attivi:
        m = r.get("momento") or "gara"
        voce = per_momento.setdefault(m, {"totale": 0, "nuovi": 0,
                                          "etichetta": r.get("momento_etichetta") or "Gara aperta"})
        voce["totale"] += 1
        voce["nuovi"] += 1 if r["nuovo"] else 0

    per_fonte = {}
    for r in attivi:
        per_fonte[r.get("fonte", "MePA")] = per_fonte.get(r.get("fonte", "MePA"), 0) + 1

    per_settore = {}
    for chiave, s in SETTORI.items():
        sel = [r for r in attivi if r["settore"] == chiave]
        valori = [r["valore"] for r in sel
                  if r.get("valore") and not r.get("valore_sospetto")]
        per_settore[chiave] = {
            "etichetta": s["etichetta"],
            "colore": s["colore"],
            "totale": len(sel),
            "nuovi": sum(1 for r in sel if r["nuovo"]),
            "valore_totale": round(sum(valori), 2) if valori else 0,
        }
    valori_tutti = [r["valore"] for r in attivi
                    if r.get("valore") and not r.get("valore_sospetto")]
    return {
        "aggiornato": adesso().isoformat(timespec="minutes"),
        "aggiornato_testo": quando_leggibile(adesso()),
        "esaminati": esaminati,
        "attivi": len(attivi),
        "nuovi": sum(1 for r in attivi if r["nuovo"]),
        "in_scadenza_7gg": sum(
            1 for r in attivi
            if r.get("giorni_alla_scadenza") is not None and 0 <= r["giorni_alla_scadenza"] <= 7
        ),
        "valore_totale": round(sum(valori_tutti), 2) if valori_tutti else 0,
        "valore_mediano": round(sorted(valori_tutti)[len(valori_tutti) // 2], 2) if valori_tutti else 0,
        "con_importo": len(valori_tutti),
        "importi_sospetti": sum(1 for r in attivi if r.get("valore_sospetto")),
        "manifestazioni": sum(1 for r in attivi if r.get("momento") == "manifestazione"),
        "per_settore": per_settore,
        "settore_societa": {k: s["societa"] for k, s in SETTORI.items()},
        "per_societa": per_societa,
        "per_momento": per_momento,
        "per_fonte": per_fonte,
        "esiti": len(esiti),
        "soglia": SOGLIA_MINIMA,
    }


def demo():
    """Set dimostrativo: serve solo a validare la dashboard prima del primo run reale."""
    base = oggi()
    def d(n):
        return (base + timedelta(days=n)).isoformat()
    return [
        {"id": "demo1", "numero": "4512336", "titolo": "Servizio di supporto specialistico al RUP per l'attuazione degli interventi PNRR - Missione 5",
         "descrizione": "Affidamento di servizi di assistenza tecnica specialistica per il monitoraggio, la rendicontazione e la valutazione degli interventi finanziati dal PNRR.",
         "ente": "Comune di Frosinone", "stazione_appaltante": "Settore Programmazione",
         "categorie": ["Servizi professionali - Supporto specialistico"], "cpv": ["79411000-8"],
         "valore": 78000.0, "pubblicazione": d(-4), "scadenza": d(11), "strumento": "RDO", "tag": [],
         "url": "https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO"},
        {"id": "demo2", "numero": "4509871", "titolo": "Organizzazione e gestione integrata degli eventi istituzionali - anno 2026/2027",
         "descrizione": "Segreteria organizzativa, allestimenti, service audio video e accoglienza per il calendario degli eventi istituzionali.",
         "ente": "Regione Lazio", "stazione_appaltante": "Direzione Cultura",
         "categorie": ["Servizi di organizzazione eventi"], "cpv": ["79952000-2"],
         "valore": 145000.0, "pubblicazione": d(-2), "scadenza": d(19), "strumento": "RDO", "tag": [],
         "url": "https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO"},
        {"id": "demo3", "numero": "4501220", "titolo": "Servizio di catering e coffee break per convegni e cerimonie istituzionali",
         "descrizione": "Fornitura di coffee break, light lunch e buffet in occasione di convegni, cerimonie e incontri istituzionali.",
         "ente": "Università degli Studi di Roma", "stazione_appaltante": "Area Servizi Generali",
         "categorie": ["Ristorazione - Servizi di catering"], "cpv": ["55520000-1"],
         "valore": 42000.0, "pubblicazione": d(-9), "scadenza": d(5), "strumento": "RDO", "tag": [],
         "url": "https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO"},
        {"id": "demo4", "numero": "4498005", "titolo": "Consulenza direzionale per la riorganizzazione dei processi e il controllo di gestione",
         "descrizione": "Analisi organizzativa, mappatura dei processi e impianto del sistema di controllo di gestione.",
         "ente": "Azienda Speciale Servizi", "stazione_appaltante": "Direzione Generale",
         "categorie": ["Servizi professionali"], "cpv": ["79410000-1"],
         "valore": 39500.0, "pubblicazione": d(-14), "scadenza": d(3), "strumento": "RDO", "tag": [],
         "url": "https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO"},
        {"id": "demo5", "numero": "4487731", "titolo": "Percorso di formazione manageriale e team building per il personale dirigente",
         "descrizione": "Progettazione ed erogazione di un percorso formativo con moduli d'aula, coaching e attività di team building.",
         "ente": "ASL Roma 2", "stazione_appaltante": "UOC Formazione",
         "categorie": ["Servizi di formazione"], "cpv": ["80532000-2"],
         "valore": 24000.0, "pubblicazione": d(-21), "scadenza": d(26), "strumento": "RDO", "tag": [],
         "url": "https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO"},
        {"id": "demo6", "numero": "4486110", "titolo": "Allestimento stand e servizi di segreteria per la partecipazione alla fiera del turismo",
         "descrizione": "Progettazione e allestimento dello stand, hostess, materiali promozionali e logistica.",
         "ente": "Camera di Commercio", "stazione_appaltante": "Servizio Promozione",
         "categorie": ["Servizi di organizzazione eventi", "Allestimenti"], "cpv": ["79956000-0"],
         "valore": 61000.0, "pubblicazione": d(-6), "scadenza": d(8), "strumento": "RDO", "tag": [],
         "url": "https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO"},
        {"id": "demo7", "numero": "4479442", "titolo": "Servizio di banqueting per la cena di gala del congresso nazionale",
         "descrizione": "Servizio completo di banqueting per 300 coperti, personale di sala e allestimento tavoli.",
         "ente": "Ente Fiera", "stazione_appaltante": "Ufficio Eventi",
         "categorie": ["Ristorazione"], "cpv": ["55520000-1"],
         "valore": 18500.0, "pubblicazione": d(-30), "scadenza": d(2), "strumento": "RDO", "tag": [],
         "url": "https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO"},
        # ANAC: il pezzo nuovo. Manifestazioni d'interesse ed esiti, con Joule.
        {"id": "anac:demo9", "numero": "BCAF44A14B", "fonte": "ANAC",
         "momento": "manifestazione", "momento_etichetta": "Manifestazione d'interesse",
         "titolo": "Indagine esplorativa di mercato per l'affidamento dei servizi integrati di comunicazione, disseminazione e organizzazione di eventi",
         "descrizione": "Individuazione di 5 operatori economici da invitare alla successiva procedura negoziata: ideazione, produzione e diffusione di materiali informativi e multimediali.",
         "ente": "Regione Basilicata", "stazione_appaltante": "Dipartimento Protezione Civile",
         "categorie": ["Servizi di organizzazione di eventi"], "cpv": [], "cpv_filtrato_a_monte": True,
         "cpv_etichetta": "Servizi di organizzazione di eventi", "luogo": "Matera",
         "valore": 210438.52, "pubblicazione": d(-1), "scadenza": d(20), "strumento": "PVL ANAC", "tag": [],
         "link_gara": "https://www.sua-rb.it/PortaleAppalti/it/procedure",
         "url": "https://pubblicitalegale.anticorruzione.it/avvisi/84976105-7f36-4413-b64b-89d98b9514de"},
        {"id": "anac:demo10", "numero": "B7712004C1", "fonte": "ANAC",
         "momento": "manifestazione", "momento_etichetta": "Manifestazione d'interesse",
         "titolo": "Avviso pubblico di manifestazione di interesse per il servizio di ufficio stampa, media relations e gestione dei canali social",
         "descrizione": "Affidamento triennale dei servizi di ufficio stampa, produzione di contenuti e piano editoriale dei canali social dell'Ente.",
         "ente": "Comune di Viterbo", "stazione_appaltante": "Servizio Comunicazione",
         "categorie": ["Servizi di pubbliche relazioni"], "cpv": [], "cpv_filtrato_a_monte": True,
         "cpv_etichetta": "Servizi di pubbliche relazioni", "luogo": "Viterbo",
         "valore": 118000.0, "pubblicazione": d(-3), "scadenza": d(9), "strumento": "PVL ANAC", "tag": [],
         "url": "https://pubblicitalegale.anticorruzione.it/avvisi/demo10"},
        {"id": "anac:demo11", "numero": "B4491200AA", "fonte": "ANAC",
         "momento": "gara", "momento_etichetta": "Gara aperta",
         "titolo": "Procedura aperta per l'affidamento della campagna di comunicazione istituzionale e della progettazione grafica dell'immagine coordinata",
         "descrizione": "Ideazione creativa, produzione video, piano media e immagine coordinata per il triennio 2026-2029.",
         "ente": "Camera di Commercio di Roma", "stazione_appaltante": "Area Promozione",
         "categorie": ["Servizi di pubblicità e marketing"], "cpv": [], "cpv_filtrato_a_monte": True,
         "cpv_etichetta": "Servizi di pubblicità e marketing", "luogo": "Roma",
         "valore": 190000.0, "pubblicazione": d(-5), "scadenza": d(24), "strumento": "PVL ANAC", "tag": [],
         "url": "https://pubblicitalegale.anticorruzione.it/bandi/demo11"},
        {"id": "anac:demo12", "numero": "B48F36B2EA", "fonte": "ANAC",
         "momento": "esito", "momento_etichetta": "Esito",
         "titolo": "Piano di indagini annuale di customer satisfaction 2025-2027 per i servizi di mobilità",
         "descrizione": "Progettazione e realizzazione del piano di rilevazione della qualità attesa e percepita.",
         "ente": "Roma Servizi per la Mobilità S.r.l.", "stazione_appaltante": "Roma Servizi per la Mobilità S.r.l.",
         "categorie": ["Servizi di inchiesta relativi alla soddisfazione della clientela"],
         "cpv": [], "cpv_filtrato_a_monte": True, "luogo": "Roma",
         "cpv_etichetta": "Servizi di inchiesta relativi alla soddisfazione della clientela",
         "valore": 270000.0, "valore_aggiudicato": 182614.5,
         "aggiudicatari": [{"nome": "Centro Statistica Aziendale S.r.l.",
                            "codice_fiscale": "05196740483", "importo": 182614.5}],
         "pubblicazione": d(-2), "scadenza": None, "strumento": "PVL ANAC", "tag": [],
         "url": "https://pubblicitalegale.anticorruzione.it/esiti/demo12"},
        {"id": "demo8", "numero": "4472018", "titolo": "Indagine di customer satisfaction e analisi dei processi di front office",
         "descrizione": "Disegno del questionario, somministrazione, elaborazione e restituzione dei risultati.",
         "ente": "Comune di Latina", "stazione_appaltante": "Servizio Qualità",
         "categorie": ["Ricerche di mercato"], "cpv": ["79310000-0"],
         "valore": 15000.0, "pubblicazione": d(-11), "scadenza": d(14), "strumento": "RDO", "tag": [],
         "url": "https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO"},
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true",
                    help="usa dati dimostrativi invece di data/rdo_grezze.json")
    ap.add_argument("--input", default=str(GREZZE), help="grezzi MePA")
    ap.add_argument("--input-anac", default=str(GREZZI_ANAC), help="grezzi ANAC PVL")
    ap.add_argument("--input-portali", default=str(GREZZI_PORTALI),
                    help="grezzi dei Portale Appalti degli enti")
    args = ap.parse_args()

    if args.demo:
        records = demo()
        modalita = "demo"
    else:
        percorsi = [args.input, args.input_anac, args.input_portali]
        records = carica_sorgenti(percorsi)
        if not records:
            print(f"[run] nessuna sorgente in {percorsi}: eseguire prima "
                  f"scraper/fetch_rdo.py e/o scraper/fetch_anac.py", file=sys.stderr)
            return 2
        modalita = "reale"

    storico = carica_storico() if modalita == "reale" else {"visti": {}, "run": []}
    attivi, tenuti, tutti, esiti = elabora(records, storico)
    stat = statistiche(attivi, len(records), esiti)
    stat["modalita"] = modalita

    payload = {"meta": stat, "opportunita": attivi, "esiti": esiti}
    (DOCS / "data.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if modalita == "reale":
        STORICO.write_text(json.dumps(storico, indent=2, ensure_ascii=False), encoding="utf-8")

    scrivi_dashboard(payload, DOCS / "index.html")
    scrivi_digest(payload, DATA / "digest.html")

    riepilogo_societa = " · ".join(
        f"{v['etichetta']} {v['totale']}" for v in stat["per_societa"].values())
    print(f"[run] {modalita}: {len(records)} esaminati -> {len(tenuti)} pertinenti "
          f"-> {len(attivi)} attivi ({stat['nuovi']} nuovi, "
          f"{stat['manifestazioni']} manifestazioni d'interesse, "
          f"{stat['in_scadenza_7gg']} in scadenza entro 7 giorni)")
    print(f"[run] {riepilogo_societa} · {len(esiti)} esiti archiviati")
    return 0


if __name__ == "__main__":
    sys.exit(main())
