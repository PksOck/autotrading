# Končni povezani pregled R1 / BL-221 in BL-204

**Datum:** 2026-10-30. **Verdikt SPEC: PASS. Verdikt kakovosti: PASS. Končna povezana integracija: PASS.** Prvotni P2-1/P2-2 in integracijski P2-3/P2-4 so **ADDRESSED**. Brez novih ugotovitev, ki bi zahtevale spremembo tega paketa.

## Obseg in način

Pregled velja za novi val od osnove `21a0b3d` v izolirani veji `feat/uxui-demo-upgrade`, vključno z R1 (`dcec5d7`), BL-204 in ozkima integracijskima popravkoma Back/fokusa. Merila so izvedbeni plan `docs/superpowers/plans/2026-10-30-radar-trajna-oddaja.md`, SG-09–11 in F-G06–09. Pregledan je celotni začetni `final-review.diff` (127.702 bajtov; tracked diff in priložene nove datoteke), dejanski helper, composer, prevodi, novi enotski/E2E/API/DB testi ter povezani ADR-0024, DESIGN, S-G1, raziskava in vprašanja. Kasneje so ozko pregledane dodatne spremembe hooka, fokusnega lifecycle, E2E merilne sinhronizacije in starega pričakovanja vrstnega reda simbolov. Obstoječi API sprejem, DTO, transportni hook in Radar model/serializacija so prebrani zaradi preverbe meja.

To je povezani pregled tega novega vala, ne ponovitev starega pregleda celotne funkcionalnosti. Pregledovalec ni ponavljal testov ali spreminjal produktne kode, indeksa, HEAD, baze oziroma storitev. Edini njegov zapis je to poročilo. Testni rezultati so pregledani izvajalčevi/rootovi dejanski dokazi, ne lastni ponovni zagoni.

## Ugotovitve po resnosti

- **Critical:** ni ugotovitev.
- **Important:** ni preostalih ugotovitev; vse štiri P2 so odpravljene.
- **Minor:** ni ugotovitev, ki bi zahtevale spremembo tega paketa. Dodatna neobvezna dodelava ni pogoj PASS.

## Izrecna presoja ugotovitev

| Ugotovitev | Končni verdict | Preverjena odprava in dokaz |
|---|---|---|
| P2-1: A-jeva potrditev izbriše nove trajne podatke B | **ADDRESSED** | `apps/web/lib/proposal-draft.ts:269` primerja vseh sedem aktualno shranjenih polj s pričakovanim posnetkom pod isto writer transakcijo. `apps/web/components/proposals/ProposalComposer.tsx:98,104` označi samo uporabniško urejanje kot dirty; restore/reopen ne postane stale writer. Potrditev na `:234` uporablja pogojno brisanje in varuje tudi lokalna urejanja med čakanjem. Helper test `apps/web/lib/proposal-draft.test.ts:37`, komponentni test `apps/web/components/proposals/ProposalComposer.test.tsx:103` in pravi brskalniški test `apps/web/e2e/proposal-idempotency.spec.ts:173` pokrivajo B-save vseh polj → samo A-ack → A-reopen/cancel → B-reload. Obstajata vedenjski komponentni RED ter dejanski prvotni phone E2E RED; končni primeri uspejo. |
| P2-2: storage napaka po POST lažno zagotavlja, da nič ni bilo poslano | **ADDRESSED** | `apps/web/messages/en.json:415` in `apps/web/messages/sl.json:415` uporabljata nevtralno ustavitev oddajanja ter ohranitev/kopiranje besedila. `apps/web/components/proposals/ProposalComposer.test.tsx:128` najprej uspešno sprejme POST, nato povzroči odpoved zapisa potrditve; preveri isti trajni ID, nevtralni besedili ter poznejšo obnovo z matching GET brez dodatnega POST. |
| P2-3: Back po reload ne zapre obrazca | **ADDRESSED, potrjeno v brskalniku** | `apps/web/lib/useBackToClose.ts:36` izbere novi counter token, ki ga celotni trenutni retained stack ne vsebuje. Prejšnji history entry ga zato nima in Back izvede onClose. Spread celotnega history.state ter kopija prejšnjega stacka ohranita Next state, URL in nested plasti; podpis in preostali close/pop protokol ostaneta. Novi test `apps/web/lib/useBackToClose.test.tsx:10` preveri retained overlay-1/2, callback in ohranjen state/URL. Vedenjski RED **1 failed / 5 passed**, nato GREEN z vsemi šestimi hook primeri; končni dejanski reload/Back E2E uspe. |
| P2-4: zaprtje ne vrne fokusa zunanjemu odpiralniku | **ADDRESSED, potrjeno v brskalniku** | `apps/web/components/proposals/ProposalComposer.tsx:127` shrani dejanski aktivni HTMLElement ob odpiranju zaprtega obrazca; PROPOSE_EVENT med odprtim dialogom ne zamenja odpiralnika. `:281` v Radix close autofocus lifecycle prepreči privzeto pot samo za še povezano tarčo in jo fokusira s preventScroll. Odstranjen odpiralnik ohrani privzeto pot. Test `apps/web/components/proposals/ProposalComposer.test.tsx:63` preveri resnični opener → input → Cancel → opener. Vedenjski RED **1 failed / 12 skipped** (fokus body), nato ciljni GREEN; končni dejanski Back/fokus E2E uspe. |

