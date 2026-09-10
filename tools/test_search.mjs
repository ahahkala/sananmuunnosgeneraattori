/* Ajaa web/worker.js:n Nodessa ja tarkistaa hakulogiikan. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const webdir = path.join(here, '..', 'web');

globalThis.fetch = async (url) => new Response(
  fs.readFileSync(path.join(webdir, url)), { status: 200 });

globalThis.self = { postMessage: () => {} };

const src = fs.readFileSync(path.join(webdir, 'worker.js'), 'utf8');
const mod = new Function('self', 'performance', 'DecompressionStream', 'Response', 'fetch',
  src + '\n; return { search, lookupExact, splitPoints, init };');
const w = mod(globalThis.self, performance, DecompressionStream, Response, globalThis.fetch);

const t0 = Date.now();
await w.init();
console.log('lataus', Date.now() - t0, 'ms\n');

const VOW = 'aeiouyäöå';
function split(s) {
  let i = 0;
  while (i < s.length && !VOW.includes(s[i])) i++;
  const v = s[i];
  const len = s[i + 1] === v ? 2 : 1;
  return { on: s.slice(0, i), v, len, tail: s.slice(i + len) };
}
const norm = (s) => s.replace(/ä/g, 'a').replace(/ö/g, 'o').replace(/y/g, 'u');

let bad = 0, checked = 0;
function check(q, r) {
  // Yhdyssanahaussa muunnos on tehty alkuosalle ja loppuosa liitetään R1:een
  // vasta näytettäessä. Tarkistus tehdään siis alkuosaa vasten, ja loppuosalle
  // erikseen: sen on oltava sanastossa ja hakusanan lopussa.
  if (r.suf) {
    if (!q.endsWith(r.suf) || !w.lookupExact(r.suf)) {
      bad++;
      console.log(`  VIRHE ${q}: kelvoton loppuosa ${r.suf}`);
      return;
    }
    q = q.slice(0, q.length - r.suf.length);
  }
  // Worker isontaa erisnimien alkukirjaimen näyttöä varten. Sääntötarkistus ja
  // sanastohaku tehdään sanaston omalla kirjoitusasulla eli pienellä.
  const bs = r.b.toLowerCase(), r1s = r.r1.toLowerCase(), r2s = r.r2.toLowerCase();
  const a = split(q), b = split(bs), x = split(r1s), y = split(r2s);
  const problems = [];
  // R1 = W:n pää + lähtösanan häntä (lähtösanan vokaalin kestolla)
  if (x.on !== b.on || x.v !== b.v) problems.push('R1:n pää ei ole parisanan pää');
  if (x.len !== a.len) problems.push('R1:n vokaalin kesto väärä');
  if (norm(x.tail) !== norm(a.tail)) problems.push('R1:n häntä ei ole lähtösanan häntä');
  // R2 = lähtösanan pää + W:n häntä (W:n vokaalin kestolla)
  if (y.on !== a.on || y.v !== a.v) problems.push('R2:n pää ei ole lähtösanan pää');
  if (y.len !== b.len) problems.push('R2:n vokaalin kesto väärä');
  if (norm(y.tail) !== norm(b.tail)) problems.push('R2:n häntä ei ole parisanan häntä');
  // kaikkien neljän sanan on löydyttävä sanastosta
  for (const s of [bs, r1s, r2s]) {
    if (!w.lookupExact(s)) problems.push('ei sanastossa: ' + s);
  }
  checked++;
  if (problems.length) {
    bad++;
    if (bad < 15) console.log(`  VIRHE ${q} ${r.b} -> ${r.r1} ${r.r2}: ${problems.join('; ')}`);
  }
}

const QUERIES = ['kissa', 'talo', 'sana', 'koti', 'raha', 'auto', 'kahvi', 'perse',
  'lautanen', 'talossa', 'juokseminen', 'ähky', 'hauska', 'juoksin', 'pöytä',
  'kaappi', 'strutsi', 'maito', 'hyvä', 'kova', 'tie', 'suo', 'yö', 'käsi',
  'ilta', 'mies', 'vesi', 'lumi', 'kaupunki', 'ostaa', 'nähdä', 'kirjoittaa'];

console.log('== nopeus ja tulosmäärät ==');
for (const q of QUERIES) {
  const t = Date.now();
  const r = w.search(q, { limit: 100000, noProper: false });
  const ms = Date.now() - t;
  console.log(`${q.padEnd(14)} ${String(r.total).padStart(7)} osumaa  ${String(ms).padStart(4)} ms`);
  for (const x of (r.results || [])) check(q, x);
}

console.log(`\n== ristiintarkistus: ${checked} tulosta, ${bad} virhettä ==`);

/* Parisanan alkurajaus: sen on annettava täsmälleen sama joukko kuin
   rajaamattoman haun suodattaminen jälkikäteen. */
