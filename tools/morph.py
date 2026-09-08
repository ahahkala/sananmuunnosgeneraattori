# -*- coding: utf-8 -*-
"""
Suomen kielen taivutusgeneraattori.

Tuottaa Joukahainen/Voikko -taivutusluokkien pohjalta sanojen taivutusmuodot.
Luokkanimet ovat suomi-malagan mukaisia (esim. "risti-av1"); nimen alkuosa on
Kotus-tyypin esimerkkisana ja "-avN" kertoo astevaihtelun.
"""

VOW = set('aeiouyäöå')
FRONTV = set('äöy')
BACKV = set('aou')

# av1/av3/av5: hakumuoto vahvassa asteessa -> heikko aste johdetaan
# av2/av4/av6: hakumuoto heikossa asteessa -> vahva aste johdetaan
STRONG_CITATION = {'1', '3', '5'}

# (klusteri -> vastine); pisin osuma voittaa
GRAD_TABLE = {
    '1': [('kk', 'k'), ('pp', 'p'), ('tt', 't'), ('nk', 'ng'), ('mp', 'mm'),
          ('lt', 'll'), ('nt', 'nn'), ('rt', 'rr'), ('ht', 'hd'),
          ('t', 'd'), ('p', 'v'), ('k', 'v')],
    '2': [('ng', 'nk'), ('mm', 'mp'), ('ll', 'lt'), ('nn', 'nt'), ('rr', 'rt'),
          ('hd', 'ht'), ('d', 't'), ('v', 'p'), ('kk', 'kk'), ('pp', 'pp'),
          ('tt', 'tt'), ('k', 'kk'), ('p', 'pp'), ('t', 'tt')],
    '3': [('k', 'j')],
    '4': [('j', 'k')],
    '5': [('k', '')],
    '6': [('', 'k')],
}


def _split_site(s):
    """(alku, konsonanttiklusteri, loppu); klusteri on viimeisen vokaalin edessä."""
    i = len(s) - 1
    while i >= 0 and s[i] not in VOW:
        i -= 1
    if i < 0:
        return None
    j = i
    while j > 0 and s[j - 1] not in VOW:
        j -= 1
    return s[:j], s[j:i], s[i:]


def _split_site_prev(s):
    """Sama edellisen tavun kohdalta (varajako, esim. 'rangai')."""
    i = len(s) - 1
    while i >= 0 and s[i] not in VOW:
        i -= 1
    if i < 0:
        return None
    i -= 1
    while i >= 0 and s[i] not in VOW:
        i -= 1
    if i < 0:
        return None
    j = i
    while j > 0 and s[j - 1] not in VOW:
        j -= 1
    return s[:j], s[j:i], s[i:]


def grad(s, av):
    """Vaihda s:n aste. av on '1'..'6' tai None."""
    if not av:
        return s
    table = GRAD_TABLE[av]
    for splitter in (_split_site, _split_site_prev):
        parts = splitter(s)
        if parts is None:
            continue
        head, clus, tail = parts
        if av == '6':
            return head + clus + 'k' + tail
        for a, b in table:
            if clus.endswith(a) and a:
                if (av == '3' and len(head) >= 2 and head[-1] == 'i'
                        and head[-2] in VOW):
                    head = head[:-1]
                return head + clus[:-len(a)] + b + tail
    return s


# Yhdyssanan sointu määräytyy viimeisestä osasta, jota pelkkä sananloppuinen
# haku ei tunnista (esim. "sanomalehti" -> "sanomalehteä"). generate.py asettaa
# tämän, kun se on tunnistanut yhdyssanan loppuosan.
FORCE_HARM = [None]


def harm(word):
    """Vokaalisointu: 'a' (takavokaalinen) tai 'ä' (etuvokaalinen)."""
    if FORCE_HARM[0]:
        return FORCE_HARM[0]
    for ch in reversed(word):
        if ch in BACKV:
            return 'a'
        if ch in FRONTV:
            return 'ä'
    return 'ä'


