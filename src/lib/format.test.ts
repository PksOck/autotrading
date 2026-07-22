import { describe, expect, it } from "vitest";

import { formatCompactNumber, formatCurrency, formatMultiple, formatPercent } from "./format";

describe("financial formatters", () => {
  it("does not coerce missing values to zero", () => {
    expect(formatCurrency(null, "USD")).toBe("Not available");
    expect(formatPercent(null)).toBe("Not available");
    expect(formatMultiple(null)).toBe("Not available");
    expect(formatCompactNumber(null)).toBe("Not available");
  });

  it("formats supported financial values", () => {
    expect(formatCurrency(217.35, "USD")).toBe("$217.35");
    expect(formatPercent(0.0342)).toBe("3.42%");
    expect(formatMultiple(42.25)).toBe("42.3×");
    expect(formatCompactNumber(2_310_000_000_000)).toBe("2.31T");
  });
});
