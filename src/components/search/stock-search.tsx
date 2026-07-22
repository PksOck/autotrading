"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { InstrumentSearchResult } from "@/domain/instrument";

export function StockSearch({ initialResults }: { initialResults: InstrumentSearchResult[] }) {
  const [query, setQuery] = useState("");
  const matches = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return [];
    return initialResults.filter(
      ({ symbol, name }) =>
        symbol.toLowerCase().includes(normalized) ||
        name.toLowerCase().includes(normalized),
    );
  }, [initialResults, query]);

  return (
    <div className="search-panel">
      <label htmlFor="stock-search">Symbol or company name</label>
      <input
        id="stock-search"
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Try AMZN or Amazon"
      />
      {!query.trim() ? (
        <p className="search-help">Enter a symbol or company name</p>
      ) : matches.length === 0 ? (
        <p className="search-help">No fixture matches</p>
      ) : (
        <ul className="search-results">
          {matches.map((result) => (
            <li key={result.symbol}>
              <Link href={`/instruments/${result.symbol}`}>
                <strong>{result.symbol}</strong> {result.name} · {result.venue}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
