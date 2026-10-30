# Claudov pregled `feat/uxui-demo-upgrade` @ 9ec9e88 (baseline 1855eb8)

Odgovor na [prevzem za Claude](./2026-10-30-prevzem-za-claude-pregled.md). Popravke vodi BL-218.

Datum: 2026-10-30. Pregled je bil read-only. Ni bilo merga, deploya na :3000, pošiljanja pošte ali LLM klicev.

## 1. Povzetek

Veja je kakovostna in vsi avtomatski testi so zeleni. Pred mergem pa je treba popraviti nekaj napak v dividendah, avtomatizaciji (stikalo in outbox) in BacktestPanel.
Priporočilo: **REQUEST_CHANGES**. Pred mergem v `master` popravi D1, A1, A2, A4, U1 in U2. F1, A3 in R1 so starejše napake in gredo v pakete B in G1. Deploy na :3000 naj bo ločen korak: najprej backup, nato migracije 0016–0019.

## 2. Preverjeni rezultati (ločen review worktree, izolirana test DB)

| Preverjanje | Rezultat |
|---|---|
| API `ruff check`, `ruff format --check`, `mypy` domain | čisto |
| API `pytest` | 554 passed |
| Agents `ruff` + `pytest` | 221 passed |
| OpenAPI `openapi.json` skladen s kodo | da |
| Web `typecheck`, `lint` (0 warnings), `i18n:check` (1290 ključev) | čisto |
| Web `vitest` | 42 datotek, 155 testov passed |
| Grep: oddaja naročil, neposredni LLM ponudniki, `float(` v novih storitvah | nič ni najdeno |

## 3. Ugotovitve po resnosti

Oznake: **NAPAKA** (potrjena v kodi), **OMEJITEV** (znana), **MANJKA PREVERJANJE**, **PREDLOG**. Pri vsaki je navedeno, ali je nastala v tej veji ali je obstajala že pred 1855eb8.

### Visoko

**D1. Ponovni uvoz brez sekcije izbriše odprte dividendne obveznosti.** NAPAKA, nova.
- Mesto: `services/api/preza/broker/dividends.py:94` in `services/api/preza/services/dividends.py:101-106`.
- Scenarij:
  1. Uporabnik uvozi Flex XML z `OpenDividendAccruals`.
  2. Isti dan uvozi drug izvoz za isto obdobje, ki te sekcije nima.
- Vzrok:
  - Parser zapiše coverage s `status="missing"`.
  - `snapshot_version` je izpeljan iz dneva, zato je enak kot pri prvem uvozu.
  - Upsert se izvede pri `<=`, zato prepiše payload z `missing`.
  - `services/dividends.py:168` nato ignorira vrstice `missing`, zato odprte obveznosti za račun izginejo iz "latest open".
- Popravek: upsert naj nikoli ne prepiše `complete`/`partial` z `missing`, na primer z dodatnim pogojem `excluded.status != 'missing'`. Dodaj regresijski test z dvema uvozoma.

**F1. FX tečaj se ne preveri glede na bazno valuto.** NAPAKA, obstaja že pred 1855eb8, ni regresija.
- Mesto: `services/api/preza/services/portfolio.py:135-143`.
- Scenarij: IBKR `fxRateToBase` je tečaj glede na bazno valuto **računa**. Če ima račun bazo USD, `settings.base_currency` pa je EUR, se vrednosti pomnožijo z napačnim tečajem. Pri več računih se seštejejo različne baze.
- Popravek: shrani bazno valuto računa iz Flex `AccountInformation`/`currency`. FX uporabi samo, če je enaka zahtevani bazi; sicer `missing_fx`.
- Spada v paket B (Flex robovi).

**A1. Glavno stikalo avtomatskih analiz ne ustavi drugega LLM poskusa.** NAPAKA, nova.
- Mesto: `services/api/preza/llm/automatic.py:30-35`, `services/api/preza/llm/client.py:137-150`.
- Scenarij:
  1. Avtomatska analiza pokliče model.
  2. Med prvim HTTP klicem uporabnik izklopi avtomatske analize.
  3. Odgovor ne ustreza shemi.
  4. `for _attempt in range(2)` sproži nov plačljiv klic.
