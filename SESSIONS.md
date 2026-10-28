# SESSIONS.md: dnevnik delovnih sej

Najnovejša seja je na vrhu. Vsaka seja ima ID `S-xxx`, datum, cilj, rezultat, odločitve in odprta vprašanja. Predloga je na dnu.

---

## S-013 · 2026-10-28 · Vitka zaporedna analiza delnice

**Cilj:** BL-167: manj žetonov na analizo delnice, vsak klic pod 16 tisoč vhodnih žetonov. Čim več dela opravi koda, AI samo presodi in združi.

**Narejeno:**
- ADR-0016: koda pripravi povzetke trga, temeljev in novic ter register dokazov. Trije analitiki tečejo zaporedno, sledita bik in medved ter en odločevalec, ki pri delnicah nadomesti kartico in preverjanje hipoteze. Lokalni povzetek je neobvezen.
- `budget.py`: ocena vhoda, delovna meja 12 tisoč, trda 16 tisoč, meje izhoda po vlogah (6000, 10.000, 2000). Poraba po klicih se shrani v `models.usage`. API in UI prikažeta nov zapis modelov.
- Preverjanje številk: številke brez opore v registru postanejo `[?]`. Obdobja (tudi »200-dnevno«, »20- in 50-dnevnega«), datumi (»30. junija 2026«) in predznak, izražen z besedo (»padec«, »odtok«), niso več napačno označeni.
- Prvi živi tek je padel s praznim odgovorom: splošne novice so izrinile dejstva o AMD, model ni vedel, katero podjetje analizira, MiniMax pa ne upošteva `response_format`. Popravki: prednostni red v registru, splošne novice (`G`) največ 5 in nikoli uradne, polje `instrument`, shema tudi v sistemskem pozivu, višje meje izhoda.
- Živi tek AMD (`b782bf65`) je uspel: 6 klicev, okoli 76 tisoč žetonov namesto 353 tisoč (−78 %), največji vhod okoli 8,4 tisoč, 6,5 minute namesto 42.
- AMD ni imel temeljev in ne novic o podjetju, ker ni na watchlisti in ga nimaš v portfelju. Finnhub novice in temelje dobijo samo ti simboli, temelje samo ob nedeljah. Zdaj analiza delnice pred začetkom sama naloži manjkajoče ali več kot 7 dni stare temelje in novice Finnhub za ta simbol. Novice gredo samo v posnetek analize, ne v bazo, da jih radar pozneje še vedno obdela. Pri analizi za datum, starejši od 3 dni, se nič ne naloži, ker bi to pomenilo pogled v prihodnost.
- Sklad je bil ponovno zgrajen in zagnan.
- Ponovni tek AMD (`0098df84`) je padel, ker je medved vrnil 6 citatov namesto največ 4. Zdaj shema modelu še vedno sporoča kratke meje, sprejme pa do 16 citatov in 6 točk. Nič se ne reže pred preverjanjem govoric; na javne meje kartice se skrajša šele po njem (neodvisni pregled je pokazal, da bi rezanje lahko skrilo govorico za nakupom).
- Preverjanje številk sprejme "3-, 6-mesečni" ter "RSI 14", "ATR 14" in "SMA 200" s presledkom. "RSI 70", "ATR 14 %" in "SMA 200 000" se še vedno preverjajo.
- Napaka pri nalaganju temeljev ali novic ne pusti več analize v stanju `running`: zapis temeljev je v savepointu, vsaka napaka pa se samo zabeleži.
- Tek AMD `9d4dfe69` (pred popravki pregleda): uspel, Underweight, 0 `[?]` (prej 57), temelji Finnhub prisotni, 248 novic, 6 klicev, okoli 46 tisoč vhodnih in 48 tisoč izhodnih žetonov, 8 minut. Klica medveda in odločevalca sta potrebovala popravni poskus; vsak posamezen klic je pod 16k.
- Preverjeno: agenti 192 testov z bazo, ruff, mypy; API 289 testov z bazo, ruff.
- Tek AMD `3bd633f4` na končni različici: uspel, Overweight, 248 novic, temelji Finnhub z današnjim datumom, 6 klicev brez popravnih poskusov, okoli 38 tisoč vhodnih in 38 tisoč izhodnih žetonov, 5,6 minute. En `[?]` (odstotek rasti prihodkov, ki ga ni med dejstvi) in opozorilo `unverified_numbers`: preverjanje številk deluje, kot mora.

