"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fixtureSearchIndex } from "@/data/fixture-provider";
import { loadWatchlist, saveWatchlist } from "@/lib/watchlist-storage";

export default function WatchlistPage() {
  const [symbols, setSymbols] = useState<string[] | null>(null);

  useEffect(() => {
    setSymbols(loadWatchlist());
  }, []);

  if (symbols === null) {
    return (
      <main className="page-shell stock-page">
        <h1>Watchlist</h1>
        <p role="status">Loading watchlist…</p>
      </main>
    );
  }

  return (
    <main className="page-shell stock-page">
      <p className="eyebrow">Saved on this device</p>
      <h1>Watchlist</h1>
      {symbols.length === 0 ? (
        <p>
          Your watchlist is empty. Search for an instrument and use the watch button to save it
          here.
        </p>
      ) : (
        <ul className="watchlist-list">
          {symbols.map((symbol) => {
            const known = fixtureSearchIndex.find((entry) => entry.symbol === symbol);
            return (
              <li key={symbol}>
                <div>
                  <strong>{symbol}</strong>{" "}
                  {known ? (
                    <Link href={`/instruments/${symbol}`}>{known.name}</Link>
                  ) : (
                    <span>Detail not available for this symbol</span>
                  )}
                </div>
                <button
                  type="button"
                  aria-label={`Remove ${symbol} from watchlist`}
                  onClick={() => {
                    const next = symbols.filter((entry) => entry !== symbol);
                    saveWatchlist(next);
                    setSymbols(next);
                  }}
                >
                  Remove
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
