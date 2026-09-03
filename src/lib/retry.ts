export interface RetryOptions {
  maxAttempts?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
  isRetryable?: (error: unknown) => boolean;
  sleep?: (ms: number) => Promise<void>;
}

function defaultSleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

/**
 * Runs an async operation with exponential-backoff retries.
 * Defaults to 3 attempts starting at 200ms doubling each time.
 * Inject `sleep` in tests to avoid real timers.
 */
export async function withRetry<T>(operation: () => Promise<T>, options: RetryOptions = {}): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelayMs = 200,
    backoffFactor = 2,
    isRetryable = () => true,
    sleep = defaultSleep,
  } = options;

  let delayMs = initialDelayMs;
  let lastError: unknown;
  for (let attempt = 1; attempt <= Math.max(1, maxAttempts); attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      const hasMoreAttempts = attempt < Math.max(1, maxAttempts);
      if (!hasMoreAttempts || !isRetryable(error)) break;
      await sleep(delayMs);
      delayMs *= backoffFactor;
    }
  }
  throw lastError;
}
