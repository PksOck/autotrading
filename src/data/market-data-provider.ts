import type { FinancialSeries } from "@/domain/financials";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import type { InstrumentSearchResult, InstrumentSnapshot } from "@/domain/instrument";

export interface MarketDataProvider {
  searchInstruments(query: string): Promise<InstrumentSearchResult[]>;
  getInstrumentSnapshot(symbol: string): Promise<InstrumentSnapshot>;
  getPriceHistory(symbol: string, range: PriceRange): Promise<PricePoint[]>;
  getFinancials(symbol: string): Promise<FinancialSeries | null>;
}