def AA(stem, s):
    """Korvaa A->a/ä, O->o/ö, U->u/y sointuvasti."""
    if harm(stem) == 'a':
        return s.replace('A', 'a').replace('O', 'o').replace('U', 'u')
    return s.replace('A', 'ä').replace('O', 'ö').replace('U', 'y')


def lastv(s):
    for ch in reversed(s):
        if ch in VOW:
            return ch
    return ''


def is_long_end(s):
    return len(s) >= 2 and s[-1] in VOW and s[-2] in VOW


def i_stem(s):
    """Vartalo ennen i-ainesta (imperfekti, konditionaali, monikko)."""
    if len(s) >= 2 and s[-1] == 'i' and s[-2] in VOW:
        return s[:-1]
    if is_long_end(s):
        return s[:-2] + s[-1]
    if s and s[-1] in 'ei':
        return s[:-1]
    return s


def grades(lemma, av):
    """(vahva, heikko) hakumuodosta."""
    if not av:
        return lemma, lemma
    other = grad(lemma, av)
    if av in STRONG_CITATION:
        return lemma, other
    return other, lemma


def _v(s, e):
    return s + AA(s, e)


# ================================================================== NOMINIT
class Nom:
    __slots__ = ('nom', 'wvs', 'svs', 'ess', 'par', 'ill', 'plw', 'pls',
                 'parpl', 'genpl', 'illpl', 'nompl')

    def __init__(self, nom, wvs=None, svs=None, ess=None, par=None, ill=None,
                 plw=None, pls=None, parpl=None, genpl=None, illpl=None,
                 nompl=None):
        self.nom = nom
        self.wvs = wvs
        self.svs = svs if svs is not None else wvs
        self.ess = ess if ess is not None else self.svs
        self.par = par or []
        self.ill = ill or []
        self.plw = plw
        self.pls = pls if pls is not None else plw
        self.parpl = parpl or []
        self.genpl = genpl or []
        self.illpl = illpl or []
        self.nompl = nompl


SG_ENDINGS = ['n', 'ssA', 'stA', 'llA', 'ltA', 'lle', 'ksi', 'ttA']
PL_ENDINGS = ['ssA', 'stA', 'llA', 'ltA', 'lle', 'ksi', 'ttA']


def nom_forms(n):
    out = [n.nom]
    if n.wvs:
        for e in SG_ENDINGS:
            out.append(_v(n.wvs, e))
    if n.nompl is not None:
        out.extend(n.nompl)
    elif n.wvs:
        out.append(n.wvs + 't')
    if n.ess:
        out.append(_v(n.ess, 'nA'))
    out.extend(n.par)
    out.extend(n.ill)
    if n.plw:
        for e in PL_ENDINGS:
            out.append(_v(n.plw, e))
    if n.pls:
        out.append(_v(n.pls, 'nA'))
    out.extend(n.parpl)
    out.extend(n.genpl)
    out.extend(n.illpl)
    return [x for x in out if x]


def n_valo(l, av, extra_ita=False):
    S, W = grades(l, av)
    n = Nom(l, wvs=W, svs=S, par=[_v(S, 'A')], ill=[S + lastv(S) + 'n'],
            plw=W + 'i', pls=S + 'i',
            parpl=[_v(S, 'jA')], genpl=[_v(S, 'jen')], illpl=[S + 'ihin'])
    if extra_ita:
        n.parpl.append(_v(S, 'itA'))
        n.genpl.append(S + 'iden')
    return n


def n_autio(l, av):
    S, W = grades(l, av)
    return Nom(l, wvs=W, svs=S, par=[_v(S, 'tA')], ill=[S + lastv(S) + 'n'],
               plw=W + 'i', pls=S + 'i',
               parpl=[_v(S, 'itA')], genpl=[S + 'iden'], illpl=[S + 'ihin'])