**Odločitve:** ADR-0016. TradingAgents za delnice ni več v uporabi (odstranitev BL-171).

**Odprto:**
- Razmišljanje MiniMax je okoli polovice izhodnih žetonov (BL-168).
- Kartica je imela prepričanje 6 in oceno Hold, odločitev pa Overweight.
- Tek `b063971d` je ostal v stanju `running`, ker je bil sklad med njim ustavljen. Pometanje pobere samo `queued` teke, zato osirotelih `running` vrstic nihče ne zaključi (BL-177).
- Novice Finnhub se ne klasificirajo kot govorice (BL-175). Poraba ne beleži števila poskusov (BL-176).

**Naslednji korak:** BL-175, BL-177, nato BL-168.

---

## S-012 · 2026-10-27 · Kalibracija uteži, LiteLLM in cene na watchlisti

**Cilj:** BL-103, popraviti padlo analizo (LiteLLM) in hitrejše cene na watchlisti.

**Narejeno:**
- BL-103 (ADR-0015): predlog uteži iz izidov (Wilsonov interval, krčenje proti osnovi, meje 0,50–1,50), tabela `signal_weight_set` (migracija 0015), `GET/POST /calibration`, potrditev samo z `{"confirm": true}`, utež pomnoži moč novih signalov radarja in pravil. SCR-10 ima razdelek »Predlog uteži«.
- BL-097: analiza je padla po 24 minutah, ker OpenCode Go zavrne klice brez seje OpenCode, nadomestni klici pa so se ponavljali. `cloud-quick` in `cloud-deep` sta zdaj na MiniMax, timeout 600 s za `cloud-deep`, brez ponavljanja ob timeoutu. Ponovna analiza AMD je uspela (42 min, 15 korakov).
- BL-166: dodajanje na watchlisto takoj sproži prenos cen; prej so prišle šele ob 21:30 UTC ob delavnikih. ELF, O, UNH, NVO in MSFT so dobili cene in ceno ob dodajanju.
- Živi sklad: varnostna kopija v `preza-backups`, migraciji 0014 in 0015 uveljavljeni.
- Preverjeno: API 289 testov, ruff, mypy; web vitest, tsc, eslint; e2e SCR-10 na demo skladu (namizje in telefon).

**Odločitve:** ADR-0015. Glave `x-opencode-session` ne ponarejamo.

**Odprto:** poraba žetonov pri analizi je previsoka (BL-167).

**Naslednji korak:** BL-167.

---

## S-011 · 2026-10-27 · Uspešnost in zaključek M5

**Cilj:** zaključiti preostale naloge M5: BL-163, BL-161 in BL-102 (SCR-10).

**Narejeno:**
- BL-163: `vendor_local` piše CSV z `
` na vseh platformah, zato se golden kontrolne vsote ujemajo tudi na Windows.
- BL-161: različica osnutka teze ima `edit_count` in `edited_at` (migracija 0014). Urejanje pošlje `expected_edit_count`; zastarelo urejanje vrne 409 `revision_edit_conflict` s prijaznim sporočilom. `updated_at` zdaj upošteva tudi urejanja.
- BL-102: `GET /track-record` (domena `track_record.py` je čista in brez I/O) in zaslon SCR-10. Zadetki in donos so v smeri signala, alfa je proti indeksu, shranjenemu ob izidu. Tvoji predlogi (`manual` ali s `proposal_id`) se merijo ločeno. Kalibracija ima 5 razredov moči. Pod 10 izidi je številka označena.
- Proxy `app/api/[...path]` je imel seznam dovoljenih poti brez `track-record`; dodano.
- Oznake mejnika v navigaciji so odstranjene pri izvedenih zaslonih (Vstopi, Teze, Uspešnost).
- Demo seed doda 14 preteklih signalov; izidi se izračunajo iz demo sveč proti CSPX.
- Preverjeno: API z bazo 281 testov, ruff, mypy; web tsc, eslint, vitest 108; e2e na demo skladu 34 uspešnih in 10 preskočenih; telefon brez vodoravnega drsenja.
- Neodvisnega pregleda ni bilo, ker OpenCode Sol nima kvote.

**Odločitve:** SCR-10 kalibracijo samo prikaže. Predlog novih uteži je ločena naloga (BL-103) in zahteva tvojo potrditev.

