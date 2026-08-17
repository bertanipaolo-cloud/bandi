"""
Classificazione e punteggio delle RDO MePA rispetto ai settori di 4x4.

Formula del punteggio (0-100) per settore:
    +45  se almeno una keyword "forte" compare nel titolo
    +30  se almeno una keyword "forte" compare nella descrizione/categoria
    +25  se il CPV del lotto ha un prefisso nella lista del settore
    +20  se la categoria merceologica MePA e' fra quelle del settore
    +4   per ogni keyword "debole" distinta trovata (max 20)
    -15  per ogni penalita' globale trovata (max -30)
     0   (azzerato) se compare una keyword di esclusione del settore
         SENZA che compaia anche una keyword forte dello stesso settore

Il record finale porta:
    punteggi      -> dict settore -> punteggio
    settore       -> settore con punteggio piu' alto
    punteggio     -> punteggio del settore vincente
    fascia        -> alta / media / bassa
    motivi        -> spiegazione leggibile del match
"""

import re
import unicodedata

from dictionaries import (SETTORI, PENALITA_GLOBALI, SEGNALI_COMPLESSITA,
                          ESCLUSIONI_GLOBALI, CPV_ESCLUSI, CPV_ECCEZIONI,
                          societa_di)

# 45 titolo + 30 testo + 20 categoria + 20 affini, piu' 25 di CPV quando c'e'.
# La vetrina MePA non espone il CPV: normalizzare su 140 comprimerebbe tutti i
# punteggi verso il basso, quindi il massimo si calcola record per record.
PUNTEGGIO_BASE = 115
PUNTEGGIO_CPV = 25
PUNTEGGIO_MASSIMO = PUNTEGGIO_BASE + PUNTEGGIO_CPV
SOGLIA_MINIMA = 30       # sotto questa soglia l'opportunita' non entra in dashboard
FASCE = ((70, "alta"), (50, "media"), (SOGLIA_MINIMA, "bassa"))


def normalizza(testo):
    """minuscolo, senza accenti, spazi compattati, punteggiatura -> spazio."""
    if not testo:
        return ""
    testo = unicodedata.normalize("NFKD", str(testo))
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    testo = testo.lower()
    testo = re.sub(r"[^a-z0-9]+", " ", testo)
    return re.sub(r"\s+", " ", testo).strip()


VOCALI_FINALI = "aeiou"


def _radice(parola):
    """
    Stemming minimo per l'italiano: toglie la vocale finale, cosi' che
    'evento'/'eventi', 'manifestazione'/'manifestazioni', 'servizio'/'servizi'
    condividano la stessa radice. Le parole corte restano intatte.
    """
    if len(parola) >= 5 and parola[-1] in VOCALI_FINALI:
        return parola[:-1]
    return parola


def _pattern(termine_norm):
    """
    Costruisce il regex di un termine:
      - ogni parola e' ridotta a radice e puo' avere fino a 3 lettere di coda
        (plurali, femminili, forme flesse);
      - fra una parola e l'altra sono ammesse fino a 2 paroline di collegamento
        ('di', 'della', 'per', 'e'), cosi' 'organizzazione eventi' intercetta
        anche 'organizzazione di eventi' e 'organizzazione e gestione eventi'.
    """
    def pezzo(parola):
        r = _radice(parola)
        # La coda ammessa cresce con la lunghezza della radice: su parole corte
        # tre lettere libere fanno danni ("palio" -> "pali" -> "paline").
        coda = 3 if len(r) >= 6 else (1 if len(r) >= 4 else 0)
        return rf"{re.escape(r)}\w{{0,{coda}}}"

    parole = termine_norm.split()
    pezzi = [pezzo(p) for p in parole]
    collante = r"(?:\s+\w{1,7}){0,2}\s+"
    return r"\b" + collante.join(pezzi) + r"\b"


_CACHE_REGEX = {}


def _trova(termini, testo):
    """Ritorna i termini presenti nel testo (gia' normalizzato)."""
    if not testo:
        return []
    trovati = []
    for t in termini:
        tn = normalizza(t)
        if not tn:
            continue
        rx = _CACHE_REGEX.get(tn)
        if rx is None:
            rx = _CACHE_REGEX[tn] = re.compile(_pattern(tn))
        if rx.search(testo):
            trovati.append(t)
    return trovati


