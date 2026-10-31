# Spremljanje, Teze in pojasnila · UX SPEC

**Datum:** 2026-10-30, S-025. **Status:** v S-026 izvedena pomoč UXH/BL-224 in razločitev metod BL-228 ([dokazi pomoči](../../implementation/2026-10-31-pomoc-in-hierarhija-podatkov.md), [dopolnitev Escape](../../implementation/2026-10-31-pomoc-escape-popravek.md), [metode](../../implementation/2026-10-31-metode-uspesnosti.md)). Osebno spremljanje, lastne ideje, nove Teze in merila še niso implementirani. **Osnova:** `6a9f07c` in uporabnikova nova posnetka portfelja/Pregleda.

[Neodvisni pregled](../../implementation/2026-10-30-neodvisni-pregled-kompaktnega-portfelja-in-plana.md): dokumentarni PASS po odpravi UX-R1/R2. To potrjuje skladnost predloga in preizkusljivost plana, ne izvedbe pomoči, idej ali novih meril.

Uporabnik želi nižje vrstice in graf ob instrumentu, razumljivejše Teze s podatki za presojo, dodajanje spremljanja iz drugih strani in manj stalnih opisov. Potrdil je **tudi lastne ideje brez predhodne analize** ter **več meril glede na ciljno dolžino investicije**. Ni izbral posameznih številčnih pragov ali obveznih metrik; spodnje predloge so izvedbeni predlog, ne njegove naložbene zahteve.

Podlage: [raziskava Tez](../../research/2026-10-30-teze-uporabniski-potek-raziskava.md), [raziskava Uspešnosti](../../research/2026-10-30-uspesnost-in-povezave-raziskava.md), DESIGN, VOICE, ADR-0012/0017/0018/0022/0024. [Izvedbeni plan](../plans/2026-10-30-spremljanje-in-pojasnila-ux.md). :3000 ostane nedotaknjen; :3100 je ločen pregled.

## 1. Preverjeno izhodišče in izbor pristopa

| Tema | Sedaj | Predlagana sprememba |
|---|---|---|
| Portfelj/watchlista | Graf in štiri dodatne vrstice so pod identiteto; prvi vrstici na :3100 217,25 px. | BL-223: horizontalni sklop identiteta/graf, ohranjeno obdobje, cona in opozorila; brez ponastavitve stolpcev. |
| Glave strani | Datum ali SCR koda, opis ter dodatne vrstice metapodatkov. | BL-224: naslov + pogosto dejanje + ena ikona pomoči. Datum v stranski nogi, tehnična oznaka le v `/ux`; dolga navodila v pomoč. |
| Uspešnost | Zaporedno globalni izidi signalov in drugačna študija signalov/končnih analiz; brez osebne zbirke ali ročne ideje. | BL-225: Moje spremljanje / Vsi signali / Testiranje mnenj. Trajni izbor konkretnega mnenja in lastne ideje, jasna različna merilna osnova. |
| Teze | Nastanek iz zaključene analize, besedilne trditve in dokazi. Seznam kaže verzijo in pet števcev, ne naslednje odločitve. | BL-226: jasen nastanek, naslednje dejanje, zadnja dejanska preverba, pending predlogi; zgodovina in urejanje postopno razkrita. |
| Merljiva teza | Ni strukturirane metrike, začetnega/trenutnega opažanja ali pravila. | BL-227: ločena pogodba meril z izvorom/obdobjem/enoto, odvisna od horizonta. Podatkovnih vrzeli ne prikrije oblikovanje. |
| Različni izidi | Stari SignalOutcome in ADR-0022 nimata iste vstopne cene/stroškov; stara neutral smer se računa kot long. | BL-228: reprodukcija, obseg vpliva in verzionirana odločitev; ne prepisovati preteklih izidov ali združiti odstotkov brez oznake metode. |

Obravnavani pristopi: **A** samo kozmetična ureditev je poceni, a ne omogoči lastnih idej ali dokazljive primerjave; **B** ena obsežna prenova z novim splošnim pravilnikom pred odkrivanjem podatkovnih vrzeli je preveč tvegana; **C, priporočeno** skupna pomoč/gostota → trajno spremljanje in ročne ideje → jasne Teze → preverjeni kazalniki. Posamezni rezi dajo uporabno celoto in imajo ločena dokazna vrata. Uporabnik je določil funkcionalni obseg; izbira te postopne arhitekture je predlog izvajalca.

