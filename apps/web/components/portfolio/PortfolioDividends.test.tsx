import { render, screen, fireEvent } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import messages from "@/messages/en.json";
import fragment from "@/messages/en.json";
import tableFragment from "@/messages/en.json";
import { useDividends } from "@/lib/api/dividends";
import { PortfolioDividends } from "./PortfolioDividends";

const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/portfolio",
  useSearchParams: () => new URLSearchParams("tab=dividends&dvAccount=SYNTH-A"),
}));
vi.mock("@/lib/api/dividends", () => ({ useDividends: vi.fn() }));

function show(value: object) {
  vi.mocked(useDividends).mockReturnValue(value as ReturnType<typeof useDividends>);
  render(
    <NextIntlClientProvider
      locale="en"
      messages={{
        ...messages,
        table: { ...messages.table, ...tableFragment.table },
        dividends: { ...messages.dividends, ...fragment.dividends },
      }}
    >
      <PortfolioDividends />
    </NextIntlClientProvider>,
  );
}

it("shows a retryable error without pretending no dividends were paid", () => {
  const refetch = vi.fn();
  show({ isPending: false, isError: true, refetch });
  expect(screen.getByRole("alert")).toHaveTextContent("could not be loaded");
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(refetch).toHaveBeenCalled();
  expect(screen.queryByText("No received cash events in this period.")).not.toBeInTheDocument();
});

it("uses statement coverage dates, signed booked amounts and server reconciliation without fabricating cash", () => {
  show({
    isPending: false,
    isError: false,
    data: {
      accounts: ["SYNTH-A"],
      currencies: ["USD"],
      as_of: "2026-10-29T12:00:00Z",
      accruals: [],
      received: [],
      cash_events: [
        {
          broker: "ibkr",
          account_id: "SYNTH-A",
          transaction_id: "1",
          booking_date: "2026-10-27",
          symbol: "SYNTH",
          kind: "withholding",
          amount: "-5",
          currency: "USD",
          source: "ibkr_flex",
          as_of: "2026-10-29T12:00:00Z",
        },
      ],
      coverage: [
        {
          account_id: "SYNTH-A",
          section: "CashTransactions",
          status: "complete",
          from_date: "2026-10-01",
          to_date: "2026-10-28",
          source: "ibkr_flex",
          as_of: "2026-10-29T12:00:00Z",
        },
      ],
      projections: [
        {
          account_id: "SYNTH-A",
          symbol: "SYNTH",
          quantity: "10",
          currency: "USD",
          annual_gross: "20",
          basis: "indicated_annual",
          position_as_of: "2026-10-25",
          source: "issuer",
          as_of: "2026-10-26T00:00:00Z",
        },
      ],
      reconciliation: [
        {
          account_id: "SYNTH-A",
          symbol: "SYNTH",
          currency: "USD",
          action_id: "ACTION-1",
          expected_gross: "20",
          received_gross: "19",
          difference: "-1",
          status: "changed",
          as_of: "2026-10-29T12:00:00Z",
        },
      ],
    },
  });
  expect(screen.getByText("SYNTH-A: statement reported through 2026-10-28")).toBeInTheDocument();
  expect(screen.getByText("Position snapshot: 2026-10-25")).toBeInTheDocument();
  expect(screen.getByText(/▼.*−.*5/)).toHaveClass("text-neg");
  expect(screen.getByText("Changed amount")).toBeInTheDocument();
  expect(screen.getByText(/▼.*−.*1/)).toHaveClass("text-neg");
  fireEvent.click(screen.getByRole("checkbox", { name: "Show coverage details" }));
  expect(screen.queryByText("Changed amount")).not.toBeInTheDocument();
  expect(screen.getByText("SYNTH-A: statement reported through 2026-10-28")).toBeInTheDocument();
});

it("keeps unknown withholding, missing coverage and projection gaps explicit", () => {
  show({
    isPending: false,
    isError: false,
    data: {
      cash_events: [],
      accruals: [],
      accounts: ["SYNTH-A"],
      currencies: ["USD"],
      as_of: null,
      received: [
        {
          currency: "USD",
          gross: "100",
          payment_in_lieu: "0",
          withholding: null,
          net: null,
          unresolved_withholding: null,
          base_amount: null,
          fx_complete: false,
        },
      ],
      coverage: [
        {
          account_id: "SYNTH-A",
          section: "CashTransactions",
          status: "missing",
          from_date: "2026-01-01",
          to_date: "2026-10-28",
          source: "ibkr_flex",
          as_of: "2026-10-29T00:00:00Z",
          gaps: [],
        },
      ],
      projections: [
        {
          account_id: "SYNTH-A",
          symbol: "SYNTH",
          quantity: "10",
          currency: "USD",
          annual_gross: null,
          annual_per_share: null,
          basis: null,
          reason: "incomplete_history",
          source: null,
          as_of: null,
        },
      ],
    },
  });
  expect(screen.getByText("Incomplete distribution history")).toBeInTheDocument();
  expect(screen.getByText("Section missing")).toBeInTheDocument();
  expect(screen.getByText("Estimated next 12 months · gross")).toBeInTheDocument();
  expect(screen.getByText("No confirmed cash coverage date is available.")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("checkbox", { name: "Show estimates" }));
  expect(screen.queryByText("Estimated next 12 months · gross")).not.toBeInTheDocument();
  expect(
    screen.getByText("Estimates are hidden. Imported cash and entitlements remain visible."),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole("checkbox", { name: "Show coverage details" }));
  expect(screen.queryByText("Section missing")).not.toBeInTheDocument();
  expect(
    screen.getByText(
      "Each new Flex import checks and reconciles imported records. Estimates never become booked cash automatically.",
    ),
  ).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Currency"), { target: { value: "USD" } });
  expect(replace).toHaveBeenCalledWith(expect.stringContaining("dvCurrency=USD"), {
    scroll: false,
  });
});
