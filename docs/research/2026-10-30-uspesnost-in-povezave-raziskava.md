# Uspešnost in dodajanje iz drugih strani: raziskava

**Datum:** 2026-10-30. **Prebrana osnova:** `6a9f07c`. **Status:** raziskava za SPEC in plan, brez produktne implementacije. **Prejeti odgovor:** uporabnik želi v tem krogu vključiti tudi lastne ideje brez predhodne analize in več parametrov, odvisnih od nameravanega obdobja naložbe. Konkretna predloga metrik še ni potrjena. Raziskava temelji na kodi, projektni dokumentaciji in tem odgovoru; brez branja baze, zagonov API, modelnih klicev, ponudnikov ali posegov v okolji :3000/:3100. Testi spodaj so predlagana merila, ne rezultati novega zagona.

## 1. Kaj je danes in zakaj stran ni jasna

Uspešnost danes na isti strani zaporedno prikazuje dva različna izračuna. Uporabnik nima osebne zbirke predmetov, ki bi jih izrecno dodal za spremljanje. Beseda »shranjeni« v obstoječi študiji pomeni zapise, ki že obstajajo v podatkovni bazi, ne uporabnikove izbire.

| Del | Dejanska pogodba | Posledica za uporabnika |
|---|---|---|
| `BacktestPanel` | Ročni `POST /backtest`, vsi signali in zaključene analize; razpoložljivost, horizont shranjenih sej, stroški, moč/status signalov, omejitev 1000. | Lahko primerja pretekla mnenja; ne zna izbrati konkretnega ID ali osebne zbirke. |
| Obstoječi pregled signalov | `GET /track-record` in `/outcomes`, samo shranjeni `SignalOutcome`, datum nastanka signala, alfa in kalibracija moči. | To so globalni izidi signalov, ne izidi analiz ali osebnih zaznamkov. |
| Spremljaj / Sprejmi | Spremenita `Signal.status` v `watching` / `accepted`. | Gre za obravnavo signala, ne ločeno evidenco spremljanja uspešnosti. |
| Watchlista | Članstvo instrumenta, ne konkretnega mnenja o njem. | Isti instrument ima lahko več različnih signalov in analiz; članstvo instrumenta ne določi, katero mnenje se meri. |

Oba izračuna uporabljata zaporedje shranjenih dnevnih sveč, **ne koledarskih dni**. Razlikujeta pa se v vstopu: `compute_outcome` začne s prvo svečo na dan signala ali pozneje; študija ADR-0022 začne strogo po UTC dnevu razpoložljivosti in izključi tekoči UTC dan. Študija odšteje določene stroške na obeh straneh; globalni pregled uporablja že zapisane izide in alfo. Zato ni pravilno izenačiti dveh odstotkov samo zato, ker imata oba oznako 20.

Pomembna robna razlika: `compute_outcome` trenutno vse smeri razen `down` obravnava kot dolgo smer, študija pa `neutral`/neznano preskoči. To je ugotovitev statičnega pregleda, ne izmerjeno število prizadetih vrstic. Pri prenovi je ne smemo skriti ali tiho prepisati zgodovinskih globalnih statistik; morebitno popravljanje stare pogodbe zahteva ločeno odločitev in regresijske dokaze.

## 2. Tri izvedljive smeri

| Možnost | Kako bi delovala | Korist in cena |
|---|---|---|
| A. Jasnejša študija brez zbirke | Dva jasno ločena pogleda, povezava »Poglej izid« iz signala/analize in izračun samo tega zapisa. | Najmanj sprememb; odpravi zmedo pri konkretnem mnenju, vendar ne izpolni trajnega »dodaj v spremljanje«. |
| B. Osebna zbirka obstoječih mnenj | Ločeno trajno članstvo konkretnih signalov in zaključenih analiz; gumb iz izvorne strani, pregled v Uspešnosti, ista deterministična metoda ADR-0022. | Manjši obseg, vendar po prejetem odgovoru ni zadosten samostojen rezultat tega kroga, saj ne omogoči lastnih idej. |
| C. Osebna zbirka in dnevnik lastnih idej | Poleg B še samostojna lastna ideja s smerjo, časom, razlogom, obdobjem naložbe in strukturiranimi merili; poznejši izidi od aktivacije ideje. | **Priporočena smer po uporabnikovem odgovoru.** Zahteva pravila osnutka/aktivacije, kotacije, različic in ločeno merjenje cene ter vsebinskih trditev; ne zahteva predhodne analize ali LLM klica. |

