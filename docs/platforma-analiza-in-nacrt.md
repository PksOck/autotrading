# Agentska trgovalna platforma: analiza in načrt

**Datum:** 2026-10-22
**Namen:** interna platforma za analizo trga, signale in usmeritve za nakup delnic pri Interactive Brokers (IBKR). Človek vedno odobri odločitev, platforma ne trguje sama.

---

## 1. Povzetek (TL;DR)

| Komponenta | Odločitev | Zakaj |
|---|---|---|
| **Agentska analiza** | **TradingAgents** (TauricResearch) kot jedro, ovit v lasten FastAPI servis | Apache-2.0, aktivno vzdrževan (v0.7.0, okt. 2026), majhen in testiran, nativno podpira Claude, ima strukturiran izhod (Buy/Overweight/Hold/Underweight/Sell + cena, stop, horizont) in že pretaka vmesne korake LangGraph |
| **Tehnični indikatorji** | **TA-Lib** v Python backendu, **trading-signals** (TS) v frontendu za grafe v živo | TA-Lib je industrijski standard. trading-signals je MIT, brez odvisnosti, 100 % pokritost s testi, inkrementalni `add()`/`replace()` API |
| **IBKR** | **Flex Web Service** za portfelj (samo branje), **IB Gateway (Docker) + ib_async** za tržne podatke in kasneje naročila | Flex ne potrebuje gatewaya ne 2FA in ne more oddati naročila. ib_async je naslednik ib_insync, gnzsnz/ib-gateway-docker pa poskrbi za headless delovanje |
| **Backtesting** | Najprej lasten, enostaven backtester (prenos iz obstoječega `src/quant/`), **LEAN** šele kasneje in neobvezno | LEAN je odličen, a težak (.NET, več GB Docker slika) in za IBKR live zahteva plačljivo QC naročnino (licenčni klic v kodi) |
| **Frontend** | Next.js + React + shadcn/ui + lightweight-charts + SSE | Ostanemo na znanem skladu iz obstoječega repoja |
| **Vibe-Trading** | Samo referenca (ideje za UI, varovala za naročila, IBKR read-only konektor) | Prevelik (~500k vrstic), se hitro spreminja, odprt agent, ki izvaja LLM-generirano kodo |
| **TradeMaster** | Ne uporabimo (največ kot branje za ideje) | Akademski RL okvir, zastarele odvisnosti (TF 2.11, Ray 1.13), brez IBKR, brez žive podpore |

**Glavno sporočilo:** nobeno od orodij ni "platforma", ki bi jo samo izpopolnil. Najboljša pot je **lasten tanek sistem** (frontend + API + baza), v katerega vključiš **TradingAgents** kot agentski motor in **ib_async** kot most do IBKR. Ostala orodja so knjižnice ali reference.

---

## 2. Analiza kandidatov

### 2.1 QuantConnect LEAN

- **Sklad:** C# / .NET 10, Python algoritmi prek pythonnet (Python 3.11). Apache-2.0. Zelo aktiven (~22k zvezdic, commit 2026-10-21). Okrog 780k vrstic C#.
- **Prednosti:**
  - zrel dogodkovni motor, ista koda za backtest, paper in live;
  - realistično modeliranje (provizije, slippage, margin, splits/dividende);
  - Algorithm Framework (Universe → Alpha → Portfolio → Risk → Execution); Alpha "Insights" se lepo preslikajo v signale;
  - JSON rezultati (statistika, equity krivulja, naročila).
- **IBKR:** obstaja plugin (`Lean.Brokerages.InteractiveBrokers`), ki sam upravlja IB Gateway. Zahteva IBKR PRO, 2FA ob tedenskem ponovnem zagonu in naročnino na tržne podatke (ali vklop zakasnjenih podatkov).
- **Past (preverjeno v kodi):** `InteractiveBrokersBrokerage.Initialize()` pokliče `ValidateSubscription()` na QC API. Brez plačljive QC organizacije z IB modulom se brokerage ugasne, tudi če ga zgradiš iz izvorne kode. Lean CLI po dokumentaciji prav tako zahteva plačljiv paket (okvirno 84 $/mes. za Researcher; točna cena IB modula ni preverjena).
- **Podatki:** lasten format na disku. QC podatki so plačljivi, lastne podatke je treba pretvoriti.
- **Slabosti za enega razvijalca:** težka operativa, razhroščevanje .NET + pythonnet, LLM klici znotraj algoritma so nerodni in naredijo backtest nedeterminističen.
- **Ocena:** **delna uporaba ali referenca.** Smiseln kot neodvisen validacijski motor za backteste v kasnejši fazi. Ni primeren kot jedro agentske spletne aplikacije.

