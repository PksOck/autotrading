# PLAN.md

Povzetek sprejetega načrta. Podrobna utemeljitev je v [`docs/research/2026-10-22-zasnova-resitve.md`](./docs/research/2026-10-22-zasnova-resitve.md), primerjava kandidatov v [`docs/research/2026-10-22-analiza-kandidatov.md`](./docs/research/2026-10-22-analiza-kandidatov.md).

## 1. Cilj

Zaznati **(a) priložnost iz novic, filingov in špekulacij** ter **(b) dobro (ponovno) vstopno točko** za kakovostne delnice in ETF-je. Uporabnik je dolgoročni vlagatelj pri IBKR, ki občasno kupi kratkoročno ali uporabi opcije. Podatki v realnem času niso potrebni.

## 2. Okvirni pogoji (potrjeno v S-001)

| Tema | Odločitev |
|---|---|
| Gostovanje | Docker Compose lokalno, dostop prek Tailscale ([ADR-0001](./docs/adr/ADR-0001-docker-lokalno.md)) |
| Lokalni LLM | ločena naprava v LAN, **24 GB VRAM**, Ollama, Qwen ~27B Q4 (točno verzijo potrdi v BL-012) |
| Oblačni LLM | **Claude Pro** (Agent SDK kredit), **OpenAI** naročnina (ChatGPT prijava), **OpenCode** naročnina. API ključev zaenkrat ni |
| Broker | IBKR PRO: Flex Web Service + IB Gateway (Read-Only API) + ib_async |
| Univerzum | trije pogledi: **Novi predlogi** (S&P 500 + Nasdaq 100 + izbrani ETF-ji), **Watchlista**, **Portfelj** |
| Obvestila | Telegram bot (long polling, brez javnega webhooka) |
| Jezik | slovenščina privzeto, preklop na angleščino (next-intl) ([ADR-0005](./docs/adr/ADR-0005-i18n-sl-privzeto.md)) |
| Tema | svetla in temna, privzeto po sistemu |
| Prejšnja koda | veja `legacy` (samo za branje) |

## 3. Arhitektura

```text
 Tailscale ─► web (Next.js) ──REST/SSE──► api (FastAPI)
                                            │
     ┌──────────────┬──────────────┬────────┼─────────────┬───────────────┐
     ▼              ▼              ▼        ▼             ▼               ▼
 postgres        redis          worker   claude_runner   broker          notify
 Timescale       vrste,         (arq)    Agent SDK       ib_async ─►     Telegram
 pgvector        pub/sub        ingest,  (Claude Pro)    ib-gateway      bot
                                radar,                   (read-only)
                                agenti
                                   │
                                   ▼
                               litellm ──► Ollama (GPU naprava v LAN)
                                       ──► OpenCode · OpenAI (ChatGPT prijava)
```

Odločitve: [ADR-0002](./docs/adr/ADR-0002-python-backend-nextjs-frontend.md) (sklad), [ADR-0003](./docs/adr/ADR-0003-tradingagents-kot-odvisnost.md) (TradingAgents), [ADR-0004](./docs/adr/ADR-0004-llm-vloge-litellm.md) (LLM vloge), [ADR-0006](./docs/adr/ADR-0006-clovek-vedno-odloci.md) (brez samodejnih naročil), [ADR-0007](./docs/adr/ADR-0007-telegram-obvestila.md) (Telegram).

## 4. LLM vloge (prilagojeno tvoji opremi)

| Vloga | Model | Naloge | Obseg |
|---|---|---|---|
| `embed` | Ollama `bge-m3` ali `nomic-embed-text` (~1 GB VRAM) | vektorji novic, grozdenje | vse novice |
| `local-fast` | Ollama Qwen ~27B Q4, *brez razmišljanja* | triaža novic (JSON), tikerji, tip dogodka, sentiment, povzetek | stotine na dan |
| `local-reason` | isti model, *z razmišljanjem* | prvi prehod analize vzroka padca, ETF tema, prevodi povzetkov | desetine na dan |
| `cloud-quick` | OpenCode Go (GLM / Kimi / DeepSeek) | analitiki in debata v TradingAgents | nekaj zagonov na dan |
| `cloud-deep` | OpenAI prek ChatGPT prijave (TradingAgents), **Claude** prek Agent SDK (naši agenti) | končne odločitve, opcijski strateg, tedenski pregled tez | omejeno s krediti |

