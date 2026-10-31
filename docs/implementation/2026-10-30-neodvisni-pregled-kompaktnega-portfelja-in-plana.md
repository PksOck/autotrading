# Končni povezani pregled: kompaktni portfelj in prihodnji UX

**Pregledovalec:** neodvisni SOL. **Osnova:** `6a9f07c`. **Povezani produktni rez BL-223: PASS. Prihodnji SPEC/plan BL-224–228: PASS. UX-R1/UX-R2: ADDRESSED. Preostalih zahtevanih ugotovitev ni.** Pregled ni ponovni pregled celotne stare veje.

## Ugotovitvi prihodnje pogodbe in ponovni pregled

### UX-R1 · P2 · Ohraniti sedanji obseg legacy študije

Plan `docs/superpowers/plans/2026-10-30-spremljanje-in-pojasnila-ux.md:84–87` hkrati določa privzeti `selection=all` za legacy zahteve in razširitev unije z lastnimi idejami. Sedanji `BacktestRequest.source=all` pa pomeni samo signale in zaključene analize (`domain/backtest.py:13`, `services/backtest.py:95–100`). Raziskava Uspešnosti pri vrstici 91 izrecno zahteva, da se ta obseg ne razširi brez verzije pogodbe. Iz trenutnega plana je mogoče pravilno ohraniti SignalOutcome in hkrati pomotoma razširiti staro študijo z idejami.

**Zahtevano:** v SPEC in T4 določiti, da legacy/default `selection=all` s `source=all` še naprej pomeni signal + analysis; `idea_revision` se v prvem rezu vključi samo z izrecnim mine/single oziroma drugo eksplicitno verzionirano pogodbo. Dodati regresijo: prisotnost aktivnih lastnih idej ne spremeni legacy `total_matching` ali rezultatov.

**ADDRESSED:** ponovno prebrani UXP-08, F-UX06 in T4 zdaj izrecno ohranijo legacy signal+analysis unijo/count/povprečje, ideje omejijo na mine/single in zahtevajo `legacy_all_unchanged_after_saving_ideas`. Izvedbena dvoumnost je odpravljena.

### UX-R2 · P2 · Prenesti ločeni povzetek pending opozoril v izvedbeno pogodbo

Raziskava Uspešnosti pri vrsticah 101 in 129 zahteva ločeno skupino pending `thesis_break`, izključeno iz privzetega povzetka potrjenih mnenj, z izrecno vključitvijo. SPEC UXP-09/F-UX08 in plan T4 trenutno zahtevajo oznako pending, ne pa skupine ali pravila imenovalca. Izvajalec bi tako lahko označil vrstico in jo vseeno brez razlike štel med potrjena mnenja.

**Zahtevano:** prenesti skupino/default izključitev v SPEC/T4 in merilo sprejema. Snapshot stanja ob dodajanju ter kasnejša odločitev ostaneta ločena; `Signal.status=accepted` ni dokaz sprejema predloga. Ohraniti sedanjo globalno SignalOutcome kohorto; sprememba velja za novi osebni povzetek.

**ADDRESSED:** ponovno prebrani UXP-09, F-UX08 in T4 zahtevajo vidno ločeno skupino Mine, izključitev nerešenih/nepreverljivih predlogov iz privzetega imenovalca, izrecno vključitev in razkrit obseg/stanje ob izračunu. Dodani sta regresiji `mine_pending_review_separate_denominator` in `include_pending_is_explicit_and_records_review_state`; legacy metoda ohrani povprečje z jasno oznako prisotnih pending pregledov. Ni več odprte ugotovitve.

## Statični pregled malega produktnega reza

**PASS za pregled izvorne kode, brez nove statične ugotovitve.** Pregledan je diff obeh panelov/MarketContext in njihovih treh testov ter novi density E2E in prilagoditev review-feedback E2E. Sprememba ohrani ID stolpcev, ključe preferenc, URL in finančne podatke; doda notranjo horizontalno postavitev ter izbirni compact prikaz. Dejanski vzorec/razpon, cona in opozorila ostanejo. Vir/čas sta v native razkritju dostopna tudi brez hover. Imena se naravno prelomijo. Ni fiksne višine ali rezanja cele vrstice, novega modela, mutacije ali naročila. Dodatni razmik dejanj watchliste je zmanjšan, 48-px cilji ostanejo.

