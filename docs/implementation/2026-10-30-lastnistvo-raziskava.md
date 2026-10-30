# S-G1 A3/A5: dokaz lastništva in živosti

2026-10-30. Samo statična raziskava za naslednjo pogodbo SG-01/02/05–08. Pregledana osnova `21a0b3d187c17be0919f43f67fb2d29e5fdd7da0`; brez sprememb kode, zagona testov, povezovanja na bazo/Redis/ponudnike ali branja skrivnosti. Ta zapis ni dokaz odprave A3 ali reprodukcije A5.

## Ugotovitev

V sedanji kodi **ni avtoritativne trajne identitete instance delavca** in ni njenega dokaza prenehanja. `job_id`, arq `in_progress`, iztečen heartbeat in nov zagon drugega workerja tega ne nadomestijo. Engineering lahko izbere in preveri novo pogodbo; uporabniku ni treba izbirati lease sheme ali interpretacije TTL.

Najmanjši smiseln naslednji korak je skupna storitev lastništva z dvema tipiziranima FK tabelama za delo in ločenim registrom instanc. Pred prvim dispatchom je iztečeno pravico mogoče odvzeti s CAS brez trditve, da je stari proces mrtev. Po dispatchu isti run/review ne dobi novega plačljivega ownerja. Dokler ni potrjen konec stare izvedbe, ostane poslovni status nespremenjen in diagnostika označi `recovery_pending`.

## Kaj obstoječi dokazi pomenijo

| Dokaz v kodi | Dejanski pomen in meja |
|---|---|
| `services/api/preza/services/analyses.py:15–16,78–82` | `analysis:<run_id>` je deduplikacijski ključ oddaje, ne identiteta procesa ali prevzema. |
| `services/agents/preza_agents/worker.py:237–270` | Analiza zavrne samo done/failed; ponovno dostavljen running znova sestavi snapshot in začne delo. Ni row-lock/CAS prevzema ali dispatch markerja. To je statična podlaga A3. |
| `services/agents/preza_agents/worker.py:444–490` | `_job_alive` enači queued/deferred/in_progress z živostjo. Sweep poleg starosti zahteva samo odsotnost teh stanj, nato piše failed. To ni dokaz smrti konkretne instance in ni fencing. |
| `services/api/preza/models_automation.py:42–60`; `services/api/preza/automation_worker.py:58–80` | ProcessExecution ima en `heartbeat_at`, ki se posodobi na 30 s po `id/state`. Nima tokena posameznega prevzema ali instance. |
| `services/api/preza/automation_worker.py:82–111`; `services/agents/preza_agents/worker.py:525–565` | Parent batch/discovery samo odda otroška opravila. Parent sme že biti done, medtem ko otrok še čaka/teče. Njegov heartbeat ni heartbeat analize/review. |
| `services/api/preza/services/automation.py:477–529` | `review_gate` dovoljuje parent running/done. `dispatch_review_ids` v JSON counts beleži zgodovino dovoljenja te izvedbe, ne živosti executorja. None nima niti te povezave. |
| `services/agents/preza_agents/thesis_tracker/runner.py:60–78` | Po dispatchu drug execution ohrani running; isti durable execution pa sproži `_fail(unknown=True)` brez dokaza, da prejšnja instanca ne teče. Nov executor in stari živi executor z istim execution_id nista ločena. To je cilj A5, še brez zahtevane reprodukcije. |
| `services/api/preza/services/thesis_reviews.py:262–288,291–333,336–352` | Dispatch je pod zaklepom, vendar finalize/fail preverjata samo poslovno stanje, ne owner tokena/generacije. Terminalni check prepreči del ponovitev, ne dokazuje veljavnega writerja. |
| `services/agents/preza_agents/worker.py:514–520,569–590` | Startup pripravi odjemalca in mapo; WorkerSettings ne registrira instance/ownerja ali ustavitvenega dokaza. `max_jobs=1` velja na proces, ne na celoten sklad. |

Nameščeni arq je pregledan samo z branjem datotek pod:

`C:/Users/Jan/Documents/Claude-autotrading/.claude/worktrees/preverjanje-podatkovnih-povezav-53ab37/services/agents/.venv/Lib/site-packages/arq/` (v nadaljevanju `ARQ/`). `ARQ/version.py:2` in oba lockfile (`services/api/uv.lock:63–64`, `services/agents/uv.lock:96–97`) navajajo **0.28.0**. To ni dokaz verzije slike v živem skladu.

| arq dokaz | Posledica |
|---|---|
| `ARQ/jobs.py:152–169` | `status()` bere obstoj result/in-progress ključev in score vrste. Ne preveri procesa ali njegovega tokena. `not_found` ne pomeni dokazano mrtev worker. |
| `ARQ/worker.py:275–277,449–465` | In-progress ključ vsebuje `b'1'` z enkratnim TTL največjega timeouta +10 s. To je rezervacija, ne osveževan per-instance heartbeat. Pri teh nastavitvah se izračuna iz 3 h timeouta. Mrtev proces lahko pusti ključ; izguba Redis ključa ne ustavi živega procesa. |
| `ARQ/worker.py:255–259,773–785` | Privzeti health ključ je skupen za queue in vsebuje števce; več instanc ga lahko prepisuje. Ne veže runa na instanco. |
| `ARQ/worker.py:576–585` | Job ctx vsebuje job_id/job_try/enqueue_time/score, ne trajne identitete instance. Hooki so na voljo, aplikacija jih za lastništvo še ne uporablja. |
| `ARQ/worker.py:595–627,852–877` | Cancellation se lahko ponovno dostavi. `close()` počaka na arq tasks in nato kliče on_shutdown, vendar samo cancellation zahteva ni dokaz, da so vsi ločeno ustvarjeni otroci ustavljeni. |

Posebna meja: analiza ustvari `asyncio.ensure_future(work)` (`worker.py:316–319`) in ga nima v `finally` z `cancel()` ter `await`. Preklic parenta med `asyncio.wait` sam ne zagotovi konca otroka. Za dokaz nadzorovanega zaključka je treba zajeti tudi ta task, vse njegove podklice in transport; sicer je zanesljiv šele potrjen izhod celotnega procesa. Izhod procesa še vedno ne dokazuje, da ponudnik ni obdelal že poslanega HTTP.

## Predlagana trajna pogodba

### Shema za engineering pregled

Predlagam **`analysis_work_lease` + `thesis_review_work_lease`** in skupno implementacijo operacij. Polimorfni `(work_kind, work_id)` brez pravih FK zahteva dodatne ročne kontrole ob vsakem ustvarjanju/brisanju. Dve tabeli sta pri dveh že znanih tipih manjša skupna dokazna površina; en skupen helper prepreči razhajanje semantike.

Obe lease tabeli imata naslednja polja (vsi datumi `timestamptz`, vedno DB čas):

| Polje | Tip / pravilo |
|---|---|
| `run_id` oziroma `review_id` | UUID PK in FK na pravi parent z `ON DELETE CASCADE`. |
| `owner_token` | UUID NOT NULL; nov pri vsakem dovoljenem prevzemu, tudi znotraj iste instance. |
| `generation` | BIGINT NOT NULL, CHECK >0; začne pri 1, poveča samo ob dovoljenem prevzemu pred dispatchom. |
| `worker_instance_id` | UUID NOT NULL FK na register, `ON DELETE RESTRICT`. |
| `execution_id` | UUID NULL FK na ProcessExecution, `ON DELETE RESTRICT`; sled izvora/dovoljenj, ne dokaz ownership. |
| `state` | VARCHAR(16), CHECK `active|released`; poslovni izid ostane v run/review. |
| `acquired_at`, `heartbeat_at`, `lease_until` | NOT NULL; CHECK lease_until >= heartbeat_at in heartbeat_at >= acquired_at. |
| `first_dispatch_at` | NULL do prvega commit dovoljenja za HTTP; nato nespremenljivo. |
| `released_at`, `terminal_reason` | NULL za active; released zahteva released_at in varno reason kodo. |
| `recovery_pending_at`, `recovery_reason` | NULL ali diagnostični čas/koda; ne spreminjata poslovnega statusa ali lastnika. |

