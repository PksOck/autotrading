import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import en from "@/messages/en.json";
import { analysis } from "@/test/thesis-fixtures";
import { useAnalysis } from "@/lib/api/hooks";
import { AnalysisView } from "@/components/analysis/AnalysisView";
import type { AnalysisOut } from "@/lib/api/types";

vi.mock("@/lib/api/hooks", () => ({
  useAnalysis: vi.fn(),
  useAnalysisStream: () => ({ steps: [], connected: false }),
}));
vi.mock("@/components/theses/CreateThesisButton", () => ({
  CreateThesisButton: () => <button>Create thesis draft</button>,
}));
vi.mock("@/components/analysis/AgentTimeline", () => ({ AgentTimeline: () => null }));

it.each([
  ["done", true, true],
  ["running", true, false],
  ["queued", true, false],
  ["failed", true, false],
  ["done", false, false],
] as [AnalysisOut["status"], boolean, boolean][])(
  "offers a draft for status %s and triggers %s only when finished",
  (status, triggers, visible) => {
    const run = {
      ...analysis,
      status,
      card: {
        ...analysis.card!,
        upgrade_if: triggers ? ["Margins remain stable"] : [],
        downgrade_if: [],
      },
    };
    vi.mocked(useAnalysis).mockReturnValue({
      data: run,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useAnalysis>);
    render(
      <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
        <AnalysisView runId={analysis.id} />
      </NextIntlClientProvider>,
    );
    if (visible) expect(screen.getByRole("button", { name: "Create thesis draft" })).toBeVisible();
    else
      expect(screen.queryByRole("button", { name: "Create thesis draft" })).not.toBeInTheDocument();
  },
);
