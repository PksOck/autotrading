import { describe, expect, it } from "vitest";
import { selectedEntry, analysisFilters, eventConfirmation } from "./research-state";

describe("research navigation", () => {
  it("never replaces a missing explicit selection with the first entry", () => {
    const items = [{ symbol: "ASML" }];
    expect(selectedEntry(items, "MISSING")).toBeNull();
    expect(selectedEntry(items, null)).toEqual(items[0]);
    expect(selectedEntry(items, "asml")).toEqual(items[0]);
  });
  it("selects latest successful runs by default and preserves explicit all histories", () => {
    expect(analysisFilters(new URLSearchParams())).toMatchObject({status: "done", latest_per_instrument: true});
    expect(analysisFilters(new URLSearchParams("status=all&latest=false"))).toMatchObject({status: undefined, latest_per_instrument: false});
  });
  it("requires official source evidence to call a non-rumor event verified", () => {
    expect(eventConfirmation({is_rumor:false,sources:[{kind:"news"}]})).toBe("unverified");
    expect(eventConfirmation({is_rumor:false,sources:[{kind:"filing"}]})).toBe("verified");
    expect(eventConfirmation({is_rumor:true,sources:[{kind:"filing"}]})).toBe("rumor");
  });
});
