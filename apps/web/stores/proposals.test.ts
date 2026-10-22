import { parseSymbols } from "./proposals";

describe("parseSymbols", () => {
  it("normalizes, dedupes and drops noise", () => {
    expect(parseSymbols("msft, asml  $nvda; msft brk.b 123")).toEqual(["MSFT", "ASML", "NVDA", "BRK.B"]);
  });
});
