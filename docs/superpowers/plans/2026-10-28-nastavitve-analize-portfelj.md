# Nastavitve procesov, analize, predlogi in dividende — izvedbeni načrt

> **Posodobitev po pregledu aktualne Claudove veje:** ta dokument je začetni delovni osnutek proti starejšemu `c0c15ae`. Njegovi BL-161–171 so na aktualni veji `1855eb8` že zasedeni z drugimi nalogami in niso veljavne rezervacije. Merodajen predlog je [celoviti načrt UX/UI](./2026-10-28-celovita-uxui-nadgradnja.md) z oznakami UX-01–20. Ta ožji osnutek ostane tehnično gradivo; ob ponovni uporabi preveri aktualno kodo, zlasti že izvedeni M5, analize, uvoz Flex in ADR-0013 z 48 px cilji na dotik.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or, if the user chooses delegation, superpowers:subagent-driven-development. Implement task-by-task and track checkbox steps.

**Cilj:** Obstoječo Prežo nadgraditi z uporabniškim nadzorom opravil, preglednimi analizami, zanesljivimi predlogi in dividendnim pogledom dejanskega portfelja.

**Arhitektura:** Obdržimo FastAPI, PostgreSQL, arq in Next.js. Nastavitve in zgodovina izvajanja živijo v bazi; arq periodično preverja zapadlost, poslovna opravila pa pred začetkom preverijo veljavno politiko. Dividende temeljijo na denarnih dogodkih IBKR, napovedi pa so ločene od prejetih izplačil.

**Sklad:** Python 3.12, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, arq, Next.js 16, TanStack Query, next-intl, pytest, Vitest in Playwright. Brez novega zunanjega razporejevalnika.

**Specifikacija:** Zahteve uporabnika iz 2026-10-28, AGENTS.md, PLAN.md §5, DESIGN.md SCR-06/SCR-08/SCR-11/SCR-12, ADR-0004, ADR-0006, ADR-0011. Spodnji razdelek »Predlog zasnove« je delovni predlog za pregled; uporabnik še ni odobril podrobnosti ali začetka implementacije.

## Status in sodelovanje

- Samo načrtovanje; v tej seji se aplikacijska koda ne spreminja.
- Claude je po uporabnikovem sporočilu na pavzi, njegov OpenCode podagent je še aktiven. Njegov obseg ni znan. Ne ustavljamo ga in mu ne pošiljamo sporočil brez navodila uporabnika.
- Pregledana osnova: `master`, HEAD `c0c15ae`; ob začetku je bil nepričakovan samo nesleden `graphify-out/`. To ni dokaz, da podagent ne bo naknadno zapisal sprememb.
- Pred izvedbo ponovno preberi SESSIONS/PLAN/BACKLOG, `git status`, diff in HEAD; uskladi lastništvo datotek ter uporabi izolirano delovno drevo. Migracijsko številko izberi po ponovnem pregledu Alembic glav.
- Naloge BL-161–BL-171 so predlagane in neizvedene. Vsaka je ločeno pregledljiv sklop; ne izvajaj vseh v enem velikem PR.

## Kaj je potrjeno s pregledom

1. `apps/web/app/settings/page.tsx` prikazuje samo `Planned`.
2. `services/api/preza/routes/analyses.py` filtrira samo po simbolu; privzeto vrne 30 zagonov, največ 100. Filtriranje zgolj že prenesenih vrstic bi skrilo veljavne starejše rezultate.
3. `services/api/preza/worker.py` in `services/agents/preza_agents/worker.py` imata statične urnike. Agentski worker ima `max_jobs=1`; to še ne zagotavlja enkratnosti pri več instancah.
4. Dnevno kvoto trenutno računa `used_today()` po UTC; neuspešni zagoni ne štejejo. Preverjanje in ustvarjanje zagona nista ena zaklenjena transakcija.
5. Posnetek Predlogov kaže nepravilne enum vrednosti oziroma `strength` v `ProposalVerdict`. `LiteLlmClient.complete_json()` že poskusi začetni klic in en popravljalni klic; samo dodajanje prvega retryja torej ni rešitev.
6. Worker napako zapisuje v `proposal.verdict` z interpolacijo v JSON niz. Če napaka vsebuje narekovaje, je JSON neveljaven. API ob napaki razčlenjevanja vrne celoten niz, komponenta pa ga izpiše. To pojasni surovi prikaz na posnetku; dejanski odgovor ponudnika in razlog ponovljenih kartic še nista reproducirana.
7. `_deep_run()` se kliče tudi po neuspešni predhodni presoji; stanje predloga in globoke analize zato nista enaka. Za več simbolov trenutno izbere samo `proposal.symbols[0]`.
8. Finnhub že ponuja `dividend_yield_pct`, vendar Flex parser obravnava le pozicije, posle in CashReport. Denarni dogodki izplačil in davčnih odtegljajev še niso modelirani. Donosnost iz profila ni evidenca prejete dividende.
9. `WatchlistOut` že vsebuje `last_close`, vendar ne valute, časa zadnje cene ali fundamentov. `WatchlistPanel` prikazuje predvsem simbol, opombo, sparkline, donos od dodaje in dejanja. Finnhub parser shranjuje P/E TTM in dividendni donos; forward P/E in denarna dividenda na delnico še nista mapirana. Obstoj podatka pri ponudniku je treba preveriti s pogodbenim vzorcem.

## Predlog zasnove za pregled

### Možni pristopi

