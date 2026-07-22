import type { StockSnapshot } from "@/domain/stock";
import { formatCurrency, formatPercent } from "@/lib/format";

export function StockHeader({ snapshot, stale }: { snapshot: StockSnapshot; stale: boolean }) {
  return (
    <header className="stock-header">
      <div>
        <p className="eyebrow">{snapshot.symbol} · {snapshot.exchange} · {snapshot.currency}</p>
        <h1>{snapshot.companyName}</h1>
      </div>
      <div className="price-block">
        <strong>{formatCurrency(snapshot.price, snapshot.currency)}</strong>
        <span>{formatCurrency(snapshot.dailyChange, snapshot.currency)} · {formatPercent(snapshot.dailyChangePercent)}</span>
        {stale ? <span className="status stale">Stale fixture data</span> : <span className="status">Fixture current</span>}
      </div>
    </header>
  );
}
