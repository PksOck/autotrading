import { z } from "zod";

import amznFixture from "@/data/fixtures/amzn.json";
import searchIndexFixture from "@/data/fixtures/search-index.json";
import { fixtureStockSchema } from "@/domain/fixture-schema";
import type { FinancialSeries } from "@/domain/financials";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import type { StockSearchResult, StockSnapshot } from "@/domain/stock";
import { normalizeSymbol } from "@/lib/market-data";

import { MarketDataNotFoundError } from "./market-data-errors";
import type { MarketDataProvider } from "./market-data-provider";

const searchIndexSchema = z.array(
  z.object({
    symbol: z.string().trim().min(1),
    companyName: z.string().trim().min(1),
    exchange: z.string().trim().min(1),
  }),
);

const stockFixture = fixtureStockSchema.parse(amznFixture);
export const fixtureSearchIndex = searchIndexSchema.parse(searchIndexFixture);

export class FixtureMarketDataProvider implements MarketDataProvider {
  async searchStocks(query: string): Promise<StockSearchResult[]> {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return [];
    return fixtureSearchIndex.filter(
      ({ symbol, companyName }) =>
        symbol.toLowerCase().includes(normalizedQuery) ||
        companyName.toLowerCase().includes(normalizedQuery),
    );
  }

  async getStockSnapshot(symbol: string): Promise<StockSnapshot> {
    this.assertSupported(symbol);
    return stockFixture.snapshot;
  }

  async getPriceHistory(symbol: string, _range: PriceRange): Promise<PricePoint[]> {
    this.assertSupported(symbol);
    const uniqueByTimestamp = new Map(
      stockFixture.priceHistory.map((point) => [point.timestamp, point]),
    );
    return [...uniqueByTimestamp.values()].sort((a, b) =>
      a.timestamp.localeCompare(b.timestamp),
    );
  }

  async getFinancials(symbol: string): Promise<FinancialSeries> {
    this.assertSupported(symbol);
    return stockFixture.financials;
  }

  private assertSupported(symbol: string): void {
    const normalizedSymbol = normalizeSymbol(symbol);
    if (normalizedSymbol !== stockFixture.snapshot.symbol) {
      throw new MarketDataNotFoundError(normalizedSymbol);
    }
  }
}
