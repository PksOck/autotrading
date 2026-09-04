# Forecasting Baselines + Paper Simulator — Milestone 6 Design

**Date:** 2026-09-04

## Goal

Add the next boundary after the quant research core: deterministic
next-close forecasting baselines and a paper-trading simulator with a risk
engine. No live execution, no broker keys, no external ML dependencies.
LightGBM / TimesFM / Chronos remain challenger interfaces, not implementations.

## Scope

Milestone 6 includes a pure feature builder (`src/quant/features.ts`), three
baseline predictors plus a challenger-adapter interface (`src/quant/forecast.ts`),
walk-forward forecast evaluation with promotion rules, a paper domain
(`src/paper/orders.ts`, `portfolio.ts`, `risk.ts`) with idempotency keys,
kill switch, position limits and audit log, a Forecast section on the
instrument page, a `/paper` demo route running the SMA-cross paper run on
served history, and methodology/roadmap updates.

It does not include live brokers, real order routing, model training
infrastructure, Python services, or any buy/sell recommendation. Forecasts
and fills are labelled simulations.

## Forecast Domain

```ts
export type PredictFn = (closes: number[], index: number) => number | null;
export interface ForecastEvaluation {
  mae: number | null; rmse: number | null;
  directionalAccuracy: number | null; predictions: number;
}
```

Predictors (all use closes[0..index] only):

- naiveLast: predicts closes[index] (persistence baseline).
- smaPredict(n): predicts SMA-n of closes[0..index].
- linRegPredict(window): OLS on last `window` closes, extrapolates one step.
- challengerAdapter: `wrapChallenger(fn) -> PredictFn`, so a future
  LightGBM/TimesFM HTTP service plugs in without changing evaluation.

Evaluation (`evaluateForecast(history, fn)`): walk over i in
[warmup..n-2], compare predict(i) vs closes[i+1]. Metrics: MAE, RMSE,
directional accuracy (sign of predicted change vs realized change).
Promotion rule (`beatsNaive`): challenger counts as promoted only if
MAE < naive MAE **and** directional accuracy > 0.5 **and** predictions >= 30.
Otherwise the UI shows "does not beat naive baselines".

Features (`buildFeatures(closes, index)`): lagged returns r1/r5, distance
to SMA20/SMA50, RSI14, realized volatility 20d. All nullable during warmup.
Features are documentation for the future ML service, not consumed by the
baselines (baselines stay closed-form so tests stay hand-verifiable).

## Paper Domain

```ts
export interface PaperOrder { idempotencyKey: string; symbol: string; side: "buy" | "sell"; quantity: number; limitPrice: number | null; }
export interface RiskLimits { maxPositionPct: number; maxOrdersPerDay: number; killSwitch: boolean; }
export interface AuditEntry { seq: number; timestamp: string; kind: string; detail: string; }
```

Rules:

- Orders validate with Zod: quantity > 0 finite, side enum, idempotency key
  non-empty. Duplicate idempotency keys are rejected, never double-filled.
- Risk engine (`checkOrder`): refuses when killSwitch is on, when notional
  exceeds maxPositionPct of equity, or when daily order count exceeds
  maxOrdersPerDay. Refusals carry reasons, never silent.
- Portfolio (`PaperPortfolio`): cash + positions map, `execute` fills market
  orders at bar close with commission/slippage, appends audit entries with
  sequence numbers. Limit orders fill only when touched. No shorting, no
  leverage in v1.
- `/paper` demo: server runs SMA 50/200 signals over served MAX history
  through the paper portfolio with default limits, renders equity, trades,
  audit tail, and risk configuration. Fixture data keeps it deterministic.

## Seams under test

- `quant/features.ts` warmup nulls and hand-computed lag values.
- `quant/forecast.ts` predictors on linear series, OLS exactness,
  evaluation metrics on known arrays, promotion rule boundaries.
- `paper/orders.ts` Zod accept/reject + idempotency duplicates.
- `paper/risk.ts` kill switch, position cap, daily cap with reasons.
- `paper/portfolio.ts` cash/share math with costs, limit-order touch
  logic, audit sequencing.
- Forecast section rendering + `/paper` empty/audit states.

## Testing

Vitest covers every predictor, metric, rule boundary, and risk refusal.
React Testing Library covers the forecast table and paper audit rendering.
Playwright covers the instrument forecast section and the `/paper` demo
route (desktop + mobile, reused server).

Quality gates remain `lint`, `typecheck`, `test`, `test:e2e`, `build`
(plus `docker build` for the standalone image).

## Acceptance Criteria

- Instrument page shows next-close baselines with MAE/RMSE/DA and an
  explicit "does not beat naive" or promoted label.
- No predictor reads future bars; warmup is null, never zero.
- Paper demo fills only at served closes with costs, respects kill switch
  and limits, and keeps a sequenced audit log.
- Every forecast/fill carries the simulation-not-advice label.
- Lint, strict typecheck, unit/component tests, Playwright tests, and
  production build pass.

## Deferred Work

Model training pipelines, Python services, LightGBM/TimesFM weights,
broker adapters, real order routing, options/futures/forex.
