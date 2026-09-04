import { z } from "zod";

import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSearchResult, InstrumentSnapshot } from "@/domain/instrument";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import { normalizeSymbol } from "@/lib/market-data";

import { fetchJsonWithRetry } from "./http";
import { MarketDataNotFoundError } from "./market-data-errors";
import type { MarketDataProvider } from "./market-data-provider";

const quoteSchema = z.object({ "Global Quote": z.object({
  "01. symbol": z.string(),
  "05. price": z.string(),
  "09. change": z.string().optional(),
  "10. change percent": z.string().optional(),
}) });

/**
 * Server-only AlphaVantage adapter: fallback for quotes only.
 * Free tier is 25 req/day so this adapter never owns primary traffic;
 * the composite router calls it only when Finnhub fails.
 */
export class AlphaVantageProvider implements MarketDataProvider {
  constructor(
    private readonly apiKey: string,
    private readonly baseUrl = "https://www.alphavantage.co/query",
  ) {}

  private url(params: Record<string, string>): string {
    return `${this.baseUrl}?${new URLSearchParams({ ...params, apikey: this.apiKey })}`;
  }

  async searchInstruments(query: string): Promise<InstrumentSearchResult[]> {
    const normalized = query.trim();
    if (!normalized) return [];
    const raw = await fetchJsonWithRetry(
      "alphavantage",
      this.url({ function: "SYMBOL_SEARCH", keywords: normalized }),
      this.apiKey,
    );
    const parsed = z.object({ bestMatches: z.array(z.object({
      "1. symbol": z.string(),
      "2. name": z.string(),
      "4. region": z.string().optional(),
    })).default([]) }).parse(raw);
    return parsed.bestMatches.slice(0, 10).map((entry) => ({
      symbol: normalizeSymbol(entry["1. symbol"]),
      name: entry["2. name"],
      type: "stock" as const,
      venue: entry["4. region"] || "US",
    }));
  }

  async getInstrumentSnapshot(symbol: string): Promise<InstrumentSnapshot> {
    const normalized = normalizeSymbol(symbol);
    const raw = await fetchJsonWithRetry(
      "alphavantage",
      this.url({ function: "GLOBAL_QUOTE", symbol: normalized }),
      this.apiKey,
    );
    const quote = quoteSchema.parse(raw)["Global Quote"];
    const price = Number(quote["05. price"]);
    if (!Number.isFinite(price) || price <= 0) throw new MarketDataNotFoundError(normalized);

    return {
      symbol: normalizeSymbol(quote["01. symbol"]),
      name: normalized,
      type: "stock",
      venue: "US",
      quoteCurrency: "USD",
      price,
      dailyChange: quote["09. change"] ? Number(quote["09. change"]) : null,
      dailyChangePercent: quote["10. change percent"] ? Number(quote["10. change percent"].replace("%", "")) / 100 : null,
      source: "AlphaVantage",
      asOf: new Date().toISOString(),
      stockMetrics: null,
    };
  }

  async getPriceHistory(symbol: string, _range: PriceRange): Promise<PricePoint[]> {
    const normalized = normalizeSymbol(symbol);
    const raw = await fetchJsonWithRetry(
      "alphavantage",
      this.url({ function: "TIME_SERIES_DAILY", symbol: normalized, outputsize: "compact" }),
      this.apiKey,
    );
    const parsed = z.object({ "Time Series (Daily)": z.record(z.string(), z.object({ "4. close": z.string(), "5. volume": z.string() })).default({}) }).parse(raw);
    const points: PricePoint[] = Object.entries(parsed["Time Series (Daily)"])
      .map(([date, row]) => ({
        timestamp: new Date(`${date}T20:00:00Z`).toISOString(),
        close: Number(row["4. close"]),
        volume: Number(row["5. volume"]),
      }))
      .filter((point) => Number.isFinite(point.close) && point.close > 0)
      .sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    if (points.length === 0) throw new MarketDataNotFoundError(normalized);
    return points;
  }

  async getFinancials(_symbol: string): Promise<FinancialSeries | null> {
    return null;
  }
}
