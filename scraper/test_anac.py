"""
Test dell'estrattore ANAC e dello smistamento fra 4x4 e Joule.

Il container di sviluppo non raggiunge pubblicitalegale.anticorruzione.it, quindi
i test girano su un campione **reale** catturato dal browser l'11 agosto 2026
(finestra 04-11/08, CPV dei quattro settori) piu' alcuni casi costruiti sui falsi
amici che ci aspettiamo dal CPV 79340.

    python3 scraper/test_anac.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch_anac import normalizza_avviso  # noqa: E402
from classify import classifica  # noqa: E402


def avviso(tipologia, scheda, descrizione, ente, cpv_etichetta, *,
           titolo=None, valore=None, natura="Servizi", pubblicazione="2026-08-11T06:00:00.000+00:00",
           scadenza=None, termine_invito=None, aggiudicatari=None, vinto=None,
           luogo="Roma", cig="B0000000AA", id_avviso="00000000-0000-0000-0000-000000000000"):
    """Costruisce un avviso nella forma esatta restituita dall'API PVL."""
    item = {
        "tipo_oggetto": "lotto",
        "cig": cig,
        "natura_principale": natura,
        "descrizione": descrizione,
        "cpv": cpv_etichetta,
        "luogo_nuts": luogo,
        "luogo_istat": luogo.upper(),
        "documenti_di_gara_link": "https://www.sua-rb.it/PortaleAppalti/it/procedure/codice/G00564",
    }
    if valore is not None:
        item["valore_complessivo_stimato"] = valore
    if vinto is not None:
        item["valore_offerta_vincente"] = vinto
    if termine_invito:
        item["termine_invito"] = termine_invito
    if aggiudicatari:
        item["aggiudicatari"] = aggiudicatari
    return {
        "idAvviso": id_avviso,
        "codiceScheda": scheda,
        "tipologia": tipologia,
        "dataPubblicazione": pubblicazione,
        "dataScadenza": scadenza,
        "templates": [{"template": {
            "metadata": {"titolo": titolo, "descrizione": descrizione},
            "sections": [
                {"name": "SEZ. A - Committente", "fields": {"soggetti_sa": [
                    {"codice_fiscale": "80002950766", "denominazione_amministrazione": ente}]}},
                {"name": "SEZ. B - Dati Generali", "fields": {
                    "documenti_di_gara_link": "https://www.sua-rb.it/PortaleAppalti/it/procedure"}},
                {"name": "SEZ. C - Oggetto", "items": [item]},
            ],
        }, "lingua": "it"}],
    }


# ---------------------------------------------------------------------------
# 1. Campione reale, verbatim dalla PVL dell'11 agosto 2026
# ---------------------------------------------------------------------------
REALI = [
    avviso(
        "INDAGINI_DI_MERCATO_SOTTO_SOGLIA", "P7_1_3",
        "Indagine esplorativa di mercato finalizzata all'individuazione di n. 5 operatori economici "
        "da invitare alla successiva procedura negoziata senza bando, ai sensi dell'art. 50, comma 1, "
        "lett. e), del D.Lgs. n. 36/2023, per l'affidamento dei servizi integrati di comunicazione, "
        "disseminazione, organizzazione di eventi, capacity building, sensibilizzazione, coinvolgimento "
        "del volontariato, networking e stakeholder engagement, supporto organizzativo e logistico alla "
        "realizzazione di esercitazioni di protezione civile, ideazione, produzione e diffusione di "
        "materiali informativi e multimediali nell'ambito del Progetto BREATH.",
        "REGIONE BASILICATA", "Servizi di organizzazione di eventi",
        valore=210438.52, termine_invito="2026-08-31T23:59:00Z", luogo="Matera",
        cig="BCAF44A14B", id_avviso="84976105-7f36-4413-b64b-89d98b9514de"),
    avviso(
        "RISULTATI", "A1_29",
        "affidamento della progettazione e realizzazione del piano di indagini annuale di customer "
        "satisfaction per il triennio 2025 - 2027 per i servizi di mobilità pubblica e privata offerti "
        "nel territorio di Roma Capitale.",
        "ROMA SERVIZI PER LA MOBILITA' S.R.L.",
        "Servizi di inchiesta relativi alla soddisfazione della clientela",
        titolo="Piano di indagini annuale di customer satisfaction 2025-2027",
        valore=270000.0, vinto=182614.5,
        aggiudicatari=[{"importo": 182614.5, "soggetti": [
            {"codice_fiscale": "05196740483", "denominazione": "Centro Statistica Aziendale S.r.l."}]}],
        cig="B48F36B2EA", id_avviso="7ba688c8-ce44-4357-9c2e-c580855142b6"),
    avviso(
        "BANDI", "P2_16",
        "PROCEDURA APERTA PER L'AFFIDAMENTO IN CONCESSIONE DEL SERVIZIO DI REFEZIONE SCOLASTICA "
        "E PASTI A DOMICILIO PER GLI ANNI SCOLASTICI 2026/2029",
        "PROVINCIA DI BRESCIA", "Servizi di ristorazione scolastica",
        valore=1250000.0, scadenza="2026-09-15T12:00:00.000+00:00", luogo="Brescia"),
    avviso(
        "INDAGINI_DI_MERCATO_SOTTO_SOGLIA", "P7_1_3",
        "AVVISO PUBBLICO PER MANIFESTAZIONE DI INTERESSE FINALIZZATA ALL'INDIVIDUAZIONE DI OPERATORI "
        "ECONOMICI DA INVITARE ALLA PROCEDURA NEGOZIATA PER IL SERVIZIO DI MENSA SCOLASTICA",
        "COMUNE DI GARDA", "Servizi di mensa scolastica",
        valore=95000.0, termine_invito="2026-08-28T12:00:00Z", luogo="Verona"),
    avviso(
        "MODIFICHE_CONTRATTUALI", "M2",
        "CONTRATTO FORNITURA DI POLIELETTROLITA PER IMPIANTI DI DEPURAZIONE - LOTTO 2",
        "SERVIZI INTEGRATI BELLUNESI SPA", "Additivi chimici",
        natura="Forniture", luogo="Belluno"),
]

