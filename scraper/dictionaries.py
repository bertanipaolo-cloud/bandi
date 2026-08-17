"""
Dizionari di rilevanza per il radar appalti del gruppo 4x4.

Quattro settori di interesse, divisi fra due societa':

  4x4
  - consulenza    : consulenza aziendale (direzionale, organizzativa, strategica,
                    formazione, project management, PNRR)
  - eventi        : organizzazione e gestione di eventi, congressi, fiere, allestimenti
  - catering      : catering, ristorazione, coffee break, banqueting, mense

  Joule
  - comunicazione : comunicazione istituzionale, campagne, digital e social, contenuti,
                    branding e grafica, ufficio stampa e media relations

Ogni settore ha:
  societa   -> a chi va assegnata l'opportunita' in dashboard e nel digest
  cpv       -> prefissi di codice CPV (match per prefisso) usati nel punteggio
  cpv_query -> prefissi da mandare ad ANAC come filtro lato server (3-8 cifre)
  categorie -> frammenti di "categoria merceologica" MePA (match per sottostringa)
  forti     -> keyword che da sole qualificano l'opportunita'
  deboli    -> keyword di contorno: contano solo in combinazione
  esclusioni-> keyword che azzerano il match (falsi amici tipici del settore)

Il punteggio finale e' 0-100. Vedi classify.py per la formula.

Nota sul confine consulenza / comunicazione. Il marketing e la comunicazione erano
nati dentro "consulenza" quando il radar serviva solo 4x4. Da agosto 2026 sono un
settore a se' e appartengono a Joule: i termini di comunicazione sono stati spostati,
non duplicati, cosi' un bando di comunicazione finisce a Joule e non a 4x4.
"""

# ---------------------------------------------------------------------------
# Normalizzazione: tutto viene confrontato su testo minuscolo senza accenti.
# ---------------------------------------------------------------------------

