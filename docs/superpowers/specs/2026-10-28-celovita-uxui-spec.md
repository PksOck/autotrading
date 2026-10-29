# SPEC v0.1: celovita UX/UI nadgradnja Preže

**Status:** osnutek za pregled, brez implementacije. **Datum:** 2026-10-28, dopolnjeno 2026-10-29. **Naloga:** BL-189.

**Izhodišče:** [Opusov posodobljeni načrt](../plans/2026-10-28-celovita-uxui-nadgradnja.md), commit `28f2990`, SHA256 datoteke `030CD7F3293E558FD21ADCBEB9750B00A58384CB9E117F5DDC638CDF259B32BF`. Kopija v tem delovnem drevesu je bajtno enaka izvirniku v Claudovi veji. Koda delovnega drevesa ostaja pri `1855eb8`; razlika novejšega commita je dokumentacija. Opusovih komentarjev ne obravnavamo kot dokaz uspešne implementacije ali aktualnih živih podatkov.

**Povezani dokumenti:** [pregled komentarjev](./2026-10-28-opus-komentarji.md), [podrobni SPEC prvega vala](./2026-10-28-val-minus-1-spec.md), [Astra pregled](../../research/2026-10-28-astra-ux-review.md), DESIGN.md, VOICE.md in ADR-0004/0006/0013/0014/0016. Stare BL-161–171 oznake iz začetnih osnutkov se ne uporabljajo.

## 1. Namen, rezultat in meje

Uporabnik lahko v istem delovnem prostoru primerja delnice in ETF-je, razume stanje analiz, pride do pravih dokazov, pregleduje svoje pozicije in dividende ter omeji obremenitev procesov. Gostota prikaza je nastavljiva; pomen številk in opozoril ostane enak.

SPEC določa pogodbe vedenja, odvisnosti, podatkovne meje in preverljive pogoje. Ne pomeni vklopa avtomatike, oddaje naročil, menjave LLM toka, nadgradnje M6/M7 ali ponovne gradnje že delujočih Tez/Uspešnosti/horizontov analiz/Flex uvoza.

Prva izvedba sta ločena FIX-A in FIX-B, ne splošna prenova. UX-00 je dokazna raziskava, UX-01 je zagon in dopolnitev obstoječega izoliranega demo sklada. Nadaljnje sklope sprostimo po njihovih podatkovnih in oblikovnih pogojih; uporabnikove že potrjene zahteve se ne odpirajo ponovno.

## 2. Potrjene usmeritve in predlogi

Iz uporabnikovega naročila in Opusovega zapisa prevzamemo: prednost dveh signalnih popravkov; izbirni stolpci v Pozicijah in Watchlisti; preverjanje virov pred metrikami; Flex kot evidenco prejetih dividend in accrualov; ločene deterministične ocene prihodnjega denarnega toka.

Predlagane izvedbene odločitve tega SPEC: dodajna polja API, URL kot vir deljivega stanja, lokalne preference videza, lokalni čas + IANA zona za ponavljanje urnika, kvota v eni transakciji, ločene evidence dividendnih dogodkov in ocen. Dokončno arhitekturno sprejetje je v predlaganih ADR-0017–0020; številke se pred zapisom preverijo. Opus je avtorstvo ADR dodelil Astri v ločeni seji, zato tukaj ne nastanejo podvojeni ADR ali navidezno sprejete odločitve.

| Vrata | Kaj mora biti zaključeno | Kaj sme slediti |
|---|---|---|
| G-FIX | Prebran podrobni SPEC in potrjena regresija | FIX-A/B samostojno, brez čakanja na demo/DataMeta |
| G-DATA | UX-00 poročilo z vzorci in pokritostjo | Izbor privzetih metrik Pozicij/Watchliste |
| G-META | ADR-0017 in fixture stanj | UX-02/11a in postopno dodajanje metapodatkov |
| G-TABLE | ADR-0018 in pregled treh reprezentativnih postavitev | Skupna tabela ter širjenje na module |
| G-AUTO | Arhitekturni pregled, ADR-0019, kvota/claim/recovery testi | Scheduler in paketne analize, ob dostavi izklopljeni |
| G-DIV | Vzorec razširjenega Flex, ADR-0020 in pogodba idempotence | Uvoz denarnih dogodkov/accrualov in dividendni UI |

## 3. Skupna pogodba podatkov in napak

### 3.1 DataMeta ni stanje React komponente

Predlagani `DataMeta` vsebuje:

