import { z } from "zod";

import { instrumentTypeSchema } from "./instrument";

const nullableMetricSchema = z.number().finite().nullable();
const utcTimestampSchema = z.string().datetime({ offset: true });

export const stockMetricsSchema = z.object({
  marketCap: nullableMetricSchema,
  enterpriseValue: nullableMetricSchema,
  peRatio: nullableMetricSchema,
  evToEbitda: nullableMetricSchema,
  fcfYield: nullableMetricSchema,
});

export const instrumentSearchResultSchema = z.object({
  symbol: z.string().trim().min(1),
  name: z.string().trim().min(1),
  type: instrumentTypeSchema,
  venue: z.string().trim().min(1),
});

export const instrumentSnapshotSchema = instrumentSearchResultSchema.extend({
  quoteCurrency: z.string().trim().min(1),
  price: z.number().positive(),
  dailyChange: nullableMetricSchema,
  dailyChangePercent: nullableMetricSchema,
  source: z.string().trim().min(1),
  asOf: utcTimestampSchema,
  stockMetrics: stockMetricsSchema.nullable(),
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

export const fixtureInstrumentSchema = z.object({
  snapshot: instrumentSnapshotSchema,
  financials: financialSeriesSchema.nullable(),
  priceHistory: z.array(pricePointSchema),
});

export type FixtureInstrument = z.infer<typeof fixtureInstrumentSchema>;
