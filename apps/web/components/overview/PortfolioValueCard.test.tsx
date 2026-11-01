import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "@/messages/en.json";
import { PortfolioValueCard } from "./PortfolioValueCard";

it("labels the signed daily price estimate and keeps the snapshot link beside its date", () => {
  render(
    <NextIntlClientProvider locale="en" messages={en}>
      <PortfolioValueCard
        data={{
          total_value: 1000,
          base_currency: "EUR",
          as_of: "2026-10-29",
          daily_move: {
            amount: 48,
            percent: 10,
            market_date: "2026-10-30",
            previous_market_date: "2026-10-29",
            holdings_dates: ["2026-10-29"],
            sources: ["synthetic"],
            basis: "held_positions_constant_reported_fx",
            reason: null,
          },
        }}
      />
    </NextIntlClientProvider>,
  );
  expect(screen.getByText(/▲.*48/)).toBeVisible();
  expect(screen.getByText(/▲.*10/)).toBeVisible();
  expect(screen.getByText("Held positions · last session estimate")).toBeVisible();
  expect(
    screen.getByRole("link", { name: /Portfolio/ }).parentElement?.querySelector("time"),
  ).toHaveAttribute("datetime", "2026-10-29");
});

it("keeps native estimates separate and preserves unknown groups", () => {
  render(
    <NextIntlClientProvider locale="en" messages={en}>
      <PortfolioValueCard
        data={{
          total_value: 1000,
          base_currency: "EUR",
          as_of: "2026-10-29",
          daily_move: {
            amount: null,
            reason: "unverified_fx_target",
            basis: "held_positions_constant_reported_fx",
          },
          daily_native: [
            {
              currency: "USD",
              position_count: 2,
              amount: 20,
              percent: 10,
              reason: null,
              basis: "held_positions_constant_reported_fx",
            },
            {
              currency: "EUR",
              position_count: 1,
              amount: null,
              reason: "missing_price",
              basis: "held_positions_constant_reported_fx",
            },
          ],
        }}
      />
    </NextIntlClientProvider>,
  );
  expect(screen.getByText("Held positions by currency · estimate")).toBeVisible();
  expect(screen.getByText(/▲.*20/)).toHaveTextContent("$");
  expect(screen.getByText("Daily estimate unavailable")).toBeVisible();
});