| Polje | Tip in pomen |
|---|---|
| `source` | `str | null`; neposredni vir vrednosti, ne ime zaslona |
| `as_of` | timezone-aware UTC trenutek ali null; trenutek opazovanja, kadar ga vir daje |
| `market_date` | datum seje/računovodski datum ali null; datum ni izmišljen čas ob polnoči |
| `fetched_at` | timezone-aware UTC trenutek pridobitve ali null |
| `availability` | `available | missing | not_applicable | partial` |
| `reason_code` | stabilna koda ali null: `not_configured`, `never_run`, `source_unavailable`, `no_observation`, `identity_unresolved`, `unsupported_instrument`, `incomplete_history`, `missing_fx`, `missing_tax`, `partial_import`, `stale_observation` |
| `stale` | bool; politika svežine se uporablja glede na vrsto podatka, ne univerzalni timeout |
| `basis` | izračunska osnova/obdobje ali null |
| `coverage` | objekt z `included_count`, `expected_count` in `excluded_reasons`, kadar so štetja znana |

Frontend posebej predstavlja `loading`, `refreshing`, `error`, `ready` ter empty rezultat. Transportna napaka ne prepiše zadnjega uspešnega DataMeta in ne postane `missing`. Zastarelost lahko soobstaja z delno pokritostjo; zato ni izključujoča vrednost `availability`.

Novi metapodatki so opcijski dodatek obstoječemu odzivu, brez preimenovanja/odstranjevanja starih polj. Naknadno dodana enotna ovojnica ne spremeni vseh list endpointov iz array v object v enem koraku. Pri paginiranih novih odzivih ima odjemalec ločeno novo pot/pogodbo; obstoječe poti ostanejo združljive do načrtovanega prehoda.

### 3.2 Številke in enote

Denarni izračuni uporabljajo `Decimal` in `numeric`. Nova denarna polja imajo decimalni niz in valuto. Obstoječi `Num` trenutno serializira Decimal v JSON number; SPEC ne skriva tega dolga in ne zahteva nenapovedane spremembe vseh starih odjemalcev. Nove pogodbe ne širijo uporabe `float` za obračune; načrtovan prehod starih polj se obravnava ločeno z generiranimi tipi.

`0` je prava ničelna vrednost; `null` je neznano, brez podatka ali neuporabno z razlogom. Neznana valuta ni USD. Vrednosti različnih valut se ne seštejejo/razvrščajo kot iste enote brez dokazljive pretvorbe. Cena ima datum seje, fundament svojo osnovo, analiza svoj zamrznjeni posnetek in današnji blok svojo svežino.

### 3.3 Napake in dejanja

Novi `OperationError` uporablja `code`, `retryable`, `correlation_id`, opcijski `field_errors`. Uporabniško besedilo je prevedeno iz code; odgovor ne vsebuje ključev, neobdelanega ponudniškega telesa, URL s tokenom ali osebnega Flex XML. Obstoječe error kode, npr. `output_truncated` in `schema_validation_failed`, se ohranijo.

Mutacija loči oddano v vrsto, v teku, uspešno in neuspešno. Pending velja za konkreten predmet. Razveljavitev obnovi isti zapis in zgodovinsko osnovo; novejša sočasna sprememba povzroči viden konflikt, ne tihega prepisovanja. »Pregledano« je za Watchlisto že obstoječa oznaka, za Signal pa se ne uvaja kot nov poslovni status brez ločene odločitve.

## 4. Identiteta, povezave in zgodovina

Interni `instrument_id` identificira kotacijo. Simbol je oznaka in ostane združljiv v starih URL; ob več zadetkih prikažemo borzo/valuto ali eksplicitno dvoumnost. Minimalni UX-11a uvede pogodbo identitete pred novimi tabelami; ni odvisen od prihodnjih raziskovalnih panelov UX-11b.

Signal po ID pridobimo neodvisno od statusnega filtra, prve strani ali trenutnega nabora. Isto načelo velja za Radar event ID in izbrani Entry instrument. Odsoten predmet pokaže not-found z vrnitvijo, nikoli prvega drugega predmeta. Napačen/poškodovan ID pokaže validacijsko stanje; ne sproži neomejenih ponovitev.

`peek=signal:<uuid>` ostane podprt zaradi že poslanih povezav. Pri branju predogleda ne spremenimo statusa. Podrobnosti na telefonu so dosegljive takoj, z enim jasnim zapiranjem in pravilnim fokusom. Nazaj pri normalnem odprtju vrne prejšnje stanje; pri neposrednem zunanjem vstopu zapiranje odstrani samo `peek`, ne pošlje uporabnika iz aplikacije.

