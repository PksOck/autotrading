# Instrument Charts Milestone 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize the AMZN stock vertical into an instrument-ready domain and add accessible price, volume, and financial trend charts.

**Architecture:** Canonical `/instruments/[symbol]` server routes load instrument-neutral domain objects and maximum history. Pure transformation functions filter and summarize history; a client chart component talks to Lightweight Charts through one adapter while accessible HTML carries the chart meaning.

**Tech Stack:** Node.js 22 LTS, pnpm, Next.js 15, React 19, strict TypeScript, Tailwind CSS 4, Zod, Lightweight Charts, Vitest, React Testing Library, Playwright.

## Global Constraints

- Supported instrument types are exactly `stock`, `etf`, `crypto`, and `commodity`.
- AMZN is the only complete detail fixture and has type `stock`.
- Canonical detail URLs use `/instruments/[symbol]`; `/stocks/[symbol]` redirects permanently.
- Range boundaries use the latest observation, not wall-clock time.
- Missing observations remain gaps; `null` is never converted to zero or interpolated.
- Currency, unit, source, freshness, and accessible text summaries remain visible.
- No live providers, DCF, watchlist, forecasting, backtesting, brokers, or execution.

---

### Task 1: Instrument-neutral domain and compatibility route

**Files:**
- Create: `src/domain/instrument.ts`, `src/domain/instrument.test.ts`
- Modify: `src/domain/stock.ts`, `src/domain/fixture-schema.ts`, `src/domain/fixture-schema.test.ts`
- Modify: `src/data/market-data-provider.ts`, `src/data/fixture-provider.ts`, `src/data/fixtures/amzn.json`, `src/data/fixtures/search-index.json`
- Create: `src/app/instruments/[symbol]/page.tsx`, `loading.tsx`, `not-found.tsx`, `error.tsx`
- Modify: `src/app/stocks/[symbol]/page.tsx`, `src/components/search/stock-search.tsx`, related tests

**Interfaces:**
- Produces `InstrumentType`, `InstrumentSearchResult`, `InstrumentSnapshot`, and provider methods `searchInstruments`, `getInstrumentSnapshot`, `getFinancials`, `getPriceHistory`.
- Canonical route consumes these interfaces; legacy stock route returns `permanentRedirect('/instruments/' + symbol)`.

- [ ] **Step 1: Write failing domain, provider, link, and redirect tests**

```ts
expect(instrumentTypeSchema.options).toEqual(["stock", "etf", "crypto", "commodity"]);
expect((await provider.getInstrumentSnapshot("AMZN")).type).toBe("stock");
expect((await provider.searchInstruments("amazon"))[0]).toMatchObject({
  symbol: "AMZN", name: "Amazon.com, Inc.", type: "stock", venue: "NASDAQ",
});
expect(screen.getByRole("link", { name: /amazon/i })).toHaveAttribute("href", "/instruments/AMZN");
```

Mock `next/navigation.permanentRedirect` in the legacy route test and assert it receives `/instruments/AMZN`.

- [ ] **Step 2: Run RED**

Run: `pnpm test src/domain/instrument.test.ts src/data/fixture-provider.test.ts src/components/search/stock-search.test.tsx src/app/stocks`

Expected: FAIL because instrument types, renamed provider methods, canonical route, and redirect do not exist.

- [ ] **Step 3: Implement the exact domain and mapping**

```ts
export type InstrumentType = "stock" | "etf" | "crypto" | "commodity";
export interface InstrumentSearchResult {
  symbol: string; name: string; type: InstrumentType; venue: string;
}
export interface InstrumentSnapshot extends InstrumentSearchResult {
  quoteCurrency: string; price: number; dailyChange: number | null;
  dailyChangePercent: number | null; source: string; asOf: string;
  stockMetrics: StockMetrics | null;
}
```

Move stock-only market cap, enterprise value, P/E, EV/EBITDA, and FCF yield into `StockMetrics`. Update Zod fixtures, provider, search UI, canonical route, and legacy permanent redirect without changing visible AMZN content.

- [ ] **Step 4: Run GREEN and commit**

Run: `pnpm test src/domain src/data src/components/search src/app/stocks src/app/instruments && pnpm lint && pnpm typecheck && pnpm build`

Expected: PASS; build lists `/instruments/AMZN` and the compatibility route.

Run: `git add src && git commit -m "refactor: generalize stock research to instruments"`

### Task 2: Deterministic five-year history and pure transformations

