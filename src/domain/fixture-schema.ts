import { z } from "zod";

const nullableMetricSchema = z.number().finite().nullable();
const utcTimestampSchema = z.string().datetime({ offset: true });

export const stockSnapshotSchema = z.object({
  symbol: z.string().trim().min(1),
  companyName: z.string().trim().min(1),
  exchange: z.string().trim().min(1),
  currency: z.string().trim().min(1),
  price: z.number().positive(),
  dailyChange: nullableMetricSchema,
  dailyChangePercent: nullableMetricSchema,
  marketCap: nullableMetricSchema,
  enterpriseValue: nullableMetricSchema,
  peRatio: nullableMetricSchema,
  evToEbitda: nullableMetricSchema,
  fcfYield: nullableMetricSchema,
  source: z.string().trim().min(1),
  asOf: utcTimestampSchema,
});

export const financialPeriodSchema = z.object({
  period: z.string().trim().min(1),
  revenue: nullableMetricSchema,
  operatingIncome: nullableMetricSchema,
  freeCashFlow: nullableMetricSchema,
  operatingMargin: nullableMetricSchema,
  dilutedShares: nullableMetricSchema,
});

export const financialSeriesSchema = z.object({
  currency: z.string().trim().min(1),
  unit: z.string().trim().min(1),
  source: z.string().trim().min(1),
  asOf: utcTimestampSchema,
  annual: z.array(financialPeriodSchema),
  quarterly: z.array(financialPeriodSchema),
});

export const pricePointSchema = z.object({
  timestamp: utcTimestampSchema,
  close: z.number().positive(),
  volume: z.number().nonnegative().nullable(),
});

export const fixtureStockSchema = z.object({
  snapshot: stockSnapshotSchema,
  financials: financialSeriesSchema,
  priceHistory: z.array(pricePointSchema),
});

export type FixtureStock = z.infer<typeof fixtureStockSchema>;