def _match_cpv(prefissi, cpv_list):
    for cpv in cpv_list:
        c = re.sub(r"\D", "", str(cpv or ""))
        if not c:
            continue
        for p in prefissi:
            if c.startswith(p.rstrip("0")) or c.startswith(p):
                return cpv
    return None


CPV_AMMESSI = sorted({c for s in SETTORI.values() for c in s["cpv"]})


def _cifre(cpv):
    return re.sub(r"\D", "", str(cpv or ""))


def stato_cpv(record):
    """
    Verdetto del cancello CPV, per le fonti che il CPV lo espongono.

      "assente"  -> il record non ha CPV (e' il caso del MePA): si va a keyword
      "ammesso"  -> almeno un CPV rientra in uno dei tre settori
      "escluso"  -> tutti i CPV stanno in divisioni fuori perimetro
      "dubbio"   -> CPV presente ma in zona grigia: serve un termine forte

    Le eccezioni battono le esclusioni: 66171 (consulenza finanziaria) passa
    anche se l'intera divisione 66 e' esclusa.
    """
    # ANAC filtra gia' per CPV lato server e restituisce l'etichetta, non il
    # codice: il cancello locale sarebbe cieco proprio dove il filtro e' piu'
    # affidabile. Chi ha gia' passato il filtro alla fonte entra come "ammesso".
    if record.get("cpv_filtrato_a_monte"):
        return "ammesso"

    cpv = [_cifre(c) for c in (record.get("cpv") or [])]
    cpv = [c for c in cpv if c]
    if not cpv:
        return "assente"

    for c in cpv:
        if any(c.startswith(e) for e in CPV_ECCEZIONI):
            return "ammesso"
        if any(c.startswith(p.rstrip("0")) or c.startswith(p) for p in CPV_AMMESSI):
            return "ammesso"
    if all(c[:2] in CPV_ESCLUSI for c in cpv):
        return "escluso"
    return "dubbio"


def punteggio_settore(record, chiave, settore):
    # Le RDO di "Lavori" sono appalti edili: nessuno dei tre settori li tocca.
    if normalizza(record.get("tipo")) == "lavori":
        return 0, ["natura: lavori"]

    titolo = normalizza(record.get("titolo"))
    # La categoria (su ANAC e' l'etichetta del CPV, es. "Servizi di marketing")
    # sta fuori dal corpo: vale gia' 20 punti come categoria, e lasciarla anche
    # fra i termini forti aprirebbe il cancello a qualunque record classificato
    # sotto quel CPV — teleselling e merchandising compresi.
    corpo = normalizza(
        " ".join(
            filter(
                None,
                [
                    record.get("descrizione"),
                    record.get("stazione_appaltante"),
                    record.get("ente"),
                    " ".join(record.get("tag") or []),
                ],
            )
        )
    )
    categorie_norm = normalizza(" ".join(record.get("categorie") or []))
    tutto = f"{titolo} {corpo} {categorie_norm}"

    forti_titolo = _trova(settore["forti"], titolo)
    forti_corpo = _trova(settore["forti"], corpo)
    escl_titolo = _trova(settore["esclusioni"], titolo)
    escl_corpo = _trova(settore["esclusioni"], corpo)

    # Un'esclusione nel titolo vince sempre: "eventi avversi" o "buoni pasto
    # elettronici" restano fuori anche se il titolo contiene termini forti.
    if escl_titolo:
        return 0, [f"escluso dal titolo: {escl_titolo[0]}"]
    # Un'esclusione nel corpo vince solo se il titolo non qualifica il bando
    # (es. "catering" nel titolo e "noleggio tovagliato" fra i dettagli).
    if escl_corpo and not forti_titolo:
        return 0, [f"escluso: {escl_corpo[0]}"]

    # Gate: senza almeno un termine "forte" non si entra. Categoria merceologica
    # e parole affini, da sole, descrivono un'affinita' generica - non un bando
    # su cui ha senso lavorare. Senza questo filtro passerebbero gli acquisti di
    # integratori ospedalieri (categoria "Alimenti" + qualche parola comune).
    if not forti_titolo and not forti_corpo:
        return 0, []

    punti = 0
    motivi = []

    if forti_titolo:
        punti += 45
        motivi.append(f"titolo: «{forti_titolo[0]}»")
    if forti_corpo:
        punti += 30
        # non ripetere lo stesso termine gia' segnalato nel titolo
        altro = next((f for f in forti_corpo if f not in forti_titolo), None)
        if altro:
            motivi.append(f"testo: «{altro}»")

    cpv_hit = _match_cpv(settore["cpv"], record.get("cpv") or [])
    if cpv_hit:
        punti += 25
        motivi.append(f"CPV {cpv_hit}")

    cat_hit = next((c for c in settore["categorie"] if normalizza(c) in categorie_norm), None)
    if cat_hit:
        punti += 20
        motivi.append(f"categoria MePA: {cat_hit}")

    deboli = set(_trova(settore["deboli"], tutto))
    if deboli:
        bonus = min(len(deboli) * 4, 20)
        punti += bonus
        motivi.append(f"{len(deboli)} termini affini")

    penalita = _trova(PENALITA_GLOBALI, tutto)
    if penalita:
        malus = min(len(penalita) * 15, 30)
        punti -= malus
        motivi.append(f"penalita: {penalita[0]}")

    # Scala 0-100 sul massimo che *questo* record poteva raggiungere.
    massimo = PUNTEGGIO_BASE + (PUNTEGGIO_CPV if record.get("cpv") else 0)
    return max(0, round(min(massimo, punti) / massimo * 100)), motivi


