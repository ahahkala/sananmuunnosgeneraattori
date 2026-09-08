# -*- coding: utf-8 -*-
"""Luo taivutusmuotolistan build/lemmas.json -tiedostosta."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from morph import (AA, FORCE_HARM, Nom, Verb, nom_forms, verb_forms, grades, lastv, _v,
                   i_stem, n_valo, n_autio, n_karahka, n_risti, n_nalle,
                   n_kala, n_koira, n_asema, n_kulkija, n_korkea, n_suurempi,
                   n_vapaa, n_pii, n_suo, n_lovi, n_huuli, n_lumi, n_niemi,
                   n_susi, n_kansi, n_veitsi, n_sisar, n_askel, n_uistin,
                   n_onneton, n_sisin, n_nainen, n_vastaus, n_kalleus,
                   n_vieras, n_mies, n_ohut, n_kuollut, n_hame, n_minimal,
                   n_foreign, IRREGULAR_NOM, IRREGULAR_VERB,
                   v_type1, v_oida, v_saada, v_kaydä, v_nuolaista, v_tulla,
                   v_valita, v_juosta, v_nähdä, v_aleta, v_salata, v_katketa)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')

# --- imperfektin muodostimet ------------------------------------------
imp_i = lambda s: s + 'i'                       # sanoa -> sanoi
imp_drop = lambda s: s[:-1] + 'i'               # muistaa -> muisti
imp_si = lambda s: s[:-2] + 'si'                # huutaa -> huusi
imp_o = lambda s: s[:-1] + AA(s, 'Oi')          # kaivaa -> kaivoi

NOMINALS = {
    'valo': n_valo,
    'arvelu': lambda l, av: n_valo(l, av, extra_ita=True),
    'autio': n_autio,
    'video': n_autio,
    'karahka': n_karahka,
    'risti': n_risti,
    'siisti': n_risti,
    'suksi': n_lovi,
    'hapsi': n_lovi,
    'toholampi': n_risti,
    'paperi': lambda l, av: n_risti(l, av, paperi=True),
    'kalsium': lambda l, av: n_risti(l, av, cons=True),
    'edam': lambda l, av: n_risti(l, av, paperi=True, cons=True),
    'nalle': n_nalle,
    'kala': n_kala,
    'pitkä': n_koira,
    'poika': n_koira,
    'ruoka': n_koira,
    'nahka': n_kala,
    'ylkä': n_koira,
    'koira': n_koira,
    'matala': n_koira,
    'jumala': lambda l, av: n_koira(l, av, genpl_ain=True),
    'asema': n_asema,
    'peruna': lambda l, av: n_asema(l, av, o_plural=True),
    'pasuuna': lambda l, av: n_asema(l, av, o_plural=True),
    'kulkija': n_kulkija,
    'kantaja': n_kulkija,
    'apaja': lambda l, av: n_kulkija(l, av, also_ia=True),
    'korkea': n_korkea,
    'suurempi': n_suurempi,
    'vapaa': n_vapaa,
    'kamee': n_vapaa,
    'pii': n_pii,
    'tie': n_suo,
    'suo': n_suo,
    'lovi': n_lovi,
    'kiiski': n_lovi,
    'huuli': n_huuli,
    'tuohi': n_huuli,
    'lumi': n_lumi,
    'meri': lambda l, av: n_lumi(l, av, back_par=True),
    'niemi': n_niemi,
    'tuomi': n_niemi,
    'pieni': lambda l, av: n_huuli(l, av),
    'susi': n_susi,
    'tosi': n_susi,
    'kansi': n_kansi,
    'veitsi': n_veitsi,
    'lapsi': n_veitsi,
    'sisar': n_sisar,
    'ahven': n_sisar,
    'askel': n_askel,
    'uistin': n_uistin,
    'laidun': n_uistin,
    'onneton': n_onneton,
    'sisin': n_sisin,
    'vasen': n_sisin,
    'nainen': n_nainen,
    'vastaus': n_vastaus,
    'kalleus': n_kalleus,
    'vieras': n_vieras,
    'iäkäs': n_vieras,
    'kaunis': n_vieras,
    'autuas': n_vieras,
    'laupias': n_vieras,
    'valmis': n_vieras,
    'koiras': n_vieras,
    'altis': n_vieras,
    'mies': n_mies,
    'ohut': n_ohut,
    'kuollut': n_kuollut,
    'hame': n_hame,
    'terve': n_hame,
    'rosé': n_foreign,
    'spray': n_foreign,
    'parfait': n_minimal,
    'bébé': n_minimal,
    'loppu': n_minimal,
    'poikkeava': n_minimal,
    'haaksi': n_minimal,
    'banaali': n_minimal,
}

VERBS = {
    'punoa': lambda l, av: v_type1(l, av, imp_i),
    'antautua': lambda l, av: v_type1(l, av, imp_i),
    'sulaa': lambda l, av: v_type1(l, av, imp_drop),
    'aavistaa': lambda l, av: v_type1(l, av, imp_drop),
    'hidastaa': lambda l, av: v_type1(l, av, imp_drop),
    'muistaa': lambda l, av: v_type1(l, av, imp_drop),
    'loistaa': lambda l, av: v_type1(l, av, imp_drop),
    'kirjoittaa': lambda l, av: v_type1(l, av, imp_drop),
    'heittää': lambda l, av: v_type1(l, av, imp_drop),
    'inttää': lambda l, av: v_type1(l, av, imp_drop),
    'hujahtaa': lambda l, av: v_type1(l, av, imp_drop),
    'pahentaa': lambda l, av: v_type1(l, av, imp_si),
    'paleltaa': lambda l, av: v_type1(l, av, imp_si),
    'juontaa': lambda l, av: v_type1(l, av, imp_si),
    'murtaa': lambda l, av: v_type1(l, av, imp_si),
    'sukeltaa': lambda l, av: v_type1(l, av, imp_si),
    'hohtaa': lambda l, av: v_type1(l, av, imp_drop),
    'laittaa': lambda l, av: v_type1(l, av, imp_drop),
    'haastaa': lambda l, av: v_type1(l, av, imp_drop),
    'huutaa': lambda l, av: v_type1(l, av, imp_si),
    'vuotaa': lambda l, av: v_type1(l, av, imp_si),
    'soutaa': lambda l, av: v_type1(l, av, imp_drop, extra_impf=imp_si),
    'kaivaa': lambda l, av: v_type1(l, av, imp_o),
    'saartaa': lambda l, av: v_type1(l, av, imp_si, extra_impf=imp_o),
    'laskea': lambda l, av: v_type1(l, av, imp_drop, inf2_e_to_i=True),
    'tuntea': lambda l, av: v_type1(l, av, imp_si, inf2_e_to_i=True),
    'lähteä': lambda l, av: v_type1(l, av, imp_drop, inf2_e_to_i=True),
    'sallia': lambda l, av: v_type1(l, av, imp_drop),
    'taitaa': lambda l, av: v_type1(l, av, imp_si),
    'kaikaa': lambda l, av: v_type1(l, av, imp_o, defective=True),
    'voida': v_oida,
    'kanavoida': v_oida,
    'haravoida': v_oida,
    'saada': v_saada,
    'juoda': v_saada,
    'käydä': v_kaydä,
    'nuolaista': v_nuolaista,
    'kihistä': v_nuolaista,
    'kitistä': v_nuolaista,
    'tulla': v_tulla,
    'mennä': v_tulla,
    'purra': v_tulla,
    'katsella': v_tulla,
    'kirjoitella': v_tulla,
    'valita': v_valita,
    'juosta': v_juosta,
    'nähdä': v_nähdä,
    'aleta': v_aleta,
    'kevetä': v_aleta,
    'salata': v_salata,
    'saneerata': v_salata,
    'palata': v_salata,
    'katketa': v_katketa,
    'kohota': v_katketa,
    'haluta': v_katketa,
    'juoruta': v_katketa,
    'siivota': v_katketa,
}

# Pronominit, partikkelit ja muut umpiluokan sanat, joita Joukahaisessa ei ole.
EXTRA = """
minä minun minua minussa minusta minuun minulla minulta minulle minuksi minuna
sinä sinun sinua sinussa sinusta sinuun sinulla sinulta sinulle sinuksi sinuna
hän hänen häntä hänessä hänestä häneen hänellä häneltä hänelle häneksi hänenä
me meidän meitä meissä meistä meihin meillä meiltä meille meiksi meinä
te teidän teitä teissä teistä teihin teillä teiltä teille teiksi teinä
he heidän heitä heissä heistä heihin heillä heiltä heille heiksi heinä
se sen sitä siinä siitä siihen sillä siltä sille siksi sinä ne niiden niitä
niissä niistä niihin niillä niiltä niille niiksi niinä
tämä tämän tätä tässä tästä tähän tällä tältä tälle täksi tänä nämä näiden
näitä näissä näistä näihin näillä näiltä näille näiksi näinä
tuo tuon tuota tuossa tuosta tuohon tuolla tuolta tuolle tuoksi tuona nuo
noiden noita noissa noista noihin noilla noilta noille noiksi noina
joka jonka jota jossa josta johon jolla jolta jolle joksi jona jotka joiden
joita joissa joista joihin joilla joilta joille joiksi joina
mikä minkä mitä missä mistä mihin millä miltä mille miksi minä mitkä
kuka kenen ketä kenessä kenestä keneen kenellä keneltä kenelle keneksi kenenä
ketkä keiden keitä
itse itsensä itseä itsessä itsestä itseen itsellä itseltä itselle itseksi
kaikki kaiken kaikkea kaikessa kaikesta kaikkeen kaikella kaikelta kaikelle
kaikkien kaikkia kaikissa kaikista kaikkiin kaikilla kaikilta kaikille
moni monen monta monessa monesta moneen monella monelta monelle moneksi
muu muun muuta muussa muusta muuhun muulla muulta muulle muuksi muut muiden
muita muissa muista muihin muilla muilta muille
ja tai sekä eli mutta vaan kun jos vaikka koska että jotta kuin niin
ei en et emme ette eivät älä älköön älkää älkäämme älkööt
yksi yhden yhtä yhdessä yhdestä yhteen yhdellä yhdeltä yhdelle yhdeksi
kaksi kahden kahta kahdessa kahdesta kahteen kahdella kahdelta kahdelle
kolme kolmen kolmea neljä neljän neljää viisi viiden viittä kuusi kuuden
seitsemän kahdeksan yhdeksän kymmenen sata sadan sataa tuhat tuhannen tuhatta
"""

# Yhdyssanojen loppuosia, joissa on vain neutraalit vokaalit e ja i. Tällaisen
# lopun sisältävä yhdyssana taipuu etuvokaalisesti, vaikka alkuosassa olisi
# takavokaaleja: "sanomalehti" -> "sanomalehteä", ei "sanomalehtea".
NEUTRAL_HEADS = ('kivi', 'vesi', 'meri', 'niemi', 'lehti', 'tie', 'mies',
                 'kieli', 'mieli', 'hetki', 'henki', 'pilvi', 'veri', 'peili',
                 'metri', 'seksi', 'liike', 'viesti', 'este', 'viive', 'ilme',
                 'keli', 'penkki', 'kirje', 'hiiri', 'siipi', 'tiili', 'viini',
                 'sieni', 'helmi', 'kilpi', 'hiili', 'kieli', 'silti')
LINKERS = ('n', 's', 'en', 'in', 'un', 'an', 'än', 'on', 'ön', 'yn')


def compound_harmony(lemma, lemmaset):
    """Palauttaa 'ä', jos sana on yhdyssana, jonka loppuosassa on vain e/i."""
    for head in NEUTRAL_HEADS:
        if not lemma.endswith(head) or len(lemma) <= len(head) + 2:
            continue
        pre = lemma[:-len(head)]
        if pre in lemmaset:
            return 'ä'
        for link in LINKERS:
            if pre.endswith(link) and pre[:-len(link)] in lemmaset:
                return 'ä'
    return None


CLEAN = re.compile(r'^[a-zåäöéšž]+$')
SKIP_WCLASS = {'abbreviation', 'prefix'}
BASE_ONLY = {'adverb', 'interjection', 'conjunction'}
PROPER = {'pnoun_lastname', 'pnoun_firstname', 'pnoun_place', 'pnoun_misc'}


def split_class(name):
    if '-av' in name:
        base, av = name.split('-av')
        return base, av
    return name, None


def forms_for(lemma, cls, is_verb):
    base, av = split_class(cls)
    if lemma in IRREGULAR_NOM:
        return [lemma] + IRREGULAR_NOM[lemma].split()
    if lemma in IRREGULAR_VERB:
        return [lemma] + IRREGULAR_VERB[lemma].split()
    table = VERBS if is_verb else NOMINALS
    fn = table.get(base)
    if fn is None:
        return [lemma]
    try:
        res = fn(lemma, av)
    except Exception:
        return [lemma]
    out = []
    for item in (res if isinstance(res, list) else [res]):
        out.extend(verb_forms(item) if isinstance(item, Verb)
                   else nom_forms(item))
    return out


def main():
    entries = json.load(open(os.path.join(ROOT, 'build', 'lemmas.json'),
                             encoding='utf-8'))
    # sana -> lippubitit: 1 = perusmuoto, 2 = ei erisnimi, 4 = yleiskielinen
    words = {}

    def add(w, flags):
        if not CLEAN.match(w) or len(w) < 2 or len(w) > 30:
            return
        words[w] = words.get(w, 0) | flags

    lemmaset = set(EXTRA.split())
    for e in entries:
        lemmaset.add(e['w'].lower())
    harmony_override = {}
    for w in lemmaset:
        h = compound_harmony(w, lemmaset)
        if h:
            harmony_override[w] = h

    unknown = {}
    for e in entries:
        wcs = set(e['c'])
        if wcs & SKIP_WCLASS:
            continue
        lemma = e['w'].lower()
        if not CLEAN.match(lemma):
            continue
        styles = set(e['s'])
        if 'incorrect' in styles:
            continue                       # ei kuulu kirjakieleen
        common = 0 if wcs and wcs <= PROPER else 2
        if not (styles & {'dialect', 'old'}):
            common |= 4
        add(lemma, 1 | common)
        if wcs & BASE_ONLY and not (wcs - BASE_ONLY):
            continue
        is_verb = 'verb' in wcs
        FORCE_HARM[0] = harmony_override.get(lemma)
        for cls in e['i']:
            base, _av = split_class(cls)
            table = VERBS if is_verb else NOMINALS
            if base not in table and lemma not in IRREGULAR_NOM \
                    and lemma not in IRREGULAR_VERB:
                unknown[cls] = unknown.get(cls, 0) + 1
                continue
            for f in forms_for(lemma, cls, is_verb):
                add(f, common)
        FORCE_HARM[0] = None

    for w in EXTRA.split():
        add(w.lower(), 1 | 2)

    if unknown:
        print('tuntemattomat luokat:', sorted(unknown.items(),
                                              key=lambda x: -x[1])[:20],
              file=sys.stderr)

    out = os.path.join(ROOT, 'build', 'wordforms.txt')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        for w in sorted(words):
            f.write('%s\t%d\n' % (w, words[w]))
    print('muotoja:', len(words))


if __name__ == '__main__':
    main()
