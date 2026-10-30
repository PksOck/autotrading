# Izvedbeni plan dodatnega kroga po Claudovem pregledu

> **For agentic workers:** Ko je odobrena produktna izvedba, uporabi superpowers:subagent-driven-development ali superpowers:executing-plans. Produktna izvedba je odobrena v S-023; živi prenos ostane ločen.

**Goal:** Izvesti D1/A1/A2/A4/U1/U2 iz BL-218 z regresijami in prenesti vse druge pripombe v pravi naslednji SPEC brez izgube sledi.

**Architecture:** Ohranjeni podatkovni ključi, trajne izvedbe, ročna dovoljenja in LiteLLM vloge. Doda se omejen hook na dejanskem poskusu transporta in odpravi izguba stanja UI; brez novega analitičnega cevovoda ali nepreverjenega dividendnega pravila.

**Tech Stack:** Python 3.12/Pydantic/SQLAlchemy/arq, pytest z izolirano bazo; Next.js/TypeScript/next-intl, Vitest/Playwright.

**Spec:** [Izvedbeni SPEC dodatnega kroga](../specs/2026-10-30-dodatni-krog-claude-spec.md). **Osnova:** `c55e37d`. Izvajalec prebere tudi AGENTS in aktualni SESSIONS/PLAN/BACKLOG. Izhodišče pred vsako izvedbo ponovno preveri.

## Stanje izvedbe S-023

R1–R5 so izvedeni in preverjeni. Dokazi, popravki po neodvisnem pregledu in komiti so v [dokaznem zapisu](../../implementation/2026-10-30-izvedba-dodatnega-kroga.md). R6 je pripravil pet pogojnih NEXT-SPEC; inventura starih BL, S-014, merge/restore in živa namestitev ostanejo posebej označeni izdaji pogoji. Zaključek neposrednega kroga ne zapre prihodnjih paketov.

## Skupna pravila in vrstni red

R1 coverage in R2 transportni hook sta neodvisna. R3 pregled teze zahteva R2. R4 outbox je ločen od SMTP dostave in ne sme spreminjati njenih zagotovil. R5 UI lahko poteka neodvisno od API. R6 pregleda celoto in dokumentira naslednji val. Deljene datoteke/protokoli imajo enega integratorja.

SPEC pripravljamo samo za naslednji izvedbeni val. Preostali dokumenti S-B/S-F5/S-G1/S-C/S-H se pripravljajo v prednostnem vrstnem redu, I/J/K ostanejo skice. Ne čakamo na vse prihodnje module, preden popravimo dokazljivo napako trenutne izdaje.

Za vse korake veljajo omejitve SPEC §2: brez živih modelov, pošiljanja, naročil, migriranja :3000 ali samodejnega merge/push. Vzorce Flex očisti pred vključitvijo v repo. Stanje done mora pomeniti dokaz, ne samo zapis načrta.

## R1 — D1: coverage upsert

**Spremeni:** `services/api/preza/services/dividends.py`; parser samo, če reprodukcija to zahteva.
**Testi:** `services/api/tests/test_dividends_db.py`, `test_dividends.py`.
**Vmesnik:** obstoječi store/import in DividendsOut ostaneta združljiva. Porabnik naslednjega koraka je nespremenjen prikaz aktivnih odprtih obračunov.

- [x] Napiši `test_missing_same_period_import_preserves_open_accruals`: prvi uvoz open → drugi missing za isti ključ → GET in coverage ohranita prvi dokaz.
- [x] Zaženi test nad namensko bazo; potrdi prvotni neuspeh zaradi izgubljenega dokaza.
- [x] Popravi pogoj upserta po prehodni tabeli R-D1; ohrani revizijo in varovala konfliktov.
- [x] Dodaj replay, missing→complete, starejši dokaz in novejšo prazno complete sekcijo; vse morajo uspeti.
- [x] Ciljno `pytest -q tests/test_dividends.py tests/test_dividends_db.py tests/test_dividend_controls.py`, Ruff/mypy; ločen commit z BL-218/D1.

## R2 — A1: transportna meja

**Spremeni:** `services/api/preza/llm/client.py`, `llm/automatic.py` in lokalne protokole/dvojnike.
**Testi:** `services/api/tests/test_llm_client_limits.py`, `test_settings_feedback.py`.
**Vmesnik:** `AttemptGuard = Callable[[], Awaitable[None]]`, keyword-only `before_attempt: AttemptGuard | None = None`; združljiv osnovni protokol in eksplicitna varovana razširitev. Wrapper uporablja hook brez globalnega mutiranja klienta.

