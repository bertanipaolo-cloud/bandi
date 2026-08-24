# Radar appalti · gruppo 4x4

Motore di ricerca settimanale sugli appalti pubblici, filtrato sui mestieri delle otto società del gruppo:

| Società | Settori |
|---|---|
| **4x4** | consulenza aziendale · organizzazione eventi |
| **Joule** | comunicazione e marketing: campagne, digital e social, branding e grafica, ufficio stampa |
| **Latta** | catering per eventi: coffee break, banqueting, buffet. **Non** le mense |
| **New Food** | forniture alimentari: derrate, ortofrutta, biologico, lattiero-caseari |
| **Gabrini** | gastronomia e retail: salumeria, carni, prodotti da forno, piatti pronti |
| **Berebene** | bevande: analcoliche, acque minerali, birra |
| **Icaro** | vino ed enologia |
| **Topic** | editoria: libri, periodici, patrimonio librario |

Dal 24/08/2026 il radar guarda anche le **forniture di beni**, non solo i servizi.
Il confine con il catering è netto: gestire una mensa è un servizio ed è fuori
perimetro; vendere le derrate a quella stessa mensa è una fornitura e resta dentro,
a New Food o Gabrini.

Dashboard pubblicata: `https://bertanipaolo-cloud.github.io/mepa-radar/`

---

## Perché guarda le manifestazioni d'interesse

Sui servizi ANAC misura che **il 92–95% delle procedure è affidamento diretto, ma solo
il 17–31% del valore**. Quasi tutto quello che la PA compra lo compra per chiamata, e la
consulenza sta lì: i singoli incarichi stanno sotto i 140.000 €, la soglia entro cui
l'affidamento diretto è ammesso senza gara. C'è anche un addensamento vistoso appena
sotto: nel 2024 il 31% degli affidamenti della fascia stava fra 135.000 e 140.000 €.

Un radar che guardasse solo i bandi vedrebbe quindi la fetta sbagliata del mercato.
Il punto di ingresso vero è l'**avviso di indagine di mercato**: la manifestazione
d'interesse con cui una stazione appaltante sceglie chi invitare alla procedura
negoziata. È pubblicato, ha termini brevi, ed è l'unico momento in cui si entra in
partita. Per questo in dashboard e nel digest le manifestazioni vengono prima di tutto
il resto, con un bollino viola.

---

## Le tre fonti

### ANAC · Piattaforma di Pubblicità a Valore Legale (principale)

Registro a valore legale: dal 2024 ogni bando, avviso ed esito italiano passa di qui.
È l'unica fonte che porta le indagini di mercato sotto soglia.

```
GET https://pubblicitalegale.anticorruzione.it/api/v0/avvisi-full-text-specializzata
    ?page=0&pageSize=100
    &dataPubblicazioneStart=GG/MM/AAAA&dataPubblicazioneEnd=GG/MM/AAAA
    &cpv=79340,79341,…            (3-8 cifre, più codici separati da virgola)
    &sortField=dataPubblicazione&sortDirection=desc
    &operatore=AND
```

GET semplice, nessuna autenticazione, nessun WAF: a differenza del MePA non serve un
browser. L'endpoint è stato trovato l'11 agosto 2026 leggendo il traffico della
*ricerca avanzata* del portale.

**Il filtro CPV lato server è ciò che rende sostenibile la scala nazionale.** ANAC
pubblica decine di migliaia di avvisi al mese; sui 111 prefissi CPV dei nove settori
restano poche centinaia a settimana. I prefissi stanno in `cpv_query` dentro
`dictionaries.py` e vengono spediti in gruppi da 12.

Due dettagli che contano:

- nella risposta il campo `cpv` è l'**etichetta** ("Servizi di organizzazione di
  eventi"), non il codice. Il codice lo conosciamo solo come filtro inviato, quindi i
  record escono con `cpv_filtrato_a_monte` e il cancello CPV locale li lascia passare;
- il campo `tipologia` distingue `INDAGINI_DI_MERCATO_SOTTO_SOGLIA`, `BANDI`,
  `RISULTATI`, `MODIFICHE_CONTRATTUALI`. La mappatura in *momento*
  (manifestazione / gara / esito) è in `fetch_anac.py`.

### Portale Appalti degli enti (seconda fonte)

Centinaia di enti usano lo stesso software (Maggioli / DigitalPA), con gli stessi indirizzi:

```
https://<dominio-ente>/PortaleAppalti/it/ppgare_avvisi_lista.wp
```

Pagine **HTML servite dal server**: niente JS, niente WAF. Ogni record è una sequenza di
coppie etichetta/valore ("Stazione appaltante :", "Tipologia :", "Titolo :", …) identiche
su tutte le installazioni anche quando cambia il tema grafico — per questo il parser
lavora sul testo e non sui selettori CSS.

