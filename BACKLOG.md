# BACKLOG.md

**Statusi:** `next` (naslednje) · `doing` (v delu) · `done` · `blocked` (z razlogom) · `later`
**Pravila:**
- ID je stalen in se ne uporabi ponovno.
- Nova naloga dobi naslednji prost ID v razponu svojega mejnika (PLAN.md §6). Ko je razpon poln, dobi naslednji prost ID od BL-160 naprej.
- Vsaka naloga navede reference (`SCR`, `CMP`, `ADR`) in definicijo končanega.

---

## M0: Temelji

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-001 | Pravila projekta: BRAND, VOICE, DESIGN, PLAN, BACKLOG, SESSIONS, AGENTS, ADR-ji | S-001 | done |
| BL-002 | Struktura monorepa z README v vsaki mapi, veja `legacy` | S-001 | done |
| BL-003 | UI prototipi na Artifact platnu: tokeni, SCR-01, 02, 03, 05, 06, 07, 11 (kopija v `design/canvas/`) | DESIGN §4 | done |
| BL-004 | Pregled prototipov z uporabnikom in popravki (komentarji na platnu) | BL-003 | done |
| BL-005 | Prototipi še za SCR-04, 08, 09, 10, 12 + mobilna različica SCR-01/02 (zdaj neposredno v React, ne na platnu) | DESIGN §4 | later |
| BL-006 | `infra/docker-compose.yml`: postgres (Timescale + pgvector), redis, litellm, api, worker, web; `.env.example` | ADR-0001 | done |
| BL-007 | `apps/web`: Next.js 15 + Tailwind 4 + shadcn/ui, tokeni iz DESIGN §2 kot CSS spremenljivke, `data-theme` preklop | DESIGN §2 | done |
| BL-008 | i18n: next-intl, `messages/sl.json` + `en.json`, preklop SL/EN, CI preverjanje manjkajočih ključev | ADR-0005, VOICE §6 | done |
| BL-009 | CMP-01 AppShell + CMP-02 SystemStatus (prazni podatki) | DESIGN §3 | done |
| BL-010 | `services/api`: FastAPI okostje, SQLAlchemy 2, Alembic, `/health`, OpenAPI → `openapi-typescript` | ADR-0002 | done |
| BL-011 | LiteLLM `config.yaml`: 5 vlog, proračuni, fallbacki; test klica vsake vloge (konfiguracija narejena, živi test na tvojem strežniku) | ADR-0004 | doing |
| BL-012 | Ollama na GPU napravi: potrdi model (Qwen ~27B Q4), dodaj embed model, izmeri hitrost triaže (novic/min) | PLAN §4 | next |
| BL-013 | ~~Claude Pro Agent SDK~~ Claude ni v cevovodu (S-003). Namesto tega: MiniMax API ključ in izbira modela za `cloud-deep` | PLAN §4 | next |
| BL-014 | CI (GitHub Actions): ruff, mypy, pytest, eslint, tsc, vitest, i18n ključi | AGENTS §4 | done |
| BL-015 | `NOTICE` datoteka in predloga glave za prevzeto kodo | AGENTS §4 | done |
| BL-016 | Tailscale na strežniku, HTTPS (Tailscale cert), dostop s telefona (Tailscale je že nameščen na vseh napravah) | ADR-0001 | next |
| BL-019 | UX temelji: motion tokeni, MO-01–MO-10 primitivi, ⌘K (CMP-23), kukalo (CMP-21), EntityLink + HoverPreview, AnimatedNumber, Treemap, PulseTimeline, Funnel, RegimeStrip, Sparkline; stran `/ux` z vzorčnimi podatki | ADR-0009, DESIGN §8–§10 | done |
| BL-160 | Uporabniški pregled M0 lupine na tvojem strežniku (docker compose up) in popravki UX | S-002 | next |
| BL-017 | Varnostne kopije: nočni `pg_dump` v ločen disk | ADR-0001 | later |
| BL-018 | Preveri dostopnost instrumentov za EU malega vlagatelja pri IBKR (PRIIPs/KID): ameriški ETF-ji niso na voljo, univerzum ETF = UCITS (LSE/Xetra), valute USD/EUR/GBP | ADR-0008 | done |

