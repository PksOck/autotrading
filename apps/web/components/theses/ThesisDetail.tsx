"use client";

import { useState } from "react";
import Link from "next/link";
import { useFormatter, useTranslations } from "next-intl";
import {
  useChangeClaimStatus,
  useConfirmThesisRevision,
  usePatchThesisRevision,
  useThesis,
  useThesisReviews,
  useThesisReviewProposals,
} from "@/lib/api/hooks";
import type {
  ThesisClaimOut,
  ThesisClaimStatusChange,
  ThesisEvidence,
  ThesisRevisionOut,
} from "@/lib/api/types";
import { isHttpUrl, thesisErrorKey } from "@/lib/thesis";
import { LocalTime } from "./LocalTime";
import { ThesisCheck } from "./ThesisCheck";
import { ThesisReviewProposals, ThesisReviewRun } from "./ThesisReviewProposals";
import { thesisButton } from "./styles";

const field = "min-h-11 w-full rounded-md border border-border bg-surface px-3 py-2 text-text";
const userStatuses = ["open", "confirmed", "weakening", "broken"] as const;

function Provenance({ source, asOf }: { source: string; asOf: string }) {
  const t = useTranslations("thesis");
  return (
    <p className="text-xs text-text-3">
      {t("source")}: {source}
      {" · "}
      {t("asOf")}: <LocalTime value={asOf} />
    </p>
  );
}