| Pristop | Prednost | Slabost |
|---|---|---|
| Dodatne `.env` nastavitve in obstoječi cron | Najmanj sprememb | Brez smiselnega upravljanja v UI, zahteva ponovne zagone |
| **Politike v bazi in obstoječi arq** | Takojšnje spremembe v UI, sledljivost, uporaba obstoječe infrastrukture | Zahteva transakcijsko proženje, varovala in nove tabele |
| Nov workflow sistem | Več možnosti za kompleksne procese | Dodatna infrastruktura in prevelik obseg za trenutne potrebe |

Priporočilo je drugi pristop. Ne dodajamo splošnega urejevalnika workflowov ali poljubnih cron izrazov.

### Kam sodijo funkcije

- **Nastavitve → Procesi:** skupna ustavitev novih avtomatskih opravil; kartica za vsak proces, vklop, urnik, časovno okno, zadnji/naslednji tek, razlog preskoka. Dodatno »Samodejne analize« z izbiro obsega in omejitev.
- **Analize:** filtri »Status«, »Instrument«, »Vsi zagoni / zadnji za vsak instrument«; shranjeni v URL. Privzeto predlagamo uspešno zaključene in zadnjo za vsak instrument; v teku/čakajoče ostanejo dostopne z enim filtrom in ločenim števcem.
- **Portfelj:** zavihki »Pozicije«, »Analize«, »Dividende«. Analize pokažejo pokritost portfelja, starost zadnje uspešne analize in »Analiziraj portfelj zdaj«; ne podvajajo celotnega SCR-06.
- **Watchlista:** ostane zavihek Portfelja na `/portfolio?tab=watchlist`; na namizju dobi tabelo z izbirnimi stolpci in razvrščanjem. Izbor, vrstni red in gostota se shranijo za naslednji obisk. Dejanja dobijo ozek desni stolpec z manjšimi gumbi enega nad drugim.
- **Predlogi:** razumljiv rezultat hipoteze, argumenti, tveganja, stanje obdelave in povezane analize po instrumentih. Napaka je ločen blok z možnostjo ponovnega poskusa, ne rezultat hipoteze.
- **Dividende:** sprva v `/portfolio?tab=dividends`, skladno z obstoječim parametrom `tab`; analize na `?tab=analyses`. Samostojna `/dividends` bi bila poznejša razširitev ob dokazani potrebi, ne podvojen zaslon. Obstoječi Watchlist zavihek se ohrani.

### Watchlista: predlagani stolpci in gostota

| Skupina | Izbirni stolpci | Razlaga |
|---|---|---|
| Instrument in cena | Ime, tip, valuta, zadnja cena, dnevna sprememba %, mini graf | Simbol ostane vedno viden; zadnja cena je zadnja razpoložljiva zaključna cena, ne nujno živa kotacija |
| Vrednotenje | P/E TTM, Forward P/E, FCF donos % | TTM in prihodnja ocena sta ločena; forward P/E vsebuje obdobje in izvor ocene |
| Dividende | Dividenda na delnico, dividendni donos %, payout ratio % | Denarni znesek ima valuto in osnovo TTM/letno indicirano/zadnje izplačilo; te osnove niso zamenljive |
| Kakovost | ROE %, neto marža %, rast prihodkov %, dolg/kapital | Samo razpoložljivi podatki z virom in časom |
| Spremljanje | Od dodaje %, datum dodaje, ciljna cena, opomba, zadnja analiza, pregledano | Ohranijo se aktivna/zalogovna raven, opombe ter obstoječa dejanja |

Predlagani privzeti izbor: simbol + ime, cena/valuta, dnevna sprememba %, Forward P/E, dividendni donos %, od dodaje %, dejanja. Denarna dividenda na delnico je samostojen izbirni stolpec. Prednastavitve »Osnovno«, »Vrednotenje«, »Dividende« in »Po meri« uporabniku olajšajo začetek. Podatki, ki jih ni, ostanejo `—` z razlogom; opcijski stolpec ni zagotovilo, da imajo vsi instrumenti podatek.

Desni stolpec predvidi tri kratka dejanja »Pregledano«, »V zalogo / Aktiviraj«, »Odstrani«, navpično. Na namizju 28–32 px višine z razmikom, pri dotiku vsaj 44 px. Odstranitev ohrani razveljavitev; ikonam dodaj dostopna imena in tooltip. Na telefonu najprej simbol/cena/sprememba, izbrane dodatne metrike ob razširitvi; ne stiskaj desetih stolpcev v širino telefona.

### Meje prve izdaje

