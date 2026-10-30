import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import en from "@/messages/en.json";
import feedback from "@/messages/en.json";
import { BacktestPanel } from "./BacktestPanel";

const { send } = vi.hoisted(() => ({ send: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ api: { send } }));

it("calculates only after submission and displays incomplete observations explicitly", async () => {
  send.mockResolvedValue({
    as_of: "2026-10-29T12:00:00Z",
    source: "database",
    total_matching: 1,
    evaluated: 1,
    truncated: false,
    completed: 0,
    skipped: 1,
    mean_net_return_pct: null,
    positive_share: null,
    parameters: { source: "signal", horizon_sessions: 20, cost_bps: "10" },
    rows: [
      {
        id: "17",
        source: "signal",
        origin: "radar",
        symbol: "MSFT",
        direction: "up",
        available_at: "2026-10-28T12:00:00Z",
        record_status: "new",
        skip_reason: "insufficient_future_sessions",
      },
    ],
  });
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { mutations: { retry: false } } })}
    >
      <NextIntlClientProvider locale="en" messages={{ ...en, ...feedback }} timeZone="UTC">
        <BacktestPanel />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  expect(send).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText(feedback.backtestFeedback.source), {
    target: { value: "signal" },
  });
  fireEvent.click(screen.getByRole("button", { name: feedback.backtestFeedback.calculate }));
  await waitFor(() =>
    expect(send).toHaveBeenCalledWith(
      "/backtest",
      "POST",
      expect.objectContaining({ source: "signal", horizon_sessions: 20, cost_bps: "10" }),
    ),
  );
  expect(
    await screen.findByText(feedback.backtestFeedback.insufficient_future_sessions),
  ).toBeInTheDocument();
  expect(screen.getByText("MSFT")).toBeInTheDocument();
});