function Evidence({ item }: { item: ThesisEvidence }) {
  const t = useTranslations("thesis");
  const safeUrl = item.url && /^https?:\/\//i.test(item.url) ? item.url : null;
  return (
    <li
      className={`rounded-md border p-3 text-[13px] [overflow-wrap:anywhere] ${item.is_rumor ? "border-rumor border-dashed bg-rumor-soft" : "border-border"}`}
    >
      {item.is_rumor && <p className="font-medium text-rumor">{t("rumor")}</p>}
      {item.ref && <p>{item.ref}</p>}
      {safeUrl && (
        <a
          href={safeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent underline"
        >
          {safeUrl}
        </a>
      )}
      <Provenance source={item.source} asOf={item.as_of} />
    </li>
  );
}

function EventHistory({ claim }: { claim: ThesisClaimOut }) {
  const t = useTranslations("thesis");
  return (
    <details className="border-t border-border pt-3">
      <summary className="min-h-11 cursor-pointer text-[13px] text-text-2">
        {t("history", { count: claim.events?.length ?? 0 })}
      </summary>
      {!claim.events?.length ? (
        <p className="text-[13px] text-text-3">{t("noEvents")}</p>
      ) : (
        <ol className="flex flex-col gap-3">
          {claim.events.map((event) => (
            <li key={event.id} className="rounded-md bg-surface-2 p-3">
              <p className="flex flex-wrap items-center gap-2">
                <ThesisCheck status={event.from_status} />
                <span aria-hidden="true">→</span>
                <ThesisCheck status={event.to_status} />
                <span className="text-xs text-text-3">{t(`actor.${event.actor}`)}</span>
              </p>
              <p className="my-2 whitespace-pre-wrap text-[13px]">{event.rationale}</p>
              <Provenance source={event.source} asOf={event.as_of} />
              <p className="mt-1 text-xs text-text-3">
                {t("recorded")}: <LocalTime value={event.created_at} />
              </p>
              <ul className="mt-2 flex flex-col gap-2">
                {event.evidence.map((item, index) => (
                  <Evidence key={index} item={item} />
                ))}
              </ul>
            </li>
          ))}
        </ol>
      )}
    </details>
  );
}

type EvidenceInput = {
  key: number;
  source: string;
  as_of: string;
  url: string;
  ref: string;
  is_rumor: boolean;
};

function ClaimStatusForm({ thesisId, claim }: { thesisId: string; claim: ThesisClaimOut }) {
  const t = useTranslations("thesis");
  const format = useFormatter();
  const mutation = useChangeClaimStatus(thesisId, claim.id);
  const [status, setStatus] = useState<ThesisClaimStatusChange["to_status"]>("open");
  const [rationale, setRationale] = useState("");
  const [rows, setRows] = useState<EvidenceInput[]>([]);
  const [nextKey, setNextKey] = useState(0);
  const [invalid, setInvalid] = useState(false);
  const [saved, setSaved] = useState(false);
  const updateRow = (key: number, patch: Partial<EvidenceInput>) =>
    setRows((previous) => previous.map((row) => (row.key === key ? { ...row, ...patch } : row)));
  return (
    <details className="border-t border-border pt-3">
      <summary className="min-h-11 cursor-pointer text-[13px] text-accent">
        {t("changeStatus")}
      </summary>
      <form
        className="flex flex-col gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          setSaved(false);
          if (
            !rationale.trim() ||
            (status !== "open" && !rows.length) ||
            rows.some(
              (row) =>
                !row.source.trim() ||
                !row.as_of ||
                Number.isNaN(new Date(row.as_of).getTime()) ||
                (!row.url.trim() && !row.ref.trim()) ||
                (row.url.trim() !== "" && !isHttpUrl(row.url.trim())),
            )
          ) {
            setInvalid(true);
            return;
          }
          setInvalid(false);
          mutation.mutate(
            {
              to_status: status,
              expected_status: claim.status,
              rationale: rationale.trim(),
              evidence: rows.map((row) => ({
                source: row.source.trim(),
                as_of: new Date(row.as_of).toISOString(),
                is_rumor: row.is_rumor,
                url: row.url.trim() || null,
                ref: row.ref.trim() || null,
              })),
            },
            {
              onSuccess: () => {
                setSaved(true);
                setRationale("");
                setRows([]);
              },
            },
          );
        }}
      >
        <fieldset disabled={mutation.isPending} className="flex min-w-0 flex-col gap-3">
          <label className="text-[13px]">
            {t("newStatus")}
            <select
              className={field}
              value={status}
              onChange={(e) => {
                setSaved(false);
                setStatus(e.target.value as typeof status);
              }}
            >
              {userStatuses.map((value) => (
                <option value={value} key={value}>
                  {t(`status.${value}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="text-[13px]">
            {t("rationale")}
            <textarea
              className={field}
              required
              maxLength={10000}
              value={rationale}
              onChange={(e) => {
                setSaved(false);
                setRationale(e.target.value);
              }}
            />
          </label>
          <p className="text-xs text-text-3">{t("evidenceHint")}</p>
          {rows.map((row, index) => (
            <fieldset
              key={row.key}
              className="flex min-w-0 flex-col gap-3 rounded-md border border-border p-3"
            >
              <legend className="px-1 text-[13px]">
                {t("evidenceRow", { number: format.number(index + 1) })}
              </legend>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-[13px]">
                  {t("source")}
                  <input
                    className={field}
                    required
                    maxLength={64}
                    value={row.source}
                    onChange={(e) => updateRow(row.key, { source: e.target.value })}
                  />
                </label>
                <label className="text-[13px]">
                  {t("asOfLocal")}
                  <input
                    className={field}
                    type="datetime-local"
                    required
                    value={row.as_of}
                    onChange={(e) => updateRow(row.key, { as_of: e.target.value })}
                  />
                </label>
                <label className="text-[13px]">
                  {t("url")}
                  <input
                    className={field}
                    type="url"
                    pattern="https?://.+"
                    maxLength={2000}
                    value={row.url}
                    onChange={(e) => updateRow(row.key, { url: e.target.value })}
                  />
                </label>
                <label className="text-[13px]">
                  {t("ref")}
                  <input
                    className={field}
                    maxLength={10000}
                    value={row.ref}
                    onChange={(e) => updateRow(row.key, { ref: e.target.value })}
                  />
                </label>
              </div>
              <label
                className={`flex min-h-11 items-center gap-2 text-[13px] ${row.is_rumor ? "text-rumor" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={row.is_rumor}
                  onChange={(e) => updateRow(row.key, { is_rumor: e.target.checked })}
                />
                {t("rumor")}
              </label>
              <button
                className={`${thesisButton} w-fit`}
                type="button"
                onClick={() =>
                  setRows((previous) => previous.filter((item) => item.key !== row.key))
                }
              >
                {t("removeEvidence")}
              </button>
            </fieldset>
          ))}
          <button
            className={`${thesisButton} w-fit`}
            type="button"
            disabled={rows.length >= 100}
            onClick={() => {
              setRows([
                ...rows,
                { key: nextKey, source: "", as_of: "", url: "", ref: "", is_rumor: false },
              ]);
              setNextKey(nextKey + 1);
              setSaved(false);
            }}
          >
            {t("addEvidence")}
          </button>
          <button className={`${thesisButton} w-fit`} type="submit">
            {t(mutation.isPending ? "saving" : "saveStatus")}
          </button>
        </fieldset>
        {invalid && (
          <p role="alert" className="text-warn">
            {t("errors.evidenceRequired")}
          </p>
        )}
        {mutation.error && (
          <p role="alert" className="text-warn">
            {t(thesisErrorKey(mutation.error))}
          </p>
        )}
        {saved && (
          <p role="status" className="text-pos">
            {t("saved")}
          </p>
        )}
      </form>
    </details>
  );
}

type ClaimEdit = { statement: string; invalidated_if: string };

function DraftEditor({ revision }: { revision: ThesisRevisionOut }) {
  const t = useTranslations("thesis");
  const format = useFormatter();
  const patch = usePatchThesisRevision(revision.thesis_id, revision.id);
  const confirm = useConfirmThesisRevision(revision.thesis_id, revision.id);
  // Only local edits live in state; untouched fields follow the server copy, and a
  // save sends only the claims the user changed, so it never overwrites newer data.
  const [edits, setEdits] = useState<Record<string, ClaimEdit>>({});
  const server = (revision.claims ?? []).map((claim) => ({
    id: claim.id,
    statement: claim.statement,
    invalidated_if: claim.invalidated_if ?? "",
  }));
  const claims = server.map((claim) => ({ ...claim, ...edits[claim.id] }));
  const byId = new Map(server.map((claim) => [claim.id, claim]));
  const isEdited = (claim: (typeof claims)[number]) => {
    const original = byId.get(claim.id);
    return (
      claim.statement !== original?.statement || claim.invalidated_if !== original.invalidated_if
    );
  };
  const changed = claims.filter(isEdited);
  const setClaims = (next: typeof claims) =>
    setEdits(
      Object.fromEntries(
        next
          .filter(isEdited)
          .map((claim) => [
            claim.id,
            { statement: claim.statement, invalidated_if: claim.invalidated_if },
          ]),
      ),
    );
  const [saved, setSaved] = useState(false);
  const dirty = changed.length > 0;
  const pending = patch.isPending || confirm.isPending;
  const invalid = claims.some((claim) => !claim.statement.trim());
  return (
    <div className="flex flex-col gap-4">
      <p className="text-[13px] text-text-2">{t("draftHint")}</p>
      <form
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          event.preventDefault();
          patch.mutate(
            {
              expected_version: revision.version,
              claims: changed.map((claim) => ({
                ...claim,
                statement: claim.statement.trim(),
                invalidated_if: claim.invalidated_if.trim() || null,
              })),
            },
            {
              onSuccess: () => {
                setEdits({});
                setSaved(true);
              },
            },
          );
        }}
      >
        <fieldset disabled={pending} className="flex min-w-0 flex-col gap-4">
          {claims.map((claim, index) => (
            <fieldset
              key={claim.id}
              className="flex min-w-0 flex-col gap-2 rounded-md border border-border p-3"
            >
              <legend className="px-1 text-[13px]">
                {t("claimNumber", { number: format.number(index + 1) })}
              </legend>
              <label className="text-[13px]">
                {t("statement")}
                <textarea
                  className={field}
                  required
                  maxLength={10000}
                  value={claim.statement}
                  onChange={(e) => {
                    setClaims(
                      claims.map((item) =>
                        item.id === claim.id ? { ...item, statement: e.target.value } : item,
                      ),
                    );
                    setSaved(false);
                  }}
                />
              </label>
              <label className="text-[13px]">
                {t("invalidatedIf")}
                <textarea
                  className={field}
                  maxLength={10000}
                  value={claim.invalidated_if}
                  onChange={(e) => {
                    setClaims(
                      claims.map((item) =>
                        item.id === claim.id ? { ...item, invalidated_if: e.target.value } : item,
                      ),
                    );
                    setSaved(false);
                  }}
                />
              </label>
            </fieldset>
          ))}
          <button
            className={`${thesisButton} w-fit`}
            type="submit"
            disabled={!dirty || invalid || !claims.length}
          >
            {t(patch.isPending ? "saving" : "saveDraft")}
          </button>
        </fieldset>
      </form>
      {saved && !dirty && (
        <p role="status" className="text-pos">
          {t("saved")}
        </p>
      )}
      {dirty && <p className="text-xs text-warn">{t("saveBeforeConfirm")}</p>}
      <button
        className={`${thesisButton} w-fit`}
        disabled={pending || dirty || invalid || !claims.length}
        onClick={() => confirm.mutate()}
      >
        {t(confirm.isPending ? "confirming" : "confirm")}
      </button>
      {(patch.error || confirm.error) && (
        <p role="alert" className="text-warn">
          {t(thesisErrorKey(patch.error || confirm.error))}
        </p>
      )}
    </div>
  );
}