- Procesi: Flex, sveče, Radar, Vstopi, izidi signalov, fundamenti, ETF profili, Telegram obvestila, jutranji povzetek in nova paketna analiza. Obstoječa opravila dobijo privzeto svoje sedanje UTC urnike. UI jasno loči UTC urnik od uporabniškega lokalnega urnika; selitev ne sme tiho prestaviti obstoječega časa.
- Nova avtomatska globoka analiza je privzeto izklopljena. Ob vklopu uporabnik izbere portfelj, aktivno watchlisto ali izbrane instrumente; predlagani začetni profil: tedensko, sobota 08:00 Europe/Ljubljana, okno 08:00–12:00, svežina 7 dni, največ 3 novi zagoni na cikel. To so predlogi, ne uporabnikove že potrjene nastavitve.
- Dnevna kvota ostane 6 in po UTC zaradi združljivosti; UI navede čas ponastavitve lokalno. Posebej omejimo avtomatske poskuse, ker neuspehi ne zmanjšajo obstoječe kvote in bi sicer dopuščali neskončne ponovitve. Prva izdaja nima samodejnih vsebinskih ponovitev neuspešnih analiz.
- Globalna pavza ustavi nove avtomatske začetke, ne ubije tekočega opravila. Ročni zagon ostane možen, vendar ne obide kvote ali izrecno onemogočenega procesa. Privzeto spoštuje okno; izrecna možnost »Zaženi zdaj zunaj okna« je sledljiva in velja samo za ta ročni zahtevek.
- Recovery opravili `sweep_runs` in `sweep_proposals` sta interna in nimata lastnih uporabniških urnikov. Pri ponovnem postavljanju in pri dejanskem začetku spoštujeta politike izvornega opravila. API dostop do obstoječih podatkov ostane mogoč.
- Časovno okno omejuje začetke. Že začeta analiza se dokonča tudi po koncu okna; UI to jasno pove. Opravila v vrsti se zunaj okna odložijo, ne označijo kot vsebinsko neuspešna.
- Nastavitve veljajo za obstoječo enouporabniško namestitev. Skrivnosti ostanejo v okolju; ta projekt ne dodaja upravljanja ponudniških API ključev v UI.
- Brez oddaje naročil; IB Gateway ostane Read-Only. LLM ne izračunava denarja, donosov ali dividend.

## Globalne omejitve

- Projektna dokumentacija slovensko; koda, komentarji, commit sporočila in pozivi modelom angleško.
- Vsa UI besedila v `apps/web/messages/{sl,en}.json`; datumi/števila prek obstoječih oblikovalnikov in tokenov.
- UTC `timestamptz` za trenutke, `date` za računovodske dneve; denar `Decimal`/`numeric`, brez `float`.
- Vsak podatek/izračun ima vir, čas in stanje pokritosti; manjkajoče vrednosti niso ničle.
- API sheme Pydantic v2; generirane TS sheme samo prek izvoza OpenAPI.
- Pred spremembami Next.js preberi ustrezno lokalno dokumentacijo po `apps/web/AGENTS.md`.
- Nove tabele imajo Alembic migracije, indekse in preverjeno nadgradnjo na testni bazi. Ne spreminjaj zgodovinskih migracij.

## Pregledna tveganja in lastniki testov

| Tveganje | Pričakovano vedenje | Naloga |
|---|---|---|
| DST, polnoč, dva workerja, izpad Redis | En tek na termin; brez dvojnega izvajanja in navala zamujenih zagonov | BL-164 |
| Ročni/paketni zagon hkrati, pavza med čakanjem | Skupna kvota in ponovni pregled politike ob začetku | BL-165 |
| Več simbolov, poškodovan zgodovinski JSON, ponovni klik | Ločena stanja, brez lažnega rezultata in dvojnega signala | BL-161/162 |
| Delnica prodana, več računov, starejši posnetki | Paketi samo aktualnih pozicij; pretekla izplačila ostanejo vidna | BL-165/167 |
| Več valut, davki, storno, akumulacijski ETF, manjkajoči podatki | Brez seštevanja različnih valut ali izmišljenega neto prihodka | BL-167/168 |

## Faza A — najprej zanesljivi rezultati

### BL-161: Diagnoza in pogodba rezultatov Predlogov

**Datoteke:** spremeni `services/api/preza/{llm/client.py,proposals/analyze.py,domain/radar.py,models.py,routes/proposals.py,worker.py}`; nova migracija za ločene podatke napak in poskusov; testi `services/api/tests/test_proposals.py`, `services/api/tests/test_llm_client.py` in obstoječi `test_api_m2.py`.

**Vmesnik:** `ProposalOut` dobi `result: ProposalResult | None`, `error: ProposalError | None`, `attempt_count: int`; `ProposalError` vsebuje stabilen `code`, `retryable`, `occurred_at`, `correlation_id`. Združljiv `verdict` ostane samo uporabniški povzetek uspešnega rezultata. `ProposalResult` vsebuje validirane `verdict`, `summary`, `key_points`, `risks`, `direction`, `horizon`, `strength`, `model`, `source`, `as_of`; `ProposalError` ne vsebuje surovega ponudniškega odgovora.

- [ ] V testnem okolju reproduciraj primer s posnetka. Zabeleži vlogo/dejanski model, verzijo sheme, očiščen izhod in validacijsko napako; preveri, ali živi API/UI ustrezata HEAD. Brez skrivnosti in brez pošiljanja novih plačljivih klicev samo za načrtovanje.
- [ ] Dodaj teste za napačen `direction`, `verdict` in `strength`, en neuspešen popravljalni klic, narekovaje v napaki ter obstoječ poškodovan JSON. Pri neuspehu `result is None`, ni signala; odgovor API ne izpiše interne napake kot priporočila.
- [ ] Po dokazu vzroka popravi pogodbo poziva/ponudniškega adapterja. Ne pretvarjaj neveljavnih enumov ali številk v poljubne privzete vrednosti. Ohranita se največ dva LLM klica za presojo; podrobnosti diagnostike so ločene od UI.
- [ ] Preveri večsimbolno semantiko: hiter predlog ostane presoja skupne hipoteze; globoka analiza ustvari povezavo za vsak podprt instrument, ne samo prvega. `ProposalOut.analyses` je seznam `{symbol, analysis_id, status}`; stari `analysis_id` ostane združljiv za prvi rezultat. Napaka hitre presoje ne prikrije stanja že sprožene globoke analize.
- [ ] Ponovi `uv run pytest tests/test_proposals.py tests/test_llm_client.py tests/test_api_m2.py -q` v `services/api`; pričakovano vsi testi PASS. Nato `ruff` in `mypy`. Commit `fix(proposals): separate verdicts from processing errors [BL-161]`.