- [x] Napiši `test_automatic_schema_repair_rechecks_switch`: prvi fake HTTP vrne neveljaven JSON in izklopi kontrolo → `http_calls == 1`, prvi usage ohranjen, razlog stop razviden.
- [x] Zaženi in potrdi, da obstoječa koda naredi dva klica.
- [x] Hook umesti neposredno pred vsak transport; prilagodi AutomaticLlm in scripted dvojnike brez ne-varovanega fallbacka.
- [x] Testi: manual poprava dovoljena, avtomatska poprava ob vklopu uspe, izklop pred prvim klicem 0 transportov, output limit in accounting nespremenjena.
- [x] Ciljno `pytest -q tests/test_llm_client_limits.py tests/test_settings_feedback.py`, tipi in Ruff; commit A1.

## R3 — A2: pregled teze in zaklep

**Zahteva:** R2.
**Spremeni:** `services/agents/preza_agents/thesis_tracker/runner.py`, po potrebi `worker.py`.
**Testi:** `services/agents/tests/test_thesis_review_worker.py`, `test_thesis_review.py` in po potrebi nov integracijski test z DB zaklepom.
**Vmesnik:** obstoječi kontekst validirane trajne izvedbe; automatic uporablja varovani transport, manual ostane nespremenjen. `mark_dispatched`/finalizacija ohranita lastništvo in ne podvajata klica.

- [x] Napiši reprodukcijo z dvema povezavama/bariero: zaklep zadrži dispatch, kontrola se izklopi, nato se zaklep sprosti; HTTP count ostane 0.
- [x] Potrdi prvotni neuspeh; če se scenarij ne ponovi, dokumentiraj dokaz in popravi razumevanje pred spremembo.
- [x] Ponovi preverjanje na meji po commitu in varuj vsak transportni poskus. Blokiran prvi HTTP dobi končen razlog brez lažne porabe, ne večni running.
- [x] Regresije za dovoljeni manual/izjemo okna, popravo JSON z izklopom, nepripadajočo izvedbo, stale revision in drugega živega lastnika.
- [x] Ciljno agents `pytest -q tests/test_thesis_review_worker.py tests/test_thesis_review.py`, API testi callbacka, Ruff/mypy; commit A2. Uporabi agents runtime z njegovimi odvisnostmi.

## R4 — A4: outbox brez izstradanja

**Spremeni:** `services/api/preza/services/automation.py:deliver_pending`; morebitna sprememba modela zahteva predhodno dopolnitev natančne sheme v SPEC in novo migracijo, ne posega v stare migracije.
**Testi:** `services/api/tests/test_automation_db.py`, `test_automation_integration_edges.py`.
**Vmesnik:** ohrani `deliver_pending(session, settings) -> int`, job_id in claim; klasifikacija razlogov/časovnih kombinacij je opredeljena v R-A4.

- [x] Napiši `test_deliver_pending_passes_100_blocked_rows`: 100 blokiranih + 1 dovoljen → v istem ticku je dovoljen posel v fake enqueue.
- [x] Potrdi prvotni neuspeh, nato filter upravičenosti pred LIMIT in omejeno pregledovanje s stabilnim `(scheduled_for,id)`.
- [x] Trajno neveljavno revizijo terminalno preskoči; začasna pavza/onemogočenost/okno ostanejo obnovljivi, ročni override se spoštuje.
- [x] Dokaži meje 100 novih dostav / 1000 kandidatov, napredovanje pri večjem naboru, že enqueued vrsticah in restartu. Če je potreben trajni cursor, ne uporabi samo pomnilnika procesa; pred izdelavo določi njegovo shranjevanje/migracijo.
- [x] Regresije Redis izpada, dveh schedulerjev in enqueue deduplikacije brez dvojne izvedbe; ciljno automation testi, Ruff/mypy; commit A4.

## R5 — U1/U2: BacktestPanel povezave

**Spremeni:** `apps/web/components/track-record/BacktestPanel.tsx`, SL/EN.
**Testi:** obstoječi `BacktestPanel.test.tsx`; nov `apps/web/e2e/backtest-navigation.spec.ts`.
**Vmesnik:** signalni EntityLink/usePeek, analiza na pravi `/analysis/{id}` v novem zavihku z oznako. Zahteva ohranitve stanja velja za prvotni zavihek; ne uvajamo novega neobstoječega analysis Peek.

