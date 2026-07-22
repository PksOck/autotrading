# Stock Research Milestone 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested AMZN stock-research vertical slice with fixture search, responsive detail page, provenance, and quality gates.

**Architecture:** Next.js App Router server components consume validated domain objects through `MarketDataProvider`. `FixtureMarketDataProvider` validates bundled JSON with Zod; client code is limited to search and theme interaction.

**Tech Stack:** Node.js 22 LTS, pnpm, Next.js 15, React 19, strict TypeScript, Tailwind CSS 4, Zod, Vitest, React Testing Library, Playwright, ESLint, Prettier.

## Global Constraints

- Show currency, unit, source, and `asOf`; missing values are `null`, never zero.
- No charts, DCF, watchlist, live API, trading, forecasting, target-price, or buy/sell claims.
- Implement every behavior test-first: RED, GREEN, refactor.

---

### Task 1: Application and quality foundation

**Files:**
- Create: `package.json`, `pnpm-workspace.yaml`, `next.config.ts`, `tsconfig.json`, `next-env.d.ts`
- Create: `eslint.config.mjs`, `.prettierrc.json`, `.gitignore`, `vitest.config.ts`, `playwright.config.ts`
- Create: `src/test/setup.ts`, `src/app/globals.css`, `src/app/layout.tsx`, `src/app/page.tsx`
- Test: `src/app/page.test.tsx`

**Interfaces:** Produces scripts `dev`, `build`, `lint`, `typecheck`, `test`, `test:e2e`, strict TS, `@/*` alias, and jsdom.

- [ ] **Step 1: Write the failing home-page test**

```tsx
import { render, screen } from "@testing-library/react";
import HomePage from "./page";
it("identifies stock research", () => {
  render(<HomePage />);
  expect(screen.getByRole("heading", { name: /research stocks/i })).toBeInTheDocument();
});
```

- [ ] **Step 2: Install dependencies and verify RED**

Run: `pnpm add next@15 react@19 react-dom@19 zod && pnpm add -D typescript@5 @types/node@22 @types/react@19 @types/react-dom@19 tailwindcss@4 @tailwindcss/postcss eslint@9 eslint-config-next@15 prettier vitest jsdom @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event @playwright/test`

Run: `pnpm test src/app/page.test.tsx`; expected FAIL because `page.tsx` is absent.

- [ ] **Step 3: Add configuration and minimal implementation**

Use scripts `next dev`, `next build`, `eslint . --max-warnings=0`, `tsc --noEmit`, `vitest run`, and `playwright test`. Configure `strict: true`, Tailwind import, metadata, and:

```tsx
export default function HomePage() {
  return <main><h1>Research stocks with context</h1></main>;
}
```

- [ ] **Step 4: Verify GREEN**

Run: `pnpm test src/app/page.test.tsx && pnpm lint && pnpm typecheck && pnpm build`; expected PASS without warnings.

- [ ] **Step 5: Commit**

Run: `git add package.json pnpm-lock.yaml pnpm-workspace.yaml next.config.ts tsconfig.json next-env.d.ts eslint.config.mjs .prettierrc.json .gitignore vitest.config.ts playwright.config.ts src && git commit -m "build: initialize stock research app"`

### Task 2: Domain, validation, formatting, and freshness

**Files:**
- Create: `src/domain/stock.ts`, `financials.ts`, `price-history.ts`, `fixture-schema.ts`
- Create: `src/domain/fixture-schema.test.ts`, `src/lib/format.ts`, `format.test.ts`, `market-data.ts`, `market-data.test.ts`

**Interfaces:** Produces `StockSnapshot`, `StockSearchResult`, `FinancialSeries`, `FinancialPeriod`, `PricePoint`, `PriceRange`, `fixtureStockSchema`, `normalizeSymbol`, `isStale`, and nullable formatters.

- [ ] **Step 1: Write failing boundary tests**

```ts
expect(normalizeSymbol(" amzn ")).toBe("AMZN");
expect(formatCurrency(null, "USD")).toBe("Not available");
expect(formatMultiple(42.25)).toBe("42.3×");
expect(isStale("2026-07-20T12:00:00Z", new Date("2026-07-22T12:01:00Z"), 48)).toBe(true);
expect(() => fixtureStockSchema.parse({ symbol: "AMZN", currency: "USD" })).toThrow();
```

