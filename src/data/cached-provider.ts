import type { FinancialSeries } from "@/domain/financials";
import type { PriceRange } from "@/domain/price-history";
import { normalizeSymbol } from "@/lib/market-data";

import type { MarketDataProvider } from "./market-data-provider";

interface CacheEntry<T> {
  value: T;
  expiresAt: number;
}

/**
 * TTL cache decorator over any MarketDataProvider.
 * Entries expire lazily on read; failures are never cached.
 * A future licensed provider gets caching by wrapping it here.
 */
export class CachedMarketDataProvider implements MarketDataProvider {
  private readonly entries = new Map<string, CacheEntry<unknown>>();

  constructor(
    private readonly inner: MarketDataProvider,
    private readonly ttlMs = 60_000,
    private readonly now: () => number = Date.now,
  ) {}

  searchInstruments(query: string): Promise<Awaited<ReturnType<MarketDataProvider["searchInstruments"]>>> {
    return this.cached(`search:${query.trim().toLowerCase()}`, () =>
      this.inner.searchInstruments(query),
    );
  }

  getInstrumentSnapshot(symbol: string): Promise<Awaited<ReturnType<MarketDataProvider["getInstrumentSnapshot"]>>> {
    const normalized = normalizeSymbol(symbol);
    return this.cached(`snapshot:${normalized}`, () => this.inner.getInstrumentSnapshot(normalized));
  }

  getPriceHistory(
    symbol: string,
    range: PriceRange,
  ): Promise<Awaited<ReturnType<MarketDataProvider["getPriceHistory"]>>> {
    const normalized = normalizeSymbol(symbol);
    return this.cached(`history:${normalized}:${range}`, () =>
      this.inner.getPriceHistory(normalized, range),
    );
  }

  getFinancials(symbol: string): Promise<FinancialSeries | null> {
    const normalized = normalizeSymbol(symbol);
    return this.cached(`financials:${normalized}`, () => this.inner.getFinancials(normalized));
  }

  private async cached<T>(key: string, load: () => Promise<T>): Promise<T> {
    const hit = this.entries.get(key) as CacheEntry<T> | undefined;
    if (hit && hit.expiresAt > this.now()) return hit.value;
    const value = await load();
    this.entries.set(key, { value, expiresAt: this.now() + this.ttlMs });
    return value;
  }
}
