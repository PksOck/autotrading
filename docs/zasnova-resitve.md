# Zasnova rešitve: kaj prevzamemo in kako gradimo

**Datum:** 2026-10-22
**Nadgrajuje:** [`platforma-analiza-in-nacrt.md`](./platforma-analiza-in-nacrt.md) (splošna analiza kandidatov). Ta dokument je **izvedbena zasnova**.

---

## 0. Kaj se je spremenilo glede na prvo analizo

Tvoji odgovori premaknejo težišče:

| Zahteva | Posledica za zasnovo |
|---|---|
| Trgujem **dolgoročno**, občasno kratkoročno in **opcije** | Signali so dnevni ali tedenski, ne znotrajdnevni. Dodamo opcijski modul, a ozek: strukture, ki služijo vstopu ali dolgoročni poziciji |
| Podatki v živo **niso** potrebni | IBKR zakasnjeni podatki (15 min) in EOD svečke zadoščajo. Ni naročnine na tržne podatke, ni WebSocket cen |
| Ključno: **zaznati priložnost iz novic/špekulacij** in **dobro (ponovno) vstopno točko** | Glavni modul je **Radar novic in dogodkov** z dvema izhodoma: *katalizator* (nekaj se dogaja) in *vstopna točka* (cena je padla, vzrok pa ne ruši teze) |
| **Delnice IN ETF-ji** | TradingAgents je narejen za delnice (in kripto). Za ETF-je dodamo lasten analitski korak (sestava, izpostavljenost, stroški, tokovi) |
| Docker lokalno ali cPanel (Neoserv) | **Docker lokalno.** Utemeljitev v §1 |
| Ollama lokalno + naročnine Claude, OpenAI, OpenCode | LLM usmerjevalnik z vlogami: poceni lokalno za množično triažo, oblak za globoko analizo. Podrobno v §2 |
| IBKR PRO | API je na voljo, Flex Web Service tudi |

---

## 1. Kje teče: Docker lokalno

**Odločitev: vse teče v Docker Compose na lokalnem stroju, ki je stalno prižgan. cPanel pri Neoservu ne uporabimo.**

| Zahteva | Docker lokalno | cPanel (deljeno gostovanje) |
|---|---|---|
| IB Gateway (Java, stalni proces, 2FA) | ✅ `gnzsnz/ib-gateway` | ❌ ni mogoče poganjati stalnih procesov |
| Ollama z lokalnimi modeli | ✅ isti stroj, GPU | ❌ |
| Postgres + Timescale, Redis | ✅ | ⚠️ samo MySQL/MariaDB, brez Redisa |
| Python workerji (vrsta, scheduler) | ✅ | ⚠️ Passenger aplikacija se ugaša, cron samo na intervale |
| Podatki portfelja na tujem strežniku | ostanejo doma | na deljenem strežniku |
| Dostop od zunaj | Tailscale (brez odprtih portov) | javno, kar pomeni več napadalne površine |

cPanel lahko kasneje služi kvečjemu za statično stran ali obvestila. Za ta sistem ni potreben.

**Priporočena strojna oprema:** 16 GB RAM ali več in disk ~100 GB. Za Ollamo GPU z 8 do 16 GB VRAM (za modele 7 do 14 B, ki zadoščajo za triažo).

**Dostop:** Tailscale na strežniku in telefonu. Spletni vmesnik je viden samo v tvojem tailnetu. Za obvestila Telegram bot ali ntfy (push na telefon).

---

## 2. LLM strategija: usmerjevalnik po vlogah

### 2.1 Vloge in modeli

Vsak LLM klic v sistemu ima **vlogo** in nikoli ne kliče konkretnega ponudnika neposredno. Vloge preslika v modele **LiteLLM proxy** (Docker, OpenAI-kompatibilen vmesnik), ki skrbi tudi za beleženje stroškov, omejitve in fallback.

| Vloga | Naloge | Privzeti model | Fallback |
|---|---|---|---|
| `local-fast` | razvrščanje novic (relevanca, tiker, tip dogodka, sentiment), deduplikacija, povzetek v 1 stavek, ekstrakcija številk | **Ollama** (npr. Qwen 2.5/3 7–14B, Llama 3.x 8B), JSON izhod | `cloud-quick` |
| `embed` | vektorji za grozdenje novic in iskanje podobnih dogodkov | **Ollama** (`nomic-embed-text` ali `bge-m3`) | — |
| `cloud-quick` | analitiki TradingAgents, bull/bear debata, ETF analitik, ocena vzroka padca | **OpenCode Go** (GLM / Kimi / DeepSeek prek `https://opencode.ai/zen/go/v1`) ali **OpenAI** | drug ponudnik |
| `cloud-deep` | Research Manager, Portfolio Manager, opcijski strateg, tedenski pregled portfelja | **Claude** (Opus/Sonnet) | OpenAI (GPT) |

Modele zamenjaš v enem konfiguracijskem fajlu (`infra/litellm/config.yaml`) brez spremembe kode.

### 2.2 Naročnine in kaj velja