**Odprto:**
- Živa baza potrebuje migracijo 0014, ko se živi sklad zgradi iz te veje.
- Osnutek teze ASML čaka tvojo potrditev, BL-097 je tvoja odločitev, IB še ni povezan.

**Naslednji korak:** BL-103 kalibracija uteži, nato M6.

---

## S-010 · 2026-10-27 · Demo sklad za e2e

**Cilj:** e2e naj teče zeleno na vzorčnih podatkih, brez posega v živo bazo (BL-162).

**Narejeno:**
- `infra/docker-compose.demo.yml`: ločen projekt `preza-demo` z lastno bazo, Redisom, API-jem in webom na `127.0.0.1:3100`. Brez LiteLLM, workerja, agentov in obvestil. Yahoo, Stooq in RSS so izklopljeni.
- `infra/scripts/demo-stack.sh` (`up`, `seed`, `stop`).
- `seed_demo` se brez `PREZA_DEMO_DB=1` ustavi, ker pobriše vse vstope in signale pravil.
- Demo analize imajo v posnetku sveče in temeljne podatke, zato so obeti (ADR-0014) izpolnjeni.
- Besedilo praznega portfelja in README-ji kažejo na nov ukaz.
- e2e na demo skladu: 32 uspešnih in 10 namerno preskočenih (delitev telefon/namizje). Prej je bilo 13 neuspešnih.
- Neodvisnega pregleda ni bilo, ker OpenCode Sol nima kvote.

**Odločitve:** vzorčni podatki samo v ločenem skladu, nikoli v živem (`preza`).

**Odprto:**
- Ob `--repeat-each` z več delavci se kopije testa watchliste (NVDA) med seboj motijo. Običajen zagon ni prizadet.
- Na disku C: sprosti prostor (97 %).
- Osnutek teze ASML čaka tvojo potrditev, BL-097 je tvoja odločitev, IB še ni povezan.

**Naslednji korak:** naslednja naloga M5.

---

## S-009 · 2026-10-27 · Analiza za odločitev

**Cilj:** stran analize naj pokaže samo tisto, kar potrebuješ za odločitev (uporabnikova pripomba: preveč podatkov naenkrat, "Underweight" ni razumljiv, manjkajo obeti po obdobjih).

**Narejeno:**
- ADR-0014: obeti za kratko (do 3 mesecev), srednje (~1 leto) in dolgo obdobje (3+ let) računa deterministična koda iz posnetka podatkov (`domain/outlook.py`). Agenti jih ne ocenjujejo. Vsak dokaz ima vir, čas, vrednost in prag.
- API: `AnalysisOut.outlook`, `AnalysisSummary.conviction` in `outlook_brief`.
- Web (BL-165): glava z dejanjem v navadnem jeziku ("Zmanjšaj delež" namesto "Underweight"), prepričanjem, trenutno ceno in pozicijo; tri kartice obetov; dokazi za rast levo in proti desno; "Ocena gre gor/dol, če". Utemeljitev, kontrolna ocena in koraki analitikov so zloženi, koraki so razvrščeni po agentu. `/analysis` ima tabelo s stolpci za dejanje, obdobja, za/proti, prepričanje in delnice v portfelju, na telefonu pa kartice.
- Testi: API 223, web 103 enotskih, tsc, eslint in i18n so čisti. Preverjeno v brskalniku na živi analizi ASML (namizje in 375 px, brez prelivanja). e2e: 19 uspešnih in 13 neuspešnih, vsi neuspešni potrebujejo vzorčne podatke, ki jih živa baza nima (BL-162).
- Neodvisnega pregleda ni bilo, ker OpenCode Sol nima kvote.
- Docker Desktop se je sesul (containerd SIGBUS, disk C: 97 % poln). Pomagalo je zaporedje `docker desktop stop`, `wsl --shutdown`, `docker desktop start`.

**Odločitve:** ADR-0014.

**Odprto:**
- BL-162: e2e potrebuje vzorčne podatke, ker test ASML preverja vzorčne vrednosti.
- Na disku C: sprosti prostor, sicer se Docker lahko spet sesuje.
- Osnutek teze ASML čaka tvojo potrditev, BL-097 je tvoja odločitev, IB še ni povezan.

**Naslednji korak:** BL-162 (vzorčni podatki za e2e), nato naslednja naloga M5.

---

## S-008 · 2026-10-25 · Oblikovanje za Android in Windows

