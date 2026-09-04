import { z } from "zod";

import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSearchResult, InstrumentSnapshot } from "@/domain/instrument";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import { normalizeSymbol } from "@/lib/market-data";
import { filterPriceHistory } from "@/lib/price-history";

import { fetchJsonWithRetry } from "./http";
import { MarketDataNotFoundError } from "./market-data-errors";
import type { MarketDataProvider } from "./market-data-provider";

const profileSchema = z.array(
  z.object({
    symbol: z.string(),
    companyName: z.string().optional(),
    exchange: z.string().optional(),
    currency: z.string().optional(),
    mktCap: z.number().nullable().default(null),
    price: z.number().optional(),
  }),
);

const incomeSchema = z.array(
  z.object({
    date: z.string(),
    revenue: z.number().nullable().default(null),
    operatingIncome: z.number().nullable().default(null),
    netIncome: z.number().nullable().default(null),
    weightedAverageShsOutDil: z.number().nullable().default(null),
  }),
);

const cashflowSchema = z.array(z.object({ date: z.string(), freeCashFlow: z.number().nullable().default(null) }));

const searchSchema = z.array(z.object({ symbol: z.string(), name: z.string().optional() }));

/**
 * Server-only FMP adapter. Quota-tight by design (user budget: 10/day):
 * fundamentals snapshots are cached for 30 days at the composite layer,
 * prices are NOT fetched here (Finnhub owns prices).
 */
export class FmpProvider implements MarketDataProvider {
  constructor(
    private readonly apiKey: string,
    private readonly baseUrl = "https://financialmodelingprep.com/stable",
  ) {}

  private url(path: string, params: Record<string, string>): string {
    return `${this.baseUrl}${path}?${new URLSearchParams({ ...params, apikey: this.apiKey })}`;
  }

  async searchInstruments(query: string): Promise<InstrumentSearchResult[]> {
    const normalized = query.trim();
    if (!normalized) return [];
    const raw = await fetchJsonWithRetry("fmp", this.url("/search-symbol", { query: normalized }), this.apiKey);
    return searchSchema.parse(raw).slice(0, 10).map((entry) => ({
      symbol: normalizeSymbol(entry.symbol),
      name: entry.name || entry.symbol,
      type: "stock" as const,
      venue: "US",
    }));
  }

  async getInstrumentSnapshot(symbol: string): Promise<InstrumentSnapshot> {
    const normalized = normalizeSymbol(symbol);
    const raw = await fetchJsonWithRetry("fmp", this.url("/profile", { symbol: normalized }), this.apiKey);
    const profile = profileSchema.parse(raw)[0];
    if (!profile) throw new MarketDataNotFoundError(normalized);

    return {
      symbol: normalized,
      name: profile.companyName || normalized,
      type: "stock",
      venue: profile.exchange || "US",
      quoteCurrency: profile.currency || "USD",
      price: profile.price && profile.price > 0 ? profile.price : 1,
      dailyChange: null,
      dailyChangePercent: null,
      source: "FMP",
      asOf: new Date().toISOString(),
      stockMetrics: profile.mktCap === null ? null : {
        marketCap: profile.mktCap,
        enterpriseValue: null,
        peRatio: null,
        evToEbitda: null,
        fcfYield: null,
      },
    };
  }

  async getPriceHistory(symbol: string, range: PriceRange): Promise<PricePoint[]> {
    const normalized = normalizeSymbol(symbol);
    const raw = await fetchJsonWithRetry(
      "fmp",
      this.url("/historical-price-eod/full", { symbol: normalized }),
      this.apiKey,
    );
    const parsed = z.object({ historical: z.array(z.object({
      date: z.string(),
      close: z.number(),
      volume: z.number().nullable().default(null),
    })).default([]) }).parse(raw);
    const points: PricePoint[] = parsed.historical
      .filter((row) => row.close > 0)
      .map((row) => ({ timestamp: new Date(`${row.date}T20:00:00Z`).toISOString(), close: row.close, volume: row.volume }));
    const sorted = [...new Map(points.map((p) => [p.timestamp, p])).values()]
      .sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    if (range === "MAX") return sorted;
    return filterPriceHistory(sorted, range);
  }

  async getFinancials(symbol: string): Promise<FinancialSeries | null> {
    const normalized = normalizeSymbol(symbol);
    const [incomeRaw, cashRaw] = await Promise.all([
      fetchJsonWithRetry("fmp", this.url("/income-statement", { symbol: normalized, period: "annual", limit: "5" }), this.apiKey),
      fetchJsonWithRetry("fmp", this.url("/cash-flow-statement", { symbol: normalized, period: "annual", limit: "5" }), this.apiKey),
    ]);
    const income = incomeSchema.parse(incomeRaw);
    if (income.length === 0) return null;
    const cash = new Map(cashflowSchema.parse(cashRaw).map((row) => [row.date, row.freeCashFlow]));

    return {
      currency: "USD",
      unit: "millions",
      source: "FMP",
      asOf: new Date().toISOString(),
      annual: [...income].reverse().map((row) => ({
        period: row.date.slice(0, 4),
        revenue: row.revenue === null ? null : row.revenue / 1_000_000,
        operatingIncome: row.operatingIncome === null ? null : row.operatingIncome / 1_000_000,
        freeCashFlow: (() => {
          const fcf = cash.get(row.date);
          return fcf == null ? null : fcf / 1_000_000;
        })(),
        operatingMargin: row.revenue && row.operatingIncome ? row.operatingIncome / row.revenue : null,
        dilutedShares: row.weightedAverageShsOutDil === null ? null : row.weightedAverageShsOutDil / 1_000_000,
      })),
      quarterly: [],
    };
  }
}