## 2. Pomoč in hierarhija informacij [BL-224]

**UXH-01:** vsaka produktna stran ima ob naslovu eno vizualno majhno ikono `?` z jasno dostopnim imenom »Pomoč za …«. Cilj dotika najmanj 48 × 48 px, vidni fokus in primeren kontrast. Klik/Enter odpre skupni bralni panel; Escape, Zapri ali Nazaj ga zaprejo in vrnejo fokus. Hover ni edina pot. Pomoč ne kliče modela in ne izvaja produktnih dejanj.

**UXH-02:** vsebina pomoči ima največ štiri kratke sklope: Kaj vidim / Kaj lahko naredim / Kako nastanejo podatki / Omejitve in povezave. Slovenska in angleška vsebina sta uredniški zapis v messages, ne generirano besedilo pri vsakem obisku. Pri podrobnostih se vsebina prilagodi vrsti strani, ne osebni vsebini teze.

| Vedno v osnovnem pogledu | Na klik ob konkretnem podatku | V pomoči/tehničnih podrobnostih |
|---|---|---|
| Demo oznaka, govorica, zastarelo/delno/neznana identiteta, konflikt, napaka, omejitev dejanja, veljavni filter/horizont/stroški ob rezultatu | Vir, čas, obdobje, definicija posamezne metrike, točna osnova izračuna | Dolga navodila, razlaga vseh ikon, podroben primer, interni model/UUID/revizija, razvojna SCR oznaka |

**UXH-03:** odstranitev stalnega opisa ni odstranitev pomena podatka. Pozitiven/negativen podatek še vedno ima predznak/barvo, cena valuto, negotovost vidno stanje. Datum danes v nogi navigacije ni datum podatka. Datum posnetka portfelja in datum tržne cene ostaneta ločena in dosegljiva ob podatku. Tehnično `database` ni uporabniška razlaga izvora; »shranjeno«/dejanski vir sodita v ustrezne podrobnosti.

**UXH-04 / Pregled:** odstrani današnji datum iz vrha, daljši uvod in podvojene definicije preseli v pomoč. Če ni na voljo noben makro kazalnik, prikaži kompakten razdelek »Tržni kontekst: ni preverjenih podatkov« z razkritjem štirih kazalnikov, ne štirih praznih visokih kartic. Če je del podatkov na voljo, pokaži vrednosti in vidne vrzeli; izpad API ni isto kot manjkajoč vir. Ne izračunaj režima iz nepopolnih kazalnikov.

**UXH-05 / pregled vseh poti:**

| Pot | Jedro ostane vidno | Pomoč / umik dodatnih opisov |
|---|---|---|
| `/` | Stanje portfelja, signali z močjo, cona, bistvena opozorila | Legenda zemljevida/Radarja/lijaka, metoda, razpon/vir |
| `/radar`, `/entries`, `/signals` | Filtri, stanje, smer, dokazna opozorila in glavna dejanja | Kaj pomenijo ocena, cona, sprejem/spremljanje, govorica |
| `/proposals` | Vnos, status in rešitev negotove oddaje | Pot predloga do rezultata, razlika presoja hipoteze/cenovni izid |
| `/analysis`, `/analysis/[id]` | Status, izvorno mnenje, datum in bistvena dokazila | Metoda, faze agentov, poraba/tehnični podatki |
| `/portfolio` in štirje zavihki | Podatki izbranega računa, standardni profil, barve/vrzeli, obdobje | Razlaga profilov, dividendna ocena/knjižba, avtomatika |
| `/i/[symbol]` | Identiteta, cena/graf, podatkovna kakovost in pomembne povezave | Definicije kazalnikov, vir, povezave v spremljanje |
| `/theses`, `/theses/[id]` | Glavna trditev, veljavno stanje, naslednja odločitev in svežina dokazov | Nastanek/različice, pomen pregledov in zgodovina |
| `/track-record` | Jasno izbrani pogled, cilj merjenja, veljavni parametri, preskoki | Metoda, razlika donos mnenja/portfelja, pristranskost |
| `/settings` | Spremenjene/shranjene nastavitve, enabled in posledice procesa | Pomoč polj/procesov, okna/kvote/SMTP; ohrani obstoječe pojasnjevanje |
| `/options` | Vidna omejitev, da je modul odložen | Kratko pojasnilo prihodnjega obsega, noben navidez delujoč posel |
| `/ux` | Razvojni vzorci/tokens/SCR oznake | Ostane razvojna stran; ni privzeto uporabniško navodilo |