### 2.2 TradeMaster (NTU)

- Python 3.9, Apache-2.0. Edina izdaja je v1.0.0 (marec 2023), zadnji commit junij 2025 (samo README).
- RL okolja (DQN, EIIE, DeepTrader ...), Alpha158 značilke, orodja za evalvacijo. Vsebuje FinAgent (LLM agent, samo OpenAI/Azure).
- Brez IBKR, brez live trgovanja, Flask demo backend s `shell=True` in wildcard CORS.
- **Ocena:** **preskoči.** Za ideje lahko prebereš FinAgent (prompti, spomin) in evalvacijske metrike.

### 2.3 bennycode/trading-signals

- TypeScript, ESM, MIT, **brez runtime odvisnosti**. Zelo aktiven (8.3.0, avg. 2026).
- 127 indikatorjev (trend, momentum, volatilnost, volumen), mnogi vračajo BULLISH/BEARISH/SIDEWAYS signal.
- Pretočni API: `add()`, `replace()` za svečo, ki se še oblikuje, `isStable`, omejen spomin.
- 100 % pokritost, preverjanje proti Tulip Indicators, mutacijsko testiranje.
- Od v7 ni več big.js (samo `number`). Dve prelomni glavni verziji v enem letu, zato je treba zakleniti verzijo.
- **Ocena:** **uporabi v frontendu** (indikatorji na grafu v živo, ob sveči iz WebSocketa). V Python backendu za izračune uporabi TA-Lib, trading-signals pa po želji kot navzkrižno preverjanje.

### 2.4 TauricResearch/TradingAgents

- Python 3.11+, LangGraph/LangChain, Apache-2.0. Približno 113k zvezdic, izdaja na 2 do 3 tedne (v0.7.0, 2026-10-16), ~28k vrstic, CI z ruff + pytest.
- **Agenti (fiksen cevovod, model trgovalne firme):**
  1. do 4 analitiki vzporedno: tehnični, sentiment (StockTwits, Reddit), novice/makro, fundamentalni;
  2. Bull vs. Bear debata;
  3. Research Manager napiše načrt;
  4. Trader predlaga posel (vstop, stop, velikost);
  5. tri risk perspektive (agresivna, konservativna, nevtralna);
  6. Portfolio Manager poda končno oceno.
- **LLM:** nativni Claude (`langchain-anthropic`) in skoraj vsi ostali ponudniki. Dva nivoja modelov: "quick" (analitiki, debate) in "deep" (managerji). Smiselno je npr. Sonnet za quick in Opus za deep.
- **Podatki:** yfinance, SEC EDGAR (point-in-time), Alpha Vantage, FRED, Reddit, StockTwits, Polymarket. Ponudniki so zamenljivi prek `dataflows/router.py`, zato lahko dodaš lastnega (IBKR, Finnhub, FMP).
- **Izhod:** Pydantic strukture (`ResearchPlan`, `TraderProposal`, `PortfolioDecision`), Markdown in HTML poročilo. Ob neberljivi oceni vrne `REVIEW`. Sprejme tudi trenutni portfelj (gotovina + pozicije).
- **Spomin:** dnevnik odločitev. Po 5 trgovalnih dneh oceni donos in alfo proti SPY in zapiše refleksijo, ki jo PM upošteva pri naslednjih odločitvah.
- **Vmesniki:** Python API (`propagate(ticker, date)`), CLI, Docker. **Ni HTTP API-ja ne spletnega vmesnika**, vendar `stream_run()` že uporablja `graph.stream(..., subgraphs=True)`, zato je ovoj v FastAPI + SSE enostaven.
- **Stroški in hitrost (ocena, ni izmerjeno):** 25 do 50 LLM klicev na tiker, nekaj minut, ~0,5 do 5 $ na analizo glede na modele.
- **Zanesljivost:** README sam pravi, da rezultati niso ponovljivi. Rezultati iz članka (visoki Sharpe na nekaj delnicah v 3 mesecih leta 2024) niso verodostojni zaradi kratkega obdobja in znanja modela iz učnih podatkov. Projekt je od takrat veliko naredil za point-in-time podatke, a uhajanja znanja LLM-ja ni mogoče odstraniti. **Edina poštena ocena je sprotno (forward) sledenje signalom.**
- **Ocena:** **uporabi kot jedro agentske analize.** Zakleni verzijo, nastavi Claude modele, ovij v servis.