- Vzrok: `AutomaticLlm.allowed()` preveri stikalo samo enkrat, pred zanko. To krši ADR-0021, ki dovoli dokončanje samo tekočega klica.
- Popravek: stikalo preveri pred vsakim HTTP poskusom, na primer s callbackom `before_attempt`. Dodaj test izklopa med prvim in drugim poskusom.

**A2. Pregled teze lahko pokliče `cloud-deep` po izklopu stikala.** VERJETNA NAPAKA, nova.
- Mesto: `services/agents/preza_agents/thesis_tracker/runner.py:73-87`.
- Vzrok:
  - `review_gate` teče pred `mark_dispatched`, ki lahko čaka na zaklep.
  - Po commitu sledi neposreden `complete_json`.
  - `ctx["llm"]` za thesis_review ni ovit v `AutomaticLlm`.
- Popravek: ponovno preveri stikalo tik pred klicem in avtomatske preglede ovij v `AutomaticLlm`.

**A3. Ponovna dostava globoke analize v stanju `running` ponovi plačljive klice.** NAPAKA, obstaja že pred 1855eb8.
- Mesto: `services/agents/preza_agents/worker.py:245-255`.
- Vzrok: vrstica `if run.status in ("done","failed")` je bila v kodi že na baseline. Z avtomatizacijo je ponovna dostava pogostejša.
- Popravek: ob vstopu v `running` brez lastnika označi `failed_unknown` in ne ponavljaj slepo. Spada v G1 (idempotentnost).

### Srednje

**A4. Blokirani zapisi outboxa izstradajo poznejše izvedbe.** NAPAKA, nova.
- Mesto: `services/api/preza/services/automation.py:209-224`.
- Vzrok: `pending ORDER BY scheduled_for LIMIT 100` sledi `gate(...) -> continue`. Če je prvih 100 trajno blokiranih, se nič drugega nikoli ne dostavi.
- Popravek: trajno neveljavne zaključi kot `skipped`, začasno blokirane izloči iz izbora (paginacija ali filter). Dodaj test s 100 blokiranimi in eno dovoljeno izvedbo.

**A5. Prekinjen pregled teze lahko trajno ostane `running`.** VERJETNA NAPAKA, nova.
- Mesto: `thesis_tracker/runner.py:57-69`, `services/automation.py:431-434`.
- Vzrok: nova izvedba ni lastnik starega dispatcha, zato pregleda ne zaključi kot `failed_unknown`.
- Popravek: preverjanje lastnika z izteklim heartbeatom; opuščen pregled zaključi brez ponovnega klica.

**U1. Povezava na mnenje v BacktestPanel odpre "ni najdeno".** NAPAKA, nova.
- Mesto: `apps/web/components/track-record/BacktestPanel.tsx:240-242`, `apps/web/components/common/PeekPanel.tsx:72-77`.
- Scenarij: `?peek=analysis:<id>` se odpre, PeekPanel pa zna prikazati samo `instrument` in `signal`.
- Popravek: povezava na stran analize ali predogled analize v PeekPanel. Dodaj test za vrstico `source='analysis'`.

**U2. Klik vrstice v BacktestPanel zavrže izračunano študijo.** NAPAKA, nova.
- Mesto: `BacktestPanel.tsx:240-242`, isti `<a href="?peek=...">`.
- Vzrok: navaden `<a>` sproži polno navigacijo, nastavitve in rezultat pa so samo v `useState`/query.
- Popravek: `EntityLink`/`usePeek` (`router.push`) z ohranitvijo obstoječih parametrov URL.

**D2. Popravek obračuna (`ChangeInDividendAccrual`, vrstica `Re`) se šteje kot pričakovani bruto.** VERJETNA NAPAKA, nova.
- Mesto: `services/api/preza/services/dividend_controls.py:18-41`.
- Scenarij: negativna vrstica razveljavitve postane "najnovejša" obveznost, zato uskladitev pokaže lažno razliko.
- Dokaz: najdba pregledovalca. Logika `latest` po `(as_of, snapshot_version)` to dopušča. Posnetka s pravim `Re` primerom nisem poganjal.
- Popravek: vrstice `Re`/reversal izloči ali jih nettaj. Za ta primer dodaj fixture.