## 5. Skupni prikaz tabel

`TableViewPreferencesV1`: `version`, `columns`, `column_order`, `column_widths`, `pinned_columns`, `density: comfortable|compact`. Lokalni ključ: `preza.view.<module>.v1`. Posamezna tabela ima svoj allowlist stolpcev, prevodov, enot, formatov, dostopnosti in sortiranja. Neznane shranjene stolpce ignoriramo, obvezne vrnemo, pokvarjen JSON ponastavimo. Lokalna shramba se bere po hidraciji; začetni SSR se ne razlikuje od prvega client renderja.

Filtri, `sort`, `direction`, stran/cursor in izbrani ID so v URL; niso podvojeni v localStorage. Ob spremembi filtrov se resetira pagination. Sort je strežniški nad celotnim naborom, z determinističnim tie-break ID. `null` je na koncu obeh smeri; sort po valutnem znesku zahteva isto valuto/osnovo ali jasno grupiranje. Query key vsebuje vse parametre API.

Obvezni ostanejo simbol/identiteta, dejanja in značke govorica/neuspeh/zastarelo/delno, tudi če uporabnik skrije povezan stolpec. Ponastavi pogled vpliva le na izbrani modul. Preference veljajo za ta brskalnik; sinhronizacije med napravami v prvi izdaji ne obljubljamo.

Namizni gumbi so lahko 28–32 px; dotikalni cilji ohranijo 48 px po ADR-0013. Kompaktna vrstica ima eno vidno pogosto dejanje in meni. Udobna ali razširjena vrstica lahko pokaže manjše navpične gumbe. Ne obljubljamo treh navpičnih gumbov znotraj 32 px vrstice. Premik stolpcev deluje tudi s tipkovnico/gumbi.

## 6. Podatkovna izvedljivost: Pozicije in Watchlista

UX-00 pripravi isto matriko za oba pogleda. Metrika vsebuje stabilen ključ, vir/endpoint/polje, vrsto instrumenta, enoto, periodo, čas, dovoljen dostop, opaženo pokritost in razlog vrzeli. Možna stanja: `supported`, `partial`, `not_observed`, `unsupported`, `entitlement_required`, `unverified`. Odsoten podatek pri enem instrumentu ni dokaz plačljivosti endpointa.

V Opusovem načrtu je časovni posnetek »1 od 46« in en zapis tipa unknown. V tem SPEC to ni ponovno potrjena trenutna statistika. Najprej se z read-only poizvedbami ugotovi cilje, zadnji tek, napake in metapodatke; ne kliče se celotnega ponudniškega univerzuma ter ne spreminja produkcijske watchliste samo zaradi raziskave.

Pregled kode potrjuje: tedenski `fundamentals()` prebere held/watched simbole; ETF refresh preskoči; kliče `/stock/metric` z `metric=all`; trenutno shranjuje P/E TTM in več kazalnikov kakovosti ter dividendni donos/payout. Razlog nizke pokritosti ni dokazan samo s to potjo. Polj forward P/E in denarne dividende ne predpostavimo.

Ponudniška vrednost dobi `source_field`, osnovo in periodo ob ingestu. Trenutni fallback med indiciranim in TTM dividendnim donosom ter med TTM/Annual payout mora ohraniti izbrano polje. Datum pridobitve ni dokaz fiskalnega datuma. Vrednost z neznano osnovo ne postane pravilno poimenovan stolpec z ugibanjem.

Predlog osnovnega profila: instrument, cena/valuta, dnevna sprememba, od dodaje za Watchlisto oziroma količina/vrednost/teža za Pozicije. Profil Vrednotenje/Dividende se sprosti glede na UX-00 matriko. Redke potrjene metrike so lahko opcijske z vrzelmi; privzeto ne zapolnimo večine zaslona z nepojasnjenimi prazninami.

## 7. Specifikacija modulov in sledljivost

