# Prevzem Vala −1: BL-190–192

## Kaj je pripravljeno

Veja `fix/signal-read-contracts`, izhodišče kode `1855eb8`; dokumentarni izvor Opusovega načrta `28f2990`. Delo je ločeno od aktivnega Claudovega checkouta in ni objavljeno na tekočem demo portu 3000. Oba popravka in raziskava sledijo [prvi specifikaciji](../superpowers/specs/2026-10-28-val-minus-1-spec.md).

- FIX-A: en pogojni UPDATE poteka odprtih signalov pred filtri/limitom; `< now`, null ostane brez roka. Accepted/dismissed/expired se ne prepišejo; PATCH in rumor guard ostaneta enaka. Stabilno razvrščanje created_at/id desc. Commit `0720806`.
- FIX-B: podrobnost po točnem UUID, 404/422, isti expiry servis kot seznam; brez odvisnosti od prvih 100 ali aktivnega filtra. SignalOut in generirani API tipi ostajajo usklajeni. Frontend kaže izvorne podatke/dokazila brez cen ali dejanj, ki jih pogodba nima. Odpiranje ne sprejme ali zavrne signala. Varno zapiranje odstrani peek, ohrani ostale parametre in vrne fokus povezanemu sprožilcu. Noben nov popstate handler.
- UX-00: [poročilo in podatkovna vrata](./2026-10-29-izvedljivost-metrik.md), [JSON](./2026-10-29-izvedljivost-metrik.json), [ponovljiva read-only poizvedba](./2026-10-29-izvedljivost-metrik.sql). Raziskava ne osvežuje podatkov. Hipoteza tedenskega urnika ni predstavljena kot dokazan vzrok odsotnosti podatkov.

## Preverjanje

| Preverjanje | Rezultat |
|---|---|
| Celoten pytest API s PostgreSQL | 467 passed, 18 obstoječih opozoril o zastarelih API-jih knjižnic |
| Dodatna pogodba notify povezave po dopolnitvi asercije | 23 passed v test_notify.py; brez pošiljanja sporočil |
| Ruff check in format celotnega API | uspešno; 169 datotek formatiranih skladno |
| mypy --strict preza/domain | brez napak, 17 datotek |
| Celoten Vitest | 28 datotek, 126 passed |
| TypeScript in ESLint | brez napak |
| i18n | SL/EN enakih 847 ključev |
| Next produkcijski Docker build | uspešen, 16 generiranih strani in dinamične poti |
| Playwright signal-deeplink.spec.ts | 10/10; desktop + 390×844 touch; SL/EN, direct URL, Entries, Back, Escape, fokus, 48px cilj, instrument preview, brez API mutacij pri branju |
| OpenAPI | izvožen iz create_app in nato generiran z openapi-typescript; brez ročnega urejanja schema.d.ts |
| SQL/JSON | read-only SQL uspešno izveden; veljaven JSON, 19 metrik, 36 dedupliciranih ciljev |

RED→GREEN je bil opažen pri FIX-A (4 neuspešni filtri/paginacija), FIX-B API (6 neuspešnih zaradi 405 pred dodatkom GET), komponenti (manjkajoča implementacija), Close (push namesto replace) in fokusu (test na sliki pred popravkom dvakrat pade, po njem uspe). Naknadni testi pokrivajo še mejo roka, null, stabilno razvrščanje, zapis zunaj prve strani, cache med ID-ji in invalidacijo. Neodvisni sveži pregled je našel samo pomembno vrzel fokusa; popravljena je in preverjena na obeh napravah.

## Okolje in ponovitev

API je uporabljal odvisnosti in orodja iz obstoječega Claudovega `.venv`, vendar je bil `PYTHONPATH` nastavljen na `services/api` te veje, kjer so tekli testi in migracije. Izolirana baza `codex_signal_expiry_test` v `preza-test-pg`, port 55432. Fixture ob začetku pytest izvaja downgrade/upgrade: **testov proti tej bazi ne poganjaj sočasno in je nikoli ne nadomesti z demo/produkcijsko bazo**. Geslo je bilo prebrano zasebno iz lokalnega testnega vsebnika, ni zapisano v dokumentacijo.

Na Windows se pnpm samodejno preusmerja na različico iz packageManager; zato so bili lokalni JS testi/lint/tipi izvedeni z neposrednimi Node CLI iz nameščenih odvisnosti. Windows SWC build se ustavi pri preverjanju lastništva predpomnilnika. Dostopov/varnostnih pravil nismo izklapljali; build je opravljen z obstoječim `apps/web/Dockerfile` v Linux Dockerju. Namestitev uporablja isti frozen lockfile. Opozorila o preskočenih install skriptah niso bila obiti.

Za ločeno ponovitev:

```powershell
# Iz korena te veje; drug port in lastno ime preprečita poseg v demo.
docker build -f apps/web/Dockerfile -t preza-codex-signal-check .
docker run -d --rm --name preza-codex-signal-check -p 127.0.0.1:3200:3000 -e API_URL=http://127.0.0.1:9 preza-codex-signal-check
# Iz apps/web; CHROMIUM_PATH nastavi na dejansko nameščeni testni brskalnik.
$env:BASE_URL = 'http://localhost:3200'
node node_modules/@playwright/test/cli.js test signal-deeplink.spec.ts --workers=2
```

Testi vse `/api/**` odgovore zamenjajo z izmišljenimi fixtures; ne potrebujejo žive baze, Telegrama ali brokerja. Začasni vsebnik je po preverjanju ustavljen. Testna slika in izolirana testna baza ostaneta za ponovitev.

## Pred vključitvijo in nadaljevanjem

1. Preberi aktualna SESSIONS/BACKLOG ter Git stanje **ciljne Claudove veje**. Commiti tu ne vsebujejo njenih morebitnih novih sprememb. Ne izvajaj reset/overwrite njenega dela. Preveri tudi sočasno dodeljene BL-ID-je in session ID-je.
2. Prevzemi FIX-A pred FIX-B. Dokumente SESSIONS/BACKLOG uskladi vsebinsko, ker se tam sočasne spremembe najverjetneje prekrivajo. Po vključitvi ponovno preveri teste na sestavljeni kodi.
3. Demo objavi šele po tej uskladitvi; ta seja ga ni zamenjala. Živi podatki so bili samo prebrani agregatno.
4. BL-193/194 odpravita vrzeli refresha in identitete; BL-195 določi skupno read pogodbo stolpcev. BL-196 pokrije snapshot po računu. Ločene nove naloge niso del že izvedene inventure. Prikazi /proposals, filtri analiz, urniki in dividende sledijo potrjenim nadaljnjim valovom.

Obstoječi načrt/komentarji/specifikacije so ohranjeni kot dokumenti. Niti BL-188/189 niti ta prevzem ne pomenijo, da je celotna večvalovna UX/UI nadgradnja že implementirana.
