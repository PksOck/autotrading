import type { FinancialSeries } from "@/domain/financials";
import type { InstrumentSearchResult, InstrumentSnapshot } from "@/domain/instrument";
import type { PricePoint, PriceRange } from "@/domain/price-history";
import { normalizeSymbol } from "@/lib/market-data";

import { AlphaVantageProvider } from "./alphavantage-provider";
import { CachedMarketDataProvider } from "./cached-provider";
import { CoinGeckoProvider, coinIdForSymbol } from "./coingecko-provider";
import { FinnhubProvider } from "./finnhub-provider";
import { FixtureMarketDataProvider } from "./fixture-provider";
import { FmpProvider } from "./fmp-provider";
import { MarketDataNotFoundError } from "./market-data-errors";
import type { MarketDataProvider } from "./market-data-provider";
import { QuotaTracker } from "./quota-tracker";

export interface CompositeDeps {
  crypto: MarketDataProvider;
  primary: MarketDataProvider;
  fallback: MarketDataProvider;
  fundamentals: MarketDataProvider;
  fixture?: MarketDataProvider;
}

export interface LiveEnv {
  FINNHUB_API_KEY?: string;
  FMP_API_KEY?: string;
  ALPHAVANTAGE_API_KEY?: string;
  COINGECKO_API_KEY?: string;
}

function isNotFound(error: unknown): boolean {
  return error instanceof MarketDataNotFoundError || (error as Error)?.name === "MarketDataNotFoundError";
}

/**
 * Routes by instrument class with quota-aware fallbacks:
 * crypto -> CoinGecko; stocks -> Finnhub primary, AlphaVantage fallback;
 * fundamentals -> FMP; everything degrades to fixture when no key is set.
 */
export class CompositeMarketDataProvider implements MarketDataProvider {
  constructor(private readonly deps: CompositeDeps, private readonly quotas = new QuotaTracker({})) {}

  static fromEnv(env: LiveEnv): MarketDataProvider {
    const hasLiveKey = env.FINNHUB_API_KEY || env.FMP_API_KEY || env.ALPHAVANTAGE_API_KEY || env.COINGECKO_API_KEY;
    if (!hasLiveKey) return new FixtureMarketDataProvider();

    const quotas = new QuotaTracker({ fmp: 10, alphavantage: 25 });
    const finnhub = new CachedMarketDataProvider(new FinnhubProvider(env.FINNHUB_API_KEY ?? ""), 60_000);
    const fallback = new CachedMarketDataProvider(new AlphaVantageProvider(env.ALPHAVANTAGE_API_KEY ?? ""), 86_400_000);
    const fundamentals = new CachedMarketDataProvider(new FmpProvider(env.FMP_API_KEY ?? ""), 30 * 86_400_000);
    const crypto = new CachedMarketDataProvider(new CoinGeckoProvider(env.COINGECKO_API_KEY ?? ""), 300_000);
    return new CompositeMarketDataProvider(
      { crypto, primary: finnhub, fallback, fundamentals, fixture: new FixtureMarketDataProvider() },
      quotas,
    );
  }

  private isCrypto(symbol: string): boolean {
    return coinIdForSymbol(symbol) !== null;
  }

  async searchInstruments(query: string): Promise<InstrumentSearchResult[]> {
    try {
      const results = await this.deps.primary.searchInstruments(query);
      if (results.length > 0) return results;
    } catch { /* fall through to crypto + fixture */ }
    const crypto = await this.deps.crypto.searchInstruments(query).catch(() => []);
    if (crypto.length > 0) return crypto;
    return this.deps.fixture?.searchInstruments(query) ?? [];
  }

  async getInstrumentSnapshot(symbol: string): Promise<InstrumentSnapshot> {
    const normalized = normalizeSymbol(symbol);
    if (this.isCrypto(normalized)) return this.deps.crypto.getInstrumentSnapshot(normalized);

    try {
      return await this.deps.primary.getInstrumentSnapshot(normalized);
    } catch (error) {
      if (!isNotFound(error)) throw error;
    }
    try {
      return await this.deps.fundamentals.getInstrumentSnapshot(normalized);
    } catch (error) {
      if (!isNotFound(error)) throw error;
    }
    if (this.deps.fixture) return this.deps.fixture.getInstrumentSnapshot(normalized);
    throw new MarketDataNotFoundError(normalized);
  }

  async getPriceHistory(symbol: string, range: PriceRange): Promise<PricePoint[]> {
    const normalized = normalizeSymbol(symbol);
    if (this.isCrypto(normalized)) return this.deps.crypto.getPriceHistory(normalized, range);

    try {
      return await this.deps.primary.getPriceHistory(normalized, range);
    } catch (error) {
      if (!isNotFound(error)) throw error;
    }
    try {
      return await this.deps.fallback.getPriceHistory(normalized, range);
    } catch (error) {
      if (!isNotFound(error)) throw error;
    }
    if (this.deps.fixture) return this.deps.fixture.getPriceHistory(normalized, range);
    throw new MarketDataNotFoundError(normalized);
  }

  async getFinancials(symbol: string): Promise<FinancialSeries | null> {
    const normalized = normalizeSymbol(symbol);
    if (this.isCrypto(normalized)) return null;
    try {
      const financials = await this.deps.fundamentals.getFinancials(normalized);
      if (financials) return financials;
    } catch (error) {
      if (!isNotFound(error)) throw error;
    }
    return this.deps.fixture?.getFinancials(normalized) ?? null;
  }
}
