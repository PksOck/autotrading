import type { FinancialPeriod } from "@/domain/financials";
import { formatCompactNumber, formatPercent } from "@/lib/format";

export function FinancialTrends({ title, periods, currency, unit }: { title: string; periods: FinancialPeriod[]; currency: string; unit: string }) {
  return (
    <section className="data-section">
      <div className="section-heading"><h2>{title}</h2><p>{currency} {unit}</p></div>
      {periods.length === 0 ? <p>Not available</p> : (
        <div className="table-wrap"><table>
          <thead><tr><th>Period</th><th>Revenue</th><th>Operating income</th><th>Free cash flow</th><th>Margin</th><th>Diluted shares</th></tr></thead>
          <tbody>{periods.map((period) => <tr key={period.period}>
            <th>{period.period}</th><td>{formatCompactNumber(period.revenue)}</td><td>{formatCompactNumber(period.operatingIncome)}</td><td>{formatCompactNumber(period.freeCashFlow)}</td><td>{formatPercent(period.operatingMargin)}</td><td>{formatCompactNumber(period.dilutedShares)}</td>
          </tr>)}</tbody>
        </table></div>
      )}
    </section>
  );
}
