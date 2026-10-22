// Generates the indicator parity fixture for the Python backend (TA-Lib) tests.
// Series is deterministic (no Math.random). Indicators come from trading-signals,
// the same classes and options as apps/web/lib/indicators.ts.
// Run: pnpm -s gen:indicator-fixture
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { ATR, RSI, SMA } from "trading-signals";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "../../..");
const outPath = resolve(repoRoot, "services/api/tests/fixtures/indicator_parity.json");
const pkg = JSON.parse(
  readFileSync(resolve(here, "../node_modules/trading-signals/package.json"), "utf8"),
);

const BARS = 300;
const round4 = (x) => Math.round(x * 1e4) / 1e4;
const round6 = (x) => (x === null ? null : Math.round(x * 1e6) / 1e6);

const closes = [];
for (let i = 0; i < BARS; i++) {
  closes.push(round4(100 + 10 * Math.sin(i / 9) + 0.15 * i + 3 * Math.sin(i / 2.3)));
}

const bars = [];
for (let i = 0; i < BARS; i++) {
  const close = closes[i];
  const open = i === 0 ? close : closes[i - 1];
  const high = round4(Math.max(open, close) + 1 + 0.5 * Math.abs(Math.sin(i)));
  const low = round4(Math.min(open, close) - 1 - 0.5 * Math.abs(Math.cos(i)));
  bars.push({ open: round4(open), high, low, close });
}

const sma50 = new SMA(50);
const sma200 = new SMA(200);
const rsi14 = new RSI(14);
const atr14 = new ATR(14);

const out = { sma50: [], sma200: [], rsi14: [], atr14: [] };
for (const bar of bars) {
  const s50 = sma50.add(bar.close);
  const s200 = sma200.add(bar.close);
  const r = rsi14.add(bar.close);
  const a = atr14.add({ high: bar.high, low: bar.low, close: bar.close });
  out.sma50.push(sma50.isStable && s50 !== null ? round6(s50) : null);
  out.sma200.push(sma200.isStable && s200 !== null ? round6(s200) : null);
  out.rsi14.push(rsi14.isStable && r !== null ? round6(r) : null);
  out.atr14.push(atr14.isStable && a !== null ? round6(a) : null);
}

const fixture = {
  generator: `trading-signals ${pkg.version}`,
  bars: bars.map((b) => ({ open: b.open, high: b.high, low: b.low, close: b.close })),
  sma50: out.sma50,
  sma200: out.sma200,
  rsi14: out.rsi14,
  atr14: out.atr14,
};

writeFileSync(outPath, JSON.stringify(fixture) + "\n");
console.log(`wrote ${outPath} (${BARS} bars, generator ${fixture.generator})`);