SETTORI = {
    "consulenza": {
        "etichetta": "Consulenza aziendale",
        "societa": "4x4",
        "colore": "#2a78d6",
        "colore_scuro": "#3987e5",
        # Prefissi mandati ad ANAC come filtro lato server: tagliano il volume
        # prima ancora del punteggio. Vanno tenuti stretti, non larghi.
        "cpv_query": [
            "79400", "79410", "79411", "79412", "79413", "79414", "79415",
            "79417", "79418", "79419", "79421",
            "72221", "72224", "73200", "73220",
            "79310", "79311", "79320",
            "80500", "80510", "80511", "80522", "80532",
            "79951", "66171", "79212", "75112100",
        ],
        "cpv": [
            "79400000",  # consulenza commerciale, di gestione e affini
            "79410000",  # consulenza gestionale
            "79411",     # consulenza gestione generale / finanziaria
            "79412000",  # consulenza gestione finanziaria
            "79413000",  # consulenza gestione marketing
            "79414000",  # consulenza gestione risorse umane
            "79415",     # consulenza gestione produzione / progettazione
            "79417000",  # consulenza sicurezza
            "79418000",  # consulenza acquisti
            "79419000",  # servizi di valutazione
            "79421",     # gestione progetti (non di costruzione)
            "72224000",  # consulenza gestione progetti
            "72221000",  # consulenza analisi di business
            "73200000",  # consulenza in ricerca e sviluppo
            "73220000",  # consulenza in sviluppo
            "79310000",  # ricerche di mercato
            "79311",     # indagini / sondaggi
            "79320000",  # sondaggi di opinione
            "80500000",  # servizi di formazione
            "80510000",  # formazione specialistica
            "80511000",  # formazione del personale
            "80522000",  # seminari di formazione
            "80532000",  # formazione manageriale
            "79951000",  # organizzazione di seminari
            "66171000",  # consulenza finanziaria
            "79212",     # revisione / audit
            "75112100",  # progetti di sviluppo amministrativo
        ],
        "categorie": [
            "servizi professionali",
            "supporto specialistico",
            "consulenza",
            "servizi di formazione",
            "formazione e addestramento",
            "ricerche di mercato",
            "servizi organizzativi",
            "servizi di supporto",
            "assistenza tecnica",
            "servizi per il funzionamento della pa",
        ],
        "forti": [
            "consulenza direzionale", "consulenza strategica", "consulenza aziendale",
            "consulenza organizzativa", "consulenza gestionale", "consulenza manageriale",
            "supporto specialistico", "assistenza tecnica specialistica",
            "advisory", "business plan", "piano industriale", "piano strategico",
            "riorganizzazione aziendale", "analisi organizzativa", "modello organizzativo",
            "controllo di gestione", "pianificazione strategica", "project management",
            "program management", "project management office", "pmo",
            "change management", "process reengineering", "reingegnerizzazione dei processi",
            "analisi dei processi", "mappatura dei processi", "efficientamento organizzativo",
            "studio di fattibilita", "piano economico finanziario",
            "due diligence", "valutazione d'impatto", "valutazione ex ante",
            "monitoraggio e valutazione", "supporto al rup", "supporto tecnico operativo",
            "capacity building", "assistenza tecnica pnrr", "supporto attuazione pnrr",
            "ricerche di mercato", "indagine di mercato conoscitiva",
            "formazione manageriale", "percorso formativo", "corso di formazione",
            "attivita formativa", "docenza", "coaching", "team building",
            "bilancio di sostenibilita", "rendicontazione sociale", "bilancio sociale",
            "carta dei servizi", "customer satisfaction", "analisi di customer",
        ],
        "deboli": [
            "consulenza", "supporto", "assistenza", "affiancamento", "advisory",
            "analisi", "studio", "ricerca", "valutazione", "monitoraggio",
            "formazione", "docenza", "aggiornamento professionale",
            "organizzazione", "processi", "governance", "strategia", "strategico",
            "sviluppo", "pianificazione", "programmazione", "progettazione", "redazione",
            "servizi professionali", "professionista", "esperto", "specialista",
            "pnrr", "fondi europei", "fesr", "fse", "programmazione comunitaria",
            "innovazione", "digitalizzazione", "transizione digitale",
            "risorse umane", "personale", "selezione", "reclutamento",
            "qualita", "certificazione", "iso 9001", "accreditamento",
            "rendicontazione", "audit", "revisione", "controllo",
        ],
        "esclusioni": [
            # consulenze specialistiche che non sono il nostro mestiere
            "consulenza medica", "consulenza sanitaria", "medico competente",
            "consulenza legale", "patrocinio legale", "difesa in giudizio", "avvocato",
            "consulenza notarile", "notaio",
            "consulenza informatica", "sviluppo software", "manutenzione software",
            "system integration", "help desk", "assistenza sistemistica",
            "software", "licenze", "licenza d'uso", "piattaforma informatica",
            "data protection officer", "dpo", "responsabile protezione dati",
            "rassegna stampa", "monitoraggio media", "media monitoring",
            "progettazione strutturale", "direzione lavori", "collaudo statico",
            "coordinatore per la sicurezza", "sicurezza in fase di esecuzione",
            "responsabile servizio prevenzione", "rspp", "d.lgs 81",
            "consulenza assicurativa", "brokeraggio assicurativo", "broker",
            "consulenza del lavoro", "elaborazione buste paga", "paghe e contributi",
            "consulenza fiscale", "dichiarazione dei redditi", "caf",
            "consulenza agronomica", "agronomo", "veterinario",
            "psicologo", "psicoterapia", "logopedista", "assistente sociale",
            "geologo", "indagine geognostica", "energetic", "diagnosi energetica",
            "certificazione energetica", "ape",
        ],
    },
    "eventi": {
        "etichetta": "Organizzazione eventi",
        "societa": "4x4",
        "colore": "#eb6834",
        "colore_scuro": "#d95926",
        "cpv_query": [
            "79950", "79951", "79952", "79953", "79954", "79956", "79957",
            "92300", "92310", "92312", "92320", "92330",
            "55120", "55130", "39154", "51313", "98341",
        ],
        "cpv": [
            "79950000",  # organizzazione mostre, fiere e congressi
            "79951000",  # organizzazione di seminari
            "79952",     # servizi di organizzazione di eventi
            "79953000",  # organizzazione di festival
            "79954000",  # organizzazione di feste
            "79955000",  # organizzazione di sfilate di moda
            "79956000",  # organizzazione di fiere ed esposizioni
            "79957000",  # organizzazione di aste
            "92000000",  # servizi ricreativi, culturali e sportivi
            "92300000",  # servizi di intrattenimento
            "92310000",  # servizi artistici e letterari
            "92312",     # servizi artistici
            "92320000",  # gestione di opere d'arte
            "92330000",  # servizi di aree ricreative
            "92360000",  # servizi pirotecnici
            "63510000",  # agenzie di viaggio
            "55120000",  # riunioni e conferenze in alberghi
            "55130000",  # altri servizi alberghieri
            "39154000",  # attrezzature per esposizioni
            "32321200",  # apparecchi audiovisivi
            "51313000",  # installazione attrezzature audio
            "98341",     # servizi di alloggio
        ],
        "categorie": [
            "servizi di organizzazione eventi",
            "organizzazione e gestione integrata degli eventi",
            "eventi",
            "servizi congressuali",
            "servizi culturali",
            "allestimenti",
            "servizi di comunicazione",
            "servizi turistici",
            "servizi ricreativi",
            "audio video",
        ],
        "forti": [
            "organizzazione eventi", "organizzazione di eventi", "gestione eventi",
            "gestione integrata degli eventi", "servizi per eventi", "event management",
            "organizzazione convegni", "organizzazione di convegni", "convegnistica",
            "congressi", "servizi congressuali", "segreteria organizzativa",
            "segreteria tecnico organizzativa", "provider ecm",
            "organizzazione manifestazioni", "manifestazione fieristica",
            "fiere ed esposizioni", "partecipazione a fiere", "stand fieristico",
            "allestimento stand", "allestimento espositivo", "allestimento scenografico",
            "allestimento mostra", "organizzazione mostra", "mostra ed esposizione",
            "rassegna culturale", "festival", "spettacolo dal vivo", "spettacoli",
            "servizi di hostess", "hostess e steward", "accoglienza e registrazione",
            "service audio", "service audio luci", "service tecnico audio video",
            "amplificazione e service", "impianto audio luci video",
            "noleggio palco", "montaggio palco", "service luci",
            "cerimoniale", "inaugurazione", "premiazione",
            "workshop ed eventi", "roadshow", "convention aziendale",
            "team building", "attivita di animazione",
            "supporto logistico organizzativo", "logistica dell'evento",
            # feste e manifestazioni popolari: il grosso dei bandi comunali
            "sagra", "festa patronale", "festa popolare", "palio",
            "corteo storico", "rievocazione storica", "notte bianca",
            "capodanno in piazza", "carnevale", "villaggio di natale",
            "cartellone eventi", "cartellone degli eventi", "programma di eventi",
            "programmazione culturale", "stagione teatrale", "stagione culturale",
            "ideazione e organizzazione", "ideazione e realizzazione",
            "direzione artistica", "gestione del programma culturale",
        ],
        "deboli": [
            "evento", "eventi", "manifestazione", "iniziativa", "rassegna",
            "convegno", "conferenza", "seminario", "workshop", "incontro",
            "congresso", "assemblea", "forum", "summit",
            "mostra", "esposizione", "fiera", "stand", "expo",
            "allestimento", "montaggio", "smontaggio", "noleggio attrezzature",
            "spettacolo", "concerto", "animazione", "intrattenimento",
            "cultura", "culturale", "promozione del territorio",
            "audio", "video", "luci", "palco", "amplificazione", "streaming",
            "hostess", "accoglienza", "reception", "segreteria",
            "logistica", "organizzativo", "promozionale",
            "gadget", "materiale promozionale", "grafica", "stampa",
        ],
        "esclusioni": [
            "eventi atmosferici", "eventi avversi", "eventi sismici",
            "eventi calamitosi", "gestione eventi alluvionali",
            "eventuali", "event log", "gestione degli eventi di sicurezza",
            "siem", "eventi informatici",
            "manifestazione di interesse per l'affidamento di lavori",
            "eventi sentinella",
            # servizi che gravitano intorno agli eventi ma sono altri mestieri
            "bagni chimici", "bus navetta", "servizio navetta",
            "safety e security", "steward di sicurezza", "raccolta rifiuti",
            "transennamento stradale", "pulizia post evento",
        ],
    },
    "catering": {
        "etichetta": "Catering e ristorazione",
        "societa": "4x4",
        "colore": "#1baf7a",
        "colore_scuro": "#199e70",
        "cpv_query": [
            "55300", "55310", "55320", "55330", "55400", "55410",
            "55500", "55510", "55511", "55512",
            "55520", "55521", "55523", "55524", "15894",
        ],
        "cpv": [
            "55520000",  # servizi di catering
            "55521",     # catering per privati / consegna pasti
            "55522000",  # catering per imprese di trasporto
            "55523",     # catering per altre imprese o enti
            "55524000",  # catering scolastico
            "55300000",  # servizi di ristorazione e mescita
            "55310000",  # servizi di ristorazione con cameriere
            "55320000",  # servizi di distribuzione pasti
            "55330000",  # servizi di caffetteria
            "55400000",  # servizi di mescita bevande
            "55410000",  # gestione bar
            "55500000",  # servizi di mensa e catering
            "55510000",  # servizi di mensa
            "55511000",  # mensa e altri servizi di caffetteria
            "55512000",  # gestione mensa
            "15894200",  # pasti preparati
            "15894210",  # pasti scolastici
            "15895000",  # prodotti da consumarsi in punti di ristoro
            "15982000",  # bevande analcoliche
            "42933000",  # distributori automatici
        ],
        "categorie": [
            "ristorazione",
            "catering",
            "servizi di ristorazione",
            "mensa",
            "buoni pasto",
            "alimenti",
            "bevande",
            "generi alimentari",
        ],
        "forti": [
            "servizio di catering", "servizi di catering", "catering",
            "banqueting", "servizio di banqueting",
            "coffee break", "welcome coffee", "light lunch", "lunch box",
            "colazione di lavoro", "buffet", "aperitivo", "cocktail",
            "rinfresco", "servizio di rinfresco", "cena di gala", "pranzo di lavoro",
            "somministrazione di alimenti e bevande", "somministrazione alimenti",
            "servizio di ristorazione", "servizi di ristorazione",
            "ristorazione collettiva", "ristorazione scolastica",
            "ristorazione aziendale", "ristorazione ospedaliera",
            "gestione mensa", "servizio mensa", "mensa aziendale", "mensa scolastica",
            "preparazione e fornitura pasti", "fornitura di pasti",
            "veicolazione pasti", "pasti veicolati", "consegna pasti a domicilio",
            "gestione bar", "gestione punto ristoro", "servizio bar",
            "cucina interna", "centro cottura",
            "refezione", "refezione scolastica", "servizio di refezione",
            "pasti preconfezionati", "vettovagliamento",
            "gestione del servizio di ristoro", "punto ristoro",
        ],
        "deboli": [
            "pasti", "pasto", "cibo", "alimenti", "alimentari", "bevande",
            "ristoro", "ristorazione", "mensa", "buffet", "bar",
            "cucina", "cuoco", "chef", "personale di sala", "cameriere",
            "food", "beverage", "menu", "derrate", "derrate alimentari",
            "haccp", "celiachia", "diete speciali",
            "stoviglie", "monouso", "compostabile",
            "colazione", "pranzo", "cena", "merenda",
        ],
        "esclusioni": [
            "buoni pasto elettronici",  # e' un servizio finanziario, non ristorazione
            "ticket restaurant",
            # il vending e' un altro mestiere: concessioni di distributori
            # automatici, erogatori d'acqua, snack. Non e' ristorazione servita.
            "distributori automatici", "distributore automatico",
            "distribuzione automatica", "erogatori di acqua", "erogatore di acqua",
            "snack e bevande", "bevande calde e fredde", "bevande calde fredde",
            "mangime", "alimentazione animale", "crocchette",
            "fornitura di attrezzature da cucina",
            "manutenzione attrezzature cucina",
            "lavori di ristrutturazione cucina",
            "derattizzazione", "disinfestazione",
            "smaltimento oli esausti", "raccolta rifiuti mensa",
            "vigilanza mensa", "sorveglianza mensa",
            "lavaggio stoviglie", "noleggio tovagliato",
        ],
    },
    "comunicazione": {
        "etichetta": "Comunicazione e marketing",
        "societa": "Joule",
        "colore": "#8b5cf6",
        "colore_scuro": "#a78bfa",
        "cpv_query": [
            "79340", "79341", "79342", "79413", "79416",
            "79822", "79823", "79824", "79970", "92400", "72413",
        ],
        "cpv": [
            "79340000",  # pubblicita' e marketing
            "79341",     # servizi pubblicitari (79341400 campagne pubblicitarie)
            "79342",     # marketing (direct marketing, promozionale)
            "79413000",  # consulenza gestione marketing
            "79416",     # servizi di pubbliche relazioni
            "79822",     # servizi di composizione e progettazione grafica
            "79823000",  # servizi di stampa e consegna
            "79824000",  # servizi di stampa e distribuzione
            "79970000",  # servizi di editoria
            "92400000",  # servizi di agenzie di stampa
            "72413000",  # progettazione di siti web
        ],
        "categorie": [
            "servizi di comunicazione",
            "comunicazione e marketing",
            "pubblicita",
            "marketing",
            "grafica",
            "servizi di stampa",
            "servizi editoriali",
            "servizi digitali",
            "audio video",
        ],
        "forti": [
            # comunicazione istituzionale e campagne
            "piano di comunicazione", "strategia di comunicazione",
            "campagna di comunicazione", "campagna informativa",
            "campagna pubblicitaria", "campagna di sensibilizzazione",
            "campagna promozionale", "comunicazione istituzionale",
            "comunicazione pubblica", "servizi di comunicazione",
            "attivita di comunicazione", "servizi integrati di comunicazione",
            "piano media", "pianificazione media", "media planning",
            "acquisto di spazi pubblicitari", "spazi pubblicitari",
            "pubblicita istituzionale", "comunicazione e disseminazione",
            "attivita di disseminazione", "stakeholder engagement",
            # formulazioni viste sui bandi veri di agosto 2026, che i termini
            # sopra non intercettavano: la PA scrive "nell'ambito della
            # comunicazione" molto piu' spesso di "piano di comunicazione"
            "ambito della comunicazione", "servizi di marketing",
            "marketing e comunicazione", "comunicazione e marketing",
            "attivita promozionali", "attivita di promozione",
            "servizi promozionali", "promozione e comunicazione",
            # ANAC pubblica anche schede in inglese (agenzie, ICE, progetti UE)
            "communication services", "marketing services",
            "communication and marketing", "press office", "media planning",
            "graphic design", "social media management", "branding",
            # digital, social, contenuti
            "social media", "social network", "gestione dei canali social",
            "gestione dei social", "campagna social", "piano editoriale",
            "content strategy", "produzione di contenuti", "creazione di contenuti",
            "digital marketing", "web marketing", "advertising online",
            "sito web istituzionale", "restyling del sito", "realizzazione del sito web",
            "gestione del sito istituzionale", "newsletter", "community management",
            # branding, identita' visiva, grafica
            "brand identity", "identita visiva", "immagine coordinata",
            "linea grafica", "progettazione grafica", "impaginazione grafica",
            "art direction", "direzione creativa", "naming",
            "materiale informativo", "materiali divulgativi", "prodotti editoriali",
            "materiale promozionale e divulgativo",
            # Nota: la produzione audiovisiva e fotografica NON e' mestiere di
            # Joule (deciso l'11/08/2026). I termini di pura produzione — video,
            # riprese, spot, servizio fotografico, videomaker — sono percio'
            # scesi fra i "deboli": un bando di comunicazione che include anche
            # dei video continua a entrare grazie ai termini di comunicazione,
            # ma un bando di sola produzione video resta fuori.
            # ufficio stampa e media relations
            "ufficio stampa", "addetto stampa", "media relations",
            "relazioni con i media", "rassegna stampa", "comunicati stampa",
            "conferenza stampa", "pubbliche relazioni",
            # marketing e promozione del territorio
            "piano di marketing", "marketing territoriale", "destination marketing",
            "promozione turistica", "brand del territorio", "storytelling",
        ],
        "deboli": [
            "comunicazione", "marketing", "promozione", "promozionale",
            "pubblicita", "campagna", "informazione", "divulgazione",
            "grafica", "stampa", "editoriale", "contenuti", "redazionale",
            "social", "web", "digitale", "online", "sito", "portale",
            "immagine", "brand", "logo", "media", "multimediale",
            "video", "fotografia", "spot", "audiovisivo", "videomaker",
            "produzione video", "riprese video", "servizio fotografico",
            "contenuti multimediali", "produzione multimediale",
            "brochure", "depliant", "locandina", "manifesti", "affissione",
            "gadget", "materiale promozionale",
            "sensibilizzazione", "disseminazione", "engagement", "community",
            "target", "pubblico", "cittadini", "utenza",
            "evento", "ufficio stampa", "editoria",
        ],
        "esclusioni": [
            # 1. "comunicazione" in senso telefonico / informatico
            "comunicazione elettronica", "servizi di comunicazione elettronica",
            "rete di comunicazione", "reti di comunicazione", "apparati di comunicazione",
            "sistema di comunicazione radio", "comunicazione dati", "connettivita",
            "centralino", "telefonia", "traffico telefonico",
            "teleselling", "vendita telefonica", "call center", "contact center",
            "front office", "back office", "billing", "assistenza alla clientela",
            # concessioni e sfruttamento commerciale del marchio o degli spazi:
            # l'ente cede un diritto, non compra un servizio creativo
            "concessione dell'uso del marchio", "merchandising",
            "sfruttamento pubblicitario", "gestione delle pensiline",
            "affissione manifesti", "servizio di affissione",
            # 2. "comunicazione" come atto amministrativo
            "comunicazioni obbligatorie", "comunicazione obbligatoria",
            "notifica e comunicazione atti", "notificazione degli atti",
            "messo notificatore", "comunicazione degli atti impositivi",
            # 3. la pubblicita' come tributo, non come servizio creativo:
            #    e' il falso amico numero uno del CPV 79340 nella PA
            "imposta di pubblicita", "imposta comunale sulla pubblicita",
            "pubbliche affissioni", "diritti sulle pubbliche affissioni",
            "canone unico patrimoniale", "canone patrimoniale",
            "accertamento e riscossione", "riscossione coattiva",
            # 4. tipografia e postalizzazione: altro mestiere
            "stampa tipografica", "tipografia", "fornitura di stampati",
            "stampa di modulistica", "carta intestata", "stampa di registri",
            "stampa e imbustamento", "postalizzazione", "servizi postali",
            "recapito della corrispondenza", "invio massivo",
            # 5. segnaletica e cartellonistica
            "segnaletica stradale", "cartellonistica stradale", "targhe",
            "insegne luminose", "impianti pubblicitari",
            # 6. la PA cerca uno sponsor, non un fornitore
            "avviso di sponsorizzazione", "ricerca di sponsor",
            "sponsorizzazione tecnica", "manifestazione di interesse per sponsor",
            # 7. omonimie sanitarie e sociali
            "comunicazione aumentativa", "comunicazione aumentativa alternativa",
            "mediatore culturale", "mediazione linguistica", "interpretariato",
        ],
    },
}