## M1: Podatki + portfelj

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-020 | Pogodba vira podatkov (Protocol + skupni pytest nabor), prepis iz legacy `provider-contract.ts` | research §3.6 | done |
| BL-021 | Router virov s kvotami in fallbackom (prepis legacy `composite-provider` + `quota-tracker`) | research §3.6 | done |
| BL-022 | IBKR Flex: token, Flex Query (pozicije, posli, gotovina, dividende), parser, nočna sinhronizacija | PLAN §5.1 | done |
| BL-187 | Ročni uvoz izpisa Flex XML na Portfelju (`POST /portfolio/import`, surovo telo XML do 10 MB, brez tokena); zapis v zadnjo sinhronizacijo in osvežitev tečajev | BL-022 | done |
| BL-023 | IB Gateway Docker (`gnzsnz/ib-gateway`, READ_ONLY_API, IBC auto-restart), ločen API uporabnik (compose profil `broker` narejen; živi preizkus na strežniku) | ADR-0006 | doing |
| BL-024 | `services/broker`: ib_async klient (EOD svečke, contract details), prepis delov Vibe-Trading `ibkr/local.py` | research §3.2 | done |
| BL-025 | Tabele `instrument`, `bar` (hypertable), `position`, `trade`, `cash`, `watchlist` | research §4.2 | done |
| BL-026 | Univerzum: S&P 500 + Nasdaq 100 + seznam ETF-jev (konfiguracija), dnevna posodobitev sestave | PLAN §2 | done |
| BL-027 | ETF profili: TER, AUM, holdings (izdajatelji CSV / yfinance), sektorji, države (seznam UCITS + ISIN narejen; holdings še ne) | research §5.5 | doing |
| BL-028 | SCR-08 Portfelj | DESIGN §4 | done |
| BL-029 | SCR-05 Instrument: CMP-13 PriceChart (lightweight-charts + trading-signals), ključni podatki, CMP-08 | DESIGN §4 | done |
| BL-030 | Watchlista: dodaj/odstrani, skupine | SCR-05 | done |
| BL-031 | Iskanje ⌘K (simbol, ime) | CMP-01 | done |
| BL-032 | Model watchliste: raven (aktivna / zaloga), vir ideje, oznake, cena in datum dodaje, donos od dodaje, cenovna opozorila, pregledano | research/trading-list §1 | done |
| BL-033 | (neobvezno) Uvoz idej in tez iz `trading-list` (MySQL izvoz) | research/trading-list §1 | later |
| BL-034 | Stooq privzeto izklopljen (`STOOQ_ENABLED=false`): stooq.com skriptam vrne JS izziv, ki ga ne obidemo; Yahoo ostane vir dnevnih cen | S-006 | done |

