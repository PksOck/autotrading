# Instrument Charts — Milestone 2 Design

**Date:** 2026-07-22

## Goal

Add responsive price, volume, and financial trend visualizations while making the domain ready for stocks, ETFs, crypto assets, and commodities. AMZN remains the only complete fixture and demonstrates an instrument with type `stock`.

## Scope

Milestone 2 includes an instrument-neutral domain, `/instruments/[symbol]`, backward-compatible `/stocks/[symbol]` redirects, a deterministic five-year AMZN price fixture, range controls, a Lightweight Charts price-and-volume view, financial trend charts, and explicit loading, empty, stale, missing-data, and error states.

It does not include live providers, additional complete instrument fixtures, authentication, watchlists, DCF, forecasting, backtesting, broker integrations, or trading execution.

## Instrument Domain

```ts
export type InstrumentType = "stock" | "etf" | "crypto" | "commodity";

export interface InstrumentSearchResult {
  symbol: string;
  name: string;
  type: InstrumentType;
  venue: string;
}

export interface InstrumentSnapshot extends InstrumentSearchResult {
  quoteCurrency: string;
  price: number;
  dailyChange: number | null;
  dailyChangePercent: number | null;
  source: string;
  asOf: string;
}
```

Stock-specific metrics and financial series are optional capabilities rather than required fields on every instrument. The provider reports whether fundamentals exist. UI sections render only supported capabilities and explain unavailable capabilities without converting them to zero.

AMZN uses `type: "stock"`, `venue: "NASDAQ"`, and `quoteCurrency: "USD"`. Small search identities may remain for AAPL and MSFT, but no new complete detail fixture is required.

## Routes and Compatibility

The canonical detail route is `/instruments/[symbol]`. Search results link to that route. `/stocks/[symbol]` performs a permanent compatibility redirect to the canonical instrument URL so existing bookmarks and tests remain valid.

Unknown symbols render the not-found state. Invalid fixture data reaches the route error boundary. The route loads snapshot, maximum price history, and optional financials concurrently.

## Price Data and Range Semantics

The AMZN price history is deterministic illustrative data checked into the repository. It spans at least five years with regular observations and includes explicit UTC timestamps, close prices, and nullable volume.

Supported ranges remain `1M`, `6M`, `1Y`, `5Y`, and `MAX`. Boundaries are calculated backward from the latest available observation, not the wall-clock date. The provider implements correct range filtering for contract consumers. For the fixture UI, the server loads `MAX` once and the client filters locally for immediate switching.

Price points are validated, de-duplicated by timestamp, and sorted ascending. Missing dates remain gaps; the system does not invent or interpolate observations. A pure transformation module owns range selection, summary calculation, and conversion to chart-library data.

## Price and Volume Chart

`PriceChart` is a client component behind a focused Lightweight Charts adapter. It receives domain `PricePoint[]`, currency, freshness, and an initial range. Library-specific types do not leak into the provider or domain layers.

The chart contains a price line and volume histogram on separate scales with one time axis and synchronized crosshair. A `ResizeObserver` keeps the chart responsive. Theme colors respond to the application light/dark state, and the chart keeps a stable height during loading and empty states.

Range controls use native buttons with `aria-pressed`. Above the canvas, a text summary always reports the selected period, first price, last price, absolute and percentage change, currency, and observation count. This summary is the accessible source of the chart's key meaning.

## Financial Trend Charts

Existing annual and quarterly tables remain the authoritative accessible and exact-value presentation. Compact charts above the tables visualize revenue, operating income, and free cash flow.

Financial charts use simple semantic SVG or CSS bars rather than Lightweight Charts. They share a zero baseline where appropriate, show currency and unit, and expose a text alternative. A `null` value creates a labelled gap reading “Not available”; it never creates a zero-height value.

Instruments without fundamentals omit financial charts and tables and show one concise capability message.

## States and Errors

- Loading: stable chart frame with `role="status"`.
- Empty price history: explanation inside the chart frame and no library initialization.
- Stale data: visible stale badge and unchanged source/as-of metadata.
- Missing volume: price remains visible; volume is omitted with an explanation.
- Missing financial observation: visible gap and “Not available” in the table.
- Unknown instrument: route not-found state.
- Invalid fixture: generic error boundary with retry.

## Testing

Vitest covers instrument schemas, backward-compatible mappings, deterministic fixture validity, de-duplication, sorting, every range boundary, summary calculations, missing-volume behavior, and nullable financial chart data.

React Testing Library covers range button state, accessible text summaries, empty/stale states, and conditional fundamentals. The Lightweight Charts module is wrapped behind the adapter boundary; tests verify inputs and lifecycle rather than canvas internals.

Playwright covers home search to `/instruments/AMZN`, all range controls, visible price/volume/financial sections, legacy `/stocks/AMZN` redirection, light/dark rendering, and desktop/mobile layouts without document overflow.

The required quality gates remain:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm build
```

## Acceptance Criteria

- AMZN is represented as a stock through the instrument-neutral domain.
- Search uses the canonical instrument route and the old stock route redirects.
- The checked-in fixture supports meaningful `1M`, `6M`, `1Y`, `5Y`, and `MAX` views.
- Range switching is immediate and its text summary remains accessible.
- Price and available volume render responsively in light and dark themes.
- Revenue, operating income, and FCF trends supplement the existing tables.
- Missing, empty, stale, loading, not-found, and invalid-data states are explicit.
- No graph interpolates missing observations or converts `null` to zero.
- Unit, currency, source, and freshness remain visible.
- Lint, strict typecheck, unit/component tests, desktop/mobile Playwright tests, and production build pass.

## Deferred Work

Complete ETF, crypto, and commodity fixtures and their type-specific metrics are deferred to a later milestone. DCF and watchlists remain Milestone 3 work. Live providers, caching, retries, and protected API keys remain Milestone 4 work.
