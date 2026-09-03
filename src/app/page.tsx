import { StockSearch } from "@/components/search/stock-search";
import { fixtureSearchIndex } from "@/data/fixture-provider";

export default function HomePage() {
  return (
    <main className="page-shell hero">
      <p className="eyebrow">Transparent fixture-backed analysis</p>
      <h1>Research stocks with context</h1>
      <p className="lede">
        Inspect market snapshots, financial trends, data freshness, and limitations
        before drawing conclusions.
      </p>
      <StockSearch initialResults={fixtureSearchIndex} />
      <p className="fixture-note">Full instrument detail is currently available for AMZN; AAPL and MSFT remain search-only identities.</p>
    </main>
  );
}
