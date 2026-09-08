/* Sananmuunnosgeneraattorin hakukone.
 *
 * Sanasto pidetään yhtenä tavupuskurina, jossa jokainen kirjain on yksi tavu
 * (oma aakkosto, ks. tools/build_web_data.py). Sanat indeksoidaan kahdesti:
 *   pää  = alkukonsonantit + ensimmäinen vokaali
 *   häntä = loput sanasta, vokaalisointu neutralisoituna (ä->a, ö->o, y->u)
 *          + ensimmäisen vokaalin kesto
 * Sananmuunnoksessa vaihtuu vain pää, joten parin toinen sana löytyy
 * yhdistämällä sopiva pää ja sopiva häntä ja tarkistamalla sanaston kautta,
 * että syntynyt sana on olemassa.
 */
'use strict';

var A = '';           // aakkosto
var codes = null;     // kaikki sanat peräkkäin, 1 tavu / kirjain
var offs = null;      // sanan i alku = offs[i], loppu = offs[i+1]
var flags = null;     // 1 = perusmuoto, 2 = ei erisnimi, 4 = yleiskielinen
var vpos = null;      // ensimmäisen vokaalin sijainti sanan sisällä
var vlen = null;      // ensimmäisen vokaalin kesto (1 tai 2)
var N = 0;

var isVowel = new Uint8Array(64);
var normCode = new Uint8Array(64);   // vokaalisoinnun neutralointi
var backV = new Uint8Array(64);
var frontV = new Uint8Array(64);
var charToCode = Object.create(null);

var headIx = null, tailIx = null;

function post(m) { self.postMessage(m); }

