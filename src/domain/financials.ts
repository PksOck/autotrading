export interface FinancialPeriod {
  period: string;
  revenue: number | null;
  operatingIncome: number | null;
  freeCashFlow: number | null;
  operatingMargin: number | null;
  dilutedShares: number | null;
}

export interface FinancialSeries {
  currency: string;
  unit: string;
  source: string;
  asOf: string;
  annual: FinancialPeriod[];
  quarterly: FinancialPeriod[];
}
