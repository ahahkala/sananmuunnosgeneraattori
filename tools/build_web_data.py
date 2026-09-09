# -*- coding: utf-8 -*-
"""Pakkaa sanamuodot selainta varten.

Sanat koodataan omalla yksitavuisella aakkostolla, jotta selaimessa voi
lukea sanoja tavutasolla ilman UTF-8-purkua.

web/data/words.bin.gz  etuliitekoodattu, aakkosjärjestyksessä:
                       [jaetun etuliitteen pituus][loppuosan koodit][0]
web/data/flags.bin.gz  1 tavu / sana: 1 = perusmuoto, 2 = ei erisnimi,
                       4 = yleiskielinen, 8 = kelpaa esimerkiksi,
                       16 = karkea kieli, 32 = ei yhdyssanan loppuosaksi
web/data/meta.json     aakkosto ja sanamäärä

Käyttö:
    python tools/build_web_data.py            kirjoittaa web/data/
    python tools/build_web_data.py --check    vertaa web/data/ sisältöä
                                              lähdeaineistoon, ei kirjoita
"""
import gzip
import io
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'build', 'wordforms.txt')
OUT = os.path.join(ROOT, 'web', 'data')


def build():
    """Rakenna selaimen tavupuskurit muistiin."""
    rows = []
    chars = set()
    for line in io.open(SRC, encoding='utf-8'):
        w, f = line.rstrip('\n').split('\t')
        rows.append((w, int(f)))
        chars.update(w)

    alphabet = ''.join(sorted(chars))
    assert len(alphabet) < 250, 'aakkosto liian iso yksitavuiseksi'
    code = {c: i + 1 for i, c in enumerate(alphabet)}   # 0 = erotin

    buf = bytearray()
    flags = bytearray()
    prev = b''
    for w, f in rows:
        cur = bytes(code[c] for c in w)
        n, m = 0, min(len(prev), len(cur), 200)
        while n < m and prev[n] == cur[n]:
            n += 1
        buf.append(n)
        buf += cur[n:]
        buf.append(0)
        flags.append(f)
        prev = cur

    meta = {'alphabet': alphabet, 'count': len(rows),
            'totalChars': sum(len(w) for w, _ in rows)}
    return bytes(buf), bytes(flags), meta


def write(words, flags, meta):
    os.makedirs(OUT, exist_ok=True)
    for name, data in (('words.bin', words), ('flags.bin', flags)):
        path = os.path.join(OUT, name + '.gz')
        # mtime=0 ja tyhjä filename pitävät tuloksen vakaana saman koneen
        # ajojen välillä, jottei pelkkä uudelleenajo tuota turhaa diffiä.
        # HUOM: pakatut tavut eivät ole vertailukelpoisia eri koneiden
        # välillä – zlibin versio vaikuttaa tulokseen. Käytä --check.
        with open(path, 'wb') as raw:
            with gzip.GzipFile(filename='', mode='wb', compresslevel=9,
                               fileobj=raw, mtime=0) as f:
                f.write(data)
        print('%-11s %8d -> %7d' % (name, len(data), os.path.getsize(path)))
    with io.open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False)
    print('sanoja:', meta['count'], 'aakkosto:', meta['alphabet'])


def _first_diff(a, b):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else -1


def check(words, flags, meta):
    """Vertaa julkaistua web/data/ hakemistoa lähdeaineistoon.

    Vertailu tehdään puretulle sisällölle, ei pakatuille tavuille: gzipin
    tuloste riippuu zlibin versiosta, joten eri koneilla pakatut tiedostot
    eroavat tavutasolla vaikka sisältö olisi sama.
    """
    problems = []
    for name, want in (('words.bin', words), ('flags.bin', flags)):
        path = os.path.join(OUT, name + '.gz')
        if not os.path.exists(path):
            problems.append('%s puuttuu' % path)
            continue
        with gzip.open(path, 'rb') as f:
            got = f.read()
        if got != want:
            i = _first_diff(got, want)
            problems.append(
                '%s: sisältö eroaa (julkaistu %d tavua, lähteestä %d tavua, '
                'ensimmäinen ero kohdassa %d)' % (name, len(got), len(want), i))

    mpath = os.path.join(OUT, 'meta.json')
    if not os.path.exists(mpath):
        problems.append('%s puuttuu' % mpath)
    else:
        got = json.load(io.open(mpath, encoding='utf-8'))
        if got != meta:
            problems.append('meta.json eroaa: julkaistu %r, lähteestä %r'
                            % (got, meta))

    if problems:
        print('web/data/ ei vastaa lähdeaineistoa:', file=sys.stderr)
        for p in problems:
            print('  - ' + p, file=sys.stderr)
        print('\nAja "python tools/build_web_data.py" ja commitoi web/data/.',
              file=sys.stderr)
        return 1
    print('web/data/ vastaa lähdeaineistoa (%d sanaa, %d + %d tavua purettuna)'
          % (meta['count'], len(words), len(flags)))
    return 0


def main():
    words, flags, meta = build()
    if '--check' in sys.argv[1:]:
        return check(words, flags, meta)
    write(words, flags, meta)
    return 0


if __name__ == '__main__':
    sys.exit(main())