# Ordine di visualizzazione e appartenenza societaria.
SOCIETA = {
    "4x4": {
        "etichetta": "4x4",
        "descrizione": "consulenza, eventi e catering",
        "colore": "#2a78d6",
    },
    "Joule": {
        "etichetta": "Joule",
        "descrizione": "comunicazione e marketing",
        "colore": "#8b5cf6",
    },
}


def societa_di(settore):
    """Societa' a cui appartiene un settore; None se il settore non esiste."""
    s = SETTORI.get(settore)
    return s["societa"] if s else None


def cpv_query_tutti():
    """
    Prefissi CPV da mandare ad ANAC, deduplicati e ordinati.

    Il filtro CPV lato server e' la ragione per cui questo radar regge la scala
    nazionale: senza, ANAC restituisce decine di migliaia di pubblicazioni al mese.
    """
    prefissi = {p for s in SETTORI.values() for p in s.get("cpv_query", [])}
    return sorted(prefissi)

# ---------------------------------------------------------------------------
# Termini che qualificano *qualsiasi* settore come poco interessante:
# tipicamente lavori pubblici, forniture di beni durevoli, servizi tecnici.
# Non azzerano il punteggio, lo penalizzano.
# ---------------------------------------------------------------------------
ESCLUSIONI_GLOBALI = [
    # La PA cerca uno sponsor che le dia soldi, non un fornitore da pagare.
    # Vale per tutti i settori: la sponsorizzazione di una stagione teatrale
    # sembra un bando eventi ed e' l'esatto contrario di un'opportunita'.
    "avviso di sponsorizzazione", "ricerca di sponsor", "ricerca di sponsorizzazioni",
    "sponsorizzazione tecnica", "proposta di sponsorizzazione",
    "sponsorizzazione economica", "contratto di sponsorizzazione",
    # Selezioni di personale: non sono appalti di servizi.
    "selezione pubblica per titoli", "concorso pubblico per esami",
    "avviso di mobilita esterna", "conferimento di incarico individuale",
    "borsa di studio", "tirocinio formativo",
    # Vendite e concessioni di beni: si compra dall'ente, non si vende.
    "asta pubblica per la vendita", "alienazione di immobili",
    "bando di locazione", "concessione di aree demaniali",
]