### BL-162: Predlogi — uporaben prikaz in nadzorovan retry

**Datoteke:** `apps/web/components/proposals/ProposalList.tsx`, nov `ProposalResultPanel.tsx`, `apps/web/lib/api/{hooks.ts,types.ts}`, sporočila SL/EN, `services/api/preza/routes/proposals.py`; novi `apps/web/e2e/proposals.spec.ts` in API testi iz BL-161.

**Vmesnik:** `POST /proposals/{id}/retry` vrne posodobljen `ProposalOut`, 409 za tekoč ali uspešen predlog. Uporabi zaklep vrstice in nov identifikator poskusa; zgodovina neuspehov ostane. Ponovni poskus ne sme ustvariti dveh signalov ali podvojenih globokih analiz.

- [ ] Najprej testi: berljiva napaka brez JSON; uspeh pokaže sklep/argumente/tveganja; hiter in globok status ločeno; dve sočasni retry zahtevi sprožita en poskus.
- [ ] Dodaj filtre statusa/simbola, razširitev kartice in »Poskusi znova« za ponovljive napake. Povezave vodijo na pravi instrument in ustrezni globoki rezultat.
- [ ] Razišči ponavljajoče kartice s posnetka: primerjaj ID-je in izvor (seed, ponovljene zahteve, retry). Ne briši zgodovine in ne združuj različnih legitimnih predlogov samo po enaki hipotezi. Onemogoči večkratno oddajo med čakajočo zahtevo; varovanje POST z idempotency ključem mora vključiti proxy, odjemalca in API.
- [ ] Po regeneraciji OpenAPI preveri API teste, UI teste in Playwright `proposals.spec.ts`; commit `feat(proposals): show structured results and retry state [BL-162]`.

### BL-163: Filtri analiz v API in UI

**Datoteke:** `services/api/preza/routes/analyses.py`, `services/api/tests/test_analyses.py`, `apps/web/components/analysis/AnalysisRunList.tsx`, nov `AnalysisFilters.tsx`, `apps/web/app/analysis/page.tsx`, `apps/web/lib/api/{hooks.ts,types.ts}`, sporočila, `apps/web/e2e/analysis.spec.ts`.

**Vmesnik:** `GET /analyses?symbol=AMD&status=done&latest_per_instrument=true&limit=30&offset=0`; status je obstoječi `AnalysisStatus`, limit 1–100, offset >= 0. Ohranimo seznam kot odziv zaradi združljivosti.

- [ ] Dodaj podatkovne teste z več kot 100 zagoni, enakim `created_at`, različnimi instrumenti istega simbola, zadnjim neuspelim in starejšim uspešnim zagonom. Status filtriraj pred izbiro zadnjega, nato razvrsti in šele nato paginiraj.
- [ ] Uporabi particijo po `instrument_id`, vrstni red `created_at DESC, id DESC`; instrumentov ne združuj po simbolu. API validira negativne limite. Ne izvajaj teh filtrov samo na trenutnih 30 zapisih v brskalniku.
- [ ] Dodaj URL filtre, ponastavitev strani ob spremembi, »Naloži več«, prazna stanja in TanStack query ključ z vsemi parametri. Instrumentov kompaktni seznam ostane združljiv.
- [ ] Preveri `uv run pytest tests/test_analyses.py -q`, web enotske in e2e teste za filter kombinacij; commit `feat(analysis): filter successful and latest runs [BL-163]`.

## Faza B — nastavitve in avtomatika

### BL-164: Politike procesov in zanesljivo razporejanje

**Datoteke:** novi `services/api/preza/domain/automation.py`, `services/api/preza/automation/{__init__.py,registry.py,schedule.py,service.py}`, `services/api/preza/routes/automation.py`; spremeni `models.py`, `main.py`, oba workerja; nova migracija; novi `services/api/tests/test_automation_schedule.py`, `test_automation_db.py`, agentski testi varoval.

**Pogodba:** `ProcessPolicy` vsebuje `process_key`, `enabled`, `schedule` (interval ali dnevni/tedenski čas), `timezone`, `weekdays`, `window_start/end`, `revision`, `source`, `updated_at`; skupne nastavitve `automatic_paused`. `ProcessExecution` vsebuje ključ procesa, `scheduled_for`, izvor manual/scheduled, stanje, začetek/konec, heartbeat, razlog, napako in števce. Unikat `(process_key, scheduled_for)` za avtomatske termine. `GET /automation/processes`, `PATCH /automation/processes/{key}`, `PATCH /automation/control`, `GET /automation/executions`; sprememba z zastarelo revision vrne 409.

**Funkcije:** `next_due(policy: ProcessPolicy, after: datetime) -> datetime | None`, `is_start_allowed(policy: ProcessPolicy, now: datetime, origin: str, override_window: bool = False) -> bool`, `dispatch_due(ctx: dict[str, Any]) -> int`. Vsi vhodni trenutki morajo biti timezone-aware.

