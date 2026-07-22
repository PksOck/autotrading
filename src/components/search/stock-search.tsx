"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { StockSearchResult } from "@/domain/stock";

export function StockSearch({ initialResults }: { initialResults: StockSearchResult[] }) {
  const [query, setQuery] = useState("");
  const matches = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return [];
    return initialResults.filter(
      ({ symbol, companyName }) =>
        symbol.toLowerCase().includes(normalized) ||
        companyName.toLowerCase().includes(normalized),
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
              <Link href={`/stocks/${result.symbol}`}>
                <strong>{result.symbol}</strong> {result.companyName} · {result.exchange}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
