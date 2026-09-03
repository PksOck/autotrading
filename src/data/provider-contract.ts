import type { MarketDataProvider } from "./market-data-provider";

function fail(message: string): never {
  throw new Error(`Market data contract violation: ${message}`);
}

function assertIsoUtcTimestamp(value: string, label: string): void {
  const time = new Date(value).getTime();
  if (!Number.isFinite(time) || !/Z$|[+-]00:00$/.test(value)) {
    fail(`${label} must be an ISO-8601 UTC timestamp, got ${JSON.stringify(value)}`);
  }
}

/**
 * Vendor-neutral contract every MarketDataProvider must satisfy.
 * The fixture provider passes today; a future licensed provider
 * reuses this same suite before replacing the fixture implementation.
 */
export async function assertMarketDataContract(
  provider: MarketDataProvider,
  options: { supportedSymbol: string; unsupportedSymbol: string },
): Promise<void> {
  const { supportedSymbol, unsupportedSymbol } = options;

  const results = await provider.searchInstruments(supportedSymbol.slice(0, 2));
  if (!Array.isArray(results) || results.length === 0) {
    fail("search must return at least one result for a known symbol prefix");
  }
  for (const result of results) {
    if (!result.symbol.trim() || !result.name.trim() || !result.venue.trim()) {
      fail("search results must carry symbol, name, and venue");
    }
  }

  const snapshot = await provider.getInstrumentSnapshot(` ${supportedSymbol.toLowerCase()} `);
  if (!snapshot.quoteCurrency.trim()) fail("snapshot must carry a currency");
  if (!(snapshot.price > 0)) fail("snapshot price must be positive");
  if (!snapshot.source.trim()) fail("snapshot must carry a source");
  assertIsoUtcTimestamp(snapshot.asOf, "snapshot asOf");

  const maximumHistory = await provider.getPriceHistory(supportedSymbol, "MAX");
  if (maximumHistory.length === 0) fail("MAX history must not be empty");
  const seen = new Set<string>();
  let previous = Number.NEGATIVE_INFINITY;
  for (const point of maximumHistory) {
    assertIsoUtcTimestamp(point.timestamp, "price timestamp");
    if (seen.has(point.timestamp)) fail(`duplicate price timestamp ${point.timestamp}`);
    seen.add(point.timestamp);
    const time = new Date(point.timestamp).getTime();
    if (time < previous) fail("price history must sort ascending");
    previous = time;
    if (time > new Date(snapshot.asOf).getTime()) fail("price history cannot postdate snapshot provenance");
    if (!(point.close > 0)) fail("price closes must be positive");
    if (point.volume !== null && !(point.volume >= 0)) fail("volume must be null or non-negative");
  }

  const shortHistory = await provider.getPriceHistory(supportedSymbol, "1M");
  if (shortHistory.length === 0 || shortHistory.length > maximumHistory.length) {
    fail("1M history must be a non-empty subset of MAX history");
  }
  if (shortHistory.at(-1)?.timestamp !== maximumHistory.at(-1)?.timestamp) {
    fail("ranged history must share the latest MAX observation");
  }

  const financials = await provider.getFinancials(supportedSymbol);
  if (financials !== null) {
    if (!financials.currency.trim() || !financials.unit.trim() || !financials.source.trim()) {
      fail("financials must carry currency, unit, and source");
    }
    assertIsoUtcTimestamp(financials.asOf, "financials asOf");
  }

  for (const method of ["getInstrumentSnapshot", "getPriceHistory", "getFinancials"] as const) {
    try {
      if (method === "getInstrumentSnapshot") await provider.getInstrumentSnapshot(unsupportedSymbol);
      if (method === "getPriceHistory") await provider.getPriceHistory(unsupportedSymbol, "MAX");
      if (method === "getFinancials") await provider.getFinancials(unsupportedSymbol);
      fail(`${method} must reject unknown symbols with a typed error`);
    } catch (error) {
      const name = (error as Error)?.constructor?.name ?? "";
      if (name !== "MarketDataNotFoundError") throw error;
    }
  }
}