| Zahteva | UI vedenje | Pogodba/odvisnost | Prevzem |
|---|---|---|---|
| SCR-01 Pregled | Kaj zahteva pozornost, resnične novosti, skriti nedelujoči moduli z razlogom | isti signalni nabor/časovni obseg kot nabiralnik; brez samodejnega sample fallback | API izpad ne pokaže vzorčnega premoženja ali signalov |
| SCR-02 Radar | kratek seznam, datum/vir/potrditev, filtri, dosegljiv telefon detail | event po ID, potrditev ima uradni dokaz; not-rumor ni verified | izbrani skriti event se odpre ali not-found, nikoli napačen |
| SCR-03 Vstopi | cena/valuta, razdalja do cone, razlog in neodvisno stanje teze; prilagodljiv graf | identiteta/market date, null thesis ≠ true | neznan vzrok ne avtomatsko potrdi teze; lestvica ima enote |
| SCR-04 Signali | vsa stanja vključno expired, filtri in dokaz, varna dejanja | FIX-A/B; obstoječ rumor guard | filtered new nikoli expired; sprejem ne odda naročila |
| SCR-05 Instrument | polna identiteta, smiselno poimenovana dejanja, paneli delnica/ETF | UX-11a nato 11b; ista dejstva kot preview | neznana valuta brez znaka USD; datum cen skladen z grafom |
| SCR-06 Analize | obstoječi horizonti, filter zadnje uspešne, snapshot/current ločeno | status filter → particija instrument → sort → limit; stable ID | starejši uspešen rezultat viden tudi za novejšim neuspelim, >100 zapisov |
| SCR-07 Opcije | jasno še neizvedeno, razumljiv obseg | M6/M7 ostaneta izven te izvedbe | brez navideznega izračuna ali gumbov naročil |
| SCR-08 Pozicije | račun/konsolidirano, FX pokritost, frakcije, izbirni stolpci | zadnji uspešni celotni snapshot po računu, tudi prazen; objava kontrole uvoza | dva računa s starejšim snapshotom, prodaja vseh pozicij, več valut |
| SCR-08 Watchlista | podatkovni profili, gostota, kratka dejanja, ohranjen undo | UX-00/04/11a; možnost podatkov ni isti kot podatkovni dogodek | undo ohrani added_at/price/tags/alerts; metrike imajo osnovo |
| SCR-08 Analize | sveža/nepokrita pozicija, preview paketa, status avtomatike | batch policy/kvota; aktualne pozicije po računu | cap in že aktivni simbol pojasnjena pred in po zagonu |
| SCR-08 Dividende | prejeto, accrual in 12m ocena ločeno | §9; razširjeni Flex in ADR-0020 | storno/davek/FX vrzeli in akumulacijski sklad brez lažne gotovine |
| SCR-09 Teze | aktivna različica in čakajoče spremembe najprej, zgodovina postopno | ohrani version guard, dokaze in potrditev | konflikt ne izgubi osnutka, 100 pregledov ne naloži vsega na vrh |
| SCR-10 Uspešnost | izbrana kohorta/horizont, vzorec, drilldown in sekundarna kalibracija | kohorta po nastanku signala; kalibracija ima lastno prikazano osnovo | seštevek drilldown reproducira n in merilo; error ≠ default uteži |
| SCR-11 Nastavitve | povezave, videz, procesi, avtomatika, vloge, obvestila | API veljavnosti in revision, brez skrivnosti | pending/dirty/conflict/error; ne obljublja neizvedenih social virov |
| SCR-12 Predlogi | hipoteza, hitra presoja in več globokih analiz ločeno, user-safe napaka | strukturiran rezultat/error, idempotency, ohranjen osnutek | neveljaven izhod ne ustvari uspešnega rezultata/signala |
| Lupina/predogled | vidni status tudi na telefonu, kratek »Več«, fokus in Back | FIX-B, obstoječi ADR-0013, safe entity decoding | telefon doseže detail brez skrola skozi ves seznam |

Vse UI besedilo gre v SL/EN messages. Spremembe komponent/tokens/zaslonov ob izvedbi posodobijo DESIGN. Trditve modela ne postanejo numerični podatki. Nakupni signal brez uradne potrditve govorice ostane blokiran na API, ne samo na gumbu.

## 8. Procesi, kvota in ponavljajoči urniki

Predlagana `ProcessPolicy` hrani `id`, `process_key`, `enabled`, `revision`, `timezone` (IANA), `schedule_kind`, `local_time` ali interval, `weekdays`, `window_start/end`, `limits`. UTC se hrani za materializirane termine/izvajanja, ne kot edini podatek ponavljanja. Sicer lokalni čas pri DST zdrsne.

Obstoječi UTC croni se prenesejo kot UTC politike in ne prestavijo tiho. Novi lokalni urnik velja v izbrani coni. Okno je [začetek, konec), pri prehodu čez polnoč pripada dnevu začetka. Neobstoječi lokalni termin se preskoči; ponovljena ura ima en logični tek. Natančen DST izbor se potrdi v ADR-0019 in testira z istimi primeri, ki jih uporablja predogled naslednjih terminov.

