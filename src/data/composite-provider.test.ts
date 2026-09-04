import { describe, expect, it, vi } from "vitest";

import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSnapshot } from "@/domain/instrument";
import type { PricePoint } from "@/domain/price-history";
import { FixtureMarketDataProvider } from "@/data/fixture-provider";
import { MarketDataNotFoundError } from "@/data/market-data-errors";
import type { MarketDataProvider } from "@/data/market-data-provider";

import { CompositeMarketDataProvider } from "./composite-provider";

const cryptoSnapshot: InstrumentSnapshot = {
  symbol: "BTC", name: "Bitcoin", type: "crypto", venue: "CRYPTO", quoteCurrency: "USD",
  price: 100_000, dailyChange: null, dailyChangePercent: null, stockMetrics: null,
  source: "CoinGecko", asOf: "2026-09-04T00:00:00Z",
};

const stockSnapshot: InstrumentSnapshot = {
  symbol: "AMZN", name: "Amazon.com, Inc.", type: "stock", venue: "NASDAQ", quoteCurrency: "USD",
  price: 217.35, dailyChange: 1.2, dailyChangePercent: 0.0055, stockMetrics: null,
  source: "Finnhub", asOf: "2026-09-04T00:00:00Z",
};

const cryptoPoints: PricePoint[] = [{ timestamp: "2026-09-03T00:00:00Z", close: 100_000, volume: 1 }];

function stub(overrides: Partial<MarketDataProvider>): MarketDataProvider {
  return {
    searchInstruments: async () => [],
    getInstrumentSnapshot: async () => { throw new MarketDataNotFoundError("X"); },
    getPriceHistory: async () => [],
    getFinancials: async () => null,
    ...overrides,
  };
}

describe("CompositeMarketDataProvider", () => {
  it("routes crypto to the crypto provider and stocks to primary with fallback", async () => {
    const crypto = stub({
      getInstrumentSnapshot: vi.fn(async () => cryptoSnapshot),
      getPriceHistory: vi.fn(async () => cryptoPoints),
    });
    const primary = stub({
      getInstrumentSnapshot: vi.fn(async () => stockSnapshot),
      getPriceHistory: vi.fn(async () => { throw new MarketDataNotFoundError("AMZN"); }),
    });
    const fallback = stub({
      getPriceHistory: vi.fn(async () => cryptoPoints),
    });
    const fundamentals = stub({
      getFinancials: vi.fn(async () => ({ currency: "USD" }) as FinancialSeries),
    });

    const composite = new CompositeMarketDataProvider({ crypto, primary, fallback, fundamentals });

    await expect(composite.getInstrumentSnapshot("BTC")).resolves.toMatchObject({ source: "CoinGecko" });
    await expect(composite.getInstrumentSnapshot("AMZN")).resolves.toMatchObject({ source: "Finnhub" });
    await expect(composite.getPriceHistory("AMZN", "MAX")).resolves.toEqual(cryptoPoints);
    expect(fallback.getPriceHistory).toHaveBeenCalledTimes(1);
    expect(composite.getFinancials).toBeDefined();
  });

  it("falls back to fixture data when live providers have no key configured", async () => {
    const composite = CompositeMarketDataProvider.fromEnv({});
    const snapshot = await composite.getInstrumentSnapshot("AMZN");

    expect(snapshot.source).toContain("fixture");
    expect(new FixtureMarketDataProvider()).toBeDefined();
  });
});
