# Nastavitve varnostnih kopij — izvedbeni plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** pripravljen dokumentarni predlog za BL-222, ne začeta implementacija. Vsi koraki spodaj so prihodnje delo. Uporabnik je določil nastavljivo pot/pogostost in dovolil isti disk; dejanske mape še ni izbral.

**Goal:** V SCR-11 omogočiti varno izbiro dovoljenega lokalnega cilja, pogostosti, hrambe, ročne kopije in jasnega statusa brez samodejne obnove.

**Architecture:** Politika in nameni so trajni SQL zapisi s revision CAS in deduplikacijo, Redis/arq je dostava. Omejeni ločeni backup worker uporablja obstoječo API/Python osnovo z združljivimi PG17 orodji, vnaprej priklopljen dovoljen root in omejeni povezavi za branje vira ter pisanje backup kontrolnih zapisov. API nikoli ne sprejema shell ukaza ali poljubnega host mounta; UI sledi sedanjemu Settings obrazcu in generiranim API tipom.

**Tech Stack:** Python 3.12, FastAPI/Pydantic v2, SQLAlchemy 2/Alembic, PostgreSQL 17/Timescale/pgvector, arq/Redis, Docker Compose, Next.js/React/TanStack Query/next-intl, pytest/Vitest/Playwright.

**Spec:** [S-F5a](../specs/2026-10-30-nastavitve-varnostnih-kopij-spec.md). Obvezen tudi [S-F5](../specs/2026-10-30-varnostne-kopije-restore-spec.md); samo njegova zahteva ločenega diska je nadomeščena z uporabnikovo izbiro istega diska. [S-H](../specs/2026-10-30-prevzem-in-prenos-spec.md) ostane nespremenjen.

## Global Constraints

- Privzeto `enabled=false`, `target_id=null`; do izbire cilja samo sintetični podatki/fake transport. Brez zasebnega Flex, poverilnic, žive kopije ali restore, :3000/:3100 sprememb in novih zunanjih povezav v tej pripravi.
- En izbran SQL source/target; urnik `manual|daily|weekly`, predlog `02:00 Europe/Ljubljana`, nedelja=6, retention 14 dnevnih +8 tedenskih, uporabniško nastavljivo. UTC zapisi, civilni urnik fold=0 in preskok neobstoječe ure.
- Isti disk je dovoljen, omejitev je jasno vidna. Ne trdi, da Docker volumen/mapa dokazuje fizično ločitev, ACL pomeni šifriranje ali hash pomeni uspešno obnovo.
- Samo vnaprej dovoljeni host root → container root; marker, varne podmape, ponovna preverba ob vsaki operaciji. Brez shell ukazov iz UI, Docker socketa, poljubnih mountov ali ponudniških poverilnic runnerja.
- Nova migracija za shemo, ne sprememba starih. Aktualni dokumentarni head je 0020; ob izvedbi preveri dejanski head in naslednjo prosto številko. Generirani OpenAPI/TS se ne urejajo ročno.
- Dokumentacija slovenščina; koda/komentarji/commiti angleščina; besedila samo SL/EN messages; posodobi DESIGN šele ob izvedeni UI spremembi. Brez samodejnih SMTP/Telegram obvestil.
- Plan ni dovoljenje za deploy, migracijo žive baze ali avtomatski restore. Sintetični restore ne odpre vrat za živo migracijo.

## Review Focus

- Nepriklopljen host cilj ne sme neopazno postati mapa v containerju; T2 pin-a mount/marker/path test pred pisanjem.
- Izgubljen odgovor, dva zavihka ali restart ne sme ustvariti dvojnega namena/finala; T1/T3 dokazujeta request_id in claim bariero.
- 02:00 ob DST, sprememba ure isti dan in downtime ne smejo povzročiti dveh avtomatskih kopij ali neskončnega catch-up; T3 preveri civilno identiteto in en nadomestni slot.
- Napaka po uspešnem rename in izgubljen SQL commit ne sme izgubiti dobre kopije ali povzročiti njenega prepisa; T2/T3 preverita filesystem/SQL uskladitev.
- Znižana hramba, nov target in tuji/pinned imeniki ne smejo sprožiti nenamernega brisanja; T4 pin-a natančen nabor dovoljenih brisanj, T5 jasno razliko checksum/restore.

---

## Datoteke in odgovornosti

Predlagane nove datoteke so majhne enote za ta obseg, ne splošna backup platforma:

| Datoteke | Odgovornost |
|---|---|
| `services/api/preza/domain/backups.py`, `models_backups.py` | Pydantic pogodbe/varne kode in SQL politika/nameni/preverbe. |
| `services/api/preza/services/backups.py`, `routes/backups.py` | Revision CAS, sprejem namena, statusi in omejeni REST brez dolgega dumpa. |
| `services/api/preza/backups/paths.py`, `archive.py`, `worker.py` | Dovoljeni root/probe, fixed argv dump/manifest/hash/retention ter omejen arq prevzem/urnik. Brez splošnega izvajalnika ukazov. |
| Nova migracija `services/api/migrations/versions/<datum>_<naslednja>_backup_settings.py` | Backup shema/FK/check/unique/indeksi po takratnem head. `migrations/env.py` registrira nove modele, če avtomatski import tega ne pokrije. |
| `services/api/preza/config.py`, `main.py`, API `Dockerfile`, `infra/docker-compose.yml`, `.env.example` | Neskrivne nastavitve/registracija routerja, backup build target in storitev z omejeno konfiguracijo. V .env.example le placeholders. |
| `apps/web/components/settings/BackupSettings.tsx`, `lib/api/backups.ts`, `components/settings/SettingsView.tsx` | Settings obrazec, API hooki in vključitev razdelka. |
| `services/api/openapi.json`, `apps/web/lib/api/schema.d.ts`, `messages/sl.json`, `messages/en.json` | Generirana pogodba in oba jezika; brez ročnega urejanja API tipov. |
| `services/api/tests/test_backups.py`, `test_backup_paths.py`, `test_backup_worker.py`, `test_backup_restore_db.py`; `BackupSettings.test.tsx`; `apps/web/e2e/backup-settings.spec.ts` | Dokazi BK-01–10. DB/drill test samo izoliran in sintetičen. |
| `infra/README.md`, `services/api/README.md`, `DESIGN.md`, prihodnji ADR, `SESSIONS.md`, `BACKLOG.md` | Po izvedbi runbook, obseg/omejitve, UI in sled odločitve istega diska. V tem dokumentarnem koraku se te datoteke ne urejajo. |

### T1: Trajna politika, status in API brez kopiranja

**Pokriva:** BK-01/02/09, F-BK01/02/05/09.

**Interfaces:** `BackupPolicyInput/Out`, `BackupRunCreate(request_id: UUID, revision: int)`, `BackupRunOut`, `TargetValidationCreate/Out` v `domain/backups.py`; polja/statusi natanko po SPEC. `save_policy(session, body) -> BackupPolicyOut`, `request_backup(session, body) -> BackupRunOut`, `request_target_validation(session, body) -> TargetValidationOut` v `services/backups.py`. HTTP poti natanko BK-02; vklop zahteva isto uspešno preverbo cilja do 5 minut in isto strežniško mapiranje. API ne zaganja pg_dump.

- [ ] Napiši najprej teste `test_backup_defaults_do_no_io`, `test_backup_policy_revision_conflict`, `test_enable_requires_fresh_matching_target_validation`, `test_manual_request_id_lost_response_is_one_intent`, `test_request_id_payload_conflict` in `test_api_omits_secrets`: pričakovani false/null, 0 I/O, 409 CAS, max 5 minut, en run ID, nič credential markerja.
- [ ] Zaženi ciljne teste in potrdi pričakovani manjkajoči model/router, ne okoljske napake.
- [ ] Dodaj modele/migracijo/router in zgornje funkcije. Politika singleton ima revision; run hrani immutable policy snapshot, source/target, request_id/payload hash, schedule identiteto, owner/claim token in čase, backup/restore faze, varen error_code ter rezultat manifest hash. Validation hrani isto mapiranje in readiness/čas. DB unique indeksi varujejo request ID, slot in aktivni prevzem; seznami so bounded do 100.
- [ ] Na izolirani SQL bazi dokaži prehod iz aktualnega head, CAS na dveh povezavah in obstoj runa ob Redis napaki; po sprejemu API vrne 202 brez trditve izdelave. Uporabi `uv run pytest tests/test_backups.py -q` v services/api z izrecno izoliranim TEST_DATABASE_URL.
- [ ] Preglej diff in pripravi commit `feat(backups): persist backup settings and intents [BL-222]`; commit šele ob odobreni izvedbi, ne v pripravi plana.

### T2: Dovoljena mapa in atomarna kopija

**Pokriva:** BK-03/04/06/07, F-BK03/06/07/09.

