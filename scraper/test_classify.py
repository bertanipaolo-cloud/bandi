"""
Banco di prova del classificatore su titoli realistici di RDO MePA.
Serve a verificare che i dizionari non producano falsi positivi/negativi grossolani.

  python3 scraper/test_classify.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from classify import classifica, SOGLIA_MINIMA  # noqa: E402

# (titolo, categoria MePA, atteso: settore o None)
# I casi in coda vengono da bandi reali: servono a non far regredire la taratura.
CASI = [
    # --- consulenza: devono passare ---
    ("Affidamento del servizio di supporto specialistico al RUP per l'attuazione degli interventi PNRR",
     "Servizi - Servizi professionali", "consulenza"),
    ("Servizio di consulenza direzionale per la riorganizzazione dell'assetto organizzativo dell'Ente",
     "Servizi professionali di supporto specialistico", "consulenza"),
    ("Affidamento incarico per la redazione del piano industriale e del business plan della società partecipata",
     "Servizi", "consulenza"),
    ("Corso di formazione manageriale per dirigenti e posizioni organizzative",
     "Servizi di formazione", "consulenza"),
    ("Indagine di customer satisfaction sui servizi comunali e analisi dei processi di front office",
     "Ricerche di mercato", "consulenza"),
    ("Servizio di assistenza tecnica specialistica per il monitoraggio e la valutazione del programma FESR",
     "Servizi di supporto", "consulenza"),

    # --- eventi: devono passare ---
    ("Servizio di organizzazione e gestione integrata degli eventi istituzionali dell'Amministrazione",
     "Servizi di organizzazione eventi", "eventi"),
    ("Affidamento dei servizi di segreteria organizzativa e allestimento per il convegno nazionale",
     "Eventi e congressi", "eventi"),
    ("Service audio luci video per la rassegna culturale estiva in piazza",
     "Servizi - Allestimenti", "eventi"),
    ("Allestimento dello stand fieristico per la partecipazione alla fiera internazionale del turismo",
     "Servizi di organizzazione eventi", "eventi"),
    ("Organizzazione di festival cinematografico: direzione artistica, logistica e accoglienza ospiti",
     "Servizi culturali", "eventi"),

    # --- catering: devono passare ---
    ("Servizio di catering e coffee break per gli eventi istituzionali dell'Ente - anno 2026",
     "Ristorazione", "catering"),
    ("Affidamento del servizio di banqueting per la cena di gala di chiusura del congresso",
     "Servizi di ristorazione", "catering"),
    ("Servizio di ristorazione collettiva mediante centro cottura per la mensa scolastica",
     "Ristorazione collettiva", "catering"),
    ("Fornitura di light lunch e buffet per la giornata di studio del 12 novembre",
     "Servizi di catering", "catering"),

    # --- devono essere scartati ---
    ("Fornitura e posa in opera di arredi per ufficio", "Arredi", None),
    ("Servizio di pulizia e sanificazione degli immobili comunali", "Servizi di pulizia", None),
    ("Manutenzione straordinaria della copertura della scuola primaria", "Lavori", None),
    ("Rinnovo licenze software antivirus per 300 postazioni", "Informatica", None),
    ("Servizio di consulenza legale e patrocinio in giudizio dell'Ente", "Servizi legali", None),
    ("Incarico di RSPP ai sensi del D.Lgs 81/2008 e consulenza sulla sicurezza sui luoghi di lavoro",
     "Servizi professionali", None),
    ("Fornitura di buoni pasto elettronici per i dipendenti", "Buoni pasto", None),
    ("Servizio di gestione degli eventi avversi e degli eventi sentinella in ambito sanitario",
     "Servizi sanitari", None),
    ("Consulenza informatica per lo sviluppo software del portale istituzionale",
     "Servizi informatici", None),
    ("Noleggio autoveicoli a lungo termine per il parco mezzi comunale", "Veicoli", None),
    ("Servizio di trasporto scolastico per l'anno 2026/2027", "Trasporti", None),
    ("Fornitura di dispositivi medici e materiale sanitario monouso", "Sanitario", None),

    # --- casi reali presi dalla vetrina MePA del 06/08/2026 ---------------
    # (tarature nate guardando i 465 bandi effettivamente aperti quel giorno)
    ("AFFIDAMENTO DEL SERVIZIO DI REFEZIONE SCOLASTICA.", "Alimenti, ristorazione e buoni pasto", "catering"),
    ("Servizio di Refezione per le Scuole di Golasecca e per il Micronido", "", "catering"),
    ("Acquisto servizio Coffe break presidiato presso l'Università di Trento per 30 persone", "", "catering"),
    ("S028/2026 Accordo quadro avente ad oggetto i servizi di catering per eventi per la Città Metropolitana", "", "catering"),
    ("Concessione del Servizio Bar dell'Organismo di Protezione Sociale del Comando Aeroporto", "", "catering"),
    ("Servizio di ideazione, progettazione, produzione e gestione del programma culturale e degli eventi", "", "eventi"),
    ("Servizio di organizzazione della Sagra del Pistacchio 2026", "", "eventi"),
    ("Noleggio palco di dimensioni m. 12x m 14, di n. 1.500 sedie e di n. 100 transenne per n. 2 eventi", "", "eventi"),
    ("affidamento del servizio integrato di supporto tecnico-specialistico per la programmazione", "", "consulenza"),

    # il vending e' un altro mestiere, non ristorazione servita
    ("Concessione del servizio di distributori automatici", "Alimenti, ristorazione e buoni pasto", None),
    ("CONCESSIONE TRIENNALE DEL SERVIZIO DI SOMMINISTRAZIONE DI ALIMENTI E BEVANDE MEDIANTE DISTRIBUTORI AUTOMATICI", "Alimenti", None),
    ("Servizio di fornitura, installazione e gestione di erogatori di acqua alla spina", "Alimenti", None),
    # acquisti sanitari che pescano nel vocabolario alimentare
    ("DSS 66 ACQUISTO MODULEN IBD LATTE POLVERE", "Alimenti, ristorazione e buoni pasto", None),
    ("Copia di FORNITURA SUINI", "Alimenti, ristorazione e buoni pasto", None),
    ("FORNITURA DI MANGIME DEL TIPO SECCO E UMIDO PER ALIMENTAZIONE ANIMALE", "Alimenti", None),
    # informatica e privacy travestite da consulenza
    ("Rinnovo e potenziamento di software a supporto del progetto SFIDA2, con servizi di formazione, assistenza e supporto specialistico", "Informatica", None),
    ("SERVIZIO DI SUPPORTO SPECIALISTICO AL DATA PROTECTION OFFICER (DPO) DELL'AZIENDA SANITARIA", "Servizi professionali", None),
    # Dall'agosto 2026 la rassegna stampa non e' piu' uno scarto: e' Joule.
    # Restava fuori quando il radar serviva la sola 4x4, per cui era un falso
    # amico della consulenza. Ora deve finire nel settore comunicazione.
    ("servizi di rassegna stampa e monitoraggio file multimediali, radiofonici e televisivi", "Servizi di comunicazione", "comunicazione"),
    # comunicazione: casi che devono restare fuori anche con il nuovo settore
    ("Concessione del servizio di accertamento e riscossione dell'imposta di pubblicità e pubbliche affissioni", "Servizi di comunicazione", None),
    ("Affidamento dei servizi di comunicazione elettronica e connettività per le sedi", "Servizi di comunicazione", None),
    ("Servizio di comunicazione aumentativa alternativa per alunni con disabilità", "Servizi di comunicazione", None),
    # comunicazione: casi che devono entrare
    ("Servizio di ideazione e realizzazione della campagna di comunicazione istituzionale", "Servizi di comunicazione", "comunicazione"),
    ("Affidamento del servizio di ufficio stampa e media relations", "", "comunicazione"),
    ("Realizzazione del nuovo sito web istituzionale e dell'immagine coordinata dell'Ente", "", "comunicazione"),
    ("Gestione dei canali social e produzione di contenuti multimediali", "", "comunicazione"),
    # servizi che gravitano intorno agli eventi ma sono altri mestieri
    ("Affidamento del servizio di noleggio bagni chimici per la manifestazione Sagra del Pistacchio", "Rifiuti", None),
    ("Servizio di noleggio bus navetta per la manifestazione Sagra del Pistacchio 2026", "", None),
    ("Servizio di Safety e Security in occasione della manifestazione per la valorizzazione", "", None),
    # over-stemming: "paline" non e' "palio"
    ("FORNITURA E INSTALLAZIONE DI ULTERIORI PALINE INTELLIGENTI INFORMATIVE E SISTEMA DI MONITORAGGIO", "", None),
]


def main():
    ok = errori = 0
    righe = []
    for titolo, categoria, atteso in CASI:
        r = classifica({"titolo": titolo, "categorie": [categoria],
                        "descrizione": "", "cpv": [], "ente": "", "stazione_appaltante": ""})
        ottenuto = r["settore"] if r["punteggio"] >= SOGLIA_MINIMA else None
        buono = ottenuto == atteso
        ok += buono
        errori += (not buono)
        righe.append(
            f"{'OK ' if buono else 'ERR'} | {str(atteso):<11} -> {str(ottenuto):<11} "
            f"({r['punteggio']:>3}) | {titolo[:72]}"
        )
        if not buono:
            righe.append(f"      motivi: {r['motivi']} | punteggi: {r['punteggi']}")

    print("\n".join(righe))
    print(f"\n{ok}/{len(CASI)} corretti, {errori} errori")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
