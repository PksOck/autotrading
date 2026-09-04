# Forecasting Baselines + Paper Simulator Milestone 6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministic next-close baselines with promotion rules plus a paper simulator with risk engine, following the Milestone 6 design spec.

**Architecture:** Pure quant functions in `src/quant/features.ts` and `src/quant/forecast.ts`; paper domain in `src/paper/` (orders, risk, portfolio); server-computed `ForecastSection` on the instrument page; server-run `/paper` demo route over served history.

**Tech Stack:** Node.js 22 LTS, Next.js 15, React 19, strict TypeScript, Zod, Vitest, React Testing Library, Playwright.

## Global Constraints

- No future-bar reads; warmup is null, never zero.
- Every forecast/fill labelled simulation, never advice.
- No live brokers, no real routing, no shorts/leverage in v1.
- No new runtime ML dependencies.

---

### Task 1: Feature builder

**Files:**
- Create: `src/quant/features.ts`, `src/quant/features.test.ts`

**Interfaces:**
- Produces `buildFeatures(closes, index)` returning `{ r1, r5, distSma20, distSma50, rsi14, vol20 }` with null warmup.

- [ ] **Step 1: Write failing feature tests**

```ts
const closes = [100, 101, 102, 103, 104, 105];
expect(buildFeatures(closes, 1)?.r1).toBeCloseTo(0.01, 8);
expect(buildFeatures(closes, 0)).toBeNull();
```

Cover r5 warmup (< 5 bars), SMA distance nulls, RSI/vol warmup.

- [ ] **Step 2: Run RED**

Run: `vitest run src/quant/features.test.ts`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement pure feature math**

Lagged returns, SMA distances via `sma`, RSI via `rsi`, realized vol as
stdev of last-20 simple returns. Index-only reads `closes[0..index]`.

- [ ] **Step 4: Run GREEN**

Expected: PASS, typecheck and lint clean.

### Task 2: Forecast baselines + evaluation

**Files:**
- Create: `src/quant/forecast.ts`, `src/quant/forecast.test.ts`

**Interfaces:**
- Produces `naiveLast`, `smaPredict(n)`, `linRegPredict(window)`,
  `wrapChallenger(fn)`, `evaluateForecast(closes, fn)`, `beatsNaive(eval, naiveEval)`.

- [ ] **Step 1: Write failing forecast tests**

```ts
expect(naiveLast([1, 2, 3], 2)).toBe(3);
expect(linRegPredict(3)([10, 20, 30], 2)).toBeCloseTo(40, 6);
const ev = evaluateForecast([100, 101, 102, 103], naiveLast);
expect(ev?.predictions).toBe(3);
```

Cover OLS exactness on linear series, MAE/RMSE/DA hand values,
promotion boundaries (predictions < 30 never promotes).

- [ ] **Step 2: Run RED**

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement predictors and metrics**

OLS closed-form on last-`window` points; DA compares predicted vs
realized direction; `beatsNaive` requires lower MAE, DA > 0.5, n >= 30.

- [ ] **Step 4: Run GREEN**

Expected: PASS, typecheck and lint clean.

### Task 3: Paper domain (orders, risk, portfolio)

**Files:**
- Create: `src/paper/orders.ts`, `orders.test.ts`, `src/paper/risk.ts`,
  `risk.test.ts`, `src/paper/portfolio.ts`, `portfolio.test.ts`

**Interfaces:**
- Produces `parsePaperOrder`, `checkOrder(state, order, equity, price)`,
  `PaperPortfolio` with `execute` + `audit` + `positions`.

- [ ] **Step 1: Write failing paper tests**

```ts
expect(() => parsePaperOrder({ quantity: 0 })).toThrow();
expect(checkOrder({ killSwitch: true, ... }, order, 10000, 100).ok).toBe(false);
```

Cover duplicate idempotency rejection, position cap, daily cap,
limit-touch fills, audit sequencing.

- [ ] **Step 2: Run RED**

Expected: FAIL because the modules do not exist.

- [ ] **Step 3: Implement Zod orders, risk checks, portfolio fills**

Market fills at bar close with commission/slippage; no shorts.

- [ ] **Step 4: Run GREEN**

Expected: PASS, typecheck and lint clean.

### Task 4: Forecast UI + /paper demo route

**Files:**
- Create: `src/components/quant/forecast-section.tsx`, `forecast-section.test.tsx`
- Create: `src/app/paper/page.tsx`, `page.test.tsx`
- Modify: `src/app/instruments/[symbol]/page.tsx`, `src/app/globals.css`

**Interfaces:**
- Produces `ForecastSection({ closes, currency })` and the `/paper` route.

- [ ] **Step 1: Write failing component tests**

Cover baseline table values, promoted/not-beats label, paper audit
rendering and kill-switch copy.

- [ ] **Step 2: Run RED**

Expected: FAIL because the components/route do not exist.

- [ ] **Step 3: Implement section, route, header link, styles**

Server computes evaluation over served MAX history; `/paper` runs the
SMA 50/200 paper run through `PaperPortfolio` with default limits.

- [ ] **Step 4: Run GREEN**

Expected: PASS, lint/typecheck clean.

### Task 5: E2E, docs, final verification

**Files:**
- Create: `e2e/forecast-paper.spec.ts`
- Modify: `docs/architecture.md`, `docs/methodology.md`, `docs/roadmap.md`,
  `src/app/methodology/page.tsx`, `next.config.ts` if needed

- [ ] **Step 1: Write browser expectations**

Forecast section visible with baselines; `/paper` shows audit + risk copy.

- [ ] **Step 2: Run RED**

Expected: FAIL before Task 4 integration; after, PASS.

- [ ] **Step 3: Run complete verification**

Run: `lint && typecheck && test && test:e2e && build && git diff --check`

Expected: zero warnings/errors, all tests PASS, successful build.

- [ ] **Step 4: Commit**

Run: `git add <changed paths> && git commit -m "feat: add forecast baselines and paper simulator"`
