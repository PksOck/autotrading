# Valuation and Watchlist Milestone 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministic two-stage DCF scenarios with editable assumptions plus a localStorage watchlist, following the Milestone 3 design spec.

**Architecture:** Pure domain math in `domain/valuation.ts` (Zod-validated), a state-holding client `ValuationSection` composing a pure `ValuationForm` and a pure `ValuationResult`, guarded storage helpers in `lib/watchlist-storage.ts`, a client `WatchlistButton`, a client `/watchlist` page, and vendor-neutral contract assertions in `data/provider-contract.ts`.

**Tech Stack:** Node.js 22 LTS, Next.js 15, React 19, strict TypeScript, Tailwind CSS 4, Zod, Vitest, React Testing Library, Playwright.

## Global Constraints

- Missing values stay `null` and render as unavailable; never zero-filled.
- Every estimate is labelled as an estimate, never a recommendation or target.
- Terminal growth must stay below the discount rate; dangerous inputs refuse.
- Currency, unit, source, and freshness remain visible.
- No live providers, auth, forecasting, backtesting, brokers, or execution.

---

### Task 1: DCF domain with hand-verified math

**Files:**
- Create: `src/domain/valuation.ts`, `src/domain/valuation.test.ts`

**Interfaces:**
- Produces `ValuationAssumptions`, `ValuationBreakdown`, `ValuationScenario`, `VALUATION_SCENARIOS`, `validateValuationAssumptions(a)` returning `{ errors: string[]; warnings: string[] }`, and `calculateDcfValue(a)` returning `ValuationBreakdown` (precondition: no validation errors).

- [ ] **Step 1: Write failing domain tests**

```ts
const base = { normalizedFcf: 100, growthRate: 0.1, explicitYears: 3, terminalGrowthRate: 0.02, discountRate: 0.1, netDebt: 50, dilutedShares: 10 };
expect(calculateDcfValue(base)).toMatchObject({ explicitPeriodValue: 300, terminalValuePresentValue: 1275, enterpriseValue: 1575, equityValue: 1525, perShareValue: 152.5 });
expect(validateValuationAssumptions({ ...base, terminalGrowthRate: 0.1 }).errors).not.toHaveLength(0);
expect(validateValuationAssumptions({ ...base, growthRate: 0.2 }).warnings).not.toHaveLength(0);
expect(VALUATION_SCENARIOS.every((s) => s.assumptions.terminalGrowthRate < s.assumptions.discountRate)).toBe(true);
```

Use `toBeCloseTo` for float fields. Cover every blocking error and every warning threshold from the spec.

- [ ] **Step 2: Run RED**

Run: `.\node_modules\.bin\vitest.cmd run src/domain/valuation.test.ts` (or `pnpm test src/domain/valuation.test.ts` where pnpm exists)

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement pure DCF math and Zod validation**

Two-stage projection with yearly discounting; Zod schema plus cross-field `superRefine` for terminal < discount; warnings as documented thresholds.

- [ ] **Step 4: Run GREEN**

Run: unit test for the file plus `tsc --noEmit` and `eslint` on changed files.

Expected: PASS with zero warnings.

### Task 2: Watchlist storage boundary

**Files:**
- Create: `src/lib/watchlist-storage.ts`, `src/lib/watchlist-storage.test.ts`

**Interfaces:**
- Produces `WATCHLIST_STORAGE_KEY`, `parseWatchlist(value: unknown): string[]`, `toggleWatchlistSymbol(symbols: string[], symbol: string): string[]`, `isWatchlisted(symbols, symbol)`, `loadWatchlist(): string[]`, `saveWatchlist(symbols): void`.

- [ ] **Step 1: Write failing storage tests**

```ts
expect(parseWatchlist([" amzn ", "AMZN", 42])).toEqual(["AMZN"]);
expect(parseWatchlist({ nope: true })).toEqual([]);
expect(toggleWatchlistSymbol([], "amzn")).toEqual(["AMZN"]);
expect(toggleWatchlistSymbol(["AMZN"], "amzn")).toEqual([]);
```

Cover corrupt JSON, missing `window`/`localStorage`, and quota-throwing `setItem`.

- [ ] **Step 2: Run RED**

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement guarded storage helpers**

Zod `z.array(z.string())` parsing with trim/uppercase normalize and dedupe; try/catch around every `localStorage` touch.

- [ ] **Step 4: Run GREEN**

Expected: PASS, typecheck and lint clean.

### Task 3: Valuation UI on the instrument page

**Files:**
- Create: `src/components/valuation/valuation-form.tsx`, `valuation-result.tsx`, `valuation-section.tsx`, `valuation-section.test.tsx`
- Modify: `src/app/instruments/[symbol]/page.tsx`, `src/app/globals.css`

