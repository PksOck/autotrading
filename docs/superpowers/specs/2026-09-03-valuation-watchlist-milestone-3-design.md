# Valuation and Watchlist — Milestone 3 Design

**Date:** 2026-09-03

## Goal

Add deterministic two-stage DCF scenarios and a local watchlist to the
instrument research page. AMZN remains the only complete fixture; valuation
inputs are derived from fixture financials and every assumption stays
user-visible and editable.

## Scope

Milestone 3 includes a pure DCF domain module with Zod validation, three
scenario presets (conservative, base, optimistic), an editable assumption
form with blocking errors and non-blocking extreme-value warnings, a
presentational result with an explicit estimate label, `localStorage`
watchlist storage with a toggle button and a `/watchlist` page, and
provider contract tests that any future licensed provider must satisfy.

It does not include live providers, caching/retries against real APIs,
authentication, user databases, backtesting, forecasting, brokers, or
execution.

## Valuation Domain

```ts
export interface ValuationAssumptions {
  normalizedFcf: number;
  growthRate: number;
  explicitYears: number;
  terminalGrowthRate: number;
  discountRate: number;
  netDebt: number;
  dilutedShares: number;
}

export interface ValuationBreakdown {
  explicitPeriodValue: number;
  terminalValuePresentValue: number;
  enterpriseValue: number;
  equityValue: number;
  perShareValue: number;
}
```

Math is a standard two-stage DCF: project
`FCF_t = normalizedFcf * (1 + growthRate)^t`, discount each year at
`discountRate`, terminal value
`TV = FCF_N * (1 + terminalGrowthRate) / (discountRate - terminalGrowthRate)`
discounted to present, `EV = explicit + terminal PV`,
`equity = EV - netDebt`, `perShare = equity / dilutedShares`.

Blocking errors (calculation refused): non-finite inputs, `discountRate <= 0`,
`dilutedShares <= 0`, `explicitYears` not an integer in 1..20,
`terminalGrowthRate >= discountRate`. Extreme-value warnings (calculation
allowed): growth above 15%, discount below 6% or above 20%, terminal growth
above 4%, explicit horizon above 10 years.

The result is labelled "Estimate — not a recommendation or target price".

Scenario presets (growth, years, terminal, discount):

- conservative: 4%, 5y, 1.5%, 12%
- base: 8%, 5y, 2%, 10%
- optimistic: 12%, 5y, 2.5%, 9%

`normalizedFcf`, `netDebt`, and `dilutedShares` are per-instrument, not part
of presets. Prefill: latest annual FCF that is not `null` (fixture unit,
period shown), latest annual diluted shares, `netDebt` defaults to 0 and is
labelled as an assumption to edit. When FCF or shares are unavailable, the
section renders one "Valuation not available" message instead of inputs.

## Watchlist

`lib/watchlist-storage.ts` owns the storage key
`northstar-research:watchlist:v1`, Zod parsing with `[]` fallback, a pure
`toggleWatchlistSymbol` helper, and guarded `localStorage` access (safe
without `window`, tolerant of corrupt JSON). `WatchlistButton` is a client
toggle with `aria-pressed`. `/watchlist` is a client page joining stored
symbols with the fixture search index; unknown symbols render the stored
symbol with a "detail not available" note. Header gains a Watchlist link;
the instrument page gains the toggle next to the header.

## Provider Contract (Milestone 4 groundwork, vendor-neutral)

`data/provider-contract.ts` exports plain assertion helpers covering the
data rules every provider must satisfy: ISO-8601 UTC timestamps, required
currency, `null`-not-zero missing values, `source` + `asOf` presence, unique
ascending price points at or before snapshot `asOf`, unknown-symbol typed
error. `fixture-provider.test.ts` runs the contract against the fixture
provider; a future licensed provider reuses the same suite.

## Seams under test

- `domain/valuation.ts` pure functions (`validateValuationAssumptions`,
  `calculateDcfValue`, `VALUATION_SCENARIOS`).
- `lib/watchlist-storage.ts` pure helpers + guarded storage boundary.
- `ValuationResult` rendering, `ValuationForm` error/warning behaviour,
  `ValuationSection` scenario switching and unavailable state.
- `WatchlistButton` toggle + persistence, `/watchlist` empty/populated
  states.
- Provider contract assertions against the fixture provider.

## Testing

Vitest covers DCF hand-verified literals (100 FCF, 10% growth, 3 years, 2%
terminal, 10% discount gives explicit PV 300, terminal PV 1275, EV 1575,
equity 1525 with net debt 50, per-share 152.5 over 10 shares), every
blocking error, every warning threshold, scenario preset invariants
(terminal < discount), storage parsing/toggling, and component behaviour.
Playwright covers scenario switching with recomputed estimates, invalid
input refusal, watchlist add/persist/remove, and the watchlist page.

Quality gates remain `lint`, `typecheck`, `test`, `test:e2e`, `build`.

## Acceptance Criteria

- AMZN page shows three DCF scenarios with editable assumptions.
- Dangerous inputs are refused with messages; extreme inputs warn.
- Every estimate carries the non-recommendation label plus currency/unit.
- Missing FCF or shares shows one unavailable message, never zero-filled.
- Watchlist survives reload; header, toggle, and page stay consistent.
- Provider contract passes on the fixture provider.
- Lint, strict typecheck, unit/component tests, desktop/mobile Playwright
  tests, and production build pass.

## Deferred Work

Licensed provider selection, server-side secrets, caching, and retries stay
Milestone 4. ETF/crypto/commodity fixtures stay deferred. Forecasting,
backtesting, brokers, and execution remain separate future systems.
