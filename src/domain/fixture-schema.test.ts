import { describe, expect, it } from "vitest";

import { fixtureStockSchema } from "./fixture-schema";

const validFixture = {
  snapshot: {
    symbol: "AMZN", companyName: "Amazon.com, Inc.", exchange: "NASDAQ", currency: "USD",
    price: 217.35, dailyChange: 1.2, dailyChangePercent: 0.0055,
    marketCap: 2_310_000_000_000, enterpriseValue: 2_370_000_000_000,
    peRatio: 42.25, evToEbitda: 21.5, fcfYield: null,
    source: "Illustrative fixture data", asOf: "2026-07-22T12:00:00Z",
  },
  financials: {
    currency: "USD", unit: "millions", source: "Illustrative fixture data",
    asOf: "2026-07-22T12:00:00Z", annual: [], quarterly: [],
  },
  priceHistory: [],
};

describe("fixtureStockSchema", () => {
  it("accepts explicit null metrics", () => {
    expect(fixtureStockSchema.parse(validFixture).snapshot.fcfYield).toBeNull();
  });

  it("rejects incomplete data contracts", () => {
    expect(() => fixtureStockSchema.parse({ symbol: "AMZN", currency: "USD" })).toThrow();
  });

  it("rejects timestamps without an ISO-8601 timezone", () => {
    const invalid = structuredClone(validFixture);
    invalid.snapshot.asOf = "2026-07-22 12:00";
    expect(() => fixtureStockSchema.parse(invalid)).toThrow();
  });
});
