# S-G1 · Lastništvo, ponovna dostava in trajna oddaja

**Status: NEXT-SPEC / CONDITIONAL PROPOSAL.** 2026-10-30. BL-214; A3/A5/R1 iz BL-218; posebej BL-204. Shema lease in tehnične konstante spodaj so predlog za pregled/izvedbeni plan. Vezana varnostna pravila veljajo že zdaj. Dokument ne dokazuje odprave A3 ali reprodukcije A5.

Podlage: [neposredni SPEC §4–6/8](./2026-10-30-dodatni-krog-claude-spec.md), [R6](../plans/2026-10-30-dodatni-krog-claude-izvedba.md), [priprava SPEC](./2026-10-30-odprti-sklopi-priprava-spec.md). Statični ogled na osnovi `d0ceebf4cb28cb8919d23e00f2c419fa9c41d802`: `preza_agents/worker.py:deep_analysis` sprejme tudi running; `thesis_tracker/runner.py` že preverja dispatch owner; `ProcessExecution` ima heartbeat_at, vendar to samo po sebi še ni lease posamezne analize/review.

## 1. Ločene odgovornosti

1. **SG-01 / A3:** isti AnalysisRun, ponovno dostavljen drugemu executorju, ne sproži nove plačljive verige. `running` sam ne dokazuje niti živosti niti opustitve.
2. **SG-02 / A5:** opuščen ThesisReview po dokazanem izteku lastništva dobi sledljiv negotov terminalni izid; živega lastnika druga dostava ne zaključi. A5 potrebuje reprodukcijo z drugim executorjem in restartom.
3. **SG-03 / R1:** članstvo Radar pogleda se filtrira v SQL pred urejenim LIMIT; brez branja `limit*3` in naknadnega Python filtriranja.
4. **SG-04 / BL-204:** trajen request ID v osnutku prepreči novo oddajo ob reload/izgubljenem odgovoru. To ne nadomesti SG-01: sprejem predloga in prevzem že obstoječega run sta različni transakciji/testa.

A1/A2/A4 so neposredni popravki tega kroga: zahtevaj njihove rezultate T-A1/T-A2/T-A4 in širšo regresijo, **ne izvajaj jih znova v tem paketu**. Varovalo vsakega HTTP poskusa, ponovno preverjanje po zaklepu, manual dovoljenja ter bounded outbox s cursorjem morajo ostati ohranjeni. SMTP dostava ostaja v lastni sending/unknown pogodbi; lease analiz je ne razširi ali omogoči.

## 2. Predlog trajnega lastništva

**SG-05:** dodaj eno interno tabelo `work_lease`, ključ `(work_kind, work_id)` s work_kind `analysis|thesis_review`, `owner_token UUID`, `generation BIGINT`, `execution_id UUID NULL`, `acquired_at`, `heartbeat_at`, `lease_until`, `first_dispatch_at NULL`, `released_at NULL`, `terminal_reason NULL`. Datumi UTC/timestamptz. `work_id` je obstoječi AnalysisRun.id/ThesisReview.id; izvedba mora transakcijsko potrditi obstoj pravega tipa in ne puščati visečih lease ob brisanju. Če pregled izbere dve FK tabeli namesto polimorfnega ključa, mora ohraniti iste invariante in dopolniti migracijski plan pred kodo.

Predlagane konstante: heartbeat vsakih 20 s v ločeni async nalogi, lease 120 s po DB času, recovery največ 100 vrstic/tick po `(lease_until, work_kind, work_id)`. Preveri skladnost z dejanskim worker timeout/review skupnim rokom 660 s in časom zaključnega DB zapisa. Ne drži transakcije/row lock čez HTTP. Izpad heartbeat naloge ni dovoljenje za nov plačljivi dispatch.

`owner_token` določa posamezen worker prevzem, ne le ProcessExecution ID, ki je lahko ponovno dostavljen. Generation se poveča pri dovoljenem novem prevzemu pred prvim dispatchom. Kratke transakcije pod row lock/CAS preverijo token/generation. Vsi heartbeat, zapis dispatcha, koraka in končnega rezultata morajo ustrezati trenutnemu tokenu; izgubljeni owner ne sme dokončati rezultata nove generacije.

**SG-06, vezana omejitev:** pravica do prvega dispatcha se zapiše/commit pred transportom. Po zapisanem dispatchu opustitev pomeni negotov izid, tudi če je proces padel tik pred dejanskim HTTP. Ne obljubljaj exactly-once pri zunanjem plačljivem ponudniku. Noben timeout/restart/nov job ID sam ne dovoljuje slepe ponovitve. Accounting ostane znana poraba/spodnja meja/unknown; ne pretvori se v lažno 0.

## 3. Prehodi in recovery