**Cilj:** vmesnik naj na Androidu in Windows ne deluje kot aplikacija za Apple (uporabnikova pripomba).

**Narejeno:**
- ADR-0013: en platformno nevtralen vmesnik, kjer se platformi razlikujeta, sledi Material 3 (dotik) in Fluent 2 (miška).
- Web (BL-164): oznaka bližnjice `Ctrl K` (`⌘K` samo na macOS, skrita na dotiku), skupni `SegmentedButtons` (obrobljena skupina M3 namesto drsnika iOS), brez `backdrop-blur` (polna glava, temna prosojna plast), obrobljena polja, kritično dušene vzmeti, 48 px na dotik, navigacijska vrstica M3 s 5 cilji (Vstopi pod Več), polmeri 4/8/12, tanki drsniki, spletni manifest in barva teme, sistemska tipka nazaj zapre paleto ukazov in okno predloga.
- Reviewer (Sol) je našel napako v zgodovini kukala (`?peek=`): kukalo smo vrnili na prejšnje vedenje (`router.push`, nemodalno), ker ga tipka nazaj že zapre. `useBackToClose` velja samo za prekrivni plasti, ki nista v URL-ju.
- Testi: web 98 enotskih, e2e 19 uspešnih, 10 preskočenih (vzorčni podatki, BL-162). tsc, eslint, i18n čisti. Vsebnik `web` je na novi sliki.

**Odločitve:** ADR-0013.

**Odprto:**
- Preveri na pravem telefonu Android (namestitev kot aplikacija, tipka nazaj) in v Edge na Windows.
- Osnutek teze ASML še čaka tvojo potrditev; BL-097 ostaja tvoja odločitev; IB še ni povezan.

**Naslednji korak:** naslednja naloga M5 iz BACKLOG.

---

## S-007 · 2026-10-25 · BL-101 tedenski pregled tez

**Cilj:** tedenski pregled tez s predlogi in signalom `thesis_break` (ADR-0012).

**Narejeno:**
- API: tabeli `thesis_review` in `thesis_claim_review_proposal` (migracija 0013), posnetek vhoda z do 30 viri (10 mest za uradne), uradnost določi koda (EDGAR, `rss:prnewswire` z gostiteljem), družbena omrežja so vedno govorica. Predlog `broken` z vsaj enim uradnim citatom brez govorice ustvari `thesis_break` (prioriteta 0,8). Sprejem gre skozi obstoječo spremembo statusa z `actor = "user"`, 409 ob spremembi trditve; zavrnitev zahteva razlog in zapre odprt signal.
- Agents: `thesis_tracker` z nedeljskim tekom ob 06:15 UTC in dnevnim ob 06:20 UTC, en klic `cloud-deep` (4000 izhodnih žetonov, 660 s), brez odprte transakcije med klicem, `failed_unknown` po prekinitvi brez ponovnega klica.
- Web: predlogi na SCR-09 ločeno od dejanskega stanja trditve, sprejem z izrecno potrditvijo, zavrnitev z razlogom, SL/EN.
- Testi: API 269 (z DB na izolirani bazi), agents 68 (z DB), web 79 enotskih, e2e teze 8.
- Migracija 0013 na živi bazi (varnostna kopija `C:/Users/Jan/Documents/preza-backups/preza-pre-0013-20261025T193625Z.dump`, pisci ustavljeni, reviewer APPROVE). Vse storitve so na novi sliki iz te veje.

**Odločitve:** ADR-0012 (pregled ustvari predlog, status trditve spremeni samo uporabnik).

**Odprto:**
- Prvi živi pregled bo v nedeljo ob 06:15 UTC oziroma ob dnevnem teku, ko bo potrjena aktivna različica (osnutek ASML še čaka tvojo potrditev).
- Štirje regresijski testi agents padejo samo na Windows zaradi CRLF kontrolnih vsot (v Linux kontejnerju uspejo), BL-163.
- BL-097 ostaja tvoja odločitev.

**Naslednji korak:** oblikovanje za Android in Windows (BL-164).

---

## S-006 · 2026-10-25 · Živi viri podatkov in začetek M5 Teze

**Cilj:** preveriti žive povezave iz `.env` (IB še ni povezan), popraviti ugotovljeno in začeti M5.

