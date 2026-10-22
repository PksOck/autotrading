import { InstrumentView } from "@/components/instrument/InstrumentView";

/** SCR-05 Instrument (BL-029). */
export default async function InstrumentPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  return <InstrumentView symbol={decodeURIComponent(symbol).toUpperCase()} />;
}
