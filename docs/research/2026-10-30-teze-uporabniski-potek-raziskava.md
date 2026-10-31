# Teze: raziskava uporabniškega poteka in merljivega spremljanja

**Datum:** 2026-10-30. **Izhodišče:** pregledna veja `feat/uxui-demo-upgrade`, produktni rez `9c4aebf`, dokumentarni `6a9f07c`. **Vrsta:** statična raziskava in predlog za naslednji SPEC; brez implementacije, zagona modela, baze, API ali spreminjanja demo okolja. Uporabnik želi Teze lažje spremljati in imeti konkretne podatke, na katere se lahko opre. Spodnje rešitve so predlog raziskovalca, ne že potrjena uporabnikova izbira.

**Prejeti odgovor v istem krogu:** »Parametri so odvisni glede na ciljno dolžino investicije. Je pa kot si zapisal vec parametrov.« Potrjena uporabniška smer je zato več meril glede na nameravano trajanje naložbe, ne univerzalen izbor dveh ali treh kazalnikov. Uporabnik je zahteval tudi spremljanje lastne ideje v Uspešnosti; to ne potrjuje samodejno novega načina ustvarjanja Teze brez analize.

## 1. Kaj danes res obstaja

| Del poti | Preverjena pogodba in dokaz | UX posledica |
|---|---|---|
| Nastanek | `services/api/preza/domain/thesis.py:26` sprejema samo `analysis_run_id`; `services/theses.py:79` zahteva zaključeno analizo s kartico in vsaj enim nepraznim `upgrade_if`/`downgrade_if`. | Teze danes ni mogoče prosto napisati s seznama ali ustvariti samo iz tickerja/novice. Gumb je v analizi, ne na Tezah. |
| En instrument, več različic | `models.py:461` določa eno tezo na instrument; `ThesisRevision` na `:478` ima unique po thesis/version in thesis/analysis_run, največ eno aktivno različico. | Nova analiza pomeni lahko nov osnutek iste teze, ne še dodatne aktivne naložbene teze za isti instrument. To je pomembna meja morebitnega ročnega ustvarjanja. |
| Osnutek | `services/theses.py:100–145` kopira sprožilce kot posamezne trditve; podvojen klik vrne že obstoječo različico iste analize. `ThesisDetail.tsx:315` omogoča urejanje besedila in razveljavitvenega pogoja ter CAS edit_count. | Del za pregled in dopolnitev obstaja, manjka pa razlaga namena posameznega polja, izvornega pogoja in rezultata aktivacije. |
| Aktivacija | `services/theses.py:182` potrdi osnutek in prejšnjo aktivno različico označi superseded. UI potrditve ne dovoli ob neshranjenih spremembah. | Pred potrditvijo je treba jasno pokazati, kaj bo zamenjano. Aktivacija ni nov modelni izračun ali naročilo. |
| Vsebina trditve | `domain/thesis.py:115` vsebuje statement, original_text, trigger_kind, invalidated_if, status, expires_at, source/as_of in dogodke. | Ni strukturirane metrike, enote, obdobja, praga, začetnega/trenutnega opažanja ali posnetka ob aktivaciji. Sam prikaz nove tabele tega ne bo ustvaril. |
| Ročna odločitev | `services/theses.py:204` dovoli status aktivne različice ob expected_status; sprememba shrani append-only dogodek z razlogom in dokazom. `domain/thesis.py:81` zahteva dokaz za confirmed/weakening/broken. | Dokaz in odločitev že imata sled. Obrazec je težek za hitro branje, ker so dokazni obrazci in zgodovina pri vsaki trditvi. |
| Tedenski agentov pregled | ADR-0012, `services/thesis_reviews.py:100,214,336` ter agents `thesis_tracker/context.py` uporabljajo nespremenljiv omejen posnetek novic/filingov, do 20 trditev, 30 virov, 32 KiB. Brez novih dokazov je `done_no_evidence`, brez modelnega klica. | Pregled trenutno preverja besedilne trditve proti shranjenim objavam, ne spremlja poljubnih strukturiranih fundamentalnih meril. Stari ADR urnik ni obljuba časa: dejanska procesna politika/okna/pavza imajo prednost. |
| Predlog ni dejansko stanje | `services/thesis_reviews.py:475` in `ThesisReviewProposals.tsx:116` zahtevata aktivno isto različico, nespremenjen status/zadnji dogodek in izrecen sprejem; zavrnitev zahteva razlog. | Ločiti je treba »Tvoja zadnja potrjena ocena« od »Nov agentov predlog«. Stale ali nezadosten dokaz ne postane nov status. |
| Opozorilo na možen zlom | `services/thesis_reviews.py:87,409` dovoli `thesis_break` že ob predlogu broken z uradnim citiranim virom, ki ni govorica. Status trditve ostane do sprejema nespremenjen. | Vidno mora pisati »Možen zlom, predlog pregleda«, ne trditi, da je uporabnik tezo že zavrnil. Zavrnitev predloga zapre njegov odprti signal. |
| Seznam | `ThesisList.tsx:11–18,63–102` prikazuje simbol/ime, aktivno verzijo/osnutek, vseh pet statusnih števcev in updated_at. Filter je točen simbol, stanje in pagination sta lokalna React stanja. | Ni seznama stvari za odločitev, povzetka glavne trditve, števila novih predlogov, zadnjega dejanskega pregleda ali roka. Vseh pet ničelnih števcev porablja prostor. Reload ne ohrani filtra/strani v URL. |
| Podrobnosti | `ThesisDetail.tsx:453–578` bere podrobnosti vseh različic, vse strani pregledov in pending predlogov, prikaže aktivno različico pred ostalimi. | Zgodovinska besedila in tehnični run podatki preglasijo vprašanje »Kaj se je spremenilo in kaj zahteva mojo odločitev?«. Skrivanje zgodovine v UI samo ne omeji prenosa podatkov. |
| Pot v Uspešnost | `domain/backtest.py:12,51` in `services/backtest.py:69–94` bereta samo Signal in zaključeni AnalysisRun. | Teza/claim/sprejem predloga danes niso samostojen vir študije. Signal `thesis_break` lahko vstopi v signalno kohorto tudi pred sprejemom predloga; to ni merilo resničnosti teze. |

