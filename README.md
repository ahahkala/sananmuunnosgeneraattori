# Sananmuunnosgeneraattori

Verkkosivu, johon kirjoitetaan **yksi** suomenkielinen sana missä tahansa
taivutusmuodossa. Sivu listaa heti kaikki sanat, joiden kanssa se muodostaa
kelvollisen sananmuunnoksen – eli parin, jonka alkutavut vaihtamalla syntyy
kaksi oikeaa suomen sanaa.

```
kissa  pieli   →   pissa  kieli
ilta   mukava  →   multa  ikävä
pöytä  lilja   →   liuta  pöljä
nähdä  teko    →   tehdä  näkö
```

**Demo: <https://ahahkala.github.io/sananmuunnosgeneraattori/>**

Hakusana tallentuu osoitteen `#`-osaan, joten yksittäiseen hakuun voi linkata
suoraan: <https://ahahkala.github.io/sananmuunnosgeneraattori/#kissa>.

Kaikki neljä sanaa (lähtösana, parisana ja molemmat tulokset) tarkistetaan
n. **993 000 sanamuodon** sanastosta, joka on generoitu Joukahaisen
perusmuodoista ja taivutusluokista.

## Käynnistys paikallisesti

Sivu on täysin staattinen – `web/`-hakemiston voi julkaista sellaisenaan;
GitHub Pages -julkaisun hoitaa [`.github/workflows/pages.yml`](.github/workflows/pages.yml).
Paikallisesti sivu tarvitsee HTTP-palvelimen (`fetch` ei toimi `file://`-osoitteesta).

```
start.cmd            # Windows: käynnistää palvelimen ja avaa selaimen
./serve.sh           # muut: http://localhost:8000/
```

Tai käsin:

```
cd web && python -m http.server 8000
```

Selaimelta vaaditaan `DecompressionStream` (Chrome 80+, Firefox 113+,
Safari 16.4+). Ensilatauksessa siirtyy ~490 kt pakattua dataa; sen jälkeen
haut ovat 1–50 ms.

## Miten se toimii

### Sananmuunnoksen säännöt

Sana jaetaan **päähän** ja **häntään**: pää = alkukonsonantit + ensimmäinen
vokaali, häntä = kaikki loput. Parin päät vaihdetaan keskenään, ja lisäksi:

* **Vokaalin kesto jää paikalleen**, ei seuraa päätä:
  `kaappi tuoli → tuuppi kaoli`.
* **Vokaalisointu korjautuu** uuden pään mukaan: `ilta mukava → multa ikävä`.
* Diftongista siirtyy vain ensimmäinen vokaali: `pöytä lilja → liuta pöljä`.

Sointukorjausta ei tehdä sääntönä vaan haun kautta: sanat indeksoidaan häntä
neutralisoituna (ä→a, ö→o, y→u), jolloin sanasto itse kertoo, kumpi
sointuvariantti on oikea sana.

### Haku

Sanastosta rakennetaan kaksi hakemistoa: pään ja hännän mukaan. Lähtösanalle
`S` haetaan

1. sanat, joilla on **S:n häntä** → näistä saadaan mahdolliset tulossanat `R1`
   ja samalla parisanan pää;
2. sanat, joilla on **S:n pää** → näistä saadaan mahdolliset tulossanat `R2` ja
   samalla parisanan häntä.

Parisana on sanaston sana, jolla on jokin (1):n pää ja jokin (2):n häntä.
Koska kaikki kolme sanaa poimitaan sanastosta, tulos on rakenteeltaan aina
kelvollinen. Työ tehdään web workerissa, joten käyttöliittymä ei jumitu.

### Sanaston generointi

`vendor/joukahainen.xml` (Voikko-projektin sanasto, GPL) sisältää n. 39 600
perusmuotoa taivutusluokkineen (suomi-malagan luokkanimet, esim. `risti-av1`).
`tools/morph.py` toteuttaa näiden luokkien taivutuksen: astevaihtelun
kuusi luokkaa (av1–av6), nominien 24 sijamuotoa yksikössä ja monikossa sekä
verbien n. 45 muotoa (preesens, imperfekti, konditionaali, imperatiivi,
passiivi, partisiipit, infinitiivit).

```
python tools/parse_joukahainen.py    # XML -> build/lemmas.json
python tools/generate.py             # -> build/wordforms.txt (~993 000 riviä)
python tools/build_web_data.py       # -> web/data/*.gz
python tools/stamp_assets.py         # versioleima index.html:ään
```

### Testit

```
python tools/test_morph.py     # 101 taivutusparadigmaa tunnettuja muotoja vastaan
node   tools/test_search.mjs   # ajaa worker.js:n Nodessa ja ristiintarkistaa
                               # ~240 000 hakutulosta sananmuunnoksen sääntöjä vastaan
```

## Rajaukset

* Sanasto on generoitu, ei korpuksesta poimittu: se sisältää muotoja, jotka
  ovat morfologisesti oikein mutta harvinaisia (esim. abstraktien
  substantiivien monikkoja).
* Yleisyystietoa ei ole saatavilla, joten tulosten järjestys perustuu
  heuristiikkaan: perusmuodot, yleisnimet, yleiskieliset sanat ja arkipituiset
  (5–10 merkkiä) sanat nousevat ylös. Joukahaisen tyylimerkinnät
  `dialect`/`old` laskevat sijoitusta, `incorrect`-sanat on jätetty pois.
* Yhdyssanojen vokaalisointu päätellään sanan lopusta. Tapaukset, joissa
  loppuosassa on vain neutraalit vokaalit (`sanomalehti` → `sanomalehteä`),
  tunnistetaan erillisen yhdyssanalistan avulla; harvinaisimmat tällaiset
  yhdyssanat voivat jäädä väärään sointuun.
* Yhdysmerkilliset ja välilyönnilliset hakusanat on jätetty sanastosta pois.

## Tiedostot

```
vendor/joukahainen.xml     lähdesanasto (Voikko-projekti, GPL)
build/                     generoidut välitulokset (ei versionhallinnassa)
tools/parse_joukahainen.py XML-jäsennin
tools/morph.py             taivutusmoottori
tools/generate.py          taivutusluokkien kartta + sanamuotojen generointi
tools/build_web_data.py    selaimen binäärimuotojen pakkaus
tools/stamp_assets.py      välimuistin ohittava versioleima
tools/test_morph.py        taivutustestit
tools/test_search.mjs      hakukoneen testit
web/index.html             käyttöliittymä
web/app.js                 näkymä
web/worker.js              sanaston lataus, indeksointi ja haku
web/data/                  pakattu sanasto
```

Sanasto on peräisin [Joukahaisesta](https://joukahainen.puimula.org/)
(Voikko-projekti) ja on GPL-lisensoitu.