Uporaba `accepted` ali `watching` namesto novega članstva ni samostojna ustrezna možnost: ista statusa že vodita inbox, analize ju nimajo, status se lahko spremeni in pri govorici »Sprejmi« namenoma ni dovoljeno. Za osebno zbirko zaradi tega ne smemo spreminjati pomena obstoječih statusov.

## 3. Predlagan uporabniški tok za možnost C

Predlog poimenovanja na Uspešnosti: trije razločno poimenovani pogledi **Moje spremljanje**, **Vsi signali** in **Primerjava mnenj**. Prvi je osebna zbirka, drugi ohrani obstoječe globalne izide in kalibracijo, tretji vsebuje širšo ročno študijo obstoječih zapisov. V prvem koraku ni nove samostojne aplikacije, nove analize ali polnega portfeljskega backtesterja. Predlagana privzeta vstopna stran je Moje spremljanje; obstoječe neposredne povezave z globalnimi parametri morajo še odpreti svoj prvotni pogled.

1. Na podrobnostih signala je izrecen gumb **Dodaj v spremljanje**. Ne nadomesti »Spremljaj« v inboxu. Po potrjenem shranjevanju se spremeni v **V spremljanju**, kratek odziv ponudi **Odpri spremljanje** in **Razveljavi**. Razliko je smiselno pojasniti v pomoči; dodatnih dolgih opozoril na vsaki kartici ni treba dodajati.
2. Na zaključeni analizi isti gumb shrani konkretni `run.id`. Na seznamu z zadnjo uspešno analizo mora biti razvidno, katero izvedbo dodaja. Naslednja nova analiza istega instrumenta ne zamenja že dodane.
3. Na Predlogih gumb deluje na povezani signal ali posamezno zaključeno analizo. Hitra presoja `verdict_result` ni avtomatsko smer tržnega gibanja, zato se je ne preslika v nakup/prodajo. Če ima predlog oba izhoda ali več analiz, so na voljo konkretno označene izbire, ne samodejno dodajanje vseh. Če ni nobenega primernega izhoda, ostane povezava do predloga in jasen razlog, ne namišljena merljiva vrstica.
4. Radar in Vstopi lahko ponudita isto dejanje, kadar imata konkreten povezani signal. Sam dogodek ali trenutna vstopna kartica ni zgodovinsko mnenje z lastno stabilno identiteto. Brez signala ponudita ogled podrobnosti, ne ustvarjanja signala za potrebe spremljanja. Instrument/watchlista ne izbereta »zadnjega mnenja« brez prikaza njegovega časa in tipa.
5. Moje spremljanje pokaže instrument, vrsto zapisa, izvorno mnenje/smer, **mnenje na voljo**, **dodano v spremljanje**, trenutno stanje merjenja in povezavo na izvor. Stanja vključujejo izmerjeno, čaka na dovolj sej, brez jasne smeri in nepopolne podatke. Nevtralni in preskočeni zapisi ostanejo v seznamu.
6. Osnovni pogled izpostavi seznam in horizont. Izračun izrecno sproži **Izračunaj izide**. Stroški, datumski filtri in podrobna metoda so pod **Možnosti izračuna**; veljavni stroški/horizont in obseg ostanejo kratko vidni ob rezultatu. Odstranitev iz aktivnega pogleda ne izbriše mnenja, signala, analize ali izračunanih izidov.
7. **Dodaj svojo idejo** odpre obrazec brez naročanja analize. Uporabnik izbere nedvoumno kotacijo, navede smer, svoj razlog in nameravano obdobje naložbe ter dopolni zanj relevantna merila. Osnutek lahko ureja. Dejanje **Začni spremljanje** objavi nespremenljivo različico s trenutnim časom strežnika in jo doda v osebno zbirko. Katere skupine meril se prikažejo za posamezno obdobje, določi povezani SPEC; uporabnik še ni potrdil točno določenega seznama ali pragov.

»Poglej izid« je dodatno, ločeno dejanje: odpre en konkretni predmet brez dodajanja v zbirko in brez samodejnega novega LLM klica. Uporabi isti tipizirani ključ kot zbirka. Uporabnik lahko po ogledu posebej izbere Dodaj v spremljanje.

Zgornji povzetek zbirke naj poudari **dodano / izmerjeno / čaka / preskočeno**. Delež pozitivnih neto izidov in povprečni neto izid se izračunata samo iz dejansko izmerjenih zapisov in sta označena kot izida izbranih mnenj, ne donos portfelja. Signal in analiza, ki izhajata iz istega dogodka, sta lahko ločeni mnenji; v združenem povprečju nista neodvisni stavi. Privzeta povzetka po tipu zapisa in povezava med sorodnima izhodoma to naredita vidno.