**Narejeno:**
- Preverjeni viri: Finnhub, Yahoo, EDGAR (po vpisu e-pošte), PR Newswire RSS, Telegram. GlobeNewswire (403) in Business Wire (prazen vir) odstranjena, ker nista brezplačna (BL-059).
- notify ne izpisuje več Telegram žetona (`httpx` na WARNING), log očiščen. Migracija 0010 (`news_item.external_id` daljši za URL guid) na živi bazi.
- BL-034: Stooq privzeto izklopljen (JS izziv, ki ga ne obidemo).
- BL-066: EV/EBIT iz `evRevenue / operatingMargin` (Finnhub ne vrne `ebitTTM`); MSFT 25,7, 27 letnih točk.
- BL-091: Yahoo `funds_data` za UCITS: pozicije in sektorji za vse, TER manjka za Vanguard, `categoryName` vedno prazen.
- BL-095, BL-096: TER in ime indeksa iz `ucits_etfs.yaml` (KIID izdajatelja ima prednost pred Yahoo, z lastnim `ter_source`/`ter_as_of`, migracija 0011). VWRA/VWCE 0,14 % iz Vanguard KIID 2026-07-28.
- BL-100 končan: modeli teze, različice, trditve in dogodki (migracija 0012), API (osnutek iz končane analize, urejanje osnutka, izrecna potrditev, status trditve z razlogom in dokazi), SCR-09 seznam in podrobnosti, gumb "Ustvari osnutek teze" na SCR-06. Živi preizkus: osnutek teze ASML iz zagona `26e4dff1…` (6 trditev) čaka na tvoj pregled in potrditev.
- Migraciji 0011 in 0012 na živi bazi (varnostna kopija `C:/Users/Jan/Documents/preza-backups/preza_pre0012_20261025.dump`, pisci ustavljeni, reviewer APPROVE).
- BL-092: globoka analiza ASML uspešna prek MiniMax v 1501 s (Underweight, 6 sprožilcev). LiteLLM padci: `cloud-quick` → `cloud-deep` → `local-fast`.
- Testi web: 58 enotskih, e2e teze 4 (Playwright z `CHROMIUM_PATH` na chromium-1234; `analysis.spec.ts` potrebuje demo podatke, BL-162).
- Delo je delegirano OpenCode Sol agentom (general, architect), diff in teste je preveril glavni agent.

**Odločitve:** teza nastane šele na klik iz končane analize, sprožilci ostanejo besedilo (brez negiranja in parsanja številk), potrditev različice ne potrdi trditev, status trditve spremeni samo uporabnik z razlogom in dokazom.

**Odprto:**
- BL-097: `cloud-quick` (OpenCode Go) zavrača klice brez glave `x-opencode-session`; zdaj gre prek MiniMax. Potrebna je tvoja odločitev o ponudniku.
- BL-161: `expected_version` pri urejanju osnutka preverja različico, ne urejanj (spletni vmesnik pošlje samo spremenjene trditve).
- IB Gateway ni povezan (BL-023). Seznam spremljanja je prazen, zato Radar ne daje signalov.

**Naslednji korak:** BL-101 tedenski pregled tez in signal `thesis_break`.

---

## S-005 · 2026-10-22 · M3 zaključek in M4 Globoka analiza

**Cilj:** BL-068 do BL-070 in mejnik M4 (samostojno, brez uporabnika).

**Narejeno:**
- BL-068: signali `entry` in vrstica vstopov v Telegramu. BL-069: cona, stop in lestvica na grafu instrumenta. BL-070: kartica "V coni" na Pregledu.
- BL-080 do BL-082: nova storitev `services/agents` (paket `preza_agents`, lasten arq delavec na `arq:agents`). TradingAgents v0.7.0 iz gita, modeli prek LiteLLM vlog, `vendor_local` servira posnetek naše baze (brez Yahooja), koraki v `analysis_step`, SSE z `Last-Event-ID` (ADR-0011).
- BL-083: ETF analitik (profil sklada, prekrivanje skozi ETF-je v portfelju, TA-Lib, dva klica vlog), tedenska osvežitev profilov.
- BL-085: SCR-06 Analiza in CMP-12 AgentTimeline v živo, gumb "Globoka analiza" na instrumentu (Sonnet subagent).
- BL-090: globok ročni predlog ustvari zagon agentov s hipotezo; po zagonu jo en klic izrecno potrdi ali ovrže. Panel "Tvoja hipoteza".
- BL-089: kartica odločitve: deterministična kontrolna ocena, prepričanje, razred velikosti, sprožilci, `delta_note`. Razlika z oceno agentov zniža zaupanje (`control_disagrees`).
- BL-093: dnevni limit globokih analiz (privzeto 6) s prikazom porabe.
- BL-086: regresijski testi na 5 fiksnih posnetkih z "golden" datotekami.
- BL-088: kakovost poslovanja in dividende iz Finnhuba, kakovost v kontrolni oceni.
- Testi: API 162, agenti 31, web 18 enotskih, e2e 22.

