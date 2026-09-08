# CLAUDE.md

Ohjeet agentille tässä projektissa. Lue myös [README.md](README.md) – siinä on
projektin kuvaus ja sananmuunnoksen säännöt.

## ⚠️ Älä koskaan lue datatiedostoja kokonaan

Projektissa on isoja datatiedostoja. Niiden lukeminen kokonaan täyttää
kontekstin turhaan.

| Tiedosto | Koko | Riveja |
|---|---|---|
| `vendor/joukahainen.xml` | 8,7 Mt | 511 735 |
| `build/lemmas.json` | 2,5 Mt | 1 (yksi JSON-rivi!) |
| `build/wordforms.txt` | 15 Mt | 993 276 |
| `web/data/*.gz` | 490 kt | binääri |

**Älä käytä Read-työkalua näihin.** Älä myöskään `cat`, `grep` ilman rajausta,
`sort`, `jq .` tai `json.load` + `print`. Ota aina pieni otos:

```bash
sed -n '200000,200060p' vendor/joukahainen.xml     # pätkä keskeltä
grep -m 20 '<wclass>verb' vendor/joukahainen.xml   # rajaa osumamäärä
grep -c '<word id' vendor/joukahainen.xml          # pelkkä lukumäärä
shuf -n 30 build/wordforms.txt              # satunnaisotos
grep -E "^(kissa|kissan|kissoja)	" build/wordforms.txt  # tarkat sanat, TAB perässä
```

Yhteenvedot lasketaan skriptillä, joka tulostaa vain tuloksen – ei dataa:

```bash
python - <<'EOF'
import json, collections
d = json.load(open('build/lemmas.json', encoding='utf-8'))
c = collections.Counter(i for e in d for i in e['i'])
print(c.most_common(20))          # vain yhteenveto ulos
EOF
```

Sama koskee testiajojen tulosteita: putkita `| head -40` tai `| tail -20`.
`tools/test_search.mjs` tulostaa kymmeniä rivejä, ei satojatuhansia – mutta jos
lisäät sinne tulostusta, rajaa se.

## Ympäristö

- Windows, PowerShell + Git Bash. Bash-työkalu on kätevämpi näihin komentoihin.
- **Aseta aina `export PYTHONIOENCODING=utf-8`** ennen Python-ajoja, muutoin
  ä/ö tulostuu mojibakena konsoliin.
- Python 3.14, Node 22. Ei riippuvuuksia – vain vakiokirjastot.
- **Heredoc-rajoite:** yli ~150 rivin `cat > tiedosto <<'EOF'` epäonnistui
  ("unexpected EOF"). Kirjoita isot tiedostot Write-työkalulla, pienet
  paikkaukset Edit-työkalulla tai lyhyellä Python-skriptillä.

## Rakennusputki

Ajojärjestys on pakollinen – jokainen vaihe lukee edellisen tuotoksen:

```bash
export PYTHONIOENCODING=utf-8
python tools/parse_joukahainen.py    # vendor/joukahainen.xml -> build/lemmas.json
python tools/generate.py             # lemmas.json           -> build/wordforms.txt
python tools/build_web_data.py       # wordforms.txt         -> web/data/*.gz
```

Datahakemistoja on kolme, älä sekoita niitä:
`vendor/` = ulkoinen lähdeaineisto, `build/` = kertakäyttöiset välitulokset
(ei versionhallinnassa, voi poistaa milloin vain), `web/data/` = selaimelle
julkaistava artefakti (versionhallinnassa).

**Jos muutat `tools/morph.py` tai `tools/generate.py`, aja aina vaiheet 2 ja 3.**
Pelkkä `generate.py` ei riitä: selain lukee vain `web/data/`-hakemistoa, joten
muutos ei näy sivulla ennen `build_web_data.py`:tä.

`web/worker.js`- ja `web/app.js`-muutokset eivät vaadi uudelleengenerointia.

**Älä vertaa pakattuja tavuja koneiden välillä.** gzipin tuloste riippuu
zlibin versiosta, joten Windowsilla ja CI:n Ubuntulla pakatut `web/data/*.gz`
eroavat tavutasolla vaikka sisältö olisi identtinen. `mtime=0` pitää tuloksen
vakaana vain saman koneen ajojen välillä.

Ajantasaisuuden tarkistaa `python tools/build_web_data.py --check`, joka
purkaa julkaistut tiedostot ja vertaa **sisältöä** lähdeaineistoon.
Julkaisu-workflow (`.github/workflows/pages.yml`) ajaa sen, joten jos muutat
generaattoria etkä commitoi `web/data/`:ta, julkaisu pysähtyy.

