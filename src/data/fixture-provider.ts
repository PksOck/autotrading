import { z } from "zod";

import amznFixture from "@/data/fixtures/amzn.json";
import searchIndexFixture from "@/data/fixtures/search-index.json";
import {
  fixtureInstrumentSchema,
  instrumentSearchResultSchema,
} from "@/domain/fixture-schema";
import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSearchResult, InstrumentSnapshot } from "@/domain/instrument";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import { normalizeSymbol } from "@/lib/market-data";

import { MarketDataNotFoundError } from "./market-data-errors";
import type { MarketDataProvider } from "./market-data-provider";

const searchIndexSchema = z.array(instrumentSearchResultSchema);

const instrumentFixture = fixtureInstrumentSchema.parse(amznFixture);
export const fixtureSearchIndex = searchIndexSchema.parse(searchIndexFixture);

export class FixtureMarketDataProvider implements MarketDataProvider {
  async searchInstruments(query: string): Promise<InstrumentSearchResult[]> {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return [];
    return fixtureSearchIndex.filter(
      ({ symbol, name }) =>
        symbol.toLowerCase().includes(normalizedQuery) ||
        name.toLowerCase().includes(normalizedQuery),
    );
  }

  async getInstrumentSnapshot(symbol: string): Promise<InstrumentSnapshot> {
    this.assertSupported(symbol);
    return instrumentFixture.snapshot;
  }

  async getPriceHistory(symbol: string, _range: PriceRange): Promise<PricePoint[]> {
    this.assertSupported(symbol);
    const uniqueByTimestamp = new Map(
      instrumentFixture.priceHistory.map((point) => [point.timestamp, point]),
    );
    return [...uniqueByTimestamp.values()].sort((a, b) =>
      a.timestamp.localeCompare(b.timestamp),
    );
  }

  async getFinancials(symbol: string): Promise<FinancialSeries> {
    this.assertSupported(symbol);
    return instrumentFixture.financials;
  }

  private assertSupported(symbol: string): void {
    const normalizedSymbol = normalizeSymbol(symbol);
    if (normalizedSymbol !== instrumentFixture.snapshot.symbol) {
      throw new MarketDataNotFoundError(normalizedSymbol);
    }
  }
}