Prebrani so SESSIONS/PLAN/BACKLOG, DESIGN/VOICE, README API/web/agents, ADR-0012 in ADR-0022 ter zgornje poti in pripadajoče UI sheme. Ni bilo novega omrežnega ali modelnega preverjanja. Številke testov stare seje niso nov dokaz te raziskave.

## 2. Ključna semantična tveganja pri novi postavitvi

1. **Pogoj analize še ni preverjena pozitivna trditev.** Izvorna `downgrade_if` je lahko »če marža pade pod …«. Njena izpolnitev sama ne pomeni, da je isto besedilo ovrženo. ADR-0012 in agents `prompts.py:11–18` izrecno prepovedujeta avtomatsko negiranje/računanje pragov iz besedila. UI mora pokazati tip in izvorni pogoj ter uporabniku omogočiti zapis »Kaj mora ostati res« in »Kaj bi to ovrglo«. Modelni predlog besedila je le predlog; ne parsati številk iz proste povedi v pravilo.
2. **updated_at ni datum zadnjega preverjanja.** `services/theses.py:245–266,305` združuje ustvarjanje/urejanje/potrditev/dogodke trditve. Uspešen pregled brez spremembe statusa se ne sme lažno prikazati kot nov dokaz. Ločena polja: zadnja uporabnikova odločitev, zadnji poskus pregleda, zadnji uspešni pregled z njegovim input_cutoff in zadnji datum konkretnega vira.
3. **Cena in veljavnost teze sta različni stvari.** Pozitivni donos ali bližina vstopne cone ne dokazujeta, da poslovna teza drži. Cena mora biti ločen kontekst, s svojo kotacijo/valuto in datumom; odločilna dokazila ostanejo pri trditvah.
4. **Ni dokazov ni enako drži.** `done_no_evidence`, insufficient, failed_unknown, stale, paused in skipped_limits potrebujejo razumljive različne izide. Trenutni `ThesisReviewRun` failed_unknown preslika v splošni failed; podrobnost naj ohrani negotovost in odsotnost avtomatske ponovitve. Gumb Osveži danes samo ponovno prebere shranjeno stanje, ne sproži pregleda/modela.
5. **Potek roka ni samodejno vsebinsko ovrženje.** Polje expires_at in status expired obstajata; v pregledanih runtime poteh ni najden samostojen izvajalnik, ki bi trditvi ob roku zapisal dogodek expired. Prvi UX rez lahko pokaže »Rok je potekel«, ne sme pa na skrivaj spreminjati stanja ali obljubljati avtomatike.
6. **Krajši prikaz ne sme skriti neskladij.** Oznake govorice, manjkajoči vir/čas, stale predlog, neaktiven osnutek in konflikt odločitve ostanejo vidni. Metoda, interni UUID/model ter polna zgodovina lahko gredo v razširljive podrobnosti.
7. **Ustvarjen osnutek še ni zagotovilo podpore avtomatskemu pregledu.** `DecisionCard` ne omeji števila besedilnih sprožilcev, `create_draft` pa jih kopira vse; review ima MAX_CLAIMS=20. Novi potek mora pred aktivacijo prikazati dejansko omejitev in njen učinek, ne obljubljati tedenskega preverjanja za nepodprt obseg. Delitev/omejevanje trditev je ločen izrecen produktni dogovor, ne tiho zavračanje ali odrez podatkov.