## M2: Radar

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-040 | Ingest novic: Finnhub, RSS (GlobeNewswire, PR Newswire, Business Wire), normalizacija, dedupe po URL | PLAN §5 | done |
| BL-041 | Ingest EDGAR: 8-K, Form 4, 13D/G (User-Agent, 10 req/s) | PLAN §5 | done |
| BL-042 | Reddit/StockTwits pozornost (omembe proti 30-dnevni bazi) za watchlisto + kandidate (še ni vira; zdaj samo RSS, Finnhub, EDGAR) | PLAN §5 | later |
| BL-043 | Embed + grozdenje v `event` (pgvector, cos > 0,85, okno 48 h) | PLAN §5 | done |
| BL-044 | Triaža `local-fast` z JSON shemo + testi na posnetkih 50 novic | VOICE §7 | done |
| BL-045 | Deterministični kontekst: odziv cene (z-score proti sektorju/SPY), relativni volumen | research §5.2 | done |
| BL-046 | Ocena priložnosti (konfiguracija uteži, verzija) | research §5.2.1 | done |
| BL-047 | Govorice: oznaka, nadgradnja ob uradni potrditvi | AGENTS §3.4 | done |
| BL-048 | Shema `Signal` + tabela, API | research §4.2 | done |
| BL-049 | SCR-02 Radar s tremi pogledi (CMP-04, 05, 16) | DESIGN §4 | done |
| BL-050 | SCR-04 Signali (nabiralnik) | DESIGN §4 | done |
| BL-051 | Telegram bot: obvestila, gumbi Odpri / Spremljaj / Zavrzi, omejitev na tvoj chat_id | ADR-0007 | done |
| BL-052 | SCR-01 Pregled (prva verzija) (portfelj in vrednost sta živa; utrip, lijak in režim še vzorčni) | DESIGN §4 | doing |
| BL-053 | Ročni predlogi: model `proposal`, API, CMP-30, ⌘K akcija, Telegram `/predlog`, ekstrakcija simbolov iz prilepljenega besedila (local-fast), hitra analiza | DESIGN §11 | done |
| BL-054 | SCR-12 Predlogi | DESIGN §11 | done |
| BL-055 | Prevod povzetkov dogodkov in signalov v jezik uporabnika (local-fast), oznaka "prevedeno" | VOICE §7 | done |
| BL-056 | Grozdenje brez vektorjev: upoštevaj isti simbol in tip dogodka v 24 h, ne samo besede v naslovu | PLAN §5 | done |
| BL-057 | Telegram bot: besedila odgovorov (/start, /predlog, gumbi) v messages, ne v kodi | VOICE §6 | later |
| BL-058 | Jutranji povzetek ob 7:30 po lokalnem času (zdaj 05:30 UTC, pozimi 6:30) | ADR-0007 | later |
| BL-059 | RSS in EDGAR preverjena v živo: ohranjen samo PR Newswire; GlobeNewswire in Business Wire opuščena kot nebrezplačna vira; oblika EDGAR feeda potrjena | research §5.1 | done |
| BL-182 | Spremljani viri (osebe, kanali, strani): model `watched_source` (vrsta, URL, oznaka, aktivno), API in seznam v nastavitvah. Vse objave so vrste `social`, torej govorica, dokler je ne potrdi uradni vir (AGENTS §3.4). Primera: YouTube `@jeremylefebvremakesmoney7934`, Instagram `moby.invest` | AGENTS §3.4 | later |
| BL-183 | YouTube: nove objave kanala prek YouTube Data API (seznam naloženih videov), prepis podnapisov, povzetek `local-fast`/`cloud-quick` s simboli in trditvami v `event`. Številke iz videa so trditve avtorja, ne dejstva. Preveri kvoto API in pravno podlago za prepise (uradni API daje podnapise samo lastniku kanala) | BL-182 | later |
| BL-184 | Instagram: uradni Graph API bere tuje račune samo prek lastnega poslovnega računa (Business Discovery), strganje krši pogoje uporabe. Odloči: Business Discovery, ročno posredovanje objav (Telegram `/predlog`, BL-053) ali opustitev vira | BL-182 | later |
| BL-185 | Spletne strani: RSS, kjer obstaja, sicer periodično branje strani s primerjavo vsebine (spoštuj `robots.txt`), nova vsebina gre v isti cevovod kot novice | BL-182 | later |
| BL-186 | Predlog iz slike: prilepljen posnetek zaslona (CMP-30 v spletu, fotografija v Telegramu) → izluščeni simboli s kratkim kontekstom → uporabnik potrdi, katere doda na watchlisto → takoj hitra analiza (`depth=quick`), globoka v nizko prioritetni vrsti, ko je delavec prost. Potrebuje vlogo LiteLLM s podporo slikam (sprememba ADR-0004) ali lokalni OCR pred `local-fast`. Številke s slike niso dejstva | BL-053 | later |

