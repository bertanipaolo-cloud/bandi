"""
Dizionari di rilevanza per il radar appalti del gruppo 4x4.

Nove settori di interesse, divisi fra le otto societa' del gruppo.

Servizi:
  4x4       - consulenza    : consulenza aziendale (direzionale, organizzativa,
                              strategica, formazione, project management, PNRR)
  4x4       - eventi        : eventi, congressi, fiere, allestimenti
  Latta     - catering      : catering per eventi, coffee break, banqueting.
                              NON le mense: la ristorazione collettiva e' fuori
                              perimetro dal 24/08/2026.
  Joule     - comunicazione : comunicazione istituzionale, campagne, digital e
                              social, contenuti, branding, ufficio stampa

Forniture di beni (aggiunte il 24/08/2026):
  New Food  - alimentari    : derrate, ortofrutta, biologico, lattiero-caseari
  Gabrini   - gastronomia   : gastronomia pronta, salumeria, carni, forno
  Berebene  - bevande       : bevande analcoliche, acque minerali, birra
  Icaro     - vino          : vini e servizi enologici
  Topic     - editoria      : libri, periodici, patrimonio librario

Il confine fra catering e forniture alimentari e' netto e va tenuto: gestire una
mensa e' un SERVIZIO (fuori perimetro), vendere le derrate a quella stessa mensa
e' una FORNITURA (dentro, a New Food o Gabrini).

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
        "etichetta": "Catering per eventi",
        "societa": "Latta",
        "colore": "#1baf7a",
        "colore_scuro": "#199e70",
        "cpv_query": [
            "55300", "55310", "55330", "55400", "55410",
            "55520", "55521", "55523",
        ],
        "cpv": [
            "55520000",  # servizi di catering
            "55521",     # catering per privati / consegna pasti
            "55522000",  # catering per imprese di trasporto
            "55523",     # catering per altre imprese o enti
            "55300000",  # servizi di ristorazione e mescita
            "55310000",  # servizi di ristorazione con cameriere
            "55330000",  # servizi di caffetteria
            "55400000",  # servizi di mescita bevande
            "55410000",  # gestione bar
            "15895000",  # prodotti da consumarsi in punti di ristoro
            "15982000",  # bevande analcoliche
        ],
        "categorie": [
            "ristorazione",
            "catering",
            "servizi di ristorazione",
            "alimenti",
            "bevande",
        ],
        "forti": [
            "servizio di catering", "servizi di catering", "catering",
            "banqueting", "servizio di banqueting",
            "coffee break", "welcome coffee", "light lunch", "lunch box",
            "colazione di lavoro", "buffet", "aperitivo", "cocktail",
            "rinfresco", "servizio di rinfresco", "cena di gala", "pranzo di lavoro",
            "somministrazione di alimenti e bevande", "somministrazione alimenti",
            "catering per eventi", "servizio di ristorazione per eventi",
            "brunch", "open bar", "servizio di sala e cucina per eventi",
            "gestione bar", "gestione punto ristoro", "servizio bar",
            "gestione del servizio di ristoro", "punto ristoro",
        ],
        "deboli": [
            "pasti", "pasto", "cibo", "alimenti", "alimentari", "bevande",
            "ristoro", "ristorazione", "buffet", "bar",
            "cucina", "cuoco", "chef", "personale di sala", "cameriere",
            "food", "beverage", "menu", "derrate", "derrate alimentari",
            "haccp", "celiachia", "diete speciali",
            "stoviglie", "monouso", "compostabile",
            "colazione", "pranzo", "cena", "merenda",
        ],
        "esclusioni": [
            # La ristorazione collettiva esce in blocco (24/08/2026): prima
            # era uscito il solo mondo scuola, poi Paolo ha tolto "le mense e
            # dintorni". Gestire una mensa — centro cottura, dietista, appalto
            # pluriennale — non e' il mestiere di Latta, che fa catering
            # d'evento. La FORNITURA di cibo a una mensa resta invece dentro,
            # ma nei settori alimentari e gastronomia: la' si vende merce, qui
            # si eroga un servizio.
            "refezione", "refezione scolastica", "servizio di refezione",
            "ristorazione scolastica", "mensa scolastica", "mense scolastiche",
            "pasti scolastici", "catering scolastico",
            "mensa per le scuole", "mensa degli alunni", "mensa alunni",
            "ristorazione per le scuole", "pasti per le scuole",
            "scuola dell'infanzia", "scuole dell'infanzia",
            "asilo nido", "asili nido", "nido comunale",
            "mensa", "mense", "gestione mensa", "servizio mensa",
            "mensa aziendale", "mensa ospedaliera", "mensa di servizio",
            "ristorazione collettiva", "ristorazione aziendale",
            "ristorazione ospedaliera", "ristorazione assistenziale",
            "centro cottura", "cucina interna", "cucina centralizzata",
            "veicolazione pasti", "pasti veicolati", "distribuzione pasti",
            "consegna pasti a domicilio", "pasti a domicilio",
            "preparazione e fornitura pasti", "fornitura di pasti",
            "pasti preconfezionati", "vettovagliamento",
            "casa di riposo", "residenza sanitaria assistenziale", "rsa",
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

    # -----------------------------------------------------------------------
    # Forniture di beni. Aggiunte il 24/08/2026 insieme alle altre societa'
    # del gruppo: fino a quel giorno il radar guardava solo i servizi.
    # Sono un mondo piu' affollato dei servizi — i CPV 15xxx (alimentari) sono
    # fra i piu' battuti della PA — quindi qui i cancelli CPV vanno tenuti
    # stretti e le esclusioni sono piu' lunghe delle inclusioni.
    # -----------------------------------------------------------------------

    "alimentari": {
        "etichetta": "Forniture alimentari",
        "societa": "New Food",
        "colore": "#0d9488",
        "colore_scuro": "#14b8a6",
        "cpv_query": [
            "15300", "15310", "15330", "15331", "15332", "15500", "15510",
            "15540", "15550", "15600", "15610", "15800", "15810", "15870",
            "03220", "03221", "03222",
        ],
        "cpv": [
            "15300000",  # frutta, ortaggi e affini
            "15310000",  # patate e prodotti a base di patate
            "15330000",  # frutta e ortaggi trasformati
            "15331",     # ortaggi trasformati / surgelati
            "15332",     # frutta trasformata, confetture
            "15500000",  # prodotti lattiero-caseari
            "15510000",  # latte e panna
            "15540000",  # formaggi
            "15550000",  # prodotti lattiero-caseari vari
            "15600000",  # prodotti di macinazione, cereali, amidi
            "15610000",  # prodotti della macinazione
            "15800000",  # prodotti alimentari vari
            "15810000",  # produzione di pane, pasticceria fresca
            "15870000",  # condimenti e spezie
            "03220000",  # ortaggi, frutta e frutta a guscio
            "03221",     # ortaggi
            "03222",     # frutta e frutta a guscio
        ],
        "categorie": [
            "alimenti", "generi alimentari", "prodotti alimentari",
            "ortofrutta", "prodotti ortofrutticoli", "derrate alimentari",
            "prodotti biologici",
        ],
        "forti": [
            "fornitura di generi alimentari", "fornitura generi alimentari",
            "fornitura di derrate alimentari", "fornitura derrate",
            "fornitura di prodotti alimentari", "acquisto di generi alimentari",
            "derrate alimentari", "generi alimentari",
            "prodotti ortofrutticoli", "fornitura di ortofrutta",
            "frutta e verdura", "frutta e ortaggi", "ortaggi freschi",
            "prodotti biologici", "filiera biologica", "prodotti a km zero",
            "prodotti a chilometro zero", "prodotti dop e igp",
            "prodotti lattiero caseari", "fornitura di latte",
            "fornitura di pane", "prodotti da forno",
            "alimenti per celiaci", "prodotti senza glutine",
            "prodotti vegetali", "alimenti vegetali", "prodotti vegani",
        ],
        "deboli": [
            "fornitura", "acquisto", "approvvigionamento", "somministrazione",
            "alimenti", "alimentari", "food", "biologico", "bio", "fresco",
            "surgelati", "conserve", "dispensa", "economato",
            "frutta", "verdura", "ortaggi", "latte", "formaggi", "pane",
            "accordo quadro", "lotto", "annuale", "triennale",
        ],
        "esclusioni": [
            # non e' cibo per persone
            "mangime", "alimentazione animale", "crocchette", "pet food",
            "alimenti zootecnici", "foraggio",
            # nutrizione clinica: mestiere farmaceutico, non alimentare
            "nutrizione artificiale", "nutrizione enterale", "nutrizione parenterale",
            "integratori alimentari", "latte in polvere per lattanti",
            "alimenti a fini medici speciali", "dietetici per nefropatici",
            # attrezzature e contorno, non la merce
            "attrezzature da cucina", "arredi per mensa", "stoviglie",
            "lavastoviglie", "cella frigorifera", "abbattitore",
            "trasporto di derrate", "facchinaggio",
            # i buoni pasto sono un servizio finanziario
            "buoni pasto", "buoni spesa", "ticket restaurant",
        ],
    },

    "gastronomia": {
        "etichetta": "Gastronomia e retail",
        "societa": "Gabrini",
        "colore": "#b45309",
        "colore_scuro": "#d97706",
        "cpv_query": [
            "15100", "15110", "15130", "15131", "15200", "15220", "15230",
            "15810", "15811", "15812", "15820", "15840", "15850",
        ],
        "cpv": [
            "15100000",  # prodotti di origine animale, carne
            "15110000",  # carni
            "15130000",  # prodotti a base di carne
            "15131",     # conserve e preparati di carne
            "15200000",  # pesce preparato e conservato
            "15220000",  # pesce, filetti surgelati
            "15230000",  # pesce essiccato o affumicato
            "15810000",  # pane, prodotti di panetteria
            "15811",     # prodotti di panetteria
            "15812",     # paste alimentari e dolci
            "15820000",  # fette biscottate e biscotti
            "15840000",  # cacao, cioccolato, dolciumi
            "15850000",  # paste alimentari
        ],
        "categorie": [
            "gastronomia", "salumeria", "carni", "prodotti a base di carne",
            "prodotti da forno", "pasticceria", "alimenti",
        ],
        "forti": [
            "prodotti di gastronomia", "fornitura di gastronomia",
            "piatti pronti", "pasti pronti confezionati", "gastronomia pronta",
            "salumi e formaggi", "fornitura di salumi", "prodotti di salumeria",
            "fornitura di carni", "carni fresche", "prodotti a base di carne",
            "fornitura di prodotti ittici", "prodotti ittici",
            "prodotti di panetteria", "prodotti di pasticceria",
            "pasticceria fresca", "prodotti dolciari",
            "fornitura di pizze", "prodotti di rosticceria",
            "banco gastronomia", "banco salumeria",
        ],
        "deboli": [
            "fornitura", "acquisto", "approvvigionamento",
            "gastronomia", "salumeria", "rosticceria", "pasticceria",
            "carne", "carni", "salumi", "formaggi", "pesce", "ittici",
            "pane", "pizza", "dolci", "biscotti", "pasta",
            "confezionato", "porzionato", "monoporzione",
            "accordo quadro", "lotto",
        ],
        "esclusioni": [
            "mangime", "alimentazione animale", "pet food",
            "macellazione", "impianto di macellazione",
            "attrezzature da cucina", "banco frigo", "vetrina refrigerata",
            "buoni pasto", "ticket restaurant",
            "smaltimento", "sottoprodotti di origine animale",
        ],
    },

    "bevande": {
        "etichetta": "Bevande e distribuzione",
        "societa": "Berebene",
        "colore": "#0891b2",
        "colore_scuro": "#22d3ee",
        "cpv_query": [
            "15900", "15910", "15960", "15961", "15980", "15981", "15982",
        ],
        "cpv": [
            "15900000",  # bevande, tabacco e prodotti affini
            "15960000",  # birra di malto
            "15961",     # birra
            "15980000",  # bevande analcoliche
            "15981",     # acque minerali
            "15982000",  # bevande analcoliche varie
        ],
        "categorie": [
            "bevande", "acque minerali", "birra", "alimenti",
        ],
        "forti": [
            "fornitura di bevande", "fornitura bevande", "acquisto di bevande",
            "bevande analcoliche", "acqua minerale", "fornitura di acqua minerale",
            "acque minerali", "bibite", "fornitura di birra",
            "distribuzione di bevande", "logistica delle bevande",
            "fornitura di succhi", "bevande calde e fredde in confezione",
        ],
        "deboli": [
            "bevande", "acqua", "bibite", "birra", "succhi", "analcoliche",
            "fornitura", "distribuzione", "consegna", "approvvigionamento",
            "bottiglie", "lattine", "fusti", "accordo quadro", "lotto",
        ],
        "esclusioni": [
            # il vending e' un altro mestiere: c'e' gia' un settore per il resto
            "distributori automatici", "distributore automatico",
            "distribuzione automatica", "erogatori di acqua", "erogatore di acqua",
            "erogatori d'acqua", "casette dell'acqua",
            # non e' la bevanda, e' la rete idrica
            "servizio idrico", "acquedotto", "rete idrica", "potabilizzazione",
            "fornitura di acqua potabile mediante autobotte", "autobotte",
            "analisi delle acque", "acqua per uso industriale",
            # bar e mescita sono servizi, stanno nel catering
            "gestione bar", "servizio bar", "mescita",
            "attrezzature per la refrigerazione",
        ],
    },

    "vino": {
        "etichetta": "Vino ed enologia",
        "societa": "Icaro",
        "colore": "#9d174d",
        "colore_scuro": "#be185d",
        "cpv_query": [
            "15930", "15931", "15932", "15940", "15950",
        ],
        "cpv": [
            "15930000",  # vini
            "15931",     # vini non aromatizzati
            "15932000",  # fecce di vino
            "15940000",  # sidro e altri vini di frutta
            "15950000",  # bevande fermentate non distillate
        ],
        "categorie": [
            "vino", "vini", "bevande alcoliche", "alimenti",
        ],
        "forti": [
            "fornitura di vino", "fornitura di vini", "acquisto di vino",
            "vini doc", "vini docg", "vini igt", "vino sfuso",
            "vini da tavola", "cantina sociale", "prodotti vitivinicoli",
            "promozione del vino", "degustazione di vini", "carta dei vini",
            "servizi enologici", "consulenza enologica", "analisi enologiche",
            "vendemmia", "vinificazione", "imbottigliamento del vino",
        ],
        "deboli": [
            "vino", "vini", "vitivinicolo", "enologia", "enologico",
            "cantina", "uve", "vigneto", "degustazione", "sommelier",
            "fornitura", "acquisto", "lotto", "accordo quadro",
        ],
        "esclusioni": [
            # il vigneto come opera agricola non e' vendita di vino
            "impianto di vigneto", "reimpianto viticolo", "potatura",
            "trattamenti fitosanitari", "macchine agricole",
            "estirpazione", "diserbo",
            # alcolici che non sono vino
            "superalcolici", "distillati", "liquori", "grappa",
            "alcool etilico", "alcol denaturato",
            # concessioni di somministrazione
            "licenza di somministrazione", "gestione enoteca",
        ],
    },

    "editoria": {
        "etichetta": "Editoria e libri",
        "societa": "Topic",
        "colore": "#475569",
        "colore_scuro": "#94a3b8",
        "cpv_query": [
            "22110", "22111", "22112", "22113", "22114", "22120", "22200",
            "22210", "92511",
        ],
        "cpv": [
            "22110000",  # libri stampati
            "22111000",  # libri scolastici
            "22112000",  # libri di testo
            "22113000",  # libri per biblioteche
            "22114",     # dizionari, mappe, spartiti, altri libri
            "22120000",  # pubblicazioni
            "22200000",  # giornali, riviste, periodici
            "22210000",  # giornali
            "92511000",  # servizi di biblioteche
        ],
        "categorie": [
            "libri", "editoria", "pubblicazioni", "periodici",
            "prodotti editoriali", "servizi bibliotecari",
        ],
        "forti": [
            "fornitura di libri", "acquisto di libri", "fornitura libri",
            "libri per la biblioteca", "incremento del patrimonio librario",
            "patrimonio librario", "materiale librario", "volumi a stampa",
            "fornitura di volumi", "acquisto di volumi",
            "abbonamenti a periodici", "abbonamenti a riviste",
            "fornitura di periodici", "riviste specializzate",
            "pubblicazioni scientifiche", "editoria specializzata",
            "cataloghi d'arte", "catalogo della mostra",
            "servizio di edizione", "stampa del catalogo",
            "libri d'arte", "monografie",
        ],
        "deboli": [
            "libri", "libro", "volumi", "editoria", "editoriale",
            "pubblicazione", "pubblicazioni", "riviste", "periodici",
            "abbonamento", "abbonamenti", "catalogo", "collana",
            "biblioteca", "biblioteche", "patrimonio librario",
            "fornitura", "acquisto", "lotto", "accordo quadro",
        ],
        "esclusioni": [
            # i libri di testo scolastici gratuiti sono una partita
            # amministrativa del comune, non una fornitura editoriale
            "cedole librarie", "cedola libraria", "libri di testo gratuiti",
            "fornitura gratuita dei libri di testo",
            # banche dati e periodici elettronici: mestiere da aggregatore
            "banche dati", "banca dati", "risorse elettroniche",
            "periodici elettronici", "e-book", "piattaforma digitale",
            "abbonamento software", "licenze",
            # la gestione della biblioteca e' un servizio, non una fornitura
            "gestione della biblioteca", "servizio di prestito",
            "catalogazione", "riordino archivistico", "archivio storico",
            "digitalizzazione del patrimonio",
            # tipografia: si stampa per conto terzi, non si vende un libro
            "stampa tipografica", "tipografia", "fornitura di stampati",
            "stampa di modulistica",
        ],
    },
}

# Ordine di visualizzazione e appartenenza societaria.
SOCIETA = {
    "4x4": {
        "etichetta": "4x4",
        "descrizione": "consulenza ed eventi",
        "colore": "#2a78d6",
    },
    "Joule": {
        "etichetta": "Joule",
        "descrizione": "comunicazione e marketing",
        "colore": "#8b5cf6",
    },
    "Latta": {
        "etichetta": "Latta",
        "descrizione": "catering per eventi",
        "colore": "#1baf7a",
    },
    "New Food": {
        "etichetta": "New Food",
        "descrizione": "forniture alimentari",
        "colore": "#0d9488",
    },
    "Gabrini": {
        "etichetta": "Gabrini",
        "descrizione": "gastronomia e retail alimentare",
        "colore": "#b45309",
    },
    "Berebene": {
        "etichetta": "Berebene",
        "descrizione": "bevande e distribuzione",
        "colore": "#0891b2",
    },
    "Icaro": {
        "etichetta": "Icaro",
        "descrizione": "vino ed enologia",
        "colore": "#9d174d",
    },
    "Topic": {
        "etichetta": "Topic",
        "descrizione": "editoria e libri",
        "colore": "#475569",
    },
}


def slug_societa(societa):
    """
    Nome della societa' ridotto a etichetta di file e di variabile d'ambiente.
    "New Food" -> "new-food" (file) e NEW_FOOD (env). Serve perche' dal
    24/08/2026 le societa' sono otto e i nomi contengono spazi.
    """
    fuori = []
    for carattere in (societa or "").lower():
        fuori.append(carattere if carattere.isalnum() else "-")
    return "-".join(pezzo for pezzo in "".join(fuori).split("-") if pezzo)


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