console.log('\n== parisanan alkurajaus ==');
let pbad = 0;
for (const [q, pre] of [['kissa', 'ka'], ['talo', 'per'], ['pöytä', 'l'],
                        ['kahvi', 'muna'], ['sana', 'zzz']]) {
  const all = w.search(q, { limit: 100000, noProper: false });
  const want = (all.results || []).filter((r) => r.b.toLowerCase().startsWith(pre));
  const got = w.search(q, { prefix: pre, limit: 100000, noProper: false });
  const list = got.results || [];
  const problems = [];
  if (got.total !== want.length) problems.push(`total ${got.total} != ${want.length}`);
  if (list.length !== want.length) problems.push(`osumia ${list.length} != ${want.length}`);
  for (const r of list) {
    if (!r.b.toLowerCase().startsWith(pre)) { problems.push('ei ala oikein: ' + r.b); break; }
  }
  if (problems.length) { pbad++; console.log(`  VIRHE ${q} ${pre}: ${problems.join('; ')}`); }
  console.log(`${q.padEnd(8)} ${pre.padEnd(6)} ${String(got.total).padStart(6)} osumaa` +
              ` (rajaamaton ${all.total})`);
}
console.log(`rajaus: ${pbad} virhettä`);

/* Tuloksen ensimmäisen sanan rajaus. Ryhmien on katettava koko rajaamaton
   osumajoukko, ja yhden ryhmän valinnan on annettava täsmälleen sen ryhmän
   osumat - myös yhdyssanahaussa, jossa ryhmän nimi on R1 + liitetty loppuosa. */
console.log('\n== ensimmäisen sanan rajaus ==');
let gbad = 0;
for (const q of ['kissa', 'talo', 'pöytä', 'esimies']) {
  const all = w.search(q, { limit: 100000, noProper: false, groups: true, compound: true });
  const list = all.results || [];
  const groups = all.groups || [];
  const problems = [];
  const sum = groups.reduce((a, g) => a + g.n, 0);
  if (sum !== all.total) problems.push(`ryhmien summa ${sum} != ${all.total}`);
  if (new Set(groups.map((g) => g.w)).size !== groups.length) problems.push('ryhmä kahdesti');
  for (const g of groups.slice(0, 5)) {
    const want = list.filter((r) => r.r1 + r.suf === g.w);
    const got = w.search(q, { limit: 100000, noProper: false, compound: true, first: g.w });
    if (got.total !== g.n || want.length !== g.n) {
      problems.push(`${g.w}: ${got.total}/${want.length} != ${g.n}`);
    }
    for (const r of got.results || []) {
      if (r.r1 + r.suf !== g.w) { problems.push('väärä sana: ' + r.r1 + r.suf); break; }
    }
  }
  if (problems.length) { gbad++; console.log(`  VIRHE ${q}: ${problems.join('; ')}`); }
  console.log(`${q.padEnd(9)} ${String(groups.length).padStart(4)} eri ensimmäistä sanaa` +
              ` (${all.total} osumaa)`);
}
console.log(`ensimmäisen sanan rajaus: ${gbad} virhettä`);

/* Yhdyssanan alkuosalla haku. Varauma: tämä tarkistaa rakenteen, ei sitä onko
   koottu yhdyssana oikeaa suomea - ks. CLAUDE.md. */
