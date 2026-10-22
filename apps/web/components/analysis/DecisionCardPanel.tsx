"use client";

import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { RatingPill } from "@/components/analysis/RatingPill";
import type { DecisionCard } from "@/lib/api/types";
import { cn } from "@/lib/cn";

/** Diverging bar for a -1..1 value with a centre line; the value is shown as given. */
function ComponentBar({ label, value, weight }: { label: string; value: number | null; weight: number | undefined }) {
  const t = useTranslations("analysisPage.card");
  const format = useFormatter();
  const half = value == null ? 0 : Math.min(1, Math.abs(value)) * 50;
  const pos = (value ?? 0) >= 0;
  return (
    <li className="flex flex-col gap-1">
      <div className="flex flex-wrap items-baseline justify-between gap-x-2 text-[13px]">
        <span className="text-text">{label}</span>
        <span className="text-xs text-text-3">
          {weight != null && t("weight", { pct: format.number(weight * 100, { maximumFractionDigits: 0 }) })}
          {" · "}
          <span className={cn("num", value != null && (pos ? "text-pos" : "text-neg"))}>
            {value == null ? t("noData") : format.number(value, { minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: "exceptZero" })}
          </span>
        </span>
      </div>
      <div
        role="img"
        aria-label={`${label}: ${value == null ? t("noData") : format.number(value, { maximumFractionDigits: 2 })}`}
        className="relative h-2 rounded-full bg-surface-2"
      >
        {value != null && (
          <span
            className={cn("absolute inset-y-0 rounded-full", pos ? "bg-pos" : "bg-neg")}
            style={pos ? { left: "50%", width: `${half}%` } : { right: "50%", width: `${half}%` }}
          />
        )}
        <span className="absolute -inset-y-0.5 left-1/2 w-px bg-text-3" />
      </div>
    </li>
  );
}

function TriggerList({ title, items, tone }: { title: string; items: string[]; tone: string }) {
  const t = useTranslations("analysisPage.card");
  return (
    <section className="flex flex-col gap-1.5">
      <h3 className={cn("text-xs font-semibold tracking-wide uppercase", tone)}>{title}</h3>
      {items.length ? (
        <ul className="flex list-disc flex-col gap-1 pl-5 text-[14px] leading-6 text-text-2 [overflow-wrap:anywhere]">
          {items.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </ul>
      ) : (
        <p className="text-[13px] text-text-3">{t("none")}</p>
      )}
    </section>
  );
}

/** BL-089: structured decision card. All figures come from the API card, only formatted here. */
export function DecisionCardPanel({ card }: { card: DecisionCard }) {
  const t = useTranslations("analysisPage.card");
  const ratings = useTranslations("analysisPage.rating");
  const format = useFormatter();
  const { control } = card;
  const order = ["quality", "valuation", "technical", "risk"];
  const keys = [...order.filter((k) => k in control.components), ...Object.keys(control.components).filter((k) => !order.includes(k))];
  const size = card.size_class;

  return (
    <section className="card flex flex-col gap-5 p-4 sm:p-5" aria-label={t("title")} data-testid="decision-card">
      <div className="flex flex-col gap-1">
        <h2 className="text-base font-semibold">{t("title")}</h2>
        <p className="text-[13px] text-text-3">{t("note")}</p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <section className="flex flex-col gap-3" aria-label={t("control")}>
          <h3 className="text-xs font-semibold tracking-wide text-text-3 uppercase">{t("control")}</h3>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[13px] text-text-2">
            <span className="inline-flex items-center gap-2">
              {t("agents")} <RatingPill rating={card.rating} />
            </span>
            <span className="inline-flex items-center gap-2">
              {t("implied")}
              {control.implied_rating ? <RatingPill rating={control.implied_rating} /> : <span className="text-text-3">{t("noData")}</span>}
            </span>
          </div>
          {control.score == null && <p className="text-[13px] text-text-3">{t("noScore")}</p>}
          <ul className="flex flex-col gap-3">
            {keys.map((k) => (
              <ComponentBar
                key={k}
                label={t.has(`components.${k}`) ? t(`components.${k}` as "components.risk") : k}
                value={control.components[k] ?? null}
                weight={control.weights[k]}
              />
            ))}
          </ul>
          <p className="text-xs text-text-3">{t("coverage", { pct: format.number(control.coverage * 100, { maximumFractionDigits: 0 }) })}</p>
          {card.confidence === "low" && (
            <p data-testid="low-confidence" className="rounded-md bg-warn-soft px-3 py-2 text-[13px] text-warn">
              {t("lowConfidence")}
            </p>
          )}
        </section>

        <div className="flex flex-col gap-4">
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="label">{t("conviction")}</dt>
              <dd className="num text-xl font-medium" data-testid="conviction">
                {card.conviction == null ? <span className="text-[15px] text-text-3">{t("noData")}</span> : t("convictionValue", { n: card.conviction })}
              </dd>
            </div>
            <div>
              <dt className="label">{t("size")}</dt>
              <dd className="flex flex-col" data-testid="size-class">
                {size ? (
                  <>
                    <span className="text-[15px] font-medium">{t(`sizes.${size}`)}</span>
                    <span className="text-xs text-text-3">{t(`range.${size}`)}</span>
                  </>
                ) : (
                  <span className="text-[15px] text-text-3">{t("noSize")}</span>
                )}
              </dd>
            </div>
          </dl>
          <p className="text-xs text-text-3">{t("sizeNote")}</p>
          {(card.delta_note || card.previous) && (
            <div className="flex flex-col gap-1 rounded-md bg-surface-2 px-3 py-2 text-[13px] text-text-2">
              <span className="label">{t("delta")}</span>
              {card.delta_note && <p>{card.delta_note}</p>}
              {card.previous && (
                <Link href={`/analysis/${card.previous.id}`} className="w-fit text-accent hover:underline">
                  {t("previous", {
                    rating: card.previous.rating && ratings.has(card.previous.rating) ? ratings(card.previous.rating as "Buy") : (card.previous.rating ?? t("noData")),
                    date: format.dateTime(new Date(card.previous.trade_date), { dateStyle: "medium" }),
                  })}{" "}
                  →
                </Link>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <TriggerList title={t("upgrade")} items={card.upgrade_if ?? []} tone="text-pos" />
        <TriggerList title={t("downgrade")} items={card.downgrade_if ?? []} tone="text-neg" />
      </div>
    </section>
  );
}
