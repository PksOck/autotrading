export type PriceRange = "1M" | "6M" | "1Y" | "5Y" | "MAX";

export interface PricePoint {
  timestamp: string;
  close: number;
  volume: number | null;
}