### 2.5 HKUDS/Vibe-Trading

- Python (FastAPI) + React 19/Vite, MIT. Okrog 36k zvezdic, v0.1.18, zelo hiter razvoj (638 commitov v eni izdaji).
- Ogromen: ~520k vrstic Pythona (morda vključno z vendorirano kodo), ~70k vrstic frontenda, 157 MB repo.
- Splošen ReAct agent z 113 orodji, 90 "skills" in "Swarm" motor s 30 YAML predlogami (npr. `investment_committee`). Agenti imajo lahko `bash` in izvajajo LLM-generirano kodo.
- Podpira Claude, 29 podatkovnih virov (veliko kitajskih), IBKR samo za branje (TWS/Gateway), SSE API in vgrajen spletni vmesnik.
- Izhod je prosti Markdown, brez strukture Buy/Sell. Stroški na zagon so neomejeni (do ~200 iteracij).
- **Ocena:** **referenca.** Vredno pogledati: zasnovo read-only IBKR konektorja, varovala za živo trgovanje (mandat, kill switch, proračun), SSE API za seje in UX vzorce. Lahko ga poganjaš ob strani kot raziskovalni klepet, ne kot jedro.

### 2.6 Interactive Brokers: možnosti integracije

| Način | Avtentikacija | Primerno za | Opombe |
|---|---|---|---|
| **Flex Web Service** | dolgoživ token + Flex Query ID | sinhronizacija portfelja, poslov, dividend, NAV | samo branje, brez gatewaya in 2FA, 1 zahteva/s in 10/min, podatki ob koncu dneva |
| **TWS API / IB Gateway + ib_async** | Gateway proces z uporabnikom, geslom in 2FA (IBKR Mobile) | tržni podatki, pozicije v živo, naročila | dnevni restart, tedenska ponovna 2FA. Headless prek IBC v `gnzsnz/ib-gateway-docker`. Zgodovinski podatki: največ 60 zahtev/10 min. Paper račun je podprt |
| **IBKR Web API (Client Portal)** | Java gateway + prijava v brskalniku | alternativa za REST | seja največ 24 ur, potrebuje `/tickle` vsako minuto, OAuth za posameznike ni uradno podprt. Za nenadzorovano delovanje bolj krhko |

**Tržni podatki:** API v realnem času zahteva plačljivo naročnino na borze (za ne-profesionalce okvirno nekaj do ~10 $/mes., cene za 2026 niso preverjene). `reqMarketDataType(3)` vrne brezplačne 15-minutne zakasnjene podatke. Paper račun vidi podatke v živo samo, če je vklopljeno deljenje podatkov z živega računa.

**Varnost (obvezno):**
1. Za API ustvari **ločeno IBKR uporabniško ime** brez pravic za dvige.
2. Dokler ni faze naročil, pusti **Read-Only API** vklopljen.
3. Vsa naročila najprej testiraj na **paper računu**.
4. Porti 4001/4002 naj bodo dostopni samo v Docker omrežju, nikoli javno.
5. Ločen uporabnik tudi prepreči, da prijava v mobilno aplikacijo odklopi API sejo.

---

## 3. Ciljna arhitektura