Datum v nogi je lokalni datum uporabnika z Intl in varnim prehodom čez polnoč/DST, brez strežniške hidratacijske razlike. Na telefonu je isti podatek v dosegljivi navigacijski pomoči/Več; ne dodaj fiksne vrstice čez pomembna dejanja.

## 3. Osebno spremljanje in lastne ideje [BL-225]

**UXP-01 / tri razločne vsebine:** `/track-record?view=mine|signals|study`. Mine vsebuje trajno osebno zbirko in dejanje »Nova ideja«. Signals ohrani globalne izide in kalibracijo. Study vsebuje izrecno ponovljiv izračun. Stare URL povezave s horizon/kind/source še odprejo prvotni globalni pogled; brez parametrov je predlagan Mine s pojasnjenim praznim stanjem. Noben pogled ne prikrije drugačne metode drugega.

**UXP-02 / dejanja na izvornih straneh:** skupni gumb »Dodaj v spremljanje« / »V spremljanju«, z razveljavitvijo arhiviranja in povezavo v zbirko. Signal se shrani s konkretnim Signal.id; zaključena analiza s konkretnim run.id. Izbor zadnje analize ni trajni kazalec na naslednjo analizo iste delnice. Predlog/Radar/Vstop/Instrument ponudijo obstoječ povezani zapis z vidnim tipom/časom; brez njega ne ustvarijo navideznega signala ali analize. Presoja hipoteze ni samodejno smer cene.

**UXP-03 / ločena domena:** članstvo ni Signal.status=watching/accepted in ni Watchlist instrumenta. Zapis vsebuje nespremenljivi tip+UUID (`signal|analysis|idea_revision`), prvotno razpoložljivost in ločen čas dodajanja, posnetek prvotnega mnenja/smeri, revizijsko sled arhiviranja/obnove. FK/check/unique varujejo veljavnost in podvojitev. Osebna zbirka pomeni sedanjo enouporabniško namestitev, ne izmišljen prijavni sistem ali novo deljenje zasebnih podatkov.

**UXP-04 / Nova ideja:** obrazec za nedvoumen instrument, smer (gor/dol/nevtralno/še ne vem), lastno utemeljitev, ciljni horizont in opcijski ciljni datum ter več izbirnih meril. »Shrani osnutek« ne začne merjenja. »Začni spremljanje« pokaže povzetek in aktivira nespremenljivo različico z **dejanskim strežniškim časom aktivacije**; isti trenutek jo atomsko doda v zbirko. Ne ustvarja AnalysisRun ali Signal in ne kliče LLM, brokerja ali obvestil.

**UXP-05 / spremembe:** do aktivacije urejanje z revision CAS; po aktivaciji so prvotna smer/razlog/horizont/čas zamrznjeni. Popravek vsebinskega mnenja ustvari novo označeno različico, stara ostane sledljiva; opomba je ločen dodatek. Reload, dvojni klik in izgubljeni odgovor ne ustvarijo nove ideje/aktivacije: trajni request_id in točno telo pred POST, GET istega ID za obnovo, konflikt druge vsebine 409. Uporabi principe ADR-0024, ne napačnega novega UUID na vsak klik.

