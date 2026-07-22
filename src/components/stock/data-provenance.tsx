export function DataProvenance({ source, asOf }: { source: string; asOf: string }) {
  return (
    <aside className="provenance" aria-label="Data provenance">
      <span>Source: {source}</span>
      <span>As of: <time dateTime={asOf}>{new Date(asOf).toLocaleString("en-US", { timeZone: "UTC" })} UTC</time></span>
    </aside>
  );
}