**Odločitve:** ADR-0011 (ločena storitev agentov, lokalni vendor, SSE iz tabele, ETF cevovod, hipoteza po zagonu, kartica odločitve).

**Odprto:**
- BL-092: živi zagon prek LiteLLM z OpenCode Go/MiniMax (klici orodij, čas, cena). Prvi pravi preizkus M4.
- BL-091: Yahoo `funds_data` za UCITS kotacije. BL-066: nova polja Finnhuba. BL-059: viri novic.
- BL-023 živi IB Gateway, BL-160 zagon na tvojem strežniku.

**Naslednji korak:** BL-092 na tvojem strežniku (`docker compose up agents`), nato M5 Teze (sprožilci iz kartice odločitve postanejo trditve teze).

---

## S-004 · 2026-10-22 · Prevodi in M3 Vstopi

**Cilj:** BL-055 in mejnik M3 (samostojno, uporabnik ne more poganjati na svojem računalniku).

**Narejeno:**
- BL-055: povzetki dogodkov in razlogi signalov se prevedejo v jezik uporabnika (`local-fast`, en klic za do 8 povzetkov). Angleški izvirnik ostane kanoničen, prevod ima oznako "prevedeno" in izvirnik ob prehodu z miško. Telegram uporablja prevod.
- BL-060: pravila vstopov v `rules.yaml`, indikatorji s TA-Lib, test enakosti s trading-signals (Haiku subagent je pripravil posnetek).
- BL-061: pasovi vrednotenja (P/E, EV/EBIT, FCF donos proti 5 letom) iz Finnhuba in DCF iz veje `legacy` (Sonnet subagent).
- BL-062: `dip_analyst` (vzrok padca, `local-reason` → `cloud-quick`), dnevni tek vstopov ob 22:00 UTC, signal `entry` samo z nedotaknjeno tezo, `thesis_break` za temeljni vzrok pri poziciji.
- BL-063: lestvica postopnega nakupa (40/30/30, koraki po 1 ATR, nikoli nad trgom ali pod stopom).
- BL-064: SCR-03 Vstopi z zemljevidom vstopov (OV-05), cono in stopom (CMP-07), vzrokom (CMP-10), pravili, vrednotenjem in lestvico z zneskom (CMP-15). Preverjeno na namizju, telefonu in v temni temi.
- BL-065: izidi signalov po 1/5/20/60 dneh z alfo, MFE in MAE (Sonnet subagent), `/entries/outcomes`.
- Demo: vstopi z demo vrednotenjem in demo vzroki; ponovni seed zamenja demo Radar in vstope.
- Testi: API 151, web 11 enotskih, e2e 13.

**Odločitve:** ADR-0010 (TA-Lib, pravila kot konfiguracija, politika signalov za vstope).

**Odprto:** BL-066 polja Finnhuba na pravem omrežju; BL-059 viri novic; BL-023 živi IB Gateway; BL-160 zagon na tvojem strežniku.

**Naslednji korak:** M4 Globoka analiza (TradingAgents) ali manjše naloge BL-068 do BL-070.

---

## S-003 · 2026-10-22 · M1 in M2 v oblaku, brez uporabnika

**Cilj:** nadaljevati samostojno (uporabnik ne more poganjati na svojem računalniku).

**Odločitve (uporabnik):** Claude ni v cevovodu (brez API), `cloud-deep` = MiniMax z rezervo OpenCode Go. OpenCode Go modeli so javni. Tailscale je na vseh napravah. Ollama modele uporabnik določi kasneje. Za manjše naloge uporabljam manjše subagente (Sonnet, Haiku).

