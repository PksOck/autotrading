import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import messages from "@/messages/en.json";
import fragment from "@/messages/en.json";
import { WatchlistPanel } from "./WatchlistPanel";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/watchlist",
  useRouter: () => ({ replace: vi.fn() }),
}));
vi.mock("@/components/common/EntityLink", () => ({ EntityLink: () => <span>ABC</span> }));
vi.mock("@/components/table/MetricCell", () => ({ DataQualityBadges: () => null }));
vi.mock("@/components/table/market-columns", () => ({ useMarketColumns: () => [] }));
vi.mock("@/lib/api/hooks", () => ({
  useEntries: () => ({
    data: [
      {
        symbol: "ABC",
        price: 10,
        zone_low: 9,
        zone_high: 11,
        source: "rules",
        as_of: "2026-10-28",
      },
    ],
  }),
  useWatchlistMutations: () => ({ add: {}, update: {}, remove: {}, restore: {} }),
  useWatchlist: () => ({
    data: [
      {
        id: 1,
        symbol: "ABC",
        name: "ABC Corp",
        currency: "USD",
        tier: "active",
        reviewed_at: null,
        last_close: 10,
        change_pct: -2,
        since_added_pct: 10,
        added_at: "2026-10-01T00:00:00Z",
        price_meta: { source: "yahoo", market_date: "2026-10-28" },
        price_trend: {
          points: [
            { close: 9, market_date: "2026-10-27" },
            { close: 10, market_date: "2026-10-28" },
          ],
          source: "yahoo",
          as_of: "2026-10-29T08:00:00Z",
        },
      },
    ],
  }),
}));

it("restores watchlist trend and real entry context with signed daily and since-added colors", () => {
  localStorage.clear();
  render(
    <NextIntlClientProvider
      locale="en"
      messages={{ ...messages, table: { ...messages.table, ...fragment.table } }}
    >
      <WatchlistPanel />
    </NextIntlClientProvider>,
  );
  expect(screen.getByText(/▼.*−.*2/)).toHaveClass("text-neg");
  expect(screen.getByText(/▲.*\+.*10/)).toHaveClass("text-pos");
  expect(screen.getByText("In zone")).toHaveClass("text-pos");
  expect(screen.getByText("In zone")).toHaveAttribute("title", "rules · 2026-10-28");
  expect(screen.getByText("Up to 30 trading sessions")).toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: "Standard" })).toHaveLength(2);
});