## 3. Trije smiselni pristopi

| Pristop | Kaj dobimo | Cena in omejitev |
|---|---|---|
| A. Ureditev sedanjih tez | Kompakten seznam, jasni zavihki Aktivno / Za odločitev / Osnutki, kratek povzetek, podrobnosti z eno trditvijo na vrstico, zgodovina in tehnični podatki zloženi. | Najhitrejši vidni napredek, brez novega plačljivega dela. Za dejanske pending/last-review povzetke na celotnem seznamu je potreben bounded read API; ne ponavljati poizvedbe za vsako vrstico. Strukturiranih »prej/zdaj« meritev s tem še ni. |
| B. Dve fazi: jasen potek, nato dokazljiva merila | Najprej A in boljši nastanek iz analize, nato izrecno definirani kazalniki/opažanja z začetnim in sedanjim stanjem ter virom/časom. | **Priporočilo.** Uporabna prenova pride prej; podatkovne pogodbe za vsako metriko imajo svoj SPEC in teste. Ne zahteva, da se prej priklopi nov plačljivi analitik. |
| C. Polavtomatski samostojni dnevnik tez | Ročno ustvarjanje neodvisnih tez, AI predlog kazalnikov, samodejno zajemanje novih virov in periodične presoje. | Najširši obseg: nova identiteta/revizije/viri, stroški in urniki; trenutna shema zahteva analysis_run_id. Ni primeren prvi rez samo zaradi lažje postavitve. Status bi tudi tu potrdil uporabnik. |

To ni odločitev uporabnika. Root naj izbiro vključi v usklajen predlog celotnega novega UX kroga.

## 4. Predlagana uporabniška pot B

**Vstop iz končane analize:** ob jasno poimenovanem »Spremljaj tezo« povzetek pove, da nastane osnutek brez nove LLM analize. Če že obstaja, odpre isti osnutek; če instrument že ima aktivno različico, pokaže razliko pred zamenjavo. Gumb na vrhu Tez lahko ponudi »Izberi zaključeno analizo«; prosta ročna teza je ločena prihodnja razširitev, ne navidezno delujoč obrazec.

**Pregled zapisa:** uporabnik vidi simbol in kotacijo, datum izvorne analize, osnutek in izvorne upgrade/downgrade pogoje. Izbere oziroma preveri nameravano trajanje naložbe in ustrezen predlagani nabor več meril; pred aktivacijo lahko merila dodaja, izključuje ali ureja. Pri vsaki točki: razumljiva izjava, razveljavitveni pogoj, neobvezen rok. Ločeno Shrani osnutek in Aktiviraj spremljanje; neshranjene spremembe ali konflikt ohranijo besedilo. Sprememba aktivne vsebine se kasneje ureja z novo pregledano različico, ne prepisuje starega dokaza.

