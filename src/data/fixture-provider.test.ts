import { describe, expect, it } from "vitest";

import { FixtureMarketDataProvider } from "./fixture-provider";
import { MarketDataNotFoundError } from "./market-data-errors";

describe("FixtureMarketDataProvider", () => {
  const provider = new FixtureMarketDataProvider();

  it("searches case-insensitively by company name", async () => {
    expect(await provider.searchStocks("amazon")).toEqual([
      expect.objectContaining({ symbol: "AMZN", companyName: "Amazon.com, Inc." }),
    ]);
  });

  it("normalizes symbols for snapshot lookup", async () => {
    expect((await provider.getStockSnapshot(" amzn ")).symbol).toBe("AMZN");
  });

  it("reports unknown symbols with a typed error", async () => {
    await expect(provider.getStockSnapshot("NOPE")).rejects.toBeInstanceOf(
      MarketDataNotFoundError,
    );
  });

  it("returns three annual and four quarterly periods", async () => {
    const financials = await provider.getFinancials("AMZN");
    expect(financials.annual).toHaveLength(3);
    expect(financials.quarterly).toHaveLength(4);
  });

  it("deduplicates and sorts price history", async () => {
    const history = await provider.getPriceHistory("AMZN", "MAX");
    expect(history.map(({ timestamp }) => timestamp)).toEqual([
      "2026-07-18T20:00:00Z",
      "2026-07-21T20:00:00Z",
      "2026-07-22T20:00:00Z",
    ]);
  });
});
