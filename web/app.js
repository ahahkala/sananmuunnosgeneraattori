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
const $clear = document.getElementById('clear');
const $firsts = document.getElementById('firsts');
const $firstsChips = document.getElementById('firstsChips');
const $firstsLbl = document.getElementById('firstsLbl');

const PAGE = 60;
let ready = false;
let queryId = 0;
let last = null;      // viimeisin vastaus
let cur = { word: '', prefix: '' };   // viimeisimmän haun jaettu syöte
let shown = 0;
let firstSel = null;  // valittu tuloksen ensimmäinen sana, null = ei rajausta

// Napit mahtuvat riville vain jos niitä on vähän; loput jäävät rullattavaan
// laatikkoon, jottei valikko työnnä tuloksia sivun alalaitaan.
const FIRSTS_MAX = 300;

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
    b.onclick = () => { $q.value = w; firstSel = null; $q.focus(); run(); };
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

/* Tyhjennysnappi nakyy vain, kun kentassa on jotain tyhjennettavaa. */
function syncClear() {
  $clear.hidden = $q.value === '';
}

function run() {
  syncClear();
  if (!ready) return;
  const raw = $q.value.trim().toLowerCase();
  cur = parseQuery(raw);
  history.replaceState(null, '', raw ? '#' + encodeURIComponent(raw) : ' ');
  if (!cur.word) {
    $results.innerHTML = '';
    $more.hidden = true;
    $hint.hidden = true;
    $firsts.hidden = true;
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
      first: firstSel,
      groups: true,
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
  $firsts.hidden = true;

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

  // Rajaus voi tyhjentää listan, kun jokin muu valinta on kaventanut osumia sen
  // jälkeen kun nappi valittiin. Valikko jää näkyviin, jotta rajauksen purkaa.
  if (!m.total && firstSel) {
    $status.innerHTML = 'Ei sananmuunnosta sanalle <b>' + esc(q) +
      '</b>, jonka ensimmäinen sana on <b>' + esc(firstSel) + '</b>.' + known;
    $more.hidden = true;
    renderFirsts(m.groups);
    return;
  }
  if (!m.total && prefix) {
    $status.innerHTML = 'Ei sananmuunnosta sanalle <b>' + esc(q) +
      '</b>, jonka toinen sana alkaa <b>' + esc(prefix) + '</b>.' + known;
    $more.hidden = true;
    $hint.hidden = false;
    $hint.innerHTML = 'Kokeile lyhyempää alkua tai poista jälkimmäinen sana kentästä.';
    renderFirsts(m.groups);
    return;
  }
  if (!m.total) {
    $status.innerHTML = 'Ei yhtään sananmuunnosta sanalle <b>' + esc(q) + '</b>.' + known;
    $more.hidden = true;
    $hint.hidden = false;
    $hint.innerHTML = 'Kokeile toista taivutusmuotoa – esimerkiksi <code>' +
      esc(q) + 'a</code> tai <code>' + esc(q) + 'n</code>. Sananmuunnos vaatii, ' +
      'että molemmista sanoista tulee vaihdon jälkeen oikea suomen sana.';
    renderFirsts(m.groups);
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
  let filt = prefix ? ', joiden toinen sana alkaa <b>' + esc(prefix) + '</b>' : '';
  if (firstSel) filt += ', joiden ensimmäinen sana on <b>' + esc(firstSel) + '</b>';
  if (m.compound) {
    // Muunnos on tehty yhdyssanan alkuosalle ja loppuosa liitetty takaisin,
    // joten tuloksen ensimmäinen sana on koottu - sitä ei ole sanastossa.
    $status.innerHTML = 'Sanalle <b>' + esc(q) + '</b> ei löydy suoraa paria. ' +
      '<b>' + m.total.toLocaleString('fi-FI') + '</b> sananmuunnosta yhdyssanan alkuosalle (' +
      m.compound.map((x) => '<b>' + esc(x) + '</b>').join(', ') + ')' + filt +
      ' <span style="opacity:.6">(' + m.ms + ' ms)</span><br>' +
      '<span class="warn">Loppuosa liitetään takaisin sellaisenaan, joten tuloksen ' +
      'ensimmäinen sana on koottu yhdyssana – sitä ei ole tarkistettu sanastosta.</span>';
    renderFirsts(m.groups);
    appendMore();
    return;
  }
  $status.innerHTML = '<b>' + m.total.toLocaleString('fi-FI') + '</b> sananmuunnosta sanalle <b>' +
    esc(q) + '</b>' + filt + extra + ' <span style="opacity:.6">(' + m.ms + ' ms)</span>' + known;
  renderFirsts(m.groups);
  appendMore();
}

/* Tulosten ensimmäiset sanat valikkona. Worker laskee ryhmät koko osumajoukosta
   ennen rajausta, joten valikko pysyy samana myös valinnan ollessa päällä -
   muuten yhden sanan valinta jättäisi jäljelle vain sen oman napin. */
function renderFirsts(groups) {
  if (!groups || !groups.length) {
    $firsts.hidden = true;
    return;
  }
  // Yhden ryhmän lista näytetään sekin: "olavi" tuottaa tuhansia pareja, mutta
  // ensimmäinen sana on niissä kaikissa "alavi" - se on tulos sinänsä. Silloin
  // ei ole mitään rajattavaa: nappi on pelkkä tieto, ei valinta, joten se ei
  // reagoi klikkaukseen eikä kaikki-nappia tarvita purkamaan mitään.
  const one = groups.length < 2;
  $firstsLbl.textContent = one
    ? 'Ensimmäinen sana on kaikissa tuloksissa sama:'
    : 'Rajaa ensimmäisen sanan mukaan:';
  const frag = document.createDocumentFragment();
  if (!one) frag.appendChild(chip('kaikki', groups.reduce((a, g) => a + g.n, 0), null));
  for (const g of groups.slice(0, FIRSTS_MAX)) {
    frag.appendChild(one ? chip(g.w, g.n) : chip(g.w, g.n, g.w));
  }
  $firstsChips.innerHTML = '';
  $firstsChips.appendChild(frag);
  $firsts.hidden = false;
}

/* Nappi ilman value-argumenttia on pelkkä tieto: se ei ole valittavissa eikä
   nappaa nappulanavigointia. value === null on eri asia - se on kaikki-nappi,
   joka purkaa rajauksen. */
function chip(label, n, value) {
  const info = arguments.length < 3;
  const b = document.createElement(info ? 'span' : 'button');
  b.className = 'chip';
  if (!info) b.type = 'button';
  b.textContent = label;
  const c = document.createElement('span');
  c.className = 'n';
  c.textContent = n;
  b.appendChild(c);
  if (info) return b;
  b.setAttribute('aria-pressed', String(firstSel === value));
  // Saman napin painaminen uudelleen purkaa rajauksen.
  b.onclick = () => {
    firstSel = firstSel === value ? null : value;
    clearTimeout(timer);
    run();
  };
  return b;
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
      '<div class="src">' + esc(q) + ' &nbsp;<span class="w2">' + esc(r.b) + '</span></div>' +
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
  firstSel = null;
  clearTimeout(timer);
  run();
  return !!h;
}

window.addEventListener('hashchange', applyHash);

$more.onclick = appendMore;
$q.addEventListener('input', () => { firstSel = null; syncClear(); schedule(); });

/* Tyhjennys palauttaa sivun alkutilaan: run() tyhjalla kentalla nollaa
   tulokset, osoitepalkin #-osan ja tuo esimerkit takaisin. */
$clear.addEventListener('click', () => {
  $q.value = '';
  firstSel = null;
  clearTimeout(timer);
  $q.focus();
  run();
});
// Järjestys ei muuta osumajoukkoa, joten rajaus säilyy. Suodattimet sen sijaan
// voivat pudottaa valitun sanan kokonaan pois, joten valinta puretaan.
$sort.addEventListener('change', run);
$onlyBase.addEventListener('change', () => { firstSel = null; run(); });
$noProper.addEventListener('change', () => { firstSel = null; run(); });
