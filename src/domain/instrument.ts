import { z } from "zod";

import type { StockMetrics } from "./stock";

export const instrumentTypeSchema = z.enum(["stock", "etf", "crypto", "commodity"]);

export type InstrumentType = "stock" | "etf" | "crypto" | "commodity";

export interface InstrumentSearchResult {
  symbol: string;
  name: string;
  type: InstrumentType;
  venue: string;
}

export interface InstrumentSnapshot extends InstrumentSearchResult {
  quoteCurrency: string;
  price: number;
  dailyChange: number | null;
  dailyChangePercent: number | null;
  source: string;
  asOf: string;
  stockMetrics: StockMetrics | null;
}
