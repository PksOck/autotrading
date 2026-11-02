# YTD podatki, kakovost in GitHub predaja

> Execute inline; root implements; one independent final review.

**Goal:** Številčni YTD iz koherentnega prilagojenega zajema, pregledna zastarelost in preverjen GitHub master za testiranje.
**Architecture:** aditivna SQLAlchemy/Alembic snapshot tabela + provider/router capability, obstoječi worker cen, Decimal YTD/read metadata, sintetičen demo. Native details za kakovost.
**Spec:** ../specs/2026-11-02-ytd-podatki-in-predaja-spec.md

## Constraints
3000/tuji master checkout ostaneta. Brez resničnih modelnih klicev, sporočil ali naročil. SL/EN,48px dotik. Nespremenljivi zajemi, brez mešanja osnov/valut in brez provider dostopa ob GET portfelja. Push je izrecno odobren, ne force.

## Review Focus
1. Delni/future/nepreverjeni odgovor ne dobi jamstva; oba konca iz istega zajema.
2. Split spremeni stare cene: novi zajem atomaren, stari arhiv ostane; incremental Bar ni letna osnova.
3. Osvežitev uporablja gate/kvote, napaka ohrani zadnji dokaz in audit; noben nov GET stranski učinek.
4. Demo CLI ne piše zasebne baze; dump/restore samo svojih sintetičnih podatkov za migracijski dokaz.
5. Master push vključuje pravo testirano drevo in delujoč CI backend, brez prepisovanja tujih sprememb.

## T1 BL-235
- [x] RED razčlenitev stale cene/kazalnikov z virom/časom, ohranitev partial/identity in skritih stolpcev.
- [x] Native details, SL/EN, regresije gostote/clip.

## T2 BL-234
- [x] RED pogodbe router/IBKR koherentne split-only zgodovine, nepripravljen/neskladen odgovor.
- [x] Aditivni immutable history capture model/migracija, validator Decimal/identiteta/leto/bounded/future, test shranitve in nadomestnega zajema.
- [x] Osveževanje cen: samostojen YTD fetch s kvoto tudi ob svežih inkrementalnih svečkah; ohranitev ob napaki.
- [x] Portfelj bere en zajem za oba konca in DTO provenance; test numeričnega YTD, splita, stale/identity/currency in nobenih provider GET.
- [x] Sintetični demo zajemi z opt-in varovali; aditivno posodobiti3100 in ohraniti podatke.

## T3 BL-236
- [x] Sveži API/agents/web suite, Ruff/mypy/TS/ESLint/i18n/generacija, migracija/check/restore na sintetični bazi.
- [x] CI E2E z delujočim demom, Docker build, browser SL/EN/phone, vizualni pregled.
- [x] Neodvisni pregled in odprava, SESSIONS/BACKLOG/DESIGN/ADR/navodila testiranja.
- [x] Commit, fetch/preveri fast-forward, push GitHub master in pregledna veja; potrdi remote SHA in CI brez spremembe3000.

Predaja kode: d859fce1f43fe2ca102cc03f1bae309c34365cdb na Autotrading/master in feat/uxui-demo-upgrade; remote SHA preverjena. GitHub CI41477710171 success (API/agents/web/compose, tudi izolirana prijava).3000 nespremenjen. Operativni BL239 ostaja odprt.
