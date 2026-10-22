# services/api: FastAPI

Domena, podatki in deterministična logika. **Brez LLM klicev v request poti** (ti tečejo v workerju).

```text
domain/        Pydantic modeli: Signal, Event, Instrument, Thesis ... (research §4.2)
data/          pogodba virov, router, kvote (BL-020, BL-021)
ingest/        finnhub, rss, edgar, yfinance, ibkr_bars, flex, fred, etf (M1, M2)
radar/         triage, cluster, score, escalate (M2)
entries/       rules, valuation_bands, ladder (M3)
signals/       indicators (TA-Lib), screener, outcomes (M2, M3)
options/       chain, payoff, strategies (M6)
portfolio/     flex_parser, exposure (M1)
backtest/      vectorized, validation (kasneje)
routes/        REST + SSE
worker/        arq opravila in razpored
migrations/    Alembic
```

Ref: PLAN.md §5, ADR-0002.