## Povezane pogodbe in prednosti izvedbe

- **R1 ostane omejen popravek.** `services/api/preza/services/radar_views.py:56` uporabi array presek oziroma komplement unije. Članstvo, starost, status in pozitivni min_score so SQL WHERE pred urejenim LIMIT; vrstni red na `:68` je `score DESC NULLS LAST, last_seen_at DESC, id DESC`. Ni več Python filtriranja omejenega prefiksa. Prazna množica in več simbolov imata pravilno semantiko brez join podvajanja. Podpis, `event_out`, exact-ID pot in izbira zadnjih popolnih pozicij ostanejo ohranjeni.
- **Omejen rezultat ne pomeni konstantne latence.** DB testi preverijo upravičen zadetek za več kot `limit*3` tujimi dogodki v vseh treh pogledih, odstranjeno watchlisto, ničelne/stare pozicije, prazne/mešane/podvojene simbole, filtre, NULL score, stabilne vezi in limit=0. Instrumentacijski test preveri štiri SELECT ter en source query samo za izbrana ID. EXPLAIN poročilo pravilno loči bounded SQL/ORM rezultat od širšega pregleda vrstic v bazi; novega indeksa ali migracije ni.
- **Oddaja je ločena od nadaljnjega urejanja.** `apps/web/lib/proposal-draft.ts:73,223` trajno shrani vseh sedem poslovnih polj z natančno simbolno normalizacijo pred transportom. Zamrznjeni body in request_id se pri ponovnem preverjanju ne ustvarita iz trenutnega obrazca. `ProposalComposer.tsx:206` začne z GET istega ID; samo 404 dovoli isti POST, drugi izidi ostanejo negotovi ali konfliktni. `proposal-draft.ts:286` preveri ID in vsa poslovna polja odgovora.
- **Koordinacija dopolnjuje strežniško idempotenco.** Vsi novi writerji uporabljajo skupni IndexedDB readwrite mehanizem (`proposal-draft.ts:167`), znotraj katerega so localStorage read/modify/write/readback sinhroni. Web Locks so rezervna pot, brez varne koordinacije POST obstane. Kriptografski UUID fallback podpira navadni HTTP brez randomUUID. Pravi two-tab E2E uporablja dejanski IndexedDB z izključenima Web Locks in randomUUID.
- **Varnostno stanje se ne ponastavi ob napaki.** Koruptiran v2 ne povzroči tihega novega ID; v1 obnovi posamezna veljavna polja brez izmišljene prejšnje namere. `setOperationState` (`proposal-draft.ts:239`) ne poslabša že potrjenega sprejema s kasnejšim unknown/conflict zapisom. Novo namero odpre samo ločeno izrecno dejanje po terminalnem stanju. Odpiranje, reload, jezik in urejanje sami ne dispatchajo ničesar.
- **Strežniške meje ostanejo ohranjene.** API sprejem, DTO in vsebinski 409 so nespremenjeni. Novi test `services/api/tests/test_proposal_idempotency_db.py:19` izgubi odgovor po 202, obnovi GET in ponovi isti POST ter preveri en Proposal/AnalysisRun/Signal, eno oddajo analize in en fake modelni klic. Test na `:78` preveri sočasni sprejem istega ID in nespremenjeno prvotno vsebino po 409. To ne predstavlja dokaza prihodnjega lastništva vsake ponovne dostave analize.

## Končni preveritveni dokazi