**Interfaces:** `resolve_backup_target(target_id: str, relative_dir: str, allowed_targets: ...) -> Path`, `validate_target(...) -> TargetValidationOut` v paths.py; `create_archive(run: BackupRunOut, target: Path, tools: ...) -> BackupArtifact` v archive.py. `BackupArtifact` vsebuje `backup_id: UUID`, final basename, dump SHA256/size, manifest SHA256 in checksum fazo, brez vsebine dumpa. To ni vhodni tip retention; bogatejši `BackupRetentionEntry` definira T4. Točni tipe strežniškega mapiranja definira domain/backups.py; ne uporablja uporabniškega argv.

- [ ] Najprej napiši `test_missing_mount_marker_never_creates_fallback`, `test_path_escape_and_symlink_rejected`, `test_unicode_path_is_data_not_command`, `test_acl_failure_blocks_copy`, `test_dump_failure_keeps_previous_backup`, `test_atomic_final_has_dump_and_manifest`, `test_publish_syncs_files_temp_directory_then_final_parent`, `test_directory_fsync_failure_blocks_success_and_retention` ter `test_redacted_manifest_and_logs`; fake orodje zajame argv in credential marker ne sme biti v njem/logu. Zajeti vrstni red mora biti fsync datotek → fsync partial imenika → rename → fsync final parenta → SQL checksum_verified; injiciraj napako obeh imeniških fsync.
- [ ] Zaženi `uv run pytest tests/test_backup_paths.py tests/test_backups.py -q`; potrdi nove pričakovane napake pred implementacijo.
- [ ] Dodaj marker/root preverbo in fixed argv transport. Konsistenten read-only snapshot naj pripada dumpu in kontrolnim poizvedbam. Po exit=0, format preverbi, SHA256 in manifestu fsync-aj datoteke in partial imenik, izvedi rename na istem filesystemu ter fsync-aj končni parent; šele nato zapiši checksum_verified/dovoli retention. Napaka ali nepodprt directory fsync pomeni publish_failed brez retention. Najden final pri obnovi potrebuje isto potrditev parent fsync pred uspehom; ne prepisuj ga.
- [ ] Dodaj backup build target s kompatibilnim PG17 clientom in ločeno Compose službo brez Docker socketa/provider poverilnic, izključeno do konfiguracije. Namestitveni root/marker ostane prazen placeholder; ne izberi dejanske host mape. Dokaži konfiguracijo z redigiranim pregledom modela Compose, ne izpisom resolved secrets.
- [ ] Testiraj fake fsync/rename/dump napake in sintetični PG17 format v `test_backup_restore_db.py`; zabeleži, da je `pg_restore --list` format kontrola, ne restore. Pripravi commit `feat(backups): create bounded atomic database archives [BL-222]`.

### T3: Redni urnik, prevzem in uskladitev po restartu

**Pokriva:** BK-05/09, F-BK04/05/06.

**Interfaces:** `next_backup_slots(policy: BackupPolicyInput, after: datetime, count: int=5) -> list[datetime]`, `backup_tick(ctx) -> int`, `run_backup(ctx, run_id: str) -> str` v backups/worker.py. Uporabi obstoječo civilno semantiko next_slots; weekly preslika izbrani weekday, ne uvaja druge interpretacije DST. Dedicated arq queue `arq:backups`; trajni SQL je resnica pending namenov.

- [ ] Najprej napiši `test_daily_fold_first_occurrence_only`, `test_missing_0200_is_skipped`, `test_weekly_local_day_to_utc`, `test_revision_change_same_day_does_not_duplicate`, `test_outage_coalesces_to_one_slot`, `test_llm_pause_does_not_pause_backups`, `test_manual_backup_runs_when_schedule_disabled`, `test_disabled_schedule_does_not_run`, `test_both_origins_recheck_revision_and_target`, `test_two_runners_claim_one_archive` in `test_final_rename_before_sql_commit_recovers_same_backup`. Konfiguriran/validiran cilj + enabled=false + manual pomeni en fake dump; isti pogoji za scheduled pomenijo nič dumpov. Stale revision/neveljaven cilj pomenita nič dumpov za oba izvora.
- [ ] Zaženi `uv run pytest tests/test_backup_worker.py -q`; popravi samo testno okolje, če ni pričakovanega red izida.
- [ ] Implementiraj minute tick, durable slot/civilno deduplikacijo, bounded dostavo in kratke token/CAS prevzeme. `origin=scheduled|manual` shrani iz zaupanja vrednega ticka/endpointa. Pred začetkom samo scheduled zahteva enabled=true; manual izpusti enabled check. Oba zahtevata aktualno revision in ponovno preverjen dovoljen cilj/marker/pravice/prostor; med dumpom uporabljata immutable snapshot. Ob izgubi ownerja/DB ustavi nove objave/retention; stale timer sam ne dovoljuje novega ownerja med neznano aktivnim procesom.
- [ ] Z dejanskima izoliranima DB povezavama in fake dump bariero dokaži en final pri dveh executorjih. Padec pred/po rename uskladi isti backup_id, brez izgube prejšnjega finala. Brez dokaza konca starega runnerja zabeleži recovery_pending, ne tekmujoč nov dump.
- [ ] Pripravi commit `feat(backups): schedule and recover durable backup intents [BL-222]`.

