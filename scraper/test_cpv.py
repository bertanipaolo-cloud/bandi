"""
Prova del cancello CPV, che serve alle fonti dove il CPV c'e' (ANAC).

Sul MePA il CPV non viene esposto e il cancello resta inerte: i casi "assente"
verificano proprio che non cambi nulla per la fonte attuale.

  python3 scraper/test_cpv.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from classify import classifica, stato_cpv, SOGLIA_MINIMA  # noqa: E402

# (cpv, stato atteso del cancello)
STATI = [
    ([], "assente"),                       # MePA: nessun CPV, si va a keyword
    (["79411000-8"], "ammesso"),           # consulenza gestionale
    (["79952000-2"], "ammesso"),           # organizzazione eventi
    (["55520000-1"], "ammesso"),           # catering
    (["80532000-2"], "ammesso"),           # formazione manageriale
    (["45000000-7"], "escluso"),           # lavori di costruzione
    (["33600000-6"], "escluso"),           # farmaci
    (["34110000-1"], "escluso"),           # autovetture
    (["90500000-2"], "escluso"),           # rifiuti
    (["71241000-9"], "ammesso"),           # studi di fattibilita': eccezione in div. 71
    (["66171000-9"], "ammesso"),           # consulenza finanziaria: eccezione in div. 66
    (["79710000-4"], "dubbio"),            # vigilanza: div. 79 ma non nei nostri gruppi
    (["79620000-6"], "dubbio"),            # fornitura di personale
    (["45000000-7", "79400000-8"], "ammesso"),  # basta un CPV buono
    (["45000000-7", "33600000-6"], "escluso"),  # tutti fuori perimetro
]

# (titolo, cpv, settore atteso dopo il cancello)
ESITI = [
    ("Servizio di supporto specialistico per l'attuazione del PNRR",
     ["79411000-8"], "consulenza"),
    ("Affidamento del servizio di catering per eventi istituzionali",
     ["55520000-1"], "catering"),
    ("Organizzazione degli eventi culturali estivi",
     ["79952000-2"], "eventi"),
    # CPV fuori perimetro: cade anche con un titolo invitante
    ("Servizio di supporto specialistico alla direzione lavori",
     ["45000000-7"], None),
    ("Fornitura pasti e supporto specialistico logistico",
     ["33690000-3"], None),
    # zona grigia: passa solo se il titolo qualifica esplicitamente
    ("Servizio di consulenza direzionale e riorganizzazione",
     ["79710000-4"], "consulenza"),
    ("Servizi vari a supporto degli uffici",
     ["79710000-4"], None),
]


def main():
    errori = 0
    for cpv, atteso in STATI:
        got = stato_cpv({"cpv": cpv})
        ok = got == atteso
        errori += not ok
        print(f"{'OK ' if ok else 'ERR'} | {str(cpv):<32} -> {got} (atteso {atteso})")

    print()
    for titolo, cpv, atteso in ESITI:
        r = classifica({"titolo": titolo, "cpv": cpv, "categorie": [],
                        "descrizione": "", "ente": "", "stazione_appaltante": ""})
        got = r["settore"] if r["punteggio"] >= SOGLIA_MINIMA else None
        ok = got == atteso
        errori += not ok
        print(f"{'OK ' if ok else 'ERR'} | {r['cancello_cpv']:<8} {str(got):<11} "
              f"{r['punteggio']:>3} | {titolo[:58]}")
        if not ok:
            print(f"      motivi: {r['motivi']}")

    totale = len(STATI) + len(ESITI)
    print(f"\n{totale - errori}/{totale} corretti, {errori} errori")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