PENALITA_GLOBALI = [
    "lavori di manutenzione", "manutenzione straordinaria", "opere edili",
    "fornitura e posa in opera", "realizzazione impianto",
    "noleggio autoveicoli", "acquisto arredi", "fornitura arredi",
    "fornitura di hardware", "licenze software", "rinnovo licenze",
    "servizio di pulizia", "servizi di pulizia", "sanificazione",
    "servizio di vigilanza", "guardia giurata",
    "trasporto scolastico", "servizio di trasporto",
    "cancelleria", "toner", "materiale di consumo",
    "dispositivi di protezione individuale", "dpi",
    "farmaci", "dispositivi medici", "materiale sanitario",
]

# Parole che indicano una procedura a cui una PMI non strutturata
# difficilmente accede: usate solo come nota, non come filtro.
SEGNALI_COMPLESSITA = [
    "accordo quadro", "sistema dinamico", "convenzione quadro",
    "centrale di committenza", "soa", "avvalimento",
    "raggruppamento temporaneo", "rti", "consorzio stabile",
]


# ---------------------------------------------------------------------------
# Filtro CPV per le fonti che lo espongono (ANAC lo ha, il MePA no).
#
# Su ANAC arrivano tutte le gare italiane: decine di migliaia al mese. Filtrare
# solo per parole chiave produrrebbe centinaia di falsi positivi a settimana.
# Il CPV e' obbligatorio e strutturato, quindi diventa il primo cancello:
#   - CPV in uno dei settori  -> si procede al punteggio
#   - CPV in questa lista     -> fuori, senza appello
#   - CPV in nessuna delle due -> ammesso solo se il titolo ha un termine forte
#     (le stazioni appaltanti sbagliano spesso il CPV: questa e' la valvola)
# ---------------------------------------------------------------------------
CPV_ESCLUSI = [
    "03",  # agricoltura, allevamento, pesca
    "09",  # petrolio, elettricita', combustibili
    "14",  # prodotti delle miniere
    "16",  # macchine agricole
    "18",  # abbigliamento e calzature
    "19",  # cuoio, tessili, plastica
    "22",  # stampati (stampa tipografica)
    "24",  # prodotti chimici
    "31",  # macchine e apparecchi elettrici
    "33",  # dispositivi medici e farmaci
    "34",  # veicoli e attrezzature per trasporto
    "35",  # attrezzature di sicurezza, difesa, armi
    "37",  # strumenti musicali, articoli sportivi, giochi
    "38",  # apparecchiature da laboratorio e ottiche
    "41",  # acqua captata e depurata
    "43",  # macchinari per estrazione e movimento terra
    "44",  # materiali da costruzione
    "45",  # lavori di costruzione
    "48",  # pacchetti software
    "50",  # servizi di riparazione e manutenzione
    "60",  # servizi di trasporto (escluso rifiuti)
    "64",  # poste e telecomunicazioni
    "65",  # erogazione acqua, gas, elettricita'
    "66",  # servizi finanziari e assicurativi  (66171 consulenza fin. resta ammesso a parte)
    "70",  # servizi immobiliari
    "71",  # servizi di architettura, ingegneria, collaudo
    "75",  # amministrazione pubblica, difesa, previdenza
    "76",  # servizi per l'industria del petrolio e del gas
    "77",  # servizi agricoli, forestali, orticoli
    "85",  # servizi sanitari e di assistenza sociale
    "90",  # servizi fognari, rifiuti, ambientali
    "98",  # altri servizi di comunita' (esclusi alloggio, gia' ammesso a parte)
]

# Prefissi che restano ammessi anche se la loro divisione e' nella lista sopra:
# l'eccezione batte la regola generale.
CPV_ECCEZIONI = [
    "66171",     # consulenza finanziaria
    "71241",     # studi di fattibilita'
    "75112100",  # progetti di sviluppo amministrativo
    "98341",     # servizi di alloggio (eventi residenziali)
]
