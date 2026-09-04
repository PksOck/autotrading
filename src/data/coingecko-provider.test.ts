import { describe, expect, it, vi } from "vitest";

import { CoinGeckoProvider, coinIdForSymbol } from "./coingecko-provider";

const rangePayload = {
  prices: [
    [1753132800000, 112000.5],
    [1753219200000, 113000.25],
  ],
  total_volumes: [
    [1753132800000, 50_000_000_000],
    [1753219200000, 52_000_000_000],
  ],
};

describe("coingecko mapping", () => {
  it("maps BTC/ETH/SOL symbols to CoinGecko ids", () => {
    expect(coinIdForSymbol("btc")).toBe("bitcoin");
    expect(coinIdForSymbol("ETH")).toBe("ethereum");
    expect(coinIdForSymbol("sol")).toBe("solana");
    expect(coinIdForSymbol("AMZN")).toBeNull();
  });

  it("maps range payload to price points", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(rangePayload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    try {
      const provider = new CoinGeckoProvider("demo-key");
      const history = await provider.getPriceHistory("BTC", "MAX");

      expect(history).toHaveLength(2);
      expect(history[0]?.close).toBeCloseTo(112000.5, 5);
      expect(history[0]?.volume).toBe(50_000_000_000);
      expect(history[0]?.timestamp.endsWith("Z")).toBe(true);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("rejects non-crypto symbols with a typed error", async () => {
    const provider = new CoinGeckoProvider("demo-key");
    await expect(provider.getPriceHistory("AMZN", "MAX")).rejects.toThrowError(
      expect.objectContaining({ name: "MarketDataNotFoundError" }),
    );
  });
});