- [ ] Najprej deterministični testi: Europe/Ljubljana poletni/zimski čas, ponovljena ura enkrat, neobstoječa ura preskočena, okno čez polnoč pripada dnevu začetka, prazni dnevi neveljavni, neveljaven timezone 422, meja konca izključena.
- [ ] Uvedi tabeli politik/izvajanj in skupne kontrole. Privzete stare urnike prenesi brez spremembe UTC trenutkov; interno recovery proženje ohrani. En minutni tick nadomesti uporabniške statične crone, ne teče poleg njih.
- [ ] Transakcijsko rezerviraj zapadli termin in dostavo prek trajnega zapisa v bazi. Če Redis odpove po commitu, naslednji tick ponovi dostavo istega execution ID; stabilen job ID in atomaren claim v workerju preprečita dvojno delo. Lease z heartbeat omogoča zaznavo sesutja; recovery ne podvoji še aktivnega opravila.
- [ ] Pred dejanskim začetkom ponovno preberi politiko v obeh workerjih in podklicih (npr. `sync_flex → refresh_bars`). Izklopljenih dragih procesov ne sme obiti recovery ali posreden klic. Globalna pavza velja le za avtomatiko.
- [ ] Po izpadu izvedi največ en najnovejši zapadli tek, stare termine označi preskočene. Prikazuj čas naslednjega teka in razlog odloga; sprememba politike velja brez restartov. Nikoli ne logiraj praznega minutnega ticka kot novo uporabniško opravilo.
- [ ] Testi dveh dispatcherjev, dveh workerjev, padca pred/po enqueue, zastarele revizije in odloga do naslednjega okna morajo PASS na pravi testni bazi in Redis. Commit `feat(automation): persist process schedules and execution guards [BL-164]`.

### BL-165: Paketne analize portfelja in watchliste

**Datoteke:** novi `services/api/preza/automation/analysis_batches.py`, `services/api/tests/test_analysis_batches.py`; spremeni `services/api/preza/{services/analyses.py,services/portfolio.py,routes/analyses.py,worker.py,models.py}`, agentski worker in teste; nova migracija.

**Pogodba:** `POST /analyses/batches` z `scope: portfolio|watchlist|selected`, `symbols`, `max_runs: 1..100`, `freshness_days: 1..365`, `override_window: bool`; `GET /analyses/batches/{id}`. `AnalysisBatchOut` ima števce in postavke `{instrument_id, symbol, analysis_id, state, reason}`. `create_batch(session, request, now) -> AnalysisBatchOut` uporabljata ročni endpoint in scheduler, ne podvajata logike.

- [ ] Najprej testi zadnjega posnetka za vsak račun, praznega portfelja, prodane pozicije, ničelne količine, kratke pozicije, istega instrumenta na dveh računih, aktivne/rezervne watchliste in nepodprtega tipa. V prvi izdaji delnice/ETF, brez opcij in denarja; odprta kratka pozicija je vključena z oznako, ne privzeto preskočena.
- [ ] Targete dedupliciraj po instrument ID in zamrzni v paket; simbolno dvoumnost vrni uporabniku, ne izberi naključno. Pri portfelju uporabi zadnji uspešni celotni snapshot vsakega računa, tudi prazen snapshot po prodaji vseh pozicij; po potrebi dodaj evidenco snapshotov z migracijo. `MAX(report_date)` samo nad pozicijami tega ne reši.
- [ ] Svežina temelji na zadnji uspešni analizi; queued/running pomeni »že v obdelavi«. Vrstni red kandidatov: brez uspešne analize, nato najstarejša uspešna, nato instrument ID. Preskočeni ostanejo z razlogi `fresh`, `already_active`, `unsupported`, `daily_limit`, `batch_limit`, `process_disabled`.
- [ ] En skupen zaklenjen sprejem za ročne analize, globoke predloge in pakete atomarno rezervira kvoto ter aktivni instrument. Dodaj podatkovno varovalo največ enega queued/running zagona na instrument. Kvota za queued/running/done ostane UTC; avtomatski attempt cap je ločen in šteje tudi neuspehe. Ob doseženem limitu ostanek označi preskočen, brez tihega zagona naslednji dan.
- [ ] Test dveh sočasnih paketov in ročnega POST pri eni preostali kvoti mora ustvariti največ en nov zagon; ponovna dostava istega paketa ne ustvari novih. Varovalo za začetek prebere aktualno okno/pavzo tudi po več urah čakanja; odložitev ne drži edine agentske reže z dolgim sleepom.
- [ ] Preveri API/agentske DB teste in regresije; commit `feat(analysis): schedule bounded portfolio analysis batches [BL-165]`.

### BL-166: Nastavitve in portfeljski pregled analiz

**Datoteke:** `apps/web/app/settings/page.tsx`, `apps/web/app/portfolio/page.tsx`, novi `apps/web/components/settings/{ProcessSettings,AnalysisAutomationSettings,ExecutionHistory}.tsx`, `apps/web/components/portfolio/PortfolioAnalyses.tsx`, API hooks/tipi, sporočila, proxy whitelist, novi e2e `settings.spec.ts` in dopolnjen `analysis.spec.ts`.

