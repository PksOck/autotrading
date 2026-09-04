import { describe, expect, it, vi } from "vitest";

import { FinnhubProvider } from "./finnhub-provider";

const quote = { c: 217.35, d: 1.2, dp: 0.55, t: 1753130700 };
const profile = { ticker: "AMZN", name: "Amazon.com, Inc.", exchange: "NASDAQ", currency: "USD" };
const candles = {
  s: "ok",
  t: [1753046400, 1753132800],
  c: [216.1, 217.35],
  v: [40_000_000, 42_000_000],
};

function mockFetch(): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn(async (url: string | URL | Request) => {
    const href = String(url);
    if (href.includes("/quote")) return new Response(JSON.stringify(quote), { status: 200 });
    if (href.includes("/stock/profile2")) return new Response(JSON.stringify(profile), { status: 200 });
    if (href.includes("/stock/candle")) return new Response(JSON.stringify(candles), { status: 200 });
    if (href.includes("/search")) {
      return new Response(
        JSON.stringify({ result: [{ symbol: "AMZN", description: "Amazon.com, Inc.", type: "Common Stock" }] }),
        { status: 200 },
      );
    }
    return new Response("{}", { status: 200 });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("FinnhubProvider", () => {
  it("returns a snapshot mapped from quote + profile", async () => {
    mockFetch();
    try {
      const provider = new FinnhubProvider("test-key");
      const snapshot = await provider.getInstrumentSnapshot(" amzn ");

      expect(snapshot).toMatchObject({
        symbol: "AMZN",
        name: "Amazon.com, Inc.",
        type: "stock",
        venue: "NASDAQ",
        quoteCurrency: "USD",
        price: 217.35,
      });
      expect(snapshot.source).toContain("Finnhub");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("maps candles to ascending unique price points", async () => {
    mockFetch();
    try {
      const provider = new FinnhubProvider("test-key");
      const history = await provider.getPriceHistory("AMZN", "MAX");

      expect(history).toHaveLength(2);
      expect(history[0]).toMatchObject({ close: 216.1, volume: 40_000_000 });
      expect(history[1]?.timestamp.endsWith("Z")).toBe(true);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("searches by symbol description", async () => {
    mockFetch();
    try {
      const provider = new FinnhubProvider("test-key");
      const results = await provider.searchInstruments("amaz");

      expect(results[0]).toMatchObject({ symbol: "AMZN", venue: "US" });
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("reports financials as unavailable capability (Finnhub fundamentals are a separate paid tier)", async () => {
    mockFetch();
    try {
      const provider = new FinnhubProvider("test-key");
      await expect(provider.getFinancials("AMZN")).resolves.toBeNull();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
