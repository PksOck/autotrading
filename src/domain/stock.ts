export interface StockSearchResult {
  symbol: string;
  companyName: string;
  exchange: string;
}

export interface StockSnapshot extends StockSearchResult {
  currency: string;
  price: number;
  dailyChange: number | null;
  dailyChangePercent: number | null;
  marketCap: number | null;
  enterpriseValue: number | null;
  peRatio: number | null;
  evToEbitda: number | null;
  fcfYield: number | null;
  source: string;
  asOf: string;
}
