# BL-228: metode uspešnosti in ohranjena zgodovina

## Dokazana razlika

Osnova je T1 commit 3e9bee3. Karakterizacijski testi najprej shranijo dejansko obnašanje brez popravljanja matematike. Pri istem sintetičnem zapisu po zaključku dneva (23. oktober, cene 80 → 100 → 110) stari izračun uporabi prvo svečo na datum signala, študija pa prvo svečo strogo po UTC dnevu razpoložljivosti. Stari up izid je 25 %, nov gross 10 % in po 10 bps na obeh nominalih 9,79 %. Neutral/neznano sta v stari funkciji long, nova študija ju preskoči. Testi zajamejo tudi down, vikend, 20 shranjenih sej in manjkajoči benchmark (null, ne nič). Vse številke tega primera so sintetične fixture in preverjene z Decimal.

## Producenti in obseg

| Pot v sedanji kodi | Kaj je dokazano |
|---|---|
| radar/signals.py upsert_signal | Sentiment v nevtralnem pasu lahko ustvari neutral; dejanski DB test naredi tak signal, consumer zapiše legacy 25 %, študija ga preskoči. |
| proposals/analyze.py ProposalVerdict → Signal | Shema dovoli neutral in producent prenese smer; statični dokaz poti, brez pravega LLM klica. |
| entries/service.py | Navedeni potek izdela up vstop oziroma down zlom teze. |
| services/thesis_reviews.py | Upravičen sprejeti prelom izdela down. |
| cli/seed_demo.py | Zgodovinski vzorci uporabljajo up oziroma down. |

To ni popis živih vrstic. Uporabnikova dejanska zgodovina ni pregledana in obseg vpliva ostaja **neznan**, ne 0. Sedanja koda ne dokazuje metode vsake stare vrstice.

## Izvedena pogodba

[ADR-0025](../adr/ADR-0025-locene-metode-izidov.md) ohrani stari producent in izračune. Globalni TrackRecordOut, TrackOutcomePage ter OutcomeStat vrnejo method_id=legacy-unversioned. To ne pripiše izmišljene v1 zgodovinskim vrsticam. Novi BacktestOut vrne saved-record-after-utc-close-v1, identiteto deterministične metode novega izračuna, ne cenovnega point-in-time posnetka. Sprememba pravil zahteva novo identiteto.

OpenAPI in TypeScript sta ponovno generirana, brez ročnega urejanja. Ponovna generacija obeh da isti SHA256. TypeScript ostane v kanoničnem formatu generatorja (CI preverja njegov nespremenjen izhod); Prettier preverja ročno kodo. Stare API odgovore brez polja UI označi kot odsotno oznako in jim ne izmisli nove verzije.

V Uspešnosti sta ločena naslov in vidno opozorilo; podatki metode so v razkritju ob razdelku. Pojasnilo govori o **sedanjem starem producentu** in izrecno pove, da posamezne metode neoznačene zgodovine ni mogoče potrditi. Tudi glavna SL/EN pomoč vsebuje to omejitev. Izbrani parametri, stroški, preskoki in opozorila ob rezultatu ostanejo vidni.

Ni spremembe matematičnih funkcij, SQL kohort, producentov, source=all, signalnih statusov, sheme baze ali že shranjenih izidov. Ponovni compute_outcomes na sintetičnem zapisu ne zapiše ničesar; datum/izid/computed_at ostanejo enaki. Legacy neutral ni matematično popravljen in tega ne predstavljamo kot novo pravilno smerno napoved.

## Preverjanje

- Novi pogodbeni test RED zaradi manjkajoče oznake, nato GREEN; dodatni DB RED/GREEN za /entries/outcomes. Sedem čistih karakterizacij, ena pogodba in en Postgres producer/no-rewrite test.
- Celotni API **606 passed / 1 pogojni Redis skip / 19 obstoječih opozoril**. Prava, povsem ločena preza_ux_test baza v začasnem kontejnerju; pytest resetira samo to bazo. Nobenih živih modelov, borznih naročil ali sporočil.
- API Ruff čist, format 224 datotek in mypy 135 source files čisti (domain posebej 22).
- Končni celotni web po skupnem popravku pomoči **194 passed / 47 datotek**, z obstoječim testnim timezone opozorilom; TypeScript, celotni ESLint in i18n 1385 uspešni. UI RED/GREEN za identifikatorje in razlago neoznačene zgodovine, fallback starega API odgovora preverjen.
- Neodvisni metodni pregled najde P2 glede preveč določnega besedila; popravljeno v obeh jezikih, regresijski test in ponovni pregled **PASS**. Pregledovalec ne trdi lastnih runtime rezultatov.
- Linux API/web build uspešen. Končni povezani celotni browser **90 passed / 10 namernih device-specific skipov** (100 primerov). Zagon po zadnjem skupnem popravku pokrije tudi resnične nove API oznake in odsotnost spreminjanja izidov. Predhodni ciljni24 je razkril še občasni Escape; [produktni popravek](./2026-10-31-pomoc-escape-popravek.md) je neodvisno pregledan in dodatno 20/20 ponovljen.

## Namestitev in preostalo

Samo demo :3100 dobi novi API/web, brez reseeda ali nove sheme (pred/po 0020). :3000 web/API digesta ostaneta začetna. Končni demo web je db936fb786a7afd6581603f84e3078ba0242a9398d1bdaaccde315f9c65989d1, API b7978aa4883fd9a47c7f78244e7c42b743a02154f13a5fe84dd189585e8ec3eb. :3000 web ostane 4eaf458ee0525197f3800d28ed6d758aaffa70ec23d6bfcf7ddaaff67e06f7c9 in API 973f535ba8840631e0442f59c346c6b3469a17646f5b338703b50fdc9349e194. Začasni testni kontejner 771a88b0 je po koncu odstranjen, oba obstoječa sklada ostaneta zagnana. Brez push/merge.

Naslednja sta T3–T4/BL-225: trajno spremljanje obstoječih mnenj **in lastne ideje brez analize**. Za novi izbor velja verzionirana metoda ADR-0022/0025; legacy all ohrani signale/zaključene analize. Teze, več meril, backup/Flex/SMTP in lastniške vrzeli ostanejo ločeni odprti pogoji.
