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
  src + '\n; return { search, lookupExact, init };');
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
  const a = split(q), b = split(r.b), x = split(r.r1), y = split(r.r2);
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
  for (const s of [r.b, r.r1, r.r2]) {
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

console.log('\n== näytteitä ==');
for (const q of ['kissa', 'kahvi', 'pöytä', 'nähdä', 'ilta', 'yö']) {
  const r = w.search(q, { limit: 10, noProper: true, onlyBase: true });
  console.log(`\n${q} (${r.total}):`);
  for (const x of (r.results || []).slice(0, 6)) {
    console.log(`   ${q} ${x.b}  →  ${x.r1} ${x.r2}`);
  }
}
process.exit(bad ? 1 : 0);