| Izhodišče | Dogodek / dokaz | Dovoljeno dejanje |
|---|---|---|
| queued, brez dispatcha | Gate dovoljen, atomsko pridobljen lease | Isti worker preide v running, pripravi nespremenljiv snapshot in zapiše dispatch tik pred HTTP. |
| running, veljaven lease | Redelivery istega work_id, drug token/executor | Vrne trenutno stanje/»already owned« brez novega HTTP, brez spreminjanja run/lease/usage. |
| running, brez dispatcha | Lease dokazano opuščen, CAS uspe, gates ponovno veljajo | Varno nadaljevanje z novo generacijo; prejšnji owner izgubi pravico do dispatcha. |
| running, z dispatchom | Iztečen heartbeat/lease **in** dokaz mrtvega/starega workerja ali nadzorovano zaključena/preklicana stara izvedba; CAS ponovno potrdi iztek | Terminalni negotovi izid, brez HTTP. Nov executor ne prevzame iste plačljivega dela. |
| running | Heartbeat iztečen, živost/lastništvo še neznana, DB/Redis nedosegljiv ali še aktiven owner | Zabeleži recovery pending/diagnostiko zunaj poslovnega statusa; ne dispatchaj in ne zaključi dokazano živega ownerja. Sam heartbeat timeout ni dokaz smrti. |
| terminal | Ponovitev dostave/zaključka | Vrne isti izid; nič dodatnih korakov, signalov, kvote ali HTTP. |

**SG-07:** recovery preveri lease **in** pripadajoče trajno izvedbo/worker registracijo; arq job retention ali `running` vrstica sama nista dokaz živosti. Izvedbeni plan mora določiti, kateri obstoječi worker instance token/heartbeat je avtoritativni dokaz in kako ob restartu dokaže smrt prejšnje instance. Če tega dokaza ni, odvisni recovery ostane blokiran; ne izmisli ga iz časa začetka. Testna bariera omogoči heartbeat tik pred CAS in preveri, da recovery tedaj ne zaključi ownerja.

**SG-08:** AnalysisStatus trenutno dovoljuje queued/running/done/failed, `AnalysisRun.status` ima String(10). Zato AnalysisRun uporabi **status `failed` in varno reason/error kodo `dispatch_outcome_unknown`**, ne nepodprtega statusa `failed_unknown`. UI jo predstavi kot negotov izid brez samodejne ponovitve. ThesisReview lahko uporabi obstoječi `failed_unknown`/error_code, ob preverbi sedanjega terminalnega nabora. Rezultati ne spremenijo trditev teze brez uporabnikove potrditve. Sprejem/kvota starega run se ne porabi znova.

Za daljšo večkorakovno analizo lastnik pred vsakim naslednjim HTTP preveri aktualen lease in obstoječe A1 varovalo. Če lease med že začetim HTTP izgubi, transporta ni mogoče atomsko razveljaviti; odgovor je mogoče shraniti samo z veljavnim tokenom, sicer gre v diagnostično sled brez objave nove odločitve/signala. Iztek ni podlaga za avtomatsko ponovno analizo. Ročni nov run zahteva novo izrecno dejanje in običajno kvoto/politiko.

## 4. R1: SQL pogodba pogleda

**SG-09:** `services/api/preza/services/radar_views.py:list_events` najprej določi trenutne simbole zadnjih popolnih pozicijskih posnetkov oziroma aktivne watchliste. PORTFOLIO: SQL presek Event.symbols in held; WATCHLIST: presek z watched; DISCOVER: brez preseka z unijo. Nato time/status/min_score filter, `score DESC NULLS LAST, last_seen_at DESC, id DESC`, šele nato `LIMIT limit` v dovoljenem obsegu routes. Pri praznem held/watched zadevni pogled vrne prazno zbirko, DISCOVER vse upravičene; dogodek z več simboli se vrne enkrat.

To ohranja sedanjo simbolno semantiko Radarja; nov instrument identity join je izven minimalnega R1. Ne spreminjaj exact-ID detail poti za signal ali dogodek. Ne odpravljaj limita, ne uvajaj poizvedbe na dogodek ali ponudniških klicev. Potrebni indeks/EXPLAIN dokaz na sintetičnem naboru je del izvedbenega plana, ne razlog za neomejeno branje.

## 5. BL-204: osnutek in sprejem predloga

Statično izhodišče: `ProposalComposer.tsx` hrani osnutek `preza.proposal.draft.v1`, operation ID pa v pomnilniku; `routes/proposals.py:create` že serializira request_id z advisory lock, preveri vsebinski konflikt in uporablja request_id kot Proposal.id. Pogodbo strežnika ohrani in preizkusi; ne piši novega sistema sprejema po nepotrebnem.