**Narejeno (M1):**
- API: pogodba virov + skupni testni nabor, usmerjevalnik s kvotami in rezervo (IB Gateway → Yahoo → Stooq), IBKR Flex odjemalec in parser (ponovni poskusi ob 1019, omrežne napake kot FlexError), tabele in migracija 0002 (hypertable na Timescale), UCITS seznam, `/instruments`, `/bars`, `/portfolio`, `/portfolio/sync`, `/watchlist`, arq opravila (Flex 05:15 UTC, sveče 21:30 UTC), demo podatki (`seed_demo`).
- Web: Portfelj (toplotni zemljevid, tabela, gotovina, sinhronizacija, stanje zadnje sinhronizacije), Watchlista (dve ravni, opombe, od dodaje, razveljavitev), Instrument (sveče, SMA50/200, volumen, RSI, ATR, 52-t. vrh/dno, lokaliziran graf), kukalo, predogled in ⌘K na pravem API.
- Testi: API 30 (vključno z integracijskimi na Postgres in preizkusom na TimescaleDB), web 11 enotskih, e2e 11 (Sonnet subagent je dodal 5 in našel napako v ⌘K, popravljeno).
- Preverjeno: migracije na TimescaleDB (hypertable), pot API → Redis → worker, napaka pri Flex sinhronizaciji se zapiše in prikaže.

**Narejeno (M2):**
- Viri novic: RSS/Atom, Finnhub, SEC EDGAR (napisal Sonnet subagent, 25 testov). Cevovod Radarja: shranjevanje po kanoničnem URL, grozdenje (vektorji ali besede), triaža z `local-fast`, odziv cene (z) in pozornost, ocena priložnosti, signali; govorica ostane "spremljaj" do uradne potrditve.
- API: `/radar/events` (trije pogledi), `/signals`, `/proposals` (analiza predloga: številke izračuna koda, model presodi hipotezo).
- Telegram bot (napisal Sonnet subagent): obvestila s tihimi urami in dnevnim limitom, gumbi, `/predlog`, jutranji povzetek.
- Web: Radar, Signali, Predlogi na pravem API.
- Napake, ki so jih našli testi in posnetki zaslona: proxy ni prepuščal novih poti; `POST /proposals` je vedno vrnil 500; manjkajoči Redis je zrušil zahtevo. Vse popravljeno.
- Testi: API 87, web 11 enotskih, e2e 11.

**Omejitve okolja (ne repoja):** omrežna politika blokira opencode.ai, api.minimax.io, sec.gov, stooq.com, Yahoo in ghcr.io bloke; Docker Hub omejuje (429), Googlov mirror deluje; build kontejnerji nimajo proxyja, zato slik API/web tu ni bilo mogoče zgraditi. Živih podatkov tu ni bilo, testi uporabljajo ročno sestavljene posnetke formatov.

**Odprto:** BL-023 živi IB Gateway, BL-027 ETF holdings, BL-011 imena modelov, celoten `docker compose up` na tvojem strežniku (BL-160).

**Naslednji korak:** M3 Vstopi (pravila, vzrok padca, lestvica) in BL-055, BL-056.

---

## S-002 · 2026-10-22 · Napreden UX, ročni predlogi, M0

**Cilj:** odločitve iz pregleda prototipov, napreden React UX, ročni predlogi, mejnik M0.

**Narejeno:**
- Pravila: DESIGN §8 (motion sistem MO-01–MO-10), §9 (povezovanje LX-01–LX-08), §10 (pregledi OV-01–OV-07), §11 (ročni predlogi, SCR-12, CMP-30). ADR-0008 (UCITS), ADR-0009 (Motion UX). Ime Preža in model Qwen 3.8 27B (4-bit) potrjena.
- **M0 zgrajen:**
  - `services/api`: FastAPI, `/health`, `/system/status` (sonde za 7 servisov s časovno omejitvijo), Alembic (Timescale + pgvector), arq worker, izvoz OpenAPI. 6 testov, ruff, mypy strict.
  - `apps/web`: Next.js 16 lupina (stranski meni z drsnim indikatorjem, spodnja navigacija na telefonu, glava s stanjem sistema), svetla/temna/sistemska tema brez utripa, SL/EN (next-intl, 220+ ključev, preverjanje enakosti), ⌘K paleta, kukalo v URL, EntityLink s predogledom, navzkrižno poudarjanje, AnimatedNumber, Treemap, PulseTimeline, Funnel, RegimeStrip, Sparkline, kartice signalov z razširitvijo in razveljavitvijo, obrazec za ročne predloge, stran `/ux`. 9 enotskih testov, 6 e2e testov (Playwright, namizje + telefon).
  - `infra`: Docker Compose (postgres, redis, litellm, api, worker, web, ib-gateway v profilu `broker`), LiteLLM 5 vlog s fallbacki.
  - CI (GitHub Actions): API, web (i18n, tipi API, lint, tipi, testi, build, e2e), preverjanje compose.