**UXP-06 / čas in izid:** pri obstoječih mnenjih ostane Signal.created_at / AnalysisRun.finished_at, pri lastni ideji čas njene aktivacije. Retrospektivni datum se ne sme predstavljati kot dejanska napoved iz preteklosti. Morebitna zgodovinska simulacija mora biti ločena, označena in izključena iz statistike dejanskih idej. Cenovna metoda ostane ADR-0022: prvi shranjeni zaključek strogo po UTC dnevu razpoložljivosti, horizont shranjenih trgovalnih sej, stroški na obeh straneh, preskoki za neutral/unknown, manjkajoče/neveljavne cene in premalo prihodnjih sej. Dodano danes in mnenje pred mesecem sta vidno različna časa. Izid od dodajanja je morebitna poznejša druga metoda, ne prikrita zamenjava.

**UXP-07 / horizont:** ciljni čas investicije je ločen od horizonta cenovnega testa. Današnji test podpira 1/5/20/60 shranjenih sej; ni ustrezna končna sodba o triletni ideji. Mine prikaže ciljni horizont/rok in vmesne izide jasno označi. Daljši horizonti potrebujejo ločeno razširitev bounded metode in zadostno zgodovino, ne izmišljenih 252 sej za vsako koledarsko leto ali novih plačljivih klicev ob shranjevanju.

**UXP-08 / izračun:** filter posameznega zapisa/osebne zbirke mora veljati v SQL pred COUNT, ORDER in LIMIT; ne filtriraj že naloženih 1000 vrstic. Identiteta je tip+ID, ne sam UUID ali ticker. Članstvo se bere paginirano, seznam in seznam preskokov sta vidna. Izračun ostane izrecno dejanje; reload/odpiranje strani ne kliče analitika. Povzetek pokaže dodano/izmerjeno/čaka/preskočeno, ne samo lepih izidov. Članov različnih izvorov ne razglašaj za neodvisne stave; ne enači povprečja izbranih mnenj z donosom portfelja.

Združljivost izvorov je izrecna: obstoječi `/backtest` brez novega selection oziroma z `selection=all` in `source=all` še vedno pomeni **samo signal + končna analiza**, tudi ko so v bazi lastne ideje. `idea_revision` vstopi samo skozi novi `selection=mine|single`; morebitni prihodnji širši vir zahteva novo izrecno verzionirano pogodbo. Dodana ideja ne sme spremeniti starega total/count/povprečja.

**UXP-09 / povezava s Tezami:** predlagani `thesis_break` je lahko ustvarjen še pred uporabnikovim sprejemom predloga. Prikaži »Čaka na tvoj pregled« in povezavo na trditev/predlog; cenovni izid ni dokaz veljavnosti teze. Spremljanje ročne ideje ni samodejna aktivacija uradne teze za isti instrument. Nova ideja se lahko kasneje izrecno poveže s tezo, brez spreminjanja trenutne pogodbe ene teze na instrument.

V Mine nerešeni/nepreverljivi predlogi pregleda ostanejo vidni v ločeni skupini »Zahteva pregled« in štejejo v skupno članstvo, **ne v privzeto povprečje izidov brez nerešenih pregledov**. Uporabnik lahko izrecno izbere vključitev vseh; obseg in ločen imenovalec sta vidna ob rezultatu. Vsak izračun zabeleži stanje predloga ob času izračuna, ne prepiše izvornega mnenja/časa. To pravilo ne spreminja legacy `selection=all` povprečij; ta so označena kot vsi izidi signalov/analiz, z opozorilom, kadar vključujejo še nerešene preglede tez. Signal z izvorom thesis_break sam po sebi ni dokaz uporabnikove potrditve.

## 4. Teze: smiseln potek pred strukturiranimi metrikami [BL-226]

**UXT-01 / seznam:** zavihki/filtri Za odločitev / Aktivne / Osnutki / Arhiv, simbol in stran v URL. Vrstica: instrument, kratek povzetek dejanske aktivne teze, ciljni horizont če ga poznamo, veljavno potrjeno stanje, število nerešenih predlogov, datum zadnje dejanske preverbe ali »še ni preverjeno«, naslednji rok/dejanje. Pet ničelnih statusnih števcev gre v podrobnosti. Vsi podatki so iz iste strani strežniško omejenega read modela; brez N+1 in brez »filtriraj prvo stran potem preštej«.

