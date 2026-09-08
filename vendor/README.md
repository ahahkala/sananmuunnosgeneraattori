# vendor/

Ulkopuolista aineistoa. **Älä muokkaa näitä tiedostoja käsin** – päivitä ne
alkuperäisestä lähteestä. Aineistolla on oma lisenssinsä, joka on eri kuin
tämän projektin oma koodi.

## joukahainen.xml

- **Lähde:** https://avoindata.suomi.fi/data/fi/dataset/joukahainen-suomen-kielen-sanastotietokanta
- **Lisenssi:** GNU GPL v2 tai uudempi
- **Tekijänoikeus:** ks. Suomi-malagan `CONTRIBUTORS`-tiedosto
- **Sisältö:** 39 612 suomen kielen perusmuotoa taivutusluokkineen
- **Haettu:** 2026-09-08 (tiedoston generointiaika 2026-09-08 04:26 EEST,
  merkitty XML:n alkukommenttiin)

Päivitys: lataa uusi vienti Joukahaisesta tämän tiedoston tilalle ja aja

```
python tools/parse_joukahainen.py
python tools/generate.py
python tools/build_web_data.py
python tools/test_morph.py
node   tools/test_search.mjs
```

Uusi vienti voi tuoda mukanaan taivutusluokkia, joita `tools/generate.py`
ei tunne. Ne tulostuvat ajossa rivillä `tuntemattomat luokat:` – tällaiset
sanat päätyvät sanastoon vain perusmuodossa, kunnes luokka lisätään
`NOMINALS`- tai `VERBS`-karttaan.