```text
┌──────────────────────────── Frontend (Next.js) ────────────────────────────┐
│ Dashboard · Signali (inbox) · Instrument · Agentski zagon (živo) · Portfelj │
│ Dnevnik/uspešnost · Nastavitve                                              │
└───────────────▲───────────────────────────────▲─────────────────────────────┘
                │ REST (TanStack Query)          │ SSE (agentski dogodki, cene)
┌───────────────┴──────────── API (FastAPI, Python) ──────────────────────────┐
│ auth (en uporabnik) · instrumenti · signali · zagoni · portfelj · naročila  │
└──────┬──────────────┬───────────────────┬──────────────────┬────────────────┘
       │              │                   │                  │
┌──────▼─────┐ ┌──────▼────────┐ ┌────────▼────────┐ ┌───────▼──────────────┐
│ Postgres   │ │ Redis (vrsta  │ │ Agent worker    │ │ Broker servis        │
│ (+Timescale│ │ + pub/sub)    │ │ TradingAgents   │ │ ib_async → IB Gateway│
│  za svečke)│ └───────────────┘ │ (Claude)        │ │ (Docker, read-only)  │
└────────────┘                   └─────────────────┘ └──────────────────────┘
       ▲
┌──────┴──────────────────────────────────────────────────────────────────────┐
│ Scheduler (APScheduler/arq): EOD podatki · Flex sinhronizacija · screener   │
│ · nočni agentski zagoni za watchlisto · ocena preteklih signalov            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Struktura monorepa

```text
autotrading/
├── apps/web/                 # Next.js 15, React 19, shadcn/ui, lightweight-charts, trading-signals
├── services/api/             # FastAPI, SQLAlchemy/SQLModel, Alembic, Pydantic
│   ├── domain/               # signali, instrumenti, portfelj, naročila (čisti modeli)
│   ├── data/                 # ponudniki: IBKR, Finnhub/FMP, EDGAR, FRED (pogodba + testi)
│   ├── signals/              # deterministični signali (TA-Lib), screener, scoring
│   ├── agents/               # ovoj okrog TradingAgents, prompti, stroškovni števec
│   ├── broker/               # ib_async klient, Flex parser, varovala za naročila
│   └── backtest/             # vektorski backtest + walk-forward + deflated Sharpe
├── infra/docker-compose.yml  # postgres, redis, ib-gateway, api, worker, web
└── docs/
```

**Zakaj Python backend:** TradingAgents, ib_async, TA-Lib in LEAN Python API so vsi v Pythonu. Frontend ostane TypeScript. Pogodbe med njima generiraj iz OpenAPI (npr. `openapi-typescript`), da tipi ostanejo usklajeni.

### 3.2 Podatkovni model (jedro)

- `instrument` (simbol, borza, conId IBKR, sektor)
- `bar` (instrument, interval, ts, OHLCV, vir), Timescale hypertable
- `position`, `trade`, `cash` (iz Flex/ib_async, z `as_of`)
- `watchlist`, `watchlist_item`
- `signal` (instrument, vir: `rule` | `agent`, smer, moč 0..1, horizont, vstop/stop/cilj, razlaga, `created_at`, status: `new` | `accepted` | `dismissed` | `expired`)
- `agent_run` (instrument, datum analize, modeli, verzija TradingAgents, stroški v tokenih in $, trajanje, status)
- `agent_event` (run, korak/agent, tip, vsebina), za ponovni ogled debate
- `decision` (struktura `PortfolioDecision` + povezava na `signal`)
- `signal_outcome` (donos po 1/5/20 dneh, alfa proti SPY, MFE/MAE), osnova za sledenje uspešnosti
- `order_draft` (pozneje: predlog, odobritev, oddaja, IBKR orderId, revizijska sled)

### 3.3 Dva sloja signalov

1. **Deterministični sloj (poceni, vsak dan, cela watchlista ali univerzum):**
   - trend (cena nad SMA200, SMA50/200), momentum (RSI, MACD, 12-1M momentum), volatilnost (ATR, Bollinger squeeze), relativna moč proti SPY in sektorju, volumen (relativni volumen, OBV);
   - fundamentalni filtri (rast prihodkov, marže, dolg, vrednotenje proti zgodovini);
   - izhod: rangirana lista kandidatov z razlogi ("zakaj je na seznamu").
2. **Agentski sloj (drag, samo top N kandidatov ali na zahtevo):**
   - TradingAgents na kandidatih iz koraka 1 in na tvojih pozicijah (s portfeljem kot kontekstom);
   - izhod: ocena, teza, bull/bear argumenti, vstop/stop/cilj, horizont, tveganja.

To drži stroške LLM pod nadzorom (npr. 5 do 10 analiz na dan namesto 500) in vsak agentski signal ima tudi preverljivo kvantitativno podlago.

### 3.4 Frontend: zasloni

1. **Dashboard:** vrednost portfelja in dnevna sprememba, izpostavljenost po sektorjih, današnji novi signali, opozorila (stop blizu, poročilo o dobičku ta teden), stanje sistema (IB Gateway povezan, zadnja Flex sinhronizacija, poraba LLM ta mesec).
2. **Signali (inbox):** kartice s smerjo, močjo, virom (pravilo ali agent), ključnim razlogom v eni vrstici, vstopom/stopom/ciljem in razmerjem tveganje/nagrada. Akcije: *Sprejmi v načrt*, *Zavrzi (z razlogom)*, *Zaženi poglobljeno analizo*. Filtri po viru, horizontu in sektorju.
3. **Instrument:** graf (lightweight-charts) z indikatorji iz trading-signals, oznakami preteklih signalov in odločitev, fundamentalni povzetek, zadnje agentsko poročilo in zgodovina analiz.
4. **Agentski zagon v živo:** časovnica oziroma graf agentov (analitiki → debata → trader → risk → PM). Vsak korak se pretaka prek SSE, ob kliku se odpre celoten izhod. Prikazani so števec tokenov in stroškov ter končna strukturirana odločitev z gumbom "Ustvari načrt naročila".
5. **Portfelj:** pozicije iz IBKR, nerealiziran P/L, teža, za vsako pozicijo zadnja agentska ocena in "zdravje teze".
6. **Dnevnik in uspešnost:** vsak signal z izidom po 1/5/20 dneh, hit rate, povprečna alfa, kalibracija (ali "močni" signali res delujejo bolje) in primerjava pravila proti agentu proti SPY.
7. **Nastavitve:** watchlista, univerzum, izbira modelov (quick/deep), dnevni in mesečni proračun za LLM, povezave (Flex token, Gateway status).

**UX načela:**
- vsaka številka ima vir in čas osvežitve (kot že v obstoječem repoju);
- vsak signal ima razlago in ga lahko preveriš;
- nikoli "kupi zdaj" brez tvoje potrditve;
- temna tema je privzeta, gost, a berljiv prikaz.

---

## 4. Načrt po fazah

Okvirne ocene veljajo za enega razvijalca s pomočjo AI, ob delu v prostem času.

### Faza 0: Temelji (1 do 2 tedna)
- Nov monorepo (`apps/web`, `services/api`, `infra/`), docker-compose (Postgres + Timescale, Redis).
- FastAPI okostje, Alembic migracije, en uporabnik (lokalno ali za Tailscale/Cloudflare Access).
- CI: ruff, mypy, pytest, eslint, tsc, vitest.
- Prenos dobrih idej iz obstoječega repoja: pogodba ponudnika podatkov s skupnim testnim naborom, quota-aware routing, fixture fallback, prikaz izvora podatkov.
- **Rezultat:** prazen, a deploy-abilen sklad, `docker compose up` deluje.

### Faza 1: Podatki in portfelj, samo branje (2 tedna)
- Flex Web Service: nočna sinhronizacija pozicij, poslov, gotovine in dividend.
- EOD svečke: obstoječi ponudniki (Finnhub/FMP) ali yfinance za začetek, shranjevanje v `bar`.
- Zasloni Portfelj in Instrument (graf + osnovni podatki), watchlista v bazi.
- **Rezultat:** v aplikaciji vidiš svoj IBKR portfelj in grafe brez kakršnegakoli tveganja.

### Faza 2: Deterministični signali in screener (2 tedna)
- Modul `signals/` s TA-Lib, definicije pravil kot konfiguracija (YAML/JSON) s parametri.
- Dnevni screener na watchlisti (kasneje na S&P 500), zapis v `signal`.
- Inbox signalov, indikatorji v grafu prek trading-signals.
- Nočno ocenjevanje izidov (`signal_outcome`).
- **Rezultat:** vsak dan dobiš rangiran seznam kandidatov z razlogi, sistem pa že meri, ali so signali dobri.

### Faza 3: Agentska analiza (2 do 3 tedne), jedro projekta
- `agents/` ovoj okrog TradingAgents (zaklenjena verzija). Konfiguracija: Claude Sonnet za quick, Opus za deep, `TRADINGAGENTS_NO_UPDATE_CHECK=1`.
- Lasten data vendor v routerju TradingAgents, ki bere iz **tvoje** baze (enaki podatki kot v UI).
- Worker (arq/Celery) za zagone, dogodke objavlja v Redis pub/sub, API jih pretaka prek SSE v UI.
- Shranjevanje vseh korakov (`agent_event`), strukturirane odločitve in stroškov.
- Proračunska varovala: največ N zagonov na dan in $X na mesec, predpomnjenje analiz (isti tiker in dan).
- Portfelj kot kontekst (TradingAgents to podpira).
- **Rezultat:** klik "Analiziraj" na instrumentu ali signalu, debata agentov v živo, strukturiran predlog na koncu.

### Faza 4: Sledenje uspešnosti in kalibracija (1 do 2 tedna, nato stalno)
- Zaslon Dnevnik in uspešnost: pravilo proti agentu proti SPY, kalibracija moči signala.
- Avtomatski nočni agentski zagoni na top-N kandidatih in na lastnih pozicijah.
- Refleksijski spomin TradingAgents poveži z `signal_outcome` iz baze.
- **Rezultat:** po 2 do 3 mesecih imaš realne, ne backtestirane, podatke o tem, ali agent dodaja vrednost.

### Faza 5: Tržni podatki v živo in backtest (2 do 3 tedne, neobvezno)
- IB Gateway v Dockerju (`gnzsnz/ib-gateway`, Read-Only API) + ib_async servis: intraday svečke in kotacije, pozicije v živo.
- Vektorski backtest pravil z walk-forward in deflated Sharpe (prenos logike iz obstoječega `src/quant/`).
- LEAN samo, če potrebuješ realistično simulacijo naročil (ne potrebuje IB modula, če backtestiraš z lastnimi podatki; preveri licenco CLI).

### Faza 6: Pomoč pri naročilih s človeško potrditvijo (2 tedna, šele po fazi 4)
- `order_draft` iz odobrenega signala: samo limit naročila, bracket (vstop + stop + cilj), izračun velikosti glede na tveganje (npr. 0,5 do 1 % kapitala na posel).
- Varovala:
  - seznam dovoljenih simbolov;
  - največja velikost naročila in dnevna izpostavljenost;
  - kill switch;
  - dvojna potrditev;
  - popolna revizijska sled;
  - **najprej samo paper račun**.
- Šele po nekaj tednih paper trgovanja ločen servis z izklopljenim Read-Only API na živem računu.

**Skupaj do uporabnega MVP (faze 0 do 3):** ~7 do 9 tednov. Prava vrednost se pokaže po fazi 4, ko so na voljo realni izidi.

---

## 5. Stroški delovanja (okvirno, mesečno)

| Postavka | Ocena |
|---|---|
| LLM (Claude), 5 do 10 analiz na dan | ~30 do 300 $ (odvisno od modelov in števila zagonov; nastavi proračun) |
| IBKR tržni podatki za API | 0 $ (zakasnjeni) do ~10 $ (US bundle) |
| Podatki EOD/fundamenti | 0 $ (brezplačni nivoji) do ~30 $ |
| Gostovanje (VPS 4 GB ali domači strežnik) | 0 do 20 $ |
| QuantConnect (samo če želiš LEAN + IB live) | ~84 $+ (ni priporočeno na začetku) |

---

## 6. Tveganja in kako jih omejiti

| Tveganje | Ukrep |
|---|---|
| LLM "ve" prihodnost iz učnih podatkov, zato so backtesti agenta preveč optimistični | Agenta ocenjuj **samo sprotno** (faza 4). Backtesti agenta niso dokaz |
| Nedeterminističnost odločitev | Shrani celoten zagon, verzijo, modele in podatke. Pri pomembnih odločitvah poženi 2 do 3 zagone in poglej soglasje |
| Stroški LLM uidejo iz nadzora | Dnevni in mesečni proračun, deterministični predfilter, predpomnjenje |
| IB Gateway se odklopi, zahteva 2FA | Flex za portfelj (neodvisen od gatewaya), opozorilo v dashboardu, IBC auto-restart |
| Napaka pri naročilu | Read-only do faze 6, paper najprej, limit naročila, omejitve velikosti, kill switch |
| Odvisnost od hitro razvijajočega se projekta (TradingAgents) | Zaklenjena verzija, tanek adapter (`agents/`), lasten podatkovni vendor, lastni regresijski testi na fiksnih vhodih |
| Pretiravanje z obsegom | Faze 0 do 3 so MVP. Faza 6 šele, ko podatki iz faze 4 pokažejo vrednost |

---

## 7. Kaj obdržati iz obstoječega repoja

Obstoječi `PksOck/autotrading` ima dobre zamisli, ki jih je vredno prenesti (ne nujno kodo):
- **pogodba ponudnika podatkov** s skupnim testnim naborom (`src/data/provider-contract.ts`) in quota-aware composite routing;
- **prikaz izvora in svežine** vsakega podatka (`data-provenance`, `freshness-status`);
- **metodologija validacije:** IS/OOS, walk-forward, deflated Sharpe (`src/quant/validation.ts`);
- **promotion gate** za napovedne modele (`src/quant/forecast.ts`) in **pre-trade risk gate** z revizijsko sledjo (`src/paper/risk.ts`);
- determinističen DCF (lahko postane orodje, ki ga uporablja fundamentalni agent).

---

## 8. Odprta vprašanja zate

1. **Nov repo ali reorganizacija obstoječega?** Priporočam nov monorepo v tem repoju na novi veji, z obstoječo kodo v `legacy/`, dokler ne preneseš idej.
2. **Kje bo teklo?** Domači strežnik ali NAS (IB Gateway najlažje), VPS ali samo lokalno. Za dostop od zunaj: Tailscale.
3. **Horizont trgovanja?** Swing (dnevi do tedni) ali dolgoročno. To vpliva na izbiro signalov in na to, ali sploh potrebuješ podatke v realnem času (za swing/dolgoročno zadoščajo EOD + zakasnjeni).
4. **Univerzum:** samo watchlista (~20 do 50 delnic) ali S&P 500 / Nasdaq 100?
5. **Mesečni proračun za LLM?**
6. **Imaš IBKR PRO** (potrebno za API)? Ali lahko ustvariš ločenega API uporabnika?

---

## Viri

- TradingAgents: https://github.com/TauricResearch/TradingAgents (v0.7.0, 2026-10-16)
- Vibe-Trading: https://github.com/HKUDS/Vibe-Trading (v0.1.18)
- LEAN: https://github.com/QuantConnect/Lean, IB plugin: https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers
- TradeMaster: https://github.com/TradeMaster-NTU/TradeMaster
- trading-signals: https://github.com/bennycode/trading-signals (8.3.0)
- IBKR Web API FAQ: https://www.interactivebrokers.com/docs/web-api/authentication/faq
- IBKR Flex SendRequest: https://www.interactivebrokers.com/docs/web-api/api-reference/send-request.md
- TWS API: https://www.interactivebrokers.com/docs/tws-api/doc/md/introduction
- ib_async: https://pypi.org/project/ib_async/
- IB Gateway Docker: https://hub.docker.com/r/gnzsnz/ib-gateway

*Nepreverjeno: točne cene QC IB modula in IBKR tržnih podatkov za 2026, dejanski stroški in latenca TradingAgents (ocenjeno iz kode), obnašanje `READ_ONLY_API` v gnzsnz sliki.*