def n_karahka(l, av):
    S, W = grades(l, av)
    ow = W[:-1] + AA(W, 'O')
    os_ = S[:-1] + AA(S, 'O')
    return Nom(l, wvs=W, svs=S, par=[_v(S, 'A')], ill=[S + lastv(S) + 'n'],
               plw=ow + 'i', pls=ow + 'i',
               parpl=[_v(ow + 'i', 'tA'), _v(os_, 'jA')],
               genpl=[ow + 'iden', _v(os_, 'jen')], illpl=[ow + 'ihin'])


def n_risti(l, av, paperi=False, cons=False):
    base = l + 'i' if cons else l
    S, W = grades(base, av)
    eS, eW = S[:-1] + 'e', W[:-1] + 'e'
    n = Nom(l, wvs=W, svs=S, par=[_v(S, 'A')], ill=[S + 'in'],
            plw=eW + 'i', pls=eS + 'i',
            genpl=[S[:-1] + 'ien'], illpl=[eS + 'ihin'])
    if paperi:
        n.parpl = [_v(eW + 'i', 'tA'), _v(eS, 'jA')]
        n.genpl.insert(0, eW + 'iden')
    else:
        n.parpl = [_v(eS, 'jA')]
    return n


def n_nalle(l, av):
    S, W = grades(l, av)
    return Nom(l, wvs=W, svs=S, par=[_v(S, 'A')], ill=[S + 'en'],
               plw=W + 'i', pls=S + 'i',
               parpl=[_v(S, 'jA')], genpl=[_v(S, 'jen'), S + 'in'],
               illpl=[S + 'ihin'])


def n_kala(l, av):
    S, W = grades(l, av)
    ow, os_ = W[:-1] + AA(W, 'O'), S[:-1] + AA(S, 'O')
    return Nom(l, wvs=W, svs=S, par=[_v(S, 'A')], ill=[S + lastv(S) + 'n'],
               plw=ow + 'i', pls=os_ + 'i',
               parpl=[_v(os_, 'jA')], genpl=[_v(os_, 'jen')],
               illpl=[os_ + 'ihin'])


def n_koira(l, av, genpl_ain=False):
    S, W = grades(l, av)
    iw, is_ = W[:-1] + 'i', S[:-1] + 'i'
    n = Nom(l, wvs=W, svs=S, par=[_v(S, 'A')], ill=[S + lastv(S) + 'n'],
            plw=iw, pls=is_,
            parpl=[_v(is_, 'A')], genpl=[is_ + 'en'], illpl=[is_ + 'in'])
    if genpl_ain:
        n.genpl.append(_v(S[:-1], 'in'))
    return n


def n_asema(l, av, o_plural=False):
    S, W = grades(l, av)
    iw, is_ = W[:-1] + 'i', S[:-1] + 'i'
    n = Nom(l, wvs=W, svs=S, par=[_v(S, 'A')], ill=[S + lastv(S) + 'n'],
            plw=iw, pls=is_,
            parpl=[_v(is_, 'A')], genpl=[is_ + 'en'], illpl=[is_ + 'in'])
    if o_plural:
        os_ = S[:-1] + AA(S, 'Oi')
        n.parpl.append(_v(os_, 'tA'))
        n.genpl.append(os_ + 'den')
        n.illpl.append(os_ + 'hin')
    return n


def n_kulkija(l, av, also_ia=False):
    S, W = grades(l, av)
    os_ = S[:-1] + AA(S, 'O')
    n = Nom(l, wvs=W, svs=S, par=[_v(S, 'A')], ill=[S + lastv(S) + 'n'],
            plw=os_ + 'i', pls=os_ + 'i',
            parpl=[_v(os_ + 'i', 'tA')],
            genpl=[os_ + 'iden', _v(S[:-1], 'in')],
            illpl=[os_ + 'ihin'])
    if also_ia:
        n.parpl.append(_v(S[:-1] + 'i', 'A'))
        n.genpl.append(S[:-1] + 'ien')
    return n