# ---------------------------------------------------------------------------
# 2. Casi Joule: quello che il settore comunicazione deve prendere...
# ---------------------------------------------------------------------------
JOULE_SI = [
    avviso("INDAGINI_DI_MERCATO_SOTTO_SOGLIA", "P7_1_3",
           "Manifestazione di interesse per l'affidamento dei servizi di ideazione e realizzazione della "
           "campagna di comunicazione istituzionale, gestione dei canali social e produzione di contenuti "
           "multimediali per il triennio 2026-2028",
           "COMUNE DI VITERBO", "Servizi di pubblicità e marketing",
           valore=118000.0, termine_invito="2026-09-05T12:00:00Z"),
    avviso("BANDI", "P2_16",
           "Procedura aperta per l'affidamento del servizio di ufficio stampa, media relations e "
           "rassegna stampa dell'Ente",
           "AZIENDA OSPEDALIERA SAN CAMILLO", "Servizi di pubbliche relazioni",
           valore=145000.0, scadenza="2026-09-20T12:00:00.000+00:00"),
    avviso("INDAGINI_DI_MERCATO_SOTTO_SOGLIA", "P7_1_3",
           "Indagine di mercato per l'affidamento dei servizi di progettazione grafica, immagine "
           "coordinata e realizzazione del nuovo sito web istituzionale",
           "CAMERA DI COMMERCIO DI ROMA", "Servizi di progettazione grafica",
           valore=76000.0, termine_invito="2026-09-01T12:00:00Z"),
]

# ---------------------------------------------------------------------------
# 3. ...e i falsi amici che deve lasciare fuori. Sono tutti casi che il CPV
#    79340 (pubblicita' e marketing) porta dentro per davvero.
# ---------------------------------------------------------------------------
JOULE_NO = [
    avviso("BANDI", "P2_16",
           "Concessione del servizio di accertamento e riscossione dell'imposta di pubblicità, dei "
           "diritti sulle pubbliche affissioni e del canone unico patrimoniale",
           "COMUNE DI SAN MAURO TORINESE", "Servizi di pubblicità e marketing",
           valore=240000.0),
    avviso("BANDI", "P2_16",
           "Affidamento dei servizi di comunicazione elettronica, connettività e traffico telefonico "
           "per le sedi dell'Ente",
           "ASL ROMA 3", "Servizi di pubblicità e marketing", valore=310000.0),
    avviso("INDAGINI_DI_MERCATO_SOTTO_SOGLIA", "P7_1_3",
           "Avviso di sponsorizzazione per la ricerca di sponsor a sostegno della stagione teatrale",
           "COMUNE DI LATINA", "Servizi di pubblicità e marketing"),
    avviso("BANDI", "P2_16",
           "Fornitura di stampati e stampa di modulistica, carta intestata e registri per gli uffici",
           "PROVINCIA DI FROSINONE", "Servizi di stampa e consegna",
           natura="Forniture", valore=42000.0),
]