- [ ] Najprej komponentni testi shranjevanja/napake/409 konflikta in Playwright scenarij nastavitev → avtomatski paket na fiksni uri → prikaz rezultatov. Brez čakanja na resnično uro v testu.
- [ ] Uvedi kartice procesov, globalno pavzo, ureditev urnika/okna, jasen timezone, predogled naslednjih treh terminov, zadnji tek in razlog preskoka. Prikaži, da okno omejuje začetke. Uporabnik mora videti neuspešno shranjevanje; brez lažnega optimističnega »shranjeno«.
- [ ] Dodaj izbor obsega analiz, svežino, cap cikla, dnevno porabo in čas ponastavitve. Pred ročnim paketom pokaži obseg in omejitve; za obhod časovnega okna je potreben izrecen klik.
- [ ] Portfelj dobi pregled »X od Y instrumentov ima svežo analizo«, zadnjo oceno, čas, čakalno vrsto in odpiranje analize; izračun pokritosti na strežniku nad celotnim portfeljem. Podatek za ta pogled doda `GET /portfolio/analyses`, ne N posameznih zahtev iz brskalnika.
- [ ] Regeneriraj OpenAPI/TS; dodaj `automation` v whitelist. Preveri tipkanje, lint, i18n, web teste, e2e na namizju/telefonu in temno temo. Posodobi DESIGN SCR-06/08/11. Commit `feat(settings): manage process windows and analysis automation [BL-166]`.

## Faza C — dividende z dokazljivimi podatki

### BL-167: Uvoz dividendnih denarnih dogodkov iz Flex

**Datoteke:** novi `services/api/preza/domain/dividends.py`, `services/api/preza/services/dividends.py`, `services/api/tests/test_dividends.py`, očiščeni XML fixture v `services/api/tests/fixtures/`; spremeni `broker/flex.py`, `domain/portfolio.py`, `models.py`, `services/portfolio.py`; nova migracija.

**Pogodba:** `DividendCashEventIn` vsebuje račun, stabilen broker transaction ID, tip dividend/withholding/reversal/payment_in_lieu, instrument ID ali nerešeno referenco, valuto, podpisan `amount: Decimal`, knjižni dan, povezan izvirni dogodek, `source`, `as_of`. `FlexStatement` dobi `dividend_events` s privzetim praznim seznamom za združljivost.

- [ ] Najprej pridobi očiščen reprezentativen Flex izvoz s CashTransactions: dividenda, davčni odtegljaj, storno, različne valute. Preveri nastavitve Flex Query in dejanska imena polj. Brez realnega vzorca se lahko napiše adapter/test, ne pa trdi, da je živ uvoz potrjen.
- [ ] Testi dvakratnega uvoza istega obdobja, naknadnega popravka/storna, dveh računov, manjkajoče instrument reference in odtegljaja brez ujemanja. Broker ID + račun sta idempotentna ključa; brez ID uporabi dokumentiran konservativen ključ in zaznaj kolizijo, ne briši dogodkov tiho.
- [ ] Hrani posamezne dogodke, ločeno bruto/odtegljaj/neto. Neto = bruto + podpisani povezani odtegljaji; manjkajoč odtegljaj ne dokazuje ničelnega davka. Nepovezane dogodke pokaži za pregled. Storno pobota izvirni dogodek, ne izbriše sledi.
- [ ] Evidentiraj pokrito obdobje uvoza; odsoten CashTransactions razdelek je »ni podatkov«, ne dokaz nič dividend. Pretekla izplačila prodanih instrumentov ostanejo v evidenci.
- [ ] Preveri `uv run pytest tests/test_flex.py tests/test_api_m1.py tests/test_dividends.py -q` ter nadgradnjo migracije na prazni in obstoječi bazi; commit `feat(portfolio): import dividend cash events from Flex [BL-167]`.

### BL-168: Dividendni API in pogled znotraj Portfelja

**Datoteke:** nova `services/api/preza/routes/dividends.py`, `apps/web/components/portfolio/PortfolioDividends.tsx`; spremeni `main.py`, `services/dividends.py`, `app/portfolio/page.tsx`, hooks/tipi, sporočila; novi API/komponentni testi in `apps/web/e2e/dividends.spec.ts`.

**Pogodba:** `GET /portfolio/dividends?year=2026&account_id=...&symbol=...` vrne prejeta izplačila, mesečni pregled, vsote po valuti, obdobje pokritosti, nerešene povezave in metapodatke. Ločen `GET /portfolio/dividends/forecast` vrne samo potrjene bodoče dogodke z virom ali označene ocene; manjkajoč vir pomeni prazen/neznan forecast.

- [ ] Testi vsot z `Decimal`, negativnega popravka, več valut brez FX, neznanega neta, prodanega instrumenta in akumulacijskega ETF. Prejete dividende in prihodnja pričakovanja imajo ločene strukture in nikoli skupnega seštevka.
- [ ] Prva uporabna različica: kartice prejetega bruto/znanega odtegljaja/znanega neta, mesečni graf, tabela izplačil, filtri leta/računa/instrumenta in povezava na instrument. Kjer podatki niso popolni, prikaži delno pokritost namesto navidezno točnega skupnega neta.
- [ ] Prednostno vsote po originalni valuti. Skupni EUR samo za dogodke z dokazljivim zgodovinskim FX po knjižnem dnevu; manjkajoče pretvorbe izloči in navedi pokritost. Trenutni FX portfelja ni zgodovinski FX dividend.
- [ ] Prihodnji koledar samo ob potrjenem viru ex/pay datumov; sicer »Podatki o prihodnjih izplačilih niso na voljo«. Donosnost iz profila ni datum izplačila. Letna indikativna ocena iz donosa in vrednosti pozicije je neobvezna poznejša razširitev z jasno metodo/časom, ne obljuba prihodnjega neto prihodka.
- [ ] Za akumulacijski ETF ne izmišljaj denarnega izplačila; yield-on-cost in davčne napovedi ostanejo zunaj prve izdaje. Vsa aritmetika v determinističnem servisu.
- [ ] Preveri API/komponentne/e2e teste, brez-podatkov stanje in mobilni prikaz; posodobi DESIGN SCR-08. Commit `feat(portfolio): add source-backed dividend view [BL-168]`.

