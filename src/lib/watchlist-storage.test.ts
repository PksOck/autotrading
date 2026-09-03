import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  WATCHLIST_STORAGE_KEY,
  isWatchlisted,
  loadWatchlist,
  parseWatchlist,
  saveWatchlist,
  toggleWatchlistSymbol,
} from "./watchlist-storage";

describe("watchlist storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("exposes a versioned storage key", () => {
    expect(WATCHLIST_STORAGE_KEY).toBe("northstar-research:watchlist:v1");
  });

  it("normalizes, uppercases, and dedupes parsed symbols", () => {
    expect(parseWatchlist([" amzn ", "AMZN", "msft"])).toEqual(["AMZN", "MSFT"]);
  });

  it("falls back to an empty list for corrupt or foreign input", () => {
    expect(parseWatchlist(["AMZN", 42, null])).toEqual(["AMZN"]);
    expect(parseWatchlist({ nope: true })).toEqual([]);
    expect(parseWatchlist("AMZN")).toEqual([]);
    expect(parseWatchlist(JSON.parse('{"a":1}'))).toEqual([]);
  });

  it("toggles symbols case-insensitively", () => {
    expect(toggleWatchlistSymbol([], "amzn")).toEqual(["AMZN"]);
    expect(toggleWatchlistSymbol(["AMZN", "MSFT"], "amzn")).toEqual(["MSFT"]);
    expect(isWatchlisted(["MSFT"], "msft")).toBe(true);
    expect(isWatchlisted([], "AMZN")).toBe(false);
  });

  it("round-trips through localStorage", () => {
    saveWatchlist(["AMZN"]);
    expect(loadWatchlist()).toEqual(["AMZN"]);
  });

  it("loads an empty list when storage is empty or corrupt", () => {
    expect(loadWatchlist()).toEqual([]);
    window.localStorage.setItem(WATCHLIST_STORAGE_KEY, "not-json{{{");
    expect(loadWatchlist()).toEqual([]);
  });

  it("survives unavailable or throwing storage", () => {
    vi.spyOn(window.localStorage.__proto__, "getItem").mockImplementation(() => {
      throw new Error("denied");
    });
    expect(loadWatchlist()).toEqual([]);
    vi.restoreAllMocks();
    vi.spyOn(window.localStorage.__proto__, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() => saveWatchlist(["AMZN"])).not.toThrow();
  });
});
