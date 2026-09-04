import { z } from "zod";

import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSearchResult, InstrumentSnapshot } from "@/domain/instrument";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import { normalizeSymbol } from "@/lib/market-data";
import { filterPriceHistory } from "@/lib/price-history";

import { fetchJsonWithRetry } from "./http";
import { MarketDataNotFoundError } from "./market-data-errors";
import type { MarketDataProvider } from "./market-data-provider";

const COIN_IDS: Record<string, { id: string; name: string }> = {
  BTC: { id: "bitcoin", name: "Bitcoin" },
  ETH: { id: "ethereum", name: "Ethereum" },
  SOL: { id: "solana", name: "Solana" },
};

export function coinIdForSymbol(symbol: string): string | null {
  return COIN_IDS[normalizeSymbol(symbol)]?.id ?? null;
}

const rangeSchema = z.object({
  prices: z.array(z.tuple([z.number(), z.number()])).default([]),
  total_volumes: z.array(z.tuple([z.number(), z.number()])).default([]),
});

/**
 * Server-only CoinGecko adapter (crypto only, demo plan = 365 days history).
 * Stocks resolve to MarketDataNotFoundError so the composite router
 * can fall through to the equity provider.
 */
export class CoinGeckoProvider implements MarketDataProvider {
  constructor(
    private readonly apiKey: string,
    private readonly baseUrl = "https://api.coingecko.com/api/v3",
  ) {}

  private url(path: string): string {
    const separator = path.includes("?") ? "&" : "?";
    return `${this.baseUrl}${path}${separator}x_cg_demo_api_key=${this.apiKey}`;
  }

  async searchInstruments(query: string): Promise<InstrumentSearchResult[]> {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return [];
    return Object.entries(COIN_IDS)
      .filter(
        ([symbol, coin]) =>
          symbol.toLowerCase().includes(normalized) || coin.name.toLowerCase().includes(normalized),
      )
      .map(([symbol, coin]) => ({ symbol, name: coin.name, type: "crypto" as const, venue: "CRYPTO" }));
  }

  async getInstrumentSnapshot(symbol: string): Promise<InstrumentSnapshot> {
    const normalized = normalizeSymbol(symbol);
    const coin = COIN_IDS[normalized];
    if (!coin) throw new MarketDataNotFoundError(normalized);
    const history = await this.getPriceHistory(normalized, "MAX");
    const last = history.at(-1);
    if (!last) throw new MarketDataNotFoundError(normalized);

    return {
      symbol: normalized,
      name: coin.name,
      type: "crypto",
      venue: "CRYPTO",
      quoteCurrency: "USD",
      price: last.close,
      dailyChange: null,
      dailyChangePercent: null,
      source: "CoinGecko",
      asOf: last.timestamp,
      stockMetrics: null,
    };
  }

  async getPriceHistory(symbol: string, range: PriceRange): Promise<PricePoint[]> {
    const normalized = normalizeSymbol(symbol);
    const coinId = coinIdForSymbol(normalized);
    if (!coinId) throw new MarketDataNotFoundError(normalized);

    const now = Math.floor(Date.now() / 1000);
    const from = range === "MAX" ? now - 365 * 86_400 : now - 365 * 86_400;
    const raw = await fetchJsonWithRetry(
      "coingecko",
      this.url(`/coins/${coinId}/market_chart/range?vs_currency=usd&from=${from}&to=${now}`),
      this.apiKey,
    );
    const parsed = rangeSchema.parse(raw);
    const volumes = new Map<number, number>(parsed.total_volumes);

    const points: PricePoint[] = parsed.prices
      .filter(([, close]) => close > 0)
      .map(([ms, close]) => ({
        timestamp: new Date(ms).toISOString(),
        close,
        volume: volumes.get(ms) ?? null,
      }));
    const deduped = [...new Map(points.map((point) => [point.timestamp, point])).values()].sort(
      (a, b) => a.timestamp.localeCompare(b.timestamp),
    );
    if (range === "MAX") return deduped;
    return filterPriceHistory(deduped, range);
  }

  async getFinancials(_symbol: string): Promise<FinancialSeries | null> {
    return null;
  }
}
