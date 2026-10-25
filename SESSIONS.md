# SESSIONS.md: dnevnik delovnih sej

Najnovejša seja je na vrhu. Vsaka seja ima ID `S-xxx`, datum, cilj, rezultat, odločitve in odprta vprašanja. Predloga je na dnu.

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
