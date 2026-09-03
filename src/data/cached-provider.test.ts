import { describe, expect, it, vi } from "vitest";

import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSearchResult, InstrumentSnapshot } from "@/domain/instrument";
import type { PricePoint } from "@/domain/price-history";
import type { MarketDataProvider } from "@/data/market-data-provider";

import { CachedMarketDataProvider } from "./cached-provider";

const snapshot: InstrumentSnapshot = {
  symbol: "AMZN", name: "Amazon.com, Inc.", type: "stock", venue: "NASDAQ",
  quoteCurrency: "USD", price: 217.35, dailyChange: null, dailyChangePercent: null,
  stockMetrics: null, source: "test", asOf: "2026-07-22T20:05:00Z",
};

const points: PricePoint[] = [{ timestamp: "2026-07-22T20:00:00Z", close: 217.35, volume: 100 }];

const financials: FinancialSeries = {
  currency: "USD", unit: "millions", source: "test", asOf: "2026-07-22T20:05:00Z",
  annual: [], quarterly: [],
};

function stubProvider(): MarketDataProvider & {
  calls: Record<string, number>;
} {
  const calls: Record<string, number> = { search: 0, snapshot: 0, history: 0, financials: 0 };
  const results: InstrumentSearchResult[] = [
    { symbol: "AMZN", name: "Amazon.com, Inc.", type: "stock", venue: "NASDAQ" },
  ];
  return {
    calls,
    searchInstruments: vi.fn(async () => {
      calls.search += 1;
      return results;
    }),
    getInstrumentSnapshot: vi.fn(async () => {
      calls.snapshot += 1;
      return snapshot;
    }),
    getPriceHistory: vi.fn(async () => {
      calls.history += 1;
      return points;
    }),
    getFinancials: vi.fn(async () => {
      calls.financials += 1;
      return financials;
    }),
  };
}

describe("CachedMarketDataProvider", () => {
  it("serves repeated reads from cache within the TTL", async () => {
    const inner = stubProvider();
    let now = 1_000;
    const provider = new CachedMarketDataProvider(inner, 60_000, () => now);

    await expect(provider.getInstrumentSnapshot("amzn")).resolves.toEqual(snapshot);
    now += 30_000;
    await expect(provider.getInstrumentSnapshot("AMZN")).resolves.toEqual(snapshot);
    expect(inner.calls.snapshot).toBe(1);
  });

  it("refetches after the TTL expires and isolates cache keys", async () => {
    const inner = stubProvider();
    let now = 0;
    const provider = new CachedMarketDataProvider(inner, 1_000, () => now);

    await provider.getPriceHistory("AMZN", "MAX");
    await provider.getPriceHistory("AMZN", "1M");
    expect(inner.calls.history).toBe(2);

    now += 1_001;
    await provider.getPriceHistory("AMZN", "MAX");
    expect(inner.calls.history).toBe(3);
  });

  it("caches search and financials but never caches failures", async () => {
    const inner = stubProvider();
    const provider = new CachedMarketDataProvider(inner);

    await provider.searchInstruments("amz");
    await provider.searchInstruments("AMZ");
    expect(inner.calls.search).toBe(1);

    await provider.getFinancials("AMZN");
    await provider.getFinancials("AMZN");
    expect(inner.calls.financials).toBe(1);

    inner.getInstrumentSnapshot = vi.fn(async () => {
      inner.calls.snapshot += 1;
      throw new Error("flaky");
    });
    await expect(provider.getInstrumentSnapshot("AMZN")).rejects.toThrow("flaky");
    await expect(provider.getInstrumentSnapshot("AMZN")).rejects.toThrow("flaky");
    expect(inner.calls.snapshot).toBe(2);
  });
});
