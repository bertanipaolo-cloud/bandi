"""
Test del parser dei Portale Appalti.

La fixture riproduce l'HTML della pagina avvisi del Comune di Brescia
(infogare.comune.brescia.it, letta l'11 agosto 2026): stesse etichette, stessi
valori, struttura ridotta a due temi grafici diversi per verificare che il
parser regga il cambio di markup — lavora sul testo, non sui selettori.

    python3 scraper/test_portali.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch_portali import analizza, scopri_portali  # noqa: E402

BASE = "https://infogare.comune.brescia.it/PortaleAppalti/"

# Tema 1: tabella, come lo rende l'installazione di Brescia.
HTML_TABELLA = """
<html><body><div id="contenuti">
<p>La ricerca ha restituito 44 risultati.</p>
<table><tr><td>
  <strong>Stazione appaltante :</strong></td><td>SETTORE SERVIZI SOCIALI</td></tr>
<tr><td><strong>Tipologia :</strong></td><td>Manifestazione di Interesse</td></tr>
<tr><td><strong>Titolo :</strong></td><td>PROCEDURA FINALIZZATA ALLA SELEZIONE DI OPERATORI
  PER LA GESTIONE DI SOGGIORNI CLIMATICI PER ANZIANI ANNI 2026-2028</td></tr>
<tr><td><strong>Avviso per :</strong></td><td>Servizi</td></tr>
<tr><td><strong>Data pubblicazione :</strong></td><td>12/01/2026</td></tr>
<tr><td><strong>Data scadenza :</strong></td><td>31/12/2028</td></tr>
<tr><td><strong>Riferimento procedura :</strong></td><td>A01104</td></tr>
<tr><td><strong>Stato :</strong></td><td>In corso</td></tr>
<tr><td><a href="ppgare_avvisi_scheda.wp?id=1">Visualizza scheda</a></td></tr>
</table>
<table><tr><td>
  <strong>Stazione appaltante :</strong></td><td>SETTORE SVILUPPO ECONOMICO E SUAP</td></tr>
<tr><td><strong>Tipologia :</strong></td><td>Altro</td></tr>
<tr><td><strong>Titolo :</strong></td><td>PROGETTO LUCE IN CITTA'. PROCEDURA ESPLORATIVA
  FINALIZZATA ALLA RACCOLTA DI PROPOSTE PROGETTUALI DESTINATE ALLA VALORIZZAZIONE
  TERRITORIALE IN OCCASIONE DELLE FESTIVITA NATALIZIE 2026/2027</td></tr>
<tr><td><strong>Avviso per :</strong></td><td>Servizi</td></tr>
<tr><td><strong>Data pubblicazione :</strong></td><td>01/06/2026</td></tr>
<tr><td><strong>Data scadenza :</strong></td><td>15/09/2026</td></tr>
<tr><td><strong>Riferimento procedura :</strong></td><td>A01133</td></tr>
<tr><td><strong>Stato :</strong></td><td>In corso</td></tr>
</table>
<table><tr><td>
  <strong>Stazione appaltante :</strong></td><td>SETTORE SERVIZI SOCIALI</td></tr>
<tr><td><strong>Tipologia :</strong></td><td>Altro</td></tr>
<tr><td><strong>Titolo :</strong></td><td>AVVISO RIVOLTO ALLA ACQUISIZIONE DI PREVENTIVI AL FINE
  DI PROCEDERE AD AFFIDAMENTO DIRETTO DEL SERVIZIO DI MAGAZZINAGGIO</td></tr>
<tr><td><strong>Avviso per :</strong></td><td>Servizi</td></tr>
<tr><td><strong>Data pubblicazione :</strong></td><td>26/09/2025</td></tr>
<tr><td><strong>Data scadenza :</strong></td><td>13/10/2026</td></tr>
<tr><td><strong>Riferimento procedura :</strong></td><td>A01077</td></tr>
<tr><td><strong>Stato :</strong></td><td>In corso</td></tr>
</table>
<table><tr><td>
  <strong>Stazione appaltante :</strong></td><td>SETTORE GARE</td></tr>
<tr><td><strong>Tipologia :</strong></td><td>Manifestazione di Interesse</td></tr>
<tr><td><strong>Titolo :</strong></td><td>AVVISO GIA' CHIUSO DA TEMPO</td></tr>
<tr><td><strong>Avviso per :</strong></td><td>Servizi</td></tr>
<tr><td><strong>Data pubblicazione :</strong></td><td>01/01/2025</td></tr>
<tr><td><strong>Data scadenza :</strong></td><td>01/02/2025</td></tr>
<tr><td><strong>Riferimento procedura :</strong></td><td>A00900</td></tr>
<tr><td><strong>Stato :</strong></td><td>Scaduto</td></tr>
</table>
</div></body></html>
"""

# Tema 2: liste di definizione, senza tabelle. Stesse etichette.
HTML_LISTE = """
<html><body><main>
<dl><dt>Stazione appaltante :</dt><dd>COMUNE DI VITERBO</dd>
<dt>Tipologia :</dt><dd>Indagine di mercato</dd>
<dt>Titolo :</dt><dd>Avviso per l'affidamento del servizio di ufficio stampa e
  gestione dei canali social</dd>
