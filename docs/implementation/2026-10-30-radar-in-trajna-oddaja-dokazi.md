# S-024 · Radar in trajna oddaja predloga

**Datum:** 2026-10-30. **Veja:** `feat/uxui-demo-upgrade`, osnova `21a0b3d`, končni produktni rez `9c4aebf`. BL-221/R1 in BL-204 sta samostojen zaključen nadaljnji val v pregledni veji in demu :3100, ne zaključek vseh odprtih SPEC. Končni široki brskalniški pregled in neodvisni povezani pregled sta PASS.

## Spremembe in obseg

- **Radar / BL-221, `dcec5d7`:** članstvo portfelja/watchliste/Discover je SQL pogoj pred LIMIT. Več kot `limit*3` bolje ocenjenih drugih dogodkov zato ne skrije upravičenega zadetka. Stabilni vrstni red je score DESC NULLS LAST, last_seen_at DESC, id DESC. Pogodba izhoda, točne ID podrobnosti, vir/čas in serijsko nalaganje dokazov ostanejo.
- **Predlog / BL-204:** lokalni zapis v2 loči urejana polja od zamrznjene namere. Pred POST se preverjeno shranita request_id in vseh sedem poslovnih polj. Izrecno preverjanje po izgubljenem odgovoru uporabi GET istega ID; samo 404 dovoljuje isti POST. Reload ali novo urejanje ne ustvarita nove oddaje. Po potrditvi/konfliktu je za novo namero potrebno ločeno dejanje.
- **Shramba in sočasnost:** skupna IndexedDB readwrite koordinacija, Web Locks kot rezerva in kriptografski UUID tudi na HTTP. Brez varne shrambe se POST ustavi. Poškodovan v2 ni tiho zamenjan z novim ID. Potrditev v zavihku A ne izbriše novejših sedmih urejenih polj zavihka B. Obnova/ponovno odpiranje sama ne sprožita zastarelega autosave.
- **Nazaj/fokus:** ohranjeni history marker po reload ne more trčiti z novim števcem prekrivnega okna. Next stanje/URL in ugnezdene plasti ostanejo. Composer po zapiranju vrne fokus dejanskemu še prisotnemu zunanjemu odpiralcu. Dejanja imajo najmanj 48 px in prevode SL/EN.

Strežniški sprejem je že imel idempotenco in ostane nespremenjen. Nova API testa dokazujeta pogodbo, ne uvajata novega sprejemnega sistema. Ni nove migracije, sheme API, spremembe ponudnika ali pravega modelnega klica. [ADR-0024](../adr/ADR-0024-trajna-namera-predloga.md), [izvedbeni plan](../superpowers/plans/2026-10-30-radar-trajna-oddaja.md).

## Dokazi in preverjanje

| Preverba | Dejanski rezultat in meja |
|---|---|
| Radar RED → GREEN | Pred popravkom 5 failed / 6 passed; nato 15 ciljnih passed. Vsi trije pogledi reproducirajo izgubljen zadetek. SQL instrumentacija: 4 SELECT, source query samo za izbrani 2 ID, nič klicev ponudnika. |
| EXPLAIN, sintetično | 50.000 vrstic v transakciji z rollbackom: portfolio 9,416 ms, Discover 33,156 ms; top-N 48/51 kB. Baza lahko pregleda širši nabor, omejeno je nalaganje rezultata. Brez novega indeksa ali trditve o poljubnem obsegu. |
| Celotni API | **597 passed, 1 skipped, 19 opozoril**. Skip je obstoječi arq retention test brez TEST_REDIS_URL; ta zagon ni nov dokaz Redis poti. Opozorila so obstoječe deprecations. Namenska izolirana DB, brez pravih ponudnikov. |
| Povezana API idempotenca | **9 passed**, vključeno v širši sklop: izguba odgovora po dejanskem 202/commit, GET in ponovitev istega POST, en Proposal/AnalysisRun/Signal, ena oddaja in en fake LLM klic. Sočasna sprejema istega ID samo enkrat; drugo telo 409 in prvotna vsebina ostane. To ne dokazuje še A3/A5 lastništva pri redelivery. |
| Spletne regresije | Začetni komponentni RED potrdi novi UUID/drugo telo po remount. Pregled odkrije izgubo B-jevega osnutka in lažno besedilo po POST; oba popravljena z regresijami. Dodani ločeni RED za history kolizijo ter obnovo fokusa. Končni povezani ciljni sklop **29 passed**, celotni Vitest **180 passed / 44 datotek**. |
| Statične preverbe | API Ruff/format in mypy 135 datotek PASS; TypeScript, celotni ESLint, Prettier spremenjenih spletnih datotek PASS. SL/EN **1302 ključev**; generirani OpenAPI/TS nespremenjeni. |
| Linux demo build | Uspešen po zadnji spremembi produkcijskega vira; nova slika naložena samo na :3100. Poznejša sprememba samo E2E meritve ne potrebuje nove slike. |
| Ciljni Playwright | **12 passed** na svežem demu: SL/EN × desktop/phone × sprejet/nesprejet izgubljen odgovor ter štirje dejanski IndexedDB/two-tab primeri. Vse API poti nadzorovane, nobena prava analiza ali druga mutacija. |
| Celotni Playwright | **76 passed / 10 namernih skipov glede na napravo**, exit 0, 3,2 minute. Skupaj 86 primerov, vključno z novimi 12. |