**Perché serve, se c'è già ANAC.** ANAC copre ciò che ha un CIG e passa dalla pubblicità
legale. Il portale dell'ente pubblica anche quello che lì non arriva, ed è proprio la
parte interessante: le *richieste di preventivo* che precedono un affidamento diretto, e
gli *albi di operatori qualificati* sempre aperti — la lista da cui l'ente pesca quando
affida per chiamata. Iscriversi a quelli è il vero lavoro di acquisizione.

**La lista dei portali si costruisce da sola.** Ogni record ANAC porta
`documenti_di_gara_link`, che punta al portale della stazione appaltante: girando i link
degli avvisi che rientrano nei nostri CPV si ottiene l'elenco degli enti che *comprano
davvero* i nostri servizi. `fetch_portali.py --scopri` aggiorna `data/portali.json` a
ogni run, senza curatela manuale.

### MePA · vetrina delle RDO aperte (terza fonte)

```
POST https://www.acquistinretepa.it/publicservices/vetrineservices/getAltriBandiRdoAperte
```

Nessuna autenticazione, ma il WAF FortiWeb rifiuta le chiamate senza sessione browser:
da qui Playwright. Il corpo della richiesta è in `corpo_richiesta()`; il servizio valida
l'intera struttura e risponde 400 se manca un campo.

Copre solo le RDO **aperte al mercato**: le RDO a invito e le trattative diritte non
compaiono. Il canale è strutturalmente sbilanciato sulla ristorazione — nella prima
estrazione reale (6 agosto 2026) su 465 RDO aperte erano pertinenti 23, di cui 19
catering, 3 eventi e 1 consulenza.

Le fonti sono indipendenti: se una cade il run continua con le altre e lo segnala.
Si ferma solo se cadono tutte.

---

## Classificazione

`scraper/classify.py` assegna a ogni pubblicazione un punteggio 0–100 per ciascuno dei
nove settori, combinando codice o etichetta CPV, categoria, parole chiave "forti" nel
titolo e nel testo, parole affini. Sottrae punti sui termini che segnalano forniture o
lavori, e azzera sui falsi amici.

Entra in dashboard solo chi supera **30 punti** *e* contiene almeno un termine forte.
La società segue il settore vincente; se un settore secondario appartiene a un'altra
società del gruppo, la scheda lo dice ("anche Joule").

Tre regole imparate sui bandi veri, da non smontare:

- **La categoria non è un termine forte.** Su ANAC la categoria è l'etichetta del CPV:
  contarla anche fra i termini forti aprirebbe il cancello a qualunque record classificato
  sotto quel CPV, teleselling e merchandising compresi. Vale 20 punti come categoria e basta.
- **Il CPV 79340 (pubblicità e marketing) è pieno di falsi amici.** I ricorrenti:
  l'imposta di pubblicità e le pubbliche affissioni (è un servizio di riscossione
  tributi), la comunicazione elettronica (è telefonia), la concessione degli impianti
  pubblicitari, il call center, la comunicazione aumentativa alternativa (è un servizio
  per la disabilità). Stanno tutti nelle esclusioni del settore comunicazione.
- **Gli avvisi di sponsorizzazione sono l'opposto di un'opportunità**: lì l'ente cerca
  qualcuno che gli dia dei soldi. Stanno in `ESCLUSIONI_GLOBALI`, che azzerano ogni settore.

---

## Messa in funzione

### 1. Repository

```bash
cd mepa-radar
git init -b main
git add .
git commit -m "Radar appalti: ANAC + MePA, 4x4 e Joule"
git remote add origin https://github.com/bertanipaolo-cloud/mepa-radar.git
git push -u origin main
```

### 2. GitHub Pages

*Settings → Pages → Source: Deploy from a branch → Branch `main`, cartella `/docs`.*

### 3. Email (facoltativa)

*Settings → Secrets and variables → Actions → New repository secret*:

| Secret | Valore per Gmail |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | l'indirizzo mittente |
| `SMTP_PASS` | una **password per le app** generata dall'account Google, non quella normale |
| `MAIL_TO` | destinatari del riepilogo completo, separati da virgola |
| `MAIL_TO_4X4` | *(facoltativo)* destinatari del solo digest 4x4 |
| `MAIL_TO_<SOCIETÀ>` | *(facoltativo)* destinatari del digest di una sola società: `MAIL_TO_4X4`, `MAIL_TO_JOULE`, `MAIL_TO_LATTA`, `MAIL_TO_NEW_FOOD`, `MAIL_TO_GABRINI`, `MAIL_TO_BEREBENE`, `MAIL_TO_ICARO`, `MAIL_TO_TOPIC` |

