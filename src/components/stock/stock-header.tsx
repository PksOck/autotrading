import type { InstrumentSnapshot } from "@/domain/instrument";
import { formatCurrency, formatPercent } from "@/lib/format";

import { FreshnessStatus } from "./freshness-status";

export function StockHeader({ snapshot }: { snapshot: InstrumentSnapshot }) {
  return (
    <header className="stock-header">
      <div>
        <p className="eyebrow">{snapshot.symbol} · {snapshot.venue} · {snapshot.quoteCurrency}</p>
        <h1>{snapshot.name}</h1>
      </div>
      <div className="price-block">
        <strong>{formatCurrency(snapshot.price, snapshot.quoteCurrency)}</strong>
        <span>{formatCurrency(snapshot.dailyChange, snapshot.quoteCurrency)} · {formatPercent(snapshot.dailyChangePercent)}</span>
        <FreshnessStatus asOf={snapshot.asOf} />
      </div>
    </header>
  );
}