**D3. Delna (`partial`) pokritost CashTransactions se prikaže kot potrjena.** PREDLOG/OMEJITEV, nova.
- Mesto: `apps/web/components/portfolio/PortfolioDividends.tsx:54-62`.
- Vzrok: pogoj je `status !== "missing"`.
- Popravek: za "potrjeno do" štej samo `complete`, `partial` pa prikaži z opozorilom.

**R1. Radar pogledi rabijo `limit*3` pred filtrom pogleda.** NAPAKA, obstaja že pred 1855eb8.
- Mesto: `services/api/preza/services/radar_views.py:55-75`.
- Scenarij: veliko višje uvrščenih dogodkov zunaj portfelja povzroči prazen pogled PORTFOLIO.
- Popravek: filter članstva v SQL pred `LIMIT` (`symbols && :held`).

### Nizko / omejitve

- **B5. Cash snapshot samo iz BASE_SUMMARY** postane "complete" prazen snapshot (`broker/flex.py:101-102,159-160`). OMEJITEV, že zajeta v BL-205.
- **E1. SMTP.** Pregledovalec potrjuje STARTTLS/TLS z validacijo certifikata, zapis `sending` pred transportom in brez ponovitev `sending`/`unknown`. Pravi SMTP ni bil izveden. MANJKA PREVERJANJE v živo pred vklopom pošte.
- Pregledovalci niso imeli git diffa in so brali trenutne datoteke. Ali je ugotovitev nova ali starejša, sem za ugotovitve, ki so v poročilu označene kot nove ali starejše, preveril sam z `git show 1855eb8:<pot>`.

## 4. Pregled plana `2026-10-30-zakljucevanje-odprtih-sklopov.md`

Plan je temeljit in vseh 49 odprtih BL je razporejenih po paketih. Opombe:

1. **Tveganje SPEC paralize.** V0 zahteva SPEC za vse pakete pred izvedbo. Predlog: SPEC piši samo za pakete naslednjega vala, ostale pusti kot skico.
2. **Najmanjši obseg prve izdaje:**
   - B2/B5 (Flex robovi) skupaj z D1, D2 in F1;
   - C minimalno (identiteta);
   - G1 (idempotentnost avtomatizacije);
   - H (izdaja).

   Vrzeli v D/E/F je treba izrecno sprejeti in zapisati v izdajne opombe.
3. **Kritična pot je tvoj razširjeni zasebni Flex XML** (B1/BL-202). Brez njega B ne more biti zaključen. Pridobi ga čim prej.
4. **Loči "merge v master" od "deploy na :3000".** H6 ju združuje. Merge naj gre takoj, ko so popravki in testi zeleni. Deploy naj bo ločen, odobren korak.
5. **Backup/restore (F5/BL-017) premakni pred prvo živo migracijo 0016–0019.** Migracije dodajajo 4 sheme v živo bazo.
6. **Merila sprejema so večinoma opisna.** Vsak paketni SPEC naj ima ukazna vrata (npr. `pytest -k dividends`, e2e scenarij, ročni smoke na :3100).
7. **Podvajanja:** BL-174 se prekriva z BL-193/194. Zastareli statusi BL-011/013 so zajeti v A3, zato jih zapri čim prej.
8. **Higiena vej** naj ne čaka H1. Urejeno, glej §6.
9. **SESSIONS:** vnos S-014 (Claude, 28. 10.) v veji manjka. Dodaj ga ob mergu.

**Naslednji SPEC-i po vrstnem redu:**
1. **S-B Flex/dividende:** D1, D2, F1, B5, BL-202, BL-205.
2. **S-F5 backup/restore** pred živo migracijo.
3. **S-G1 idempotentnost avtomatizacije/pošte:** A1–A5.
4. **S-C identiteta (minimalno).**
5. **S-H izdaja:** merge, nato backup, migracija, deploy in smoke.

## 5. Naloge za Codex (BL-218)