**Claude Pro je redek vir.** Agent SDK kredit za Pro je po tretjih virih okoli 20 $/mes. (preveri v računu, BL-013). Uporabimo ga samo za:
1. tedenski pregled tez portfelja (M5);
2. končno odločitev za največ 2 do 3 najmočnejše eskalacije na teden;
3. opcijskega stratega (M6).

Ko kredit poide, LiteLLM preklopi na `cloud-deep` prek OpenAI.

**Opomba o VRAM:** 27B Q4 zasede ~16 do 18 GB. Ob embed modelu ostane ~5 GB za kontekst, zato je vzporednost 1 do 2 zahtevi. Če triaža ne dohaja (S&P 500 ustvari veliko novic), dodamo manjši model (Qwen ~8B) za `local-fast` (BL-012).

## 5. Cevovodi

1. **Ingest** (`services/api/ingest`): IBKR EOD svečke in opcijske verige (zakasnjeno), Flex (portfelj), SEC EDGAR (8-K, Form 4, 13D/G), Finnhub (novice, koledar poročil), RSS (sporočila za javnost), Reddit/StockTwits (samo watchlista + kandidati), yfinance (fallback, ETF holdings), FRED.
2. **Radar** (`services/api/radar`): normalizacija → embed → grozdenje v dogodke → triaža (`local-fast`) → deterministični kontekst (odziv cene, pozornost) → ocena priložnosti → eskalacija → signal `catalyst` → Telegram.
3. **Vstopi** (`services/api/entries`): pravila (trend, pullback, podpora, padec od vrha, pasovi vrednotenja, insiderji) → `dip_analyst` (`local-reason` → `cloud-quick` pri dvomu) → signal `entry` ali `thesis_break` → lestvica postopnega nakupa.
4. **Globoka analiza** (`services/agents/deep_research`): TradingAgents (delnice), naš ETF analitik (ETF), SSE v UI.
5. **Teze** (`services/agents/thesis_tracker`): tedenski pregled prek Claude.
6. **Opcije** (`services/api/options` + `services/agents/options_strategist`): CSP, covered call, call spread, protective put. Izračuni so deterministični.
7. **Izidi** (`services/api/signals/outcomes.py`): donos po 1, 5, 20 in 60 dneh, alfa, kalibracija.

## 6. Mejniki

| ID | Mejnik | Rezultat (definicija "končano") | Naloge |
|---|---|---|---|
| **M0** | Temelji | `docker compose up` zažene vse servise. LiteLLM odgovori na vseh 5 vlog. CI je zelen. Prazna lupina UI (SL/EN, tema) | BL-001–BL-019 |
| **M1** | Podatki + portfelj | Flex in EOD svečke v bazi. SCR-08 Portfelj in SCR-05 Instrument (osnova) delujeta. Watchlista v bazi | BL-020–BL-039 |
| **M2** | Radar | dogodki za tri poglede, triaža lokalno, ocena, SCR-02 in SCR-04, Telegram obvestila | BL-040–BL-059 |
| **M3** | Vstopi | pravila, `dip_analyst`, SCR-03, lestvica, beleženje izidov | BL-060–BL-079 |
| **M4** | Globoka analiza | TradingAgents adapter, ETF analitik, claude_runner, SCR-06 v živo | BL-080–BL-099 |
| **M5** | Teze + uspešnost | SCR-09, SCR-10, kalibracija uteži | BL-100–BL-119 |
| **M6** | Opcije | veriga, payoff, strateg, SCR-07 | BL-120–BL-139 |
| **M7** | Naročila s potrditvijo | osnutki naročil, varovala, najprej paper račun | BL-140–BL-159 |

**Uporabna verzija (M0 do M3): ~7 do 9 tednov.**

## 7. Kaj prevzamemo iz odprtokodnih projektov (povzetek)

| Repo | Prevzamemo | Način |
|---|---|---|
| TradingAgents | celoten agentski graf za delnice, SSE pretakanje, sheme odločitev, portfelj kot kontekst | odvisnost, zaklenjena verzija |
| Vibe-Trading | read-only IBKR konektor, opcijska matematika in UI ideje, Markdown znanje za agente, varovala naročil | prepis izbranih delov (MIT) |
| LEAN | koncept Insight → naša shema `Signal`, ločitev Alpha/Portfolio/Risk/Execution | ideja |
| trading-signals | indikatorji na grafih v brskalniku | odvisnost |
| legacy (naš) | pogodba virov podatkov, kvote, prikaz izvora, validacija, risk gate, DCF | prepis v Python |

Podrobno (datoteke, poti): research §3.
