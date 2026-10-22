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
| BL-059 | Preveri URL-je RSS virov (GlobeNewswire, PR Newswire, Business Wire) in obliko EDGAR feeda na pravem omrežju | research §5.1 | next |

## M3: Vstopi

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-060 | Pravila vstopov (TA-Lib) kot konfiguracija + test enakosti s trading-signals | research §5.3 | done |
| BL-061 | Pasovi vrednotenja (P/E, EV/EBIT, FCF yield proti 5-letni mediani), DCF prepis iz legacy | research §5.3 | done |
| BL-062 | `dip_analyst`: vzrok padca (trg / sektor / začasno / temeljno), `local-reason` → `cloud-quick` | research §5.3 | done |
| BL-063 | Lestvica postopnega nakupa (ATR) | CMP-15 | done |
| BL-064 | SCR-03 Vstopi | DESIGN §4 | done |
| BL-066 | Preveri polja Finnhub `/stock/metric` na pravem omrežju (P/E, EV/EBIT, P/FCF serije) in dopolni zgodovino EV/EBIT | ADR-0010 | next |
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
| BL-088 | Dodatna analitika: dividende/odkupi in relativno vrednotenje (multiplikatorji računa koda) | research/trading-list §2 | later |
| BL-090 | Ročni predlog → standardna/globoka analiza: hipoteza uporabnika v kontekstu, izrecna potrditev/ovržba v izhodu (hitra in standardna globina že delujeta v M2) | DESIGN §11 | done |
| BL-091 | Preveri Yahoo `funds_data` za UCITS kotacije (LSE, Xetra) na pravem omrežju: TER, top pozicije, sektorji | ADR-0011 | next |
| BL-092 | Živi preizkus globoke analize prek LiteLLM (`cloud-quick`/`cloud-deep` z OpenCode Go/MiniMax): klici orodij, čas in cena enega zagona | ADR-0011 | next |
| BL-093 | Dnevni limit globokih analiz (`DEEP_DAILY_LIMIT`, privzeto 6, `GET /analyses/quota`, 429 `daily_limit_reached`; globok predlog nad limitom dobi samo hitro presojo) in prikaz porabe na SCR-06 | research/trading-list §4 | done |
| BL-089 | Shema odločitve: sprožilci ocene (→ trditve teze), `delta_note` proti prejšnji analizi, prepričanje, razred velikosti, deterministična kontrolna ocena | research/trading-list §3 | done |

## M5: Teze + uspešnost

| ID | Naloga | Ref | Status |
|---|---|---|---|
| BL-100 | Model teze, SCR-09, CMP-11 (sprožilci iz kartice odločitve BL-089 postanejo trditve teze) | research §5.6 | later |
| BL-101 | Tedenski pregled tez (Claude) + signal `thesis_break` | research §5.6 | later |
| BL-102 | SCR-10 Uspešnost, kalibracija | research §5.8 | later |

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
