"""
Corpo dell'email settimanale: solo le novità e le scadenze imminenti.
HTML sobrio, compatibile con i client di posta (tabelle e stili inline).

Il digest e' diviso per societa': dal 24/08/2026 sono otto (4x4, Joule, Latta,
New Food, Gabrini, Berebene, Icaro, Topic). Oltre al riepilogo completo viene
scritto un digest per singola societa', cosi' a ciascuna arriva solo quello che
la riguarda (vedi invia_email.py, variabili MAIL_TO_<SOCIETA>).

Dentro ogni sezione le **manifestazioni d'interesse** vengono prima delle gare:
sono l'unico momento in cui si entra in una procedura negoziata, e hanno
termini corti.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dictionaries import SETTORI, slug_societa  # noqa: E402

# I colori vengono dai dizionari, non riscritti a mano: erano quattro fissi e
# con nove settori i cinque nuovi sarebbero rimasti grigi nel digest.
COLORI = {chiave: info["colore"] for chiave, info in SETTORI.items()}

FONT = "system-ui,-apple-system,Segoe UI,sans-serif"


def _euro(n):
    if n is None:
        return "importo n.d."
    return "€ " + f"{n:,.0f}".replace(",", ".")


def _data(s):
    if not s:
        return "—"
    a, m, g = s.split("-")
    return f"{g}/{m}/{a}"


def _riga(o, meta):
    colore = COLORI.get(o.get("settore"), "#52514e")
    etichetta = meta["per_settore"].get(o.get("settore"), {}).get("etichetta", "—")
    g = o.get("giorni_alla_scadenza")
    scad = f"scade il {_data(o.get('scadenza'))}"
    if g is not None:
        scad += f" · fra {g} {'giorno' if g == 1 else 'giorni'}"

    bollino = ""
    if o.get("momento") == "manifestazione":
        bollino = (f'<span style="display:inline-block;background:#8b5cf6;color:#fff;'
                   f'border-radius:999px;padding:2px 9px;font:600 11px {FONT};'
                   f'margin-right:8px;vertical-align:1px;">Manifestazione d\'interesse</span>')

    link_gara = ""
    if o.get("link_gara"):
        link_gara = (f'<div style="font:12.5px/1.6 {FONT};color:#898781;margin-top:4px;">'
                     f'documenti: <a href="{o["link_gara"]}" style="color:#52514e;">'
                     f'{o["link_gara"][:70]}</a></div>')

    return f"""
    <tr><td style="padding:14px 0;border-bottom:1px solid #e1e0d9;">
      <div style="font:600 15px/1.4 {FONT};color:#0b0b0b;margin-bottom:6px;">
        {bollino}<a href="{o.get('url', '')}" style="color:#0b0b0b;text-decoration:none;">{o.get('titolo', '')}</a>
      </div>
      <div style="font:13px/1.6 {FONT};color:#52514e;">
        <span style="display:inline-block;width:9px;height:9px;border-radius:50%;
                     background:{colore};margin-right:6px;"></span>{etichetta}
        · {o.get('punteggio', 0)}/100 &nbsp;|&nbsp; {o.get('ente') or o.get('stazione_appaltante') or 'ente n.d.'}
        &nbsp;|&nbsp; {_euro(o.get('valore'))} &nbsp;|&nbsp; {scad}
        &nbsp;|&nbsp; {o.get('fonte', 'MePA')}
      </div>
      {link_gara}
    </td></tr>"""


def _prima_le_manifestazioni(righe):
    return sorted(righe, key=lambda o: (
        0 if o.get("momento") == "manifestazione" else 1,
        -(o.get("punteggio") or 0),
    ))


def _sezione(titolo, righe, meta, limite):
    if not righe:
        return ""
    righe = _prima_le_manifestazioni(righe)[:limite]
    return (f'<h2 style="font:600 16px {FONT};color:#0b0b0b;margin:28px 0 4px;">{titolo}</h2>'
            f'<table width="100%" cellpadding="0" cellspacing="0">'
            f'{"".join(_riga(o, meta) for o in righe)}</table>')


def costruisci(payload, societa=None):
    """
    Corpo HTML del digest. Con `societa` valorizzata considera solo le
    opportunita' di quella societa'; senza, le mette tutte divise per sezione.
    """
    meta = payload["meta"]
    opp = [o for o in payload["opportunita"]
           if societa is None or o.get("societa") == societa]

    nuove = [o for o in opp if o.get("nuovo")]
    urgenti = [o for o in opp
               if not o.get("nuovo")
               and o.get("giorni_alla_scadenza") is not None
               and 0 <= o["giorni_alla_scadenza"] <= 7]
    manifestazioni = [o for o in nuove if o.get("momento") == "manifestazione"]

    sezioni = ""
    if societa is None:
        # Riepilogo completo: una sezione di novita' per societa'.
        for chiave in (meta.get("per_societa") or {}):
            righe = [o for o in nuove if o.get("societa") == chiave]
            etichetta = meta["per_societa"][chiave]["etichetta"]
            descrizione = meta["per_societa"][chiave]["descrizione"]
            sezioni += _sezione(f"Novità per {etichetta} — {descrizione}", righe, meta, 20)
    else:
        sezioni += _sezione("Novità di questa settimana", nuove, meta, 25)

    sezioni += _sezione("Già segnalate, in scadenza entro 7 giorni", urgenti, meta, 15)

    if not sezioni:
        sezioni = (f'<p style="font:14px/1.6 {FONT};color:#52514e;">'
                   "Nessuna nuova opportunità pertinente questa settimana e nessuna scadenza "
                   "imminente fra quelle già segnalate.</p>")

    if societa is None:
        titolo = "Radar appalti · gruppo 4x4"
        riepilogo = " · ".join(
            f"{v['etichetta']}: {v['totale']}" for v in (meta.get("per_societa") or {}).values())
        totale_aperte = meta["attivi"]
    else:
        titolo = f"Radar appalti · {societa}"
        riepilogo = " · ".join(
            f"{v['etichetta']}: {v['totale']}"
            for k, v in meta["per_settore"].items()
            if meta.get("settore_societa", {}).get(k) == societa and v["totale"])
        totale_aperte = len(opp)

    nota_manifestazioni = ""
    if manifestazioni:
        nota_manifestazioni = (
            f'<div style="font:13.5px/1.6 {FONT};color:#0b0b0b;background:#f3efff;'
            f'border-left:3px solid #8b5cf6;padding:10px 14px;margin:18px 0 0;">'
            f'<b>{len(manifestazioni)}</b> '
            f'{"manifestazione d’interesse" if len(manifestazioni) == 1 else "manifestazioni d’interesse"} '
            f'questa settimana: sono avvisi con cui l’ente sceglie chi invitare alla procedura '
            f'negoziata. Hanno termini brevi ed è l’unico momento utile per entrare.</div>')

    return f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f9f9f7;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9f9f7;padding:24px 12px;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0"
       style="background:#fcfcfb;border:1px solid rgba(11,11,11,0.10);border-radius:12px;padding:28px 30px;">
  <tr><td>
    <div style="font:600 20px {FONT};color:#0b0b0b;">{titolo}</div>
    <div style="font:14px/1.6 {FONT};color:#52514e;margin-top:6px;">
      <b>{len(nuove)}</b> nuove opportunità · <b>{totale_aperte}</b> aperte in totale ·
      <b>{len(urgenti)}</b> in scadenza entro 7 giorni<br>
      {riepilogo}
    </div>
    {nota_manifestazioni}
    {sezioni}
    <p style="font:12.5px/1.7 {FONT};color:#898781;margin-top:28px;">
      Punteggio di pertinenza 0–100 calcolato su codice CPV, categoria e parole chiave;
      entrano solo le pubblicazioni sopra {meta.get('soglia', 30)} punti. Fonti: Piattaforma di
      Pubblicità a Valore Legale di ANAC e vetrina RDO del MePA. Verificare sempre requisiti e
      termini sulla scheda originale.<br>
      Aggiornato al {meta.get('aggiornato_testo') or meta.get('aggiornato', '')}.
    </p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""


def _oggetto(payload, societa=None):
    opp = [o for o in payload["opportunita"]
           if societa is None or o.get("societa") == societa]
    nuove = [o for o in opp if o.get("nuovo")]
    manif = sum(1 for o in nuove if o.get("momento") == "manifestazione")
    prefisso = "Radar appalti" + (f" {societa}" if societa else "")
    if not nuove:
        return f"{prefisso} · nessuna novità questa settimana"
    pezzi = [f"{len(nuove)} nuove opportunità"]
    if manif:
        pezzi.append(f"{manif} manifestazion{'e' if manif == 1 else 'i'} d'interesse")
    return f"{prefisso} · " + " · ".join(pezzi)


def scrivi_digest(payload, destinazione: Path):
    """
    Scrive il digest complessivo e, accanto, uno per societa'
    (digest.4x4.html, digest.new-food.html, ...) con il rispettivo oggetto.
    """
    destinazione.write_text(costruisci(payload), encoding="utf-8")
    destinazione.with_suffix(".oggetto.txt").write_text(_oggetto(payload), encoding="utf-8")

    for societa in (payload["meta"].get("per_societa") or {}):
        parziale = destinazione.with_name(
            f"{destinazione.stem}.{slug_societa(societa)}.html")
        parziale.write_text(costruisci(payload, societa), encoding="utf-8")
        parziale.with_suffix(".oggetto.txt").write_text(
            _oggetto(payload, societa), encoding="utf-8")

    return destinazione