## 4. Podatkovna pogodba, ki jo potrebuje SPEC

### Identiteta in trajnost

- Ključ je **vrsta zapisa + izvorni UUID** (`signal`/`analysis`/samostojna različica lastne ideje + `id`), v območju ustrezne osebne zbirke. UUID sam ni dovolj. Ne zamenjati tega s poljem `Signal.source` (`radar`, `manual`, `agent`, `rule`) ali `AnalysisRun.engine`, ki označujeta izvor, ne vrste predmeta. Lastna ideja je tretji samostojen tip, ne izmišljeni `AnalysisRun` ali `Signal` z izvorom manual.
- Enolična omejitev v bazi prepreči podvojitev istega člana tudi po dvojnem kliku, izgubljenem odgovoru in iz dveh zavihkov. Ponovljen dodaj vrne isto aktivno članstvo. Isti instrument z različnima mnenjema in isti UUID v dveh različnih vrstah sta dovoljena.
- Dodajanje mora strežniško preveriti obstoj in primernost izvornega zapisa; zaključena analiza potrebuje `done` in `finished_at`. `queued`/`running`/`failed` nimajo končnega mnenja. Hold je mogoče shraniti, vendar je njegov cenovni izid preskok. Kasnejše tiho čakanje na »naslednjo uspešno analizo« ni članstvo konkretnega mnenja.
- Članstvo ima nespremenljivi čas prvega dodajanja in revizijsko sled arhiviranja/obnove. Ponovno dodajanje istega arhiviranega zapisa lahko obnovi članstvo, ne izbriše prejšnje izbire in časa. Pogodba odstranitve naj zato pomeni »arhiviraj«, četudi je v UI poimenovana Odstrani iz spremljanja. Razveljavitev ohrani sled.

### Lastna ideja brez predhodne analize: omejena pogodba

Ta del je vključen v sedanji načrtovani obseg na izrecno uporabnikovo željo. Spodnja podatkovna struktura in omejitve so konstrukcijski predlog, ne trditev, da je uporabnik izbral vsak stolpec ali metriko.

| Vsebina aktivne različice | Predlagano pravilo |
|---|---|
| Identiteta instrumenta | Trajni ID razrešene kotacije, simbol, trg/borza, vrsta in valuta s podatkovnim virom in časom. Sam prosti tiker ni dovolj za aktivacijo. Če manjka identiteta ali je več možnih kotacij, ostane osnutek z izrecno izbiro, ne privzeti USD ali prvo ujemanje. |
| Smer | Uporabnik izrecno izbere rast, padec ali nevtralno spremljanje. Sistem ne sklepa smeri iz prostega besedila in je ne prepiše po poznejši analizi. Nevtralna ideja je dovoljena, vendar nima smernega cenovnega zadetka. |
| Razlog | Uporabnikovo besedilo, označeno kot njegova trditev. Dokazila so povezave z izvorom/časom; govorica ostane govorica. Vnesena ciljna cena ali številka iz objave ni preverjeno tržno dejstvo. |
| Nameravano obdobje | Podatek, kako dolgo naj bi se ideja razvijala, in nedvoumna interpretacija merilnega roka ali okna. Ni enak kot obstoječi izbor 1/5/20/60 sej, ki je zgolj časovna razdalja cenovnega izračuna. Če uporabnik spremeni obdobje osnutka, se nezdružljiva merila vidno označijo za ponovni pregled, ne tiho ohranijo ali izbrišejo. |
| Več meril | Verziona zbirka meril s tipom, enoto, časovnim oknom, pogojem in dokazom/virom, kadar je merilo strojno preverljivo. Razpoložljiva polja so odvisna od nameravanega obdobja. Konkretne skupine, obveznost polj in pragovi so predmet povezanega SPEC, ne avtomatska privzeta izbira iz tega dokumenta. |
| Izvorni čas | Strežniški čas objave aktivne različice je njen nespremenljivi `created_at`/`available_at`. Čas nastanka osnutka je ločen `draft_created_at`; osnutek ni objavljena napoved in njegov zgodnejši čas se ne uporabi za začetek merjenja. |
| Članstvo | `saved_at` označuje dodajanje aktivne različice v zbirko. Pri prvem »Začni spremljanje« je lahko enak objavi, pojma pa ostaneta ločena. Pri kasnejšem ponovnem dodajanju je razpoložljivost prvotne različice še vedno nespremenjena. |

