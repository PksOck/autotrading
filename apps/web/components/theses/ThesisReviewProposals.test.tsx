import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import en from "@/messages/en.json";
import sl from "@/messages/sl.json";
import { ApiError } from "@/lib/api/client";
import { useAcceptThesisReviewProposal, useDismissThesisReviewProposal } from "@/lib/api/hooks";
import { claim, review, reviewProposal, thesisId } from "@/test/thesis-fixtures";
import { ThesisCheck } from "./ThesisCheck";
import { ThesisReviewProposals, ThesisReviewRun } from "./ThesisReviewProposals";

vi.mock("@/lib/api/hooks", () => ({
  useAcceptThesisReviewProposal: vi.fn(),
  useDismissThesisReviewProposal: vi.fn(),
}));
const accept = vi.fn();
const dismiss = vi.fn();
const refresh = vi.fn();
function renderProposals(extra = {}, locale = "en") {
  return render(
    <NextIntlClientProvider locale={locale} messages={locale === "en" ? en : sl} timeZone="UTC">
      <ThesisCheck status={claim.status} />
      <ThesisReviewProposals
        thesisId={thesisId}
        claim={claim}
        active
        proposals={[reviewProposal]}
        reviews={[review]}
        refresh={refresh}
        {...extra}
      />
    </NextIntlClientProvider>,
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(useAcceptThesisReviewProposal).mockReturnValue({
    mutate: accept,
    isPending: false,
    error: null,
    reset: vi.fn(),
  } as unknown as ReturnType<typeof useAcceptThesisReviewProposal>);
  vi.mocked(useDismissThesisReviewProposal).mockReturnValue({
    mutate: dismiss,
    isPending: false,
    error: null,
    reset: vi.fn(),
  } as unknown as ReturnType<typeof useDismissThesisReviewProposal>);
});

it("keeps the actual status separate from the proposal badge, with evidence provenance and rumour label", () => {
  renderProposals();
  expect(screen.getByText("Open").closest("[data-status]")).toHaveAttribute("data-status", "open");
  expect(screen.getByText("Review proposal")).not.toHaveAttribute("data-status");
  expect(screen.getByText("Possible thesis break")).toBeVisible();
  expect(screen.getByText("Rumour, unconfirmed")).toBeVisible();
  expect(screen.getByText("Source: EDGAR", { exact: false })).toBeVisible();
  expect(screen.getByRole("link")).toHaveAttribute("href", "https://www.sec.gov/filing/1");
  expect(screen.getByText("Model role: cloud-deep · review-model")).toBeVisible();
  expect(screen.getByText("Omitted evidence items: 2")).toBeVisible();
  expect(document.querySelector("time")).toHaveAttribute("dateTime", review.as_of);
});

it("requires a second explicit click and sends the reviewed status and nullable event ID", () => {
  renderProposals();
  expect(accept).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Accept proposal" }));
  expect(accept).not.toHaveBeenCalled();
  expect(screen.getByRole("group", { name: "Confirm acceptance" })).toHaveTextContent(
    "Change the claim status",
  );
  fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
  expect(screen.queryByRole("button", { name: "Confirm acceptance" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Accept proposal" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirm acceptance" }));
  expect(accept).toHaveBeenCalledWith(
    { expected_status: "open", expected_last_event_id: null },
    expect.any(Object),
  );
});

it("requires a non-whitespace dismissal reason", () => {
  renderProposals();
  const button = screen.getByRole("button", { name: "Dismiss proposal" });
  expect(button).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Reason for dismissal"), { target: { value: "   " } });
  expect(button).toBeDisabled();
  fireEvent.submit(button.closest("form")!);
  expect(dismiss).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Reason for dismissal"), {
    target: { value: "  Await audited accounts  " },
  });
  fireEvent.click(button);
  expect(dismiss).toHaveBeenCalledWith({ reason: "Await audited accounts" });
});

it.each([
  { proposals: [{ ...reviewProposal, suggested_status: null, assessment: "insufficient" }] },
  { active: false },
  { claim: { ...claim, status: "confirmed" } },
  { proposals: [{ ...reviewProposal, last_claim_event_id_at_review: "old-event" }] },
  { reviews: [{ ...review, status: "stale" }] },
  { reviews: [{ ...review, revision_id: "superseded-revision" }] },
  { reviews: [] },
])("does not allow acceptance of insufficient, stale or unverified proposals %#", (extra) => {
  renderProposals(extra);
  expect(screen.queryByRole("button", { name: "Accept proposal" })).not.toBeInTheDocument();
  expect(accept).not.toHaveBeenCalled();
});

it("shows a friendly conflict and refresh instead of backend details", () => {
  vi.mocked(useAcceptThesisReviewProposal).mockReturnValue({
    mutate: accept,
    isPending: false,
    error: new ApiError(409, "claim_changed_raw"),
    reset: vi.fn(),
  } as unknown as ReturnType<typeof useAcceptThesisReviewProposal>);
  renderProposals();
  expect(screen.getByRole("alert")).toHaveTextContent("The claim or proposal changed");
  expect(screen.queryByText(/claim_changed_raw|409/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Refresh reviews" }));
  expect(refresh).toHaveBeenCalledOnce();
});

it.each(["failed", "failed_unknown", "stale", "done_no_evidence"] as const)(
  "shows the %s review state",
  (status) => {
    render(
      <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
        <ThesisReviewRun review={{ ...review, status }} />
      </NextIntlClientProvider>,
    );
    expect(
      screen.getByText(
        status.startsWith("failed")
          ? /The review failed/
          : status === "stale"
            ? /This review is outdated/
            : /No evidence was available/,
      ),
    ).toBeVisible();
  },
);

it("uses Slovenian review copy", () => {
  renderProposals({}, "sl");
  expect(screen.getByText("Možen zlom teze")).toBeVisible();
  expect(screen.getByRole("button", { name: "Sprejmi predlog" })).toBeVisible();
});