Vsak popravek naj ima regresijski test. Vrata pred mergem: API `ruff` + `mypy` + `pytest`, agents `pytest`, web `typecheck` + `lint` + `i18n:check` + `vitest`, vse zeleno.

**Pred mergem v `master`:**

- [ ] **D1:** upsert coverage ne sme prepisati `complete`/`partial` z `missing`. Test: dva uvoza isti dan, drugi brez `OpenDividendAccruals`; odprte obveznosti ostanejo.
- [ ] **A1:** stikalo avtomatskih analiz preveri pred vsakim HTTP poskusom v `complete_json`, tudi pri popravku JSON. Ročni klici ostanejo nespremenjeni. Test: izklop po prvem neveljavnem odgovoru → drugega klica ni.
- [ ] **A2:** v `thesis_tracker/runner.py` ponovno preveri stikalo po `mark_dispatched` in tik pred `complete_json`. Avtomatske preglede ovij v `AutomaticLlm`. Test: izklop med čakanjem na zaklep.
- [ ] **A4:** `deliver_pending` ne sme obtičati na blokiranih zapisih. Trajno neveljavne zaključi kot `skipped`, začasno blokirane izloči iz izbora. Test: 100 blokiranih in 1 dovoljena izvedba → dovoljena se dostavi.
- [ ] **U1:** `BacktestPanel` povezava `source='analysis'` naj odpre analizo (stran ali nov predogled v `PeekPanel`). Test klika.
- [ ] **U2:** namesto `<a href="?peek=...">` uporabi `EntityLink`/`usePeek`. Test: po odprtju in zaprtju predogleda rezultat in nastavitve ostanejo.

**V paketih plana (BL-214 SPEC):**

- [ ] **D2, D3, F1, B5:** v S-B (Flex/dividende). Za D2 dodaj fixture z vrstico `ChangeInDividendAccrual` `Re`. Za F1 shrani bazno valuto računa.
- [ ] **A3, A5:** v S-G1 (idempotentnost). `running` brez živega lastnika → `failed_unknown`, brez ponovnega klica.
- [ ] **R1:** filter pogleda radarja v SQL pred `LIMIT`. Lahko je samostojen manjši popravek.
- [ ] **Plan:** upoštevaj opombe §4. Merge in deploy loči v H6, backup (F5) premakni pred živo migracijo, SPEC piši samo za naslednji val.

## 6. Stanje vej (urejeno 2026-10-30)

Ureditev je izvedel Claude po potrditvi uporabnika in neodvisni presoji reviewerja (`SAFETY_VERDICT: APPROVE`).

| Veja | Stanje |
|---|---|
| `master` | c0c15ae, poslan na `Autotrading/master` (prej 38 commitov zadaj) |
| `feat/uxui-demo-upgrade` | aktivna, zdaj tudi na `Autotrading` (upstream nastavljen) |
| `claude/bold-turing-g4o16e` | ohranjena, živi stack :3000 |
| `claude/preverjanje-podatkovnih-povezav-53ab37` | vsebovana v tej veji; arhivira se po mergu |
| `legacy` (remote) | ohranjena |
| `claude/remote-control-0fb325`, `archive/nextjs-mvp-5224b31`, `fix/signal-read-contracts` | izbrisane (vsebovane v master/feat oziroma `legacy`) |
| `claude/eloquent-bhabha-620624` | izbrisana lokalno in na remote. Varnostna kopija je git bundle zunaj repa (`Documents/git-archive/autotrading/`, SHA256 zapisan ob datoteki, obnova preverjena na 8ed4f49) |

Za commite: vse nove spremembe gredo na `feat/uxui-demo-upgrade`, nato en merge v `master`. Vnos S-014 (Claudova seja 28. 10.) je v osnovnem checkoutu `master` neobjavljen; ob mergu ga prenesi v SESSIONS.

## 7. Odprto

- A2 in A5 sta preverjeni statično, ne z zagonom (sočasnost in DB zaklepi).
- D2 na pravem Flex primeru z vrstico `Re`.
- Brskalniški e2e (Playwright) v tem pregledu ni bil zagnan.
- Pravi SMTP ni bil preizkušen.
