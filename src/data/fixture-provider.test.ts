import { describe, expect, it } from "vitest";

import { FixtureMarketDataProvider } from "./fixture-provider";
import { MarketDataNotFoundError } from "./market-data-errors";

describe("FixtureMarketDataProvider", () => {
  const provider = new FixtureMarketDataProvider();

  it("searches case-insensitively by instrument name", async () => {
    expect((await provider.searchInstruments("amazon"))[0]).toMatchObject({
      symbol: "AMZN",
      name: "Amazon.com, Inc.",
      type: "stock",
      venue: "NASDAQ",
    });
  });

  it("normalizes symbols for instrument snapshot lookup", async () => {
    expect((await provider.getInstrumentSnapshot(" amzn ")).type).toBe("stock");
  });

  it("reports unknown symbols with a typed error", async () => {
    await expect(provider.getInstrumentSnapshot("NOPE")).rejects.toBeInstanceOf(
      MarketDataNotFoundError,
    );
  });

  it("returns three annual and four quarterly periods", async () => {
    const financials = await provider.getFinancials("AMZN");
    expect(financials).not.toBeNull();
    expect(financials?.annual).toHaveLength(3);
    expect(financials?.quarterly).toHaveLength(4);
  });

  it("returns a deterministic, range-aware five-year price history", async () => {
    const maximumHistory = await provider.getPriceHistory("AMZN", "MAX");
    const oneMonthHistory = await provider.getPriceHistory("AMZN", "1M");

    expect(maximumHistory).toHaveLength(1305);
    expect(maximumHistory.at(0)?.timestamp).toBe("2021-07-22T20:00:00Z");
    expect(maximumHistory.at(-1)?.timestamp).toBe("2026-07-22T20:00:00Z");
    expect(oneMonthHistory.at(0)?.timestamp).toBe("2026-06-22T20:00:00Z");
    expect(oneMonthHistory.at(-1)?.timestamp).toBe("2026-07-22T20:00:00Z");
    expect(maximumHistory.some(({ volume }) => volume === null)).toBe(true);
  });
});