| Sklop | Dejanski rezultat in meja |
|---|---|
| R1 ciljni DB | **15 passed**, predhodni vedenjski RED; neodvisni task PASS. Ruff/format ter mypy **135 datotek PASS**. |
| EXPLAIN | **50.000** sintetičnih vrstic, rollback; portfolio **9,416 ms**, Discover **33,156 ms**, top-N **48/51 kB**. Ne obljublja iste latence pri poljubnem obsegu. |
| Celotni API | **597 passed / 1 skipped / 19 warnings**. Edini skip je izrecni manjkajoči izolirani TEST_REDIS_URL v obstoječem arq retention testu; ta zagon zato ni nov dokaz dejanskega Redis retention obnašanja. Opozorila so obstoječe deprecations. |
| Povezani ciljni API | **9 passed**, vključno z izgubljenim odgovorom, ponovnim GET/POST, sočasnim sprejemom in konfliktom. Ponudniki/vrste so testni dvojniki. |
| Končni ciljni web | **29 passed**: 23 proposal + 6 hook. Vključuje prvotni dve P2 regresiji, retained history in dejanski focus lifecycle. |
| Celotni web | **180 passed v 44 datotekah**. TypeScript in celotni ESLint exit 0; **1302** enakih SL/EN ključev; Prettier spremenjenih datotek čist. |
| Sveži Linux demo build | **PASS**, posodobljen samo :3100; slika `9e5c78675b5aa9cf7ddeda568e7e9cca300d46d64a03019a611bd1f92de1a82d`. Nobena produktna sprememba po tem viru. |
| Ciljni novi Playwright | **12 passed v 1,3 minute**: osem SL/EN × desktop/phone × accepted/unaccepted lost-response poti ter štirje dejanski IndexedDB/preservation primeri. |
| Končni celotni Playwright | **76 passed / 10 obstoječih namernih device-specific skipov**, exit 0, **3,2 minute**. Vključi vseh 12 novih primerov, ročni predlog, shell ter skupne signal/backtest/Back poti. Preskoki niso nova vrzel tega paketa. |

Dokazi vključujejo tudi neuspešne vmesne zagone: prvi ciljni **8 failed / 4 passed** razkrije Back, drugi isti rezultat razkrije fokus po uspešnem Back. Ozki popravki so nato potrjeni z enotskim RED/GREEN in resničnim brskalnikom. Prvi širši zagon po teh popravkih je imel **75 passed / 10 skipped / 1 failed** zaradi starega vrstnega reda v toast pričakovanju; izolirana ponovitev tega primera je **1 passed**, nato zgornji celotni ponovljeni zagon uspe.

Pregledani sta zadnji dve spremembi samo v testih, obe **PASS**:

- `apps/web/e2e/proposal-idempotency.spec.ts:91` z expect.poll počaka na dejanski boundingBox **height >=48**. Vmesna meritev **47,17 px** je zajela vhodno Motion skalo. Prag ni znižan, tolerance ali sleep ni, poslovne/Back/fokusne trditve ostanejo. To je ustrezna sinhronizacija testa z animacijo.
- `apps/web/e2e/shell.spec.ts:59` pričakuje kanonični toast `AMD, NVDA` namesto vnosnega `NVDA, AMD`; zamrznjeni body in strežnik uporabljata urejeno množico. Izrecna oddaja, vidni uspešni toast in naslednja preverba shranjene hipoteze ostanejo. Dokaz sprejema ni oslabljen.

## Zavestno izven verdicta in izdaje

A3/A5 raziskava in dopolnitev S-G1 sta **predlog naslednje pogodbe**, ne izvedena lease shema, avtoritativna identiteta worker instance ali reprodukcija/odprava A3/A5. Prihodnje sheme, supervisor stop-proof, cancellation/drain, fencing in unknown računovodstvo zahtevajo lasten izvedbeni plan ter dejanske DB/worker dokaze. R1 in BL-204 teh vrzeli ne zapreta.

Dokument vprašanj pravilno beleži **vse tri prejete uporabnikove odgovore**, odvisni pogoji pa ostajajo odprti: razširjenega Flex še ni; backup pot/pogostost želi uporabnik nastavljati v aplikaciji, dovoljen je isti disk, konkretni cilj še ni nastavljen; SMTP predal `preza@zavadlal.com` na predvidenem `sh10.neoserv.si` bo šele ustvarjen. Dokument navaja uradno preverjena vrata 465/TLS, vendar ni bilo preverjanja računa, povezovanja ali dostave. Ta pregled ne potrjuje dejanskih dividend/FX, pravic ali pokritosti ponudnikov, zasebnega XML, izbranega cilja kopij, uspešne obnove ali SMTP dostave. BL-222 backup plan/SPEC je ločen dokumentarni obseg, ne nova izvedena funkcionalnost tega produktnega verdicta. Sintetični dokazi ne ustvarijo finančnih dejstev.

S-024, končni statusi BL-204/221, prenos tega poročila med sledene dokumente in lokalni commiti so rootov zaključni dokumentarni korak. Njihovo nastajanje med pregledom ni napaka produktne kode. Prenos v drugo vejo, merge/push, :3000, živa migracija in SMTP ostanejo pod lastnimi že določenimi vrati; ta PASS dovoljenja zanje ne daje. Lokalna brskalniška trajnost je omejena na ohranjeno shrambo istega izvora in ni varnostna kopija ali sinhronizacija med napravami.