- Najdena in popravljena napaka hidracije: Node in Chromium različno ločita 4-mestna števila v slovenščini, zato `useGrouping: "always"`.

**Odločitve (uporabnik):** UCITS ETF-ji, ime Preža, Qwen 3.8 27B 4-bit, napreden React UX z animacijami in povezanimi pogledi, ročni predlogi v analizo.

**Odprto:**
- Celoten `docker compose up` v tem okolju ni bil preizkušen (ni Docker daemona); posamezni servisi, build in e2e so preizkušeni (BL-160).
- Imena modelov OpenCode Go v `.env` preveri na `/models` (BL-011).
- BL-012, BL-013, BL-016 so na tvoji strani (GPU naprava, Claude kredit, Tailscale).

**Naslednji korak:** BL-160 (zagon na tvojem strežniku), nato M1: Flex, IB Gateway, svečke, Portfelj (SCR-08), Instrument (SCR-05).

---

## S-001 · 2026-10-22 · Analiza, zasnova, pravila, prototipi

**Cilj:** izbrati osnovo iz odprtokodnih repojev, zasnovati rešitev, postaviti pravila projekta in UI prototipe.

**Narejeno:**
- Analiza 6 kandidatov: LEAN, TradeMaster, trading-signals, TradingAgents, Vibe-Trading in IBKR API-ji → [`docs/research/2026-10-22-analiza-kandidatov.md`](./docs/research/2026-10-22-analiza-kandidatov.md).
- Podrobna zasnova in seznam prevzemov → [`docs/research/2026-10-22-zasnova-resitve.md`](./docs/research/2026-10-22-zasnova-resitve.md).
- Prejšnja koda premaknjena na vejo `legacy`. Na delovni veji je nova struktura monorepa.
- Pravila: README, AGENTS, BRAND, VOICE, DESIGN, PLAN, BACKLOG, SESSIONS, ADR-0001 do ADR-0007.
- Osnova i18n: `apps/web/messages/sl.json` in `en.json`.
- UI prototipi na Artifact platnu (BL-003): 7 zaslonov + tokeni, preklop teme in jezika, povezave med zasloni. Kopija v `design/canvas/`.
- Pregled starega projekta `PksOck/trading-list` (PHP): samo izkušnje in model podatkov → [`docs/research/2026-10-22-trading-list-prevzem.md`](./docs/research/2026-10-22-trading-list-prevzem.md). Novi BL-018, BL-032, BL-033, BL-088, BL-089.

**Odločitve (uporabnik):**
- Dolgoročno trgovanje, občasno kratkoročno in opcije. Podatki v realnem času niso potrebni.
- Fokus: priložnosti iz novic in špekulacij ter dobre (ponovne) vstopne točke, za delnice in ETF-je.
- Docker lokalno. GPU naprava v LAN s 24 GB VRAM, Qwen 3.8 27B (4-bit).
- Naročnine: Claude **Pro**, OpenAI, OpenCode. IBKR PRO.
- Radar v treh pogledih: Novi predlogi (širše), Watchlista, Portfelj.
- Obvestila prek Telegrama.
- Slovenščina privzeto, preklop na angleščino. Svetla in temna tema.
- Stari projekt ni predloga: gradimo na novo in bolje.

**Odprto:**
- Točna verzija lokalnega modela in hitrost triaže (BL-012).
- Višina Claude Pro Agent SDK kredita (BL-013).
- Delovno ime "Preža": potrdi ali zamenjaj (BRAND.md §1).
- Pregled prototipov (BL-004).
- Dostopnost ameriških ETF-jev za EU malega vlagatelja (BL-018). Prototipi zato uporabljajo UCITS ETF-je (VWRA, EQQQ, IUES).

**Naslednji korak:** BL-004 (pregled prototipov), nato M0 (BL-006 do BL-016).

---

## Predloga

```markdown
## S-xxx · LLLL-MM-DD · <kratek cilj>

**Cilj:**
**Narejeno:** (z referencami BL-xxx, commit/PR)
**Odločitve:** (+ ADR-xxxx, če nastane)
**Odprto:**
**Naslednji korak:**
```