**Seznam za dnevni pregled:** ena kratka teza na vrstico/kartico: instrument, glavna izjava, stanje posameznih trditev oziroma dejansko opozorilo, nove odločitve, zadnji pregled z izidom ter naslednji relevantni rok. Ne izmišljati enega kompozitnega »zdravja 87 %«. Prednost imajo čakajoči pregledni predlogi, ovržene/oslabele trditve in pretečeni roki; razlog razvrstitve je viden. Osnutki ločeno. Filtri in izbor preživijo reload prek URL. Na telefonu ima vrstica eno jasno dejanje Odpri.

**Podrobnost:** zgoraj »Kaj zahteva tvojo odločitev« in kratek kontekst; nato aktivne trditve. Stolpci/vrstice »Kaj spremljam«, »Zadnja potrjena ocena«, »Kaj je novo«, »Dokaz/datum«, »Dejanje«. Sprejem predloga ostane izrecen in zahteva aktualni status/zadnji dogodek. Zgodovina revizij, tehnični model/run UUID in celoten audit so sekundarni, ne glavna vsebina. Brez svežega dokaza je vidno »Ni novih dokazov«, nikoli zeleno »drži« po privzetem.

**Povezava v Uspešnost:** ločena akcija »Spremljaj izid mnenja« iz izvorne analize ali signala. Ne spreminja statusa teze, ne ustvari novega modelnega mnenja in ne pomeni naročila. Cena/donos mnenja in preverjanje resničnosti trditve sta ločeni metriki. Če bo dodana spremljevalna zbirka, je izbor record_id/source izrecen in idempotenten; obstoječa celotna kohorta vseh shranjenih zapisov ostane ločen način. Tega vira še ni v sedanji BacktestRequest pogodbi.

**Lastna ideja v Uspešnosti:** uporabnik zahteva tudi svoj izvorni zapis za spremljanje. Ta mora imeti svojo stabilno identiteto, uporabnikov zapis/smer/horizont in čas nastanka; ne izmišljene zaključene analize, modelnega mnenja ali avtomatsko ustvarjenega signala. Izbor lastne ideje ne ustvari Teze in ne spremeni njenega aktivnega stanja. Če bo pozneje omogočeno ustvarjanje samostojne Teze iz take ideje, potrebuje ločen obseg z jasnim pravilom za obstoječo eno tezo na instrument, izvorno analizo in revizije. To ostaja predlog, ne prikrita sprememba sedanje pogodbe.

## 5. Merljivi podatki za naslednjo fazo

Predlog nove pogodbe, ne sedanje polje: trditev lahko ima eno ali več spremljanih meril s stabilnim metric_key, instrument/claim/revision identiteto, definicijo, enoto/valuto, obdobjem/osnovo (npr. TTM proti forward), primerjalnim operatorjem in po uporabniku potrjenim pragom. Začetno opažanje in nova opažanja so nespremenljivi zapisi `{value, source, as_of, fetched_at, basis, coverage}`. Izračun razlik izvede Decimal koda; LLM lahko le razloži podprte podatke.

Vsako merilo mora pred uporabo odgovoriti: kateri točno podatek, iz katerega podprtega vira, za katero obdobje/kotacijo, kdaj je bil znan in kako ravnamo ob vrzeli/popravljeni objavi. Za prvo različico uporabiti samo že podprte shranjene podatke. Poljubno prosto besedilo ostane kvalitativno merilo z dokazom; ne pretvoriti ga v lažno numerično pravilo. Manjkajoča vrednost je neznano, ne nič. Različni valuti/osnovi/obdobji se ne primerjajo brez potrjene pretvorbe. Popravljen izvor ne prepiše zgodovinskega baseline.