- [ ] **Step 2: Verify RED**

Run: `pnpm test src/domain/fixture-schema.test.ts src/lib/format.test.ts src/lib/market-data.test.ts`; expected FAIL for missing modules.

- [ ] **Step 3: Implement exact contracts**

```ts
export type PriceRange = "1M" | "6M" | "1Y" | "5Y" | "MAX";
export interface StockSearchResult { symbol: string; companyName: string; exchange: string; }
export interface StockSnapshot {
  symbol: string; companyName: string; exchange: string; currency: string;
  price: number; dailyChange: number | null; dailyChangePercent: number | null;
  marketCap: number | null; enterpriseValue: number | null; peRatio: number | null;
  evToEbitda: number | null; fcfYield: number | null; source: string; asOf: string;
}
```

Validate ISO UTC datetimes, required source/currency, positive price, and annual/quarterly arrays. Implement `Intl.NumberFormat` formatters and stale when elapsed hours are strictly greater than the limit.

- [ ] **Step 4: Verify GREEN and commit**

Run: `pnpm test src/domain src/lib && pnpm typecheck`; expected PASS.

Run: `git add src/domain src/lib && git commit -m "feat: define validated market data domain"`

### Task 3: Fixture provider and AMZN data

**Files:**
- Create: `src/data/market-data-provider.ts`, `market-data-errors.ts`, `fixture-provider.ts`, `fixture-provider.test.ts`
- Create: `src/data/fixtures/amzn.json`, `search-index.json`

**Interfaces:** Produces `MarketDataProvider`, `FixtureMarketDataProvider`, and `MarketDataNotFoundError`; consumes Task 2 types and schemas.

- [ ] **Step 1: Write failing provider tests**

```ts
const provider = new FixtureMarketDataProvider();
expect(await provider.searchStocks("amazon")).toEqual([expect.objectContaining({ symbol: "AMZN" })]);
expect((await provider.getStockSnapshot(" amzn ")).symbol).toBe("AMZN");
await expect(provider.getStockSnapshot("NOPE")).rejects.toBeInstanceOf(MarketDataNotFoundError);
expect((await provider.getFinancials("AMZN")).annual).toHaveLength(3);
```

- [ ] **Step 2: Verify RED**

Run: `pnpm test src/data/fixture-provider.test.ts`; expected FAIL for missing provider.

- [ ] **Step 3: Implement fixtures and provider**

AMZN contains illustrative snapshot data, three annual periods, four quarters, price history, nullable metrics, USD, source `Illustrative fixture data`, and valid `asOf`. Search index contains AMZN/AAPL/MSFT identities. Validate before mapping; search trimmed lower-case symbol/name; normalize lookups; deduplicate and ascending-sort price timestamps.

- [ ] **Step 4: Verify GREEN and commit**

Run: `pnpm test src/data/fixture-provider.test.ts && pnpm typecheck`; expected PASS.

Run: `git add src/data && git commit -m "feat: add fixture market data provider"`

### Task 4: Search, theme, and responsive shell

**Files:**
- Create: `src/components/search/stock-search.tsx`, `stock-search.test.tsx`
- Create: `src/components/theme/theme-toggle.tsx`, `src/components/layout/app-header.tsx`, `app-footer.tsx`
- Modify: `src/app/layout.tsx`, `page.tsx`, `globals.css`

**Interfaces:** Produces `<StockSearch initialResults: StockSearchResult[] />`, theme control, header, and footer.

- [ ] **Step 1: Write failing accessible search tests**

```tsx
render(<StockSearch initialResults={[{ symbol: "AMZN", companyName: "Amazon.com, Inc.", exchange: "NASDAQ" }]} />);
await user.type(screen.getByRole("searchbox", { name: /symbol or company/i }), "amazon");
expect(screen.getByRole("link", { name: /amazon.com/i })).toHaveAttribute("href", "/stocks/AMZN");
```

Also assert exact empty copy `Enter a symbol or company name` and no-match copy `No fixture matches`.

- [ ] **Step 2: Verify RED**

Run: `pnpm test src/components/search/stock-search.test.tsx`; expected FAIL for missing component.

- [ ] **Step 3: Implement and verify GREEN**