**Osnutek in aktivacija.** Osnutek je urejljiv in ni v imenovalcu izidov. Aktivacija atomarno preveri instrument, smer, razlog, obdobje in veljavnost meril, ustvari nespremenljivi posnetek različice in članstvo. Napaka ne pusti polovice zapisa. Ponovitev iste aktivacijske namere po izgubljenem odgovoru vrne isto različico, ne nove napovedi. Aktivni smeri, razlogu, roku, začetnemu času ali ciljem ni mogoče popravljati za nazaj. Uporabnik lahko pripravi novo različico iz kopije; ta dobi svoj čas aktivacije in povezavo na predhodnico, stare vrednosti in izidi pa ostanejo sledljivi. Zaporedne različice iste ideje se v povzetku ne obravnavajo kot neodvisni uspešni poskusi.

**Cenovni izid proti stanju teze.** Smerni cenovni izid je ločena deterministična meritev po razpoložljivosti aktivne različice. Za podprte kratke horizonte se lahko uporabi metoda ADR-0022; nameravanih večletnih idej ni dopustno označiti za uspešne samo z 20-sejnim izidom. Če dolgoročni merilni rok/ustrezni podatki še niso podprti, je izrecno stanje »Merilo še ni izmerljivo«, kratkoročna sprememba cene pa ostane vmesni podatek. Razširitev horizonta prek 60 sej zahteva svojo omejeno in preverjeno poizvedbo, ne neomejenega nalaganja zgodovine.

Vsebinsko merilo, npr. preverjanje uporabnikove poslovne trditve, ni dokazano samo zato, ker je cena zrasla. Zahteva lasten dokaz ali deterministični podatek v ustreznem časovnem oknu. Merilo brez razpoložljivega podatkovnega vira je »Za ročni pregled«, ne avtomatično izpolnjeno. Nevtralna ideja ima lahko vsebinska merila, četudi je njen smerni cenovni izid preskočen. Cena, trditev, uporabnikova odločitev in stanje potrditve so zato ločene osi. Shranitev ne obljubi samodejnega zbiranja dokazov, analiziranja ali opominjanja.

**Začetni podatkovni posnetek.** Če pri aktivaciji že obstaja cena ali preverljiva vrednost merila, posnetek navede točen instrument, enoto/valuto, vrednost, vir, `as_of` ter čas zajema; tržni podatek ne sme biti poznejši od trenutka, ki ga predstavlja. Manjkajoča začetna vrednost je vrzel, ne cena, ki jo uporabnik vpiše kot preverjeno dejstvo. Shranjevanje samo bere obstoječe podatke in ne sproži ponudniškega ali LLM klica. Prva upravičena prihodnja zaključna cena je kasnejši podatek izračuna, ne domnevno znana cena ob aktivaciji. Način obravnave poznejših popravkov sveč je enak jasno označenemu ponovnemu izračunu pri drugih vrstah zapisov.

**Brez izdelovanja preteklih napovedi.** Aktivna različica ne sprejme odjemalčevega preteklega `available_at`. Morebitna ločena funkcija za uvoz starega osebnega zapiska hrani navedeni pretekli datum samo kot uporabnikovo navedbo, ne kot sistemski dokaz pravočasne napovedi. Če se pozneje doda retrospektivna simulacija s poljubnim datumom/ceno, mora biti izrecno označena **Za nazaj simulirana ideja** in izločena iz vnaprejšnje osebne natančnosti ter globalnih statistik. To je opcijska razširitev, ne pogoj za sedanjo lastno idejo od aktivacije dalje.

### Razpoložljivost, shranjevanje in posnetek

