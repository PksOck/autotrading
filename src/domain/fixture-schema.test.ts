import { describe, expect, it } from "vitest";

import { fixtureInstrumentSchema } from "./fixture-schema";

const validFixture = {
  snapshot: {
    symbol: "AMZN", name: "Amazon.com, Inc.", type: "stock", venue: "NASDAQ", quoteCurrency: "USD",
    price: 217.35, dailyChange: 1.2, dailyChangePercent: 0.0055,
    stockMetrics: { marketCap: 2_310_000_000_000, enterpriseValue: 2_370_000_000_000,
      peRatio: 42.25, evToEbitda: 21.5, fcfYield: null },
    source: "Illustrative fixture data", asOf: "2026-07-22T12:00:00Z",
  },
  financials: {
    currency: "USD", unit: "millions", source: "Illustrative fixture data",
    asOf: "2026-07-22T12:00:00Z", annual: [], quarterly: [],
  },
  priceHistory: [],
};

describe("fixtureInstrumentSchema", () => {
  it("accepts explicit null metrics", () => {
    expect(fixtureInstrumentSchema.parse(validFixture).snapshot.stockMetrics?.fcfYield).toBeNull();
  });

  it("accepts a null financial capability for a non-stock instrument", () => {
    const nonStockFixture = {
      ...validFixture,
      snapshot: { ...validFixture.snapshot, type: "crypto", stockMetrics: null },
      financials: null,
    };

    expect(fixtureInstrumentSchema.parse(nonStockFixture).financials).toBeNull();
  });

  it("rejects incomplete data contracts", () => {
    expect(() => fixtureInstrumentSchema.parse({ symbol: "AMZN", quoteCurrency: "USD" })).toThrow();
  });

  it("rejects timestamps without an ISO-8601 timezone", () => {
    const invalid = structuredClone(validFixture);
    invalid.snapshot.asOf = "2026-07-22 12:00";
    expect(() => fixtureInstrumentSchema.parse(invalid)).toThrow();
  });
});