Se `MAIL_TO_JOULE` è impostato, a Joule arriva solo la sua parte: non ha senso far
leggere a chi fa comunicazione venti bandi di refezione scolastica.

Senza secret il workflow gira lo stesso e si limita ad aggiornare la dashboard.

### 4. Primo run

*Actions → Radar appalti → Run workflow.* Il primo run marca come "novità" tutto quello
che arriva da ANAC: è normale, serve a costruire lo storico. `data/storico.json` contiene
già le RDO MePA del 6–8 agosto.

---

## Manutenzione

Tutto il vocabolario sta in `scraper/dictionaries.py`, diviso per settore in `forti`
(qualificano da sole), `deboli` (contano in combinazione) ed `esclusioni` (azzerano).
Dopo ogni modifica:

```bash
python3 scraper/test_classify.py        # 56 casi sul classificatore
python3 scraper/test_cpv.py             # 22 casi sul cancello CPV
python3 scraper/test_anac.py            # estrazione PVL e smistamento 4x4 / Joule
python3 scraper/test_campione_reale.py  # 33 pubblicazioni ANAC vere dell'11/08/2026
python3 scraper/test_portali.py         # parser dei Portale Appalti e registro automatico
python3 scraper/test_estrazione.py      # estrattore MePA contro un finto portale locale
python3 scraper/run.py --demo           # rigenera la dashboard con dati dimostrativi
```

`test_campione_reale.py` è il test che conta quando si tocca Joule: sono i bandi che il
CPV 79340 porta davvero dentro, con tutti i loro falsi amici. Quando arriva un bando che
non doveva entrare, aggiungerlo alle `esclusioni` **e** al test; quando ne sfugge uno che
serviva, aggiungere la locuzione alle `forti` e fare lo stesso.

Il matching tollera plurali e ammette fino a due parole di collegamento fra i termini,
quindi «organizzazione eventi» intercetta anche «organizzazione e gestione degli eventi».
Attenzione all'over-stemming sulle parole corte: «palio» pescava «paline intelligenti».

**Se una fonte cambia.** Il workflow non sovrascrive la dashboard buona e allega un
artifact `diagnostica-radar` con HTML e screenshot. `data/endpoint.json` conserva
l'ultima chiamata MePA funzionante.

**Soglia e pesi** stanno in cima a `scraper/classify.py`.

---

## Struttura

```
scraper/
  fetch_anac.py            estrazione dalla PVL ANAC (HTTP semplice)
  fetch_portali.py         rete dei Portale Appalti + registro automatico degli enti
  fetch_rdo.py             estrazione dalla vetrina MePA (Playwright)
  dictionaries.py          vocabolario dei nove settori: CPV, categorie, keyword, società
  classify.py              punteggio di pertinenza, cancello CPV, esclusioni globali
  run.py                   orchestrazione, storico, statistiche, separazione degli esiti
  dashboard.py             generatore della dashboard HTML
  digest.py                corpo delle email (completa + una per società)
  invia_email.py           invio SMTP
  test_*.py                casi di controllo
data/
  anac_grezzi.json         ultima estrazione ANAC
  portali_grezzi.json      ultima estrazione dai portali degli enti
  portali.json             registro dei portali, dedotto dai link di gara ANAC
  rdo_grezze.json          ultima estrazione MePA
  storico.json             memoria delle pubblicazioni già viste
  digest*.html             ultime email generate
docs/
  index.html               dashboard pubblicata
  data.json                dati in formato macchina per l'hub 4x4
```

---

## Limiti da tenere presenti

- **Il punteggio non è un giudizio di partecipabilità.** Importi, requisiti e termini
  vanno sempre verificati sulla scheda originale.
- **Gli importi MePA non sono affidabili**: diverse stazioni appaltanti compilano
  `valore` con un prezzo unitario, si trovano RDO da 0,69 €. Sotto i 1.000 € l'importo
  è mostrato con l'etichetta "da verificare" ed escluso dai totali.
- **Il radar vede solo ciò che viene pubblicato.** Sotto i 140.000 € l'ente può affidare
  direttamente senza alcun avviso preventivo: in quel caso l'unica via è essere già negli
  elenchi operatori e negli albi fornitori. Il radar serve a intercettare le chiamate che
  passano da un avviso, non a sostituire l'iscrizione.
- **Gli esiti non sono opportunità.** Stanno in fondo alla dashboard perché dicono quali
  enti comprano davvero questi servizi, da chi e a che prezzo — e quando il contratto in
  corso andrà rinnovato. È da lì che si costruisce la lista di chi contattare a freddo.
