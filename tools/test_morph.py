# -*- coding: utf-8 -*-
"""Tarkistaa, että taivutin tuottaa tunnetut muodot oikein."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate import forms_for

# (sana, luokka, verbi?, odotetut muodot pilkulla eroteltuina)
CASES = [
    ('hattu', 'valo-av1', 0, 'hattu hatun hattua hattuna hattuun hatut hattujen hattuja hatuissa hattuihin hatulle hatutta'),
    ('valo', 'valo', 0, 'valo valon valoa valona valoon valot valojen valoja valoissa valoihin'),
    ('aurinko', 'valo-av1', 0, 'aurinko auringon aurinkoa aurinkona aurinkoon auringot aurinkojen aurinkoja auringoissa'),
    ('kyky', 'valo-av1', 0, 'kyky kyvyn kykyä kykynä kykyyn kyvyt kykyjä kyvyissä'),
    ('alku', 'valo-av5', 0, 'alku alun alkua alkuna alkuun alut alkuja aluissa alkuihin'),
    ('kala', 'kala', 0, 'kala kalan kalaa kalana kalaan kalat kalojen kaloja kaloissa kaloihin kaloina'),
    ('jalka', 'kala-av5', 0, 'jalka jalan jalkaa jalkana jalkaan jalat jalkojen jalkoja jaloissa jalkoihin jalkoina'),
    ('aika', 'kala-av3', 0, 'aika ajan aikaa aikana aikaan ajat aikojen aikoja ajoissa aikoihin'),
    ('koira', 'koira', 0, 'koira koiran koiraa koirana koiraan koirat koirien koiria koirissa koiriin'),
    ('härkä', 'koira-av5', 0, 'härkä härän härkää härkänä härkään härät härkien härkiä härissä härkiin'),
    ('risti', 'risti', 0, 'risti ristin ristiä ristinä ristiin ristit ristien ristejä risteissä risteihin'),
    ('arkki', 'risti-av1', 0, 'arkki arkin arkkia arkkina arkkiin arkit arkkien arkkeja arkeissa'),
    ('paperi', 'paperi', 0, 'paperi paperin paperia paperina paperiin paperit paperien papereiden papereita papereissa papereihin'),
    ('kalsium', 'kalsium', 0, 'kalsium kalsiumin kalsiumia kalsiumina kalsiumiin kalsiumit'),
    ('joki', 'lovi-av5', 0, 'joki joen jokea jokena jokeen joet jokien jokia joissa jokiin'),
    ('kivi', 'lovi', 0, 'kivi kiven kiveä kivenä kiveen kivet kivien kiviä kivissä kiviin'),
    ('arki', 'lovi-av3', 0, 'arki arjen arkea arkena arkeen arjet arkien arkia arjissa'),
    ('huuli', 'huuli', 0, 'huuli huulen huulta huulena huuleen huulet huulien huulten huulia huulissa huuliin'),
    ('kieli', 'huuli', 0, 'kieli kielen kieltä kielenä kieleen kielet kielien kielten kieliä kielissä'),
    ('lumi', 'lumi', 0, 'lumi lumen lunta lumena lumeen lumet lumia lumissa'),
    ('meri', 'meri', 0, 'meri meren merta merenä mereen meret meriä merissä meriin'),
    ('niemi', 'niemi', 0, 'niemi niemen nientä niemeä niemenä niemeen niemet niemiä niemissä'),
    ('pieni', 'pieni', 0, 'pieni pienen pientä pienenä pieneen pienet pienten pieniä pienissä'),
    ('käsi', 'susi', 0, 'käsi käden kättä kätenä käteen kädet käsien käsiä käsissä käsiin'),
    ('kansi', 'kansi', 0, 'kansi kannen kantta kantena kanteen kannet kansien kansia kansissa'),
    ('veitsi', 'veitsi', 0, 'veitsi veitsen veistä veitsenä veitseen veitset veitsiä'),
    ('sisar', 'sisar', 0, 'sisar sisaren sisarta sisarena sisareen sisaret sisarien sisarten sisaria sisarissa'),
    ('ahven', 'sisar', 0, 'ahven ahvenen ahventa ahvenena ahveneen ahvenet ahvenia'),
    ('aallotar', 'sisar-av2', 0, 'aallotar aallottaren aallotarta aallottarena aallottareen aallottaret aallottaria'),
    ('kannel', 'askel-av2', 0, 'kannel kanteleen kannelta kanteleena kanteleeseen kanteleet kanteleita'),
    ('askel', 'askel', 0, 'askel askelen askeleen askelta askelena askeleet askelia askeleita'),
    ('uistin', 'uistin', 0, 'uistin uistimen uistinta uistimena uistimeen uistimet uistimien uistinten uistimia'),
    ('ahdin', 'uistin-av2', 0, 'ahdin ahtimen ahdinta ahtimena ahtimeen ahtimet ahtimia'),
    ('laidun', 'laidun-av2', 0, 'laidun laitumen laidunta laitumena laitumeen laitumet laitumia'),
    ('mahdoton', 'onneton-av2', 0, 'mahdoton mahdottoman mahdotonta mahdottomana mahdottomaan mahdottomat mahdottomia'),
    ('sisin', 'sisin', 0, 'sisin sisimmän sisintä sisimpänä sisimpään sisimmät sisimpiä'),
    ('vasen', 'vasen', 0, 'vasen vasemman vasenta vasempana vasempaan vasemmat vasempia'),
    ('nainen', 'nainen', 0, 'nainen naisen naista naisena naiseen naiset naisten naisien naisia naisissa naisiin'),
    ('vastaus', 'vastaus', 0, 'vastaus vastauksen vastausta vastauksena vastaukseen vastaukset vastausten vastauksia'),
    ('kalleus', 'kalleus', 0, 'kalleus kalleuden kalleutta kalleutena kalleuteen kalleudet kalleuksia kalleuksien'),
    ('vieras', 'vieras', 0, 'vieras vieraan vierasta vieraana vieraaseen vieraat vieraiden vieraita vierailla'),
    ('hammas', 'vieras-av2', 0, 'hammas hampaan hammasta hampaana hampaaseen hampaat hampaiden hampaita hampaissa'),
    ('kaunis', 'kaunis', 0, 'kaunis kauniin kaunista kauniina kauniiseen kauniit kauniita kauniiden'),
    ('aistikas', 'iäkäs-av2', 0, 'aistikas aistikkaan aistikasta aistikkaana aistikkaaseen aistikkaat aistikkaita'),
    ('ies', 'vieras-av6', 0, 'ies ikeen iestä ikeenä ikeeseen ikeet ikeitä'),
    ('kiuas', 'vieras-av6', 0, 'kiuas kiukaan kiuasta kiukaana kiukaaseen kiukaat kiukaita'),
    ('mies', 'mies', 0, 'mies miehen miestä miehenä mieheen miehet miesten miehiä miehissä'),
    ('ohut', 'ohut', 0, 'ohut ohuen ohutta ohuena ohueen ohuet ohuita ohuiden'),
    ('kuollut', 'kuollut', 0, 'kuollut kuolleen kuollutta kuolleena kuolleeseen kuolleet kuolleita'),
    ('hame', 'hame', 0, 'hame hameen hametta hameena hameeseen hameet hameiden hameita hameissa'),
    ('aarre', 'hame-av2', 0, 'aarre aarteen aarretta aarteena aarteeseen aarteet aarteiden aarteita'),
    ('hylje', 'hame-av4', 0, 'hylje hylkeen hyljettä hylkeenä hylkeeseen hylkeet hylkeitä'),
    ('koe', 'hame-av6', 0, 'koe kokeen koetta kokeena kokeeseen kokeet kokeita'),
    ('vapaa', 'vapaa', 0, 'vapaa vapaan vapaata vapaana vapaaseen vapaat vapaiden vapaita vapaissa'),
    ('maa', 'pii', 0, 'maa maan maata maana maahan maat maiden maita maissa maihin'),
    ('suo', 'suo', 0, 'suo suon suota suona suohon suot soiden soita soissa soihin'),
    ('tie', 'tie', 0, 'tie tien tietä tienä tiehen tiet teiden teitä teissä teihin'),
    ('korkea', 'korkea', 0, 'korkea korkean korkeaa korkeata korkeana korkeaan korkeat korkeiden korkeita'),
    ('nuorempi', 'suurempi-av1', 0, 'nuorempi nuoremman nuorempaa nuorempana nuorempaan nuoremmat nuorempien nuorempia'),
    ('laatikko', 'karahka-av1', 0, 'laatikko laatikon laatikkoa laatikkona laatikkoon laatikot laatikoiden laatikoita laatikoissa'),
    ('kulkija', 'kulkija', 0, 'kulkija kulkijan kulkijaa kulkijana kulkijaan kulkijat kulkijoiden kulkijoita kulkijoissa'),
    ('asema', 'asema', 0, 'asema aseman asemaa asemana asemaan asemat asemien asemia asemissa'),
    ('nalle', 'nalle', 0, 'nalle nallen nallea nallena nalleen nallet nallejen nalleja'),
    ('autio', 'autio', 0, 'autio aution autiota autiona autioon autiot autioiden autioita'),
    # --- verbit ---
    ('antaa', 'kaivaa-av1', 1, 'antaa annan annat antaa annamme annatte antavat anna antoi annoin antaisi antaisin antanut antaneet annetaan annettiin annettu antakaa antakoon antava antaminen antaessa antaen antamaan antamassa'),
    ('sanoa', 'punoa', 1, 'sanoa sanon sanot sanoo sanomme sanotte sanovat sanoi sanoin sanoisi sanonut sanotaan sanottiin sanottu sanokaa sanova sanominen'),
    ('kirjoittaa', 'kirjoittaa-av1', 1, 'kirjoittaa kirjoitan kirjoittaa kirjoitamme kirjoittavat kirjoitti kirjoitin kirjoittaisi kirjoittanut kirjoitetaan kirjoitettiin kirjoitettu kirjoittakaa'),
    ('hujahtaa', 'hujahtaa-av1', 1, 'hujahtaa hujahdan hujahtaa hujahtavat hujahti hujahdin hujahtaisi hujahtanut hujahdetaan hujahdettu'),
    ('huutaa', 'huutaa-av1', 1, 'huutaa huudan huutaa huutavat huusi huusin huutaisi huutanut huudetaan huudettiin huudettu huutakaa'),
    ('kaivaa', 'kaivaa', 1, 'kaivaa kaivan kaivaa kaivavat kaivoi kaivoin kaivaisi kaivanut kaivetaan kaivettiin kaivettu'),
    ('laskea', 'laskea', 1, 'laskea lasken laskee laskevat laski laskin laskisi laskenut lasketaan laskettiin laskettu laskiessa'),
    ('tuntea', 'tuntea-av1', 1, 'tuntea tunnen tuntee tuntevat tunsi tunsin tuntisi tuntenut tunnetaan tunnettiin tunnettu'),
    ('sallia', 'sallia', 1, 'sallia sallin sallii sallivat salli sallin sallisi sallinut sallitaan sallittiin sallittu'),
    ('tulla', 'katsella', 1, 'tulla tulen tulee tulevat tuli tulin tulisi tullut tulleet tullaan tultiin tultu tulkaa tulkoon tuleva tuleminen tullessa'),
    ('ajatella', 'katsella-av2', 1, 'ajatella ajattelen ajattelee ajattelevat ajatteli ajattelin ajattelisi ajatellut ajatellaan ajateltiin ajateltu ajatelkaa'),
    ('mennä', 'mennä', 1, 'mennä menen menee menevät meni menin menisi mennyt mennään mentiin menty menkää'),
    ('saada', 'saada', 1, 'saada saan saat saa saamme saatte saavat sai sain saisi saanut saadaan saatiin saatu saakaa'),
    ('juoda', 'juoda', 1, 'juoda juon juo juovat joi join joisi juonut juodaan juotiin juotu juokaa'),
    ('viedä', 'juoda', 1, 'viedä vien vie vievät vei veit veisi vienyt viedään vietiin viety'),
    ('käydä', 'käydä', 1, 'käydä käyn käy käyvät kävi kävin kävisi käynyt käydään käytiin käyty'),
    ('nähdä', 'nähdä', 1, 'nähdä näen näet näkee näemme näette näkevät näki näin näkisi nähnyt nähdään nähtiin nähty nähkää näkemään'),
    ('valita', 'valita', 1, 'valita valitsen valitsee valitsevat valitsi valitsin valitsisi valinnut valitaan valittiin valittu valitkaa'),
    ('juosta', 'juosta', 1, 'juosta juoksen juoksee juoksevat juoksi juoksin juoksisi juossut juostaan juostiin juostu juoskaa'),
    ('salata', 'salata', 1, 'salata salaan salaa salaavat salasi salasin salaisi salannut salataan salattiin salattu salatkaa'),
    ('avata', 'salata', 1, 'avata avaan avaa avaavat avasi avasin avaisi avannut avataan avattiin avattu'),
    ('evätä', 'salata-av2', 1, 'evätä epään epää epäävät epäsi epäsin epäisi evännyt evätään evättiin evätty'),
    ('katketa', 'katketa', 1, 'katketa katkean katkeaa katkeavat katkesi katkesin katkeaisi katkennut katketaan katkettiin katkettu'),
    ('haluta', 'haluta', 1, 'haluta haluan haluaa haluavat halusi halusin haluaisi halunnut halutaan haluttiin haluttu'),
    ('aleta', 'aleta', 1, 'aleta alenen alenee alenevat aleni alenin alenisi alennut aletaan alettiin alettu'),
    ('arvioida', 'voida-av2', 1, 'arvioida arvioin arvioi arvioivat arvioisi arvioinut arvioidaan arvioitiin arvioitu arvioikaa'),
    ('aktivoida', 'kanavoida-av2', 1, 'aktivoida aktivoin aktivoi aktivoivat aktivoisi aktivoinut aktivoidaan aktivoitiin aktivoitu'),
    ('nuolaista', 'nuolaista', 1, 'nuolaista nuolaisen nuolaisee nuolaisevat nuolaisi nuolaisin nuolaisisi nuolaissut nuolaistaan nuolaistiin nuolaistu'),
    ('kihistä', 'kihistä', 1, 'kihistä kihisen kihisee kihisevät kihisi kihisin kihisisi kihissyt kihistään kihistiin kihisty'),
    ('vavista', 'nuolaista-av2', 1, 'vavista vapisen vapisee vapisevat vapisi vapisin vapisisi vavissut vavistaan vavistiin'),
    ('purra', 'purra', 1, 'purra puren puree purevat puri purin purisi purrut purraan purtiin purtu'),
    ('hämmentää', 'pahentaa-av1', 1, 'hämmentää hämmennän hämmentää hämmentävät hämmensi hämmensin hämmentäisi hämmentänyt hämmennetään hämmennettiin hämmennetty'),
    ('kiertää', 'murtaa-av1', 1, 'kiertää kierrän kiertää kiertävät kiersi kiersin kiertäisi kiertänyt kierretään kierrettiin kierretty'),
    ('lentää', 'juontaa-av1', 1, 'lentää lennän lentää lentävät lensi lensin lentäisi lentänyt lennetään lennettiin lennetty'),
    ('lukea', 'laskea-av5', 1, 'lukea luen lukee lukevat luki luin lukisi lukenut luetaan luettiin luettu lukekaa'),
    ('poika', 'poika-av3', 0, 'poika pojan poikaa poikana poikaan pojat poikien poikia pojissa poikiin'),
    ('olla', 'poikkeava', 1, 'olla olen olet on olemme olette ovat oli olin ollut olleet ollaan oltiin oltu olkaa'),
]


def main():
    bad = 0
    for lemma, cls, isv, expect in CASES:
        got = set(forms_for(lemma, cls, bool(isv)))
        missing = [w for w in expect.split() if w not in got]
        if missing:
            bad += 1
            print('%-14s %-18s PUUTTUU: %s' % (lemma, cls, ' '.join(missing)))
    print('---')
    print('%d/%d luokkaa kunnossa' % (len(CASES) - bad, len(CASES)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
