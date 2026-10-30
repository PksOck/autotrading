import { fireEvent, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import messages from "@/messages/en.json";
import fragment from "@/messages/en.json";
import { PositionsPanel } from "./PositionsPanel";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/portfolio",
  useRouter: () => ({ replace: vi.fn() }),
}));
vi.mock("@/components/common/EntityLink", () => ({ EntityLink: () => <span>ABC</span> }));
vi.mock("@/components/table/MetricCell", () => ({ DataQualityBadges: () => null }));
vi.mock("@/components/table/market-columns", () => ({ useMarketColumns: () => [] }));
vi.mock("@/lib/api/hooks", () => ({
  useEntries: () => ({ data: [] }),
  usePortfolioImport: () => ({}),
  usePortfolioSync: () => ({}),
  usePortfolio: () => ({
    data: {
      total_value: 1000,
      base_currency: "USD",
      source: "ibkr_flex",
      cash: [],
      as_of: "2026-10-28T00:00:00Z",
      positions: [
        {
          symbol: "ABC",
          name: "ABC Corp",
          currency: "USD",
          quantity: 10,
          market_price: 100,
          market_value: 1000,
          weight_pct: 100,
          unrealized_pnl: -25,
          change_pct: 2,
          report_date: "2026-10-27",
          account_id: "ACCOUNT",
          price_meta: { source: "yahoo", market_date: "2026-10-28" },
          price_trend: {
            points: [
              { close: 99, market_date: "2026-10-27" },
              { close: 100, market_date: "2026-10-28" },
            ],
            source: "yahoo",
            as_of: "2026-10-29T08:00:00Z",
          },
        },
      ],
    },
  }),
}));

it("restores position defaults and retains signed colors and separate daily and snapshot dates", () => {
  localStorage.clear();
  render(
    <NextIntlClientProvider
      locale="en"
      messages={{ ...messages, table: { ...messages.table, ...fragment.table } }}
    >
      <PositionsPanel />
    </NextIntlClientProvider>,
  );
  const expected = [
    messages.table.instrument,
    messages.portfolio.col.quantity,
    messages.table.snapshotPrice,
    messages.portfolio.col.value,
    messages.portfolio.col.weight,
    messages.portfolio.col.pnl,
    messages.table.daily,
    messages.table.actions,
  ];
  expect(
    screen.getAllByRole("columnheader").map((cell) => cell.textContent?.replace(/ ↕$/, "")),
  ).toEqual(expected);
  fireEvent.click(screen.getByRole("button", { name: messages.table.valuation }));
  fireEvent.click(screen.getByRole("button", { name: "Standard" }));
  expect(
    screen.getAllByRole("columnheader").map((cell) => cell.textContent?.replace(/ ↕$/, "")),
  ).toEqual(expected);
  expect(screen.getByText(/▼.*−.*25/)).toHaveClass("text-neg");
  expect(screen.getByText(/▲.*\+.*2/)).toHaveClass("text-pos");
  const cells = screen.getAllByRole("cell");
  expect(within(cells[2]!).getByText("2026-10-27")).toBeInTheDocument();
  expect(within(cells[6]!).getByText("2026-10-28")).toHaveAttribute("title", "yahoo");
  expect(screen.getByText("Up to 30 trading sessions")).toBeInTheDocument();
});
