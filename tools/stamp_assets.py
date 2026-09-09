# -*- coding: utf-8 -*-
"""Kirjoittaa versioleiman web/index.html:ään.

Selain saa välimuistittaa app.js:n, worker.js:n ja sanastotiedostot pitkäksi
aikaa - ne ovat isoja eivätkä muutu usein. Ilman versioleimaa palaava kävijä
jää kiinni vanhaan versioon, ja pahimmillaan sekoitukseen, jossa uusi koodi
lukee vanhaa sanastoa (esim. uusi lippubitti puuttuu). Leima ratkaisee tämän:
kun sisältö muuttuu, osoite muuttuu, ja selain hakee tiedoston uudelleen.

Leima on sisällön tiiviste, ei juokseva numero tai aikaleima: samasta
sisällöstä syntyy aina sama leima, joten turhaa uudelleenlatausta ei tule
eikä diffiin ilmesty muutosta ilman syytä.

index.html itse ei ole leiman lähteenä eikä tarvitse leimaa: se on
aloitusdokumentti, jonka selain tarkistaa palvelimelta joka tapauksessa.

Käyttö:
    python tools/stamp_assets.py            päivittää web/index.html
    python tools/stamp_assets.py --check    kertoo, onko leima ajan tasalla
"""
import gzip
import hashlib
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
WEB = os.path.join(ROOT, 'web')
INDEX = os.path.join(WEB, 'index.html')

# Leimattavat: kaikki, mitä selain hakee erikseen index.html:n lataamisen
# jälkeen. Järjestys vaikuttaa tiivisteeseen, joten se on kiinteä.
PLAIN = ['app.js', 'worker.js', os.path.join('data', 'meta.json')]
GZIPPED = [os.path.join('data', 'words.bin.gz'), os.path.join('data', 'flags.bin.gz')]

STAMP_RE = re.compile(rb'(<script src="app\.js\?v=)([0-9a-f]{10})(">)')


def _norm(data):
    """CRLF -> LF. Windowsin työkopiossa rivinvaihdot ovat CRLF ja CI:n
    Linuxissa LF (core.autocrlf), joten raaka tavutiiviste eroaisi koneiden
    välillä ja --check hälyttäisi turhaan."""
    return data.replace(b'\r\n', b'\n')


def stamp():
    h = hashlib.sha256()
    for rel in PLAIN:
        with open(os.path.join(WEB, rel), 'rb') as f:
            h.update(_norm(f.read()))
    for rel in GZIPPED:
        # Puretaan ennen tiivistämistä: gzipin tuloste riippuu zlibin
        # versiosta, joten pakatut tavut eivät ole vertailukelpoisia
        # koneiden välillä vaikka sisältö olisi sama.
        with gzip.open(os.path.join(WEB, rel), 'rb') as f:
            h.update(f.read())
    return h.hexdigest()[:10].encode('ascii')


def main():
    want = stamp()
    with open(INDEX, 'rb') as f:
        html = f.read()
    m = STAMP_RE.search(html)
    if not m:
        print('web/index.html: app.js:n versioleimaa ei löytynyt - odotettu\n'
              '  <script src="app.js?v=xxxxxxxxxx"></script>', file=sys.stderr)
        return 1
    have = m.group(2)

    if '--check' in sys.argv[1:]:
        if have != want:
            print('web/index.html: versioleima on vanhentunut (%s, pitäisi olla %s).'
                  % (have.decode(), want.decode()), file=sys.stderr)
            print('Aja "python tools/stamp_assets.py" ja commitoi web/index.html.',
                  file=sys.stderr)
            return 1
        print('versioleima ajan tasalla:', have.decode())
        return 0

    if have == want:
        print('versioleima ennallaan:', have.decode())
        return 0
    with open(INDEX, 'wb') as f:
        f.write(STAMP_RE.sub(lambda mm: mm.group(1) + want + mm.group(3), html, count=1))
    print('versioleima %s -> %s' % (have.decode(), want.decode()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