`ProcessExecution` ima policy revision, stabilen logični termin, origin, state, job ID, started/finished/heartbeat, reason in števce. Unikaten ključ `(policy_id, scheduled_for)` in atomaren worker claim preprečita dvojni tek; commit in dostava vrsti sta povezana s trajnim outbox/pending zapisom. Redis nedosegljiv ne izgubi ustvarjenega termina. Recovery ponovno dostavi isti ID; ne podvoji še aktivnega opravila. Po izpadu največ en najnovejši zapadli tek, ne navala vseh zamujenih.

Ena transakcijska kvota sprejema ročne, proposal in samodejne analize. Ohranimo UTC dnevno osnovo obstoječega limita in v UI lokalno pokažemo reset. Neuspeh trenutno ne šteje v deep kvoto, zato avtomatika dobi še cap poskusov in neomejene samodejne vsebinske ponovitve niso dovoljene. Aktivna analiza instrumenta prepreči podvojen sprejem.

Globalna pavza ustavi nove avtomatske začetke, ne ubije tekočih. Pred začetkom worker ponovno prebere politiko; queued zunaj okna se odloži brez zasedanja edine worker reže z dolgim sleepom. Ročni »Zaženi zdaj zunaj okna« je izrecen, sledljiv in ne obide kvote/onemogočenega procesa. Nova avtomatika ostane izklopljena do uporabnikove odločitve.

## 9. Flex dividende in projekcija denarnega toka

### 9.1 Vhodi in evidence

Razširjeni izpis predvidi Cash Transactions (dividenda, payment-in-lieu, withholding, popravki/storno), Open/Change in Dividend Accruals in Financial Instrument Information. Točna XML imena in identifikatorje potrdi očiščen vzorec; naslov razdelka UI ni dokaz XML tag-a.

Sedanji parser novih sekcij ne shrani in izvirni uvoz XML se ne arhivira. Uporabnik lahko izpis pripravi že prej, vendar ga zasebno ohrani in po nadgradnji parserja ponovno uvozi. Financial Instrument Information dobavi identifikatorje/borzo; valuta se pridruži iz preverjene sekcije s conid, ne predpostavi kot obvezno polje te sekcije.

Vzorec ne sme vsebovati pravih računov, osebnih opisov ali avtentičnih zneskov; testne vrednosti so nadomeščene s sintetičnimi, ki ohranijo pomen in razmerja. Povsem prazni amount/quantity niso uporaben računski fixture. V repozitorij ne shranjuj originalnega uporabnikovega izpisa.

Modeli so ločeni:

- `DividendCashEvent`: broker/account/event ID, instrument reference, action/reference ID, vrsta, podpisani Decimal amount, valuta, knjižni/settlement datum, source/as_of, opcijski FX in njegova osnova.
- `DividendAccrualSnapshot`: račun, instrument/action ID, ex/pay datum, upravičena količina, grossRate/amount, znani tax/net in valuta, čas snapshot-a/stanje. Ni gotovinska knjižba.
- `ImportCoverage`: račun, vrsta sekcije, obdobje in stanje uvoza. Odsotna sekcija ≠ nič izplačil.

Cash idempotenca uporablja `(broker, account_id, transaction_id)` in preveri neskladno ponovno vsebino. Accruali uporabljajo svoj naravni ključ/action ID in snapshot verzijo; transactionID ne predpostavimo za vse sekcije. Popravek ohrani sled, ne podvoji gotovine. Napoved se ob izplačilu ne sešteje še enkrat s cash dogodkom.

Pretekla izplačila prodanih instrumentov ostanejo v časovni evidenci. Trenutni portfelj določa projekcijo, ne pravice do preteklega denarja. Storno je podpisan dogodek. Nepovezan davek ostane viden kot nerešen, ne pripne se naključni dividendi.

### 9.2 Tri neodvisne številke

**Prejeto:** dejanski dogodki v knjižnem obdobju, bruto in znani povezani odtegljaji/neto. Manjkajoč davek ne pomeni tax=0. Payment-in-lieu je ločeno označen.

