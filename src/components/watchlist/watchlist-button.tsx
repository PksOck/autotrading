"use client";

import { useEffect, useState } from "react";

import { normalizeSymbol } from "@/lib/market-data";
import { isWatchlisted, loadWatchlist, saveWatchlist, toggleWatchlistSymbol } from "@/lib/watchlist-storage";

export function WatchlistButton({ symbol }: { symbol: string }) {
  const normalized = normalizeSymbol(symbol);
  const [watched, setWatched] = useState(false);

  useEffect(() => {
    setWatched(isWatchlisted(loadWatchlist(), normalized));
  }, [normalized]);

  return (
    <button
      type="button"
      className="watchlist-button"
      aria-pressed={watched}
      aria-label={watched ? `Remove ${normalized} from watchlist` : `Add ${normalized} to watchlist`}
      onClick={() => {
        const next = toggleWatchlistSymbol(loadWatchlist(), normalized);
        saveWatchlist(next);
        setWatched(isWatchlisted(next, normalized));
      }}
    >
      {watched ? `★ Watching ${normalized}` : `☆ Watch ${normalized}`}
    </button>
  );
}
