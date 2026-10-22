import { formatChange, formatMoney, formatNumber } from "./format";

describe("format", () => {
  it("uses Slovenian separators", () => {
    expect(formatNumber("sl", 12345.5, 2)).toBe("12.345,50");
    expect(formatNumber("sl", 1234.5, 2)).toBe("1.234,50");
    expect(formatNumber("en", 1234.5, 2)).toBe("1,234.50");
  });

  it("always signs changes and adds an arrow", () => {
    expect(formatChange("sl", 2.14).replace(/\s/g, " ")).toBe("▲ +2,1 %");
    expect(formatChange("en", -3.44)).toBe("▼ −3.4%");
  });

  it("formats money in the quote currency", () => {
    expect(formatMoney("en", 406.8)).toBe("$406.80");
    expect(formatMoney("sl", 406.8).replace(/\s/g, " ")).toBe("406,80 $");
  });
});
