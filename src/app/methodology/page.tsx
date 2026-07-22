export default function MethodologyPage() {
  return (
    <main className="page-shell methodology-page">
      <p className="eyebrow">How to read the product</p>
      <h1>Methodology</h1>
      <section><h2>Data</h2><p>The current product uses illustrative fixture data rather than a live licensed market feed. Every dataset identifies its source, currency, unit, and observation time.</p></section>
      <section><h2>Missing values</h2><p>Missing values appear as Not available. They remain <code>null</code> in the data contract and are never converted to zero.</p></section>
      <section><h2>Freshness</h2><p>Observation timestamps use ISO-8601 UTC. Data older than its defined freshness window receives a visible stale label.</p></section>
      <section><h2>Limits</h2><p>The figures support research and interface testing only. They are estimates, not financial advice, trading instructions, recommendations, or target prices.</p></section>
    </main>
  );
}