def n_korkea(l, av):
    S, W = grades(l, av)
    i = S[:-1] + 'i'
    return Nom(l, wvs=W, svs=S, par=[_v(S, 'A'), _v(S, 'tA')],
               ill=[S + lastv(S) + 'n'], plw=i, pls=i,
               parpl=[_v(i, 'tA')], genpl=[i + 'den'], illpl=[i + 'siin'])


def n_suurempi(l, av):
    S, W = grades(l, av)
    sv, wv = _v(S[:-1], 'A'), _v(W[:-1], 'A')
    return Nom(l, wvs=wv, svs=sv, par=[_v(sv, 'A')], ill=[sv + lastv(sv) + 'n'],
               plw=W[:-1] + 'i', pls=S[:-1] + 'i',
               parpl=[_v(S[:-1] + 'i', 'A')], genpl=[S[:-1] + 'ien'],
               illpl=[S[:-1] + 'iin'])


def n_vapaa(l, av):
    S, W = grades(l, av)
    i = S[:-1] + 'i'
    return Nom(l, wvs=W, svs=S, par=[_v(S, 'tA')], ill=[S + 'seen'],
               plw=i, pls=i, parpl=[_v(i, 'tA')], genpl=[i + 'den'],
               illpl=[i + 'siin'])


def _plural_of_long(S):
    if len(S) >= 2 and S[-1] == S[-2]:
        return S[:-1] + 'i'
    if S[-1] == 'i':
        return S
    return S + 'i'


def n_pii(l, av):
    S, W = grades(l, av)
    i = _plural_of_long(S)
    return Nom(l, wvs=W, svs=S, par=[_v(S, 'tA')],
               ill=[S + 'h' + lastv(S) + 'n'], plw=i, pls=i,
               parpl=[_v(i, 'tA')], genpl=[i + 'den', i + 'tten'],
               illpl=[i + 'hin'])


def n_suo(l, av):
    S, W = grades(l, av)
    i = (S[:-2] + S[-1] + 'i') if len(S) >= 2 else S + 'i'
    return Nom(l, wvs=W, svs=S, par=[_v(S, 'tA')],
               ill=[S + 'h' + lastv(S) + 'n'], plw=i, pls=i,
               parpl=[_v(i, 'tA')], genpl=[i + 'den', i + 'tten'],
               illpl=[i + 'hin'])


def n_lovi(l, av):
    S, W = grades(l, av)
    bS, bW = S[:-1], W[:-1]
    return Nom(l, wvs=bW + 'e', svs=bS + 'e', par=[_v(bS + 'e', 'A')],
               ill=[bS + 'een'], plw=bW + 'i', pls=bS + 'i',
               parpl=[_v(bS + 'i', 'A')], genpl=[bS + 'ien'],
               illpl=[bS + 'iin'])


def n_huuli(l, av, par_cons=None, extra_par=False):
    S, W = grades(l, av)
    bS, bW = S[:-1], W[:-1]
    c = par_cons if par_cons is not None else bS
    par = [_v(c, 'tA')]
    if extra_par:
        par.append(_v(bS + 'e', 'A'))
    return Nom(l, wvs=bW + 'e', svs=bS + 'e', ess=bS + 'e', par=par,
               ill=[bS + 'een'], plw=bW + 'i', pls=bS + 'i',
               parpl=[_v(bS + 'i', 'A')],
               genpl=[bS + 'ien', _v(c, 'ten')], illpl=[bS + 'iin'])


def n_lumi(l, av, back_par=False):
    b = l[:-1]
    cons = (b[:-1] + 'n') if b.endswith('m') else b
    n = n_huuli(l, av, par_cons=cons)
    if back_par:
        n.par = [cons + 'ta']
        n.genpl = [n.genpl[0], cons + 'ten']
    return n


def n_niemi(l, av):
    b = l[:-1]
    cons = (b[:-1] + 'n') if b.endswith('m') else b
    return n_huuli(l, av, par_cons=cons, extra_par=True)


