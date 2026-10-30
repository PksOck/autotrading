# Dodatni izvedbeni krog BL-218 in demo regresija BL-220

**Datum:** 2026-10-30. **Veja:** `feat/uxui-demo-upgrade`. **Izhodišče:** `d0ceebf`. **Končni produktni rez:** `0db305d2746a0e6de07ae0e0b0279ccd0eb7d5d5`; nadaljnji commit dopolni samo dokumentacijo. **Obseg:** [SPEC](../superpowers/specs/2026-10-30-dodatni-krog-claude-spec.md) in [plan](../superpowers/plans/2026-10-30-dodatni-krog-claude-izvedba.md). Brez združitve, push ali prenosa na :3000.

## Dobavljeno in dokazano

| Pripomba / naloga | Rezultat | Regresijski dokaz |
|---|---|---|
| D1 | Odsotna sekcija ne prepiše prej poročane partial/complete pokritosti in row_keys; velja ista/novejša verzija, missing→present in izrecno novejša prazna sekcija. Konflikti knjižb/obračunov ostanejo. | Štiri začetne napake, nato 21 dividendnih testov. Starejši ponovni uvoz ne oživi zaključenih upravičenj. Commit `9edbdf2`. |
| A1 | Kontrola tik pred vsakim HTTP poskusom, tudi JSON popravo; brez ne-varovanega fallbacka. Zavrnjen poskus ne poveča HTTP attempts, predhodni tokeni/znani Decimal stroški ostanejo; pred prvim HTTP je znana ničla. | 42 ciljnih testov; avtomatski izklop, dovoljeni manual, output limit, accounting. Commit `8f95e97`. |
| A2 | Po čakanju na dispatch zaklep in pred vsakim poskusom se ponovno preverijo trajna dovoljenja pregleda teze. Varni razlogi zaključijo lastno rezervacijo; drug živi lastnik ostane nedotaknjen. | Resnični PostgreSQL row lock, `pg_blocking_pids`, druga povezava izklopi kontrolo; prvotna dva primera padeta, po popravku ciljni sklop 33 uspe. Commit `8f95e97`. |
| A4 | Upravičenost pred LIMIT; največ 100 novih dostav/1000 kandidatov. Trajni stabilni kurzor preživi restart, začasne blokade ohranijo pending, stale revision se preskoči. Isti job_id in claim ostaneta. | 100 blokiranih + dovoljen 101, 1002 enako časovno označena namena, že enqueued nabor, restart/izpad, dva schedulerja, realni arq resume istega ID. Migracija 0020. Commit `6cd2488`. |
| A4-1 iz pregleda | Terminalizacija zastarelega kandidata uporabi pogojni UPDATE samo za pending, preveri RETURNING ter ne pusti brezpogojnega ORM flush. | Trije resnični DB sessioni: pravi claim drži zaklep, tretji spremeni politiko, delivery SQL dokazano čaka; prvotno skipped namesto running, po popravku running in lastnik ostaneta. Dva ozka testa uspeta, širši ciljni nabor 23 uspe. |
| U1/U2 | Signal uporablja EntityLink/Peek z ohranjenimi filtri/rezultati; analiza odpre pravi `/analysis/{id}` v novem zavihku z oznako SL/EN. Osnutek ne preimenuje izračuna. | Isti UUID dveh virov, Close/Escape/Back in fokus, modifiers/keyboard, vsi parametri/rezultati ter samo en POST: štirje novi E2E SL/EN × desktop/phone uspejo. Commit `744a4ae`. |
| BL-220 | Zgodovinski demo signali imajo obvezni `kind` v EvidenceRef; API shema ni oslabljena. | Nov DB test prvotno pade pri GET; po popravku vseh 14 točnih sintetičnih ID vrne veljaven SignalOut. Samo teh 14 obstoječih demo dokazil popravljenih brez reseed. Commit `0db305d`. |

## Končni preizkusi trenutne kode

Python runtime je prebran iz obstoječih API/agents venv v Claudovem preverjevalnem checkoutu; `PYTHONPATH` kaže na ta worktree. Runtime in Claudova koda nista spreminjana. Baze `codex_round_*_test` so ločene na testnem PostgreSQL :55432; noben fixture ne uporablja žive ali demo baze. Polni zaključni API test uporablja lastno `codex_round_root_test` ter začasni Redis samo na 127.0.0.1:56380.

| Preverjanje | Dejanski rezultat |
|---|---|
| API `python -m pytest -q -p no:cacheprovider --tb=short`, z TEST_DATABASE_URL in TEST_REDIS_URL | **585 passed**, brez preskokov/napak, 396,50 s. **18 obstoječih deprecation opozoril**: Starlette TestClient/httpx in SQLAlchemy ARRAY.any v proposals/analyze, radar/context, entries/dip; niso popravljana v tem krogu. |
| Agents enak pytest ukaz, lastna testna DB | **229 passed**, 90,46 s. |
| API Ruff check/format, `mypy preza` | čisto; 220 Python datotek formatirano, 135 source modulov brez mypy napak. |
| Agents Ruff check/format, `mypy preza_agents` | čisto; 46 Python datotek, 23 source modulov. |
| Web `node node_modules/vitest/vitest.mjs run` | **156 passed**, 42 datotek. |
| Web TypeScript, ESLint `--max-warnings=0`, Prettier spremenjenih datotek, check-messages | uspešno; **1291 usklajenih ključev** SL/EN. |
| OpenAPI export + openapi-typescript | ponovno generirano; brez vsebinske razlike v OpenAPI/TS shemi. |
| Linux Docker build web in API | uspešno, samo `preza-demo`. |
| Playwright `BASE_URL=http://localhost:3100`, `--workers=1` | **64 passed / 10 namerno preskočenih** v 2,1 min; preskoki obstoječih primerov glede na desktop/phone, noben od štirih novih ni preskočen. |
| Migracije | head **0020** na ločenih testnih in demo bazi; downgrade/upgrade testne fixture uspe. To ni dokaz obnove žive baze. |