- **Claude:** od 15. 6. 2026 imajo Pro/Max/Team naročnine **ločen mesečni kredit za Claude Agent SDK in `claude -p`**, ki ne porablja interaktivnih limitov ([Anthropic Help Center](https://support.claude.com/articles/15036540)). Za `cloud-deep` naloge to pomeni **Claude Agent SDK z naročniško prijavo** v ločenem `claude-runner` servisu. Višino kredita po paketih (tretji viri navajajo 20/100/200 $) preveri v svojem računu. Ko se kredit porabi, je treba preklopiti na API ključ ali fallback.
- **OpenAI:** TradingAgents že podpira "Sign in with ChatGPT" (`llm_clients/chatgpt_auth.py`), kar pomeni uporabo ChatGPT Plus/Pro naročnine. Alternativa je OpenAI API ključ.
- **OpenCode Go:** OpenAI-kompatibilen endpoint z API ključem (~10 $/mes., omejitve porabe) ([docs](https://opencode.ai/docs/en/go/)). Seznam modelov se spreminja, zato ga beremo iz `/models`.
- **Ollama:** brezplačno, neomejeno. Primerno za vse, kar je masovno in enostavno.

**Posledica za TradingAgents:** ta uporablja `langchain-anthropic` (API ključ), ne Agent SDK. Zato v TradingAgents kličemo modele **prek LiteLLM proxyja** kot "OpenAI-compatible" ponudnika (`TRADINGAGENTS_QUICK_THINK_BACKEND_URL` / `TRADINGAGENTS_DEEP_THINK_BACKEND_URL`), LiteLLM pa usmeri na OpenCode, OpenAI ali Anthropic API. Naročniški Claude kredit uporabljamo v **lastnih** agentih (§5.4 do §5.6), ki tečejo prek Agent SDK.

### 2.3 Proračunska varovala

- dnevni in mesečni limit **na vlogo** (LiteLLM budgets);
- vsak zagon zapiše tokene in ceno v `agent_run`;
- predpomnjenje: ista analiza (tiker + dan + vhodni podatki) se ne ponovi;
- eskalacija v oblak samo za dogodke nad pragom (§5.2).

---

## 3. Kaj točno prevzamemo iz vsakega repoja

Legenda načina prevzema:
- **DEP** – pip/npm odvisnost, zaklenjena verzija, je ne spreminjamo;
- **PORT** – prepišemo ali prilagodimo kodo k nam (z navedbo izvora in licence v `NOTICE`);
- **IDEJA** – samo zasnova ali vzorec, koda je naša.

### 3.1 TauricResearch/TradingAgents (Apache-2.0): **jedro globoke analize delnic**

| Kaj | Način | Kje pri nas | Opomba |
|---|---|---|---|
| Celoten graf agentov (analitiki → bull/bear → research manager → trader → risk → PM) | **DEP** (`tradingagents==0.7.x`) | `services/agents/deep_research/` | kličemo `TradingAgentsGraph.propagate(ticker, date, asset_type="stock", portfolio=...)` |
| Pretakanje korakov (`stream_run`, `graph.stream(..., subgraphs=True)`) | **DEP** | worker → Redis pub/sub → SSE | vsak node postane `agent_event` v bazi |
| Strukturirani izhodi `ResearchPlan`, `TraderProposal`, `PortfolioDecision` (`agents/schemas.py`) | **DEP** + preslikava | `domain/signal.py` | rating (5 stopenj), teza, cilj, horizont, vstop, stop, velikost |
| Ocena `REVIEW` pri neberljivem izhodu | **DEP** | UI prikaže "potreben pregled" | brez tihega Hold |
| Podatkovni router (`dataflows/router.py`, `vendors/`) | **DEP** + **lasten vendor** | `services/agents/deep_research/vendor_local.py` | TradingAgents bere cene, novice in fundamente **iz naše baze**, zato agenti in UI vidijo iste podatke |
| SEC EDGAR "as filed" fundamenti (`vendors/sec_edgar.py`) | **DEP** (prek njihovega vendorja) ali **PORT** v naš ingest | `ingest/edgar/` | point-in-time, brez look-ahead |
| Spomin in refleksija (`memory/log.py`, `settlement.py`, `reflection.py`) | **IDEJA** → lastna implementacija v bazi | `signals/outcomes.py` | njihov Markdown dnevnik zamenjamo s tabelo `signal_outcome`. Refleksijo vstavimo v kontekst PM prek `portfolio`/konteksta |
| Portfelj kot kontekst (`portfolio.py`) | **DEP** | iz Flex sinhronizacije | PM ve za tvoje pozicije in gotovino |
| SQLite checkpointing | **DEP** (vklopljen) | volume v Dockerju | prekinjen zagon se nadaljuje |
| ChatGPT prijava (`llm_clients/chatgpt_auth.py`) | **DEP** (neobvezno) | — | če želiš porabljati ChatGPT naročnino |

**Česa ne prevzamemo:** CLI/TUI, njihov backtest ukaz (backtesti LLM odločitev so pristranski), privzete OpenAI modele, Markdown spomin v `~/.tradingagents`.

**ETF-ji:** TradingAgents pozna samo `stock` in `crypto`. ETF-je **ne** pošiljamo v njihov graf, ker fundamentalni analitik išče bilanco podjetja. Za ETF imamo lasten cevovod (§5.5).

**Zaklepanje in posodobitve:** verzijo posodabljamo ročno, po regresijskem testu na 5 fiksnih vhodih (posnetki podatkov), ki preveri, da izhod še ustreza shemi.

### 3.2 HKUDS/Vibe-Trading (MIT): **knjižnica idej in nekaj kode**

| Kaj | Način | Kje pri nas | Opomba |
|---|---|---|---|
| Read-only IBKR konektor (`agent/src/trading/connectors/ibkr/local.py`, ~800 vrstic) | **PORT** (izbrani deli) | `services/broker/ib_client.py` | profili `paper` / `live-readonly`, privzeti zakasnjeni podatki (tip 3/4), obravnava napake 354, **brez metode za naročila**. Prepišemo na `ib_async` |
| Opcijska matematika (`frontend/src/lib/options.ts`, `agent/backtest/options_payoff.py`) | **PORT** | `apps/web/lib/options/` in `services/api/options/payoff.py` | Black-Scholes, Greeks, payoff večnožnih struktur |
| Opcijske UI komponente (`OptionsChainTable`, `OptionsPayoffChart`, `OptionsScenarioMatrix`) | **IDEJA** (ali **PORT**, React 19) | `apps/web/components/options/` | opcijska veriga, payoff graf, scenarijska matrika |
| "Skills" kot Markdown znanje za agente: `event-driven`, `corporate-events`, `earnings-revision`, `thesis-tracker`, `us-etf-flow`, `dividend-analysis`, `valuation-model`, `options-strategy`, `sector-rotation`, `risk-analysis` | **PORT** (preberemo, skrajšamo, prevedemo, prilagodimo US trgu) | `services/agents/knowledge/*.md` | vstavimo jih v sistemske pozive naših agentov. Nekateri (npr. `etf-analysis`) so kitajski in A-share, zato jih napišemo na novo |
| Varovala za naročila (mandat, kill switch, proračun; `MandateProposalCard`) | **IDEJA** | `services/broker/guards.py` (faza 6) | |
| SSE API za seje in dogodke (`/sessions/{id}/events`) | **IDEJA** | `services/api/routes/runs.py` | oblika dogodkov in ponovna povezava |
| "Swarm" YAML predloge (npr. `investment_committee`) | **IDEJA** | naši cevovodi so fiksni grafi v kodi, ne YAML | |

**Česa ne prevzamemo:** samega agenta (ReAct z bash dostopom in izvajanjem generirane kode), kitajskih podatkovnih virov, IM botov, desktop aplikacije, alpha zoo (morda kasneje).

### 3.3 QuantConnect LEAN (Apache-2.0): **koncepti, motor morda kasneje**

| Kaj | Način | Kje pri nas | Opomba |
|---|---|---|---|
| Model **Insight** (smer, magnituda, zaupanje, obdobje, vir) | **IDEJA** | `domain/signal.py` | naša shema signala (§4.2) je zgrajena po tem vzoru |
| Ločitev Universe → Alpha → Portfolio → Risk → Execution | **IDEJA** | struktura modulov: `universe/`, `signals/`, `sizing/`, `broker/guards.py` | |
| Fill/fee modeli za IBKR | **IDEJA** | backtest pravil: provizija IBKR Pro tiered, slippage | |
| Celoten motor za backtest | **neobvezno, faza 7+** | ločen Docker servis, ki bere naše podatke | samo za backtest pravil z lastnimi podatki. **Brez** IB live (zahteva plačljiv QC modul) |

### 3.4 bennycode/trading-signals (MIT): **indikatorji v frontendu**

| Kaj | Način | Kje pri nas |
|---|---|---|
| Indikatorji za prikaz na grafu (SMA/EMA, RSI, MACD, Bollinger, ATR, Donchian, SuperTrend, OBV, relativni volumen) | **DEP** (`trading-signals@8.x`, zaklenjeno) | `apps/web/lib/indicators.ts` |
| Inkrementalni `add()` / `replace()` | **DEP** | ko uporabnik spremeni parametre, se graf izračuna v brskalniku brez klica API |

**Backend** računa iste indikatorje s **TA-Lib** (Python). Test enakosti na skupnem vzorcu podatkov (toleranca 1e-6) preprečuje razhajanje med grafom in signalom.

### 3.5 TradeMaster (Apache-2.0): **ne prevzamemo**

Samo za branje: FinAgent (večnivojski "market intelligence" povzetki in refleksija) kot navdih za Radar (§5.2). Brez kode.

### 3.6 Iz tvojega obstoječega repoja (`PksOck/autotrading`)

| Kaj | Način | Kje |
|---|---|---|
| Pogodba ponudnika podatkov + skupni testni nabor (`src/data/provider-contract.ts`) | **PORT** v Python (Protocol + pytest parametrizacija) | `services/api/data/contract.py` |
| Quota-aware composite routing in fallback (`composite-provider.ts`, `quota-tracker.ts`) | **PORT** | `services/api/data/router.py` |
| Izvor in svežina podatka (`data-provenance`, `freshness-status`) | **PORT** (React) | `apps/web/components/provenance/` |
| Validacija: IS/OOS, walk-forward, deflated Sharpe (`src/quant/validation.ts`) | **PORT** v Python | `services/api/backtest/validation.py` |
| Pre-trade risk gate + audit (`src/paper/risk.ts`) | **PORT** | `services/broker/guards.py` |
| DCF scenariji (`src/domain/valuation.ts`) | **PORT** | orodje za fundamentalnega/vstopnega agenta |
| Finnhub, FMP, FRED, AlphaVantage ponudniki | **PORT** | `ingest/` |

Obstoječa koda gre v `legacy/` (ali ostane na `main`), nova struktura nastane ob njej.

---

## 4. Naša rešitev

### 4.1 Arhitektura

```text
                         Tailscale (samo tvoje naprave)
                                     │
┌────────────────────────────── apps/web (Next.js) ─────────────────────────────┐
│ Radar · Vstopne točke · Signali · Instrument/ETF · Opcije · Portfelj · Teze     │
│ · Agentski zagon (živo) · Uspešnost · Nastavitve                               │
└───────────────▲───────────────────────────────────────────▲────────────────────┘
                │ REST (OpenAPI → TS tipi)                    │ SSE
┌───────────────┴──────────────── services/api (FastAPI) ─────┴───────────────────┐
│ domain · data router · signals · radar · entries · options · portfolio · runs   │
└──┬─────────────┬──────────────┬───────────────┬──────────────┬──────────────────┘
   │             │              │               │              │
┌──▼────────┐ ┌──▼──────┐ ┌─────▼─────────┐ ┌───▼──────────┐ ┌─▼────────────────┐
│ Postgres  │ │ Redis   │ │ worker (arq)  │ │ claude-runner│ │ broker (ib_async)│
│ Timescale │ │ vrste,  │ │ ingest, radar,│ │ Claude Agent │ │ → ib-gateway     │
│ pgvector  │ │ pub/sub │ │ signali,      │ │ SDK (naroč-  │ │   (Docker,       │
└───────────┘ └─────────┘ │ TradingAgents │ │ niški kredit)│ │   read-only)     │
                          └──────┬────────┘ └──────────────┘ └──────────────────┘
                                 │ OpenAI-compatible
                          ┌──────▼─────────────────────────────┐
                          │ litellm proxy                      │
                          │ → ollama (lokalno) · OpenCode Go   │
                          │ → OpenAI · Anthropic API           │
                          └────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│ scheduler (v workerju): ingest novic na 5–15 min · EDGAR na 10 min · EOD svečke │
│ po zaprtju · Flex ob 6:00 · screener po zaprtju · nočne analize · izidi signalov │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Docker Compose servisi:** `web`, `api`, `worker`, `claude-runner`, `broker`, `ib-gateway`, `litellm`, `ollama` (ali obstoječa namestitev na gostitelju), `postgres` (Timescale + pgvector), `redis`. Neobvezno še `ntfy` za obvestila.

### 4.2 Osrednji objekti

**Signal** (po vzoru LEAN Insight + TradingAgents PortfolioDecision):

```python
class Signal(BaseModel):
    id: UUID
    instrument_id: int            # delnica ali ETF
    kind: Literal["catalyst", "entry", "exit_warning", "thesis_break", "options_idea"]
    source: Literal["rule", "radar", "agent", "manual"]
    direction: Literal["up", "down", "neutral"]
    horizon: Literal["days", "weeks", "months", "years"]
    strength: float               # 0..1, kalibrirano po izidih
    confidence: float             # 0..1, zaupanje modela / soglasje
    entry_zone: tuple[float, float] | None
    stop: float | None
    target: float | None
    rationale: str                # 1–3 stavki, vedno prisotni
    evidence: list[EvidenceRef]   # povezave na novice, filinge, indikatorje
    rating: Literal["Buy","Overweight","Hold","Underweight","Sell","REVIEW"] | None
    agent_run_id: UUID | None
    status: Literal["new","watching","accepted","dismissed","expired"]
    created_at: datetime
    expires_at: datetime
```

**Ostale tabele:**
- `instrument` (+ `etf_profile`: izdajatelj, TER, AUM, indeks, top pozicije, sektorji, države);
- `bar` (Timescale);
- `news_item` (+ embedding v pgvector);
- `event` (gruča novic o istem dogodku);
- `filing` (EDGAR: 8-K, 10-Q/K, Form 4, 13D/G);
- `earnings_calendar`;
- `position`, `trade`, `cash` (Flex);
- `thesis` (tvoja teza za pozicijo, §5.6);
- `agent_run`, `agent_event`;
- `signal_outcome`;
- `option_snapshot`;
- `order_draft` (faza 6).

### 4.3 Struktura monorepa

```text
autotrading/
├── apps/web/                         # Next.js 15, React 19, shadcn/ui, TanStack Query,
│                                     # lightweight-charts, trading-signals
├── services/
│   ├── api/                          # FastAPI + SQLAlchemy 2 + Alembic
│   │   ├── domain/                   # Pydantic modeli (Signal, Event, Thesis ...)
│   │   ├── data/                     # contract.py, router.py, quota.py
│   │   ├── ingest/                   # finnhub, rss, edgar, yfinance, ibkr_bars, flex, fred, etf
│   │   ├── radar/                    # triage.py, cluster.py, score.py, escalate.py
│   │   ├── entries/                  # rules.py, dip_classifier.py, valuation_bands.py
│   │   ├── signals/                  # indicators.py (TA-Lib), screener.py, outcomes.py
│   │   ├── options/                  # chain.py, payoff.py, strategies.py
│   │   ├── portfolio/                # flex_parser.py, exposure.py
│   │   ├── backtest/                 # vectorized.py, validation.py
│   │   └── routes/                   # REST + SSE
│   ├── agents/
│   │   ├── deep_research/            # TradingAgents adapter + vendor_local.py
│   │   ├── etf_analyst/              # naš LangGraph cevovod za ETF
│   │   ├── dip_analyst/              # "ali padec ruši tezo?"
│   │   ├── options_strategist/       # predlog opcijske strukture
│   │   ├── thesis_tracker/           # tedenski pregled tez
│   │   └── knowledge/                # Markdown znanje (prirejeno iz Vibe-Trading skills)
│   ├── claude_runner/                # Claude Agent SDK servis (naročniški kredit)
│   └── broker/                       # ib_async: bars, chains, positions; guards.py
├── infra/
│   ├── docker-compose.yml
│   ├── litellm/config.yaml           # vloge → modeli, budgets
│   └── ib-gateway/                   # IBC nastavitve (READ_ONLY_API=yes)
├── legacy/                           # obstoječa Next.js koda (referenca)
├── NOTICE                            # navedba prevzete kode (Apache-2.0 / MIT)
└── docs/
```

---

## 5. Cevovodi (jedro vrednosti)

### 5.1 Ingest (viri podatkov, brezplačni najprej)

| Vir | Kaj | Pogostost |
|---|---|---|
| **IBKR (ib_async, zakasnjeno)** | dnevne svečke, opcijske verige (`reqSecDefOptParams`, `reqContractDetails`), Greeks/IV iz zakasnjenih podatkov | po zaprtju; opcije na zahtevo |
| **IBKR Flex** | pozicije, posli, gotovina, dividende | dnevno 6:00 |
| **SEC EDGAR** (brezplačno, 10 zahtev/s, obvezen User-Agent) | 8-K (pomembni dogodki), Form 4 (insiderji), 13D/G (aktivisti), 10-Q/K | vsakih 10 min (RSS/JSON feed) |
| **Finnhub** (brezplačni nivo) | novice po podjetju, splošne novice, koledar poročil, priporočila analitikov | 5–15 min |
| **RSS** | GlobeNewswire, PR Newswire, Business Wire (sporočila za javnost), Fed, BLS, izdajatelji ETF-jev | 5–15 min |
| **Reddit / StockTwits** (prek TradingAgents vendorjev ali neposredno) | špekulacije, nenadna pozornost (št. omemb) | 30 min, samo watchlista + kandidati |
| **yfinance** (fallback) | fundamenti, ETF holdings (`funds_data`), zgodovina | dnevno |
| **FRED** | makro (obrestne mere, krivulja, inflacija) | dnevno |
| **ETF izdajatelji** (iShares, Vanguard, SPDR CSV) | polne sestave ETF-jev | tedensko |

Vsak vir implementira pogodbo (`contract.py`), ima kvoto in fallback ter zapiše `source` in `fetched_at`.

### 5.2 Radar novic in dogodkov (glavna nova funkcija)

Cilj je **zaznati priložnost iz novic ali špekulacij**, poceni in množično, z eskalacijo samo pomembnega.

```text
news_item ──► 1. normalizacija (čas UTC, tikerji, vir, URL kanonizacija)
          ──► 2. embed (Ollama) ──► 3. grozdenje v `event` (cos > 0.85 v 48 h)
          ──► 4. TRIAŽA (local-fast, JSON shema) za vsak nov event:
                   - tickers[], event_type (earnings, guidance, M&A, FDA, contract,
                     insider_buy, analyst_action, macro, lawsuit, product, rumor ...)
                   - is_rumor: bool, sentiment: -1..1, materiality: 0..1
                   - novelty: ali je to novo glede na prejšnje evente
                   - time_sensitivity: hours/days/weeks
          ──► 5. KONTEKST (deterministično, brez LLM):
                   - odziv cene (gap, % sprememba proti sektorju/SPY, rel. volumen)
                   - abnormalna pozornost (št. omemb proti 30-dnevni bazi)
                   - je v watchlisti/portfelju? razdalja do vstopne cone?
          ──► 6. OCENA PRILOŽNOSTI (formula, §5.2.1)
          ──► 7. ESKALACIJA, če ocena > prag:
                   - cloud-quick: "kaj pomeni ta dogodek za tezo? 3 scenariji"
                   - po potrebi polna globoka analiza (TradingAgents / ETF analitik)
          ──► 8. Signal(kind="catalyst") + obvestilo (ntfy/Telegram)
```

**5.2.1 Ocena priložnosti (začetna, nato kalibrirana po izidih):**

```text
score = materiality × novelty × (0.5 + 0.5·|price_reaction_z|)
        × relevance_weight (portfelj 1.0 · watchlist 0.8 · univerzum 0.5)
        × (0.6 if is_rumor else 1.0)
        × attention_boost (1.0–1.5 glede na abnormalne omembe)
```

Pragovi in uteži so v konfiguraciji. Po 2 do 3 mesecih jih nastavimo na podlagi `signal_outcome` (kateri tipi dogodkov so res napovedovali gibanje).

**Špekulacije:** `is_rumor=true` dogodki se **nikoli** ne eskalirajo v Buy priporočilo. Postanejo signal "spremljaj" z zapisom, kaj bi jih potrdilo (npr. 8-K, uradno sporočilo). Ko se pojavi potrditev v EDGAR ali PR viru, se signal samodejno nadgradi.

### 5.3 Vstopne točke (re-entry) za dolgoročne pozicije

Cilj: **povedati, kdaj je kakovostna delnica ali ETF, ki ga želiš imeti, na dobri ceni**, in ločiti "poceni z razlogom" od "začasno poceni".

**Korak A, deterministični kandidati** (dnevno po zaprtju, watchlista + portfelj):

| Pravilo | Pogoj (privzeto, nastavljivo) |
|---|---|
| Pullback v dolgoročnem trendu | cena nad SMA200 (ali SMA200 narašča) **in** cena ≤ SMA50, RSI(14) < 40 |
| Test podpore | cena znotraj 1×ATR od SMA200 ali od zadnjega pomembnega minimuma |
| Drawdown | −15 % (ETF −8 %) ali več od 52-tedenskega vrha |
| Vrednotenje | P/E ali EV/EBIT pod 5-letno mediano (pasovi vrednotenja), FCF yield nad mediano. DCF iz obstoječega repoja kot dodaten pogled |
| Insiderji | Form 4 nakupi (ne prodaje) več insiderjev v 30 dneh |
| Pretiran odziv na novico | padec > 2σ ob dogodku, ki ga je triaža označila kot `materiality < 0.5` |
| ETF | odmik od SMA200, relativna vrednost proti zgodovini (npr. P/E indeksa), diskont na NAV |

Vsak zadetek dobi **entry_zone** (npr. SMA200 ± 0,5 ATR), **stop** (za dolgoročno: tezni stop, npr. zaprtje pod SMA200 2 tedna ali zlom fundamentov) in **zakaj**.

**Korak B, analiza vzroka padca (`dip_analyst`, cloud-quick, po potrebi cloud-deep):**
- vhod: novice in filingi zadnjih 30 dni, sprememba ocen analitikov, gibanje sektorja/SPY, tvoja teza (če obstaja);
- vprašanje: *"Je padec posledica (a) celotnega trga/sektorja, (b) začasnega dogodka, (c) spremembe temeljev, ki ruši tezo?"*;
- izhod: `cause ∈ {market, sector, transient, fundamental, unknown}`, `thesis_intact: bool`, dokazi s povezavami.

Samo `market | sector | transient` + `thesis_intact` postane `Signal(kind="entry")`. `fundamental` postane `Signal(kind="thesis_break")`, če imaš pozicijo.

**Postopni nakup (DCA lestvica):** za vstopno cono predlagamo 2 do 3 limit ravni (npr. 40 % / 30 % / 30 %) glede na ATR. To je samo predlog, ki ga vidiš v UI.

### 5.4 Globoka analiza delnice (TradingAgents)

- Sproži se ročno (gumb), iz Radarja (eskalacija) ali iz Vstopnih točk.
- Adapter nastavi: `asset_type="stock"`, `portfolio=` (iz Flex), `data_vendors` (naš `vendor_local`), modele (quick → `cloud-quick`, deep → `cloud-deep` prek LiteLLM), `max_debate_rounds=1` (2 za pozicije nad X % portfelja), checkpointing.
- Kontekst iz Radarja (dogodek, ki je sprožil analizo) se doda kot dodatna novica na vrh.
- Izhod `PortfolioDecision` + `TraderProposal` → `Signal(source="agent")`, celotna debata → `agent_event`.
- **Soglasje:** za pozicije nad pragom 2 zagona z različnima ponudnikoma (npr. Claude in GPT). Če se ocena razlikuje za več kot 1 stopnjo, dobi signal `confidence ↓` in oznako "razdeljeno mnenje".

### 5.5 ETF analitik (naš cevovod, LangGraph)

TradingAgents ne pokriva ETF-jev, zato zgradimo krajši graf:

1. **Profil** (deterministično): TER, AUM, povprečni promet, spread, indeks, top 10 pozicij in koncentracija, sektorji, države, valuta, distribucija/akumulacija.
2. **Izpostavljenost in prekrivanje** (deterministično): prekrivanje s tvojim portfeljem (uteži skozi holdings), efektivna izpostavljenost po sektorjih po nakupu.
3. **Tehnika in vstop:** isti korak A kot pri delnicah.
4. **Makro/tema** (`cloud-quick`): novice in makro (FRED), ki vplivajo na temo ETF-ja, s pomočjo znanja `us-etf-flow`, `sector-rotation`, `global-macro`.
5. **Odločitev** (`cloud-deep`, Claude Agent SDK): ista shema kot `PortfolioDecision`, zato UI obravnava ETF in delnice enako.

### 5.6 Teze in sledenje (thesis tracker)

Za vsako pozicijo ali kandidata zapišeš (ali agent predlaga, ti potrdiš) **tezo**: 3 do 5 trditev, ki morajo veljati (npr. "rast oblaka > 20 %", "marža > 30 %"), in **kaj bi jo ovrglo**.

- Tedensko (Claude Agent SDK, `cloud-deep`) preveri vsako tezo proti novim filingom in novicam: ✅ drži / ⚠️ šibi / ❌ ovržena.
- Ovržena trditev ustvari `Signal(kind="thesis_break")` in obvestilo.
- Teza je kontekst za `dip_analyst` in TradingAgents (prek `portfolio` konteksta).

### 5.7 Opcije (ozek, uporaben obseg)

Ne gradimo platforme za trgovanje z opcijami. Gradimo **opcijske ideje, ki služijo dolgoročnemu vlagatelju**:

| Struktura | Kdaj jo sistem predlaga |
|---|---|
| **Cash-secured put** | vstopna točka je blizu, želiš kupiti nižje in dobiti premijo. Strike ≈ spodnji rob vstopne cone |
| **Covered call** | imaš pozicijo nad ciljno ceno ali visoko IV, pripravljen si delno prodati |
| **Long call / call debit spread** | katalizator (Radar) z omejenim časovnim oknom, omejeno tveganje namesto nakupa delnic |
| **Protective put / collar** | velika pozicija pred dogodkom (poročilo), ki ga ne želiš prodati |

Tok:
1. signal (`entry` ali `catalyst`);
2. `options_strategist` (cloud-deep) dobi verigo iz IBKR (zakasnjeno: strike, expiry, bid/ask, IV, Greeks, OI);
3. predlaga 1 do 2 strukturi z izbiro DTE in delte;
4. **deterministično** izračunamo payoff, break-even, max izgubo, verjetnost (Black-Scholes iz IV; port iz Vibe-Trading);
5. UI prikaže payoff graf in scenarijsko matriko.

Varovala:
- LLM nikoli ne računa cen ali Greeks, samo izbira strukturo iz ponujenih podatkov;
- brez golih prodanih callov in brez struktur z neomejeno izgubo;
- opozorilo pri nizki likvidnosti (spread > 10 % ali OI < 100).

**Tržni podatki za opcije:** zakasnjeni podatki zadoščajo za idejo. Za oddajo naročila v fazi 6 bo verjetno smiselna OPRA naročnina (nekaj $/mes.; ceno preveri v IBKR).

### 5.8 Ocena izidov in kalibracija

- Za vsak signal nočno zapišemo donos po 1, 5, 20 in 60 dneh, alfo proti SPY (ETF: proti benchmarku), MFE/MAE.
- Za opcijske ideje: teoretični P/L strukture do izteka.
- Mesečno: hit rate in povprečna alfa po `kind × source × event_type`, kalibracijska krivulja `strength`.
- Uteži ocene priložnosti (§5.2.1) in pragovi se popravljajo na podlagi teh podatkov. Vsako spremembo zabeležimo z verzijo konfiguracije.

---

## 6. Frontend

| Zaslon | Vsebina |
|---|---|
| **Radar** | tok dogodkov (gruče novic), filtri (portfelj/watchlist/univerzum, tip dogodka, govorica ali potrjeno), ocena priložnosti, odziv cene, gumb "Analiziraj" |
| **Vstopne točke** | tabela kandidatov: razdalja do cone, vzrok padca, teza drži/ne, vrednotenje proti zgodovini, predlog DCA lestvice. Mini graf s cono |
| **Signali (inbox)** | vse vrste signalov s statusom, akcije Sprejmi / Spremljaj / Zavrzi (z razlogom, ki gre v kalibracijo) |
| **Instrument / ETF** | graf z indikatorji (trading-signals), oznake dogodkov in signalov na časovnici, fundamenti ali ETF profil, prekrivanje s portfeljem, zgodovina analiz |
| **Agentski zagon** | časovnica agentov v živo (SSE), razširljivi izhodi, tokeni in strošek, končna odločitev |
| **Opcije** | veriga, predlagane strukture, payoff graf, scenarijska matrika, break-even, max izguba |
| **Portfelj** | pozicije (Flex), teže, sektorska in tematska izpostavljenost (skozi ETF holdings), stanje tez |
| **Teze** | trditve s statusom ✅/⚠️/❌, zgodovina tedenskih pregledov |
| **Uspešnost** | hit rate, alfa, kalibracija po virih in tipih dogodkov |
| **Nastavitve** | watchlista, univerzum, pragovi, LLM vloge in proračun, stanje servisov (Gateway, Flex, Ollama, LiteLLM) |

Načela ostanejo enaka:
- vsak podatek ima vir in čas;
- vsak signal ima razlago in dokaze;
- govorice so vizualno ločene od potrjenih dogodkov;
- vse je odločitev tvoja.

---

## 7. Faze (revidirano)

| Faza | Vsebina | Rezultat |
|---|---|---|
| **0. Temelji** (1–2 tedna) | monorepo, Docker Compose (postgres, redis, litellm, ollama, api, worker, web), CI, Alembic, `NOTICE`, prenos pogodbe ponudnika in routerja | `docker compose up` deluje, LiteLLM odgovarja na vse 4 vloge |
| **1. Podatki + portfelj** (2 tedna) | Flex sinhronizacija, ib-gateway (read-only) + ib_async za EOD svečke, yfinance/Finnhub fallback, ETF profili, zasloni Portfelj in Instrument | vidiš svoj IBKR portfelj, grafe in ETF sestave |
| **2. Radar** (2–3 tedne) | ingest novic (Finnhub, RSS, EDGAR), embed + grozdenje, lokalna triaža, ocena priložnosti, zaslon Radar, obvestila | dnevni tok relevantnih dogodkov za tvoj portfelj in watchlisto, praktično brez stroškov LLM |
| **3. Vstopne točke** (2 tedna) | pravila (TA-Lib), pasovi vrednotenja, `dip_analyst`, zaslon Vstopne točke, `signal_outcome` | seznam "dobra cena + razlog padca" za dolgoročne pozicije |
| **4. Globoka analiza** (2–3 tedne) | TradingAgents adapter + `vendor_local`, ETF analitik, claude-runner, SSE, zaslon Agentski zagon | klik → debata agentov v živo → strukturirana odločitev |
| **5. Teze + uspešnost** (2 tedna) | thesis tracker, zaslon Uspešnost, kalibracija | sistem se uči, kaj deluje |
| **6. Opcije** (2 tedna) | veriga iz IBKR, payoff port, `options_strategist`, zaslon Opcije | opcijske ideje (CSP, covered call, spreadi) za tvoje signale |
| **7. Naročila s potrditvijo** (2 tedna, ko bodo podatki iz faze 5 prepričljivi) | `order_draft`, varovala, najprej paper | predlog naročila, ki ga oddaš z enim klikom po potrditvi |
| 8. (neobvezno) | LEAN backtest servis, alpha faktorji | |

**Uporaben MVP (faze 0 do 3): ~7 do 9 tednov.** Radar in Vstopne točke že sama dajeta največ tega, kar si opisal, brez velikih stroškov LLM.

---

## 8. Sprejete odločitve in odprta vprašanja

**Sprejeto (predlagam, potrdi):**
1. Docker lokalno, Tailscale, brez cPanela.
2. Python backend (FastAPI) + Next.js frontend, Postgres (Timescale + pgvector) + Redis.
3. TradingAgents kot odvisnost (ne fork), z lastnim podatkovnim vendorjem.
4. LiteLLM kot edini izhod do LLM-jev. Ollama za triažo, OpenCode/OpenAI za quick, Claude za deep.
5. Brez naročnine na tržne podatke do faze 7.
6. Signali nikoli ne oddajo naročila sami.

**Odprto:**
1. **Strojna oprema:** kateri stroj bo strežnik (CPU, RAM, GPU)? Kateri Ollama modeli so že naloženi?
2. **Claude naročnina:** Pro ali Max (velikost Agent SDK kredita)? Imaš tudi API ključ za Anthropic/OpenAI ali samo naročnine?
3. **Univerzum za Radar:** samo portfelj + watchlista ali tudi širše (S&P 500 + izbrani ETF-ji)? Širše pomeni več novic, a še vedno lokalna triaža.
4. **Obvestila:** Telegram ali ntfy (push)?
5. **Obstoječa koda:** jo premaknemo v `legacy/` na tej veji ali začnemo nov repo?
6. **Jezik vmesnika in poročil:** slovenščina ali angleščina? (Agenti delujejo bolje v angleščini, povzetek lahko prevedemo.)

---

## Viri

- TradingAgents (preučena koda v0.7.x): `graph/trading_graph.py` (`propagate`, `stream_run`), `agents/schemas.py`, `dataflows/router.py`, `memory/`, `llm_clients/chatgpt_auth.py`
- Vibe-Trading (preučena koda v0.1.18): `agent/src/trading/connectors/ibkr/local.py`, `frontend/src/lib/options.ts`, `agent/backtest/options_payoff.py`, `agent/src/skills/*`
- [Claude Agent SDK s Claude naročnino (Anthropic Help Center)](https://support.claude.com/articles/15036540)
- [OpenCode Go dokumentacija](https://opencode.ai/docs/en/go/), [Docker docs: OpenCode Go provider](https://docs.docker.com/ai/docker-agent/providers/opencode-go/)
- IBKR, LEAN, trading-signals: glej vire v [`platforma-analiza-in-nacrt.md`](./platforma-analiza-in-nacrt.md)

*Nepreverjeno: višina Agent SDK kredita po paketih (tretji viri), trenutni seznam OpenCode Go modelov, cena OPRA naročnine za ne-profesionalce v 2026.*