def n_susi(l, av):
    b = l[:-2]
    vs, cs = b + 'de', b + 't'
    return Nom(l, wvs=vs, svs=vs, ess=cs + 'e', par=[_v(cs, 'tA')],
               ill=[cs + 'een'], plw=l[:-1] + 'i', pls=l[:-1] + 'i',
               parpl=[_v(l, 'A')], genpl=[l + 'en'], illpl=[l + 'in'])


def n_kansi(l, av):
    b = l[:-2]
    c = b[-1]
    vs, cs = b + c + 'e', b + 'te'
    return Nom(l, wvs=vs, svs=vs, ess=cs, par=[_v(b + 't', 'tA')],
               ill=[cs + 'en'], plw=l[:-1] + 'i', pls=l[:-1] + 'i',
               parpl=[_v(l, 'A')], genpl=[l + 'en'], illpl=[l + 'in'])


def n_veitsi(l, av):
    b, vs = l[:-3], l[:-1] + 'e'
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(b + 's', 'tA')],
               ill=[vs + 'en'], plw=l[:-1] + 'i', pls=l[:-1] + 'i',
               parpl=[_v(l, 'A')], genpl=[l + 'en'], illpl=[l + 'in'])


def n_sisar(l, av):
    S, W = grades(l, av)
    vs = S + 'e'
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')], ill=[vs + 'en'],
               plw=S + 'i', pls=S + 'i', parpl=[_v(S + 'i', 'A')],
               genpl=[S + 'ien', _v(l, 'ten')], illpl=[S + 'iin'])


def n_askel(l, av):
    S, W = grades(l, av)
    out = [] if av else [n_sisar(l, av)]
    vs = S + 'ee'
    out.append(Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')],
                   ill=[vs + 'seen'], plw=S + 'ei', pls=S + 'ei',
                   parpl=[_v(S + 'ei', 'tA')], genpl=[S + 'eiden'],
                   illpl=[S + 'eisiin']))
    return out


def n_uistin(l, av):
    S, W = grades(l, av)
    b = S[:-1]
    vs = b + 'me'
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')], ill=[vs + 'en'],
               plw=b + 'mi', pls=b + 'mi', parpl=[_v(b + 'mi', 'A')],
               genpl=[b + 'mien', _v(l, 'ten')], illpl=[b + 'miin'])


def n_onneton(l, av):
    S, W = grades(l, av)
    b = S[:-1]
    vs = _v(b, 'mA')
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')],
               ill=[vs + lastv(vs) + 'n'], plw=b + 'mi', pls=b + 'mi',
               parpl=[_v(b + 'mi', 'A')], genpl=[b + 'mien'],
               illpl=[b + 'miin'])


def n_sisin(l, av):
    b = l[:-1]
    wv, sv = _v(b, 'mmA'), _v(b, 'mpA')
    return Nom(l, wvs=wv, svs=sv, ess=sv, par=[_v(l, 'tA')],
               ill=[sv + lastv(sv) + 'n'], plw=b + 'mmi', pls=b + 'mpi',
               parpl=[_v(b + 'mpi', 'A')], genpl=[b + 'mpien'],
               illpl=[b + 'mpiin'])


def n_nainen(l, av):
    b = l[:-3]
    vs = b + 'se'
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(b, 'stA')], ill=[b + 'seen'],
               plw=b + 'si', pls=b + 'si', parpl=[_v(b + 'si', 'A')],
               genpl=[b + 'sien', _v(b, 'sten')], illpl=[b + 'siin'])


def n_vastaus(l, av):
    b = l[:-1]
    vs = b + 'kse'
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')], ill=[vs + 'en'],
               plw=b + 'ksi', pls=b + 'ksi', parpl=[_v(b + 'ksi', 'A')],
               genpl=[b + 'ksien', _v(l, 'ten')], illpl=[b + 'ksiin'])


