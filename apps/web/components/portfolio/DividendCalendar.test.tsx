import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "@/messages/en.json";
import { DividendCalendar } from "./DividendCalendar";

it("lets a user select a month and see dated securities without inventing missing dates", () => {
  const totals = {
    currency: "USD",
    received_gross: "10",
    received_net: null,
    scheduled_gross: "12",
    scheduled_net: null,
    received_count: 1,
    scheduled_count: 1,
  };
  render(
    <NextIntlClientProvider locale="en" messages={en}>
      <DividendCalendar
        asOf="2026-11-01T00:00:00Z"
        calendar={{
          months: [{ ...totals, month: "2026-11" }],
          years: [{ ...totals, year: 2026 }],
          events: [
            {
              id: "one",
              account_id: "A",
              symbol: "ABC",
              currency: "USD",
              payment_date: "2026-11-15",
              gross: "12",
              state: "scheduled",
              source: "synthetic",
              as_of: "2026-11-01T00:00:00Z",
            },
          ],
          issues: [
            {
              id: "two",
              account_id: "A",
              symbol: "XYZ",
              currency: "USD",
              reason: "missing_pay_date",
            },
          ],
        }}
      />
    </NextIntlClientProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "November 2026" }));
  expect(screen.getByRole("button", { name: "November 2026" })).toHaveAccessibleDescription(
    /Received gross.*10.*Open accruals gross.*12.*2 records/,
  );
  expect(screen.getByText("ABC")).toBeVisible();
  expect(screen.getByText("2026-11-15")).toBeVisible();
  expect(screen.getByText(/XYZ/)).toBeVisible();
  expect(screen.getByText(/Payment date unavailable/)).toBeVisible();
  expect(screen.getByRole("button", { name: "December 2026" })).toHaveTextContent("—");
});