## M3: Vstopi

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-060 | Pravila vstopov (TA-Lib) kot konfiguracija + test enakosti s trading-signals | research §5.3 | done |
| BL-061 | Pasovi vrednotenja (P/E, EV/EBIT, FCF yield proti 5-letni mediani), DCF prepis iz legacy | research §5.3 | done |
| BL-062 | `dip_analyst`: vzrok padca (trg / sektor / začasno / temeljno), `local-reason` → `cloud-quick` | research §5.3 | done |
| BL-063 | Lestvica postopnega nakupa (ATR) | CMP-15 | done |
| BL-064 | SCR-03 Vstopi | DESIGN §4 | done |
| BL-066 | Preveri polja Finnhub `/stock/metric` na pravem omrežju (P/E, EV/EBIT, P/FCF serije, ROE, marže, rast, dolg, dividende) in dopolni zgodovino EV/EBIT. Preverjeno 2026-10-25: `ebitTTM` in serija `evEbit` manjkata, EV/EBIT se izpelje iz `evRevenue / operatingMargin` (MSFT 25,7, 27 letnih točk) | ADR-0010 | done |
| BL-067 | `dip_analyst`: primerjava s sektorskim ETF-jem (ne samo s SPY), sektor iz profila instrumenta | research §5.3 | later |
| BL-068 | Vstopi v Telegramu: obvestilo ob novem signalu `entry` in vrstica v jutranjem povzetku | ADR-0007 | done |
| BL-069 | Instrument (SCR-05): cona, stop in raven lestvice na grafu (CMP-07 na CMP-13) | DESIGN §4 | done |
| BL-070 | Pregled (SCR-01): kartica "V coni" z zemljevidom vstopov v malem | DESIGN §10 | done |
| BL-065 | `signal_outcome`: nočni izračun donosa po 1/5/20/60 dneh in alfe | research §5.8 | done |

## M4: Globoka analiza

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-080 | TradingAgents adapter (zaklenjena verzija, LiteLLM backend URL, checkpointing) | ADR-0003 | done |
| BL-081 | `vendor_local`: TradingAgents bere iz naše baze | research §3.1 | done |
| BL-082 | Worker + Redis pub/sub + SSE → CMP-12 AgentTimeline | research §3.1 | done |
| BL-083 | ETF analitik (profil sklada, prekrivanje skozi ETF-je, dva klica vlog; ADR-0011) | research §5.5 | done |
| BL-084 | (odloženo) `claude_runner` samo, če se kasneje odločiš za Claude Agent SDK | PLAN §4 | later |
| BL-085 | SCR-06 Analiza | DESIGN §4 | done |
| BL-086 | Regresijski testi agentov na 5 fiksnih posnetkih (sintetični; resnične dodaj po BL-059/066/091) | research §3.1 | done |
| BL-087 | Znanje za agente: prepis izbranih Vibe-Trading skills v `services/agents/knowledge/` | research §3.2 | later |
| BL-088 | Dodatna analitika: kakovost (ROE, marže, rast, dolg) in dividende iz Finnhuba, ocena kakovosti v kontrolni oceni | research/trading-list §2 | done |
| BL-094 | Relativno vrednotenje proti sorodnim podjetjem (Finnhub `/stock/peers`) in odkupi delnic (sprememba števila delnic) | research/trading-list §2 | later |
| BL-095 | TER za ETF-je, kjer ga Yahoo ne vrne (Vanguard): vir iz KID izdajatelja v `ucits_etfs.yaml` z `source` in `as_of`, prednost pred Yahoo. VWRA/VWCE: 0,14 % iz KIID 2026-07-28 (`kid:vanguard`); stolpca `ter_source`, `ter_as_of` (migracija 0011) | ADR-0011 | done |
| BL-096 | `index_name` za UCITS ETF-je iz `ucits_etfs.yaml` (Yahoo `categoryName` je prazen) | ADR-0011 | done |
| BL-097 | Ponudnik za `cloud-quick`: OpenCode Go sprejema samo klice iz OpenCode, zato `cloud-quick` in `cloud-deep` tečeta na MiniMax (časovna meja 300 s oziroma 600 s, brez ponavljanja ob timeoutu), padec na lokalni vlogi | ADR-0004 | done |
| BL-090 | Ročni predlog → standardna/globoka analiza: hipoteza uporabnika v kontekstu, izrecna potrditev/ovržba v izhodu (hitra in standardna globina že delujeta v M2) | DESIGN §11 | done |
| BL-091 | Preveri Yahoo `funds_data` za UCITS kotacije (LSE, Xetra) na pravem omrežju: TER, top pozicije, sektorji. Preverjeno 2026-10-25: pozicije in sektorji za vse; TER manjka za Vanguard (VWRA, VWCE); `categoryName` je vedno prazen (glej BL-095, BL-096) | ADR-0011 | done |
| BL-092 | Živi preizkus globoke analize prek LiteLLM (`cloud-quick`/`cloud-deep` z OpenCode Go/MiniMax): klici orodij, čas in cena enega zagona. 2026-10-25: ASML uspešno prek MiniMax v 1501 s (Underweight, 6 sprožilcev); najdaljša koraka debata bull 407 s, conservative 291 s | ADR-0011 | done |
| BL-093 | Dnevni limit globokih analiz (`DEEP_DAILY_LIMIT`, privzeto 6, `GET /analyses/quota`, 429 `daily_limit_reached`; globok predlog nad limitom dobi samo hitro presojo) in prikaz porabe na SCR-06 | research/trading-list §4 | done |
| BL-089 | Shema odločitve: sprožilci ocene (→ trditve teze), `delta_note` proti prejšnji analizi, prepričanje, razred velikosti, deterministična kontrolna ocena | research/trading-list §3 | done |