// ------------------------------------------------------------ lataus
async function loadGz(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(url + ': ' + res.status);
  const buf = new Uint8Array(await res.arrayBuffer());
  // Osa staattisista palvelimista tarjoaa .gz-tiedoston otsakkeella
  // Content-Encoding: gzip, jolloin selain on purkanut sen jo valmiiksi.
  // Puretaan siis vain, jos data alkaa gzip-tunnisteella 1f 8b.
  if (buf.length < 2 || buf[0] !== 0x1f || buf[1] !== 0x8b) return buf;
  if (typeof DecompressionStream === 'undefined') {
    throw new Error('Selain ei tue DecompressionStream-rajapintaa.');
  }
  const stream = new Response(buf).body.pipeThrough(new DecompressionStream('gzip'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

function setupAlphabet(alphabet) {
  A = alphabet;
  for (let i = 0; i < alphabet.length; i++) {
    const c = alphabet[i], code = i + 1;
    charToCode[c] = code;
    normCode[code] = code;
  }
  const map = { 'ä': 'a', 'ö': 'o', 'y': 'u' };
  for (const k in map) {
    if (charToCode[k] && charToCode[map[k]]) normCode[charToCode[k]] = charToCode[map[k]];
  }
  for (const c of 'aeiouyäöå') if (charToCode[c]) isVowel[charToCode[c]] = 1;
  for (const c of 'aou') if (charToCode[c]) backV[charToCode[c]] = 1;
  for (const c of 'äöy') if (charToCode[c]) frontV[charToCode[c]] = 1;
}

function expand(packed, count, totalChars) {
  codes = new Uint8Array(totalChars);
  offs = new Uint32Array(count + 1);
  let p = 0, w = 0, out = 0;
  while (w < count) {
    const shared = packed[p++];
    offs[w] = out;
    // kopioi jaettu etuliite edellisestä sanasta
    const prevStart = w > 0 ? offs[w - 1] : 0;
    for (let k = 0; k < shared; k++) codes[out++] = codes[prevStart + k];
    while (packed[p] !== 0) codes[out++] = packed[p++];
    p++;
    w++;
  }
  offs[count] = out;
  N = count;
}

function parseAll() {
  vpos = new Uint8Array(N);
  vlen = new Uint8Array(N);
  const hkey = new Uint32Array(N);
  const tkey = new Uint32Array(N);
  for (let i = 0; i < N; i++) {
    const s = offs[i], e = offs[i + 1];
    let j = s;
    while (j < e && !isVowel[codes[j]]) j++;
    if (j >= e) { vpos[i] = 255; hkey[i] = 0xffffffff; tkey[i] = 0xffffffff; continue; }
    const on = j - s;
    const v = codes[j];
    const len = (j + 1 < e && codes[j + 1] === v) ? 2 : 1;
    vpos[i] = on;
    vlen[i] = len;
    hkey[i] = packHead(codes, s, on, v);
    tkey[i] = hashTail(codes, j + len, e, len);
  }
  return { hkey, tkey };
}

// Pää mahtuu 32 bittiin: enintään 4 alkukonsonanttia + vokaali, 6 bittiä kukin.
function packHead(arr, start, onsetLen, v) {
  if (onsetLen > 4) return 0xffffffff;
  let h = 0;
  for (let k = 0; k < 4; k++) {
    h = (h << 6) | (k < onsetLen ? arr[start + k] : 0);
  }
  return ((h << 6) | v) >>> 0;
}

function hashTail(arr, from, to, len) {
  let h = (2166136261 ^ len) >>> 0;
  for (let k = from; k < to; k++) {
    h = (h ^ normCode[arr[k]]) >>> 0;
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h === 0xffffffff ? 1 : h;
}

function buildIndex(keys) {
  const map = new Map();
  const gid = new Uint32Array(N);
  let g = 0;
  for (let i = 0; i < N; i++) {
    const k = keys[i];
    if (k === 0xffffffff) { gid[i] = 0xffffffff; continue; }
    let x = map.get(k);
    if (x === undefined) { x = g++; map.set(k, x); }
    gid[i] = x;
  }
  const start = new Uint32Array(g + 1);
  let used = 0;
  for (let i = 0; i < N; i++) if (gid[i] !== 0xffffffff) { start[gid[i] + 1]++; used++; }
  for (let j = 1; j <= g; j++) start[j] += start[j - 1];
  const items = new Uint32Array(used);
  const pos = start.slice(0, g);
  for (let i = 0; i < N; i++) {
    const j = gid[i];
    if (j !== 0xffffffff) items[pos[j]++] = i;
  }
  return { map, gid, start, items };
}

async function init() {
  post({ type: 'status', text: 'Ladataan sanastoa…' });
  const meta = await (await fetch('data/meta.json')).json();
  setupAlphabet(meta.alphabet);
  const [packed, fl] = await Promise.all([
    loadGz('data/words.bin.gz'),
    loadGz('data/flags.bin.gz'),
  ]);
  flags = fl;
  post({ type: 'status', text: 'Puretaan sanastoa…' });
  expand(packed, meta.count, meta.totalChars);
  post({ type: 'status', text: 'Rakennetaan hakemistoa…' });
  const { hkey, tkey } = parseAll();
  headIx = buildIndex(hkey);
  headIx.key = hkey;
  tailIx = buildIndex(tkey);
  tailIx.key = tkey;
  post({ type: 'ready', count: N });
}

// ------------------------------------------------------------ apurit
function wordStr(i) {
  let s = '';
  for (let p = offs[i], e = offs[i + 1]; p < e; p++) s += A[codes[p] - 1];
  return s;
}

function group(ix, key) {
  const g = ix.map.get(key);
  if (g === undefined) return null;
  return [ix.start[g], ix.start[g + 1]];
}

function tailEqualsNorm(i, arr) {
  const s = offs[i] + vpos[i] + vlen[i], e = offs[i + 1];
  if (e - s !== arr.length) return false;
  for (let k = 0; k < arr.length; k++) if (normCode[codes[s + k]] !== arr[k]) return false;
  return true;
}

function tailEqualsWordTail(i, j) {
  const si = offs[i] + vpos[i] + vlen[i], ei = offs[i + 1];
  const sj = offs[j] + vpos[j] + vlen[j], ej = offs[j + 1];
  if (ei - si !== ej - sj) return false;
  for (let k = 0; k < ei - si; k++) {
    if (normCode[codes[si + k]] !== normCode[codes[sj + k]]) return false;
  }
  return true;
}

/* Sanan hännän sointuluokka: 1 = takavokaalinen, 2 = etuvokaalinen, 0 = neutraali */
function tailHarmony(i) {
  let r = 0;
  for (let p = offs[i] + vpos[i] + vlen[i], e = offs[i + 1]; p < e; p++) {
    if (backV[codes[p]]) return 1;
    if (frontV[codes[p]]) r = 2;
  }
  return r;
}

function headHarmony(i) {
  const v = codes[offs[i] + vpos[i]];
  return backV[v] ? 1 : (frontV[v] ? 2 : 0);
}

/* Valitse listalta se sana, jonka häntä sopii soinnultaan kohteen päähän. */
function pickHarmonic(list, headOwner) {
  if (list.length === 1) return list[0];
  const want = headHarmony(headOwner);
  for (const c of list) {
    const th = tailHarmony(c);
    if (th === 0 || want === 0 || th === want) return c;
  }
  return list[0];
}

// ------------------------------------------------------------ haku
function toCodes(text) {
  const out = [];
  for (const ch of text.toLowerCase()) {
    const c = charToCode[ch];
    if (c === undefined) return null;
    out.push(c);
  }
  return out;
}

function search(text, opts) {
  const q = toCodes(text.trim());
  if (!q || q.length < 2) return { error: 'short' };
  let j = 0;
  while (j < q.length && !isVowel[q[j]]) j++;
  if (j >= q.length) return { error: 'novowel' };
  const qOnset = j, qV = q[j];
  const qVlen = (j + 1 < q.length && q[j + 1] === qV) ? 2 : 1;
  const qHead = packHead(q, 0, qOnset, qV);
  if (qHead === 0xffffffff) return { error: 'head' };
  const qTail = [];
  for (let k = j + qVlen; k < q.length; k++) qTail.push(normCode[q[k]]);
  const qTailKey = hashTail(q, j + qVlen, q.length, qVlen);

  // R1-ehdokkaat: sanat, joilla on lähtösanan häntä (ja sama vokaalin kesto)
  const heads = new Map();          // head-gid -> [sanaindeksit]
  const tr = group(tailIx, qTailKey);
  if (tr) {
    for (let p = tr[0]; p < tr[1]; p++) {
      const x = tailIx.items[p];
      if (vlen[x] !== qVlen || !tailEqualsNorm(x, qTail)) continue;
      const g = headIx.gid[x];
      if (g === 0xffffffff) continue;
      const l = heads.get(g);
      if (l) l.push(x); else heads.set(g, [x]);
    }
  }
  // R2-ehdokkaat: sanat, joilla on lähtösanan pää
  const tails = new Map();          // tail-gid -> [sanaindeksit]
  const hr = group(headIx, qHead);
  if (hr) {
    for (let p = hr[0]; p < hr[1]; p++) {
      const y = headIx.items[p];
      const g = tailIx.gid[y];
      if (g === 0xffffffff) continue;
      const l = tails.get(g);
      if (l) l.push(y); else tails.set(g, [y]);
    }
  }
  if (!heads.size || !tails.size) return { results: [], total: 0 };

  // Käy läpi se puoli, jonka kautta ehdokkaita on vähemmän.
  let costH = 0, costT = 0;
  for (const g of heads.keys()) costH += headIx.start[g + 1] - headIx.start[g];
  for (const g of tails.keys()) costT += tailIx.start[g + 1] - tailIx.start[g];

  const hits = [];
  const consider = (w) => {
    if (headIx.key[w] === qHead) return;          // pää ei vaihtuisi
    const xs = heads.get(headIx.gid[w]);
    if (!xs) return;
    if (xs.indexOf(w) >= 0) return;   // vaihto ei muuttaisi paria
    const ys = tails.get(tailIx.gid[w]);
    if (!ys) return;
    const good = [];
    for (const y of ys) if (vlen[y] === vlen[w] && tailEqualsWordTail(y, w)) good.push(y);
    if (!good.length) return;
    hits.push([w, pickHarmonic(xs, w), pickHarmonic(good, w)]);
  };

  if (costH <= costT) {
    for (const g of heads.keys()) {
      for (let p = headIx.start[g], e = headIx.start[g + 1]; p < e; p++) consider(headIx.items[p]);
    }
  } else {
    for (const g of tails.keys()) {
      for (let p = tailIx.start[g], e = tailIx.start[g + 1]; p < e; p++) consider(tailIx.items[p]);
    }
  }

  // Arkisanat ovat tyypillisesti 5-10 merkkiä; hyvin lyhyet ja hyvin pitkät
  // osumat ovat useammin harvinaisia lainoja tai pitkiä yhdyssanoja.
  const typical = (i) => {
    const n = offs[i + 1] - offs[i];
    return n >= 5 && n <= 10 ? 1 : (n >= 4 && n <= 12 ? 0.4 : 0);
  };
  const onlyBase = !!opts.onlyBase;
  const noProper = !!opts.noProper;
  const out = [];
  for (const h of hits) {
    const [w, r1, r2] = h;
    const fw = flags[w], f1 = flags[r1], f2 = flags[r2];
    if (noProper && !((fw & 2) && (f1 & 2) && (f2 & 2))) continue;
    if (onlyBase && !((fw & 1) && (f1 & 1) && (f2 & 1))) continue;
    const score = (fw & 1 ? 3 : 0) + (fw & 2 ? 2 : 0) + (fw & 4 ? 3 : 0) +
                  (f1 & 1 ? 1.5 : 0) + (f1 & 2 ? 1 : 0) + (f1 & 4 ? 1.5 : 0) +
                  (f2 & 1 ? 1.5 : 0) + (f2 & 2 ? 1 : 0) + (f2 & 4 ? 1.5 : 0) +
                  typical(w) + typical(r1) * 0.5 + typical(r2) * 0.5;
    out.push({ w, r1, r2, score });
  }
  out.sort((a, b) => b.score - a.score || (offs[a.w + 1] - offs[a.w]) - (offs[b.w + 1] - offs[b.w]));
  const total = out.length;
  const limit = opts.limit || 400;
  const results = out.slice(0, limit).map((r) => ({
    b: wordStr(r.w),
    r1: wordStr(r.r1),
    r2: wordStr(r.r2),
    base: !!(flags[r.w] & 1),
    proper: !(flags[r.w] & 2),
  }));
  return { results, total };
}

function lookupExact(text) {
  const q = toCodes(text.trim().toLowerCase());
  if (!q) return false;
  let lo = 0, hi = N - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const s = offs[mid], e = offs[mid + 1];
    let cmp = 0;
    const n = Math.min(e - s, q.length);
    for (let k = 0; k < n; k++) {
      if (codes[s + k] !== q[k]) { cmp = codes[s + k] < q[k] ? -1 : 1; break; }
    }
    if (cmp === 0) cmp = (e - s) === q.length ? 0 : ((e - s) < q.length ? -1 : 1);
    if (cmp === 0) return true;
    if (cmp < 0) lo = mid + 1; else hi = mid - 1;
  }
  return false;
}

self.onmessage = function (ev) {
  const msg = ev.data;
  if (msg.type === 'init') {
    init().catch((err) => post({ type: 'error', text: String(err.message || err) }));
  } else if (msg.type === 'query') {
    const t0 = performance.now();
    let res;
    try {
      res = search(msg.q, msg.opts || {});
    } catch (err) {
      res = { error: 'fail', text: String(err.message || err) };
    }
    res.type = 'results';
    res.id = msg.id;
    res.ms = Math.round(performance.now() - t0);
    res.known = res.error ? false : lookupExact(msg.q);
    post(res);
  }
};