Prvi novi E2E zagon je imel 3 uspehe in eno izgubljeno prvo polje pred inicializacijo odjemalca. Test zdaj počaka na prvo klientovo query zahtevo ter preveri izvedeno spremembo povezanega `min` atributa. Ponovljeni štirje in celotna zbirka uspejo brez fiksnih časovnih pavz. Testnega neuspeha ne predstavljamo kot produktni popravek obrazca.

## Ročni demo pregled in izolacija

- :3100 je dobil novi web/API in interno migracijo 0020, brez workers/agents/notify ali ponudniških ključev. Obstoječa sintetična baza ni ponovno posejana.
- Dejanski izračun v in-app brskalniku: **17 izmerjenih / 10 preskočenih / 27 zapisov**. Stari zgodovinski MSFT signal se po ciljnem popravku dokazila odpre s statusom, virom, časom in dokazilom; Close ohrani vseh 27 rezultatov. Analizna povezava vsebuje dejanski analysis UUID in pravi zaslon.
- Posnetek: `C:/Users/Jan/.codex/visualizations/2026/10/28/01a1833d-4dbe-73b2-b9ee-2d3265ca9a98/bl218-study-signal.png`.
- :3000 ostane na nespremenjenih slikah web `sha256:4eaf458ee0525197f3800d28ed6d758aaffa70ec23d6bfcf7ddaaff67e06f7c9` in API `sha256:973f535ba8840631e0442f59c346c6b3469a17646f5b338703b50fdc9349e194`.
- Noben živ LLM/SMTP/Telegram/broker klic, naročilo, merge ali push ni del tega kroga.

## Neodvisni pregled in odločitve

D1 omejeni pregled: PASS. A1/A2 in U1/U2 omejeni pregled: PASS. A4 omejeni pregled je našel A4-1; napaka reproducirana na pravi DB in popravljena. [Končni neodvisni povezani pregled](./2026-10-30-neodvisni-pregled-dodatnega-kroga.md) je **PASS, A4-1 ADDRESSED, 0 kritičnih / 0 pomembnih / 0 manjših novih ugotovitev**. [Izpis končnih API testov](./2026-10-30-api-regresije.txt) ohrani dokaz 585 uspehov in obstoječih opozoril. BL-218 je zaključen za neposredni krog, ne za prihodnje pakete ali živo izdajo.

Odločitve izvajalca so sledljive:

1. Neuspel pomožni Git Bash zapis izvedbenega delovnega prostora je zamenjan z enakovrednim lokalnim zapisom; ni spremembe produkta ali stroška povratka.
2. OpenCode `--auto` je samodejni varnostni pregled zavrnil **pred izvedbo**, ker zunanjega dostopa DeepSeek do zasebne kode ni štel za dovolj izrecno dovoljen prenos. D1 je izveden lokalno, brez obvoda ali prenosa kode. DeepSeek v tem krogu ni uporabljen.
3. Interni trajni kurzor in migracija 0020 sta izbrana zaradi hkratne omejitve dela in poštenega nadaljevanja po restartu; [ADR-0023](../adr/ADR-0023-trajni-kurzor-dostave-opravil.md). Če je presoja napačna, sta potrebna povratna migracija in sprememba razporejanja, ne ponavljanje že začetega plačljivega dela.
4. Obseg je ozko dopolnjen z BL-220, ker je dejanski demo pregled odkril neveljaven sintetični primer. Če je presoja napačna, se popravijo sintetični primeri; živi podatki ostajajo nespremenjeni.

Astra zaključnega pregleda ni izvedla zaradi omejitve uporabe; zaključni neodvisni pregled prevzame SOL. Uspeha Astre ne navajamo.

## Naslednji koraki ostajajo ločeni

Pet novih pogojnih NEXT-SPEC je povezanih v [registru](../superpowers/specs/2026-10-30-odprti-sklopi-priprava-spec.md): S-B, S-C, S-F5, S-G1, S-H. Matrika v [S-H](../superpowers/specs/2026-10-30-prevzem-in-prenos-spec.md) pokrije vseh **14 pripomb**, vsako s pogodbo/fixture in blokado.

D2/D3/F1/B5 potrebujejo dejanski očiščen Flex/`Re`, potrditev valutne osnove in pregled backfilla. A3/A5/R1 ter trajni osnutek BL-204 ostajajo izvedbeni naslednji sklop, ne že rešeni. E1/SMTP potrebuje konfiguracijo in ločeno izrecno dovoljen prejemnik/vsebino za pravo dostavo. Manjkajoči S-014 se prenese ob dogovorjeni združitvi, brez prepisa drugih sej. BL-214/215 zato nista avtomatsko zaključena.

Backup in dokaz obnove sta pred prvo živo migracijo, vključno z 0016–0020. Združitev in namestitev sta ločeni stopnji; :3000 zahteva novo izrecno odobritev uporabnika. Pripravljeni dokumenti/testi te odobritve ne nadomestijo.
