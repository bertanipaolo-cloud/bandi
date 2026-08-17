"""
Regressione sul campione reale ANAC.

33 pubblicazioni vere estratte dalla PVL il giorno 11 agosto 2026 (finestra
28/07-11/08, CPV del settore comunicazione). Servono a tenere onesta la
taratura di Joule: sono i bandi che il CPV 79340 porta davvero dentro, con
tutti i loro falsi amici.

Verdetto atteso: il settore vincente, oppure None se il record non deve entrare.

    python3 scraper/test_campione_reale.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from classify import classifica  # noqa: E402

# (etichetta CPV, descrizione, settore atteso)
CASI = [
    ("Servizi di inchiesta relativi alla soddisfazione della clientela",
     "affidamento della progettazione e realizzazione del piano di indagini annuale di customer "
     "satisfaction per il triennio 2025 - 2027 per i servizi di mobilità pubblica e privata",
     "consulenza"),
    ("Servizi di campagne pubblicitarie",
     "REALIZZAZIONE DI ATTIVITA' DI DESTINATION MARKETING INTERNAZIONALE DELLA DESTINAZIONE CALABRIA",
     "comunicazione"),
    ("Servizi di marketing",
     "FRAMEWORK CONTRACT COMMUNICATION AND MARKETING SERVICES FOR THE ITALIAN TRADE AGENCY "
     "LOS ANGELES OFFICE 2 years",
     "comunicazione"),
    ("Servizi pubblicitari e di marketing",
     "INCARICO PROFESSIONALE PER LA COMUNICAZIONE ISTITUZIONALE E LA GESTIONE DEI CANALI SOCIAL MEDIA",
     "comunicazione"),
    ("Servizi di agenzie di stampa",
     "Procedura aperta telematica per l'approvvigionamento di un servizio di Rassegna stampa, "
     "monitoraggio delle fonti WEB",
     "comunicazione"),
    ("Servizi pubblicitari e di marketing",
     "affidamento del servizio di comunicazione istituzionale",
     "comunicazione"),
    ("Servizi di campagne pubblicitarie",
     "Servizi per l'ideazione e la realizzazione di una campagna di comunicazione istituzionale "
     "multisoggetto e dei materiali informativi e di sensibilizzazione",
     "comunicazione"),
    ("Servizi di campagne pubblicitarie",
     "Realizzazione di attività di comunicazione nell'ambito della Campagna di promozione per la "
     "filiera della pasta",
     "comunicazione"),
    ("Servizi di campagne pubblicitarie",
     "servizio di comunicazione finalizzato alla promozione dei programmi di screening oncologico",
     "comunicazione"),
    ("Servizi di marketing", "servizio gestione social media , gestione annua", "comunicazione"),
    ("Servizi pubblicitari e di marketing",
     "PROCEDURA APERTA SOPRA SOGLIA COMUNITARIA PER L'AFFIDAMENTO DEI SERVIZI DI COMUNICAZIONE PER "
     "LA PROGETTAZIONE E REALIZZAZIONE DI EVENTI",
     "comunicazione"),
    ("Servizi di campagne pubblicitarie",
     "Servizio di comunicazione e sensibilizzazione sui comportamenti a minor impatto sulla "
     "qualità dell'aria",
     "comunicazione"),
    ("Servizi pubblicitari",
     "Sviluppo di campagne creative e l'organizzazione di eventi",
     "eventi"),
    ("Servizi pubblicitari e di marketing",
     "CONTRATTO QUADRO PER IL SERVIZIO NELL'AMBITO DELLA COMUNICAZIONE PER TRE ANNI",
     "comunicazione"),
    ("Servizi di consulenza in pubbliche relazioni",
     "PROCEDURA DI GARA APERTA PER L'AFFIDAMENTO DEI SERVIZI PROFESSIONALI IN AMBITO "
     "STAKEHOLDER ENGAGEMENT",
     "comunicazione"),
    ("Servizi di marketing",
     "Gara europea per l'acquisizione, mediante accordo quadro, di servizi specialistici di "
     "supporto alle attività di comunicazione e marketing",
     "comunicazione"),
    ("Servizi di progettazione grafica",
     "Procedura negoziata per l'affidamento dei servizi di progettazione grafica, ideazione "
     "creativa e realizzazione",
     "comunicazione"),
    ("Servizi pubblicitari e di marketing",
     "Accordo quadro per il servizio di pianificazione e gestione di attività promozionali sui "
     "social network e di analisi del traffico",
     "comunicazione"),

    ("Servizi pubblicitari e di marketing",
     "PROCEDURA APERTA PER L'AFFIDAMENTO DEL SERVIZIO DI PIANIFICAZIONE E ACQUISTO DI "
     "SPAZI PUBBLICITARI",
     "comunicazione"),
    ("Servizi di marketing",
     "Servizi di marketing e comunicazione per la promozione dei vini Alto Adige DOC nei mercati "
     "Svizzera, Regno Unito, Belgio",
     "comunicazione"),

    ("Servizi di marketing",
     "Procedura telematica aperta per l'affidamento dei servizi di comunicazione e "
     "intrattenimento, nonché di produzione e diffusione di contenuti multimediali",
     "comunicazione"),

    # --- devono restare fuori --------------------------------------------
    # La produzione audiovisiva pura non è mestiere di Joule (deciso l'11/08/2026):
    # entra solo se il bando è di comunicazione e il video è una delle componenti.
    ("Produzione di film e videocassette",
     "Servizio specialistico di supporto tecnico-scientifico alla progettazione e alla "
     "realizzazione dei contenuti multimediali e della ricostruzione tridimensionale",
     None),
    ("Servizi di produzione di film e video",
     "Supporto videomaker Giornata della Sicurezza e Martedì in cantiere",
     None),
    ("Servizi di gestione pubblicitaria",
     "GARA EUROPEA PER L'AFFIDAMENTO DEL SERVIZIO DI AFFISSIONE MANIFESTI SU IMPIANTI DI "
     "PROPRIETA' DEI COMUNI DI SASSUOLO, FORMIGINE, MARANELLO",
     None),
    ("Servizi di marketing",
     "Determina a contrarre, di affidamento e impegno per i servizi relativi ad una partnership "
     "con Istituto Capri Nel Mondo",
     None),
    ("Servizi di marketing", "AQ Servizio di vendita teleselling", None),
    ("Servizi di marketing",
     "Procedura negoziata per affidamento in concessione dell'uso del marchio ASI per la "
     "commercializzazione dei prodotti di merchandising",
     None),
    ("Servizi di produzione di film e video",
     "COMUNE DI CLAUZETTO - PROGETTO PALEOLITIC VIRTUAL REALITY EXPERIENCE - MUSEO DELLA GROTTA",
     None),
    ("Servizi di campagne pubblicitarie",
     "servizi di mediazione territoriale per lo sviluppo della raccolta differenziata nel "
     "territorio comunale della città di Napoli",
     None),
    ("Servizi di editoria",
     "Procedura negoziata senza pubblicazione di un bando per la sottoscrizione del servizio di "
     "pubblicazione di articoli",
     None),
    ("Servizi pubblicitari e di marketing",
     "PROCEDURA APERTA PER L'AFFIDAMENTO DELLA CONCESSIONE DEL SERVIZIO DI GESTIONE DELLE "
     "PENSILINE DELLE FERMATE AUTOBUS A FRONTE DELLO SFRUTTAMENTO PUBBLICITARIO",
     None),
    ("Servizi di progettazione grafica",
     "PNRR ATTRATTIVITA' DEI BORGHI STORICI Rigenerazione culturale e sociale dei Borghi storici",
     None),
    ("Servizi di assistenza alla clientela",
     "SERVIZI DI FRONT OFFICE, BACK OFFICE, CALL CENTER E BILLING COMPRENSIVO DELLA FORNITURA "
     "DEL RELATIVO SOFTWARE",
     None),
]


def main():
    ok = errori = 0
    righe = []
    for cpv, descrizione, atteso in CASI:
        r = classifica({
            "titolo": descrizione, "descrizione": descrizione,
            "categorie": [cpv], "cpv": [], "cpv_filtrato_a_monte": True,
            "ente": "", "stazione_appaltante": "", "tipo": "servizi",
        })
        ottenuto = r["settore"] if r["punteggio"] > 0 else None
        buono = ottenuto == atteso
        ok += buono
        errori += (not buono)
        righe.append(f"{'OK ' if buono else 'ERR'} | {str(atteso):<13} -> {str(ottenuto):<13} "
                     f"({r['punteggio']:>3}) | {descrizione[:64]}")
        if not buono:
            righe.append(f"      motivi: {r['motivi']}")

    print("\n".join(righe))
    print(f"\n{ok}/{len(CASI)} corretti sul campione reale, {errori} errori")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
