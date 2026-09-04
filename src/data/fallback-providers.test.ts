import { describe, expect, it, vi } from "vitest";

import { AlphaVantageProvider } from "./alphavantage-provider";
import { FmpProvider } from "./fmp-provider";

describe("FmpProvider (fundamentals-first, quota-tight)", () => {
  it("maps profile + statements to snapshot and financials", async () => {
    const fetchMock = vi.fn(async (url: string | URL | Request) => {
      const href = String(url);
      if (href.includes("profile")) {
        return new Response(
          JSON.stringify([{ symbol: "AMZN", companyName: "Amazon.com, Inc.", exchange: "NASDAQ", currency: "USD", mktCap: 2310000000000, price: 217.35 }]),
          { status: 200 },
        );
      }
      if (href.includes("income-statement")) {
        return new Response(
          JSON.stringify([
            { date: "2025-12-31", revenue: 694200000000, operatingIncome: 78200000000, netIncome: 50000000000, weightedAverageShsOutDil: 10670000000 },
          ]),
          { status: 200 },
        );
      }
      if (href.includes("cash-flow-statement")) {
        return new Response(JSON.stringify([{ date: "2025-12-31", freeCashFlow: 38219000000 }]), { status: 200 });
      }
      return new Response(JSON.stringify([]), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    try {
      const provider = new FmpProvider("test-key");
      const snapshot = await provider.getInstrumentSnapshot("AMZN");
      expect(snapshot).toMatchObject({ symbol: "AMZN", price: 217.35, quoteCurrency: "USD" });

      const financials = await provider.getFinancials("AMZN");
      expect(financials?.annual[0]).toMatchObject({ period: "2025", revenue: 694200 });
      expect(financials?.source).toContain("FMP");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("AlphaVantageProvider (fallback only, 25/day)", () => {
  it("maps global quote to a snapshot", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({ "Global Quote": { "01. symbol": "AMZN", "05. price": "217.35", "09. change": "1.20", "10. change percent": "0.55%" } }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    try {
      const provider = new AlphaVantageProvider("test-key");
      const snapshot = await provider.getInstrumentSnapshot("amzn");
      expect(snapshot).toMatchObject({ symbol: "AMZN", price: 217.35 });
      expect(snapshot.source).toContain("AlphaVantage");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