<dt>Avviso per :</dt><dd>Servizi</dd>
<dt>Data pubblicazione :</dt><dd>05/08/2026</dd>
<dt>Data scadenza :</dt><dd>05/09/2026</dd>
<dt>Riferimento procedura :</dt><dd>G00231</dd>
<dt>Stato :</dt><dd>In corso</dd></dl>
</main></body></html>
"""


def verifica():
    errori = []

    def check(c, m):
        if not c:
            errori.append(m)

    r = analizza(HTML_TABELLA, BASE)
    check(len(r) == 3, f"attesi 3 avvisi in corso (uno scaduto scartato), trovati {len(r)}")

    per_rif = {x["numero"]: x for x in r}
    check("A00900" not in per_rif, "l'avviso con Stato «Scaduto» non deve entrare")

    a = per_rif.get("A01104")
    check(a is not None, "A01104 non estratto")
    if a:
        check(a["momento"] == "manifestazione",
              f"A01104: momento {a['momento']}, la tipologia dichiara Manifestazione di Interesse")
        check(a["ente"] == "SETTORE SERVIZI SOCIALI", f"A01104: ente «{a['ente']}»")
        check(a["pubblicazione"] == "2026-01-12", f"A01104: pubblicazione {a['pubblicazione']}")
        check(a["scadenza"] == "2028-12-31", f"A01104: scadenza {a['scadenza']}")
        check(a["fonte"] == "Portale Appalti", "A01104: fonte")
        check("SOGGIORNI CLIMATICI" in a["titolo"],
              "il titolo su piu' righe deve essere ricomposto in una riga sola")

    # Il caso che giustifica questa fonte: il portale lo marca "Altro", ma e' il
    # pre-affidamento vero e proprio. Deve essere riconosciuto dal titolo.
    b = per_rif.get("A01077")
    check(b is not None and b["momento"] == "manifestazione",
          f"A01077 «acquisizione di preventivi per affidamento diretto»: "
          f"momento {b['momento'] if b else '—'}, atteso manifestazione")

    c = per_rif.get("A01133")
    check(c is not None and c["momento"] == "manifestazione",
          "A01133 «procedura esplorativa» deve valere come manifestazione")

    # Tema grafico diverso, stesse etichette: il parser non deve accorgersene.
    r2 = analizza(HTML_LISTE, BASE)
    check(len(r2) == 1, f"tema a liste: attesi 1 record, trovati {len(r2)}")
    if r2:
        check(r2[0]["momento"] == "manifestazione", "tema a liste: momento")
        check(r2[0]["ente"] == "COMUNE DI VITERBO", f"tema a liste: ente «{r2[0]['ente']}»")
        check(r2[0]["numero"] == "G00231", "tema a liste: riferimento")

    # Registro: si costruisce dai link di gara che ANAC gia' porta.
    finti = [
        {"link_gara": "https://www.sua-rb.it/PortaleAppalti/it/procedure/codice/G00564",
         "ente": "REGIONE BASILICATA"},
        {"link_gara": "https://www.sua-rb.it/PortaleAppalti/it/procedure/codice/G00999",
         "ente": "REGIONE BASILICATA"},
        {"link_gara": "https://appalti.comune.ra.it/PortaleAppalti/it/procedure/codice/G02293",
         "ente": "COMUNE DI RAVENNA"},
        {"link_gara": "https://start.toscana.it/tendering/tenders/012299-2026",
         "ente": "COMUNE DI LASTRA A SIGNA"},
    ]
    percorso = Path(__file__).resolve().parent.parent / "data" / "_test_anac.json"
    percorso.parent.mkdir(parents=True, exist_ok=True)
    import json as _json
    percorso.write_text(_json.dumps(finti), encoding="utf-8")
    try:
        registro = scopri_portali(percorso)
    finally:
        percorso.unlink(missing_ok=True)

    check(len(registro) == 2,
          f"attesi 2 portali distinti (start.toscana non è un Portale Appalti), "
          f"trovati {len(registro)}: {sorted(registro)}")
    check("https://www.sua-rb.it/PortaleAppalti/" in registro,
          "il registro deve dedurre la base del portale dal link di gara")

    return errori


if __name__ == "__main__":
    errori = verifica()
    if errori:
        print(f"✗ {len(errori)} problemi:\n")
        for e in errori:
            print(f"  · {e}")
        sys.exit(1)
    print("✓ parser Portale Appalti e registro automatico: tutti i casi verdi")