Prestop praga lahko ustvari opozorilo »Preveri trditev« z izračunom in virom. Ne spremeni samodejno statusa, ne priporoči nakupa/prodaje in ne nadomesti presoje poslovne teze. Dodatek metrik zahteva novo shemo/migracijo in OpenAPI/TS ter lastno podatkovno preverbo; ni del kozmetičnega preurejanja.

### 5.1 Več meril glede na ciljno trajanje

Spodnje skupine so **predlagane predloge**, ki sledijo prejetemu odgovoru, ne obvezne že potrjene številčne meje ali seznam vseh privzetih metrik. Izbira daljšega horizonta sama ne vključi vseh podatkovnih virov ali novega plačljivega pregleda. Pri vsaki predlogi se pokaže le podprt preverljiv podatek oziroma izrecno prazna pokritost. Poljubnega manjkajočega prihodnjega kazalnika se ne ocenjuje z modelom.

| Nameravana naložba | Predlagane skupine več meril | Kaj mora ostati ločeno |
|---|---|---|
| Kratka, povezana z dogodkom ali vstopom | Dogodek/katalizator in njegov preverjeni datum, vstopna cena ali cona, pogoj razveljavitve, rok za ponovno presojo. | Cena v coni ne potrdi poslovne trditve. Neznan datum dogodka ostane neznan, ne izmišljena časovnica. |
| Srednja | Rast in marže v ustreznem poročevalnem obdobju, bližnji katalizatorji, vrednotenje z jasno TTM/forward osnovo ter razveljavitveni pogoji. | Poročana rast, pričakovana rast in vrednotenje so različni podatki. Primerjava zahteva isto definicijo, enoto, kotacijo in primerljivo obdobje. |
| Dolga | Poslovna predpostavka, denarni tok, dolg in sposobnost servisiranja, dividende kadar so pomembne, ter periodični oziroma letni pregled glavnih trditev. | Letni pregled ne izračuna prihodnje donosnosti. Dividenda ali rast cene sama ne potrdi trajne poslovne kakovosti; izvorna teza in popravki imajo zgodovino. |

Nameravano trajanje je uporabnikov cilj in mora biti zapisano ob različici; opredelitev točnega datuma ali obsega trajanja je del prihodnje pogodbe. **Pogostost pregledovanja je drugo polje.** Večletna naložba ima lahko reden pregled novic ali četrtletnih objav; kratka ideja ima lahko en sam dogodek za presojo. Pogostosti ne sklepamo iz horizonta in nastavitev ne spreminjamo brez uporabnikove odločitve. Obstoječa procesna politika/okna/pavza in stroškovne omejitve ostanejo avtoritativne.

Tudi **horizont študije izidov** 1/5/20/60 shranjenih sej je tretja ločena stvar. Rezultat po 60 sejah je vmesno opažanje večletne ideje, ne »teza zaključena«, doseženi triletni cilj ali razlog za avtomatski status. Za tri leta ni dovolj podaljšati oznake ob sedanjem 60-sejnem izračunu; razširitev zgodovine/izračuna potrebuje svoj podatkovni SPEC.

Pred aktivacijo uporabnik pregleda izbrana merila, njihove podprte vire, osnovo in roke. Nabor nima vnaprej določene uporabniške omejitve na 2–3 merila, vendar mora implementacija izrecno upoštevati omejitev pregledovalnika 20 trditev; število meril ni tiho enako številu LLM trditev. Smiselne tehnične omejitve se določijo v SPEC in razložijo, podatkov se ne reže brez opozorila.

## 6. Majhne izvedbene meje za SPEC in prevzem