def classifica(record):
    """Arricchisce il record con punteggi, settore vincente e fascia."""
    cancello = stato_cpv(record)

    # Esclusioni valide per tutti i settori: qui non c'e' niente da vendere,
    # qualunque sia il mestiere. Si controllano prima di ogni punteggio.
    testo_globale = normalizza(
        f"{record.get('titolo')} {record.get('descrizione')}")
    fuori = _trova(ESCLUSIONI_GLOBALI, testo_globale)
    if fuori:
        record = dict(record)
        record["punteggi"] = {k: 0 for k in SETTORI}
        record["settore"] = None
        record["societa"] = None
        record["punteggio"] = 0
        record["fascia"] = None
        record["motivi"] = [f"fuori perimetro: {fuori[0]}"]
        record["settori_secondari"] = []
        record["note_complessita"] = []
        record["cancello_cpv"] = cancello
        record.setdefault("fonte", "MePA")
        return record

    punteggi = {}
    motivi_per_settore = {}
    for chiave, settore in SETTORI.items():
        p, m = punteggio_settore(record, chiave, settore)
        punteggi[chiave] = p
        motivi_per_settore[chiave] = m

    # Cancello CPV, applicato dopo il punteggio cosi' resta tracciabile il perche'.
    if cancello == "escluso":
        punteggi = {k: 0 for k in punteggi}
        motivi_per_settore = {k: ["CPV fuori perimetro"] for k in motivi_per_settore}
    elif cancello == "dubbio":
        # zona grigia: si passa solo se il titolo dichiara esplicitamente il settore
        for k, m in motivi_per_settore.items():
            if not any(x.startswith("titolo:") for x in m):
                punteggi[k] = 0
                motivi_per_settore[k] = ["CPV in zona grigia, titolo non qualificante"]

    settore = max(punteggi, key=punteggi.get)
    punteggio = punteggi[settore]

    fascia = None
    for soglia, nome in FASCE:
        if punteggio >= soglia:
            fascia = nome
            break

    testo_tutto = normalizza(
        f"{record.get('titolo')} {record.get('descrizione')} {' '.join(record.get('categorie') or [])}"
    )
    complessita = _trova(SEGNALI_COMPLESSITA, testo_tutto)

    record = dict(record)
    record["punteggi"] = punteggi
    record["settore"] = settore if punteggio > 0 else None
    record["punteggio"] = punteggio
    record["fascia"] = fascia
    record["societa"] = societa_di(settore) if punteggio > 0 else None
    record["motivi"] = motivi_per_settore.get(settore, [])
    # settori secondari con punteggio comunque significativo
    record["settori_secondari"] = [
        s for s, p in punteggi.items() if s != settore and p >= SOGLIA_MINIMA
    ]
    record["note_complessita"] = complessita
    record["cancello_cpv"] = cancello
    record.setdefault("fonte", "MePA")
    return record


def filtra(records):
    """Classifica tutti i record e tiene solo quelli sopra soglia."""
    classificati = [classifica(r) for r in records]
    tenuti = [r for r in classificati if r["punteggio"] >= SOGLIA_MINIMA]
    tenuti.sort(key=lambda r: (-r["punteggio"], r.get("scadenza") or "9999"))
    return tenuti, classificati
