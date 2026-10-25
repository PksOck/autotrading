import { fireEvent, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import en from "@/messages/en.json";
import { ApiError } from "@/lib/api/client";
import {
  useThesis,
  usePatchThesisRevision,
  useConfirmThesisRevision,
  useChangeClaimStatus,
  useThesisReviews,
  useThesisReviewProposals,
} from "@/lib/api/hooks";
import { asOf, claim, revision, thesis } from "@/test/thesis-fixtures";
import type { ThesisOut } from "@/lib/api/types";
import { ThesisDetail } from "./ThesisDetail";

vi.mock("@/lib/api/hooks", () => ({
  useThesis: vi.fn(),
  usePatchThesisRevision: vi.fn(),
  useConfirmThesisRevision: vi.fn(),
  useChangeClaimStatus: vi.fn(),
  useThesisReviews: vi.fn(),
  useThesisReviewProposals: vi.fn(),
}));
const patch = vi.fn();
const confirm = vi.fn();
const change = vi.fn();
function mutation(mutate: typeof patch, extra = {}) {
  return { mutate, isPending: false, error: null, ...extra } as unknown;
}
function setData(data: ThesisOut | undefined = thesis, extra = {}) {
  vi.mocked(useThesis).mockReturnValue({
    data,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    ...extra,
  } as unknown as ReturnType<typeof useThesis>);
}
function renderDetail() {
  return render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      <ThesisDetail thesisId={thesis.id} />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  setData();
  vi.mocked(useThesisReviews).mockReturnValue({
    data: [],
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useThesisReviews>);
  vi.mocked(useThesisReviewProposals).mockReturnValue({
    data: [],
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useThesisReviewProposals>);
  vi.mocked(usePatchThesisRevision).mockReturnValue(
    mutation(patch) as ReturnType<typeof usePatchThesisRevision>,
  );
  vi.mocked(useConfirmThesisRevision).mockReturnValue(
    mutation(confirm) as ReturnType<typeof useConfirmThesisRevision>,
  );
  vi.mocked(useChangeClaimStatus).mockReturnValue(
    mutation(change) as ReturnType<typeof useChangeClaimStatus>,
  );
});

describe("ThesisDetail", () => {
  it("shows revision provenance, active claims and rumour evidence in event history", () => {
    setData({
      ...thesis,
      revisions: [
        {
          ...revision,
          claims: [
            {
              ...claim,
              status: "weakening",
              events: [
                {
                  id: "event",
                  claim_id: claim.id,
                  from_status: "open",
                  to_status: "weakening",
                  actor: "user",
                  rationale: "Await the official filing",
                  source: "manual",
                  as_of: asOf,
                  created_at: asOf,
                  evidence: [{ source: "forum", as_of: asOf, ref: "post:1", is_rumor: true }],
                },
              ],
            },
          ],
        },
      ],
    });
    renderDetail();
    expect(screen.getByText("Margins remain stable")).toBeVisible();
    expect(screen.getByRole("region", { name: "Version 1, Active" })).toHaveTextContent(
      "Source: analysis",
    );
    fireEvent.click(screen.getByText("Event history, 1 event"));
    expect(screen.getByText("Rumour, unconfirmed")).toBeVisible();
    expect(screen.getByText("post:1")).toBeVisible();
    expect(screen.getByText("Await the official filing")).toBeVisible();
  });
  it("edits draft text and invalidation with expected version; unsaved edits cannot be confirmed", () => {
    setData({ ...thesis, revisions: [{ ...revision, status: "draft", confirmed_at: null }] });
    renderDetail();
    expect(screen.getByRole("button", { name: "Confirm revision" })).toBeEnabled();
    fireEvent.change(screen.getByLabelText("Statement"), { target: { value: "Revenue grows" } });
    fireEvent.change(screen.getByLabelText("Invalidated if"), {
      target: { value: "Revenue declines" },
    });
    expect(screen.getByRole("button", { name: "Confirm revision" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(patch).toHaveBeenCalledWith(
      {
        expected_version: 1,
        claims: [{ id: claim.id, statement: "Revenue grows", invalidated_if: "Revenue declines" }],
      },
      expect.any(Object),
    );
    expect(confirm).not.toHaveBeenCalled();
    expect(screen.queryByText("Change claim status")).not.toBeInTheDocument();
  });
  it("follows newer server text for untouched claims and saves only edited ones", () => {
    const second = { ...claim, id: "claim-2", ordinal: 2, statement: "Margins hold" };
    const draft = (statement: string) => ({
      ...thesis,
      revisions: [
        {
          ...revision,
          status: "draft" as const,
          confirmed_at: null,
          claims: [claim, { ...second, statement }],
        },
      ],
    });
    setData(draft("Margins hold"));
    const view = renderDetail();
    fireEvent.change(screen.getAllByLabelText("Statement")[0]!, {
      target: { value: "Revenue grows" },
    });
    setData(draft("Margins widen"));
    view.rerender(
      <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
        <ThesisDetail thesisId={thesis.id} />
      </NextIntlClientProvider>,
    );
    expect(screen.getAllByLabelText("Statement")[1]).toHaveValue("Margins widen");
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(patch).toHaveBeenCalledWith(
      {
        expected_version: 1,
        claims: [
          {
            id: claim.id,
            statement: "Revenue grows",
            invalidated_if: claim.invalidated_if ?? null,
          },
        ],
      },
      expect.any(Object),
    );
  });
  it("confirms only through an explicit click", () => {
    setData({ ...thesis, revisions: [{ ...revision, status: "draft" }] });
    renderDetail();
    expect(confirm).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirm revision" }));
    expect(confirm).toHaveBeenCalledOnce();
  });
  it("requires evidence for non-open states and sends complete evidence with expected status", () => {
    renderDetail();
    fireEvent.click(screen.getByText("Change claim status"));
    fireEvent.change(screen.getByLabelText("New status"), { target: { value: "confirmed" } });
    fireEvent.change(screen.getByLabelText("Rationale"), {
      target: { value: "Official filing confirms margins" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save status" }));
    expect(change).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("add evidence");
    fireEvent.click(screen.getByRole("button", { name: "Add evidence" }));
    const evidence = within(screen.getByRole("group", { name: "Evidence 1" }));
    fireEvent.change(evidence.getByLabelText("Source"), { target: { value: "EDGAR" } });
    fireEvent.change(evidence.getByLabelText("As of, your local time"), {
      target: { value: "2026-10-25T13:00" },
    });
    fireEvent.change(evidence.getByLabelText("Reference"), { target: { value: "filing:1" } });
    fireEvent.click(screen.getByRole("button", { name: "Save status" }));
    expect(change).toHaveBeenCalledWith(
      {
        to_status: "confirmed",
        expected_status: "open",
        rationale: "Official filing confirms margins",
        evidence: [
          {
            source: "EDGAR",
            as_of: new Date("2026-10-25T13:00").toISOString(),
            ref: "filing:1",
            url: null,
            is_rumor: false,
          },
        ],
      },
      expect.any(Object),
    );
  });
  it("allows reopening with rationale and no evidence, and removes evidence rows", () => {
    renderDetail();
    fireEvent.click(screen.getByText("Change claim status"));
    fireEvent.click(screen.getByRole("button", { name: "Add evidence" }));
    fireEvent.click(screen.getByRole("button", { name: "Remove evidence" }));
    fireEvent.change(screen.getByLabelText("Rationale"), { target: { value: "Needs review" } });
    fireEvent.click(screen.getByRole("button", { name: "Save status" }));
    expect(change).toHaveBeenCalledWith(
      { to_status: "open", expected_status: "open", rationale: "Needs review", evidence: [] },
      expect.any(Object),
    );
  });
  it("does not show status forms for superseded revisions", () => {
    setData({ ...thesis, revisions: [{ ...revision, status: "superseded" }] });
    renderDetail();
    expect(screen.queryByText("Change claim status")).not.toBeInTheDocument();
    expect(screen.getByText("Margins remain stable")).toBeVisible();
  });
  it("shows friendly conflict feedback without raw backend details", () => {
    vi.mocked(useChangeClaimStatus).mockReturnValue(
      mutation(change, { error: new ApiError(409, "claim_status_conflict") }) as ReturnType<
        typeof useChangeClaimStatus
      >,
    );
    renderDetail();
    fireEvent.click(screen.getByText("Change claim status"));
    expect(screen.getByRole("alert")).toHaveTextContent("The claim status changed");
    expect(screen.queryByText("claim_status_conflict")).not.toBeInTheDocument();
  });
  it("handles missing and loading data", () => {
    setData(undefined, { isLoading: true });
    const view = renderDetail();
    expect(screen.getByLabelText("Loading theses")).toHaveAttribute("aria-busy", "true");
    setData(undefined, { error: new ApiError(404, "thesis_not_found") });
    view.rerender(
      <NextIntlClientProvider locale="en" messages={en}>
        <ThesisDetail thesisId={thesis.id} />
      </NextIntlClientProvider>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("was not found");
  });
});