- [x] Napiši test z obema viroma in istim UUID: signalni cilj in cilj analize se razlikujeta; noben `peek=analysis`.
- [x] Pred popravkom preveri napačno povezavo in polno navigacijo/izgubo stanja. Uporabi scripted POST rezultat, ne novih analiz.
- [x] Zamenjaj navadni anchor za signal z EntityLink; analizo poveži po SPEC §7; ne zavrzi obstoječih URL parametrov.
- [x] Test klik signal → close/Escape/Back ohrani tabelo, oddane parametre in ne ponovi POST. Novo odprta analiza ima pravilen ID, prvotna tabela ostane. Dodaj SL/EN ter desktop/phone in fokus.
- [x] Ciljno Vitest datoteke in Playwright nova datoteka; ESLint/tsc/i18n; commit U1/U2.

## R6 — Integracija, naslednji SPEC in ločen prevzem

- [x] Vsako ugotovitev iz SPEC §1 poveži na popravek/test ali na konkretni naslednji SPEC. Ne izgubi A3/A5/D2 zato, ker niso v šestih neposrednih popravkih.
- [x] Uredi S-B (D1/D2/D3/F1/B5, dejanski XML), S-F5 (restore pred živo migracijo), S-G1 (A1–A5/R1 in ločeno BL-204), minimalni S-C ter S-H. Za D2 ne izberi netiranja ali izločanja brez potrditve semantike vira.
- [ ] V master planu ohrani skice odloženih sklopov; popravi dokazana prekrivanja BL-174/193/194 in zastarele opise BL-011/013 samo po preverbi.
- [ ] Pred združitvijo dopolni manjkajoči S-014 iz osnovnega checkouta, brez prepisa drugih lokalnih sprememb. Ne ponavljaj že izvedenega čiščenja vej iz c55e37d.
- [x] Zabeleži dokaze in odprte blokade v SESSIONS/BACKLOG. BL-218 ostane odprt, dokler šest popravkov nima rezultatov.
- [ ] M: ločen pregled in potrditev dovoljenja za združitev. D: nova izrecna potrditev namestitve :3000, pred njo backup/restore, dogovorjene migracije in rollback. Ta plan ne izvrši ne M ne D.

## Ukazna vrata in dokazni paket

Ukaze izvajaj v pripadajoči mapi, s pripravljeno namensko testno bazo in lokalnim runtime, ki je dokumentiran v README/SESSIONS. Ne prekopiraj živih connection stringov v poročilo. Na Windows uporabi dejanski razpoložljivi interpreter/CLI, brez nenamerne ponovne namestitve paketov.

| Področje | Vrata | Uspeh |
|---|---|---|
| API | `python -m pytest -q`; `ruff check .`; `ruff format --check .`; `mypy preza` | Vsi izbrani testi dejansko z DB, brez nepričakovanih skipov, nič napak |
| Agents | `python -m pytest -q`; Ruff/format/mypy v agents runtime | Brez živih LLM klicev; concurrent/dispatch regresije zelene |
| Pogodbe | export OpenAPI po README in generator TS; primerjava generiranih datotek | Nobene ročne razlike sheme ali neskladnih tipov |
| Web | Vitest, `tsc --noEmit`, ESLint `--max-warnings=0`, `node scripts/check-messages.mjs` | Zelena zbirka in usklajeni SL/EN |
| Build | Docker build samo ločenega `preza-demo` sklada | Uspešen Linux build; ne spreminja slik/containerjev :3000 |
| E2E | `BASE_URL=http://localhost:3100` in Playwright `backtest-navigation.spec.ts`, nato relevantne regresije | Pravilen cilj/ID, stanje in fokus; brez nepričakovanih POST/sporočil |
| Ročni pregled | :3100, desktop/telefon, filter/izračun/obe povezavi/zapiranje | Shranjeni rezultat ostane, prava analiza se odpre, brez placeholder not-found |

## Pregled tveganih primerov

1. D1 ne sme blokirati legitimnega novejšega praznega posnetka.
2. A1 ne sme blokirati manual ali izgubiti accounting prvega plačljivega poskusa.
3. A2 ne sme izklop spremeniti v nedoločeno stanje ali poškodovati živega lastnika.
4. A4 ne sme z odpravo izstradanja uvesti neomejenega branja ali ponovljenega plačljivega dispatcha.
5. U1/U2 ne smeta povezati signala na analizo enakega UUID ali izgubiti študije ob Back/Escape.

**Merilo zaključka tega kroga:** šest neposrednih ugotovitev ima dokaze, vse ostale imajo lastnika/odvisni SPEC, ukazna vrata so zelena in neodvisni pregled nima neobravnavane blokade. Priprava dokumentov sama tega merila ne izpolni.