### T4: Hramba in ločen dokaz obnove

**Pokriva:** BK-08/10, F-BK07/08 in S-F5 obnovitvena vrata.

**Interfaces:** `BackupRetentionEntry` v domain/backups.py ima natančna polja `backup_id: UUID`, `source_alias: str`, `target_id: str`, `root_identity: str`, `final_basename: str`, `started_at: datetime`, `finished_at: datetime`, `timezone: str`, `backup_state: Literal["queued","creating","checksum_verified","failed","skipped","interrupted"]`, `restore_state: Literal["not_tested","passed","failed"]`, `pinned: bool`, `dump_sha256: str`, `manifest_sha256: str`, `ownership_verified: bool`. Datuma sta aware UTC; timezone je IANA cona iz snapshota konkretne kopije, ne trenutna cona nove politike. Metadata se sestavi iz SQL in preverjenega final manifesta; nepopoln/nepreverjen zapis ni kandidat za brisanje. `retention_candidates(entries: list[BackupRetentionEntry], policy: BackupPolicyInput, *, source_alias: str, target_id: str, root_identity: str) -> list[UUID]` v archive.py vrne samo nezaščitene lastne ID tega vira/cilja/korena. Uporabi samo checksum_verified + ownership_verified final zapise; lokalni datum/ISO leto+teden izpelji iz finished_at v entry.timezone, vrstni red znotraj skupine pa `(finished_at, backup_id)`. Zaščiti najnovejši tak backup, najnovejšega z restore_state=passed in vse pinned. `prune_verified_target(...) -> RetentionResult` tik pred izbrisom ponovno preveri root/manifest/ID. Izolirani restore test sprejme točen backup_id/SHA in vnaprej dovoljen nov sintetični testni cilj; ni restore REST endpointa, novega živega restore orodja ali avtomatskega restore v workerju.

- [ ] Napiši `test_retention_union_14_days_8_iso_weeks`, `test_failed_new_dump_never_prunes`, `test_latest_restored_and_pins_survive_lower_retention`, `test_retention_uses_each_entry_snapshot_timezone_and_stable_tie_order`, `test_incomplete_or_wrong_root_metadata_never_pruned`, `test_old_target_partial_foreign_and_symlink_untouched` in `test_retention_failure_preserves_valid_archive` s točnim seznamom ID za izbris ter z vsemi definiranimi BackupRetentionEntry polji.
- [ ] Zaženi ciljne pytest teste, nato implementiraj determinističen izbor in omejen izbris po BK-08. `retention_candidates` je čista funkcija brez SQL/filesystem poizvedb; uporablja že pripravljena polja vsakega entry, vključno z njegovo snapshot časovno cono. Nova cona trenutne politike ne reinterpretira starih kopij. I/O in ponovna preverba identitete sta samo v sestavi preverjenih metapodatkov ter `prune_verified_target`; končni seznam ni aritmetika LLM.
- [ ] Sintetični fixture naj vsebuje več računov/valut, Decimal, delni coverage, osnutke, run/review unknown, email unknown in outbox cursor; `test_isolated_restore_matches_snapshot` mora primerjati shemo/razširitve/FK/unique/kanonične vsote ter read-only smoke, s 0 zunanjimi transporti.
- [ ] Dodaj `test_restore_rejects_source_target_identity` in `test_wrong_extension_version_blocks_verification`; napačen cilj/razširitev nikoli ne dobi restore_state=passed. Noben dejanski vir/port/volumen :3000 ali zasebne poverilnice niso del fixture.
- [ ] Pripravi commit `feat(backups): retain verified archives and prove isolated restore [BL-222]`; dokaz jasno označi sintetično okolje in nepotrjeno živo obnovljivost.

### T5: Nastavitve, generirana pogodba in jasne povratne informacije

**Pokriva:** BK-01/02/09, F-BK02/10.