**Napovedano:** odprti accruali, v UI »Odprte obračunane dividende«, s statusom, ex-date/pay-date in njihovim poročanim bruto/neto. To ni prejeta gotovina in ni nujno prihodnjih polnih 12 mesecev. Prehod v cash se prikaže sledljivo, ne kot nov prihodek dvakrat. Koda Re v Change Accruals lahko pomeni popravek, preklic ali razveljavitev ob plačilu; brez ujemajoče denarne knjižbe ne dokazuje cash prejema. Razlage preverjene v [uradni referenci IBKR](https://www.ibkrguides.com/reportingreference/reportguide/change%20in%20dividend%20accrualsfq.htm).

**Ocena 12 mesecev:** `current_quantity × annual_distribution_per_share` po instrumentu/valuti. Osnova je indicirana letna distribucija z virom ali veljaven TTM per-share nabor. Osebni prejemek / današnja količina ni dovoljen izračun: količine so se lahko spremenile, uporabnik je lahko zamudil ex-date, obstajajo davki, FX in split-i. TTM per-share iz Flex je dopusten le, če vsak dogodek vsebuje dokazljivo bruto stopnjo ali upravičeno količino ob dogodku in je zgodovina popolna ter usklajena s corporate actions; sicer projekcija manjka z `incomplete_history`. Tudi 12 mesecev osebnega izpisa samo po sebi ne jamči popolne zgodovine izplačil instrumenta.

Ocena je bruto, če ni izrecne znane drugačne osnove. Ne predvidevamo davčne stopnje ali povečanja dividend. Posebne dividende dobijo oznako in vključitev v TTM se navede; niso samodejno ponavljajoče letno izplačilo. Sprememba trenutne količine spremeni oceno, ne preteklih prejemkov/accrual upravičenosti.

Potrjeno akumulacijski razred ETF ima **0 ocenjenega gotovinskega izplačila iz sklada** z razlogom `accumulating_share_class`; to ni trditev o ničelnih dividendah naložb sklada in ne izbriše dejanskih knjižb. Neznana dividendna politika je vrzel, ne 0.

FX v osnovno valuto za prejeto/accruale uporabi ustrezen `fxRateToBase` in njegovo poročano osnovo; odsoten FX povzroči delno vsoto. Stopnje iz stare osebne cash knjižbe ne uporabimo tiho za novo 12m projekcijo. Brez ustreznega današnjega FX ostane projekcija po originalnih valutah. Izračun davčnih obveznosti ni del sistema.

## 10. Sprostitev izvedbe in merila prevzema

| Paket | Vrstni red | Ključni dokaz |
|---|---|---|
| Val −1 | FIX-A/B in UX-00, samostojni | konkretni regresijski scenariji in matrika virov, brez arhitekturnega megaprojekta |
| Val 0 | obstoječi demo UX-01, DataMeta UX-02, identiteta 11a, poti UX-03 | fixtures za vse podatkovne razmere, pravilen objekt/povratek |
| Val 1 | UX-04/05, Watchlista 14, Analize 12, Predlogi 10 | trije pregledani reprezentativni prikazi, nastavljivi stolpci, brez surovih napak |
| Val 2 | UX-06/07/08/09/11b/13/15/16 | povezane poti in pravilna časovna/računska osnova |
| Val 3 | UX-17/18 | shranjene politike, preview obsega, kvota/claim/DST/recovery |
| Val 4 | UX-19/20; dividende po 13 lahko samostojno | razširjen Flex, denarna sled, ločene projekcije, celovit prevzem |

Vsi pomembni zasloni: loading/empty/error/partial/stale/ready in pending/success/error/undo. QA: SL/EN; 390×844, 768×1024, 1440×1000; svetla/temna/sistemska; tipkovnica, 200% zoom, reduced-motion, 48px dotik. Spodnja navigacija ne prekrije dejanj; dolgi seznami ne skrijejo detaila.

API: pytest na namenski izolirani bazi, ruff/format, mypy; migracije po spremembi sheme; OpenAPI in generirani TS. Web: Vitest, i18n, lint/typecheck/build, Playwright naloge z dejanskim dokazom pravilnega ID in obnove stanja. Demo ne sme uporabljati živih volumnov/ključev. Testi ne sprožajo plačljivih analiz ali Telegram sporočil samo za dokaz UI.

**DoD dokumenta:** izvor identificiran in ohranjen, Opusovi komentarji obdelani, meje odločitev navedene, prva faza ima podroben samostojen SPEC, celota ima sledljivost do UX-00–20 ter predlaganih ADR. **DoD implementacije ni dosežen z zapisom SPEC.** Ostajajo dokazna vrata virov, vzorca Flex, arhitekture in prototipov.