console.log('\n== yhdyssanan alkuosa ==');
let cbad = 0;
for (const q of ['esimies', 'talvisota', 'kirjakauppa', 'kissanruoka', 'kesäloma',
                 'sähköposti', 'aurinkorasva', 'kissa']) {
  const plain = w.search(q, { limit: 100000, noProper: true });
  const r = w.search(q, { compound: true, limit: 100000, noProper: true });
  const list = r.results || [];
  const problems = [];
  if (plain.total && r.total !== plain.total) problems.push('suora haku muuttui');
  if (r.compound && plain.total) problems.push('varajako ajettiin vaikka suoria osumia oli');
  for (const x of list) {
    if (r.compound && !x.suf) { problems.push('osumasta puuttuu loppuosa'); break; }
    if (!r.compound && x.suf) { problems.push('loppuosa ilman yhdyssanahakua'); break; }
  }
  for (const x of list) check(q, x);
  if (problems.length) { cbad++; console.log(`  VIRHE ${q}: ${problems.join('; ')}`); }
  const s0 = list[0];
  console.log(`${q.padEnd(14)} ${String(r.total).padStart(6)} osumaa  jaot=[${(r.compound || []).join(' ')}]` +
    (s0 ? `  esim: ${q} ${s0.b} -> ${s0.r1}${s0.suf} ${s0.r2}` : ''));
}
{
  const r = w.search('esimies', { compound: true, limit: 100000, noProper: true });
  const hit = (r.results || []).find((x) => x.b === 'todistaa');
  const ok = hit && hit.r1 + hit.suf === 'tosimies' && hit.r2 === 'edistää';
  if (!ok) cbad++;
  console.log(`esimies todistaa -> tosimies edistää: ${ok ? 'ok' : 'PUUTTUU'}`);
}
console.log(`yhdyssanahaku: ${cbad} virhettä`);

/* Sanaston pistokoe. Nämä muodot tulevat Joukahaisen <vtype>- ja
   ei_ysj/ei_ys-merkinnöistä, joita generaattori ei muuten mistään tarkista:
   ilman niitä sanastoon syntyy "cowboynä" ja yhdyssanahaku jakaa
   "patriotism|ien". Sääntötarkistin ei huomaa kumpaakaan, koska molemmat ovat
   rakenteellisesti kelvollisia - vain sisältö on väärin. */
console.log('\n== sanaston pistokoe ==');
let vbad = 0;
for (const [word, want] of [['cowboyna', true], ['cowboynä', false],
                            ['playboyta', true], ['playboytä', false],
                            ['designereina', true], ['designereinä', false],
                            ['doyleilla', true], ['doyleillä', false]]) {
  const got = w.lookupExact(word);
  if (got !== want) { vbad++; console.log(`  VIRHE ${word}: ${got} != ${want}`); }
}
console.log(`vokaalisointu (vtype): ${vbad} virhettä`);
let sbad = 0;
for (const [q, banned, kept] of [['patriotismien', 'ien', null],
                                 ['kerrotunlaisesta', 'laisesta', null],
                                 ['kesäloma', 'ien', 'loma'],
                                 ['esimies', 'ies', 'mies']]) {
  const pts = w.splitPoints(q).map((p) => q.slice(p));
  if (pts.includes(banned)) { sbad++; console.log(`  VIRHE ${q}: kielletty loppuosa ${banned}`); }
  if (kept && !pts.includes(kept)) { sbad++; console.log(`  VIRHE ${q}: kelpo loppuosa ${kept} katosi`); }
}
console.log(`loppuosakielto (bitti 32): ${sbad} virhettä`);

console.log('\n== näytteitä ==');
for (const q of ['kissa', 'kahvi', 'pöytä', 'nähdä', 'ilta', 'yö']) {
  const r = w.search(q, { limit: 10, noProper: true, onlyBase: true });
  console.log(`\n${q} (${r.total}):`);
  for (const x of (r.results || []).slice(0, 6)) {
    console.log(`   ${q} ${x.b}  →  ${x.r1} ${x.r2}`);
  }
}
process.exit(bad || pbad || cbad || vbad || sbad ? 1 : 0);