## M5: Teze + uspešnost

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-100 | Model teze, SCR-09, CMP-11 (sprožilci iz kartice odločitve BL-089 postanejo trditve teze). Modeli in migracija 0012, API (osnutek iz analize, urejanje, potrditev, status trditve z dokazi), SCR-09 seznam in podrobnosti, gumb na SCR-06 | research §5.6 | done |
| BL-101 | Tedenski pregled tez (`cloud-deep`) + signal `thesis_break` (ADR-0012) | research §5.6 | done |
| BL-102 | SCR-10 Uspešnost: `GET /track-record?horizon_days=1|5|20|60`, zadetki in donos v smeri signala, alfa proti shranjenemu indeksu, tvoji predlogi ločeno od sistemskih, vrsta × vir, kalibracija moči v 5 razredih, oznaka pod 10 izidi; demo seed doda pretekle signale z izidi | research §5.8 | done |
| BL-103 | Kalibracija uteži: iz izidov SCR-10 predlagaj nove uteži pravil in virov (deterministično, z intervalom zaupanja); sprememba uteži samo z izrecno potrditvijo (ADR-0015) | BL-102 | done |
| BL-161 | Števec urejanj osnutka teze: `expected_version` zdaj preverja zaporedno številko različice, ne urejanj; `updated_at` ne sledi urejanju trditev | BL-100 | done |
| BL-162 | Demo podatki za e2e: ločen sklad `preza-demo` (`infra/docker-compose.demo.yml`, web na :3100, `scripts/demo-stack.sh`), `seed_demo` zahteva `PREZA_DEMO_DB=1`, demo analize imajo sveče in temeljne podatke za obete. Lokalno se uporablja Chromium 1234 prek `CHROMIUM_PATH` | S-010 | done |
| BL-163 | Regresijski testi agents: golden kontrolne vsote padejo na Windows zaradi CRLF (`.gitattributes` za `tests/regression` ali normalizacija pred hashem) | BL-101 | done |
| BL-164 | Oblikovanje za Android in Windows (ADR-0013): bližnjice po platformi, segmentirani gumbi M3, brez zameglitve, 48 px na dotik, navigacijska vrstica M3, manifest, tipka nazaj | S-008 | done |
| BL-165 | Analiza za odločitev (ADR-0014): obeti kratko/~1 leto/3+ let iz posnetka, dokazi za in proti, cena in pozicija v glavi, koraki analitikov v spustnem seznamu, več stolpcev v `/analysis` | S-009 | done |
| BL-166 | Cene ob dodajanju na watchlisto: posel `refresh_instrument_bars` takoj prenese dnevne sveče in izpolni ceno ob dodajanju (zaključni tečaj na dan dodajanja); prej samo nočni `refresh_bars` ob 21:30 UTC | S-012 | done |
| BL-167 | Analiza porabi manj žetonov: deterministična koda pripravi zgoščene vhode, LLM samo presodi in združi (poročilo 25. 10.: ~3 M žetonov na MiniMax) | S-012 | done |
| BL-168 | Nastavitve žetonov v LiteLLM in `client.py`: `max_completion_tokens` namesto `max_tokens` za MiniMax, izklop razmišljanja za analitike, preveri podporo `json_schema`, loči `finish_reason=length` od napake sheme, uskladi timeout odjemalca (300 s) in proxyja (600 s). Pri prvi vitki analizi AMD je bilo razmišljanje okoli 48 % vseh žetonov. Razmišljanja ni mogoče izklopiti: nameščeni MiniMax-M3.1-Flash zavrne `thinking=disabled` | BL-167 | done |
| BL-169 | Radar: predpomnilnik triaže po hashu vsebine (danes ob novem članu grozda znova pošlje vse stare, ~450 k žetonov na dan na `local-fast`), prevodi dogodkov se razveljavijo, ko se povzetek spremeni | BL-167 | next |
| BL-170 | Vstopne točke: `analyze_dip` skrajša naslov in povzetek dogodka, da vhod ostane pod 16 k | BL-167 | next |
| BL-171 | Odstrani TradingAgents iz poti delnic: knjižnica, `deep_research/` graf in njegovi testi (ostane posnetek in vir EDGAR) | BL-167 | later |
| BL-172 | Poraba žetonov v UI: `models.usage` analize prikaži v podrobnostih (klici, vhod, izhod) | BL-167 | later |
| BL-173 | Analiza delnice pred začetkom naloži manjkajoče temelje in novice Finnhub za simbol, ki ni na watchlisti ali v portfelju | BL-167 | done |
| BL-174 | Ročno dodan instrument (npr. AMD) ima `kind=unknown` brez borze in valute: dopolni podatke iz profila Finnhub; tedenski posel temeljev naj zapiše `sync_run` | BL-173 | next |
| BL-175 | Novice Finnhub (shranjene in sveže) imajo vedno `is_rumor=False`, zato nepotrjen prevzem šteje kot potrjen dokaz. Dodaj determinističen klasifikator govoric (npr. "reportedly", "according to sources", "v pogovorih") pred registrom dokazov | BL-173 | done |
| BL-176 | `models.usage` naj pri vsakem klicu zapiše število poskusov; zdaj se vhod popravnega poskusa prišteje in klic na videz preseže 16k | BL-167 | next |
| BL-177 | `sweep_runs` naj teke, ki so predolgo v stanju `running` in nimajo živega arq opravila, označi kot `failed` z razlogom | BL-173 | done |
| BL-178 | Radar (`radar/cluster.py`) naj za neuradne dogodke uporabi isti `looks_like_rumor`; zdaj označi govorico samo pri vrsti `social` | BL-175 | done |
| BL-179 | `thesis_tracker/runner.py` preslika vse napake LLM v `role_unavailable`; ohrani `error_code` (`output_truncated`, `schema_validation_failed`) za diagnostiko | BL-168 | done |
| BL-180 | Rok 540 s velja za posamezen HTTP klic; s popravnim poskusom lahko klic `complete_json` traja do dvakrat dlje. Dodaj skupni rok za celoten klic | BL-168 | later |
| BL-181 | Preveri, ali MiniMax prek LiteLLM res uveljavi `json_schema` (zdaj ščiti samo lokalno preverjanje in popravni poskus) | BL-168 | later |

