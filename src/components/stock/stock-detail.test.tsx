import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSnapshot } from "@/domain/instrument";

import { FinancialTrends } from "./financial-trends";
import { MetricCard } from "./metric-card";
import { StockHeader } from "./stock-header";

const snapshot: InstrumentSnapshot = {
  symbol: "AMZN", name: "Amazon.com, Inc.", type: "stock", venue: "NASDAQ", quoteCurrency: "USD",
  price: 217.35, dailyChange: 1.2, dailyChangePercent: 0.0055,
  stockMetrics: { marketCap: 2_310_000_000_000, enterpriseValue: 2_370_000_000_000,
    peRatio: 42.25, evToEbitda: 21.5, fcfYield: null },
  source: "Illustrative fixture data", asOf: "2026-07-22T12:00:00Z",
};

const financials: FinancialSeries = {
  currency: "USD", unit: "millions", source: "Illustrative fixture data",
  asOf: "2026-07-22T12:00:00Z",
  annual: [{ period: "2025", revenue: 694200, operatingIncome: 78200, freeCashFlow: null, operatingMargin: 0.1126, dilutedShares: 10670 }],
  quarterly: [],
};

describe("stock detail presentation", () => {
  it("shows identity, currency, price, and stale status", () => {
    render(<StockHeader snapshot={snapshot} stale />);
    expect(screen.getByRole("heading", { name: /amazon.com, inc./i })).toBeInTheDocument();
    expect(screen.getByText("AMZN · NASDAQ · USD")).toBeInTheDocument();
    expect(screen.getByText("$217.35")).toBeInTheDocument();
    expect(screen.getByText(/stale fixture data/i)).toBeInTheDocument();
  });

  it("renders missing metrics explicitly", () => {
    render(<MetricCard label="FCF yield" value={null} unit="percent" currency="USD" />);
    expect(screen.getByText("Not available")).toBeInTheDocument();
  });

  it("labels financial measures and units", () => {
    render(<FinancialTrends title="Annual financials" periods={financials.annual} currency="USD" unit="millions" />);
    expect(screen.getByRole("heading", { name: "Annual financials" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Revenue" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Operating income" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Free cash flow" })).toBeInTheDocument();
    expect(screen.getByText(/USD millions/i, { selector: "p" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /revenue trend.*USD millions/i })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "Not available" })).toBeInTheDocument();
  });

  it("shows a single fundamentals capability message when financials are unavailable", () => {
    render(<FinancialTrends title="Annual financials" periods={null} currency="USD" unit="millions" />);

    expect(screen.getAllByText("Fundamentals are not available for this instrument type")).toHaveLength(1);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.queryByRole("img", { name: /trend/i })).not.toBeInTheDocument();
  });
});