**SG-10:** pred prvim POST atomarno shrani verzioniran lokalni zapis `{version, draft_id, fields, operation: {request_id, canonical_body, state, proposal_id?}, saved_at}`. Canonical body uporablja natančno strežniško normalizacijo simbolov in vključuje vsa poslovna polja; brez request_id/časa. Poslano vsebino po oddaji zamrzni ločeno od novega urejanega osnutka. Po reload »preveri/ponovi« uporablja isti request_id in isto poslano vsebino, ne ponovno ustvarjenega UUID.

Stanja: `editing → prepared → submitting → acknowledged`; timeout/izgubljen odgovor `→ outcome_unknown → lookup_by_request_id → acknowledged` ali ponovitev **istega** POST. Isti ID/druga vsebina `→ conflict`; uporabnik lahko odpre nov jasno označen osnutek/namero z novim ID. Sam reload, sprememba jezika, dvojni klik, queue failure ali 404 med nedokončanim commitom ne ustvarijo nove namere. Dva zavihka z istim draft/operation sta ista oddaja; neodvisni nov osnutek dobi nov draft_id.

**SG-11:** če lokalna shramba ni na voljo ali zapis odpove, UI pred oddajo pokaže omejitev in ne obljublja trajnosti čez reload; predlagano varno vedenje je blokirati trajno oddajo z možnostjo kopiranja vsebine, dokler ni zapis mogoče shraniti. Koruptiran v1 draft se validira; stare uporabne fields se obnovijo v nov editing draft, vendar brez izmišljanja starega operation ID. Ta odločitev o UX zahteva pregled pred izvedbo; ne spreminja strežniških varoval. Lokalna hramba ni večnapravna sinhronizacija ali varnostna kopija.

## 6. Migracije, fixture in vrata

SG-05 zahteva novo migracijo po aktualnem head (trenutni krog vključuje 0020), brez spreminjanja starih migracij. Stari running brez dokazljivega ownerja/dispatch sledi niso avtomatsko queued: inventura, unknown in ekspliciten recovery pregled. Backfill ne ustvari živih lease ali novega plačljivega dovoljenja. BL-204 lahko zahteva samo verzioniranje lokalne shrambe; sprememba API vedno regenerira OpenAPI/TS. Pred živo migracijo velja [S-F5](./2026-10-30-varnostne-kopije-restore-spec.md).

| Fixture / gate | Merljiva trditev |
|---|---|
| F-G01 / A3 | Dva dejanska executorja + DB bariera nad istim AnalysisRun → največ ena prvotna plačljiva veriga; redelivery živega ownerja 0 dodatnih HTTP in nič sprememb njegovega stanja. |
| F-G02 / A3 | Padec po commit dispatch, pred/med HTTP + restart → negotov terminalni izid, 0 novih HTTP; rezultat stare generacije se ne objavi. |
| F-G03 / A5 | Drug executor, iztečen review heartbeat, dokaz star-worker restart + CAS → failed_unknown brez modela; isti test z živim/obnovljenim heartbeat ownerjem ohrani running. To je zahtevana reprodukcija A5. |
| F-G04 / lease | Padec pred dispatchom → samo en novi owner; DB/network outage, heartbeat race in stale completion → brez dvojnega transporta/zaključka/signala. |
| F-G05 / A1/A2/A4 | Uvozi dokazne reference trenutnega kroga za switch pred JSON popravo, lock wait in bounded outbox/restart; regresija ostane zelena. |
| F-G06 / R1 | Več kot `limit*3` višje ocenjenih tujih dogodkov + en upravičen → SQL pogled ga vrne; dodaj prazno članstvo, dismissed, min_score, mešane simbole in stabilen tie-order. |
| F-G07 / BL-204 | Strežnik sprejme, odgovor izgine, reload in ponovitev → isti Proposal.id, ena analiza/kvota in nobena dodatna vrsta; Redis failure pozneje odkrije isti trajni namen. |
| F-G08 / BL-204 | Isti request ID/druga vsebina → 409 brez sprememb; dva zavihka/klik → ena oddaja; novo urejanje pomeni novo eksplicitno namero. |
| F-G09 / BL-204 | Storage failure, poškodovan stari zapis, SL/EN, telefon in Back → ni lažne obljube trajnosti ali izgube vidnega osnutka. |

Vrata: izolirani Postgres/API + agents concurrent testi s fake LLM in nadzorovano uro/heartbeat; ruff/mypy; web Vitest in Playwright samo :3100 za reload/lost-response/conflict. Dokaz vsebuje SHA, dva executor tokena, DB alias, barierni vrstni red in dejansko število HTTP/kvote, ne zgolj mock rezultata gate. Noben resničen model ali prejemnik.

**Odprto pred odvisno izvedbo:** avtoritativni dokaz worker živosti/prenehanja po restartu, pregled lease sheme in vseh writerjev, retry/UI koda za AnalysisRun unknown, potrditev lokalne storage-failure poti. Varna omejitev do takrat: negotovega dispatcha ne ponavljaj in ne zaključuj živega lastnika na podlagi running/iztečenega časa samega.
