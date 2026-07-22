import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { InstrumentSnapshot } from "@/domain/instrument";

const providerMethods = vi.hoisted(() => ({
  getInstrumentSnapshot: vi.fn(),
  getFinancials: vi.fn(),
  getPriceHistory: vi.fn(),
}));

vi.mock("@/data/fixture-provider", () => ({
  FixtureMarketDataProvider: class {
    getInstrumentSnapshot = providerMethods.getInstrumentSnapshot;
    getFinancials = providerMethods.getFinancials;
    getPriceHistory = providerMethods.getPriceHistory;
  },
}));

vi.mock("next/navigation", () => ({ notFound: vi.fn() }));

import InstrumentPage from "./page";

const snapshot: InstrumentSnapshot = {
  symbol: "BTC", name: "Bitcoin", type: "crypto", venue: "CRYPTO", quoteCurrency: "USD",
  price: 100_000, dailyChange: null, dailyChangePercent: null, stockMetrics: null,
  source: "Illustrative fixture data", asOf: "2026-07-22T12:00:00Z",
};

describe("InstrumentPage", () => {
  beforeEach(() => {
    providerMethods.getInstrumentSnapshot.mockResolvedValue(snapshot);
    providerMethods.getFinancials.mockResolvedValue(null);
    providerMethods.getPriceHistory.mockResolvedValue([]);
  });

  it("renders one fundamentals capability message when the provider has no financials", async () => {
    render(await InstrumentPage({ params: Promise.resolve({ symbol: "BTC" }) }));

    expect(screen.getAllByText("Fundamentals are not available for this instrument type")).toHaveLength(1);
    expect(screen.queryByRole("heading", { name: "Annual financials" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Quarterly financials" })).not.toBeInTheDocument();
  });
});