**Interfaces:**
- Produces `ValuationSection({ currency, unit, latestFcf: { value: number; period: string } | null, dilutedShares: number | null })`.
- Server page derives `latestFcf` from the newest annual period with non-null FCF and passes fixture currency/unit.

- [ ] **Step 1: Write failing component tests**

```tsx
render(<ValuationSection currency="USD" unit="millions" latestFcf={{ value: 38219, period: "2024" }} dilutedShares={10670} />);
await user.click(screen.getByRole("button", { name: /optimistic/i }));
expect(screen.getByText(/estimate.*not a recommendation/i)).toBeInTheDocument();
```

Cover scenario switching recompute, terminal>=discount refusal, warning display, and the single unavailable message when `latestFcf` is null.

- [ ] **Step 2: Run RED**

Expected: FAIL because the components do not exist.

- [ ] **Step 3: Implement form, result, and section**

Native number inputs with labels, scenario preset buttons with `aria-pressed`, textual breakdown with currency, per-share value, assumption provenance ("Normalized FCF 38,219 USD millions, 2024 annual; net debt assumed 0 — edit below").

- [ ] **Step 4: Run GREEN**

Expected: PASS, lint/typecheck clean, instrument route renders the section.

### Task 4: Watchlist UI and page

**Files:**
- Create: `src/components/watchlist/watchlist-button.tsx`, `watchlist-button.test.tsx`, `src/app/watchlist/page.tsx`, `src/app/watchlist/page.test.tsx`
- Modify: `src/components/layout/app-header.tsx`, `src/app/instruments/[symbol]/page.tsx`, `src/app/page.tsx` (fixture-note copy: only AMZN has full detail)

**Interfaces:**
- Produces `WatchlistButton({ symbol })` and the `/watchlist` route.

- [ ] **Step 1: Write failing component tests**

```tsx
render(<WatchlistButton symbol="AMZN" />);
expect(screen.getByRole("button", { name: /add amzn to watchlist/i })).toHaveAttribute("aria-pressed", "false");
```

Cover toggle persistence across remount, empty watchlist page, populated page with canonical links, and removal.

- [ ] **Step 2: Run RED**

Expected: FAIL because the components/route do not exist.

- [ ] **Step 3: Implement button, page, header link, and page integration**

Join stored symbols with `fixtureSearchIndex`; unknown symbols show stored symbol plus "detail not available".

- [ ] **Step 4: Run GREEN**

Expected: PASS, lint/typecheck clean.

### Task 5: Provider contract suite (Milestone 4 groundwork)

**Files:**
- Create: `src/data/provider-contract.ts`
- Modify: `src/data/fixture-provider.test.ts`

**Interfaces:**
- Produces `assertMarketDataContract(provider, { supportedSymbol, unsupportedSymbol })` as plain async assertions reusable by any future provider.

- [ ] **Step 1: Write the contract as failing-against-nothing new tests**

Wire the contract into `fixture-provider.test.ts`; it must pass on the fixture provider immediately (contract codifies existing rules).

- [ ] **Step 2: Run GREEN**

Expected: PASS; future providers import the same function.

### Task 6: Production hardening without pending decisions

**Files:**
- Modify: `src/app/layout.tsx` (title template + description), `next.config.ts` (security headers)
- Create: `src/app/robots.ts`, `src/app/sitemap.ts`
- Modify: `src/app/methodology/page.tsx` + `page.test.tsx` (valuation + watchlist sections)
- Modify: `docs/architecture.md`, `docs/methodology.md`, `docs/roadmap.md`

- [ ] **Step 1: Implement metadata, robots, sitemap, headers**

Static sitemap entries: `/`, `/methodology`, `/watchlist`, `/instruments/AMZN`. Headers: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: SAMEORIGIN`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`.

- [ ] **Step 2: Run GREEN**

`lint && typecheck && test && build` pass; headers visible in `next build` output route config (verify via `next start` response headers manually if time permits).

### Task 7: E2E and final verification

**Files:**
- Create: `e2e/valuation-watchlist.spec.ts`

- [ ] **Step 1: Write browser expectations**

Scenario switch recomputes the estimate; terminal growth >= discount refuses; watchlist toggle persists across reload; `/watchlist` lists and removes AMZN.

- [ ] **Step 2: Run RED**

Expected: FAIL before Tasks 3-4 integration is complete; after, PASS.

- [ ] **Step 3: Run complete verification**

Run: `lint && typecheck && test && test:e2e && build && git diff --check`

Expected: zero lint warnings, zero type errors, all tests PASS, successful production build, no whitespace errors.

- [ ] **Step 4: Commit**

Run: `git add <changed paths> && git commit -m "feat: add DCF scenarios and local watchlist"` plus docs commit if separate.