## Faza D — združitev in prevzem

Pred končnim prevzemom izvedi še spodnji samostojni sklop Watchliste (BL-170/171). Številčenje sledi dodajanju zahtev, ne vrstnemu redu izvedbe.

### BL-170: Podatkovna pogodba za bogatejšo Watchlisto

**Datoteke:** `services/api/preza/domain/portfolio.py`, `services/api/preza/services/watchlist.py`, `services/api/preza/fundamentals/finnhub.py`, po potrebi nov adapter vira z README; novi `services/api/tests/test_watchlist_metrics.py`, fixture v `tests/fixtures/`, obstoječi `test_fundamentals_finnhub.py`, `test_api_m1.py`.

**Vmesnik:** razširi `WatchlistOut` z `instrument_id`, `currency`, `price_as_of`, `price_source`, `day_change_pct`, `metrics: dict[str, WatchlistMetric]`. `WatchlistMetric` ima `value` kot decimalni niz ali null, `unit: ratio|percent|currency_per_share`, `currency` za denarni podatek, `basis` (TTM/indicated_annual/last_payment/forward_fiscal_year), `period_end`, `source`, `as_of`, `availability: available|missing|not_applicable|stale`. Stabilni ključi: `pe_ttm`, `forward_pe`, `dividend_per_share`, `dividend_yield_pct`, `payout_ratio_pct`, `fcf_yield_pct`, `roe_pct`, `net_margin_pct`, `revenue_growth_pct`, `debt_to_equity`.

- [ ] Najprej pogodbeni testi: zadnja cena in valuta; dve zaključni ceni za dnevno spremembo; P/E TTM ni forward P/E; dividendni znesek ima valuto/osnovo; pravilen faktor odstotkov. Poziv modelu ni vir teh vrednosti.
- [ ] Preveri dejanska polja vira za forward P/E in dividendo na delnico z očiščenim vzorcem. Brez vira ne računaj forward P/E iz preteklega EPS in ne pretvarjaj donosa v navidezno izplačano dividendo. Če sta potrebna cena in pričakovani EPS, izračunaj deterministično, shrani oba vira/časa/obdobje ter preveri EPS > 0.
- [ ] Obstoječe metrike mapiraj v pogodbo brez spremembe pomena. Finnhub trenutni fallback med indiciranim in TTM dividendnim donosom mora ohraniti, katera osnova je bila dejansko uporabljena. Novi metapodatki se shranijo pri ingestu; ne dopisuj današnjega datuma staremu podatku.
- [ ] Za ETF podjetniške metrike označi kot neuporabne, dokler ni namenskega vira portfeljskega P/E; distribucija ETF je lahko izdajateljev podatek, ne samodejno Finnhub podjetniški yield. Akumulacijski status brez potrjenega vira ni dokaz ničelne dividende.
- [ ] Razširi obstoječi `GET /watchlist` z združljivimi polji, paketnim branjem cen/fundamentov in obstoječimi pravili vrstnega reda. Brez ponudniškega ali LLM klica na GET, brez ločenega fundamentalnega requesta za vsako vrstico. Test števila poizvedb nad 50 instrumenti mora pokazati omejeno število branj, ne linearnega N+1 za metrike.
- [ ] Za denarne metrike ohrani `Decimal`/numeric ali decimalni niz v JSON; razširitev metapodatkov v obstoječem JSONB ne zahteva nove SQL kolone, sprememba sheme tabele pa zahteva novo migracijo. Testi pokrijejo zastarel, manjkajoč, ničeln in negativni vhod, ničeln EPS ter mešane valute.
- [ ] Preveri `uv run pytest tests/test_watchlist_metrics.py tests/test_fundamentals_finnhub.py tests/test_api_m1.py -q`, ruff in mypy, nato izvozi OpenAPI. Commit `feat(watchlist): expose sourced valuation and dividend metrics [BL-170]`.

### BL-171: Izbirni stolpci Watchliste in manjša navpična dejanja

**Datoteke:** `apps/web/components/watchlist/WatchlistPanel.tsx`, novi `WatchlistTable.tsx`, `WatchlistColumnPicker.tsx`, `WatchlistRowActions.tsx`, `apps/web/lib/watchlist-columns.ts`, hooks/tipi, SL/EN sporočila; novi komponentni testi in `apps/web/e2e/watchlist.spec.ts`; dokumentacija DESIGN SCR-08/CMP.

**Vmesnik:** `WatchlistViewPreferences = {version: 1, columns: WatchlistColumnId[], density: "comfortable" | "compact", sort: {column: WatchlistColumnId, direction: "asc" | "desc"} | null}`. Stabilni stolpci so navedeni v enem registru z i18n ključem, oblikovanjem, podatkovnim ključem in uporabnostjo za vrsto instrumenta. `symbol` in `actions` sta obvezna; osnovni vrstni red in privzeti izbor sta definirana zgoraj.

