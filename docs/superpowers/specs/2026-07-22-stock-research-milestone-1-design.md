# Stock Research MVP — Milestone 1 Design

**Date:** 2026-07-22

## Goal

Deliver a working, testable AMZN vertical slice of the stock-research portal. A user can search fixture-backed securities, open `/stocks/AMZN`, and inspect a clear market snapshot and fundamental data with source, currency, units, freshness, and missing-data states.

## Scope

Milestone 1 includes the Next.js application foundation, quality commands, responsive shell and theme, domain contracts and Zod validation, a fixture-backed provider, stock search, and a complete AMZN detail page. It excludes interactive charts, DCF valuation, watchlists, authentication, databases, live market APIs, forecasting, backtesting, and broker integrations.

## Architecture

Use Next.js 15 App Router with React 19 and strict TypeScript. Server components load market data through a `MarketDataProvider` interface. `FixtureMarketDataProvider` reads bundled fixtures and validates their external shape with Zod before converting them into domain objects. UI components receive domain objects rather than raw JSON, keeping rendering independent from the eventual licensed data provider.

The initial vertical is deliberately server-first. The only client-side behavior in this milestone is search navigation and theme control. This minimizes JavaScript, keeps data access on the server, and preserves a clean boundary for future API credentials.

## Components and Routes

- `/`: product introduction, prominent stock search, and fixture-universe disclosure.
- `/stocks/[symbol]`: symbol normalization, provider lookup, AMZN snapshot, core market metrics, annual and quarterly financial summaries, risks, and provenance.
- `/methodology`: concise explanation of fixture data, freshness, missing values, and research-only limitations.
- Shared header and footer: navigation, theme control, and research-only notice.
- Reusable stock UI: stock header, metric card, financial trends table, data provenance, and explicit empty/stale/error presentations.

Unknown symbols return the Next.js not-found state. Provider validation failures return an error state without leaking internal details.

## Data Contract

The provider exposes:

```ts
export type PriceRange = "1M" | "6M" | "1Y" | "5Y" | "MAX";

export interface MarketDataProvider {
  searchStocks(query: string): Promise<StockSearchResult[]>;
  getStockSnapshot(symbol: string): Promise<StockSnapshot>;
  getPriceHistory(symbol: string, range: PriceRange): Promise<PricePoint[]>;
  getFinancials(symbol: string): Promise<FinancialSeries>;
}
```

All timestamps are ISO-8601 UTC. Currency, source, and `asOf` are mandatory. Missing observations use `null`, never zero. Prices and financial values retain explicit units. The fixture provider performs case-insensitive search by symbol and company name and normalizes requested symbols to uppercase.

AMZN is the required complete fixture. Small AAPL and MSFT search records may be included to prove multi-result search, but their detail pages are not required in this milestone.

## User Experience

The design is responsive, accessible, and supports light and dark themes. The AMZN page orders information as identity and price, freshness and provenance, key market metrics, annual financials, quarterly financials, then risks and limitations. Every displayed number uses a centralized formatter so currency, percentages, multiples, large values, and unavailable values remain consistent.

Stale data is visibly labelled based on fixture metadata; the UI never silently presents it as current. Missing values render as “Not available” with their surrounding label and unit preserved.

## Error Handling

- Empty search does not navigate and shows a short prompt.
- No matching fixture produces an empty result message.
- Unknown stock detail routes use `notFound()`.
- Invalid fixture data throws a typed provider error and renders the route error boundary.
- Formatting functions accept `null` and never coerce missing data to zero.

## Testing and Quality

Vitest covers domain schemas, symbol normalization, provider search and lookup, fixture validation, formatters, stale-state logic, and component rendering. React Testing Library verifies the search flow and key AMZN content. Playwright covers home-to-AMZN navigation and the responsive stock page on desktop and mobile.

The required verification commands are:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm build
```

Each behavior is implemented test-first. Continuous integration runs install, lint, typecheck, unit tests, and build; browser tests run in their own job with the required Playwright browser.

## Acceptance Criteria

- The app starts and builds with Node.js 22 LTS and pnpm.
- A user can search for AMZN by symbol or company name and open `/stocks/AMZN`.
- The AMZN page shows price, daily change, exchange, currency, market metrics, financial summaries, source, and freshness.
- Every financial value presents its unit or format and unavailable data is explicit.
- Unknown symbols, empty search, stale data, missing data, and provider errors have defined states.
- Light and dark themes work on desktop and mobile layouts.
- Lint, strict typecheck, unit tests, Playwright tests, and production build pass.
- No trading, forecasting, target-price, or buy/sell claims appear in the product.

## Deferred Work

Interactive price and financial charts belong to Milestone 2. DCF scenarios and the local watchlist belong to Milestone 3. Live-provider contracts, caching, retry policy, and API-key handling belong to Milestone 4.
