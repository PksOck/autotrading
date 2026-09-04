import { formatPercent } from "@/lib/format";
import type { StrategyComparison, TechnicalSummary } from "@/quant/research";

function fmt(value: number | null, digits = 2): string {
  if (value === null || !Number.isFinite(value)) return "Not available";
  return value.toFixed(digits);
}

export function TechnicalsSection({ summary, currency }: { summary: TechnicalSummary; currency: string }) {
  const rows: [string, string][] = [
    ["SMA 50", summary.sma50 === null ? "Not available" : `${fmt(summary.sma50)} ${currency}`],
    ["SMA 200", summary.sma200 === null ? "Not available" : `${fmt(summary.sma200)} ${currency}`],
    ["EMA 12 / 26", summary.ema12 === null || summary.ema26 === null ? "Not available" : `${fmt(summary.ema12)} / ${fmt(summary.ema26)} ${currency}`],
    ["RSI 14", summary.rsi14 === null ? "Not available" : fmt(summary.rsi14)],
  ];
  return (
    <section className="data-section">
      <div className="section-heading"><h2>Technicals</h2><p>Deterministic · {currency}</p></div>
      <div className="table-wrap"><table>
        <thead><tr><th>Indicator</th><th>Last value</th></tr></thead>
        <tbody>{rows.map(([label, value]) => <tr key={label}><th>{label}</th><td>{value}</td></tr>)}</tbody>
      </table></div>
      <p className="valuation-provenance">Computed from displayed price history only. Research context, not a signal.</p>
    </section>
  );
}

export function BacktestSection({ comparison }: { comparison: StrategyComparison }) {
  return (
    <section className="data-section">
      <div className="section-heading"><h2>Strategy backtest</h2><p>Costs included · long/flat</p></div>
      <div className="table-wrap"><table>
        <thead><tr><th>Strategy</th><th>Total return</th><th>Max drawdown</th><th>Sharpe</th><th>Trades</th></tr></thead>
        <tbody>
          <tr><th>Buy and hold</th><td>{formatPercent(comparison.buyHold.totalReturn)}</td><td>{formatPercent(comparison.buyHold.maxDrawdown)}</td><td>{fmt(comparison.buyHold.sharpe)}</td><td>1</td></tr>
          <tr><th>SMA 50/200 cross</th><td>{formatPercent(comparison.smaCross.totalReturn)}</td><td>{formatPercent(comparison.smaCross.maxDrawdown)}</td><td>{fmt(comparison.smaCross.sharpe)}</td><td>{comparison.smaCross.trades}</td></tr>
        </tbody>
      </table></div>
      <p className="valuation-provenance">
        Out-of-sample (last 30%): {formatPercent(comparison.outOfSample.totalReturn)} · Sharpe {fmt(comparison.outOfSample.sharpe)} ·{" "}
        Walk-forward folds: {comparison.walkForwardFolds} · median fold return {formatPercent(comparison.walkForwardMedianReturn)}.
        Historical simulation, not a prediction or recommendation.
      </p>
    </section>
  );
}
