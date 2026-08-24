"""
Invio del digest settimanale via SMTP.

Legge le credenziali dalle variabili d'ambiente (su GitHub arrivano dai Secrets):
  SMTP_HOST       es. smtp.gmail.com
  SMTP_PORT       465 (SSL) oppure 587 (STARTTLS)
  SMTP_USER       indirizzo mittente
  SMTP_PASS       password per app / token SMTP
  MAIL_TO         destinatari del riepilogo completo, separati da virgola
  MAIL_TO_<SOCIETA> (facoltativo) destinatari del digest di quella societa':
                    MAIL_TO_4X4, MAIL_TO_JOULE, MAIL_TO_LATTA,
                    MAIL_TO_NEW_FOOD, MAIL_TO_GABRINI, MAIL_TO_BEREBENE,
                    MAIL_TO_ICARO, MAIL_TO_TOPIC
  MAIL_SEMPRE     se "1", invia anche quando non ci sono novita'

Se MAIL_TO_JOULE e' impostato, a Joule arriva solo la sua parte: non ha senso
far leggere a chi fa comunicazione venti forniture di derrate alimentari.

Se le variabili non ci sono, esce senza errore: la dashboard resta comunque
aggiornata e l'email si attiva quando i secret vengono configurati.
"""

import json
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dictionaries import SOCIETA, slug_societa  # noqa: E402

RADICE = Path(__file__).resolve().parent.parent
DATA = RADICE / "data"
DATI = RADICE / "docs" / "data.json"

# variabile d'ambiente -> (file digest, etichetta societa' o None per il completo)
# Un invio per societa', costruito dai dizionari invece che a mano: con otto
# societa' una lista scritta a mano si dimentica sempre l'ultima aggiunta.
# La variabile e' MAIL_TO_<SOCIETA> in maiuscolo con i trattini a underscore:
# MAIL_TO_4X4, MAIL_TO_JOULE, MAIL_TO_NEW_FOOD, MAIL_TO_LATTA...
INVII = [("MAIL_TO", DATA / "digest.html", None)]
for _societa in SOCIETA:
    _slug = slug_societa(_societa)
    INVII.append((f"MAIL_TO_{_slug.upper().replace('-', '_')}",
                  DATA / f"digest.{_slug}.html",
                  _societa))


def _destinatari(variabile):
    return [d.strip() for d in os.environ.get(variabile, "").split(",") if d.strip()]


def _oggetto(percorso, ripiego):
    f = percorso.with_suffix(".oggetto.txt")
    if f.exists():
        testo = f.read_text(encoding="utf-8").strip()
        if testo:
            return testo
    return ripiego


def _conta(meta, societa):
    if societa is None:
        return meta.get("nuovi", 0)
    return (meta.get("per_societa", {}).get(societa, {}) or {}).get("nuovi", 0)


def _spedisci(host, porta, user, pwd, msg):
    contesto = ssl.create_default_context()
    if porta == 465:
        with smtplib.SMTP_SSL(host, porta, context=contesto, timeout=60) as s:
            s.login(user, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, porta, timeout=60) as s:
            s.starttls(context=contesto)
            s.login(user, pwd)
            s.send_message(msg)


def main():
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    pwd = os.environ.get("SMTP_PASS")
    sempre = os.environ.get("MAIL_SEMPRE") == "1"

    # Il controllo delle credenziali viene prima di qualunque conversione:
    # su GitHub Actions un secret non configurato non e' assente, e' presente
    # e vuoto. Leggere la porta prima di qui faceva fallire il passo con un
    # ValueError invece di saltare l'invio come previsto.
    if not (host and user and pwd):
        print("[email] credenziali SMTP non configurate: salto l'invio")
        return 0

    # Stessa ragione: "or" al posto del default di get(), che con la stringa
    # vuota non scatta.
    grezza = (os.environ.get("SMTP_PORT") or "465").strip()
    try:
        porta = int(grezza)
    except ValueError:
        print(f"[email] SMTP_PORT non e' un numero ({grezza!r}): uso 465",
              file=sys.stderr)
        porta = 465
    if not DATI.exists():
        print("[email] manca docs/data.json: eseguire prima scraper/run.py", file=sys.stderr)
        return 1

    meta = json.loads(DATI.read_text(encoding="utf-8"))["meta"]

    inviate = 0
    problemi = 0
    for variabile, percorso, societa in INVII:
        destinatari = _destinatari(variabile)
        if not destinatari:
            continue
        if not percorso.exists():
            print(f"[email] manca {percorso.name}: salto {variabile}", file=sys.stderr)
            problemi += 1
            continue

        nuovi = _conta(meta, societa)
        if nuovi == 0 and not sempre:
            print(f"[email] {variabile}: nessuna novità, nessun invio "
                  f"(MAIL_SEMPRE=1 per forzarlo)")
            continue

        etichetta = societa or "gruppo 4x4"
        oggetto = _oggetto(percorso, f"Radar appalti {etichetta} · {nuovi} nuove opportunità")
        if societa is None and meta.get("in_scadenza_7gg"):
            oggetto += f" · {meta['in_scadenza_7gg']} in scadenza"

        msg = EmailMessage()
        msg["Subject"] = oggetto
        msg["From"] = user
        msg["To"] = ", ".join(destinatari)
        msg.set_content(
            f"{nuovi} nuove opportunità per {etichetta} questa settimana.\n"
            f"{meta.get('manifestazioni', 0)} manifestazioni d'interesse aperte in totale.\n"
            "Apri la dashboard per il dettaglio.\n"
        )
        msg.add_alternative(percorso.read_text(encoding="utf-8"), subtype="html")

        try:
            _spedisci(host, porta, user, pwd, msg)
        except Exception as e:
            print(f"[email] {variabile}: invio fallito: {type(e).__name__}: {e}", file=sys.stderr)
            problemi += 1
            continue
        inviate += 1
        print(f"[email] {variabile}: inviata a {len(destinatari)} destinatari · {oggetto}")

    if not inviate and not problemi:
        print("[email] nessun destinatario configurato "
              "(MAIL_TO oppure MAIL_TO_<SOCIETA>)")
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