## Testit – aja molemmat ennen kuin ilmoitat työn valmiiksi

```bash
python tools/test_morph.py           # 101 taivutusparadigmaa; pitää olla 101/101
node   tools/test_search.mjs | grep ristiintarkistus   # pitää olla "0 virhettä"
```

`test_morph.py` vertaa generoituja muotoja käsin kirjoitettuihin odotuksiin.
**Kun lisäät tai muutat taivutusluokkaa, lisää sille rivi `CASES`-listaan.**
Odotusmuodot pitää tarkistaa oikeasta suomesta, ei generaattorin tulosteesta –
muuten testi vain sementoi bugin.

`test_search.mjs` ajaa `web/worker.js`:n Nodessa (stubattu `fetch`/`self`) ja
tarkistaa jokaisesta hakutuloksesta sananmuunnoksen säännöt sekä sen, että
kaikki neljä sanaa löytyvät sanastosta. Se on rakenteellinen tarkistus: se ei
huomaa, jos itse sanasto sisältää virheellisen muodon.

## Sivun ajaminen selaimessa

Sivu vaatii HTTP-palvelimen (`fetch` ei toimi `file://`-osoitteesta):

```bash
cd web && python -m http.server 8123 &
```

Ulkoasun tai latauksen tarkistus oikeassa selaimessa (Chrome on koneella,
`chromium-cli`/Playwright ei):

```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new \
  --disable-gpu --no-sandbox --window-size=1100,1600 \
  --remote-debugging-port=9222 --user-data-dir=<temp-polku> http://localhost:8123/ &
```

Sen jälkeen aja CDP-skripti (Node 22:ssa on globaali `WebSocket`), joka hakee
`http://127.0.0.1:9222/json/list`, avaa page-targetin, syöttää hakusanan
`#q`-kenttään ja ottaa `Page.captureScreenshot`in. Kirjoita kuva **projektin
sisään** – `%TEMP%`-scratchpadiin kirjoitus estyy (0x5 Käyttö estetty). Poista
kuvat lopuksi.

Pelkkä `--screenshot`-lippu ei riitä: worker ei ehdi ladata sanastoa
`--virtual-time-budget`-tilassa, ja kuvaan jää "Ladataan sanastoa…".

## Osa-alueiden pitäminen synkassa

Kolme paikkaa koodaavat samaa asiaa. Jos muutat yhtä, muuta muut:

1. **Lippubitit.** `tools/generate.py` kirjoittaa ne, `tools/build_web_data.py`
   pakkaa ja `web/worker.js` lukee: `1` = perusmuoto, `2` = ei erisnimi,
   `4` = yleiskielinen (ei `dialect`/`old`). `incorrect`-tyyliset sanat
   pudotetaan kokonaan jo generoinnissa.
2. **Aakkosto.** `build_web_data.py` kirjoittaa `web/data/meta.json`:iin
   aakkoston; `worker.js` rakentaa siitä vokaali- ja sointutaulut. Jos
   sanastoon tulee uusia merkkejä, molemmat mukautuvat automaattisesti, mutta
   aakkoston on pysyttävä alle 250 merkissä (1 tavu / kirjain).
3. **Sananmuunnoksen määritelmä.** `web/worker.js`:n haku ja
   `tools/test_search.mjs`:n tarkistin toteuttavat saman säännön eri suunnista.
   Ne on tarkoituksella kirjoitettu erikseen – älä yhdistä niitä jaettuun
   moduuliin, koska silloin testi ei enää tarkista mitään.

## Toimialuetieto, jota koodista ei näe

**Astevaihteluluokat.** Joukahaisen `-avN` ei ole "vahva→heikko / heikko→vahva",
vaan ryhmittely konsonantin mukaan. Tämä johdettiin datasta, ei
dokumentaatiosta:

| Luokka | Vaihtelu | Hakumuoto |
|---|---|---|
| av1 | `kk→k, pp→p, tt→t, nt→nn, mp→mm, nk→ng, lt→ll, rt→rr, ht→hd, t→d, p→v, k→v` | vahva |
| av2 | av1:n käänteinen (`k→kk`, `d→t`, `mm→mp`, `v→p`, …) | heikko |
| av3 | `k→j` (`arki→arjen`) | vahva |
| av4 | `j→k` (`hylje→hylkeen`) | heikko |
| av5 | `k→∅` (`jalka→jalan`) | vahva |
| av6 | `∅→k` (`ies→ikeen`) | heikko |

