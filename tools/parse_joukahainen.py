# -*- coding: utf-8 -*-
"""Parse vendor/joukahainen.xml into a compact JSON list of lexicon entries."""
import json, re, sys, os

SRC = os.path.join(os.path.dirname(__file__), '..', 'vendor', 'joukahainen.xml')
OUT = os.path.join(os.path.dirname(__file__), '..', 'build', 'lemmas.json')

word_re = re.compile(r'<word id="[^"]*">(.*?)</word>', re.S)
form_re = re.compile(r'<form>([^<]*)</form>')
wclass_re = re.compile(r'<wclass>([^<]*)</wclass>')
inf_re = re.compile(r'<infclass>([^<]*)</infclass>')   # only non-historical (no type attr)
flag_re = re.compile(r'<flag>([^<]*)</flag>')
style_re = re.compile(r'<style>(.*?)</style>', re.S)

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(SRC, encoding='utf-8') as f:
        text = f.read()
    out = []
    for m in word_re.finditer(text):
        body = m.group(1)
        forms = form_re.findall(body)
        if not forms:
            continue
        # first <form> is the base form; others are compound-split spellings
        base = forms[0]
        if '=' in base or '|' in base:
            base = base.replace('=', '').replace('|', '')
        wclasses = wclass_re.findall(body)
        infs = inf_re.findall(body)
        st = style_re.search(body)
        styles = flag_re.findall(st.group(1)) if st else []
        out.append({
            'w': base,
            'c': wclasses,
            'i': infs,
            's': styles,
        })
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    print('entries:', len(out))

main()