- `available_at` ostane izvorni `Signal.created_at` oziroma `AnalysisRun.finished_at`, kakor določa ADR-0022. `saved_at` je trenutek uporabnikovega dodajanja. V UI gre za dva različna podatka. Ne uporabljati `trade_date`, `created_at` nedokončane analize ali časa prikaza strani kot časa končnega mnenja.
- Predlagana metoda za prvi korak meri **izid prvotnega mnenja od razpoložljivosti**, ne od naknadnega dodajanja. Besedilo »Zgodovinski izid mnenja« mora biti jasno; kasnejše dodajanje ni dokaz, da je uporabnik mnenje izbral že takrat.
- Ob dodajanju se shrani majhen verzioniran posnetek mnenja: ključ, instrument/kotacija, izvor, smer/izvorna ocena, razpoložljivost, razlog, povezave na dokazila in stanje potrditve ob dodajanju. Avtoritativne vrednosti pridejo s strežnika. Trenutni status se lahko prikaže posebej, ne prepisati posnetka. Nova analiza istega instrumenta ni posodobitev tega člana.
- Treba je razlikovati **posnetek mnenja** in **posnetek izračuna**. Obstoječi `/backtest` bere trenutno shranjene sveče, zato se ob dopolnitvi ali popravku podatkov lahko spremeni rezultat istega mnenja. `as_of` in oddani parametri ne pomenijo nespremenljivega arhiva cen. Za prvi korak zadostuje transparenten ponovni izračun s prikazom časa, cen, dni in virov; trajno arhiviranje vsakega izračuna je dodaten obseg.
- Če uporabnik želi meriti **mojo izbiro od dodajanja**, je to druga izrecno imenovana metoda z lastnim začetnim časom. Ne zamenjati je s preimenovanjem stolpca ob nespremenjeni stari matematiki. Lastne ideje bi morale biti od vnosa dalje, brez naknadnega datiranja kot vnaprejšnjih napovedi.

### Natančna vključitev pred omejitvijo rezultatov

Obstoječi `BacktestRequest` nima `record_ids`, `symbol` ali zbirke. Nova povezava na točno mnenje zato zahteva **strežniško** razširitev, ne filtriranja 1000 že vrnjenih vrstic v brskalniku.

- SPEC naj definira ločen obseg vseh obstoječih signalov/analiz / osebne zbirke z lastnimi idejami / točno določenih tipiziranih ključev. Nova vrsta lastne ideje ne razširi pomena obstoječega `source=all` brez eksplicitne verzije pogodbe. Za »Poglej izid« zadostuje natanko en par `(record_kind, id)`, z zanesljivo napako za manjkajoč/neprimeren predmet. Tak pogled ne podeduje skritih filtrov, ki bi iskani zapis izključili.
- Pri zbirki članstvo ali eksplicitni ključi omejijo kandidatski SQL **pred COUNT, ORDER BY in LIMIT**. Šele nato pridejo vidni filtri in stabilno razvrščanje. Isti pogoji veljajo za `total_matching` in rezultate. Prostorsko/časovno območje druge zbirke ne sme uiti v seznam.
- Obdrži se omejeno nalaganje največ horizont + 1 dnevnih sveč na izbrani zapis, zgornja meja 1000 in vidna oznaka krajšanja. Ne nalagati vse zgodovine ali celotne baze v Python/odjemalca za iskanje članov. Dodaten JOIN za stanje pregleda teze mora biti omejen in brez N+1 zahtev.
- Signalni filtri moči/statusa ne smejo izločiti analiz. Pri obsegu signal + analiza mora UI povedati, da ta filtra veljata samo za signale. Osebna članstva niso odvisna od trenutnega inbox statusa.
- Izračun uporablja samo vrnjene/oddane parametre; spreminjanje osnutka obrazca ne preimenuje že prikazanega rezultata. Za zanesljiv Reload je treba ločeno opredeliti trajnost študije: danes `BacktestPanel` hrani stanje samo v pomnilniku. Možnost B zahteva trajnost članstva, ne samodejno arhiva vseh izračunov.

### Predlogi pregleda teze in nedoločene smeri

`finalize_review` lahko objavi signal `thesis_break`, `down`, `new` hkrati s predlogom spremembe trditve, ki je še `pending`. Preverjen uradni dokaz za dovoljenost signala **ni** enak uporabnikovi potrditvi zloma teze. Potrditev predloga spremeni trditev in `proposal.state`; ne nastavi samodejno `Signal.status=accepted`. Zavržen predlog lahko signal prestavi v `dismissed`. Zato statusa signal/claim-review nista zamenljiva.

Predlagano ravnanje: tak signal je mogoče dodati, vendar z jasno oznako **Čaka na tvoj pregled** in povezavo na točno tezo/predlog. Njegov smerni cenovni izid je izid **opozorila za pregled**, ne izid potrjenega zloma teze. Prikazati ga v ločeni skupini, izključeni iz privzetega povzetka potrjenih mnenj; uporabnik jo lahko izrecno vključi. Stanje ob dodajanju in poznejša odločitev ostaneta vidna. Zavržen, potrjen ali zastarel predlog ne izgine za nazaj in ne spremeni izvornega časa razpoložljivosti. Novo »merjenje od potrditve« bi potrebovalo svoj eksplicitni čas in pogodbo.

