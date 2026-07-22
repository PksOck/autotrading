export class MarketDataNotFoundError extends Error {
  constructor(symbol: string) {
    super(`No fixture data exists for ${symbol}.`);
    this.name = "MarketDataNotFoundError";
  }
}
