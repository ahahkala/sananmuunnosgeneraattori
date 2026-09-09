'use strict';

const $q = document.getElementById('q');
const $status = document.getElementById('status');
const $results = document.getElementById('results');
const $more = document.getElementById('more');
const $hint = document.getElementById('hint');
const $onlyBase = document.getElementById('onlyBase');
const $noProper = document.getElementById('noProper');
const $sort = document.getElementById('sort');
const $examples = document.getElementById('examples');

const PAGE = 60;
let ready = false;
let queryId = 0;
let last = null;      // viimeisin vastaus
let cur = { word: '', prefix: '' };   // viimeisimmän haun jaettu syöte
let shown = 0;

/* Versioleima tulee tämän skriptin omasta osoitteesta (app.js?v=...), jonka
   tools/stamp_assets.py kirjoittaa index.html:ään. Se kuljetetaan eteenpäin
   workerille ja sanastotiedostoille, jotta palaava kävijä saa uuden version
   heti eikä vasta välimuistin vanhennuttua. */
const V = new URL(document.currentScript.src).searchParams.get('v') || '';

const worker = new Worker('worker.js' + (V ? '?v=' + V : ''));
worker.postMessage({ type: 'init', v: V });

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

/* Hakukentässä voi olla kaksi sanaa: ensimmäinen on hakusana, loput rajaavat
   parisanan alkukirjaimet ("kissa kau" -> vain parit, joiden toinen sana alkaa
   kau-). Rajaus tehdään workerissa, ei täällä: tänne tulee vain rajattu määrä
   osumia, joten selainpään suodatus laskisi väärän kokonaismäärän. */
function parseQuery(value) {
  const parts = value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return { word: parts[0] || '', prefix: parts.slice(1).join('') };
}

let timer = null;
function schedule() {
  clearTimeout(timer);
  timer = setTimeout(run, 90);
}

function run() {
  if (!ready) return;
  const raw = $q.value.trim().toLowerCase();
  cur = parseQuery(raw);
  history.replaceState(null, '', raw ? '#' + encodeURIComponent(raw) : ' ');
  if (!cur.word) {
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
    q: cur.word,
    opts: {
      onlyBase: $onlyBase.checked,
      noProper: $noProper.checked,
      sort: $sort.value,
      prefix: cur.prefix,
      compound: true,
      limit: 3000,
    },
  });
}

function render(m) {
  last = m;
  // Vastaus on aina viimeisimpään kyselyyn (id tarkistettu), joten cur kuvaa
  // sitä. Otetaan sanat talteen: "näytä lisää" voi tulla paljon myöhemmin.
  last.word = cur.word;
  last.prefix = cur.prefix;
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

  const q = last.word, prefix = last.prefix;
  const known = m.known
    ? ''
    : ' <span class="warn">(sanaa ei löydy sanastosta – tulokset perustuvat silti sen alkuun ja loppuun)</span>';

  if (!m.total && prefix) {
    $status.innerHTML = 'Ei sananmuunnosta sanalle <b>' + esc(q) +
      '</b>, jonka toinen sana alkaa <b>' + esc(prefix) + '</b>.' + known;
    $more.hidden = true;
    $hint.hidden = false;
    $hint.innerHTML = 'Kokeile lyhyempää alkua tai poista jälkimmäinen sana kentästä.';
    return;
  }
  if (!m.total) {
    $status.innerHTML = 'Ei yhtään sananmuunnosta sanalle <b>' + esc(q) + '</b>.' + known;
    $more.hidden = true;
    $hint.hidden = false;
    $hint.innerHTML = 'Kokeile toista taivutusmuotoa – esimerkiksi <code>' +
      esc(q) + 'a</code> tai <code>' + esc(q) + 'n</code>. Sananmuunnos vaatii, ' +
      'että molemmista sanoista tulee vaihdon jälkeen oikea suomen sana.';
    return;
  }

  // Karkeajärjestyksessä lista jatkuu tavallisilla osumilla, kun karkeat
  // loppuvat - kerrotaan siis suoraan, montako niitä oli.
  let extra = '';
  if (m.rudeTotal !== undefined) {
    extra = m.rudeTotal
      ? ' – niistä <b>' + m.rudeTotal.toLocaleString('fi-FI') +
        '</b> sisältää sopimattoman sanan'
      : ' – <span class="warn">ei yhtään sopimatonta sanaa</span>';
  }
  const filt = prefix ? ', joiden toinen sana alkaa <b>' + esc(prefix) + '</b>' : '';
  if (m.compound) {
    // Muunnos on tehty yhdyssanan alkuosalle ja loppuosa liitetty takaisin,
    // joten tuloksen ensimmäinen sana on koottu - sitä ei ole sanastossa.
    $status.innerHTML = 'Sanalle <b>' + esc(q) + '</b> ei löydy suoraa paria. ' +
      '<b>' + m.total.toLocaleString('fi-FI') + '</b> sananmuunnosta yhdyssanan alkuosalle (' +
      m.compound.map((x) => '<b>' + esc(x) + '</b>').join(', ') + ')' + filt +
      ' <span style="opacity:.6">(' + m.ms + ' ms)</span><br>' +
      '<span class="warn">Loppuosa liitetään takaisin sellaisenaan, joten tuloksen ' +
      'ensimmäinen sana on koottu yhdyssana – sitä ei ole tarkistettu sanastosta.</span>';
    appendMore();
    return;
  }
  $status.innerHTML = '<b>' + m.total.toLocaleString('fi-FI') + '</b> sananmuunnosta sanalle <b>' +
    esc(q) + '</b>' + filt + extra + ' <span style="opacity:.6">(' + m.ms + ' ms)</span>' + known;
  appendMore();
}

function appendMore() {
  const q = last.word;
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
      '<div class="res">' + esc(r.r1) +
        (r.suf ? '<span class="glue">' + esc(r.suf) + '</span>' : '') +
        ' &nbsp;<span class="w2">' + esc(r.r2) + '</span>' +
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
$sort.addEventListener('change', run);
$noProper.addEventListener('change', run);