**Files:**
- Create: `scripts/generate-amzn-history.mjs`
- Modify: `src/data/fixtures/amzn.json`, `src/data/fixture-provider.ts`, `src/data/fixture-provider.test.ts`
- Create: `src/lib/price-history.ts`, `src/lib/price-history.test.ts`

**Interfaces:**
- Produces `filterPriceHistory(points, range)`, `summarizePriceHistory(points, currency)`, `toChartPoints(points)`, and deterministic checked-in history.
- `summarizePriceHistory` returns range endpoints, absolute/percent change, currency, and observation count, or `null` for empty input.

- [ ] **Step 1: Write failing range and summary tests**

```ts
const points = monthlyPointsFrom("2021-07-31", "2026-07-31");
expect(filterPriceHistory(points, "1M").at(0)?.timestamp).toBe("2026-06-30T20:00:00Z");
expect(filterPriceHistory(points, "1Y").at(0)?.timestamp).toBe("2025-07-31T20:00:00Z");
expect(filterPriceHistory(points, "MAX")).toHaveLength(points.length);
expect(summarizePriceHistory([{ timestamp: "2026-01-01T20:00:00Z", close: 100, volume: null }, { timestamp: "2026-02-01T20:00:00Z", close: 125, volume: 10 }], "USD")).toMatchObject({
  startPrice: 100, endPrice: 125, absoluteChange: 25, percentChange: 0.25, observationCount: 2,
});
```

Also test duplicate timestamps keep the final observation, sorting is ascending, empty summary is `null`, and missing volume remains `null`.

- [ ] **Step 2: Run RED**

Run: `pnpm test src/lib/price-history.test.ts src/data/fixture-provider.test.ts`

Expected: FAIL because pure transformations and range-aware provider behavior do not exist.

- [ ] **Step 3: Implement deterministic fixture and transformations**

The generator uses a fixed seed and fixed start/end dates to emit regular business-day UTC observations. It writes no runtime data and is used only to reproduce the committed JSON. Implement range cutoffs from the final sorted timestamp with month arithmetic; include the latest point and every point at or after the cutoff.

```ts
export function summarizePriceHistory(points: PricePoint[], currency: string) {
  if (points.length === 0) return null;
  const first = points[0]; const last = points[points.length - 1];
  return { startPrice: first.close, endPrice: last.close,
    absoluteChange: last.close - first.close,
    percentChange: (last.close - first.close) / first.close,
    currency, observationCount: points.length };
}
```

- [ ] **Step 4: Run GREEN and commit**

Run: `node scripts/generate-amzn-history.mjs --check && pnpm test src/lib/price-history.test.ts src/data/fixture-provider.test.ts && pnpm typecheck`

Expected: generator check confirms committed output; tests and typecheck PASS.

Run: `git add scripts src/data src/lib && git commit -m "feat: add deterministic instrument price history"`

### Task 3: Accessible Lightweight Charts price and volume view

**Files:**
- Modify: `package.json`, `pnpm-lock.yaml`
- Create: `src/components/charts/lightweight-chart-adapter.ts`, `price-chart.tsx`, `price-chart.test.tsx`
- Modify: `src/app/instruments/[symbol]/page.tsx`, `src/app/globals.css`

**Interfaces:**
- Produces `PriceChart({ points, currency, source, asOf, initialRange })`.
- Adapter produces `mountPriceVolumeChart(element, data, options): { updateTheme; resize; destroy }` and contains every `lightweight-charts` import.

- [ ] **Step 1: Install dependency and write failing accessible behavior tests**

Run: `pnpm add lightweight-charts@5`

```tsx
render(<PriceChart points={points} currency="USD" source="Illustrative fixture data" asOf="2026-07-22T12:00:00Z" initialRange="1Y" />);
expect(screen.getByRole("button", { name: "1Y" })).toHaveAttribute("aria-pressed", "true");
await user.click(screen.getByRole("button", { name: "1M" }));
expect(screen.getByRole("button", { name: "1M" })).toHaveAttribute("aria-pressed", "true");
expect(screen.getByText(/observations/i)).toBeInTheDocument();
```

Add tests that empty points render `No price history available`, stale metadata remains visible, and all-null volume renders `Volume not available` without mounting a volume series.

- [ ] **Step 2: Run RED**

Run: `pnpm test src/components/charts/price-chart.test.tsx`

Expected: FAIL because `PriceChart` and adapter do not exist.

- [ ] **Step 3: Implement component and adapter**

Use `aria-pressed` native range buttons, pure Task 2 transformations, stable `.chart-frame`, a textual summary, `ResizeObserver`, and cleanup that calls `destroy()`. The adapter creates one line series and an optional histogram series on a separate price scale with a shared time scale and crosshair. Empty data bypasses adapter creation.

