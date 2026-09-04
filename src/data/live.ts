import { CompositeMarketDataProvider } from "./composite-provider";
import { FixtureMarketDataProvider, fixtureSearchIndex } from "./fixture-provider";
import type { MarketDataProvider } from "./market-data-provider";

let cached: MarketDataProvider | null = null;

/**
 * Server-only provider factory. Reads live keys from process.env once;
 * without keys it returns the deterministic fixture provider so builds
 * and tests stay reproducible.
 */
export function getMarketDataProvider(): MarketDataProvider {
  if (cached) return cached;
  cached = CompositeMarketDataProvider.fromEnv({
    FINNHUB_API_KEY: process.env.FINNHUB_API_KEY,
    FMP_API_KEY: process.env.FMP_API_KEY,
    ALPHAVANTAGE_API_KEY: process.env.ALPHAVANTAGE_API_KEY,
    COINGECKO_API_KEY: process.env.COINGECKO_API_KEY,
  });
  return cached;
}

export function getSearchIndex() {
  return fixtureSearchIndex;
}

export function isLiveProvider(provider: MarketDataProvider): boolean {
  return !(provider instanceof FixtureMarketDataProvider);
}
