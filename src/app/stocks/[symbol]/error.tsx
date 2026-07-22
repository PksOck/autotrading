"use client";
export default function StockError({ reset }: { error: Error; reset: () => void }) { return <main className="page-shell stock-page"><h1>Data unavailable</h1><p>The validated fixture could not be loaded.</p><button type="button" onClick={reset}>Try again</button></main>; }