def verifica():
    errori = []

    def check(condizione, messaggio):
        if not condizione:
            errori.append(messaggio)

    # --- estrazione -------------------------------------------------------
    basilicata = normalizza_avviso(REALI[0])
    check(basilicata["momento"] == "manifestazione",
          f"Basilicata: momento {basilicata['momento']}, atteso manifestazione")
    check(basilicata["ente"] == "REGIONE BASILICATA", "Basilicata: ente non estratto")
    check(basilicata["valore"] == 210438.52, f"Basilicata: valore {basilicata['valore']}")
    check(basilicata["scadenza"] == "2026-08-31",
          f"Basilicata: scadenza {basilicata['scadenza']}, attesa 2026-08-31 dal termine_invito")
    check(basilicata["pubblicazione"] == "2026-08-11", "Basilicata: data pubblicazione")
    check(basilicata["url"].endswith("/avvisi/84976105-7f36-4413-b64b-89d98b9514de"),
          f"Basilicata: url {basilicata['url']}")
    check(basilicata["cpv_etichetta"] == "Servizi di organizzazione di eventi",
          "Basilicata: etichetta CPV")
    check(basilicata["numero"] == "BCAF44A14B", "Basilicata: CIG non estratto")

    roma = normalizza_avviso(REALI[1])
    check(roma["momento"] == "esito", f"Roma mobilità: momento {roma['momento']}")
    check(roma["valore_aggiudicato"] == 182614.5, "Roma mobilità: valore aggiudicato")
    check(roma["aggiudicatari"] and roma["aggiudicatari"][0]["nome"].startswith("Centro Statistica"),
          "Roma mobilità: aggiudicatario non estratto")
    check("/esiti/" in roma["url"], f"Roma mobilità: url {roma['url']}")
    check(roma["titolo"].startswith("Piano di indagini"),
          "Roma mobilità: il titolo deve venire da metadata.titolo quando c'è")

    brescia = normalizza_avviso(REALI[2])
    check(brescia["momento"] == "gara", f"Brescia: momento {brescia['momento']}")
    check("/bandi/" in brescia["url"], f"Brescia: url {brescia['url']}")
    check(brescia["scadenza"] == "2026-09-15", f"Brescia: scadenza {brescia['scadenza']}")

    vuoto = normalizza_avviso({"idAvviso": "x", "templates": []})
    check(vuoto is None, "Un avviso senza templates deve dare None, non esplodere")

    # --- smistamento fra societa' ----------------------------------------
    atteso = [
        (REALI[0], "4x4", "Basilicata: comunicazione + eventi, CPV eventi → 4x4 con Joule secondario"),
        (REALI[2], "4x4", "Refezione scolastica → catering 4x4"),
        (REALI[3], "4x4", "Mensa scolastica → catering 4x4"),
    ]
    for grezzo, societa, nota in atteso:
        r = classifica(normalizza_avviso(grezzo))
        check(r["societa"] == societa, f"{nota}: risulta {r['societa']} ({r['settore']})")

    for grezzo in JOULE_SI:
        r = classifica(normalizza_avviso(grezzo))
        check(r["settore"] == "comunicazione" and r["societa"] == "Joule",
              f"Joule mancato: «{r['titolo'][:60]}…» → {r['settore']} / {r['societa']} "
              f"({r['punteggio']} punti)")
        check(r["punteggio"] >= 50,
              f"Joule debole: «{r['titolo'][:60]}…» solo {r['punteggio']} punti")

    for grezzo in JOULE_NO:
        r = classifica(normalizza_avviso(grezzo))
        check(r["punteggio"] == 0,
              f"Falso amico passato: «{r['titolo'][:70]}…» → {r['settore']} "
              f"{r['punteggio']} punti, motivi {r['motivi']}")

    # --- il cancello CPV non deve tagliare i record ANAC ------------------
    r = classifica(normalizza_avviso(REALI[0]))
    check(r["cancello_cpv"] == "ammesso",
          f"ANAC filtra il CPV a monte: atteso 'ammesso', trovato {r['cancello_cpv']}")

    # --- le modifiche contrattuali non sono opportunita' ------------------
    m = normalizza_avviso(REALI[4])
    check(m["momento"] == "modifica", f"Belluno: momento {m['momento']}")

    return errori


if __name__ == "__main__":
    errori = verifica()
    if errori:
        print(f"✗ {len(errori)} problemi:\n")
        for e in errori:
            print(f"  · {e}")
        sys.exit(1)
    print("✓ estrazione ANAC e smistamento 4x4 / Joule: tutti i casi verdi")
