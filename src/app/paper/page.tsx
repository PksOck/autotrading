import { formatPercent } from "@/lib/format";
import { getMarketDataProvider } from "@/data/live";
import { parsePaperOrder } from "@/paper/orders";
import { PaperPortfolio } from "@/paper/portfolio";
import { smaCrossSignals } from "@/quant/backtest";

const DEFAULT_LIMITS = { maxPositionPct: 1, maxOrdersPerDay: 50, killSwitch: false };

/** Server-run SMA 50/200 paper demo over served MAX history (default symbol AMZN). */
export default async function PaperPage() {
  const provider = getMarketDataProvider();
  const history = await provider.getPriceHistory("AMZN", "MAX");
  const signals = smaCrossSignals(history, 50, 200);
  const portfolio = new PaperPortfolio(10_000, { commissionBps: 5, slippageBps: 5 }, DEFAULT_LIMITS);

  let position: 0 | 1 = 0;
  for (let i = 0; i < history.length; i += 1) {
    const target = signals[i];
    if (target !== position) {
      const price = history[i].close;
      if (target === 1) {
        const cash = portfolio.equity(price);
        const quantity = Math.floor(cash / price);
        if (quantity > 0) {
          portfolio.execute(parsePaperOrder({ symbol: "AMZN", side: "buy", quantity }), price);
        }
      } else {
        const held = portfolio.positionShares("AMZN");
        if (held > 0) {
          portfolio.execute(parsePaperOrder({ symbol: "AMZN", side: "sell", quantity: held }), price);
        }
      }
      position = target as 0 | 1;
    }
  }

  const lastClose = history.at(-1)!.close;
  const equity = portfolio.equity(lastClose);
  const audit = portfolio.auditLog().slice(-15);

  return (
    <main className="page-shell stock-page">
      <p className="eyebrow">Simulated fills only</p>
      <h1>Paper trading simulator</h1>
      <p className="lede">
        SMA 50/200 signals filled at served closes with commission and slippage.
        No broker, no real orders. Risk engine: full-equity cap, 50 orders/day,
        kill switch available before going further.
      </p>
      <section className="data-section">
        <div className="section-heading"><h2>Demo portfolio</h2><p>USD · AMZN</p></div>
        <p>Final equity: <strong>${equity.toFixed(2)}</strong> ({formatPercent(equity / 10_000 - 1)} total return)</p>
      </section>
      <section className="data-section">
        <h2>Audit trail (last {audit.length})</h2>
        <div className="table-wrap"><table>
          <thead><tr><th>#</th><th>Event</th><th>Detail</th></tr></thead>
          <tbody>
            {audit.map((entry) => (
              <tr key={entry.seq}><th>{entry.seq}</th><td>{entry.kind}</td><td>{entry.detail}</td></tr>
            ))}
          </tbody>
        </table></div>
        <p className="valuation-provenance">Kill switch and limits are enforced pre-trade; refusals are logged, never silent. Simulation, not advice.</p>
      </section>
    </main>
  );
}
