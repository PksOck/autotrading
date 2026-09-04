import { z } from "zod";

import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSearchResult, InstrumentSnapshot } from "@/domain/instrument";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import { normalizeSymbol } from "@/lib/market-data";
import { filterPriceHistory } from "@/lib/price-history";

import { fetchJsonWithRetry } from "./http";
import { MarketDataNotFoundError } from "./market-data-errors";
import type { MarketDataProvider } from "./market-data-provider";

const quoteSchema = z.object({
  c: z.number(),
  d: z.number().nullable().default(null),
  dp: z.number().nullable().default(null),
});

const profileSchema = z.object({
  ticker: z.string().optional(),
  name: z.string().optional(),
  exchange: z.string().optional(),
  currency: z.string().optional(),
});

const candleSchema = z.object({
  s: z.string(),
  t: z.array(z.number()).default([]),
  c: z.array(z.number()).default([]),
  v: z.array(z.number()).default([]),
});

const searchSchema = z.object({
  result: z
    .array(z.object({ symbol: z.string(), description: z.string(), type: z.string().optional() }))
    .default([]),
});

const RANGE_SECONDS: Record<PriceRange, number> = {
  "1M": 31 * 86_400,
  "6M": 183 * 86_400,
  "1Y": 366 * 86_400,
  "5Y": 5 * 366 * 86_400,
  MAX: 366 * 86_400,
};

/**
 * Server-only Finnhub adapter (stock prices + search).
 * Fundamentals stay an explicit unavailable capability: Finnhub
 * standardized statements live on a separate paid tier, so this
 * adapter returns null rather than inventing numbers.
 */
export class FinnhubProvider implements MarketDataProvider {
  constructor(
    private readonly apiKey: string,
    private readonly baseUrl = "https://finnhub.io/api/v1",
  ) {}

  private url(path: string, params: Record<string, string>): string {
    const query = new URLSearchParams({ ...params, token: this.apiKey });
    return `${this.baseUrl}${path}?${query.toString()}`;
  }

  async searchInstruments(query: string): Promise<InstrumentSearchResult[]> {
    const normalized = query.trim();
    if (!normalized) return [];
    const data = searchSchema.parse(
      await fetchJsonWithRetry("finnhub", this.url("/search", { q: normalized }), this.apiKey),
    );
    return data.result.slice(0, 10).map((entry) => ({
      symbol: normalizeSymbol(entry.symbol),
      name: entry.description || entry.symbol,
      type: "stock" as const,
      venue: "US",
    }));
  }

  async getInstrumentSnapshot(symbol: string): Promise<InstrumentSnapshot> {
    const normalized = normalizeSymbol(symbol);
    const [quoteRaw, profileRaw] = await Promise.all([
      fetchJsonWithRetry("finnhub", this.url("/quote", { symbol: normalized }), this.apiKey),
      fetchJsonWithRetry(
        "finnhub",
        this.url("/stock/profile2", { symbol: normalized }),
        this.apiKey,
      ),
    ]);
    const quote = quoteSchema.parse(quoteRaw);
    if (!(quote.c > 0)) throw new MarketDataNotFoundError(normalized);
    const profile = profileSchema.parse(profileRaw);
    const now = new Date().toISOString();

    return {
      symbol: normalized,
      name: profile.name || normalized,
      type: "stock",
      venue: profile.exchange || "US",
      quoteCurrency: profile.currency || "USD",
      price: quote.c,
      dailyChange: quote.d,
      dailyChangePercent: quote.dp === null ? null : quote.dp / 100,
      source: "Finnhub",
      asOf: now,
      stockMetrics: null,
    };
  }

  async getPriceHistory(symbol: string, range: PriceRange): Promise<PricePoint[]> {
    const normalized = normalizeSymbol(symbol);
    const to = Math.floor(Date.now() / 1000);
    const from = to - RANGE_SECONDS[range];
    const raw = await fetchJsonWithRetry(
      "finnhub",
      this.url("/stock/candle", {
        symbol: normalized,
        resolution: "D",
        from: String(from),
        to: String(to),
      }),
      this.apiKey,
    );
    const parsed = candleSchema.parse(raw);
    if (parsed.s !== "ok" || parsed.t.length === 0) throw new MarketDataNotFoundError(normalized);

    const points: PricePoint[] = parsed.t.map((time, index) => ({
      timestamp: new Date(time * 1000).toISOString(),
      close: parsed.c[index] ?? 0,
      volume: parsed.v[index] ?? null,
    }));
    const seen = new Map<string, PricePoint>();
    for (const point of points) {
      if (point.close > 0) seen.set(point.timestamp, point);
    }
    const sorted = [...seen.values()].sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    if (range === "MAX") return sorted;
    return filterPriceHistory(sorted, range);
  }

  async getFinancials(_symbol: string): Promise<FinancialSeries | null> {
    return null;
  }
}
