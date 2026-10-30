# Izvedbeni plan: Radar in trajna oddaja predloga

> **For agentic workers:** uporabi superpowers:subagent-driven-development ali superpowers:executing-plans. Delo je uporabnik odobril z nadaljevanjem odprtih točk; :3000 ostane nedotaknjen.

**Goal:** Odpraviti izgubljene Radar zadetke ter preprečiti podvojeno oddajo istega predloga po reload/izgubljenem odgovoru.

**Architecture:** Obstoječi FastAPI/PostgreSQL in Next.js. Radar članstvo v SQL pred LIMIT; obstoječa strežniška request_id idempotenca ostane, brskalnik trajno shrani tudi poslano namero. Brez nove sheme ali ponudnikov.

**Tech Stack:** Python/SQLAlchemy/pytest, TypeScript/React/Vitest/Playwright, SL/EN.

**Spec:** [S-G1 SG-09–11, F-G06–09](../specs/2026-10-30-lastnistvo-in-idempotentnost-spec.md). Izvaja samo neodvisni R1 in BL-204. A3/A5 zahtevata ločen pregled živosti/lastništva; Flex/FX/restore/SMTP ostanejo odvisni od dejanskih vhodov.

## Global Constraints

- Izoliran worktree `feat/uxui-demo-upgrade`, osnova `21a0b3d`. Brez :3000, merge/push, živega modela, SMTP ali spreminjanja zasebnih podatkov.
- Radar `list_events(session, view, min_score=0, days=7, limit=100)` ohrani podpis/izhod. Filter pred urejenim LIMIT; en dogodek enkrat. GET ne kliče ponudnika.
- Poslani request_id in canonical body preživita reload. Negotov odgovor ne ustvari nove namere. Ista namera ostane ločena od novega urejanega osnutka.
- Če operacije ni mogoče trajno zapisati, ne oddaj POST; ohrani vsebino in razloži vrzel SL/EN. To je izbrana varna usmeritev SG-11, ne nova uporabnikova zahteva za videz.
- Denar/provenienca, obstoječe varovalke/kvote in API idempotenca ostanejo; ni novega samodejnega plačljivega retryja. Preverjanje/ponovitev iste namere sproži izrecno uporabnikovo dejanje.

## Review Focus

1. Več kot `limit*3` drugih dogodkov ne skrije zadetka izbranega pogleda; prazna članstva in isti časi ostanejo pravilni.
2. Spremenjen osnutek ob neznanem izidu ne spremeni telesa stare namere ali tiho ustvari novega request_id.
3. Uspešen sprejem + izgubljen odgovor + reload pomeni en predlog/analizo/kvoto; odgovor z drugim ID ali konflikt se ne razglasi za uspeh.
4. Dva zavihka istega osnutka ohranita identiteto; storage napaka, poškodovan zapis in migracija v1 ne izgubijo uporabne vsebine ali pošljejo nezaščitene namere.
5. Telefon, SL/EN, tipkovnica, Cancel/Back ter opozorila ostanejo dostopni; noben pravi transport med E2E.

## T1: Radar SQL filter [BL-221]

**Files:** `services/api/preza/services/radar_views.py`; nov `services/api/tests/test_radar_membership_db.py` in obstoječi `test_api_m2.py`.

**Interface:** SG-09, obstoječi user_symbols/event_out; exact-ID pot ostane.

- [x] RED: več kot `limit*3` višje ocenjenih tujih dogodkov + upravičen zadaj za portfolio/watchlist/discover; pričakuj zadetek.
- [x] Filtriraj presek array simbolov z held/watched oziroma komplement njune unije v SQL; ohrani time/status/score. Uredi `score DESC NULLS LAST, last_seen_at DESC, id DESC`, LIMIT šele nato.
- [x] GREEN: prazna članstva, mešan simbol, dismissed/stale/min_score, null-score in stabilna vez; omejen SELECT, brez N+1/providerjev. Zabeleži EXPLAIN na sintetičnem naboru, brez novega indeksa brez potrebe.
- [x] Ciljni pytest na namenski DB, Ruff/format/mypy; neodvisni pregled; commit.

