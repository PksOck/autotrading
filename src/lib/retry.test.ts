import { describe, expect, it, vi } from "vitest";

import { withRetry } from "./retry";

describe("withRetry", () => {
  it("resolves on the first attempt without sleeping", async () => {
    const sleep = vi.fn().mockResolvedValue(undefined);
    const operation = vi.fn().mockResolvedValue("ok");

    await expect(withRetry(operation, { sleep })).resolves.toBe("ok");
    expect(operation).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });

  it("retries with exponential backoff until success", async () => {
    const sleep = vi.fn().mockResolvedValue(undefined);
    const operation = vi
      .fn()
      .mockRejectedValueOnce(new Error("boom-1"))
      .mockRejectedValueOnce(new Error("boom-2"))
      .mockResolvedValue("recovered");

    await expect(
      withRetry(operation, { maxAttempts: 3, initialDelayMs: 200, backoffFactor: 2, sleep }),
    ).resolves.toBe("recovered");
    expect(operation).toHaveBeenCalledTimes(3);
    expect(sleep.mock.calls.map(([ms]) => ms)).toEqual([200, 400]);
  });

  it("throws the last error after exhausting attempts", async () => {
    const sleep = vi.fn().mockResolvedValue(undefined);
    const operation = vi.fn().mockRejectedValue(new Error("persistent"));

    await expect(withRetry(operation, { maxAttempts: 2, sleep })).rejects.toThrow("persistent");
    expect(operation).toHaveBeenCalledTimes(2);
  });

  it("does not retry errors the caller marks fatal", async () => {
    const sleep = vi.fn().mockResolvedValue(undefined);
    const operation = vi.fn().mockRejectedValue(new Error("fatal"));

    await expect(
      withRetry(operation, { isRetryable: () => false, sleep }),
    ).rejects.toThrow("fatal");
    expect(operation).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });
});