Astevaihtelun paikka on **viimeistä vokaalia edeltävä konsonanttiklusteri**
(`morph.py: _split_site`). Verbiluokat katkaisevat vartalon ensin (esim.
`katsella`-luokka: `lemma[:-3]`), jotta paikka osuu oikeaan tavuun.
`av3`:ssa diftongin `i` katoaa: `aika→ajan`, `poika→pojan`.

**Sananmuunnoksen säännöt.** Pää = alkukonsonantit + ensimmäinen vokaali.
Vokaalin kesto jää paikalleen eikä seuraa päätä (`kaappi tuoli → tuuppi kaoli`).
Diftongista siirtyy vain ensimmäinen vokaali (`pöytä lilja → liuta pöljä`).
Vokaalisointua **ei korjata säännöllä** vaan sanastohaulla: hännät
indeksoidaan neutralisoituna (ä→a, ö→o, y→u), jolloin sanasto kertoo, kumpi
variantti on olemassa oleva sana.

**Yhdyssanojen sointu.** Naiivi "viimeinen ei-neutraali vokaali" -sääntö
tuottaa `sanomalehtea`. Korjaus (`generate.py: compound_harmony`) on
tarkoituksella **tarkkuus edellä**: se vaatii, että loppuosa on kuratoidulta
`NEUTRAL_HEADS`-listalta ja alkuosa on tunnettu sana. Ahnaampi
"pisin sanaston loppuosa" -heuristiikka rikkoo oikeat muodot (`aforismia` →
`aforismiä`, `amulettia`, `violettia`), koska monet johdinlopukkeet
(`-ismi`, `-isti`, `-letti`, `-veli`) näyttävät yhdyssanan loppuosilta.

**Epävarmat muodot jätetään pois.** Jos taivutusmuodon oikeellisuudesta ei ole
varmuutta, sitä ei generoida. Väärä muoto vuotaa hakutuloksiin sanana, jota ei
ole olemassa – se rikkoo koko tuotteen lupauksen. Esim. `asema`-luokan
O-monikko (`asemoita`) jätettiin pois, mutta `peruna`/`pasuuna` säilyttivät sen.

## Mitä lähdedatassa on

`vendor/joukahainen.xml` on Voikko-projektin sanasto (GPL), 39 612 sanaa.
`vendor/` sisältää ulkopuolista, eri lisenssin alaista aineistoa - älä muokkaa
sen tiedostoja, vaan päivitä ne alkuperäisestä lähteestä.
Rakenne: `<word>` → `<forms><form>`, `<classes><wclass>`, `<inflection><infclass>`,
`<style><flag>`.

- Ensimmäinen `<form>` on perusmuoto; muut ovat yhdyssanamerkittyjä
  kirjoitusasuja (`hannun=vaakuna`). `=`-merkintä **ei** kerro yhdyssanan
  loppuosaa, joten siitä ei ole apua vokaalisoinnussa.
- `<infclass type="historical">` on vanhentunut vaihtoehto – `parse_joukahainen.py`
  poimii vain attribuutittomat.
- Sanaluokat: `noun`, `verb`, `adjective`, `adverb`, `pnoun_*`, `abbreviation`,
  `prefix`, `interjection`, `conjunction`. Lyhenteet ja etuliitteet ohitetaan,
  taipumattomat sanaluokat generoidaan vain perusmuotona.
- Luokat `loppu` ja `poikkeava` ovat "ei automaattista taivutusta" -merkintöjä.
- Osa luokkanimistä esiintyy vain historiallisina (esim. `ahven`, `kantaja`,
  `pasuuna`) – niillä on kartta `generate.py`:ssä varmuuden vuoksi.

## Suoritusrajat, joita ei kannata rikkoa

- Selainlataus ~490 kt pakattua; purku + indeksointi ~300 ms. Jos sanamuotojen
  määrä kasvaa merkittävästi, tarkista lataus uudelleen.
- Haut 1–50 ms. `search()` valitsee raskaammasta päästä kevyemmän
  (`costH`/`costT`) – älä poista tätä optimointia.
- Pää pakataan 32 bittiin: enintään 4 alkukonsonanttia + vokaali, 6 bittiä
  kukin. Aakkoston on siis mahduttava 63 merkkiin.