## T2: Trajno shranjena namera [BL-204]

**Files:** `apps/web/components/proposals/ProposalComposer.tsx`; nov `apps/web/lib/proposal-draft.ts` in test; nov `ProposalComposer.test.tsx`, `e2e/proposal-idempotency.spec.ts`. Prevodi kot fragment v scratch za integratorja. Root po potrebi doda API regresijo v `test_proposal_idempotency_db.py`.

**Dopolnitev integracijskega dokaza:** dejanski E2E po reload razkrije predobstoječo kolizijo identifikatorja prekrivnega okna v `apps/web/lib/useBackToClose.ts`. Obseg vključuje minimalno odpravo kolizije in razširitev obstoječega `useBackToClose.test.tsx`; javni podpis, Next history state in več odprtih oken ostanejo. Naslednji zagon potrdi zapiranje, vendar odkrije manjkajočo obnovo fokusa zunanjega odpiralca. Composer zato zajame dejanskega odpiralca in ga ob zapiranju obnovi, če je še prisoten. Oba vedenjska preizkusa sta najprej padla, zato gre za zahtevano pravilnost T2, ne dodatno oblikovno prenovo.

Širši E2E v `apps/web/e2e/shell.spec.ts` pričakovani vrstni red simbolov v potrditvi uskladi s kanonično shranjeno oddajo (`AMD, NVDA`). Sprejem in preverba obstoja predloga ostaneta obvezna. Nova meritev 48 px čaka na dejansko končno velikost med animacijo, brez znižanja praga.

**Interface:** uporabi obstoječi `useCreateProposal` in GET `/proposals/{request_id}`; javna API shema se ne spreminja. Verzija brskalniškega zapisa vsebuje draft_id, fields, operation/request_id/canonical_body/state/proposal_id in čas; veljavno vsebino v1 obnovi brez izmišljanja stare namere.

- [x] RED: priprava namere → POST sprejet, odgovor izgine → remount/reload → izrecna ponovitev z istim request_id in istim telesom; prvotna izvedba uporablja nov UUID.
- [x] Pred POST preverjeno trajno shrani zamrznjeno telo in request_id; osnutek lahko ostane ločen. Ponovitev najprej preveri isti ID; 404 dovoljuje isti POST, ne novega ID. Druge napake ohranijo negotov izid.
- [x] Neznan izid/konflikt je viden in ima jasno dejanje za preverjanje iste namere. Nova urejena vsebina postane nova namera samo z izrecnim uporabnikovim dejanjem. Sprejet ID mora ustrezati zahtevanemu.
- [x] Storage failure blokira POST in ohrani besedilo; poškodovan zapis se varno obravnava; dva zavihka delita isti pripravljeni ID brez tihega prepisa. Ne uvajaj samodejnega background replay.
- [x] GREEN: unit za serializacijo/preverjanje/migracijo/race; API obstoječa zaščita konflikta/sočasnosti ostane; Playwright lost-response/reload/ista oddaja, SL/EN desktop/phone, brez pravih modelov.
- [x] Vitest/tsc/ESLint/i18n; neodvisni pregled; commit.

## T3: Integracija in odprta vprašanja

- [x] Root združi prevode, preveri API lost-response/konflikt brez spremembe sprejema in dopolni DESIGN.
- [x] Ponovi primerne ciljne in skupne teste; :3100 osveži šele z uspešnim buildom. :3000 je nedotaknjen.
- [x] Zapiši S-024, statuse BL-204/221, dokaze in tabelo nadaljnjih pogojev. A3/A5 ne označi done na podlagi teh dveh popravkov.
- [x] Preveri dejanski vir za Flex/FX/SMTP/backup; vprašanja uporabniku ostanejo pending, če vhod manjka. Skrivnosti ne sodijo v pogovor/repo.
