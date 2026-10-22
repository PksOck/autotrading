# services/agents: agentski cevovodi

Vsi LLM klici gredo prek LiteLLM vlog (ADR-0004). Vsak izhod ima Pydantic shemo in test na posnetku podatkov.

| Mapa | Namen | Vloga | Mejnik |
|---|---|---|---|
| `deep_research/` | TradingAgents adapter + `vendor_local` (ADR-0003) | cloud-quick / cloud-deep | M4 |
| `etf_analyst/` | ETF: profil, prekrivanje, tema, odločitev | local-reason → cloud-deep | M4 |
| `dip_analyst/` | vzrok padca: trg / sektor / začasno / temeljno | local-reason → cloud-quick | M3 |
| `options_strategist/` | izbira opcijske strukture (številke računa koda) | cloud-deep (Claude) | M6 |
| `thesis_tracker/` | tedenski pregled tez | cloud-deep (Claude) | M5 |
| `knowledge/` | Markdown znanje za pozive (prirejeno iz Vibe-Trading skills, MIT) | | M4 |

Pozivi so v angleščini, uporabniška polja v jeziku uporabnika (VOICE.md §7).
