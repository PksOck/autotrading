import { beforeEach, describe, expect, it } from "vitest";

import { QuotaTracker } from "./quota-tracker";

describe("QuotaTracker", () => {
  beforeEach(() => {
    QuotaTracker.resetAllForTests();
  });

  it("allows consumption within the daily limit", () => {
    const tracker = new QuotaTracker({ fmp: 10 }, () => new Date("2026-09-04T10:00:00Z"));

    expect(tracker.canConsume("fmp")).toBe(true);
    expect(tracker.consume("fmp")).toBe(true);
    expect(tracker.remaining("fmp")).toBe(9);
  });

  it("blocks consumption once the daily limit is exhausted", () => {
    const tracker = new QuotaTracker({ av: 2 }, () => new Date("2026-09-04T10:00:00Z"));

    expect(tracker.consume("av")).toBe(true);
    expect(tracker.consume("av")).toBe(true);
    expect(tracker.consume("av")).toBe(false);
    expect(tracker.canConsume("av")).toBe(false);
    expect(tracker.remaining("av")).toBe(0);
  });

  it("resets counters on calendar day rollover (UTC)", () => {
    let now = new Date("2026-09-04T23:59:00Z");
    const tracker = new QuotaTracker({ av: 1 }, () => now);

    expect(tracker.consume("av")).toBe(true);
    expect(tracker.canConsume("av")).toBe(false);

    now = new Date("2026-09-05T00:01:00Z");
    expect(tracker.canConsume("av")).toBe(true);
    expect(tracker.remaining("av")).toBe(1);
  });

  it("treats unknown providers as unlimited", () => {
    const tracker = new QuotaTracker({}, () => new Date("2026-09-04T10:00:00Z"));

    expect(tracker.canConsume("fred")).toBe(true);
    expect(tracker.consume("fred")).toBe(true);
    expect(tracker.remaining("fred")).toBe(Number.POSITIVE_INFINITY);
  });
});
