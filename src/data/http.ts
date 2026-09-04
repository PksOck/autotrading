import { withRetry } from "@/lib/retry";

export class ProviderQuotaExceededError extends Error {
  constructor(readonly provider: string) {
    super(`Quota exceeded for ${provider}.`);
    this.name = "ProviderQuotaExceededError";
  }
}

export class ProviderAuthError extends Error {
  constructor(readonly provider: string) {
    super(`Authentication failed for ${provider}. Check the server-side API key.`);
    this.name = "ProviderAuthError";
  }
}

export function isRetryableProviderError(error: unknown): boolean {
  if (error instanceof ProviderAuthError) return false;
  if (error instanceof ProviderQuotaExceededError) return true;
  return true;
}

export interface FetchJsonOptions {
  sleep?: (ms: number) => Promise<void>;
  maxAttempts?: number;
}

/**
 * Server-only JSON GET with provider-aware error mapping.
 * Retry policy lives with the caller via withRetry; fetchJson itself
 * performs exactly one attempt so quota accounting stays exact.
 */
export async function fetchJson<T>(
  provider: string,
  url: string,
  apiKey: string,
  options: FetchJsonOptions = {},
): Promise<T> {
  if (!apiKey) throw new ProviderAuthError(provider);

  const response = await fetch(url);
  if (response.status === 429) throw new ProviderQuotaExceededError(provider);
  if (response.status === 401 || response.status === 403) throw new ProviderAuthError(provider);
  if (response.status === 404) {
    const { MarketDataNotFoundError } = await import("./market-data-errors");
    throw new MarketDataNotFoundError(url);
  }
  if (!response.ok) throw new Error(`Provider ${provider} request failed with ${response.status}.`);

  return (await response.json()) as T;
}

export async function fetchJsonWithRetry<T>(
  provider: string,
  url: string,
  apiKey: string,
  options: FetchJsonOptions = {},
): Promise<T> {
  return withRetry(() => fetchJson<T>(provider, url, apiKey, options), {
    maxAttempts: options.maxAttempts ?? 3,
    sleep: options.sleep,
    isRetryable: isRetryableProviderError,
  });
}