export function ThesisDetail({ thesisId }: { thesisId: string }) {
  const t = useTranslations("thesis");
  const reviewT = useTranslations("theses.review");
  const format = useFormatter();
  const { data: thesis, isLoading, error, refetch } = useThesis(thesisId);
  const reviewsQuery = useThesisReviews(thesisId, 30, 0, true);
  const proposalsQuery = useThesisReviewProposals(thesisId);
  const reviews = Array.isArray(reviewsQuery.data) ? reviewsQuery.data : [];
  const proposals = Array.isArray(proposalsQuery.data) ? proposalsQuery.data : [];
  const refreshReviews = () => {
    void refetch();
    void reviewsQuery.refetch();
    void proposalsQuery.refetch();
  };
  if (isLoading)
    return <div className="card h-64 animate-pulse" aria-busy="true" aria-label={t("loading")} />;
  if (error)
    return (
      <div className="card p-5" role="alert">
        <p>{t(thesisErrorKey(error))}</p>
        <button className={`${thesisButton} mt-3`} onClick={() => void refetch()}>
          {t("retry")}
        </button>
      </div>
    );
  if (!thesis) return null;
  return (
    <div className="flex flex-col gap-5">
      <Link href="/theses" className="text-[13px] text-accent">
        {t("back")}
      </Link>
      <header className="card flex flex-col gap-2 p-4">
        <h2 className="text-xl font-semibold">
          <Link
            className="num text-accent"
            href={`/i/${encodeURIComponent(thesis.instrument.symbol)}`}
          >
            {thesis.instrument.symbol}
          </Link>{" "}
          {thesis.instrument.name}
        </h2>
        <Provenance source={thesis.source} asOf={thesis.as_of} />
      </header>
      <section aria-label={reviewT("title")} className="card flex flex-col gap-3 p-4">
        <h2 className="text-base font-semibold">{reviewT("title")}</h2>
        {(reviewsQuery.isLoading || proposalsQuery.isLoading) && (
          <p aria-busy="true">{reviewT("loading")}</p>
        )}
        {reviewsQuery.error || proposalsQuery.error ? (
          <p role="alert">{reviewT("loadError")}</p>
        ) : (
          !reviewsQuery.isLoading &&
          !reviews.length && <p className="text-[13px] text-text-2">{reviewT("empty")}</p>
        )}
        {reviews.map((review) => (
          <ThesisReviewRun key={review.id} review={review} />
        ))}
        <button className={`${thesisButton} w-fit`} onClick={refreshReviews}>
          {reviewT("refresh")}
        </button>
      </section>
      {!thesis.revisions.some((revision) => revision.status === "active") && (
        <p className="text-[13px] text-text-2">{t("noActiveHint")}</p>
      )}
      {thesis.revisions.map((revision) => (
        <section
          key={revision.id}
          className="card flex flex-col gap-4 p-4 sm:p-5"
          aria-label={t("versionLabel", {
            version: format.number(revision.version),
            status: t(`revision.${revision.status}`),
          })}
        >
          <h2 className="flex flex-wrap items-center gap-2 text-base font-semibold">
            {t("version", { version: format.number(revision.version) })}
            <span className="rounded-full bg-surface-2 px-2 py-1 text-xs font-medium text-text-2">
              {t(`revision.${revision.status}`)}
            </span>
          </h2>
          <Provenance source={revision.source} asOf={revision.as_of} />
          <Link
            href={`/analysis/${encodeURIComponent(revision.analysis_run_id)}`}
            className="text-[13px] text-accent"
          >
            {t("analysis")}
          </Link>
          {revision.delta_note && <p className="text-[13px] text-text-2">{revision.delta_note}</p>}
          {revision.status === "draft" ? (
            <DraftEditor revision={revision} />
          ) : (
            <ul className="flex flex-col gap-4">
              {(revision.claims ?? []).map((claim) => (
                <li
                  key={claim.id}
                  className="flex flex-col gap-3 rounded-md border border-border p-3 [overflow-wrap:anywhere]"
                >
                  <ThesisCheck status={claim.status} />
                  <p className="whitespace-pre-wrap">{claim.statement}</p>
                  {claim.invalidated_if && (
                    <p className="whitespace-pre-wrap text-[13px] text-text-2">
                      {t("invalidatedIf")}: {claim.invalidated_if}
                    </p>
                  )}
                  {claim.expires_at && (
                    <p className="text-xs text-text-3">
                      {t("expires")}: <LocalTime value={claim.expires_at} />
                    </p>
                  )}
                  <Provenance source={claim.source} asOf={claim.as_of} />
                  <ThesisReviewProposals
                    thesisId={thesis.id}
                    claim={claim}
                    active={revision.status === "active"}
                    proposals={proposals}
                    reviews={reviews}
                    refresh={refreshReviews}
                  />
                  {revision.status === "active" && (
                    <ClaimStatusForm thesisId={thesis.id} claim={claim} />
                  )}
                  <EventHistory claim={claim} />
                </li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </div>
  );
}
