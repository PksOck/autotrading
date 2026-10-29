import { fireEvent, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import en from "@/messages/en.json";
import { usePortfolio } from "@/lib/api/hooks";
import { useResearchAnalyses } from "@/lib/api/research";
import type { AnalysisSummary, HorizonOutlook } from "@/lib/api/types";
import { AnalysisRunList } from "./AnalysisRunList";
import { EvidenceSplit } from "./EvidenceSplit";
import { HorizonCard } from "./HorizonCard";
import { ActionPill } from "./outlook";

vi.mock("@/lib/api/hooks", () => ({ useAnalyses: vi.fn(), usePortfolio: vi.fn() }));
vi.mock("@/lib/api/research", () => ({ useResearchAnalyses: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => "/analysis",
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ replace: vi.fn() }),
}));

const wrap = (ui: React.ReactNode) =>
  render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      {ui}
    </NextIntlClientProvider>,
  );

const medium: HorizonOutlook = {
  horizon: "medium",
  verdict: "supports",
  pro: 2,
  contra: 1,
  neutral: 1,
  balance: 0.25,
  missing: ["valuation"],
  evidence: [
    {
      key: "trend_sma200",
      horizon: "medium",
      stance: "pro",
      value: 8.4,
      reference: 0,
      unit: "pct",
      source: "stooq",
      as_of: "2026-10-24T00:00:00Z",
    },
    {
      key: "momentum_12_1",
      horizon: "medium",
      stance: "pro",
      value: 21.3,
      reference: 10,
      unit: "pct",
      source: "stooq",
      as_of: "2026-10-24T00:00:00Z",
    },
    {
      key: "quality.debt_to_equity",
      horizon: "medium",
      stance: "contra",
      value: 2.4,
      reference: 1.5,
      unit: "ratio",
      source: "fmp",
      as_of: "2026-09-30T00:00:00Z",
    },
    {
      key: "cross_50_200",
      horizon: "medium",
      stance: "neutral",
      value: 0.2,
      reference: 0,
      unit: "pct",
      source: null,
      as_of: null,
    },
  ],
};

describe("ActionPill", () => {
  it("shows the plain-language action instead of the English rating", () => {
    wrap(<ActionPill rating="Underweight" />);
    expect(screen.getByTestId("action-pill")).toHaveTextContent("Trim position");
    expect(screen.getByTestId("action-pill")).toHaveAttribute("data-rating", "Underweight");
  });

  it("falls back to the raw rating when it is unknown and renders nothing without one", () => {
    const { container } = wrap(
      <>
        <ActionPill rating="Strong" />
        <ActionPill rating={null} />
      </>,
    );
    expect(container.querySelectorAll("[data-testid=action-pill]")).toHaveLength(1);
    expect(screen.getByText("Strong")).toBeVisible();
  });
});

describe("HorizonCard", () => {
  it("shows verdict, counts, top evidence and missing items, and selects on click", () => {
    const onSelect = vi.fn();
    wrap(<HorizonCard outlook={medium} selected={false} onSelect={onSelect} />);
    const card = screen.getByRole("button", { name: "Show evidence: Medium term" });
    expect(card).toHaveAttribute("aria-pressed", "false");
    expect(within(card).getByTestId("verdict-chip")).toHaveTextContent("Supports growth");
    expect(within(card).getByRole("img")).toHaveAccessibleName(
      "Medium term: 2 for, 1 neutral, 1 against",
    );
    expect(card).toHaveTextContent("Price vs 200-day average");
    expect(card).toHaveTextContent("+8.4% from the average");
    expect(card).toHaveTextContent("Debt to equity");
    expect(card).toHaveTextContent("Missing: Valuation vs own 5-year history");
    fireEvent.click(card);
    expect(onSelect).toHaveBeenCalledOnce();
  });
});

describe("EvidenceSplit", () => {
  it("splits evidence into for, against and neutral with provenance", () => {
    wrap(<EvidenceSplit outlook={medium} />);
    const pro = screen.getByTestId("evidence-pro");
    const contra = screen.getByTestId("evidence-contra");
    expect(
      within(pro)
        .getAllByTestId("evidence-row")
        .map((r) => r.dataset.key),
    ).toEqual(["trend_sma200", "momentum_12_1"]);
    expect(
      within(contra)
        .getAllByTestId("evidence-row")
        .map((r) => r.dataset.key),
    ).toEqual(["quality.debt_to_equity"]);
    expect(
      within(screen.getByTestId("evidence-neutral")).getByText("50- vs 200-day average"),
    ).toBeVisible();
    expect(pro).toHaveTextContent("+21.3% (threshold ±10%)");
    expect(contra).toHaveTextContent("fmp, Sep 30, 2026");
  });
});

describe("AnalysisRunList", () => {
  const run: AnalysisSummary = {
    id: "10000000-0000-4000-8000-000000000003",
    symbol: "ASML",
    name: "ASML Holding",
    engine: "stock",
    trade_date: "2026-10-24",
    status: "done",
    rating: "Overweight",
    caveats: [],
    created_at: "2026-10-24T10:00:00Z",
    finished_at: "2026-10-24T10:05:00Z",
    conviction: 6,
    outlook_brief: { short: "mixed", medium: "supports", long: "insufficient", pro: 5, contra: 2 },
  };

  it("shows action, horizon verdicts, for/against, conviction and held shares", () => {
    vi.mocked(useResearchAnalyses).mockReturnValue({
      data: [run],
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useResearchAnalyses>);
    vi.mocked(usePortfolio).mockReturnValue({
      data: { positions: [{ symbol: "ASML", quantity: 12 }] },
    } as unknown as ReturnType<typeof usePortfolio>);
    wrap(<AnalysisRunList />);
    const row = within(screen.getByTestId("analysis-table")).getAllByRole("row")[1]!;
    expect(within(row).getByRole("link")).toHaveAttribute("href", `/analysis/${run.id}`);
    expect(within(row).getByTestId("action-pill")).toHaveTextContent("Add to position");
    expect(
      within(row)
        .getAllByTestId("verdict-chip")
        .map((c) => c.dataset.verdict),
    ).toEqual(["mixed", "supports", "insufficient"]);
    expect(within(row).getByLabelText("5 for, 2 against")).toBeVisible();
    expect(row).toHaveTextContent("6/10");
    expect(row).toHaveTextContent("12 shares");
  });
});