- [ ] **Step 4: Run GREEN and commit**

Run: `pnpm test src/components/charts/price-chart.test.tsx && pnpm lint && pnpm typecheck && pnpm build`

Expected: PASS with no warnings and AMZN instrument route includes the chart section.

Run: `git add package.json pnpm-lock.yaml src/components/charts src/app && git commit -m "feat: add accessible price and volume chart"`

### Task 4: Financial trend charts with nullable gaps

**Files:**
- Create: `src/components/charts/financial-trend-chart.tsx`, `financial-trend-chart.test.tsx`
- Modify: `src/components/stock/financial-trends.tsx`, `stock-detail.test.tsx`, `src/app/globals.css`

**Interfaces:**
- Produces `FinancialTrendChart({ periods, metric, label, currency, unit })` for `revenue`, `operatingIncome`, and `freeCashFlow`.
- Existing `FinancialTrends` keeps its table and composes three chart instances only when financial capability exists.

- [ ] **Step 1: Write failing semantic chart tests**

```tsx
render(<FinancialTrendChart periods={periods} metric="freeCashFlow" label="Free cash flow" currency="USD" unit="millions" />);
expect(screen.getByRole("img", { name: /free cash flow trend.*USD millions/i })).toBeInTheDocument();
expect(screen.getByText("Not available")).toBeInTheDocument();
expect(screen.queryByText("0", { exact: true })).not.toBeInTheDocument();
```

Assert existing table values still render and instruments with `financials: null` show one `Fundamentals are not available for this instrument type` message.

- [ ] **Step 2: Run RED**

Run: `pnpm test src/components/charts/financial-trend-chart.test.tsx src/components/stock/stock-detail.test.tsx`

Expected: FAIL because the financial chart and capability state do not exist.

- [ ] **Step 3: Implement SVG/CSS bars and composition**

Compute scale from non-null values only. Render each non-null bar with an accessible label containing period and formatted value; render each null as a labelled gap. Preserve tables directly below the charts.

- [ ] **Step 4: Run GREEN and commit**

Run: `pnpm test src/components/charts src/components/stock && pnpm lint && pnpm typecheck`

Expected: PASS; null FCF remains `Not available` in chart and table.

Run: `git add src/components src/app/globals.css && git commit -m "feat: visualize financial trends accessibly"`

### Task 5: E2E, documentation, and final quality gates

**Files:**
- Modify: `e2e/stock-search.spec.ts`, `e2e/stock-detail.spec.ts`, `playwright.config.ts`
- Modify: `docs/architecture.md`, `docs/methodology.md`, `docs/roadmap.md`
- Modify: `.github/workflows/ci.yml` only if existing commands do not already cover the new suite

**Interfaces:**
- Produces browser coverage for canonical navigation, legacy redirect, ranges, charts, theme, and responsive layouts.

- [ ] **Step 1: Write failing browser expectations**

```ts
await page.goto("/");
await page.getByRole("searchbox", { name: /symbol or company/i }).fill("Amazon");
await page.getByRole("link", { name: /amazon/i }).click();
await expect(page).toHaveURL(/\/instruments\/AMZN$/);
for (const range of ["1M", "6M", "1Y", "5Y", "MAX"]) {
  await page.getByRole("button", { name: range, exact: true }).click();
  await expect(page.getByRole("button", { name: range, exact: true })).toHaveAttribute("aria-pressed", "true");
}
```

Add `/stocks/AMZN` redirect assertion, visible price summary, volume/financial headings, dark theme toggle, and no overflow in desktop/mobile projects.

- [ ] **Step 2: Run RED**

Run: `pnpm test:e2e`

Expected: FAIL on canonical URL, range controls, or new chart assertions before final integration.

- [ ] **Step 3: Update documentation and any integration copy**

Document the instrument capability model, deterministic fixture, range semantics, chart accessibility, missing-data gaps, and canonical route. Roadmap names complete ETF/crypto/commodity fixtures as deferred work.

- [ ] **Step 4: Run complete verification**

Run: `pnpm lint && pnpm typecheck && pnpm test && pnpm test:e2e && pnpm build && git diff --check`

Expected: zero lint warnings, zero type errors, all unit/component/browser tests PASS, successful production build, and no whitespace errors.

- [ ] **Step 5: Commit**

Run: `git add e2e docs .github playwright.config.ts src && git commit -m "test: verify instrument charts milestone 2"`
