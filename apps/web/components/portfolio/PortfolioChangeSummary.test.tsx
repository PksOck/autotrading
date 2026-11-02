import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "@/messages/en.json";
import { PortfolioChangeSummary } from "./PortfolioChangeSummary";

it("switches between stored day and YTD estimates with explicit currency", () => {
  render(
    <NextIntlClientProvider locale="en" messages={en}>
      <PortfolioChangeSummary
        data={{
          base_currency: "EUR",
          daily_move: {
            amount: 2,
            percent: 1,
            basis: "held_positions_constant_reported_fx",
            reason: null,
          },
          ytd_move: {
            amount: null,
            basis: "held_positions_ytd_constant_reported_fx",
            reason: "unverified_fx_target",
          },
          ytd_native: [
            {
              currency: "USD",
              position_count: 1,
              amount: 30,
              percent: 37.5,
              basis: "held_positions_ytd_constant_reported_fx",
              reason: null,
            },
          ],
        }}
      />
    </NextIntlClientProvider>,
  );
  expect(screen.getByText(/▲.*2/)).toHaveTextContent("€");
  fireEvent.change(screen.getByRole("combobox", { name: "Change period" }), {
    target: { value: "ytd" },
  });
  expect(screen.getByText(/▲.*30/)).toHaveTextContent("$");
  expect(screen.getByText(/▲.*37.5/)).toBeVisible();
  expect(screen.getByText("By original currency")).toBeVisible();
  fireEvent.click(screen.getByLabelText("Price move basis"));
  expect(screen.queryByText(/at the last two closes/)).not.toBeInTheDocument();
});

it("explains missing year-start history instead of showing a zero return", () => {
  render(
    <NextIntlClientProvider locale="en" messages={en}>
      <PortfolioChangeSummary
        data={{
          base_currency: "EUR",
          ytd_native: [
            {
              currency: "USD",
              position_count: 1,
              amount: null,
              basis: "held_positions_ytd_constant_reported_fx",
              reason: "missing_year_start",
            },
          ],
        }}
      />
    </NextIntlClientProvider>,
  );
  fireEvent.change(screen.getByRole("combobox", { name: "Change period" }), {
    target: { value: "ytd" },
  });
  expect(screen.getByText("No comparable close before the start of this year.")).toBeVisible();
  expect(screen.queryByText(/0\.0%/)).not.toBeInTheDocument();
});
