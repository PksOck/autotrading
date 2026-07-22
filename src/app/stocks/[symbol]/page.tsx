import { notFound } from "next/navigation";

import { DataProvenance } from "@/components/stock/data-provenance";
import { FinancialTrends } from "@/components/stock/financial-trends";
import { MetricCard } from "@/components/stock/metric-card";
import { StockHeader } from "@/components/stock/stock-header";
import { FixtureMarketDataProvider } from "@/data/fixture-provider";
import { MarketDataNotFoundError } from "@/data/market-data-errors";
import { isStale, normalizeSymbol } from "@/lib/market-data";

const provider = new FixtureMarketDataProvider();

export function generateStaticParams() { return [{ symbol: "AMZN" }]; }

export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  const symbol = normalizeSymbol((await params).symbol);
  try {
    const [snapshot, financials] = await Promise.all([
      provider.getStockSnapshot(symbol),
      provider.getFinancials(symbol),
    ]);
    return (
      <main className="page-shell stock-page">
        <StockHeader snapshot={snapshot} stale={isStale(snapshot.asOf, new Date(), 48)} />
        <DataProvenance source={snapshot.source} asOf={snapshot.asOf} />
        <section className="data-section"><h2>Market snapshot</h2><dl className="metric-grid">
          <MetricCard label="Market cap" value={snapshot.marketCap} unit="currency" currency={snapshot.currency} />
          <MetricCard label="Enterprise value" value={snapshot.enterpriseValue} unit="currency" currency={snapshot.currency} />
          <MetricCard label="P/E" value={snapshot.peRatio} unit="multiple" currency={snapshot.currency} />
          <MetricCard label="EV/EBITDA" value={snapshot.evToEbitda} unit="multiple" currency={snapshot.currency} />
          <MetricCard label="FCF yield" value={snapshot.fcfYield} unit="percent" currency={snapshot.currency} />
        </dl></section>
        <FinancialTrends title="Annual financials" periods={financials.annual} currency={financials.currency} unit={financials.unit} />
        <FinancialTrends title="Quarterly financials" periods={financials.quarterly} currency={financials.currency} unit={financials.unit} />
        <section className="limitations"><h2>Risks and limitations</h2><p>Illustrative fixture data can be stale or incomplete. This page is research information, not a recommendation or target price.</p></section>
      </main>
    );
  } catch (error) {
    if (error instanceof MarketDataNotFoundError) notFound();
    throw error;
  }
}
