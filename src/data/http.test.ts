import { describe, expect, it, vi } from "vitest";

import {
  ProviderAuthError,
  ProviderQuotaExceededError,
  fetchJson,
  isRetryableProviderError,
} from "./http";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("provider http", () => {
  it("classifies 429 and 5xx as retryable, 401/403/404 as fatal", () => {
    expect(isRetryableProviderError(new ProviderQuotaExceededError("finnhub"))).toBe(true);
    expect(isRetryableProviderError(new ProviderAuthError("fmp"))).toBe(false);
    expect(isRetryableProviderError(new Error("boom"))).toBe(true);
  });

  it("returns parsed JSON on success without consuming quota twice", async () => {
    const fetchMock = vi.fn(async () => jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    try {
      const data = await fetchJson<{ ok: boolean }>("finnhub", "https://example.test/x", "key", {
        sleep: async () => {},
      });
      expect(data).toEqual({ ok: true });
      expect(fetchMock).toHaveBeenCalledTimes(1);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("throws quota error on 429 without retrying inside fetchJson", async () => {
    const fetchMock = vi.fn(async () => jsonResponse(429, { error: "limit" }));
    vi.stubGlobal("fetch", fetchMock);

    try {
      await expect(
        fetchJson("finnhub", "https://example.test/x", "key", { sleep: async () => {} }),
      ).rejects.toBeInstanceOf(ProviderQuotaExceededError);
      expect(fetchMock).toHaveBeenCalledTimes(1);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("throws auth error on 401/403", async () => {
    const fetchMock = vi.fn(async () => jsonResponse(401, { error: "unauthorized" }));
    vi.stubGlobal("fetch", fetchMock);

    try {
      await expect(
        fetchJson("fmp", "https://example.test/x", "key", { sleep: async () => {} }),
      ).rejects.toBeInstanceOf(ProviderAuthError);
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