| Rez | Samostojen rezultat | Preverljivi primeri |
|---|---|---|
| T-UX1: opis poti in prezentacija | Glavno/sekundarno besedilo, zložena zgodovina, izvor pogoja, jasna aktivna različica, preimenovan refresh. Uporabi sedanjo pogodbo. | SL/EN, desktop/phone; tri aktivne trditve se preberejo brez odpiranja audit zgodovine; failed_unknown ni isti pomen kot no_evidence; 0 novih mutacij/modelov ob odprtju strani. |
| T-UX2: bounded seznam za odločanje | Paginiran summary z last_review status/cutoff, pending_count in roki, URL filtri/sort; en paket SQL za stran. | 1000 tez, stran do 30: konstantno število queryjev brez N+1, brez prenosov vseh audit payloadov; pending filter pred LIMIT; ista odločitev ne podvoji števca; stale predlog vidno ločen. |
| T-UX3: nastanek iz analize | Jasna akcija iz analize, izbira zaključene analize s strani Tez, pregled izjave in izvornega pogoja ter zamenjave aktivne različice. | Dvojni klik → ista različica; osnutek brez sprožilcev/nezadostna analiza → razumljiv razlog; edit konflikt ohrani lokalno delo; samo aktivacija uporabnika zamenja prejšnjo revizijo; ob aktivaciji 0 plačljivih klicev. |
| T-DATA1: merila z opažanji | Ločen SPEC za nabor več meril glede na trajanje, katalog, baseline/current, pokritost in popravke; najprej omejen potrjen katalog, ne vsi kazalniki ali viri privzeto. | Kratek in dolg horizont ponudita različne predloge; uporabnik jih pred aktivacijo uredi. Dejanski datumi/enote/TTM/forward/valute ostanejo ločeni; unknown/stale ni uspeh; baseline preživi nov uvoz. Reden pregled ne spremeni naložbenega horizonta; 60 sej ne zaključi triletne teze; 0 novih plačljivih klicev ob izbiri predloge. |
| T-LINK1: povezave v Uspešnost | Izrecno spremljanje nespremenljivega mnenja/signala in samostojne lastne ideje, z vrnitvijo na točen izvor in ločeno identiteto. | Isti klik/dva zavihka → en izbran zapis; ideja/mnenje brez smeri ostane vidni preskok; izbor ne sprejme review predloga, ne ustvari signala, analize ali Teze. Samostojna Teza ostane ločen predlog za prihodnjo pogodbo. |

A3/A5 lastništvo pregledov je obstoječ ločen engineering dolg, opisan v S-024. Vizualna prenova se lahko preverja s shranjenimi podatki; ne sme pa razglasiti zastale avtomatike za popravljeno ali dodati brezpogojnega plačljivega »ponovi«.

## 7. Prejeti odgovor in preostale odločitve

Vprašanje o glavnih parametrih je **odgovorjeno**: parametri so odvisni od ciljnega trajanja naložbe in jih je več. Ni treba ponovno zahtevati univerzalnega izbora dveh ali treh. Naslednji SPEC naj najprej določi pogodbo nameravanega trajanja, uporabniško uredljivih več meril in preverjene pokritosti, ločeno od pogostosti pregledov in horizonta študije izidov. Predloge v §5.1 so konkreten popravljiv predlog raziskovalca, ne sklep, da je uporabnik potrdil vsako posamezno metriko ali številčno mejo.

Zahtevana lastna ideja v Uspešnosti je samostojen izvorni zapis, ne dovoljenje za prikrito spremembo ThesisRevision.analysis_run_id ali omejitve ene Teze na instrument. Če bo želel tudi samostojen zapis Teze brez analize, zahteva to ločen predlog in jasen odnos do obstoječe aktivne Teze. Ni treba blokirati jasnejšega prikaza že shranjenih tez ali priprave spremljanja lastnih idej zaradi te prihodnje odločitve. Ni potrebe ponovno vprašati o jeziku, 48 px, :3000 ali pravilu človeške potrditve.

## 8. Dokazne meje

Ta dokument ne trdi, da so merila, začetni/trenutni podatki, ročno ustvarjanje teze ali spremljevalna zbirka že zgrajeni. Ne trdi, da ima demo sveže dejanske finančne podatke. Preurejanje podatkov ne odpravi manjkajočih virov. Potreben je naslednji uporabniški dogovor o pristopu, nato SPEC z natančnimi API/vmesniki, izvedbeni plan in regresijski dokaz; deploy :3000 ostane ločen.