**Interfaces:** API tipi iz OpenAPI; `useBackupSettings`, `useSaveBackupSettings`, `useValidateBackupTarget`, `useCreateBackup`, `useBackupRuns` v lib/api/backups.ts. Komponenta `BackupSettings()` uporablja sedanje Settings obrazce, saved/dirty/409 ter status polling samo med aktivno operacijo. Ni RESTORE akcije.

- [ ] Napiši Vitest teste `shows_disabled_unconfigured_without_io`, `same_disk_is_allowed_and_limitation_visible`, `cannot_enable_without_validated_target`, `lost_response_keeps_request_id`, `checksum_success_does_not_show_restore_success` in `revision_conflict_keeps_draft` v BackupSettings.test.tsx.
- [ ] Generiraj API/TS z `uv run python -m preza.cli.export_openapi openapi.json` v services/api ter `pnpm --filter web gen:api`; generirani diff mora slediti routerju, brez ročnih popravkov.
- [ ] Dodaj obrazec/polling/SL-EN copy po SPEC. Samo target alias in podmapa, dnevni/tedenski/manual urnik, 14/8 editable, next run, save/discard/probe/manual feedback. Prikaži runner unavailable/queued/failed in zadnjo kopijo/restore ločeno. Vsa besedila prek next-intl, fokus/48px/tipkovnica po DESIGN.
- [ ] Zaženi `pnpm --filter web test`, `pnpm --filter web typecheck`, `pnpm --filter web lint`, `pnpm --filter web i18n:check`; po potrebi samo ciljno najprej, celoto ob integraciji.
- [ ] Dodaj Playwright SL/EN × desktop/phone z fake API oziroma izrecno sintetičnim lokalnim skladom. Noben zagon ali preureditev obstoječega :3100 ni implicitno dovoljen s tem planom. Po izvedbi posodobi DESIGN in pripravi commit `feat(settings): configure backup destination and frequency [BL-222]`.

### T6: Integracijski dokaz, runbook in ločena aktivacija

**Pokriva:** vse BK/F-BK in zaključna vrata.

- [ ] Zaženi API ruff/format/mypy in ustrezne teste T1–T4; nato širšo regresijo glede na dejanski diff. Čista generirana OpenAPI/TS in web preverjanja iz T5 so vrata. Zabeleži dejanski SHA, DB alias/različice, fake transport štetje, manifest hash in trajanje sintetičnega drilla; ne prepisuj starih števil testov kot novega rezultata.
- [ ] Preglej vse BK-01–10 → F-BK01–10 → izvedene teste. Neodvisni pregled naj posebej preveri brisanje/path/argv, skrivnosti v logu, DST dedup, crash po rename, CAS in razliko checksum/restore. Popravi ugotovitve pred oznako izvedeno.
- [ ] Dopolni infra/API README, ADR za dovoljeni isti disk in omejeni runner, SESSIONS ter BACKLOG. BL-222 lahko pomeni izvedene Nastavitve s sintetičnim dokazom; BL-017/215 ostaneta odprta do dejanske konfiguracije/rednih kopij in ustreznega restore dokaza.
- [ ] Predloži rezultat za pregled. Šele pred dejansko aktivacijo pridobi konkretni host root in preveri mount/ACL/prostor ter kdo dostopa do zasebnih kopij/ločeno obnovljenih skrivnosti. Ne sprašuj ponovno o retention samo zato, ker ima predlog 14/8.
- [ ] Deploy/živa migracija ali dejanska zasebna kopija ne sledijo samodejno. Uporabi obstoječa ločena S-F5/S-H vrata, nov dovoljen target ter izrecno odobreno izvedbo; noben običajni ročni backup gumb ne dovoljuje restore ali migracije.

## Pregled plana in odprto

Samopregled dokumenta: BK-01/02/09 pokrivata T1/T5, BK-03/04/06/07 T2, BK-05 T3, BK-08/10 T4, povezano dokazno/izdajno mejo T6. Pet Review Focus primerov ima eksplicitne teste. Števila/semantika so enaka SPEC; konkretni source/target/skrivnosti niso izmišljeni.

Pred pregledom izvedbe ni dodatnega vprašanja za uporabnika. Za aktivacijo manjka **konkretna dovoljena host mapa**; dokler je ni, disabled/unconfigured. Nastavitve ne ustvarijo diska ali mounta in ne dokazujejo žive obnovljivosti. Ta priprava ni zagnala testov, kopije ali obnove in ni spremenila obstoječih dokumentov, kode ali okolja.