**UXT-02 / detail:** vrh »Kaj mora držati«, »Kaj se je spremenilo«, »Kaj zahteva mojo odločitev«. Trditev ima jedro, veljaven status in zadnji dokaz. Urejanje, celotna zgodovina in stare različice se odprejo na zahtevo. Ločeno pokaži datum uporabnikove odločitve, zadnji poskus pregleda, izid/input_cutoff pregleda in datum vira. updated_at ni svežina raziskave. collapsed UI ne sme še vedno prenesti neomejene zgodovine.

**UXT-03 / nastanek iz analize:** vidna pot Analiza → Osnutek → Pregled pogojev/horizonta → Shrani → Aktiviraj. Izvirni trigger_kind/tekst ostaneta vidna, zlasti downgrade_if. Ne spremeni »če marža pade« v pozitivno trditev z avtomatskim negiranjem ali izluščenim pravilom. Uporabnik uredi, kaj mora držati in kaj bi to ovrglo. Pred zamenjavo aktivne različice vidi, kaj se nadomešča. Aktivacija ni nov LLM klic ali naročilo.

**UXT-04 / več pogojev in pregled:** uporabnik sam izbere primerno več meril. Danes pregled podpira največ 20 trditev, nastanek pa lahko ustvari več. UI mora pokazati nepodprt obseg in preprečiti lažno obljubo pregleda vseh; načrt spremembe limita potrebuje lasten dokaz, ne tihega reza. Večjega osnutka/aktivacije ne zavrni ali odreži samo zaradi novega videza: vsebina ostane, uporabnik vidi, da samodejni pregled te različice v sedanjem obsegu ni podprt. Lahko izrecno združi/uredi trditve ali jih spremlja ročno. Pregled izbranega podnabora in povečanje limita zahtevata lasten SPEC, ne skritega izbora prvih 20. Obstoječe večje teze ostanejo nespremenjene z vidno vrzeljo pokritosti.

**UXT-05:** agentov predlog in uporabnikovo veljavno stanje sta ločena. Sprejem zahteva veljavno isto aktivno različico/status/dokaz in CAS; stale/rumor/nepreverjeno ne postane potrjeno. »Brez novih dokazov«, »pregled ni uspel«, »pavza«, »negotov izid« in »rok je potekel« niso enako. Osveži samo prebere shranjene podatke; nov pregled je posebej označeno dejanje z obstoječimi dovoljenji/kvotami. Ta UX krog ne obide odprtih A3/A5 varoval živosti.

## 5. Več meril glede na ciljno investicijo [BL-227]

Ločen podatkovni SPEC pred implementacijo. Naslednji nabor je izbor predlog, ne obveznih ali med seboj zamenljivih meril:

| Namen/horizont | Primeri primernih izbir | Dokazna meja |
|---|---|---|
| Dnevi/tedni | Dogodek/rok, vstopna cena/cona, jasno razveljavitveno dejstvo, odziv cene | Cena ima kotacijo/valuto/čas, dogodek konkreten vir; cenovni odziv ne potrdi poslovne zgodbe. |
| Meseci/~1–2 leti | Rast prihodkov, marža, napoved podjetja, katalizator, vrednotenje | Obdobje/TTM/forward in datum napovedi morajo biti primerljivi; ne mešaj odstotka rasti z absolutnim zneskom. |
| Več let | Poslovna teza, denarni tok, zadolženost, kapitalska alokacija, vzdržnost/rast dividende | Znani viri/obdobja, dividenda se razlikuje od dividendne ocene. Odsoten podatek je vrzel, ne stabilnost teze. |

**UXM-01:** vsako merilo ima tip `metric|event|manual_evidence`, opis smisla, izbrani indikator/prag ali zahtevano dokazilo, enoto/valuto/osnovo/obdobje, začetni posnetek ob aktivaciji, zadnje opažanje in datum naslednje preverbe. Baseline je nespremenljiv. Opažanja so append-only s source/as_of/fetched_at/availability, povezana z različico pogoja; kasnejši restatement je nov zapis, ne popravek preteklosti brez sledi.

**UXM-02:** deterministični comparator sme računati samo iz izrecno izbranih pravil in preverjenih decimalnih podatkov z ujemajočo enoto/osnovo. Iz LLM besedila ne sestavljaj pravil ali finančnih številk. Missing/stale/basis_mismatch → »ni mogoče primerjati«, ne 0/false/confirmed. Izpolnjen numerični prag je ločena informacija, ne samodejna vsebinska potrditev ali zlom teze. Uporabnik ohrani odločitev.

