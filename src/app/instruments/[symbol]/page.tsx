import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { DataProvenance } from "@/components/stock/data-provenance";
import { PriceChart } from "@/components/charts/price-chart";
import { BacktestSection, TechnicalsSection } from "@/components/quant/research-sections";
import { FinancialTrends } from "@/components/stock/financial-trends";
import { MetricCard } from "@/components/stock/metric-card";
import { StockHeader } from "@/components/stock/stock-header";
import { ValuationSection } from "@/components/valuation/valuation-section";
import { WatchlistButton } from "@/components/watchlist/watchlist-button";
import { MarketDataNotFoundError } from "@/data/market-data-errors";
import { getMarketDataProvider } from "@/data/live";
import { normalizeSymbol } from "@/lib/market-data";
import { compareStrategies, summarizeTechnicals } from "@/quant/research";

const provider = getMarketDataProvider();

export function generateStaticParams() { return [{ symbol: "AMZN" }]; }

export async function generateMetadata({ params }: { params: Promise<{ symbol: string }> }): Promise<Metadata> {
  const symbol = normalizeSymbol((await params).symbol);
  try {
    const snapshot = await provider.getInstrumentSnapshot(symbol);
    return { title: `${snapshot.symbol} ${snapshot.name}` };
  } catch {
    return { title: symbol };
  }
}

export default async function InstrumentPage({ params }: { params: Promise<{ symbol: string }> }) {
  const symbol = normalizeSymbol((await params).symbol);
  try {
    const [snapshot, financials, priceHistory] = await Promise.all([
      provider.getInstrumentSnapshot(symbol),
      provider.getFinancials(symbol),
      provider.getPriceHistory(symbol, "MAX"),
    ]);
    const stockMetrics = snapshot.stockMetrics;
    const annualPeriods = financials?.annual ?? [];
    const latestFcfPeriod = [...annualPeriods].reverse().find((period) => period.freeCashFlow !== null);
    const technicals = summarizeTechnicals(priceHistory);
    const backtest = compareStrategies(priceHistory);
    return (
      <main className="page-shell stock-page">
        <StockHeader snapshot={snapshot} />
        <WatchlistButton symbol={snapshot.symbol} />
        <DataProvenance source={snapshot.source} asOf={snapshot.asOf} />
        <PriceChart points={priceHistory} currency={snapshot.quoteCurrency} source={snapshot.source} asOf={snapshot.asOf} initialRange="1Y" />
        <TechnicalsSection summary={technicals} currency={snapshot.quoteCurrency} />
        {backtest ? <BacktestSection comparison={backtest} /> : null}
        {stockMetrics ? <section className="data-section"><h2>Market snapshot</h2><dl className="metric-grid">
          <MetricCard label="Market cap" value={stockMetrics.marketCap} unit="currency" currency={snapshot.quoteCurrency} />
          <MetricCard label="Enterprise value" value={stockMetrics.enterpriseValue} unit="currency" currency={snapshot.quoteCurrency} />
          <MetricCard label="P/E" value={stockMetrics.peRatio} unit="multiple" currency={snapshot.quoteCurrency} />
          <MetricCard label="EV/EBITDA" value={stockMetrics.evToEbitda} unit="multiple" currency={snapshot.quoteCurrency} />
          <MetricCard label="FCF yield" value={stockMetrics.fcfYield} unit="percent" currency={snapshot.quoteCurrency} />
        </dl></section> : null}
        {financials ? <>
          <FinancialTrends title="Annual financials" periods={financials.annual} currency={financials.currency} unit={financials.unit} />
          <FinancialTrends title="Quarterly financials" periods={financials.quarterly} currency={financials.currency} unit={financials.unit} />
          <ValuationSection
            currency={financials.currency}
            unit={financials.unit}
            latestFcf={latestFcfPeriod && latestFcfPeriod.freeCashFlow !== null
              ? { value: latestFcfPeriod.freeCashFlow, period: latestFcfPeriod.period }
              : null}
            dilutedShares={annualPeriods.length > 0 ? annualPeriods[annualPeriods.length - 1].dilutedShares : null}
          />
        </> : <section className="data-section"><h2>Fundamentals</h2><p>Fundamentals are not available for this instrument type</p></section>}
        <section className="limitations"><h2>Risks and limitations</h2><p>Illustrative fixture data can be stale or incomplete. This page is research information, not a recommendation or target price.</p></section>
      </main>
    );
  } catch (error) {
    if (error instanceof MarketDataNotFoundError) notFound();
    throw error;
  }
}
