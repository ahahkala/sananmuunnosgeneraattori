# -*- coding: utf-8 -*-
"""Pakkaa sanamuodot selainta varten.

Sanat koodataan omalla yksitavuisella aakkostolla, jotta selaimessa voi
lukea sanoja tavutasolla ilman UTF-8-purkua.

web/data/words.bin.gz  etuliitekoodattu, aakkosjärjestyksessä:
                       [jaetun etuliitteen pituus][loppuosan koodit][0]
web/data/flags.bin.gz  1 tavu / sana: bitti 0 = perusmuoto, bitti 1 = yleisnimi
web/data/meta.json     aakkosto ja sanamäärä
"""
import gzip
import io
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'build', 'wordforms.txt')
OUT = os.path.join(ROOT, 'web', 'data')


def main():
    os.makedirs(OUT, exist_ok=True)
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

    for name, data in (('words.bin', bytes(buf)), ('flags.bin', bytes(flags))):
        path = os.path.join(OUT, name + '.gz')
        # mtime=0 ja tyhjä filename: sama syöte tuottaa aina samat tavut,
        # jolloin web/data/ voidaan tarkistaa versionhallintaa vasten CI:ssä.
        with open(path, 'wb') as raw:
            with gzip.GzipFile(filename='', mode='wb', compresslevel=9,
                               fileobj=raw, mtime=0) as f:
                f.write(data)
        print('%-11s %8d -> %7d' % (name, len(data), os.path.getsize(path)))

    meta = {'alphabet': alphabet, 'count': len(rows),
            'totalChars': sum(len(w) for w, _ in rows)}
    with io.open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False)
    print('sanoja:', len(rows), 'aakkosto:', alphabet)


if __name__ == '__main__':
    main()