Za cenovne izide se obdrži stroga preslikava ADR-0022: Buy/Overweight → dolga smer, Sell/Underweight → kratka smer, Hold/neznano → preskok. Kratka smer v študiji pomeni matematični izid padca cene, ne dokaz izvedljive kratke prodaje ali priporočilo za novo kratko pozicijo. Padec po opozorilu prav tako ni dejanski dobiček uporabnika, ki je zmanjšal obstoječo pozicijo. Manjkajoča zgodovina, neveljavne cene in nevtralnost imajo ločene razloge, ne ničelnega donosa.

### Meje stranskih učinkov in primerjav

- Dodaj/odstrani/oglej izid ne kliče LLM, ne ustvarja novega predloga, analize, signala, watchlista članstva, obvestila, opravila ali naročila. Obstoječemu mnenju spremeni samo evidenco zbirke; nova lastna ideja zapiše še lastno entiteto/različico, ki je izrecen namen obrazca. Izračun je determinističen read-only.
- Osebni izbor ni nepristranska validacija modela: mnenje je mogoče dodati po znanem izidu, arhivirati slab izid ali izbrati več sorodnih zapisov. Vedno pokaži čas dodajanja, arhiv ter oznako **Osebni izbor, tudi naknadno dodana mnenja**. Delež naknadno dodanih glede na vstop/izstop izbrane metode izračuna strežnik, če ga UI prikazuje kot številko.
- Osebni izbor in njegove arhivske izbire ne spreminjajo `SignalOutcome`, globalne kalibracije ali predlogov uteži. Globalni pregled ohrani svoje trenutno določene kohorte; sprememba metode potrebuje ločeno odločitev. »Tvoji predlogi« v obstoječi kodi pomeni izvor `manual`/`proposal_id`, **ne** Moje spremljanje.
- Povprečje odstotnih izidov ni sestavljeni donos, donos od dejanske naložbe, dobiček v EUR ali rezultat portfeljske strategije. Obstoječe omejitve cen, sej, korporativnih dejanj, FX in izvedbe iz ADR-0022 ostanejo v pomoči in pri metodi.

## 5. Pomoč in zgoščeni metapodatki v tem toku

Skupna rešitev pomoči po vseh straneh je predmet povezane raziskave. Za Uspešnost mora pomoč odgovoriti na: »Kaj tukaj spremljam?«, »Kako dodam mnenje?«, »Od katerega trenutka se meri?«, »Zakaj zapis čaka ali je preskočen?« in »Zakaj se številka razlikuje od Vsi signali?«.

Ob običajni vrstici zadostuje tip/izvor, čas mnenja, čas dodajanja ter kratko stanje merjenja. Podrobnosti cen, UTC meje, izvora sveč, stroškov, metode in omejitev se odprejo na zahtevo. Kadar manjka valuta, čas ali podatek o potrditvi, mora biti vidna vrzel, ne domnevna vrednost. Zgoščevanje ne sme odstraniti razlike med časom končnega mnenja, časom podatkovnega posnetka, trenutnim tržnim podatkom in dodajanjem v zbirko.

## 6. Minimalna merila sprejema poznejše izvedbe

