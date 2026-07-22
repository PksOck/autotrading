import { describe, expect, it } from "vitest";

import { isStale, normalizeSymbol } from "./market-data";

describe("normalizeSymbol", () => {
  it("trims whitespace and uppercases symbols", () => {
    expect(normalizeSymbol(" amzn ")).toBe("AMZN");
  });
});

describe("isStale", () => {
  it("is stale only after the maximum age", () => {
    const now = new Date("2026-07-22T12:01:00Z");
    expect(isStale("2026-07-20T12:00:00Z", now, 48)).toBe(true);
    expect(isStale("2026-07-20T12:01:00Z", now, 48)).toBe(false);
  });
});
