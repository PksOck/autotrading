# Roadmap

1. Milestone 1: fixture-backed AMZN search and research detail page.
2. Milestone 2: interactive price and financial charts with range controls (complete for the deterministic AMZN fixture).
3. Milestone 3: deterministic two-stage DCF scenarios and localStorage watchlist (complete; instrument page, `/watchlist`, provider contract suite).
4. Milestone 4: multi-vendor live layer done (Finnhub prices, FMP fundamentals, AlphaVantage fallback, CoinGecko crypto, FRED macro, quota-aware composite with fixture fallback). Remaining: real key wiring and TTL tuning against quotas.
5. Milestone 5: quant research core done (`src/quant/` indicators, event-driven backtester with costs, IS/OOS splits, walk-forward folds, deflated-Sharpe guard, SMA-cross vs buy-and-hold on the instrument page).

Forecasting ML, brokers, and execution remain separate future systems.

Complete ETF, crypto, and commodity fixtures are deferred work; their availability and financial-data capabilities must be represented explicitly before their instrument pages are enabled.