| Scenarij | Pričakovani rezultat |
|---|---|
| Dodaj isti signal na Signali, nato v Peek iz Radarja; dvojni klik, izgubljen odgovor in dva zavihka. | Eno aktivno članstvo, isti izvorni ključ in prvi čas dodajanja; zanesljiv ponovni GET/ponovitev, razumljivo stanje napake. |
| Signal in analiza imata enak UUID; dve analizi istega instrumenta imata različna ID. | Prvi par ostane dva različna predmeta; nova analiza ne prepiše stare. Izračun/odpiranje zadene pravi izvor. |
| Iskani predmet je šele za prvimi 1000 globalnimi kandidati. | Posamezni ogled in osebna zbirka ga še vedno vključita, ker je izbor v SQL pred omejitvijo; `total_matching` ustreza obsegu. |
| Dodan signal pozneje preide new → watching → accepted → expired. | Članstvo ostane isto; snapshot začetnega mnenja in trenutni status sta ločena; ni spremembe datuma začetka. |
| Poskus dodajanja running/failed analize, neobstoječega ID ali tujega območja zbirke. | Jasna napaka brez delnega članstva; ni »zadnje uspešne« zamenjave. |
| Hold/neznana smer, brez vstopne cene, premalo sej, neveljavna cena. | Vrstica ostane vidna z ustreznim razlogom, ne šteje med izmerjene in ni ničelni izid. |
| Pozno dodan stari signal in arhiviranje slabega izida. | Izvorni `available_at` ostane, `saved_at` in arhivska sled sta vidna; osebni izbor ni prikazan kot nepristranski rezultat. |
| Ob končanem pregledu nastane thesis_break s pending predlogom; uporabnik ga pozneje potrdi/zavrne. | Oznaka in povezava pregleda, ločena skupina, ohranjen prvotni posnetek; signalni accepted se ne uporablja kot dokaz potrditve trditve. |
| Izračun iste zbirke po dopolnitvi/popravku sveč. | Novi `as_of` in uporabljene cene/viri so razvidni; sistem ne trdi, da je posnetek mnenja nespremenljiv cenovni arhiv. |
| Uporabnik spremeni osnutek filtrov po izračunu. | Rezultati ostanejo označeni z dejansko oddanimi parametri do novega izračuna. |
| Dodajanje/ogled/arhiviranje in izračun. | Nobenih LLM/ponudniških/notify/broker klicev, nobene spremembe globalnih izidov, statusa signala, watchliste ali teze; preverjeno s fake varovali in DB regresijami. |
| Odpiranje signala in analize iz izida, nato Zapri/Escape/Nazaj. | Ohranitev zbirke, filtrov, izračuna in fokusa; analiza ostane točni run. Ohranijo se že dokazani navigacijski scenariji S-023. |
| SL/EN, telefon, tipkovnica in 200-% povečava. | Jasno razlikovanje Spremljaj / Dodaj v spremljanje, razumljiva prazna stanja, dostopno shranjevanje in pomoč, brez prekritih bistvenih dejanj. |
| Nova lastna ideja brez predloga/analize; ponovljena aktivacija po izgubljenem odgovoru. | Ena lastna aktivna različica in eno članstvo, brez `AnalysisRun`/`Signal`, brez LLM/ponudniškega/notify/broker klica; delna napaka se atomarno razveljavi. |
| Dvoumen tiker, neznana kotacija/valuta ali več trgov. | Osnutek se lahko ohrani; aktivacija zahteva razrešitev in ne izbere prvega zadetka/USD. Posnetek in poznejši izračun se sklicujeta na isti instrument. |
| Osnutek je nastal prejšnji mesec, danes je aktiviran; odjemalec pošlje stari začetni datum. | Merljivi `available_at` je današnji čas strežnika, ne čas osnutka ali odjemalca. Pretekli datum se ne uporabi za vnaprejšnjo napoved. |
| Urejanje cilja/smeri/roka že aktivne ideje po znanem izidu. | Neposredno prepisovanje ni dovoljeno; nastane nov osnutek in ob aktivaciji nova povezana različica s svojim časom. Stare vrednosti in rezultat ostanejo. |
| Kratka proti večletni ideji in sprememba nameravanega obdobja v osnutku. | Relevantni parametri so odvisni od obdobja; nezdružljiva merila zahtevajo ponovni pregled. 20-sejni cenovni izid ne zaključi večletne teze. Nepodprta dolga metoda je vidna vrzel. |
| Nevtralna lastna ideja z vsebinskim merilom; rast cene brez dokaza poslovne trditve. | Smerni izid je preskočen, vsebinsko merilo pa ločeno čaka na dokaz/ročni pregled; rast ne potrdi trditve. |
| Aktivacija z manjkajočo/zastarelo ceno ali poznejša dopolnitev podatkov. | Brez izmišljene začetne cene; vir/čas/vrzel in poznejši izračun so ločeni. Vnesena uporabnikova ciljna cena ni predstavljena kot tržno dejstvo. |
| Morebitna poznejša retrospektivna simulacija in več zaporednih različic ideje. | Simulacija ostane posebej označena in izločena iz vnaprejšnje natančnosti/globalnih statistik; različice iste ideje niso navidezno neodvisni uspehi. |

## 7. Prejeti odgovor in preostale meje SPEC

Uporabnik je odgovoril: v sedanjem krogu morajo biti tudi **lastne ideje brez predhodne analize**, z **več parametri, ki so odvisni od nameravanega obdobja naložbe**. Možnost C je zato priporočena zasnova in del zahtevanega plana. Samo možnost B ne bi izpolnila odgovora. Lastne ideje od aktivacije dalje so obvezni obseg; poljubna retrospektivna simulacija ostaja opcijska in ločena.

Odprta konstrukcijska naloga povezanega SPEC je konkretno določiti razrede meril, njihovo časovno pogojenost, preverljive podatkovne vire, ravnanje brez podatkov in meje cenovnih metod. Uporabnikov odgovor sam po sebi ne potrjuje določenega seznama metrik, cenovnih pragov, obrazca ali avtomatskih pregledov. Predlog tukaj loči nespremenljivo napoved od osnutka in cenovni izid od izpolnitve vsebinskih meril; podrobnosti sodijo v povezani SPEC tez, odvisen od horizonta.

