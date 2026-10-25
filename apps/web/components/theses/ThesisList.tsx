"use client";

import { useState } from "react";
import Link from "next/link";
import { useFormatter, useTranslations } from "next-intl";
import { useTheses } from "@/lib/api/hooks";
import { ThesisCheck } from "./ThesisCheck";
import { LocalTime } from "./LocalTime";
import { thesisButton } from "./styles";

const statuses = ["open", "confirmed", "weakening", "broken", "expired"] as const;

export function ThesisList() {
  const t = useTranslations("thesis");
  const format = useFormatter();
  const [symbol, setSymbol] = useState("");
  const [offset, setOffset] = useState(0);
  const { data, isLoading, error, refetch } = useTheses(symbol.trim() || undefined, 30, offset);
  return (
    <section className="flex flex-col gap-4" aria-label={t("title")}>
      <label className="flex flex-col gap-1 text-[13px]">
        {t("filter")}
        <input
          className="rounded-md border border-border bg-surface px-3 py-2"
          value={symbol}
          maxLength={20}
          onChange={(e) => {
            setSymbol(e.target.value);
            setOffset(0);
          }}
        />
      </label>
      {isLoading ? (
        <div className="card h-40 animate-pulse" aria-busy="true" aria-label={t("loading")} />
      ) : error ? (
        <div className="card p-4" role="alert">
          <p>{t("errors.loadFailed")}</p>
          <button className={`${thesisButton} mt-2`} onClick={() => void refetch()}>
            {t("retry")}
          </button>
        </div>
      ) : !data?.length ? (
        <div className="card p-5">
          <p>{t("empty")}</p>
          <Link className="text-accent" href="/analysis">
            {t("goAnalysis")}
          </Link>
        </div>
      ) : (
        <ul className="flex flex-col gap-3">
          {data.map((thesis) => (
            <li key={thesis.id} className="card p-4">
              <Link
                href={`/theses/${thesis.id}`}
                className="flex min-h-11 flex-wrap items-center gap-3 text-text no-underline hover:text-accent"
              >
                <span className="num text-lg font-medium">{thesis.instrument.symbol}</span>{" "}
                <span>{thesis.instrument.name}</span>{" "}
                <span className="text-[13px] text-text-2">
                  {thesis.active_revision_version == null
                    ? t("noActive")
                    : t("activeVersion", {
                        version: format.number(thesis.active_revision_version),
                      })}
                </span>{" "}
                {thesis.latest_draft_id && (
                  <span className="rounded-full bg-accent-soft px-2 py-1 text-xs text-accent">
                    {t("revision.draft")}
                  </span>
                )}
              </Link>
              <dl className="flex flex-wrap gap-x-5 gap-y-2">
                {statuses.map((status) => (
                  <div className="flex items-center gap-2" key={status}>
                    <dt>
                      <ThesisCheck status={status} />
                    </dt>
                    <dd className="num">
                      {format.number(thesis.claim_status_counts[status] ?? 0)}
                    </dd>
                  </div>
                ))}
              </dl>
              <p className="mt-3 text-xs text-text-3">
                {t("updated")} <LocalTime value={thesis.updated_at} />
              </p>
            </li>
          ))}
        </ul>
      )}
      <nav className="flex gap-3" aria-label={t("pagination")}>
        <button
          className={thesisButton}
          disabled={offset === 0 || isLoading}
          onClick={() => setOffset(Math.max(0, offset - 30))}
        >
          {t("previous")}
        </button>
        <button
          className={thesisButton}
          disabled={isLoading || !!error || (data?.length ?? 0) < 30}
          onClick={() => setOffset(offset + 30)}
        >
          {t("next")}
        </button>
      </nav>
    </section>
  );
}