Indeks za bounded recovery `(lease_until, run_id/review_id) WHERE state='active'`. `released` vrstice ostanejo kot sled in se ne uporabljajo za novo generacijo po dispatchu. Pri review je obstoječi `dispatch_at` v isti transakciji enak `first_dispatch_at`; ne ustvariti dveh neodvisnih resnic. Pri analizi snapshot ob prvem shranjevanju postane nespremenljiv; novi pred-dispatch owner uporabi isti snapshot ali ga prvič pripravi, ne prepiše obstoječega.

Register **`worker_instance`**:

- `id UUID PK` je naključen instance token ob vsakem zagonu procesa; ne ime gostitelja, PID ali queue.
- `queue_name VARCHAR(80) NOT NULL`, `started_at/heartbeat_at TIMESTAMPTZ NOT NULL`.
- `state VARCHAR(16) CHECK active|draining|stopped`, `stopped_at TIMESTAMPTZ NULL`.
- `stop_proof_kind VARCHAR(32) NULL`, `stop_proof_ref TEXT NULL`; `stopped` zahteva čas in dokaz. Sprejemljiva kind sta `local_tasks_drained` in `supervisor_process_exited`. Ref je varna identiteta dogodka/instance, brez skrivnosti.
- Heartbeat vsakih 20 s po DB uri; lease 120 s sta začetna tehnična predloga iz SG-05, ne dokaz smrti po 120 s. Heartbeat registrarja in konkretnega dela sta ločena.

V najmanjšem prvem rezu `supervisor_process_exited` ni avtomatsko na voljo: repo nima preverjene integracije nadzornika. Podpora za ta dokaz ostane izklopljena do testa povezave na **točno instanco**. Novo `started_at` ali isti container/slot name ne sme sam označiti prejšnje instance stopped. Registracija sama torej ne reši trdega padca: stale+active ostane neznan do nadzorovanega dokaza.

### Pravila prevzema, dispatcha in obnove

1. Atomarni claim naj zaklene parent in lease v doslednem vrstnem redu, preveri gates ter pridobi nov token. Začetni duplicate nikoli ne osveži heartbeat starega ownerja. Veljaven active owner pomeni povratek trenutnega stanja brez zapisov poslovnih podatkov ali HTTP.
2. Pred prvim dispatchom iztečen lease lahko dobi novo generacijo s CAS nad točnim `(owner_token,generation,lease_until,first_dispatch_at IS NULL,state)`; stari owner ni razglašen za mrtvega, izgubi pa pravico do nadaljnjih zapisov/dispatcha. Ne pretvarjaj odsotne stare sledi v dokaz, da HTTP ni bilo.
3. Vsak dejanski modelni HTTP poskus mora v kratki transakciji preveriti token/generacijo/active owner in gates. Prvi zapiše `first_dispatch_at` ter commit **pred HTTP**. Naslednji koraki in JSON poprava iste žive verige so dovoljeni samo istemu ownerju. Čez HTTP ni odprte DB transakcije.
4. Izpad DB, izgubljen heartbeat task ali izgubljen owner ustavi nadaljnje poskuse; zanesljivo cancel+await tudi otroške taske. Pravkar poslani HTTP lahko ostane negotov. Pred-dispatch dirko linearizira CAS: če stari owner prvi commit-a dispatch, takeover ni dovoljen; če takeover zmaga, stari dispatch CAS ne uspe.
5. Po zapisanem dispatchu ni novega plačljivega ownerja istega dela. Ob stale heartbeat je dovoljeno samo diagnostično `recovery_pending`. Za terminal unknown je potreben `stopped` dokaz za točen worker token oziroma lokalno potrjen konec konkretne stare izvedbe; nato recovery v eni transakciji znova preveri iztek, token/generacijo in dokaz. Obnovljen heartbeat tik pred CAS mora povzročiti no-op.
6. Pri normalnem zaključku owner atomarno objavi rezultat/usage/korake/signale in released lease. Vsak stale finalize/fail vrne konflikt/no-op brez side effectov. Recovery ima ločeno omejeno operacijo zaključka s preverjenim dokazom, ne splošnega obvoda tokena.
7. Analysis unknown uporablja `failed` + varno kodo `dispatch_outcome_unknown`; ThesisReview `failed_unknown`. `AnalysisStatus` in String(10) ne podpirata failed_unknown (`domain/analysis.py:13–17`; `models.py:386`). Poraba ostane znana/spodnja meja/unknown; dispatch marker ni dokaz dejanskega stroška ali ničle. `used_today()` trenutno izloči vse failed (`services/analyses.py:19–25`); plan mora ohraniti rezervirano kvoto za negotov plačljivi dispatch, da unknown ne ustvari lažne proste kvote.

