import { fireEvent, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, vi } from "vitest";
import en from "@/messages/en.json";
import { ApiError } from "@/lib/api/client";
import { useCalibration, useConfirmWeights, useProposeWeights, useRejectWeights } from "@/lib/api/hooks";
import type { CalibrationOut, WeightSetOut } from "@/lib/api/types";
import { WeightProposal } from "./WeightProposal";

vi.mock("@/lib/api/hooks", () => ({
  useCalibration: vi.fn(),
  useProposeWeights: vi.fn(),
  useConfirmWeights: vi.fn(),
  useRejectWeights: vi.fn(),
}));

const propose = vi.fn();
const confirm = vi.fn();
const reject = vi.fn();

function mutation(mutate: typeof propose, extra = {}) {
  return { mutate, reset: vi.fn(), isPending: false, error: null, ...extra } as unknown;
}

const group = (kind: string, source: string, current: string, proposed: string, reason: string) => ({
  kind,
  source,
  count: 30,
  hits: 28,
  hit_rate: "0.9333",
  interval: { low: "0.7868", high: "0.9815" },
  current_weight: current,
  proposed_weight: proposed,
  reason,
});

const pending = (changed: boolean): WeightSetOut => ({
  id: "set-1",
  status: "proposed",
  horizon_days: 20,
  weights: { "catalyst:radar": "1.00", "entry:rule": changed ? "1.50" : "1.00" },
  created_at: "2026-10-27T09:00:00Z",
  decided_at: null,
  proposal: {
    horizon_days: 20,
    min_sample: 10,
    baseline_hit_rate: "0.5222",
    baseline_count: 90,
    changed,
    groups: [
      group("catalyst", "radar", "1.00", "1.00", "low_sample"),
      group("entry", "rule", "1.00", changed ? "1.50" : "1.00", changed ? "better" : "not_significant"),
    ],
  } as WeightSetOut["proposal"],
});

function setup(data: Partial<CalibrationOut> = {}, errors: { confirm?: unknown } = {}) {
  vi.mocked(useCalibration).mockReturnValue({
    data: { tunable: ["catalyst:radar", "entry:rule"], active: null, proposal: null, ...data },
  } as unknown as ReturnType<typeof useCalibration>);
  vi.mocked(useProposeWeights).mockReturnValue(mutation(propose) as ReturnType<typeof useProposeWeights>);
  vi.mocked(useConfirmWeights).mockReturnValue(mutation(confirm, { error: errors.confirm ?? null }) as ReturnType<typeof useConfirmWeights>);
  vi.mocked(useRejectWeights).mockReturnValue(mutation(reject) as ReturnType<typeof useRejectWeights>);
  render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      <WeightProposal horizonDays={20} />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => vi.clearAllMocks());

describe("WeightProposal", () => {
  it("does not present default weights when loading current weights fails", () => {
    setup();
    vi.mocked(useCalibration).mockReturnValue({data:undefined,error:new Error("offline"),isLoading:false,refetch:vi.fn()} as unknown as ReturnType<typeof useCalibration>);
    const view = render(<NextIntlClientProvider locale="en" messages={en}><WeightProposal horizonDays={20}/></NextIntlClientProvider>);
    expect(within(view.container).queryByText("No weights confirmed yet: every source counts at 1.00.")).toBeNull();
    expect(within(view.container).getByRole("alert")).toBeVisible();
  });
  it("starts from default weights and calculates a proposal for the chosen horizon", () => {
    setup();
    expect(screen.getByText("No weights confirmed yet: every source counts at 1.00.")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Calculate proposal (20 d)" }));
    expect(propose).toHaveBeenCalledWith(20);
  });

  it("shows interval, weight change and reason per group", () => {
    setup({ proposal: pending(true) });
    const row = screen.getByTestId("weight-entry-rule");
    expect(within(row).getByText("1.50")).toBeVisible();
    expect(within(row).getByText("Hits more often than the baseline")).toBeVisible();
    expect(within(screen.getByTestId("weight-catalyst-radar")).getByText("Too few signals (under 10)")).toBeVisible();
    expect(screen.getByText(/baseline 52\s?% over 90 system signals/)).toBeVisible();
  });

  it("changes weights only after an explicit second confirmation", () => {
    setup({ proposal: pending(true) });
    fireEvent.click(screen.getByRole("button", { name: "Apply weights…" }));
    expect(confirm).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("button", { name: "Confirm weights" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Apply weights…" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm weights" }));
    expect(confirm).toHaveBeenCalledOnce();
    expect(confirm.mock.calls[0]![0]).toBe("set-1");
  });

  it("cannot apply an unchanged proposal but can dismiss it", () => {
    setup({ proposal: pending(false) });
    expect(screen.getByRole("button", { name: "Apply weights…" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Dismiss proposal" }));
    expect(reject).toHaveBeenCalledWith("set-1");
  });

  it("explains a stale proposal", () => {
    setup({ proposal: pending(true) }, { confirm: new ApiError(409, "stale_proposal") });
    expect(screen.getByRole("alert")).toHaveTextContent("Weights changed after this proposal was made.");
  });
});