API testi tečejo v `services/api` z namenskim TEST_DATABASE_URL in obstoječim read-only runtime iz Claudovega checkouta; fixture ponastavlja samo testno bazo. Ponovljivi ukazi: `python -m pytest -p no:cacheprovider --tb=short -q`, ciljno `tests/test_radar_membership_db.py tests/test_api_m2.py` oziroma `tests/test_proposal_idempotency_db.py tests/test_research_contracts.py`. Gesla se ne izpisujejo ali vključujejo v poročilo.

Spletni ukazi iz `apps/web`: `node node_modules/vitest/vitest.mjs run`, `node node_modules/typescript/bin/tsc --noEmit`, `node node_modules/eslint/bin/eslint.js . --max-warnings=0`, `node scripts/check-messages.mjs`, ciljni Prettier. Playwright uporablja izrecni `BASE_URL=http://localhost:3100`, lokalni CHROMIUM_PATH in `node node_modules/@playwright/test/cli.js test --workers=1`.

## Pregledi in popravni krogi

R1 ima neodvisni task PASS. Prvotni pregled BL-204 je zahteval pogojno brisanje aktualnih polj in nevtralno obvestilo o storage napaki po POST; oba sta odpravljena z vedenjskimi regresijami. Povezani pregled je zahteval še dejansko brskalniško potrditev.

Prvi brskalniški zagon: 8 neuspehov Back / 4 uspehi. Po minimalnem popravku hooka: Back uspe, 8 neuspehov obnove fokusa / 4 uspehi. Po popravku fokusa ti pogoji uspejo; neposredna enkratna meritev gumba pa med vhodno animacijo zazna 47,17 px. Test zato uporablja samodejno ponavljanje dejanske meritve do **istega praga 48 px**, brez čakanja za fiksni čas ali znižanja merila. Končni ciljni zagon je 12/12; vsak ozek popravek ima ponovni neodvisni pregled. Prvi široki zagon 75 pass / 10 skip / 1 fail pokaže še staro pričakovanje vrstnega reda simbolov v toastu. Enovrstični test se uskladi s kanonično oddajo `AMD, NVDA`; oddaja in preverba shranjene hipoteze ostaneta. Ciljni ponovni primer uspe, nato celotnih **76 pass / 10 skip**. Končni povezani verdikt je PASS, P2-1–P2-4 ADDRESSED; [poročilo](./2026-10-30-neodvisni-pregled-radarja-in-oddaje.md).

## Okolji in preostalo delo

Demo :3100 ohrani sintetične podatke, ločena DB/Redis, brez agent/notify/model delavcev. Ni ponovnega seeda, nadgradnje sheme ali branja zasebnega Flex/.env. Trenutna demo revizija **0020**.

| Okolje | Dokaz slike |
|---|---|
| :3100 web | `sha256:9e5c78675b5aa9cf7ddeda568e7e9cca300d46d64a03019a611bd1f92de1a82d` |
| demo API | `sha256:c2a6a0055ca57e674c98fbd6b270c0d1562525ffb7212d0c01d85ce1895530d7` |
| :3000 web, nespremenjen | `sha256:4eaf458ee0525197f3800d28ed6d758aaffa70ec23d6bfcf7ddaaff67e06f7c9` |
| :3000 API, nespremenjen | `sha256:973f535ba8840631e0442f59c346c6b3469a17646f5b338703b50fdc9349e194` |

Docker inspect potrdi obe začetni :3000 sliki; ta val ne spreminja živih delavcev, nastavitev ali podatkov. Ni merge/push ali dovoljenja za :3000. Brskalniška shramba velja samo za isti izvor in ni varnostna kopija oziroma sinhronizacija med napravami.

A3/A5 ima samo [read-only raziskavo](./2026-10-30-lastnistvo-raziskava.md), ne izvedene lease sheme ali dokaza konca starega izvajalca. [Prejeti odgovori in preostalo delo](./2026-10-30-odprto-in-vprasanja.md): razširjeni Flex še ni na voljo, SMTP predal šele načrtovan, backup lokacija in pogostost bosta nastavljivi. BL-222 ima nov SPEC/plan, funkcija še ni implementirana. Dejanska obnova ostaja pogoj pred prvo živo migracijo; drugi odprti paketi se s tem valom ne zaprejo.
