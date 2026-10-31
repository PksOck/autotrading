import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import en from "@/messages/en.json";
import feedback from "@/messages/en.json";
import { BacktestPanel } from "./BacktestPanel";

const { send, navigation } = vi.hoisted(() => ({
  send: vi.fn(),
  navigation: { push: vi.fn(), replace: vi.fn() },
}));
vi.mock("@/lib/api/client", () => ({ api: { send } }));
vi.mock("next/navigation", () => ({
  useRouter: () => navigation,
  usePathname: () => "/track-record",
  useSearchParams: () => new URLSearchParams("horizon=5&filter=keep&tag=one&tag=two"),
}));

beforeEach(() => vi.clearAllMocks());

it("calculates only after submission and displays incomplete observations explicitly", async () => {
  send.mockResolvedValue({
    method_id: "saved-record-after-utc-close-v1",
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
  fireEvent.click(screen.getByLabelText("Saved-opinion testing method"));
  expect(screen.getByText("saved-record-after-utc-close-v1")).toBeVisible();
});

it("keeps signal and analysis targets distinct for the same UUID and preserves submitted results", async () => {
  const id = "10000000-0000-4000-8000-000000000123";
  send.mockResolvedValue({
    as_of: "2026-10-29T12:00:00Z",
    source: "database",
    total_matching: 2,
    evaluated: 2,
    completed: 2,
    skipped: 0,
    truncated: false,
    mean_net_return_pct: "9.8",
    positive_share: "1",
    parameters: {
      source: "all",
      horizon_sessions: 20,
      cost_bps: "10",
      min_strength: "0",
      signal_status: "all",
      available_from: "2026-09-01",
      available_to: "2026-10-01",
    },
    rows: ["signal", "analysis"].map((source) => ({
      id,
      source,
      origin: "fixture",
      symbol: "MSFT",
      direction: "up",
      available_at: "2026-10-01T12:00:00Z",
      entry_price: "100",
      exit_price: "110",
      entry_date: "2026-10-02",
      exit_date: "2026-10-29",
      entry_source: "fixture",
      exit_source: "fixture",
      currency: "USD",
      net_return_pct: "9.8",
      skip_reason: null,
    })),
  });
  render(
    <QueryClientProvider client={new QueryClient()}>
      <NextIntlClientProvider
        locale="en"
        messages={{
          ...en,
          backtestFeedback: { ...en.backtestFeedback, newTab: "Opens in a new tab" },
        }}
        timeZone="UTC"
      >
        <BacktestPanel />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: feedback.backtestFeedback.calculate }));
  const signalLink = await screen.findByRole("link", { name: "MSFT" });
  fireEvent.click(screen.getByLabelText("Saved-opinion testing method"));
  expect(screen.getByText("Method identifier unavailable")).toBeVisible();
  expect(screen.queryByText("saved-record-after-utc-close-v1")).not.toBeInTheDocument();
  expect(signalLink).toHaveAttribute(
    "href",
    `/track-record?horizon=5&filter=keep&tag=one&tag=two&peek=signal%3A${id}`,
  );
  const analysisLink = screen.getByRole("link", { name: /MSFT\s*\(Opens in a new tab\)/ });
  expect(analysisLink).toHaveAttribute("href", `/analysis/${id}`);
  expect(analysisLink).toHaveAttribute("target", "_blank");
  expect(analysisLink).toHaveAttribute("rel", "noopener noreferrer");
  const results = signalLink.closest('[aria-live="polite"]')!;
  const originalResults = results.textContent;
  fireEvent.change(screen.getByLabelText(feedback.backtestFeedback.horizon), {
    target: { value: "60" },
  });
  fireEvent.change(screen.getByLabelText(feedback.backtestFeedback.cost), {
    target: { value: "30" },
  });
  fireEvent.change(screen.getByLabelText(feedback.backtestFeedback.source), {
    target: { value: "analysis" },
  });
  fireEvent.click(signalLink);
  expect(navigation.push).toHaveBeenCalledWith(signalLink.getAttribute("href"), { scroll: false });
  expect(results.textContent).toBe(originalResults);
  expect(send).toHaveBeenCalledTimes(1);
  navigation.push.mockClear();
  // The browser suite verifies native new-tab navigation. Suppress jsdom's unsupported navigation.
  signalLink.addEventListener("click", (event) => event.preventDefault());
  for (const modifier of ["ctrlKey", "metaKey", "shiftKey", "altKey"]) {
    fireEvent.click(signalLink, { [modifier]: true });
  }
  fireEvent.click(signalLink, { button: 1 });
  expect(navigation.push).not.toHaveBeenCalled();
  expect(send).toHaveBeenCalledTimes(1);
});