Prva browser serija root je razkrila preozko določeno merilo telefonske višine, razmik dejanj watchliste in dvoumen summary locator obstoječega testa. Ponovno pregledana zamrznjena koda omeji 130-px merilo na desktop skladno s prvotnim planom, ohrani telefonski preizkus geometrije/provenience/overflow, zmanjša samo razmik med obstoječima 48-px dejanjema in kvalificira obstoječi remove locator na »Dejanja«. Spodnji novi dokaz root potrdi popravljeno stanje.

### Svež dokaz root na končni zamrznjeni kodi

- Celotni spletni testi: **181 passed / 44 datotek**; TypeScript in celotni ESLint exit 0, i18n **1302** ključev. Linux build exit 0.
- Ciljni Playwright: **23 passed / 5 namernih device skipov / 0 failed**, exit 0. Vključuje vse štiri nove density primere Pozicije/Watchlista × desktop/phone, native Enter razkritje provenance, Standardno, add/remove in page overflow.
- Dejanska CUA meritev prvih treh pozicij: **129 px**, pred posegom 217,25 px; graf x=485 je desno od identitete x=269, page overflow ni zaznan. Posnetek `portfolio-compact-s025.png` je rootov dokaz, ne nova slika tega pregledovalca.
- Osvežen je samo :3100, končna slika `80cc2588224579c2256e97838d7fb313c52d15d5e58eb25eb02062414fb56d02`. Root potrjuje nespremenjena oba izvorna digesta :3000.
- Končni celotni Playwright: **80 passed / 10 namernih device skipov / 0 failed**, exit 0, 3,3 minute (root session 36612). Vključuje vse štiri nove density scenarije in predhodne proposal/backtest/skupne navigacijske regresije. Od končnih spletnih testov/builda ni bilo nove produktne spremembe.
- Ti sveži dokazi zaprejo T2 za dejansko zamrznjeno malo spremembo. Ni odprte statične, ciljne ali povezane produktne ugotovitve. Root naknadno ureja S-025, dokazni dokument, DESIGN in statuse BL-223–228; to ni nova produktna izvedba prihodnjega plana.

## Preverjena prihodnja zasnova in omejitve

Po odpravi UX-R1/R2 ni preostale zahtevane spremembe v pregledanih dveh raziskavah, UX SPEC, širšem in ozkem planu. Prihodnja zasnova vključuje izrecna dejanja na izvornih straneh in lastne ideje brez analize; nespremenljive aktivirane različice s strežniškim časom, CAS/FK/check/unique in trajno idempotenco; razliko med ciljem investicije, kadenco pregleda ter 1/5/20/60 sejami; več izbirnih meril s provenienco in primerljivimi osnovami; človeško odločitev in 0 avtomatskih naročil/LLM številk. Prenos metapodatkov v razkritja ohranja vidna opozorila. Več kot 20 trditev ne uvede nove prepovedi aktivacije ali tihega reza; nepodprt samodejni pregled je pojasnjen. A3/A5, Flex/FX, backup/restore ter :3000 ostanejo ločeni odprti pogoji. Ta PASS potrjuje primernost prihodnjega plana, ne izvedbe BL-224–228.

Pregledane so veljavne AGENTS, začetna zadnja seja S-024, PLAN/BACKLOG, ustrezna DESIGN/VOICE/BRAND pravila in README spletne aplikacije, ADR-0012/0022 ter sedanje izvorne pogodbe tez/pregledov/študije. Pregledovalec ni zagnal testov, baze, ponudnikov, OpenCode, modelov ali bral skrivnosti; navedeni novi rezultati so izrecno sveži dokazi root. Produktne kode in skupnih dokumentov pregledovalec ni spreminjal. Svež `git diff --check` je bil exit 0.

PASS za BL-223 velja za opisani majhen UI diff in dokazano matriko demo okolja. Ne potrjuje živega trga, odprave starega in nepovezanega dolga, nespremenljivosti celotne baze ali proizvodne namestitve. Prihodnji dokumentarni PASS ne pomeni, da so zbirka, lastne ideje, skupna pomoč ali strukturirana merila že implementirani; T3/T6 pred izvedbo še zahtevata izrecno določene podatkovne pogodbe/migracije iz plana. Ni dovoljenja za :3000, merge/push, nove modele, sporočila ali naročila.
