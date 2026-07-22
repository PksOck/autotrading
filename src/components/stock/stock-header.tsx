import type { InstrumentSnapshot } from "@/domain/instrument";
import { formatCurrency, formatPercent } from "@/lib/format";

export function StockHeader({ snapshot, stale }: { snapshot: InstrumentSnapshot; stale: boolean }) {
  return (
    <header className="stock-header">
      <div>
        <p className="eyebrow">{snapshot.symbol} · {snapshot.venue} · {snapshot.quoteCurrency}</p>
        <h1>{snapshot.name}</h1>
      </div>
      <div className="price-block">
        <strong>{formatCurrency(snapshot.price, snapshot.quoteCurrency)}</strong>
        <span>{formatCurrency(snapshot.dailyChange, snapshot.quoteCurrency)} · {formatPercent(snapshot.dailyChangePercent)}</span>
        {stale ? <span className="status stale">Stale fixture data</span> : <span className="status">Fixture current</span>}
      </div>
    </header>
  );
}
