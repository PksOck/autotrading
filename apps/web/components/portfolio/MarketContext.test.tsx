import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { SignedChange, PriceTrend, EntryZoneBadge } from "./MarketContext";

const show = (children: React.ReactNode) =>
  render(
    <NextIntlClientProvider
      locale="en"
      messages={{
        table: {
          trendPeriod: "Up to 30 trading sessions",
          trendSamples: "{count} sessions",
          trendUnknown: "Trend unavailable",
          zoneUnknown: "Entry zone unknown",
          inZone: "In zone",
          outsideZone: "Outside zone",
        },
      }}
    >
      {children}
    </NextIntlClientProvider>,
  );

it("pairs semantic colors with signs and arrows, and leaves missing values neutral", () => {
  show(
    <>
      <SignedChange value={12} currency="USD" />
      <SignedChange value={-2} />
      <SignedChange value={null} />
    </>,
  );
  expect(screen.getByText(/▲.*\+.*12/)).toHaveClass("text-pos");
  expect(screen.getByText(/▼.*−.*2/)).toHaveClass("text-neg");
  expect(screen.getByText("—")).not.toHaveClass("text-pos", "text-neg");
});

it("identifies the actual trend period, sample count and provenance", () => {
  show(
    <PriceTrend
      trend={{
        points: [
          { close: 10, market_date: "2026-10-27" },
          { close: 11, market_date: "2026-10-28" },
        ],
        source: "yahoo",
        as_of: "2026-10-29T08:00:00Z",
      }}
    />,
  );
  expect(screen.getByText("Up to 30 trading sessions")).toBeInTheDocument();
  expect(screen.getByText("2 sessions")).toBeInTheDocument();
  expect(screen.getByText(/2026-10-27.*2026-10-28/)).toBeInTheDocument();
  expect(screen.getByTitle(/yahoo.*2026-10-29T08:00:00Z/)).toBeInTheDocument();
});

it("does not infer an entry zone when bounds or price are unknown", () => {
  show(<EntryZoneBadge />);
  expect(screen.getByText("Entry zone unknown")).not.toHaveClass("text-pos");
});
