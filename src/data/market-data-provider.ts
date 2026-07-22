import type { FinancialSeries } from "@/domain/financials";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import type { StockSearchResult, StockSnapshot } from "@/domain/stock";

export interface MarketDataProvider {
  searchStocks(query: string): Promise<StockSearchResult[]>;
  getStockSnapshot(symbol: string): Promise<StockSnapshot>;
  getPriceHistory(symbol: string, range: PriceRange): Promise<PricePoint[]>;
  getFinancials(symbol: string): Promise<FinancialSeries>;
}
