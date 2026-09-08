'use strict';

const $q = document.getElementById('q');
const $status = document.getElementById('status');
const $results = document.getElementById('results');
const $more = document.getElementById('more');
const $hint = document.getElementById('hint');
const $onlyBase = document.getElementById('onlyBase');
const $noProper = document.getElementById('noProper');
const $examples = document.getElementById('examples');

const PAGE = 60;
let ready = false;
let queryId = 0;
let last = null;      // viimeisin vastaus
let shown = 0;

const worker = new Worker('worker.js');
worker.postMessage({ type: 'init' });

worker.onmessage = (ev) => {
  const m = ev.data;
  if (m.type === 'status') {
    $status.textContent = m.text;
  } else if (m.type === 'ready') {
    ready = true;
    $q.disabled = false;
    $q.focus();
    $status.innerHTML = '<b>' + m.count.toLocaleString('fi-FI') +
      '</b> sanamuotoa ladattu. Kirjoita sana yllä.';
    requestExamples();
    if (!applyHash() && $q.value.trim()) run();
  } else if (m.type === 'examples') {
    showExamples(m.words);
  } else if (m.type === 'error') {
    $status.innerHTML = '<span class="warn">Virhe: ' + esc(m.text) + '</span>';
  } else if (m.type === 'results') {
    if (m.id !== queryId) return;
    render(m);
  }
};

// Esimerkkisanat arvotaan sanastosta joka kerta, kun ne tulevat näkyviin.
// Worker varmistaa, että jokainen ehdotus tuottaa oikeasti tuloksia.
function requestExamples() {
  worker.postMessage({ type: 'examples', count: 7, min: 25 });
}

function showExamples(words) {
  $examples.innerHTML = '';
  for (const w of words) {
    const b = document.createElement('button');
    b.textContent = w;
    b.onclick = () => { $q.value = w; $q.focus(); run(); };
    $examples.appendChild(b);
  }
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

let timer = null;
function schedule() {
  clearTimeout(timer);
  timer = setTimeout(run, 90);
}

function run() {
  if (!ready) return;
  const q = $q.value.trim().toLowerCase();
  history.replaceState(null, '', q ? '#' + encodeURIComponent(q) : ' ');
  if (!q) {
    $results.innerHTML = '';
    $more.hidden = true;
    $hint.hidden = true;
    $examples.style.display = '';
    requestExamples();
    $status.innerHTML = 'Kirjoita sana yllä.';
    return;
  }
  $examples.style.display = 'none';
  worker.postMessage({
    type: 'query',
    id: ++queryId,
    q,
    opts: { onlyBase: $onlyBase.checked, noProper: $noProper.checked, limit: 3000 },
  });
}

function render(m) {
  last = m;
  shown = 0;
  $results.innerHTML = '';
  $hint.hidden = true;

  if (m.error === 'short') {
    $status.textContent = 'Anna vähintään kaksi kirjainta.';
    $more.hidden = true;
    return;
  }
  if (m.error === 'novowel' || m.error === 'head') {
    $status.textContent = 'Tuo ei näytä suomen sanalta.';
    $more.hidden = true;
    return;
  }
  if (m.error) {
    $status.innerHTML = '<span class="warn">Haku epäonnistui: ' + esc(m.text || '') + '</span>';
    $more.hidden = true;
    return;
  }

  const q = $q.value.trim().toLowerCase();
  const known = m.known
    ? ''
    : ' <span class="warn">(sanaa ei löydy sanastosta – tulokset perustuvat silti sen alkuun ja loppuun)</span>';

  if (!m.total) {
    $status.innerHTML = 'Ei yhtään sananmuunnosta sanalle <b>' + esc(q) + '</b>.' + known;
    $more.hidden = true;
    $hint.hidden = false;
    $hint.innerHTML = 'Kokeile toista taivutusmuotoa – esimerkiksi <code>' +
      esc(q) + 'a</code> tai <code>' + esc(q) + 'n</code>. Sananmuunnos vaatii, ' +
      'että molemmista sanoista tulee vaihdon jälkeen oikea suomen sana.';
    return;
  }

  $status.innerHTML = '<b>' + m.total.toLocaleString('fi-FI') + '</b> sananmuunnosta sanalle <b>' +
    esc(q) + '</b> <span style="opacity:.6">(' + m.ms + ' ms)</span>' + known;
  appendMore();
}

function appendMore() {
  const q = $q.value.trim().toLowerCase();
  const items = last.results;
  const end = Math.min(shown + PAGE, items.length);
  const frag = document.createDocumentFragment();
  for (let i = shown; i < end; i++) {
    const r = items[i];
    const row = document.createElement('div');
    row.className = 'row';
    row.innerHTML =
      '<div class="src">' + esc(q) + ' &nbsp;' + esc(r.b) + '</div>' +
      '<div class="arrow">→</div>' +
      '<div class="res">' + esc(r.r1) + ' &nbsp;<span class="w2">' + esc(r.r2) + '</span>' +
      (r.proper ? '<span class="tag">erisnimi</span>' : '') + '</div>';
    frag.appendChild(row);
  }
  $results.appendChild(frag);
  shown = end;
  $more.hidden = shown >= items.length;
  if (!$more.hidden) {
    $more.textContent = 'Näytä lisää (' + (items.length - shown) + ')';
  } else if (last.total > items.length) {
    $hint.hidden = false;
    $hint.textContent = 'Näytetään ' + items.length + ' parasta osumaa ' +
      last.total.toLocaleString('fi-FI') + ':stä.';
  }
}

// Osoitepalkin #-osa on jaettava linkki hakuun. Sen muokkaaminen käsin - tai
// selaimen edestakaisin selaaminen - on sama asia kuin sanan kirjoittaminen
// kenttään, joten kenttä ja tulokset seuraavat mukana.
function applyHash() {
  const h = decodeURIComponent(location.hash.slice(1)).trim();
  if (h.toLowerCase() === $q.value.trim().toLowerCase()) return !!h;
  $q.value = h;
  clearTimeout(timer);
  run();
  return !!h;
}

window.addEventListener('hashchange', applyHash);

$more.onclick = appendMore;
$q.addEventListener('input', schedule);
$onlyBase.addEventListener('change', run);
$noProper.addEventListener('change', run);
