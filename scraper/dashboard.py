"""
Generatore della dashboard HTML self-contained del radar MePA.

Il file prodotto (docs/index.html) contiene i dati incorporati: funziona aperto
da GitHub Pages, da disco o come artifact, senza dipendenze esterne.
"""

import json
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="it" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Radar MePA · 4x4</title>
<style>
  :root {
    color-scheme: light dark;
    --surface-1: #fcfcfb;
    --plane: #f9f9f7;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --muted: #898781;
    --grid: #e1e0d9;
    --baseline: #c3c2b7;
    --border: rgba(11,11,11,0.10);
    --serie-consulenza: #2a78d6;
    --serie-eventi: #eb6834;
    --serie-catering: #1baf7a;
    --serie-comunicazione: #8b5cf6;
    --good: #0ca30c;
    --warning: #fab219;
    --critical: #d03b3b;
    --radius: 12px;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      --surface-1: #1a1a19;
      --plane: #0d0d0d;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --muted: #898781;
      --grid: #2c2c2a;
      --baseline: #383835;
      --border: rgba(255,255,255,0.10);
      --serie-consulenza: #3987e5;
      --serie-eventi: #d95926;
      --serie-catering: #199e70;
      --serie-comunicazione: #a78bfa;
    }
  }
  :root[data-theme="dark"] {
    --surface-1: #1a1a19;
    --plane: #0d0d0d;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --muted: #898781;
    --grid: #2c2c2a;
    --baseline: #383835;
    --border: rgba(255,255,255,0.10);
    --serie-consulenza: #3987e5;
    --serie-eventi: #d95926;
    --serie-catering: #199e70;
    --serie-comunicazione: #a78bfa;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--plane);
    color: var(--text-primary);
    font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 1180px; margin: 0 auto; padding: 32px 20px 72px; }

  header.top { display: flex; flex-wrap: wrap; gap: 16px; align-items: baseline;
               justify-content: space-between; margin-bottom: 6px; }
  h1 { font-size: 26px; margin: 0; letter-spacing: -0.01em; }
  .sub { color: var(--text-secondary); font-size: 14px; margin: 4px 0 0; }
  .badge-demo { display: inline-block; background: var(--warning); color: #0b0b0b;
                border-radius: 999px; padding: 3px 10px; font-size: 12px; font-weight: 600; }
  .theme-btn { background: var(--surface-1); border: 1px solid var(--border);
               color: var(--text-secondary); border-radius: 999px; padding: 6px 14px;
               font-size: 13px; cursor: pointer; }

  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
           gap: 12px; margin: 24px 0; }
  .tile { background: var(--surface-1); border: 1px solid var(--border);
          border-radius: var(--radius); padding: 16px 18px; }
  .tile .k { font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em;
             color: var(--muted); margin-bottom: 8px; }
  .tile .v { font-size: 30px; font-weight: 600; line-height: 1.1; }
  .tile .n { font-size: 12px; color: var(--text-secondary); margin-top: 6px; }

  .panel { background: var(--surface-1); border: 1px solid var(--border);
           border-radius: var(--radius); padding: 20px; margin-bottom: 20px; }
  .panel h2 { font-size: 15px; margin: 0 0 4px; font-weight: 600; }
  .panel .cap { font-size: 13px; color: var(--text-secondary); margin: 0 0 18px; }

  .bars { display: grid; gap: 14px; }
  .barrow { display: grid; grid-template-columns: 190px 1fr auto; gap: 12px; align-items: center; }
  .barlab { font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 8px; }
  .dot { width: 10px; height: 10px; border-radius: 3px; flex: none; }
  .bartrack { background: var(--grid); border-radius: 4px; height: 14px; position: relative; }
  .barfill { height: 14px; border-radius: 4px; }
  .barval { font-size: 13px; font-variant-numeric: tabular-nums; color: var(--text-primary);
            min-width: 108px; text-align: right; }

  .controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 18px; }
  .controls input[type=search], .controls select {
    background: var(--surface-1); color: var(--text-primary);
    border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; font: inherit; font-size: 14px; }
  .controls input[type=search] { min-width: 260px; flex: 1 1 260px; }
  .chip { border: 1px solid var(--border); background: var(--surface-1); color: var(--text-secondary);
          border-radius: 999px; padding: 7px 14px; font-size: 13px; cursor: pointer;
          display: inline-flex; align-items: center; gap: 7px; }
  .chip[aria-pressed="true"] { border-color: currentColor; color: var(--text-primary); font-weight: 600; }
  .chip .dot { width: 9px; height: 9px; border-radius: 50%; }

  .card { background: var(--surface-1); border: 1px solid var(--border);
          border-left: 3px solid var(--baseline);
          border-radius: var(--radius); padding: 16px 18px; margin-bottom: 12px; }
  .card.consulenza { border-left-color: var(--serie-consulenza); }
  .card.eventi     { border-left-color: var(--serie-eventi); }
  .card.catering   { border-left-color: var(--serie-catering); }
  .card.comunicazione { border-left-color: var(--serie-comunicazione); }
  .tag.manifestazione { background: var(--serie-comunicazione); border-color: var(--serie-comunicazione);
                        color: #fff; font-weight: 600; }
  .tag.fonte { letter-spacing: 0.04em; }
  .gruppo { font-size: 12px; color: var(--muted); text-transform: uppercase;
            letter-spacing: 0.04em; align-self: center; margin-left: 4px; }
  .card .link2 { font-size: 12.5px; margin: 8px 0 0; }
  .card .link2 a { color: var(--text-secondary); }
  details.esiti { background: var(--surface-1); border: 1px solid var(--border);
                  border-radius: var(--radius); padding: 18px 20px; margin-bottom: 20px; }
  details.esiti summary { cursor: pointer; font-size: 15px; font-weight: 600; }
  details.esiti .cap { font-size: 13px; color: var(--text-secondary); margin: 10px 0 0; }
  .card h3 { font-size: 15.5px; margin: 0 0 8px; font-weight: 600; line-height: 1.4; }
  .card h3 a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--border); }
  .card h3 a:hover { border-bottom-color: currentColor; }
  .meta { display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 13px;
          color: var(--text-secondary); margin-bottom: 10px; }
  .meta b { color: var(--text-primary); font-weight: 600; font-variant-numeric: tabular-nums; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; }
  .tag { font-size: 11.5px; border: 1px solid var(--border); border-radius: 999px;
         padding: 3px 9px; color: var(--text-secondary); }
  .tag.settore { font-weight: 600; }
  .tag.nuovo { background: var(--good); border-color: var(--good); color: #fff; font-weight: 600; }
  .tag.urgente { background: var(--critical); border-color: var(--critical); color: #fff; font-weight: 600; }
  .tag.presto { border-color: var(--warning); color: var(--text-primary); }
  .desc { font-size: 13.5px; color: var(--text-secondary); margin: 0 0 10px;
          display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--grid); vertical-align: top; }
  th { color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.03em; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  td a { color: var(--text-primary); text-decoration: underline;
         text-decoration-color: var(--baseline); text-underline-offset: 2px; }
  td a:hover { text-decoration-color: currentColor; }
  #tabella { display: none; }
  #tabella.on { display: block; }
  #schede.off { display: none; }

  .vuoto { text-align: center; color: var(--text-secondary); padding: 40px 20px; }
  footer { color: var(--muted); font-size: 12.5px; margin-top: 32px; line-height: 1.7; }
  footer a { color: var(--text-secondary); }
</style>
</head>
<body>
<div class="wrap">

  <header class="top">
    <div>
      <h1>Radar appalti · 4x4 e Joule</h1>
      <p class="sub">Manifestazioni d'interesse, gare aperte ed esiti dalla Piattaforma di Pubblicità
        a Valore Legale di ANAC e dalle RDO aperte del MePA, filtrati per consulenza, eventi,
        catering (4x4) e comunicazione (Joule). __BADGE__</p>
    </div>
    <button class="theme-btn" id="tema" type="button">Tema</button>
  </header>

  <section class="tiles" id="tiles"></section>

  <section class="panel">
    <h2>Opportunità aperte per settore</h2>
    <p class="cap">Numero di procedure attive e valore complessivo a base d'asta, per area di interesse.</p>
    <div class="bars" id="bars"></div>
  </section>

  <div class="controls">
    <input type="search" id="cerca" placeholder="Cerca per titolo, ente, categoria…" aria-label="Cerca">
    <span class="gruppo">Società</span>
    <button class="chip" data-societa="4x4" aria-pressed="true">4x4</button>
    <button class="chip" data-societa="Joule" aria-pressed="true"><span class="dot" style="background:var(--serie-comunicazione)"></span>Joule</button>
    <span class="gruppo">Settore</span>
    <button class="chip" data-settore="consulenza" aria-pressed="true"><span class="dot" style="background:var(--serie-consulenza)"></span>Consulenza</button>
    <button class="chip" data-settore="eventi" aria-pressed="true"><span class="dot" style="background:var(--serie-eventi)"></span>Eventi</button>
    <button class="chip" data-settore="catering" aria-pressed="true"><span class="dot" style="background:var(--serie-catering)"></span>Catering</button>
    <button class="chip" data-settore="comunicazione" aria-pressed="true"><span class="dot" style="background:var(--serie-comunicazione)"></span>Comunicazione</button>
    <button class="chip" id="solomanifestazioni" aria-pressed="false">Solo manifestazioni d'interesse</button>
    <button class="chip" id="solonuove" aria-pressed="false">Solo novità</button>
    <button class="chip" id="soloscadenza" aria-pressed="false">In scadenza ≤ 7 gg</button>
    <select id="ordina" aria-label="Ordinamento">
      <option value="rilevanza">Ordina per rilevanza</option>
      <option value="scadenza">Ordina per scadenza</option>
      <option value="valore">Ordina per importo</option>
      <option value="recenti">Ordina per pubblicazione</option>
    </select>
    <button class="chip" id="vista" aria-pressed="false">Vista tabella</button>
  </div>

  <p class="sub" id="conteggio"></p>

  <section id="schede"></section>
  <section id="tabella" class="panel"></section>

  <details class="esiti" id="esiti">
    <summary id="esiti-titolo">Esiti recenti</summary>
    <p class="cap">Gare già aggiudicate negli stessi settori: non si partecipa, si studiano.
      Dicono quali enti comprano davvero questi servizi, da chi e a che prezzo — e quando il
      contratto in corso andrà rinnovato. È la lista da cui partire per farsi invitare
      alla prossima procedura negoziata.</p>
    <div id="esiti-corpo"></div>
  </details>

  <footer>
    <p><b>Come funziona.</b> Ogni lunedì mattina uno script interroga la Piattaforma di Pubblicità
    a Valore Legale di ANAC sui codici CPV dei quattro settori e la vetrina delle RDO aperte del
    MePA, poi assegna a ogni pubblicazione un punteggio di pertinenza 0–100 combinando codice CPV,
    categoria e dizionari di parole chiave. Entrano in dashboard solo le opportunità sopra
    __SOGLIA__ punti. Il punteggio è un aiuto alla selezione, non un giudizio sulla
    partecipabilità: importo, requisiti e termini vanno sempre verificati sulla scheda originale.</p>
    <p><b>Perché le manifestazioni d'interesse contano più delle gare.</b> Su servizi e forniture
    ANAC misura che il 92–95% delle procedure è affidamento diretto, ma solo il 17–31% del valore:
    quasi tutto quello che la PA compra lo compra per chiamata, e la consulenza sta lì. L'avviso
    con cui un ente cerca gli operatori da invitare è quindi il vero punto di ingresso — dopo,
    la partita è già assegnata.</p>
    <p>Fonti: <a href="https://pubblicitalegale.anticorruzione.it/">ANAC · Piattaforma di Pubblicità
    a Valore Legale</a> e <a href="https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=RDO">Acquisti
    in Rete PA · RDO aperte</a>. Ultimo aggiornamento: __AGGIORNATO__.</p>
  </footer>
</div>

<script id="dati" type="application/json">__DATI__</script>
<script>
(function () {
  const DATI = JSON.parse(document.getElementById('dati').textContent);
  const OPP = DATI.opportunita;
  const META = DATI.meta;

  const euro = n => n == null ? '—' :
    new Intl.NumberFormat('it-IT', {style:'currency', currency:'EUR', maximumFractionDigits:0}).format(n);
  const dataIt = s => { if (!s) return '—';
    const [a,m,g] = s.split('-'); return `${g}/${m}/${a}`; };
  const esc = s => String(s == null ? '' : s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

  // ---- tile di sintesi ----------------------------------------------------
  const SOC = META.per_societa || {};
  const tiles = [
    {k:'Opportunità aperte', v: META.attivi, n: `su ${META.esaminati} pubblicazioni esaminate`},
    {k:"Manifestazioni d'interesse", v: META.manifestazioni ?? 0,
     n: 'la porta di ingresso agli affidamenti diretti'},
    {k:'Novità della settimana', v: META.nuovi, n: 'mai viste nelle scansioni precedenti'},
    {k:'In scadenza entro 7 giorni', v: META.in_scadenza_7gg, n: 'da decidere subito'},
    {k:'4x4 · Joule',
     v: `${SOC['4x4'] ? SOC['4x4'].totale : 0} · ${SOC['Joule'] ? SOC['Joule'].totale : 0}`,
     n: 'opportunità aperte per società'},
    {k:'Valore complessivo', v: euro(META.valore_totale),
     n: `${META.con_importo} procedure con importo attendibile` +
        (META.importi_sospetti ? ` · ${META.importi_sospetti} sotto € 1.000, esclusi` : '')},
  ];
  document.getElementById('tiles').innerHTML = tiles.map(t =>
    `<div class="tile"><div class="k">${esc(t.k)}</div><div class="v">${esc(t.v)}</div><div class="n">${esc(t.n)}</div></div>`
  ).join('');

  // ---- barre per settore --------------------------------------------------
  const settori = META.per_settore;
  const chiavi = Object.keys(settori);
  const maxN = Math.max(1, ...chiavi.map(k => settori[k].totale));
  document.getElementById('bars').innerHTML = chiavi.map(k => {
    const s = settori[k];
    const w = (s.totale / maxN) * 100;
    return `<div class="barrow">
      <div class="barlab"><span class="dot" style="background:var(--serie-${k})"></span>${esc(s.etichetta)}</div>
      <div class="bartrack"><div class="barfill" style="width:${w}%;background:var(--serie-${k})"></div></div>
      <div class="barval">${s.totale} · ${euro(s.valore_totale)}</div>
    </div>`;
  }).join('');

  // ---- stato dei filtri ---------------------------------------------------
  const stato = {q:'', settori:new Set(chiavi), societa:new Set(Object.keys(SOC)),
                 manifestazioni:false, nuove:false, scadenza:false,
                 ordine:'rilevanza', tabella:false};

  function filtra() {
    let out = OPP.filter(o => stato.settori.has(o.settore));
    out = out.filter(o => !o.societa || stato.societa.has(o.societa));
    if (stato.manifestazioni) out = out.filter(o => o.momento === 'manifestazione');
    if (stato.nuove) out = out.filter(o => o.nuovo);
    if (stato.scadenza) out = out.filter(o => o.giorni_alla_scadenza != null && o.giorni_alla_scadenza <= 7);
    if (stato.q) {
      const q = stato.q.toLowerCase();
      out = out.filter(o => [o.titolo, o.descrizione, o.ente, o.stazione_appaltante,
        (o.categorie||[]).join(' '), o.numero].join(' ').toLowerCase().includes(q));
    }
    const cmp = {
      // Le manifestazioni d'interesse vengono prima: e' il momento in cui si
      // entra in partita, mentre su una gara gia' pubblicata si arriva tardi.
      rilevanza: (a,b) => ((b.momento === 'manifestazione') - (a.momento === 'manifestazione'))
                          || (b.nuovo - a.nuovo) || (b.punteggio - a.punteggio),
      scadenza:  (a,b) => (a.giorni_alla_scadenza ?? 9999) - (b.giorni_alla_scadenza ?? 9999),
      valore:    (a,b) => (b.valore ?? -1) - (a.valore ?? -1),
      recenti:   (a,b) => String(b.pubblicazione||'').localeCompare(String(a.pubblicazione||'')),
    }[stato.ordine];
    return out.sort(cmp);
  }

  function badgeScadenza(o) {
    const g = o.giorni_alla_scadenza;
    if (g == null) return '<span class="tag">scadenza n.d.</span>';
    const quando = g === 0 ? 'scade oggi' : g === 1 ? 'scade domani' : `scade fra ${g} giorni`;
    if (g <= 3) return `<span class="tag urgente">${quando}</span>`;
    if (g <= 7) return `<span class="tag presto">${quando}</span>`;
    return `<span class="tag">${quando}</span>`;
  }

  const etichettaSettore = k => (META.per_settore[k] || {}).etichetta || k;

  function scheda(o) {
    const cat = (o.categorie||[])[0];
    // Un bando puo' interessare entrambe: "comunicazione ed eventi" e' il caso
    // tipico. Si assegna alla societa' del settore vincente, ma l'altra va detta.
    const altre = [...new Set((o.settori_secondari||[])
      .map(s => (DATI.meta.settore_societa||{})[s])
      .filter(x => x && x !== o.societa))];
    return `<article class="card ${esc(o.settore)}">
      <h3><a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.titolo)}</a></h3>
      ${o.descrizione ? `<p class="desc">${esc(o.descrizione)}</p>` : ''}
      <div class="meta">
        <span>${esc(o.ente || o.stazione_appaltante || 'Ente non indicato')}</span>
        ${o.luogo ? `<span>${esc(o.luogo)}</span>` : ''}
        <span>Importo <b>${euro(o.valore)}</b></span>
        <span>Pubblicata il <b>${dataIt(o.pubblicazione)}</b></span>
        <span>Scade il <b>${dataIt(o.scadenza)}</b></span>
        ${o.numero ? `<span>${o.fonte === 'ANAC' ? 'CIG' : 'RDO'} <b>${esc(o.numero)}</b></span>` : ''}
      </div>
      <div class="tags">
        ${o.momento === 'manifestazione'
          ? `<span class="tag manifestazione">${esc(o.momento_etichetta || "Manifestazione d'interesse")}</span>` : ''}
        <span class="tag settore">${esc(etichettaSettore(o.settore))} · ${o.punteggio}/100</span>
        ${o.societa ? `<span class="tag settore">${esc(o.societa)}</span>` : ''}
        ${altre.length ? `<span class="tag">anche ${esc(altre.join(' e '))}</span>` : ''}
        ${o.nuovo ? '<span class="tag nuovo">Novità</span>' : ''}
        ${o.valore_sospetto ? '<span class="tag presto">importo da verificare</span>' : ''}
        ${badgeScadenza(o)}
        <span class="tag fonte">${esc(o.fonte || 'MePA')}</span>
        ${cat ? `<span class="tag">${esc(cat)}</span>` : ''}
        ${(o.motivi||[]).slice(0,2).map(m => `<span class="tag">${esc(m)}</span>`).join('')}
      </div>
      ${o.link_gara ? `<p class="link2">Documenti di gara:
        <a href="${esc(o.link_gara)}" target="_blank" rel="noopener">${esc(o.link_gara)}</a></p>` : ''}
    </article>`;
  }

  // ---- esiti: chi ha vinto, quanto, presso quale ente ----------------------
  function disegnaEsiti() {
    const box = document.getElementById('esiti');
    const righe = DATI.esiti || [];
    if (!righe.length) { box.style.display = 'none'; return; }
    document.getElementById('esiti-titolo').textContent =
      `Esiti recenti · ${righe.length} ` +
      (righe.length === 1 ? 'aggiudicazione' : 'aggiudicazioni') + ' negli stessi settori';
    document.getElementById('esiti-corpo').innerHTML =
      `<table><thead><tr><th>Oggetto</th><th>Ente</th><th>Aggiudicatario</th>
        <th class="num">Base d'asta</th><th class="num">Aggiudicato</th></tr></thead><tbody>
      ${righe.map(o => {
        const vincitori = (o.aggiudicatari||[]).map(a => esc(a.nome)).join(', ') || '—';
        const ribasso = (o.valore && o.valore_aggiudicato)
          ? ` <span class="tag">−${Math.round((1 - o.valore_aggiudicato / o.valore) * 100)}%</span>` : '';
        return `<tr>
          <td><a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.titolo)}</a></td>
          <td>${esc(o.ente || '—')}</td>
          <td>${vincitori}</td>
          <td class="num">${euro(o.valore)}</td>
          <td class="num">${euro(o.valore_aggiudicato)}${ribasso}</td>
        </tr>`; }).join('')}
      </tbody></table>`;
  }

  function tabella(righe) {
    return `<table><thead><tr>
      <th>Titolo</th><th>Ente</th><th>Tipo</th><th>Settore</th><th class="num">Punti</th>
      <th class="num">Importo</th><th>Scadenza</th></tr></thead><tbody>
      ${righe.map(o => `<tr>
        <td><a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.titolo)}</a></td>
        <td>${esc(o.ente || o.stazione_appaltante || '—')}</td>
        <td>${esc(o.momento_etichetta || 'Gara aperta')}</td>
        <td>${esc(etichettaSettore(o.settore))} · ${esc(o.societa || '')}${o.nuovo ? ' · novità' : ''}</td>
        <td class="num">${o.punteggio}</td>
        <td class="num">${euro(o.valore)}</td>
        <td>${dataIt(o.scadenza)}${o.giorni_alla_scadenza != null ? ` (${o.giorni_alla_scadenza} gg)` : ''}</td>
      </tr>`).join('')}
    </tbody></table>`;
  }

  function disegna() {
    const righe = filtra();
    document.getElementById('conteggio').textContent =
      `${righe.length} opportunità mostrate · ${righe.filter(o=>o.nuovo).length} novità · ` +
      `${righe.filter(o=>o.momento==='manifestazione').length} manifestazioni d'interesse`;
    const schede = document.getElementById('schede');
    const tab = document.getElementById('tabella');
    if (stato.tabella) {
      schede.classList.add('off'); tab.classList.add('on');
      tab.innerHTML = righe.length ? tabella(righe) : '<p class="vuoto">Nessuna opportunità con questi filtri.</p>';
    } else {
      schede.classList.remove('off'); tab.classList.remove('on');
      schede.innerHTML = righe.length ? righe.map(scheda).join('')
        : '<p class="vuoto">Nessuna opportunità con questi filtri.</p>';
    }
  }

  const chipInsieme = (attributo, insieme) =>
    document.querySelectorAll(`.chip[data-${attributo}]`).forEach(b => {
      b.addEventListener('click', () => {
        const k = b.dataset[attributo];
        const on = b.getAttribute('aria-pressed') === 'true';
        b.setAttribute('aria-pressed', String(!on));
        on ? insieme.delete(k) : insieme.add(k);
        disegna();
      });
    });
  chipInsieme('settore', stato.settori);
  chipInsieme('societa', stato.societa);
  const toggle = (id, campo) => {
    const b = document.getElementById(id);
    b.addEventListener('click', () => {
      stato[campo] = !stato[campo];
      b.setAttribute('aria-pressed', String(stato[campo]));
      disegna();
    });
  };
  toggle('solomanifestazioni', 'manifestazioni');
  toggle('solonuove', 'nuove');
  toggle('soloscadenza', 'scadenza');
  toggle('vista', 'tabella');
  document.getElementById('cerca').addEventListener('input', e => { stato.q = e.target.value; disegna(); });
  document.getElementById('ordina').addEventListener('change', e => { stato.ordine = e.target.value; disegna(); });
  document.getElementById('tema').addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme');
    document.documentElement.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
  });

  disegnaEsiti();
  disegna();
})();
</script>
</body>
</html>
"""


def scrivi_dashboard(payload, destinazione: Path):
    meta = payload["meta"]
    badge = ('<span class="badge-demo">dati dimostrativi</span>'
             if meta.get("modalita") == "demo" else "")
    html = (TEMPLATE
            .replace("__DATI__", json.dumps(payload, ensure_ascii=False))
            .replace("__BADGE__", badge)
            .replace("__SOGLIA__", str(meta.get("soglia", 30)))
            .replace("__AGGIORNATO__", meta.get("aggiornato_testo") or meta.get("aggiornato", "—")))
    destinazione.write_text(html, encoding="utf-8")
    return destinazione
