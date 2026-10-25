"use client";

import { useState } from "react";
import { useFormatter, useTranslations } from "next-intl";
import { ApiError } from "@/lib/api/client";
import { useAcceptThesisReviewProposal, useDismissThesisReviewProposal } from "@/lib/api/hooks";
import type { ClaimReviewProposalOut, ReviewOut, ThesisClaimOut } from "@/lib/api/types";
import { isHttpUrl } from "@/lib/thesis";
import { LocalTime } from "./LocalTime";
import { thesisButton } from "./styles";

function Provenance({ source, asOf }: { source: string; asOf: string }) {
  const t = useTranslations("theses.review");
  return (
    <p className="text-xs text-text-3">
      {t("source")}: {source}
      {" · "}
      {t("asOf")}: <LocalTime value={asOf} />
    </p>
  );
}

export function ThesisReviewRun({ review }: { review: ReviewOut }) {
  const t = useTranslations("theses.review");
  const format = useFormatter();
  const omitted = review.snapshot.omitted_count;
  const state =
    review.status === "failed_unknown"
      ? "failed"
      : review.status === "done_no_evidence"
        ? "noEvidence"
        : review.status;
  return (
    <div className="flex flex-col gap-2 rounded-md bg-surface-2 p-3 text-[13px] [overflow-wrap:anywhere]">
      <p className={state === "failed" || state === "stale" ? "text-warn" : "text-text-2"}>
        {t(state)}
      </p>
      <p>
        {t("modelRole")}: {review.role}
        {review.model && ` · ${review.model}`}
      </p>
      <p>
        {t("runId")}: <span className="num">{review.id}</span>
      </p>
      <p>
        {t("coverage")}: <LocalTime value={review.input_from} />
        {" → "}
        <LocalTime value={review.input_cutoff} />
      </p>
      {review.truncated && <p className="text-warn">{t("truncated")}</p>}
      {typeof omitted === "number" && <p>{t("omitted", { count: format.number(omitted) })}</p>}
      <Provenance source={review.source} asOf={review.as_of} />
    </div>
  );
}

export function ThesisReviewProposals({
  thesisId,
  claim,
  active,
  proposals,
  reviews,
  refresh,
}: {
  thesisId: string;
  claim: ThesisClaimOut;
  active: boolean;
  proposals: ClaimReviewProposalOut[];
  reviews: ReviewOut[];
  refresh: () => void;
}) {
  return (
    <>
      {proposals
        .filter((p) => p.claim_id === claim.id && p.state === "pending")
        .map((proposal) => (
          <Proposal
            key={proposal.id}
            thesisId={thesisId}
            claim={claim}
            active={active}
            proposal={proposal}
            review={reviews.find((r) => r.id === proposal.review_id)}
            refresh={refresh}
          />
        ))}
    </>
  );
}