Filter server-provided identities client-side, use accessible links, toggle root `dark` class and `localStorage.theme`, and add Home/Methodology navigation plus `Research information only — not financial advice.`

Run: `pnpm test src/components/search src/app/page.test.tsx && pnpm lint && pnpm typecheck`; expected PASS.

- [ ] **Step 4: Commit**

Run: `git add src/components src/app && git commit -m "feat: add searchable responsive app shell"`

### Task 5: AMZN detail route and states

**Files:**
- Create: `src/components/stock/stock-header.tsx`, `metric-card.tsx`, `financial-trends.tsx`, `data-provenance.tsx`, `stock-detail.test.tsx`
- Create: `src/app/stocks/[symbol]/page.tsx`, `loading.tsx`, `not-found.tsx`, `error.tsx`

**Interfaces:** Presentation components consume Task 2 objects; route consumes provider, converts not-found error to `notFound()`, and lets validation errors reach the boundary.

- [ ] **Step 1: Write failing component tests**

```tsx
render(<StockHeader snapshot={snapshot} stale />);
expect(screen.getByRole("heading", { name: /amazon.com, inc./i })).toBeInTheDocument();
expect(screen.getByText("AMZN · NASDAQ · USD")).toBeInTheDocument();
expect(screen.getByText(/stale fixture data/i)).toBeInTheDocument();
```

Assert null metric renders `Not available`; financial tables show Revenue, Operating income, Free cash flow, Margin, Diluted shares, units, annual and quarterly headings.

- [ ] **Step 2: Verify RED**

Run: `pnpm test src/components/stock/stock-detail.test.tsx`; expected FAIL for missing components.

- [ ] **Step 3: Implement route and exact states**

Load snapshot/financials concurrently and render identity/price, freshness/provenance, five market metrics, annual trends, quarterly trends, risks, and limitations. Use `<dl>` and accessible tables. Loading exposes `role=status`; not-found links home; client error boundary gives generic copy and retry.

- [ ] **Step 4: Verify GREEN and commit**

Run: `pnpm test src/components/stock src/app/stocks && pnpm lint && pnpm typecheck && pnpm build`; expected PASS.

Run: `git add src/components/stock src/app/stocks && git commit -m "feat: deliver AMZN research detail page"`

### Task 6: Methodology, E2E, CI, and final acceptance

**Files:**
- Create: `src/app/methodology/page.tsx`, `page.test.tsx`
- Create: `e2e/stock-search.spec.ts`, `stock-detail.spec.ts`, `.github/workflows/ci.yml`
- Create: `docs/architecture.md`, `docs/methodology.md`, `docs/roadmap.md`

**Interfaces:** Produces methodology route, desktop/mobile Playwright projects, project docs, and Node 22 pnpm CI.

- [ ] **Step 1: Write failing methodology and browser tests**

```ts
test("search opens AMZN", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("searchbox", { name: /symbol or company/i }).fill("Amazon");
  await page.getByRole("link", { name: /amazon.com/i }).click();
  await expect(page).toHaveURL(/\/stocks\/AMZN$/);
  await expect(page.getByRole("heading", { name: /amazon.com, inc./i })).toBeVisible();
});
```

Add mobile 390×844 coverage asserting visible price/provenance/tables and no document overflow.

- [ ] **Step 2: Verify RED**

Run: `pnpm test src/app/methodology/page.test.tsx`; expected FAIL for missing route.

- [ ] **Step 3: Implement docs and CI**

Explain illustrative fixtures, `null`, stale data, units, UTC, and research-only limits. CI job one runs install/lint/typecheck/test/build; job two installs Chromium and runs E2E.

- [ ] **Step 4: Run full acceptance**

Run: `pnpm lint && pnpm typecheck && pnpm test && pnpm exec playwright install chromium && pnpm test:e2e && pnpm build`

Expected: zero lint warnings, zero type errors, all unit/component/browser tests green, successful build.

Run: `rg -n -i "buy|sell|target price|forecast|trade|broker|api[_-]?key|secret" src public docs`; expected only research disclaimers or roadmap exclusions and no secrets.

- [ ] **Step 5: Commit**

Run: `git add src/app/methodology e2e .github docs playwright.config.ts && git commit -m "test: verify milestone 1 user journeys"`