- [ ] Najprej testi: izbor stolpcev spremeni prikaz, prestavitev spremeni vrstni red, ponovni obisk ohrani izbor, pokvarjena/stara nastavitev pade na privzeto, obveznih stolpcev ni mogoče izklopiti. Profil »Dividende« vključi znesek na delnico z osnovo in dividendni donos.
- [ ] Dodaj gumb »Stolpci«, potrditvena polja, prestavitev levo/desno z dostopnimi gumbi, prednastavitve in »Ponastavi«. Prva izdaja shrani nastavitve v versioniran localStorage ključ `preza.watchlist.columns.v1`; to velja za ta brskalnik. Sinhronizacija med napravami je ločena poznejša zahteva. Branje šele na odjemalcu, brez hidracijskega neskladja.
- [ ] Uvedi tabelo na namizju s stabilnim simbolom in ozkim desnim stolpcem dejanj. Gumbi so navpični po predlogu gostote; ohrani pregledano, premik med ravnema in odstrani/razveljavi. Dejanje med pending onemogoči, napako pokaži v prevodu; klik dejanja ne odpre instrumenta.
- [ ] Razvrščaj številčno nad decimalnimi vrednostmi, ne po lokaliziranih nizih; manjkajoče vrednosti na koncu v obe smeri, izenačene po instrument ID. Denarnih vrednosti različnih valut ne razvrščaj kot enotne kupne moči; grupiraj po valuti ali onemogoči globalno denarno razvrščanje z razlago. Ohrani aktivno/zalogovno skupino, opombo in hitro dodajanje.
- [ ] Ob podatku omogoči vpogled v vir, čas, osnovo in zastarelost; ne pretvori `missing` v 0. Na telefonu preveri razširitev dodatnih metrik in dostopnost dejanj brez odrezanih gumbov; namizna tabela lahko uporablja horizontalni scroll.
- [ ] Regeneriraj tipe API, nato web lint/typecheck/i18n/unit in Playwright watchlist na desktop/telefonu, vključno s shranjevanjem izbora ter odstranitvijo/razveljavitvijo. Posodobi DESIGN šele ob izvedbi. Commit `feat(watchlist): add configurable columns and compact row actions [BL-171]`.

### BL-169: Integracija, dokumentacija in uporabniški prevzem

- [ ] Po uskladitvi z aktivnim podagentom vključi zaključene sklope v vrstnem redu A → B → C. BL-163 se lahko dostavi samostojno; C se lahko začne po potrjeni dividendni pogodbi. Ne sprožaj paralelnih urejanj skupnih models/hooks/messages/migracij.
- [ ] Dokumentiraj ADR za izbiro politik v bazi/semantiko pavze in kvote ter ADR za dividendno evidenco, ko sta odločitvi sprejeti. Posodobi README storitev, `.env.example` samo za potrebne nove neskrivne privzete vrednosti, DESIGN, BACKLOG in SESSIONS.
- [ ] V `services/api`: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`. `TEST_DATABASE_URL` mora kazati na izolirano pravo testno bazo; preskočeni DB testi niso dokaz delovanja.
- [ ] V `services/agents`: `uv run pytest -q`, `uv run ruff check .`, `uv run mypy` po konfiguraciji paketa. Fiksne regresije ostanejo zelene.
- [ ] Izvozi `uv run python -m preza.cli.export_openapi openapi.json` v API, nato iz korena `pnpm --filter web gen:api`, `pnpm --filter web i18n:check`, `pnpm --filter web lint`, `pnpm --filter web typecheck`, `pnpm --filter web test`, `pnpm --filter web build`. Preglej generirani diff.
- [ ] Po navodilih web README zaženi Playwright proti testnemu stacku; preveri proposals/analysis/settings/dividends/portfolio/watchlist, SL/EN, telefon in temno temo. Ponovi tudi obstoječe e2e zaradi novih zavihkov, izbirnih stolpcev in privzetih filtrov.
- [ ] Preizkus integracije: spremeni politiko brez restartov → en termin → en paket → kvota → pavza med čakanjem → nadaljevanje v naslednjem oknu → rezultati; ponovi z nedosegljivim Redis in dvema workerjema. Ločeno preveri Flex dividendni uvoz dvakrat in enako vsoto.
- [ ] Pred vključitvijo v produkcijo preglej migracije, varnostno kopijo baze in način povrnitve. Začni z avtomatiko izklopljeno; vklop s konkretnim urnikom je izrecna uporabniška odločitev. Predaj stanje, rezultate preverjanj in odprte omejitve; ne trdi, da testi zagotavljajo kakovost finančne presoje modela.

## Predlagana prioriteta in odprte odločitve

1. Najprej BL-161/162 in BL-163: zanesljivi Predlogi ter uporaben seznam analiz.
2. BL-170/171: bogatejša Watchlista in kompaktna dejanja; samostojno dostavljiv sklop brez čakanja na avtomatiko ali dividendno evidenco.
3. Nato BL-164–166: nadzor obremenitve in avtomatske analize.
4. Nato BL-167/168: dejansko prejete dividende; prihodnji koledar samo z ustreznim virom.
5. BL-169 zapre celoto, vključno z BL-170/171. Aktivni OpenCode podagent se ne prevzema ali preusmerja samodejno.

Za pregled zasnove: potrditi prioriteto sklopov, umestitev dividend v Portfelj in obseg prve dividendne izdaje (prejeto, z možnostjo prihodnjih dogodkov šele ob dokazljivem viru). Konkretnih urnikov ni treba izbrati pred razvojem; nova avtomatika ostane izklopljena.

**Samopregled načrta:** zahteve imajo lastnike BL-161–171; preverjena skladnost API imen, politike ročnih/avtomatskih zagonov, kvote, zgodovinskih posnetkov, ID-jev instrumentov ter ločitve prejetih/napovedanih dividend. Živa napaka modela, dejanski dividendni Flex format in ponudniški polji forward P/E/dividenda na delnico ostajajo dokazne točke za izvedbo, ne domnevno rešena dejstva.