def n_kalleus(l, av):
    b = l[:-1]
    return Nom(l, wvs=b + 'de', svs=b + 'de', ess=b + 'te',
               par=[_v(b, 'ttA')], ill=[b + 'teen'],
               plw=b + 'ksi', pls=b + 'ksi', parpl=[_v(b + 'ksi', 'A')],
               genpl=[b + 'ksien'], illpl=[b + 'ksiin'])


def n_vieras(l, av):
    S, W = grades(l, av)
    b = S[:-1]
    vs = b + lastv(b)
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')], ill=[vs + 'seen'],
               plw=b + 'i', pls=b + 'i', parpl=[_v(b + 'i', 'tA')],
               genpl=[b + 'iden', _v(l, 'ten')], illpl=[b + 'isiin'])


def n_mies(l, av):
    b = l[:-1]
    vs = b + 'he'
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')], ill=[vs + 'en'],
               plw=b + 'hi', pls=b + 'hi', parpl=[_v(b + 'hi', 'A')],
               genpl=[b + 'hien', _v(l, 'ten')], illpl=[b + 'hiin'])


def n_ohut(l, av):
    b = l[:-1]
    vs = b + 'e'
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')], ill=[vs + 'en'],
               plw=b + 'i', pls=b + 'i', parpl=[_v(b + 'i', 'tA')],
               genpl=[b + 'iden'], illpl=[b + 'isiin'])


def n_kuollut(l, av):
    b = l[:-2]
    vs = b + 'ee'
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'tA')], ill=[vs + 'seen'],
               plw=b + 'ei', pls=b + 'ei', parpl=[_v(b + 'ei', 'tA')],
               genpl=[b + 'eiden'], illpl=[b + 'eisiin'])


def n_hame(l, av):
    S, W = grades(l, av)
    vs = S + lastv(S)
    return Nom(l, wvs=vs, svs=vs, ess=vs, par=[_v(l, 'ttA')], ill=[vs + 'seen'],
               plw=S + 'i', pls=S + 'i', parpl=[_v(S + 'i', 'tA')],
               genpl=[S + 'iden'], illpl=[S + 'isiin', S + 'ihin'])


def n_minimal(l, av):
    """Taipumaton tai poikkeuksellinen: vain perusmuoto."""
    return Nom(l)


def n_foreign(l, av):
    """rosé / spray: liitetään päätteet suoraan."""
    return Nom(l, wvs=l, par=[_v(l, 'tA')], ill=None, plw=None)


# Pienet erikoisryhmät: taivutusmuodot suoraan lueteltuina.
IRREGULAR_NOM = {
    'kevät': 'kevään kevättä keväänä kevääseen keväät keväiden keväitä '
             'keväissä keväisiin keväällä keväällä keväästä kevääseen',
    'veli': 'veljen veljeä veljenä veljeen veljet veljien veljiä veljissä '
            'veljille veljistä veljeksi veljeltä veljelle veljellä veljiin',
    'alkeet': 'alkeiden alkeita alkeissa alkeista alkeisiin alkeilla '
              'alkeilta alkeille alkeiksi',
    'hapan': 'happaman hapanta happamana happamaan happamat happamien '
             'happamia happamissa happamiin happamalla happamalta happamalle '
             'happamasta happamaksi',
    'lämmin': 'lämpimän lämmintä lämpimänä lämpimään lämpimät lämpimien '
              'lämpimiä lämpimissä lämpimiin lämpimällä lämpimältä '
              'lämpimälle lämpimästä lämpimäksi',
}


