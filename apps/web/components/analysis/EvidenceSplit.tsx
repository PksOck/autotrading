"use client";

import { useFormatter, useTranslations } from "next-intl";
import { useEvidenceText } from "@/components/analysis/outlook";
import type { HorizonOutlook, OutlookEvidence } from "@/lib/api/types";
import { cn } from "@/lib/cn";

function Row({ e }: { e: OutlookEvidence }) {
  const t = useTranslations("analysisPage.evidence");
  const format = useFormatter();
  const { label, text } = useEvidenceText();
  return (
    <li
      className="flex flex-col gap-0.5 border-t border-border py-2 first:border-t-0"
      data-testid="evidence-row"
      data-key={e.key}
    >
      <span className="text-[14px] text-text">{label(e.key)}</span>
      <span className="num text-[13px] text-text-2">{text(e)}</span>
      {(e.source || e.as_of) && (
        <span className="text-xs text-text-3">
          {t("provenance", {
            source: e.source ?? "–",
            date: e.as_of ? format.dateTime(new Date(e.as_of), { dateStyle: "medium" }) : "–",
          })}
        </span>
      )}
    </li>
  );
}

function Column({
  title,
  items,
  tone,
  mark,
  testId,
}: {
  title: string;
  items: OutlookEvidence[];
  tone: string;
  mark: string;
  testId: string;
}) {
  const t = useTranslations("analysisPage.evidence");
  return (
    <section
      className="flex min-w-0 flex-col gap-1 rounded-md border border-border p-3"
      aria-label={title}
      data-testid={testId}
    >
      <h4
        className={cn(
          "flex items-center gap-1.5 text-xs font-semibold tracking-wide uppercase",
          tone,
        )}
      >
        <span aria-hidden>{mark}</span>
        {title} <span className="num font-normal">({items.length})</span>
      </h4>
      {items.length ? (
        <ul>
          {items.map((e) => (
            <Row key={e.key} e={e} />
          ))}
        </ul>
      ) : (
        <p className="text-[13px] text-text-3">{t("empty")}</p>
      )}
    </section>
  );
}

/** CMP-32: evidence of one horizon, for growth on the left and against on the right, neutral below. */
export function EvidenceSplit({ outlook }: { outlook: HorizonOutlook }) {
  const t = useTranslations("analysisPage");
  const { label } = useEvidenceText();
  const by = (s: OutlookEvidence["stance"]) => outlook.evidence.filter((e) => e.stance === s);
  const neutral = by("neutral");
  return (
    <div className="flex flex-col gap-3" data-testid="evidence-split">
      <div className="grid gap-3 md:grid-cols-2">
        <Column
          title={t("evidence.pro")}
          items={by("pro")}
          tone="text-pos"
          mark="▲"
          testId="evidence-pro"
        />
        <Column
          title={t("evidence.contra")}
          items={by("contra")}
          tone="text-neg"
          mark="▼"
          testId="evidence-contra"
        />
      </div>
      {neutral.length > 0 && (
        <Column
          title={t("evidence.neutral")}
          items={neutral}
          tone="text-text-3"
          mark="◆"
          testId="evidence-neutral"
        />
      )}
      {outlook.missing.length > 0 && (
        <p className="text-xs text-text-3">
          {t("outlook.missing", { items: outlook.missing.map(label).join(", ") })}
        </p>
      )}
    </div>
  );
}