## M6: Opcije

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-120 | Opcijska veriga iz IBKR (zakasnjeno) | research §5.7 | later |
| BL-121 | Payoff, Greeks, verjetnost (prepis Vibe-Trading `options.ts` / `options_payoff.py`) | research §3.2 | later |
| BL-122 | `options_strategist` (Claude) + varovala (brez golih callov, likvidnost) | research §5.7 | later |
| BL-123 | SCR-07 Opcije, CMP-14 | DESIGN §4 | later |

## M7: Naročila s potrditvijo

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-140 | `order_draft`, varovala (`guards.py`, prepis legacy `risk.ts`), revizijska sled | ADR-0006 | later |
| BL-141 | Paper račun: oddaja z dvojno potrditvijo (CMP-18) | ADR-0006 | later |
| BL-142 | Odločitev o prehodu na živi račun (nov ADR) | ADR-0006 | later |

## UX/UI: načrt in specifikacija

Opusov dokument je prevzet iz Claudove veje pri `28f2990`. Izvedbena veja `fix/signal-read-contracts` izhaja iz kode `1855eb8`; Val −1 je izveden spodaj. To ne pomeni združitve vseh sočasnih sprememb ali implementacije vseh valov.

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-188 | Celovit UX/UI načrt in pregled Astra; prevzeta Opusova dopolnitev s FIX-A/B, UX-00 in viri dividend | [načrt](./docs/superpowers/plans/2026-10-28-celovita-uxui-nadgradnja.md), izvor `28f2990` | done |
| BL-189 | SPEC v0.1: pregled Opusovih komentarjev, skupne pogodbe in sledljivost modulov, podrobni Val −1 (FIX-A/B, UX-00), meje dividendnih ocen in dokazna vrata; dokumentarni osnutek zaključen v S-015, izvedba ločeno BL-190–192 | [SPEC](./docs/superpowers/specs/2026-10-28-celovita-uxui-spec.md), S-015 | done |
| BL-190 | FIX-A: normalizacija poteka new/watching pred filtri in limitom, stabilen vrstni red, ohranitev uporabnikovih odločitev | [Val −1](./docs/superpowers/specs/2026-10-28-val-minus-1-spec.md), `0720806`, S-016 | done |
| BL-191 | FIX-B: GET signal po UUID, read-only detail, varen Close/Escape/Back in obnova fokusa, ločen cache in generirana API pogodba | [Val −1](./docs/superpowers/specs/2026-10-28-val-minus-1-spec.md), `aa5d62a`, S-016 | done |
| BL-192 | UX-00: read-only inventura virov in dejanske pokritosti po računu; matrika 19 metrik, agregati in ponovljivi SQL; podatkovne vrzeli ostajajo izrecne | [raziskava](./docs/research/2026-10-29-izvedljivost-metrik.md), S-016 | done |
| BL-193 | Audit refresh fundamentov dodan (izid po instrumentu); uspešen živi refresh in vzrok prazne ciljne populacije ostajata za potrditev | UX-00, UX-11, S-017 | doing |
| BL-194 | Potrditi kotacijo/valuto/vrsto devetih unknown instrumentov na watchlisti; ne privzeti USD ali napačnega simbola | UX-00, UX-01 | next |
| BL-195 | Skupna read pogodba, DataMeta in izbirni stolpci; vir/čas/osnova, vrzeli, ločen forward P/E | ADR-0017/0018, S-017 | done |
| BL-196 | Zadnji snapshot po računu v get_portfolio/user_symbols, tudi prazen; regresije različnih datumov računov | S-017 | done |
| BL-197 | Raziskovalni pogledi: zadnja uspešna analiza, varni predlogi/retry, točen detail Radar/Vstopi/Signali, kohorta izidov in postopno razkritje | S-017 | done |
| BL-198 | Dividendna evidenca, odprti obračuni, pokritost, osnova projekcije in UI; sintetična pogodba, živi format v BL-202 | ADR-0020, S-017 | done |
| BL-199 | Skupne tabele, računski portfelj/watchlista, identiteta, Pregled in povezovanje; integracija demo | ADR-0017/0018, S-017 | done |
| BL-200 | Politike procesov, urniki, pavza, transakcijska kvota, predogled/sprejem paketa in sledi | ADR-0019, S-017 | done |
| BL-201 | Regresijski pregled in ločen demo :3100; prenos :3000 izrecno zadržan do uporabnikove potrditve | S-017, pregled sprememb | done |
| BL-202 | Potrditi razširjeni zasebni Flex XML, FinancialInstrumentInformation, dividendne identitete/davke/popravke in dejansko pokritost | ADR-0020 | next |
| BL-203 | Nadaljnji UX po pregledu: poimenovani profili, primerjava vrstic, enoten iskalnik, preostali paneli instrumenta/analize, 200-% povečava | pregled sprememb S-017 | next |
| BL-204 | Trajno vezati ključ idempotence oddaje predloga na shranjeni osnutek čez reload in izgubljen odgovor | S-017 | next |
| BL-205 | Pred prenosom zapreti dodatne Flex robove: BASE_SUMMARY-only cash in nepopolne vrstice brez potrjene valute | S-017 | next |
| BL-206 | Vedno dosegljiv standardni profil, vrnjeni stolpci portfelja, semantične barve, trend z datumi in stanje cone | S-018 | done |
| BL-207 | Vrnitev uporabnih vizualizacij Pregleda na dejanskih podatkih, moč/barve, legenda Radarja in pravilna kohorta lijaka | S-018 | done |
| BL-208 | Poenostavljene nastavitve, glavno stikalo avtomatskih LLM klicev, ročni izvor/okna, SMTP več prejemnikov in deduplikacija | ADR-0021, S-018 | done |
| BL-209 | Dividendna oblikovna uskladitev, ločene ocene in kontrola knjižb; ponovljivi sintetični primeri tez | S-018 | done |
| BL-210 | Read-only testiranje shranjenih signalov/končnih mnenj, deterministični stroški/datum/smer, vidni preskoki in bounded SQL | ADR-0022, S-018 | done |
| BL-211 | Potrjeni makro podatkovni viri VIX/US10Y/DXY in zadostna zgodovina nedvoumne kotacije SPY; ohraniti čas/vir | S-018 | next |
| BL-212 | Po uporabniški konfiguraciji SMTP izrecno preveriti dejansko dostavo in negotove dostave; med razvojem samo fake transport | ADR-0021 | next |
| BL-213 | Enotni načrt vseh odprtih/delnih nalog, popolna matrika BL → paket in priprava naslednjih SPEC | S-019, načrt 2026-10-30 | done |
| BL-214 | Pripraviti in pregledati končne SPEC S-B…S-H za osnovno izdajo ter ločene SPEC odloženih sklopov; zahteve/vmesniki/prevzem brez domnevnih podatkov | priprava SPEC 2026-10-30 | next |
| BL-215 | Pripraviti usklajen dokazni paket izdaje, razliko Claudove/pregledne veje, backup/restore in rollback; prenos :3000 samo po novi izrecni potrditvi | paket H načrta 2026-10-30 | next |
| BL-216 | Ločen SPEC in poznejša izvedba polnega portfeljskega backtesterja s point-in-time podatki, korporativnimi dejanji, stroški in gotovino; ohraniti osnovno študijo dogodkov | paket I, ADR-0022 | later |
| BL-217 | Osvežiti zadnji dokumentarni commit in pripraviti Claudov read-only pregled celotne veje/kode/plana od 1855eb8, z dokaznimi mejami in prepovedjo deploy | S-020, prevzem za Claude | done |
| BL-218 | Popravki po Claudovem pregledu 9ec9e88 pred mergem: D1 coverage upsert, A1/A2 stikalo avtomatskih LLM klicev, A4 outbox izstradanje, U1/U2 BacktestPanel povezave; ostalo v S-B/S-G1 | [Claudov pregled](./docs/implementation/2026-10-30-claude-pregled-9ec9e88.md) | next |

S-017: pregledna veja vključuje Val −1 in nadaljnje nadgradnje, objavljene samo v ločenem demu :3100. Claudova veja in okolje :3000 nista posodobljena; uporabnik zahteva pregled pred prenosom. ADR-0017–0020 so zapisani za izvedeno pregledno vejo. Podatkovne vrzeli in nedokončani deli celotnega načrta so v docs/implementation/2026-10-29-pregled-sprememb.md. Status done pomeni izvedeno v pregledni veji, ne odobrene objave na :3000.