# =================================================================== VERBIT
class Verb:
    __slots__ = ('inf1', 'strong', 'weak', 'sg3', 'impf', 'cond', 'cons',
                 'pastp', 'pass1', 'pass2', 'passneg', 'inf2s', 'defective')

    def __init__(self, inf1, strong, weak, sg3, impf, cond, cons, pastp,
                 pass1, pass2, passneg, inf2s, defective=False):
        self.inf1 = inf1
        self.strong = strong
        self.weak = weak
        self.sg3 = sg3
        self.impf = impf          # lista (vahva, heikko) -pareja
        self.cond = cond          # konditionaalin vartalo ilman -isi
        self.cons = cons          # imperatiivi-/konsonanttivartalo
        self.pastp = pastp        # (nut-partisiippi, monikko)
        self.pass1 = pass1        # passiivin preesensvartalo (+ -aan)
        self.pass2 = pass2        # passiivin imperfektivartalo (+ -iin)
        self.passneg = passneg
        self.inf2s = inf2s
        self.defective = defective


def verb_forms(v):
    S, W = v.strong, v.weak
    out = [v.inf1, v.sg3, _v(S, 'vAt')]
    for s, w in v.impf:
        out.append(s)
        out.append(_v(s, 'vAt'))
        if not v.defective:
            out += [w + 'n', w + 't', w + 'mme', w + 'tte']
    c = v.cond
    out.append(c + 'isi')
    if not v.defective:
        out += [c + 'isin', c + 'isit', c + 'isimme', c + 'isitte']
    out.append(_v(c, 'isivAt'))
    if v.defective:
        return [x for x in out if x]
    out += [W + 'n', W + 't', W + 'mme', W + 'tte', W]
    out += [_v(v.cons, 'kOOn'), _v(v.cons, 'kAAmme'), _v(v.cons, 'kAA'),
            _v(v.cons, 'kOOt')]
    out += list(v.pastp)
    out += [_v(v.pass1, 'AAn'), v.pass2 + 'iin', _v(v.pass2, 'U'),
            _v(v.pass2, 'AvA'), v.passneg]
    m = _v(S, 'mA')
    out += [m, m + lastv(m) + 'n', _v(m, 'ssA'), _v(m, 'stA'), _v(m, 'llA'),
            _v(m, 'ttA'), m + 'n']
    out += [_v(v.inf2s, 'essA'), v.inf2s + 'en']
    out += [_v(S, 'vA'), S + 'minen']
    return [x for x in out if x]


def _pass_vowel(weak):
    return (weak[:-1] + 'e') if weak and weak[-1] in 'aä' else weak


def _pass_cons(inf):
    st = inf[:-1]
    if st.endswith('d'):
        past = st[:-1] + 't'
    elif st.endswith('st'):
        past = st
    elif len(st) > 1 and st[-1] in 'lnr' and st[-2] == st[-1]:
        past = st[:-1] + 't'
    else:
        past = st + 't'
    return st, past


def v_type1(l, av, impf_fn, extra_impf=None, inf2_e_to_i=False,
            defective=False):
    stem = l[:-1]
    S, W = grades(stem, av)
    sg3 = S if is_long_end(S) else S + lastv(S)
    pairs = [(impf_fn(S), impf_fn(W))]
    if extra_impf:
        x = extra_impf(S)
        pairs.append((x, x))
    e = _pass_vowel(W)
    inf2s = (S[:-1] + 'i') if inf2_e_to_i else stem
    return Verb(l, S, W, sg3, pairs, i_stem(S), S,
                (_v(S, 'nUt'), S + 'neet'), e + 't', e + 'tt',
                _v(e, 'tA'), inf2s, defective)


def v_oida(l, av):
    stem = l[:-2]
    p1, p2 = _pass_cons(l)
    return Verb(l, stem, stem, stem, [(stem, stem)], i_stem(stem), stem,
                (_v(stem, 'nUt'), stem + 'neet'), p1, p2, l, l[:-1])


def v_saada(l, av):
    stem = l[:-2]
    p1, p2 = _pass_cons(l)
    im = i_stem(stem) + 'i'
    return Verb(l, stem, stem, stem, [(im, im)], i_stem(stem), stem,
                (_v(stem, 'nUt'), stem + 'neet'), p1, p2, l, l[:-1])


