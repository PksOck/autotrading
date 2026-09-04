export default function MethodologyPage() {
  return (
    <main className="page-shell methodology-page">
      <p className="eyebrow">How to read the product</p>
      <h1>Methodology</h1>
      <section><h2>Data</h2><p>The current product uses illustrative fixture data rather than a live licensed market feed. Every dataset identifies its source, currency, unit, and observation time.</p></section>
      <section><h2>Missing values</h2><p>Missing values appear as Not available. They remain <code>null</code> in the data contract and are never converted to zero.</p></section>
      <section><h2>Freshness</h2><p>Observation timestamps use ISO-8601 UTC. Data older than its defined freshness window receives a visible stale label.</p></section>
      <section><h2>Valuation</h2><p>Valuation scenarios use a two-stage discounted cash flow over explicit forecast years plus a terminal value. Normalized free cash flow comes from the latest available annual figure, net debt starts at an explicit editable assumption, and every scenario is labelled an estimate — never a recommendation or target price. Inputs that fail validation refuse to estimate; extreme inputs estimate with a visible warning.</p></section>
      <section><h2>Technicals and backtests</h2><p>Indicators (SMA, EMA, RSI, MACD, Bollinger) are deterministic transforms of displayed closes with null warmup. Backtests are long/flat event simulations with commission and slippage, reported with in-sample/out-of-sample splits and walk-forward folds. A strategy counts only if it beats buy-and-hold after costs; past simulation is not a prediction.</p></section>
      <section><h2>Watchlist</h2><p>The watchlist lives only in this browser&apos;s local storage under a versioned key. It never leaves the device and can be cleared at any time from the watchlist page or browser settings.</p></section>
      <section><h2>Limits</h2><p>The figures support research and interface testing only. They are estimates, not financial advice, trading instructions, recommendations, or target prices.</p></section>
    </main>
  );
}
