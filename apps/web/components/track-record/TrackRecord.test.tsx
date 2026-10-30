import { fireEvent, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import en from "@/messages/en.json";
import { useResearchTrackRecord, useResearchOutcomes } from "@/lib/api/research";
import type { TrackRecordOut } from "@/lib/api/types";
import { TrackRecord } from "./TrackRecord";

vi.mock("@/lib/api/research", () => ({
  useResearchTrackRecord: vi.fn(),
  useResearchOutcomes: vi.fn(),
}));
const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/track-record",
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock("./WeightProposal", () => ({ WeightProposal: () => null }));
const useRecord = vi.mocked(useResearchTrackRecord);
const refetch = vi.fn();

const stat = (count: number, hit: string | null, ret: string | null, alpha: string | null) => ({
  count,
  hit_rate: hit,
  avg_return_pct: ret,
  avg_alpha_pct: alpha,
  low_sample: count < 10,
});

const record: TrackRecordOut = {
  horizon_days: 20,
  horizons: [1, 5, 20, 60],
  benchmark: "SPY",
  source: "signal_outcome",
  as_of: "2026-10-26T20:00:00Z",
  min_sample: 10,
  signals_total: 15,
  measured: 12,
  pending: 3,
  overall: stat(12, "0.5833", "1.2500", "-0.4000"),
  by_origin: [
    { origin: "user", ...stat(2, "1.0000", "4.0000", "2.0000") },
    { origin: "system", ...stat(10, "0.5000", "0.7000", "-0.8000") },
  ],
  by_group: [{ kind: "entry", source: "rule", ...stat(10, "0.5000", "0.7000", "-0.8000") }],
  calibration: [0, 1, 2, 3, 4].map((i) => ({
    strength_low: String(i / 5),
    strength_high: String((i + 1) / 5),
    avg_strength: i === 4 ? "0.9000" : null,
    ...(i === 4 ? stat(12, "0.5833", "1.2500", null) : stat(0, null, null, null)),
  })),
};

function result(value: object) {
  useRecord.mockReturnValue({
    isLoading: false,
    data: undefined,
    error: null,
    refetch,
    ...value,
  } as unknown as ReturnType<typeof useResearchTrackRecord>);
  vi.mocked(useResearchOutcomes).mockReturnValue({
    data: { items: [], total: 0, offset: 0, limit: 30 },
    error: null,
    isLoading: false,
  } as unknown as ReturnType<typeof useResearchOutcomes>);
}

function renderRecord() {
  return render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      <QueryClientProvider client={new QueryClient()}>
        <TrackRecord />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("TrackRecord", () => {
  it("shows hit rate, return, alpha vs benchmark and pending outcomes", () => {
    result({ data: record });
    renderRecord();
    expect(screen.getAllByText("58%")).toHaveLength(2); // summary tile and top strength bucket
    expect(screen.getByText("Alpha vs SPY")).toBeInTheDocument();
    expect(screen.getByText("▼ −0.4%")).toBeInTheDocument();
    expect(screen.getByText("12 of 15")).toBeInTheDocument();
    expect(screen.getByText("Awaiting outcome: 3")).toBeInTheDocument();
    expect(useRecord).toHaveBeenLastCalledWith({
      horizon_days: 20,
      created_from: undefined,
      created_to: undefined,
    });
  });

  it("measures your proposals apart from system signals and flags small samples", () => {
    result({ data: record });
    renderRecord();
    const user = screen.getByTestId("origin-user");
    expect(within(user).getByText("Your proposals")).toBeInTheDocument();
    expect(within(user).getByText("100%")).toBeInTheDocument();
    expect(within(user).getByText("Little data")).toBeInTheDocument();
    expect(within(screen.getByTestId("origin-system")).queryByText("Little data")).toBeNull();
    expect(screen.getByRole("cell", { name: "Entry" })).toBeInTheDocument();
    fireEvent.click(screen.getAllByText("Strength calibration")[0]!);
    expect(screen.getAllByRole("meter")).toHaveLength(5);
  });

  it("switches the horizon", () => {
    result({ data: record });
    renderRecord();
    fireEvent.click(screen.getByRole("radio", { name: "60 d" }));
    expect(replace).toHaveBeenLastCalledWith("/track-record?horizon=60", { scroll: false });
  });

  it("explains an empty record and retries after an error", () => {
    result({ data: { ...record, measured: 0, pending: 15, overall: stat(0, null, null, null) } });
    const view = renderRecord();
    expect(screen.getByText(/No measured outcomes for the 20 d horizon yet/)).toBeInTheDocument();
    result({ error: new Error("down") });
    view.rerender(
      <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
        <QueryClientProvider client={new QueryClient()}>
          <TrackRecord />
        </QueryClientProvider>
      </NextIntlClientProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(refetch).toHaveBeenCalled();
  });
});
