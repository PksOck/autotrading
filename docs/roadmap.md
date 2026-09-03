# Roadmap

1. Milestone 1: fixture-backed AMZN search and research detail page.
2. Milestone 2: interactive price and financial charts with range controls (complete for the deterministic AMZN fixture).
3. Milestone 3: deterministic two-stage DCF scenarios and localStorage watchlist (complete; instrument page, `/watchlist`, provider contract suite).
4. Milestone 4: licensed provider selection and contract reuse (groundwork done: `withRetry` backoff, `CachedMarketDataProvider` TTL decorator, server-only env key convention in `.env.example`). Remaining: vendor choice, server-side secrets wiring, cache TTL tuning against real quotas.

Forecasting, backtesting, brokers, and execution remain separate future systems.

Complete ETF, crypto, and commodity fixtures are deferred work; their availability and financial-data capabilities must be represented explicitly before their instrument pages are enabled.
