"""
Prova end-to-end dell'estrattore contro un finto MePA servito in locale.

Non tocca la rete: monta un server che imita la vetrina reale (pagina AngularJS
che chiede la lista via XHR POST paginata, payload annidato come quello vero) e
verifica che fetch_rdo.py intercetti la chiamata, la rigiochi su tutte le pagine
e normalizzi correttamente date, importi, categorie e link.

  python3 scraper/test_estrazione.py
"""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
PORTA = 8731
TOTALE = 25

PAGINA = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>finta vetrina</title></head>
<body><div id="esito">caricamento</div>
<script>
// come il portale vero: la lista arriva da una XHR dopo il caricamento
fetch('/publicservices/vetrineservices/getAltriBandiRdoAperte', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({isArchive: false, paginazione: {pagina: 1, itemPagina: 20}})
}).then(r => r.json()).then(d => {
  document.getElementById('esito').textContent = 'ricevuti ' + d.payload.elencoBandi.length;
});
</script></body></html>"""


def finto_bando(i):
    """Record modellato sui nomi di campo reali della vetrina MePA."""
    return {
        "idBando": f"id{i:04d}",
        "numeroRdo": 4500000 + i,
        "cdSigef": f"SIGEF{i}",
        "strumento": "RDO Aperte",
        "riassuntoBando": ["Servizi", "Servizi", "Servizi", "Beni", "Servizi"][i % 5],
        "titoloBando": [
            "Servizio di catering e coffee break per gli eventi istituzionali",
            "Organizzazione e gestione integrata degli eventi dell'Ente",
            "Supporto specialistico al RUP per gli interventi PNRR",
            "Fornitura e posa in opera di arredi per gli uffici comunali",
            "Servizio di pulizia degli immobili comunali",
        ][i % 5],
        "descrizioneEnte": f"Comune di Prova {i}",
        "stazioneAppaltante": "Ufficio Gare e Contratti",
        "categorieMerceologiche": [
            {"descrizione": ["Ristorazione", "Servizi di organizzazione eventi",
                             "Servizi professionali", "Arredi", "Servizi di pulizia"][i % 5]}
        ],
        # tre formati di data e importo diversi, per provare i parser
        "dataPubblicazione": [1785000000000, "2026-07-15", "15/07/2026"][i % 3],
        "dataScadenzaBando": [1788000000000, "2026-09-30", "30/09/2026"][i % 3],
        "valore": ["12.500,00", "48000", 7500.5][i % 3],
        "tags": [{"label": "verde"}],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        corpo = PAGINA.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        richiesta = json.loads(self.rfile.read(n) or "{}")
        pag = richiesta.get("paginazione") or {}
        pagina = int(pag.get("pagina", 1))
        size = int(pag.get("itemPagina", 20))
        inizio = (pagina - 1) * size
        fetta = [finto_bando(i) for i in range(inizio, min(inizio + size, TOTALE))]
        # stessa forma della risposta reale del portale
        corpo = json.dumps({
            "result": {"exitCode": "200", "text": "OK", "identificativo": None},
            "payload": {"type": "AltriBandiRdoAperteFiltrati", "elencoBandi": fetta},
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def main():
    server = HTTPServer(("127.0.0.1", PORTA), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    uscita = RADICE / "data" / "rdo_grezze.json"
    if uscita.exists():
        uscita.unlink()

    ambiente = {
        **os.environ,
        "MEPA_VETRINA_URL": f"http://127.0.0.1:{PORTA}/vetrina.html",
        "MEPA_ENDPOINT": f"http://127.0.0.1:{PORTA}/publicservices/vetrineservices/getAltriBandiRdoAperte",
        "MEPA_ITEM_PAGINA": "10",   # forza piu' pagine, cosi' si prova la paginazione
        "MEPA_TIMEOUT_MS": "20000",
        "no_proxy": "127.0.0.1,localhost",
        "NO_PROXY": "127.0.0.1,localhost",
    }
    esito = subprocess.run(
        [sys.executable, str(RADICE / "scraper" / "fetch_rdo.py")],
        env=ambiente, capture_output=True, text=True, timeout=180,
    )
    print(esito.stdout)
    if esito.stderr.strip():
        print("stderr:", esito.stderr[-1500:])
    server.shutdown()

    problemi = []
    if not uscita.exists():
        print("FALLITO: nessun file prodotto")
        return 1
    rec = json.loads(uscita.read_text(encoding="utf-8"))

    if len(rec) != TOTALE:
        problemi.append(f"attesi {TOTALE} record, ottenuti {len(rec)} (paginazione)")

    per_id = {r["id"]: r for r in rec}
    if len(per_id) != len(rec):
        problemi.append("record duplicati non deduplicati")

    r0 = per_id.get("id0000")
    if not r0:
        problemi.append("manca il record id0000")
    else:
        if r0["titolo"] != "Servizio di catering e coffee break per gli eventi istituzionali":
            problemi.append(f"titolo errato: {r0['titolo']!r}")
        if r0["numero"] != "4500000":
            problemi.append(f"numero errato: {r0['numero']!r}")
        if r0["ente"] != "Comune di Prova 0":
            problemi.append(f"ente errato: {r0['ente']!r}")
        if r0["categorie"] != ["Ristorazione"]:
            problemi.append(f"categorie errate: {r0['categorie']!r}")
        if r0["valore"] != 12500.0:
            problemi.append(f"importo '12.500,00' -> {r0['valore']!r}, atteso 12500.0")
        if not (r0["pubblicazione"] or "").startswith("2026-"):
            problemi.append(f"data epoch non convertita: {r0['pubblicazione']!r}")
        if "idBando=id0000" not in r0["url"]:
            problemi.append(f"url scheda errato: {r0['url']!r}")

    r1 = per_id.get("id0001")
    if r1 and r1["valore"] != 48000.0:
        problemi.append(f"importo '48000' -> {r1['valore']!r}")
    if r1 and r1["pubblicazione"] != "2026-07-15":
        problemi.append(f"data ISO -> {r1['pubblicazione']!r}")

    r2 = per_id.get("id0002")
    if r2 and r2["pubblicazione"] != "2026-07-15":
        problemi.append(f"data 15/07/2026 -> {r2['pubblicazione']!r}")
    if r2 and r2["valore"] != 7500.5:
        problemi.append(f"importo numerico -> {r2['valore']!r}")

    diag = RADICE / "data" / "diagnostica.json"
    if not diag.exists():
        problemi.append("diagnostica.json non salvato")
    else:
        fasi = json.loads(diag.read_text(encoding="utf-8")).get("fasi", [])
        diretta = next((f for f in fasi if f.get("fase") == "endpoint_diretto"), None)
        if not diretta or diretta.get("items") != TOTALE:
            problemi.append(f"la chiamata diretta non ha raccolto tutto: {diretta}")

    if r0 and r0.get("tipo") != "Servizi":
        problemi.append(f"campo tipo non letto: {r0.get('tipo')!r}")

    # la catena completa: i 25 grezzi devono ridursi ai soli pertinenti
    from classify import filtra  # noqa: E402
    tenuti, _ = filtra(rec)
    attesi = sum(1 for i in range(TOTALE) if i % 5 in (0, 1, 2))
    if len(tenuti) != attesi:
        problemi.append(f"classificazione: attesi {attesi} pertinenti, ottenuti {len(tenuti)}")

    if problemi:
        print("FALLITO:")
        for p in problemi:
            print("  -", p)
        return 1
    print(f"OK: {len(rec)} record estratti e paginati, {len(tenuti)} pertinenti, "
          "date/importi/categorie/link corretti")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())