Dokaza prenehanja ne proizvajajo: TTL, izguba Redis ključa, parent ProcessExecution interrupted/done, arq retained result, sama cancellation zahteva ali registracija nove instance. `automation_tick` danes celo označi ProcessExecution interrupted samo po 10-minutnem heartbeat pragu (`automation_worker.py:145–156`); tega se ne sme uporabiti kot smrtni dokaz za otroka.

## Writerji, ki morajo dobiti CAS/fencing

| Writer / meja | Zahtevana sprememba pogodbe |
|---|---|
| `worker.py:237–270` | Analysis claim/running/start/snapshot z owner tokenom; preprečiti prepis že shranjenega snapshota. |
| `worker.py:90–120,317–331,364–385` | Sekvence in vsak flush AnalysisStep, failure cleanup, usage, kartica, poročila, rating ter done pod istim ownerjem. PK run/seq sam ne nadomesti fence. |
| `worker.py:449–484` | Sweep ne zaključuje samo po arq statusu; bounded kandidati in pogojna ponovna preverba lease/worker dokaza. |
| `thesis_tracker/runner.py:60–90,95–122,159–169` | Ne enačiti execution_id z ownerjem; token mora priti do dispatch/finalize/_fail in vsakega HTTP poskusa, tudi popravnega. |
| `services/thesis_reviews.py:214–288,291–375,376–450` | Reservation ostane enolična; dispatch/fail/finalize/stale in objava predlogov/Signal morajo deliti owner check in transakcijo. Zaklepni vrstni red naj ohrani obstoječi thesis → review zaklep. |
| `services/automation.py:507–529` | JSON seznam je samo provenance; ne uporablja se več za dokaz, da sme drugi executor zaključiti review. |
| `automation_worker.py:58–67,112–137,145–156`; `services/automation.py:177–202` | Parent heartbeat/finish/interrupted niso child owner. Če se v poznejšem rezu omogoči ponovno prevzemanje samega ProcessExecution, tudi ti writerji potrebujejo svoj token; v tem rezu ga ne uvajati posredno kot recovery dokaz. |
| `llm/client.py:161–188`, `llm/automatic.py:21–38`, agents `budget.py:146–174` | Owner guard mora doseči vsako HTTP ponovitev, vključno z ročnimi analizami. Sestaviti obstoječi A1/A2 guard z owner guardom; ne nadomestiti switch/manual dovoljenj. Guard samo okoli logical `complete_json` je prešibek. |
| `services/analyses.py:41–82`, `services/automation.py:442–447`, `worker.py:525–565` | Proizvajalci ohranijo trajni namen in dedup ID. Ne smejo popravljati running ownerja ali resetirati dispatcha. |
| `cli/seed_demo_analysis.py:141–154`, `cli/seed_demo_theses.py:29` | Demo ustvari/izbriše sintetične parent vrstice; FK cascade in omejitev na demo morata preživeti. Seed ni runtime recovery. |

Ni potrebe razširiti lease v SMTP sending/unknown pogodbo, broker ali vsak ingest proces. Raziskava ne predlaga ponovne izvedbe A1/A2/A4.