Za obstoječe signale/analize je tukaj predlagano merjenje prvotnega mnenja od `available_at`, ob ločenem `saved_at`. Če bi želeli še »meriti mojo izbiro od dodajanja«, bi to bila druga izrecna metoda. Pri lastni ideji je začetek meritve trenutek aktivacije njene konkretne različice. Imena tabel, URL-ji in videz gumbov so izvedbene izbire, ne vprašanja za uporabnika.

## 8. Preverljive oporne točke v izvorni kodi

Navedene vrstice so iz osnove `6a9f07c`, prebrane 2026-10-30. Relativne povezave so namenjene repozitoriju; vrstice so dodane v besedilu za pregled.

| Ugotovitev | Vir |
|---|---|
| Pomen študije in omejitve | [ADR-0022](../adr/ADR-0022-testiranje-shranjenih-mnenj.md), odločitev. |
| Oba pregleda zaporedno, ločeno stanje filtrov | [TrackRecord.tsx](../../apps/web/components/track-record/TrackRecord.tsx), vrstice 299–317 in 392–402. |
| Lokalno stanje in ročna oddaja študije | [BacktestPanel.tsx](../../apps/web/components/track-record/BacktestPanel.tsx), 17–24, 44–54 in 184 dalje; tipizirana navigacija 239–263. |
| Obstoječi request nima izbire konkretnega predmeta | [domain/backtest.py](../../services/api/preza/domain/backtest.py), 12–20; rezultat 49–69. |
| Razpoložljivost, omejitve in bounded SQL | [services/backtest.py](../../services/api/preza/services/backtest.py), 29–64, 69–115, 142–159 in 190 dalje. |
| Globalna kohorta in izidi samo iz SignalOutcome | [services/track_record.py](../../services/api/preza/services/track_record.py), 20–49 in 72–101. |
| Pomen »tvoji predlogi«, malo podatkov, imenovalci | [domain/track_record.py](../../services/api/preza/domain/track_record.py), 19, 98–100 in 149–150. |
| Razlika začetne sveče in neutral pri stari metodi | [domain/outcome.py](../../services/api/preza/domain/outcome.py), 66–85; [services/outcomes.py](../../services/api/preza/services/outcomes.py), 37–65. |
| Spremljaj in Sprejmi dejansko pišeta status | [SignalsInbox.tsx](../../apps/web/components/signals/SignalsInbox.tsx), 31–36 in 92–109; [routes/signals.py](../../services/api/preza/routes/signals.py), 79–91. |
| Predlogi imajo povezave na konkreten signal/analize | [ProposalList.tsx](../../apps/web/components/proposals/ProposalList.tsx), 54–60 in 70–77. |
| Zagon analize in prikaz ocen | [AnalysisView.tsx](../../apps/web/components/analysis/AnalysisView.tsx), 84–115; [DecisionHeader.tsx](../../apps/web/components/analysis/DecisionHeader.tsx), 118–119. Študija bere `AnalysisRun.rating`, glava daje prednost `card.rating`; pred izvedbo potrditi skladnost obeh, ne sklepati iz barve kartice. |
| Zadnja uspešna analiza je način seznama, ne identiteta članstva | [routes/analyses.py](../../services/api/preza/routes/analyses.py), 129–178. |
| Pregled teze objavi signal pred uporabnikovo odločitvijo | [services/thesis_reviews.py](../../services/api/preza/services/thesis_reviews.py), 87–88, 336–441; potrditev 475–525, zavrnitev 529–547; [models.py](../../services/api/preza/models.py), 597–625. |
| Trenutna regresijska osnova, brez novega zagona | [test_backtest_feedback.py](../../services/api/tests/test_backtest_feedback.py), testi od vrstic 26, 40, 59, 81, 106 in 208; [BacktestPanel.test.tsx](../../apps/web/components/track-record/BacktestPanel.test.tsx), test pri 73; [backtest-navigation.spec.ts](../../apps/web/e2e/backtest-navigation.spec.ts). |

Raziskava predlaga smer C in pogoje za SPEC skladno s prejetim odgovorom o lastnih idejah. Uporabniška zahteva po tem obsegu še ne pomeni potrditve vsakega predlaganega podatkovnega pravila ali odobritve implementacije, spremembe ADR ali objave aplikacije.
