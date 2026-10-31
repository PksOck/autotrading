import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "@/messages/en.json";
import { MarketStrip } from "./MarketStrip";

const messages = {
  ...en,
  pageHelp: { details: "Data details", marketUnavailable: "No verified market indicators" },
};
const show = (props: React.ComponentProps<typeof MarketStrip>) =>
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <MarketStrip {...props} />
    </NextIntlClientProvider>,
  );

it("keeps a fully missing market context compact and reveals individual sources on request", () => {
  show({ indicators: [], source: "database", asOf: "2026-10-30T10:00:00Z" });
  expect(screen.getByText("No verified market indicators")).toBeVisible();
  const details = screen.getByText("Data details").closest("details")!;
  expect(details).not.toHaveAttribute("open");
  fireEvent.click(screen.getByText("Data details"));
  expect(details).toHaveAttribute("open");
  expect(details).toHaveTextContent("database");
  expect(details.querySelector("time")).toHaveAttribute("dateTime", "2026-10-30T10:00:00Z");
  expect(details).toHaveTextContent(en.overviewFeedback.spy);
  expect(details).toHaveTextContent(en.overviewFeedback.vix);
});

it("distinguishes a load failure from unavailable indicator data", () => {
  show({ indicators: [], failed: true });
  expect(screen.getByRole("alert")).toHaveTextContent(en.table.loadFailed);
  expect(screen.queryByText("No verified market indicators")).not.toBeInTheDocument();
});

it("preserves a partial indicator value and an explicit missing-state label", () => {
  show({
    indicators: [{ key: "spy", value: "4.20", source: "synthetic", as_of: "2026-10-29T20:00:00Z" }],
  });
  expect(screen.getByText(/4\.20/)).toBeVisible();
  expect(screen.getAllByText(en.overviewFeedback.macroMissing).length).toBeGreaterThan(0);
});

it("retains cached indicators with a visible refresh error", () => {
  show({ indicators: [{ key: "vix", value: "19.4", source: "synthetic" }], failed: true });
  expect(screen.getByRole("alert")).toHaveTextContent(en.table.loadFailed);
  expect(screen.getByText("19.40")).toBeVisible();
});