**UXM-03:** horizont, ciljni rok in pogostost pregleda so različna polja. Izbira »več let« ne odpre trajnega LLM izvajanja. Predlagana pogostost je uredljiva in spoštuje procesne nastavitve/okna/pavzo/kvote. Stare teze brez horizonta dobijo »ni določeno«, brez izmišljenega backfilla. Ne dodaj datumov/meritev k demo primerom, ki se pretvarjajo za dejansko preteklost.

## 6. Prevzem in izdajne meje

| Vrata | Dokaz |
|---|---|
| F-UX01 | Portfelj/Watchlista: graf desno, običajna prva vrstica ≤130 px pri primerljivem desktop pogledu; vsa opozorila, barve, imena in datumi dosegljivi. |
| F-UX02 | Pomoč na vseh zgornjih poteh: SL/EN, telefon, tipkovnica, Back/Escape/fokus, 200-% povečava, brez izgube URL/filter/draft ali modelnega klica. |
| F-UX03 | Datum danes v nogi, podatkovni datumi ob podatku; DST/polnoč/hidracija. Vsa makro polja missing → kompakten pošten prikaz, delni podatki in API failure ločeni. |
| F-UX04 | Signal/končna analiza dodana iz izvorne strani → isti tip/ID v Mine po reload in drugem zavihku; dvojni klik/izgubljen odgovor ne podvoji; status signala ostane. |
| F-UX05 | Lastna ideja draft → aktivacija → članstvo atomsko in enkrat; čas strežniški, poznejša vsebinska sprememba nova različica, nič AnalysisRun/Signal/LLM/obvestil/naročil. |
| F-UX06 | Več kot 1000 tujih zapisov pred izbranim → isti predmet pravilno izračunan; count in SQL filter pred LIMIT, tip+ID kolizija varna. Lastne ideje ne spremenijo legacy source=all total/povprečij. |
| F-UX07 | Neutral/unknown, manjkajoče cene in premalo sej ostanejo vidni preskoki; izbrani pozitivni primeri se ne predstavljajo kot globalna uspešnost ali donos portfelja. |
| F-UX08 | Thesis pending broken z uradnim virom je predlog, veljavno stanje nespremenjeno; stale review in govorica ne postaneta potrjena. Mine ga pokaže ločeno, privzeti imenovalec ga ne vključi; izrecna vključitev vseh pokaže obseg/stanje ob izračunu, legacy statistika nespremenjena. |
| F-UX09 | Nastanek teze pokaže izvirni downgrade_if brez negiranja; >20 ohrani osnutek/aktivacijo in pojasni nepodprt avtomatski pregled, noben tih rez, nov limit aktivacije ali lažna obljuba. |
| F-UX10 | »Zadnja preverba« je dejanski review/input_cutoff, ne updated_at. Paginirana zgodovina in agregati brez N+1; filtri/stran se obnovijo iz URL. |
| F-UX11 | Tri različne dolžine investicije → različni izbirni sklopi; nobena ne zahteva vseh meril. Baseline ostane, nova opažanja/restatement imajo sled. |
| F-UX12 | Neujemajoča enota/obdobje/forward/TTM, missing/stale in zamenjana valuta ne sprožijo potrditve; 60 sej ni končna sodba o večletnem cilju. |
| F-UX13 | Reprodukcija stare neutral/long razlike in različne začetne sveče; ohranitev zgodovinskih rezultatov do eksplicitne verzionirane migracije. |

Novih product shem ne uvajaj brez migracije po takratnem head in generiranega OpenAPI/TS. Oblikovanje ostane v obstoječih tokenih, besedila v messages. Vsi testi podatkov/modelov so sintetični/fake, deploy :3000 ostaja ločeno dovoljenje z dejanskim backup/restore dokazom. BL-222 in podatkovne vrzeli Flex/FX niso preklicani; novi uporabniški UX krog jih le začasno prehiti v prednosti. Odprto A3/A5 ni odpravljeno s prenovo Tez.
