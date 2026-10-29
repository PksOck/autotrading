"use client";

import Link from "next/link";
import { useFormatter, useTranslations } from "next-intl";
import { TranslatedText } from "@/components/common/TranslatedText";
import { useSignal } from "@/lib/api/hooks";
import { ApiError } from "@/lib/api/client";
import { isSignalId } from "@/lib/entities";

/** Read-only view of one signal, independent of the current inbox filters. */
export function SignalDetail({ signalId }: { signalId: string }) {
  const t = useTranslations();
  const format = useFormatter();
  const { data, isLoading, error, refetch } = useSignal(signalId);
  const invalid = !isSignalId(signalId) || (error instanceof ApiError && error.status === 422);
  const missing = error instanceof ApiError && error.status === 404;
  if (invalid || missing || error) {
    return (
      <div role="alert" className="space-y-3">
        <p>
          {t(
            invalid
              ? "signalDetail.invalid"
              : missing
                ? "signalDetail.missing"
                : "signalDetail.failed",
          )}
        </p>
        {!invalid && !missing && (
          <button
            type="button"
            onClick={() => void refetch()}
            className="rounded-md border border-border px-3 py-2"
          >
            {t("signalDetail.retry")}
          </button>
        )}
      </div>
    );
  }
  if (isLoading || !data || data.id.toLowerCase() !== signalId.toLowerCase()) {
    return (
      <div
        aria-busy="true"
        aria-label={t("signalDetail.loading")}
        className="h-40 animate-pulse rounded-md bg-surface-2"
      />
    );
  }
  const timestamp = (value: string) =>
    format.dateTime(new Date(value), { dateStyle: "medium", timeStyle: "short" });
  return (
    <section className="space-y-5">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">{data.symbol}</h2>
        <p>
          <span>{t(`signal.status.${data.status}`)}</span> · {t(`signal.kind.${data.kind}`)}
        </p>
        {data.is_rumor && (
          <p className="rounded-md bg-surface-2 p-3 font-medium">{t("radar.rumor")}</p>
        )}
      </div>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        <dt className="text-text-3">{t("signalDetail.source")}</dt>
        <dd>{t(`signal.source.${data.source}`)}</dd>
        <dt className="text-text-3">{t("signalDetail.direction")}</dt>
        <dd>{t(`signalsPage.direction.${data.direction}`)}</dd>
        <dt className="text-text-3">{t("signal.horizon.label")}</dt>
        <dd>{t(`signal.horizon.${data.horizon}`)}</dd>
        <dt className="text-text-3">{t("signalDetail.created")}</dt>
        <dd>
          <time dateTime={data.created_at}>{timestamp(data.created_at)}</time>
        </dd>
        <dt className="text-text-3">{t("signalDetail.expires")}</dt>
        <dd>
          {data.expires_at ? (
            <time dateTime={data.expires_at}>{timestamp(data.expires_at)}</time>
          ) : (
            t("signalDetail.noExpiry")
          )}
        </dd>
      </dl>
      <div className="space-y-2">
        <h3 className="font-medium">{t("signal.rationale")}</h3>
        <p>
          <TranslatedText original={data.rationale} translations={data.rationale_translations} />
        </p>
      </div>
      <div className="space-y-2">
        <h3 className="font-medium">{t("signalDetail.evidence")}</h3>
        {data.evidence.length ? (
          <ul className="space-y-2">
            {data.evidence.map((item, index) => (
              <li key={index} className="break-words">
                {item.url && /^https?:\/\//i.test(item.url) ? (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent underline"
                  >
                    {item.label || item.url}
                  </a>
                ) : (
                  item.label || item.kind
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-text-3">{t("signalDetail.noEvidence")}</p>
        )}
      </div>
      <Link
        href={`/i/${encodeURIComponent(data.symbol)}`}
        className="inline-flex min-h-12 items-center rounded-md border border-border px-4"
      >
        {t("signalDetail.openInstrument")}
      </Link>
    </section>
  );
}
