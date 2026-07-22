import { permanentRedirect } from "next/navigation";

import { normalizeSymbol } from "@/lib/market-data";

export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  return permanentRedirect(`/instruments/${normalizeSymbol((await params).symbol)}`);
}