## Migracija in dokazna vrata

Nova migracija **0021, down_revision 0020**, če je ob začetku izvedbe 0020 še head; sicer naslednji prosti head brez spreminjanja zgodovine. Ustvari register, tipizirani tabeli, FK/CHECK/indekse. Ne backfill-a živih lease ali izmišljenih dispatch dovoljenj. Stari running brez nove sledi ostanejo posebej inventarizirani in recovery pending, nikoli samodejno queued; odsoten dispatch marker stare analize pomeni unknown, ne dokaz »nikoli poslano«. Downgrade ne sme med aktivnim delom tiho odstraniti varoval. Dodatni stolpci/API za varno unknown kodo zahtevajo regeneracijo OpenAPI/TS, če se pogodba razširi.

Potreben dokaz pred odvisno izvedbo/zaključkom:

1. **F-G01/A3:** dve dejanski executor instanci z različnima tokenoma, tri DB povezave/bariera, isti run. Prvi obstane pred fake HTTP; redelivery ne spreminja snapshota/steps/statusa/usage in ne pošlje dodatnega HTTP. Isti procesni max_jobs ni dovolj.
2. **F-G03/A5:** ista durable execution_id, različna owner tokena; stari fake HTTP še teče. Drugi ne sme fail-ati živega ownerja. Nato drug execution_id + dokaz exact-instance stopped ter stale lease → failed_unknown brez novega modela. To je zahtevana reprodukcija A5, ki je sedanji mock testi ne dajejo (`tests/test_thesis_review_worker.py:132–149`).
3. **F-G02/F-G04:** padec po commit dovoljenja, pred fake HTTP in med njim; po dokazanem izhodu unknown, nič novega HTTP. Ločeno padec pred markerjem → ena nova generacija, staremu tokenu prepovedani dispatch/flush/finalize/fail.
4. **Bariera heartbeat tik pred CAS:** recovery prebere starega kandidata, prvi obnovi heartbeat in lease, recovery ponovno preveri ter ne spremeni statusa. Dodati stale-token heartbeat, zakasnjen DB commit in dva recovery executorja.
5. **Motnje:** DB/Redis nedosegljivost, izginul in-progress ključ, še prisoten ključ po smrti, star queue health, zgolj nov worker start → nobena sama ne terminalizira živega ownerja. Fake ura razlikuje DB čas od ure procesa.
6. **Cleanup:** prekliči arq parent analize med čakanjem na ensure_future; pokaži, da otrok do konca nadzorovanega drain-a ne more več poslati HTTP ali objaviti rezultata. Stopped zapis nastane šele po tem. Supervisor adapter mora dokazati exact instance/container generation, ne samo ponovno uporabo imena.
7. **Obseg:** normalna delniška/ETF veriga, ročni/avtomatski review, JSON poprava, normalni failure in terminalni redelivery; fake štetje HTTP/usage/kvote/Signal, obstoječa A1/A2/A4 regresija. Migracija iz 0020 in FK brisanje na izolirani bazi. Brez pravih ponudnikov, SMTP ali brokerja.

## Kaj še potrebuje uporabnika

Za izbiro sheme, CAS pravil, testnih konstant in izolirano reprodukcijo **ni novega uporabniškega vprašanja**. Engineering mora najprej dokazati lifecycle hooke in izbrani dokaz prenehanja. Če exact-instance hard-crash dokaz v okolju ni na voljo, naj contract izrecno ohrani recovery pending; to je tehnična meja, ne dovoljenje za poenostavitev v »stari heartbeat pomeni mrtvo«.

Dejanska odločitev uporabnika bi nastala šele ob pregledu konkretnih zgodovinskih negotovih del: ali dovoli **novo, ločeno plačljivo analizo**, potem ko je stara označena unknown in je prikazana možnost že nastale porabe. To nikoli ni samodejni retry istega work_id. Namestitev/živa migracija ostajata pod že obstoječimi ločenimi vrati potrditve in backup/restore; ta raziskava ju ne zahteva in ju ni izvajala.
