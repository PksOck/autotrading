export default function Loading() {
  return (
    <main className="page-shell stock-page">
      <section className="data-section price-history" aria-labelledby="loading-price-history-heading">
        <h2 id="loading-price-history-heading">Price history</h2>
        <div
          aria-label="Loading price history"
          className="chart-frame chart-loading"
          data-testid="price-volume-chart-frame"
          role="status"
        >
          Loading price history…
        </div>
      </section>
    </main>
  );
}
