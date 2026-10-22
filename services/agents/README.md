# services/agents: agentski cevovodi

Vsi LLM klici gredo prek LiteLLM vlog (ADR-0004). Vsak izhod ima Pydantic shemo in test na posnetku podatkov. Zasnova: [ADR-0011](../../docs/adr/ADR-0011-storitev-agentov.md).

| Mapa | Namen | Vloga | Mejnik |
|---|---|---|---|
| `preza_agents/deep_research/` | TradingAgents adapter (`adapter.py`), `vendor_local.py`, posnetek podatkov (`snapshot.py`), časovnica korakov (`timeline.py`) | cloud-quick / cloud-deep | M4 |
| `preza_agents/worker.py` | arq delavec na vrsti `arq:agents` (`deep_analysis`, `sweep_runs`) | | M4 |
| `etf_analyst/` | ETF: profil, prekrivanje, tema, odločitev | local-reason → cloud-deep | M4 (BL-083) |
| `options_strategist/` | izbira opcijske strukture (številke računa koda) | cloud-deep | M6 |
| `thesis_tracker/` | tedenski pregled tez | cloud-deep | M5 |
| `knowledge/` | Markdown znanje za pozive (prirejeno iz Vibe-Trading skills, MIT) | | M4 (BL-087) |

`dip_analyst` (M3) živi v `services/api/preza/entries/dip.py`, ker je majhen in teče v API delavcu.

## Lokalno

```bash
cd services/agents
uv sync
uv run pytest -q                       # cel graf s skriptiranim modelom, brez omrežja
TEST_DATABASE_URL=postgresql+asyncpg://preza:preza@localhost:5433/preza_test uv run pytest -q
uv run arq preza_agents.worker.WorkerSettings
```

## Regresijski testi (BL-086)

`tests/regression/` požene pet fiksnih posnetkov (rast in poceni, padec in drago, samo govorica, kratka zgodovina, ETF) in primerja determinističen del zagona z datotekami v `golden/`: besedilo vsakega podatkovnega orodja (kontrolna vsota in prve vrstice), zaporedje korakov, opozorila in kontrolno oceno. Pred nadgradnjo TradingAgents morajo iti skozi (ADR-0003). Po nameravani spremembi:

```bash
UPDATE_GOLDEN=1 uv run pytest tests/regression   # nato preglej diff v golden/ kot kodo
```

Pozivi so v angleščini, poročila v jeziku uporabnika (`output_language`, VOICE.md §7).