function Proposal({
  thesisId,
  claim,
  active,
  proposal,
  review,
  refresh,
}: {
  thesisId: string;
  claim: ThesisClaimOut;
  active: boolean;
  proposal: ClaimReviewProposalOut;
  review: ReviewOut | undefined;
  refresh: () => void;
}) {
  const t = useTranslations("theses.review");
  const status = useTranslations("thesis.status");
  const accept = useAcceptThesisReviewProposal(thesisId, proposal.id);
  const dismiss = useDismissThesisReviewProposal(thesisId, proposal.id);
  const [confirming, setConfirming] = useState(false);
  const [reason, setReason] = useState("");
  const stale =
    !active ||
    review?.status === "stale" ||
    (!!review && review.revision_id !== claim.revision_id) ||
    claim.status !== proposal.status_at_review ||
    (claim.events?.[claim.events.length - 1]?.id ?? null) !==
      proposal.last_claim_event_id_at_review;
  const acceptable =
    !stale &&
    review?.status === "done" &&
    review.revision_id === claim.revision_id &&
    proposal.suggested_status !== null &&
    proposal.assessment === "sufficient";
  const pending = accept.isPending || dismiss.isPending;
  const error = accept.error || dismiss.error;
  return (
    <section
      aria-label={t("proposalBadge")}
      className="flex flex-col gap-3 rounded-md border border-warn p-3 text-[13px] [overflow-wrap:anywhere]"
    >
      <span className="w-fit rounded-full bg-warn-soft px-2 py-1 text-xs font-medium text-warn">
        {t("proposalBadge")}
      </span>
      <p className="font-medium">
        {proposal.suggested_status === "broken"
          ? t("possibleBreak")
          : proposal.suggested_status
            ? t("suggestedStatus", { status: status(proposal.suggested_status) })
            : t("insufficient")}
      </p>
      <p className="whitespace-pre-wrap">{proposal.rationale}</p>
      <Provenance source={proposal.source} asOf={proposal.as_of} />
      {!proposal.evidence.length && <p>{t("noEvidence")}</p>}
      <ul className="flex flex-col gap-2">
        {proposal.evidence.map((item, i) => (
          <li
            key={i}
            className={`rounded-md border p-3 ${item.is_rumor ? "border-rumor border-dashed bg-rumor-soft" : "border-border"}`}
          >
            {item.is_rumor && <p className="font-medium text-rumor">{t("rumor")}</p>}
            {item.ref && <p>{item.ref}</p>}
            {item.url && isHttpUrl(item.url) && (
              <a
                className="text-accent underline"
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {item.url}
              </a>
            )}
            <Provenance source={item.source} asOf={item.as_of} />
          </li>
        ))}
      </ul>
      {review && <ThesisReviewRun review={review} />}
      {!review && <p className="text-warn">{t("unverified")}</p>}
      {stale && <p className="text-warn">{t("stale")}</p>}
      {acceptable && !confirming && (
        <button
          className={`${thesisButton} w-fit`}
          disabled={pending}
          onClick={() => setConfirming(true)}
        >
          {t("accept")}
        </button>
      )}
      {acceptable && confirming && (
        <div
          role="group"
          aria-label={t("acceptConfirm")}
          className="flex flex-col gap-2 rounded-md bg-warn-soft p-3"
        >
          <p>{t("confirmHint", { status: status(proposal.suggested_status!) })}</p>
          <div className="flex flex-wrap gap-2">
            <button
              className={thesisButton}
              disabled={pending}
              onClick={() =>
                accept.mutate(
                  {
                    expected_status: proposal.status_at_review,
                    expected_last_event_id: proposal.last_claim_event_id_at_review,
                  },
                  { onSuccess: () => setConfirming(false) },
                )
              }
            >
              {t("acceptConfirm")}
            </button>
            <button
              className={thesisButton}
              disabled={pending}
              onClick={() => setConfirming(false)}
            >
              {t("cancel")}
            </button>
          </div>
        </div>
      )}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (reason.trim()) dismiss.mutate({ reason: reason.trim() });
        }}
        className="flex flex-col gap-2"
      >
        <label>
          {t("dismissReason")}
          <textarea
            className="min-h-11 w-full rounded-md border border-border bg-surface px-3 py-2 text-text"
            value={reason}
            maxLength={10000}
            required
            disabled={pending}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
        <button
          className={`${thesisButton} w-fit`}
          disabled={pending || !reason.trim()}
          type="submit"
        >
          {t("dismiss")}
        </button>
      </form>
      {error && (
        <div role="alert" className="text-warn">
          <p>{t(error instanceof ApiError && error.status === 409 ? "conflict" : "loadError")}</p>
          <button
            className={`${thesisButton} mt-2`}
            onClick={() => {
              setConfirming(false);
              accept.reset();
              dismiss.reset();
              refresh();
            }}
          >
            {t("refresh")}
          </button>
        </div>
      )}
    </section>
  );
}
