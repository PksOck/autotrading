import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { FinancialPeriod } from "@/domain/financials";

import { FinancialTrendChart } from "./financial-trend-chart";

const periods: FinancialPeriod[] = [
  { period: "2023", revenue: 574785, operatingIncome: 36852, freeCashFlow: 36813, operatingMargin: 0.0641, dilutedShares: 10492 },
  { period: "2024", revenue: 637959, operatingIncome: 68593, freeCashFlow: 38219, operatingMargin: 0.1075, dilutedShares: 10608 },
  { period: "2025", revenue: 694200, operatingIncome: 78200, freeCashFlow: null, operatingMargin: 0.1126, dilutedShares: 10670 },
];

describe("FinancialTrendChart", () => {
  it("labels nullable financial observations as gaps instead of zero", () => {
    render(
      <FinancialTrendChart
        periods={periods}
        metric="freeCashFlow"
        label="Free cash flow"
        currency="USD"
        unit="millions"
      />,
    );

    const chart = screen.getByRole("img", { name: /free cash flow trend.*USD millions/i });
    expect(chart).toHaveAccessibleDescription(/2023: 36\.81K USD millions.*2024: 38\.22K USD millions.*2025: Not available \(gap\)/);
    expect(screen.getByText("Not available")).toBeInTheDocument();
    expect(screen.queryByText("0", { exact: true })).not.toBeInTheDocument();
  });
});
