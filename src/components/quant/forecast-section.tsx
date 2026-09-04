import { formatPercent } from "@/lib/format";
import { beatsNaive, evaluateForecast, linRegPredict, naiveLast, smaPredict } from "@/quant/forecast";

function fmt(value: number | null, digits = 3): string {
  if (value === null || !Number.isFinite(value)) return "Not available";
  return value.toFixed(digits);
}

export function ForecastSection({ closes, currency }: { closes: number[]; currency: string }) {
  const naive = evaluateForecast(closes, naiveLast);
  if (!naive || naive.predictions < 30) {
    return (
      <section className="data-section">
        <h2>Next-close forecast</h2>
        <p>Forecast is not available for this history length</p>
      </section>
    );
  }

  const rows = [
    { label: "Naive last", evaluation: naive, next: naiveLast(closes, closes.length - 1) },
    { label: "SMA 5", evaluation: evaluateForecast(closes, smaPredict(5)), next: smaPredict(5)(closes, closes.length - 1) },
    { label: "LinReg 20", evaluation: evaluateForecast(closes, linRegPredict(20)), next: linRegPredict(20)(closes, closes.length - 1) },
  ];
  const promoted = rows.filter((row) => beatsNaive(row.evaluation, naive));

  return (
    <section className="data-section">
      <div className="section-heading"><h2>Next-close forecast</h2><p>Walk-forward · {currency}</p></div>
      <div className="table-wrap"><table>
        <thead><tr><th>Baseline</th><th>Next close</th><th>MAE</th><th>RMSE</th><th>Direction</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th>{row.label}</th>
              <td>{row.next === null ? "Not available" : row.next.toFixed(2)}</td>
              <td>{fmt(row.evaluation?.mae ?? null)}</td>
              <td>{fmt(row.evaluation?.rmse ?? null)}</td>
              <td>{row.evaluation?.directionalAccuracy === null || row.evaluation?.directionalAccuracy === undefined ? "Not available" : formatPercent(row.evaluation.directionalAccuracy)}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
      <p className="valuation-provenance">
        {promoted.length > 0
          ? `Promoted vs naive: ${promoted.map((row) => row.label).join(", ")}.`
          : "No baseline beats naive persistence on this history."}{" "}
        Simulation for research, not advice or a trading signal.
      </p>
    </section>
  );
}