def v_kaydä(l, av):
    stem = l[:-2]
    b = stem[:-1] + 'v'
    p1, p2 = _pass_cons(l)
    return Verb(l, stem, stem, stem, [(b + 'i', b + 'i')], b, stem,
                (_v(stem, 'nUt'), stem + 'neet'), p1, p2, l, l[:-1])


def v_nuolaista(l, av):
    A = l[:-3]
    S, W = grades(A, av)
    stem = S + 'se'
    p1, p2 = _pass_cons(l)
    cit = A + 's'
    return Verb(l, stem, stem, stem + 'e', [(stem[:-1] + 'i',) * 2],
                stem[:-1], cit,
                (_v(cit, 'sUt'), cit + 'seet'), p1, p2, l, l[:-1])


def v_tulla(l, av):
    A, C = l[:-3], l[-3]
    S, W = grades(A, av)
    stem = S + C + 'e'
    cons = A + C
    p1, p2 = _pass_cons(l)
    return Verb(l, stem, stem, stem + 'e', [(i_stem(stem) + 'i',) * 2],
                i_stem(stem), cons,
                (_v(cons + C, 'Ut'), cons + C + 'eet'), p1, p2, l, l[:-1])


def v_valita(l, av):
    stem = l[:-2] + 'tse'
    p1, p2 = _pass_cons(l)
    return Verb(l, stem, stem, stem + 'e', [(i_stem(stem) + 'i',) * 2],
                i_stem(stem), l[:-1],
                (_v(l[:-2], 'nnUt'), l[:-2] + 'nneet'), p1, p2, l, l[:-1])


def v_juosta(l, av):
    b = l[:-3]
    stem = b + 'kse'
    p1, p2 = _pass_cons(l)
    return Verb(l, stem, stem, stem + 'e', [(b + 'ksi',) * 2], b + 'ks',
                b + 's', (_v(b, 'ssUt'), b + 'sseet'), p1, p2, l, l[:-1])


def v_nähdä(l, av):
    b = l[:-3]           # 'nä' / 'te'
    S, W = b + 'ke', b + 'e'
    p1, p2 = _pass_cons(l)
    return Verb(l, S, W, S + 'e', [(b + 'ki', b + 'i')], b + 'k', b + 'h',
                (_v(b + 'h', 'nUt'), b + 'hneet'), p1, p2, l, l[:-1])


def v_aleta(l, av):
    A = l[:-2]
    S, W = grades(A, av)
    stem = S + 'ne'
    p1, p2 = _pass_cons(l)
    return Verb(l, stem, stem, stem + 'e', [(S + 'ni',) * 2], S + 'n', l[:-1],
                (_v(A, 'nnUt'), A + 'nneet'), p1, p2, l, l[:-1])


def v_salata(l, av):
    A = l[:-2]
    S, W = grades(A, av)
    stem = S + lastv(S)
    p1, p2 = _pass_cons(l)
    return Verb(l, stem, stem, stem, [(S + 'si',) * 2], S, l[:-1],
                (_v(A, 'nnUt'), A + 'nneet'), p1, p2, l, l[:-1])


def v_katketa(l, av):
    A = l[:-2]
    S, W = grades(A, av)
    stem = _v(S, 'A')
    p1, p2 = _pass_cons(l)
    return Verb(l, stem, stem, stem + lastv(stem), [(S + 'si',) * 2], stem,
                l[:-1], (_v(A, 'nnUt'), A + 'nneet'), p1, p2, l, l[:-1])


IRREGULAR_VERB = {
    'olla': 'olen olet on olemme olette ovat oli olin olit olimme olitte '
            'olivat ollut olleet ole olisi olisin olisit olisimme olisitte '
            'olisivat ollaan oltiin oltu oltava olkoon olkaa olkaamme olkoot '
            'oleva oleminen ollessa ollen olemaan olemassa olemasta olemalla '
            'olematta',
    'ei': 'en et ei emme ette eivät älä älköön älkää älkäämme älkööt',
}
