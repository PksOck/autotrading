"use client";

import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { AnalysisStatusPill } from "@/components/analysis/AnalysisStatusPill";
import { TriggerList } from "@/components/analysis/DecisionCardPanel";
import { HorizonCard } from "@/components/analysis/HorizonCard";
import { ActionPill, type Horizon } from "@/components/analysis/outlook";
import { CreateThesisButton } from "@/components/theses/CreateThesisButton";
import { useBars, usePortfolio } from "@/lib/api/hooks";
import type { AnalysisOut } from "@/lib/api/types";
import { cn } from "@/lib/cn";

function Price({ symbol }: { symbol: string }) {
  const t = useTranslations("analysisPage.price");
  const format = useFormatter();
  const { data } = useBars(symbol, "1m");
  const bars = data?.bars ?? [];
  const last = bars.at(-1);
  const prev = bars.at(-2);
  const change = last && prev && prev.close > 0 ? last.close / prev.close - 1 : null;
  return (
    <div className="flex flex-col" data-testid="header-price">
      <span className="label">{t("label")}</span>
      {last ? (
        <>
          <span className="num text-xl font-medium">
            {format.number(last.close, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          {change != null && (
            <span className={cn("num text-xs", change >= 0 ? "text-pos" : "text-neg")}>
              {t("change", {
                pct: format.number(change, {
                  style: "percent",
                  maximumFractionDigits: 2,
                  signDisplay: "exceptZero",
                }),
              })}
            </span>
          )}
          <span className="text-xs text-text-3">
            {t("source", {
              source: data?.provenance?.source ?? "–",
              date: format.dateTime(new Date(last.day), { dateStyle: "medium" }),
            })}
          </span>
        </>
      ) : (
        <span className="text-[15px] text-text-3">{t("none")}</span>
      )}
    </div>
  );
}

function Position({ symbol }: { symbol: string }) {
  const t = useTranslations("analysisPage.position");
  const format = useFormatter();
  const { data } = usePortfolio();
  const pos = data?.positions.find(
    (p) => p.symbol.toUpperCase() === symbol.toUpperCase() && p.quantity !== 0,
  );
  const money = (v: number) =>
    format.number(v, {
      style: "currency",
      currency: pos?.currency ?? "USD",
      maximumFractionDigits: 0,
    });
  return (
    <div className="flex flex-col" data-testid="header-position">
      <span className="label">{t("label")}</span>
      {pos ? (
        <>
          <span className="num text-xl font-medium">{t("shares", { qty: pos.quantity })}</span>
          {pos.market_value != null && (
            <span className="num text-xs text-text-2">
              {t("value", { value: money(pos.market_value) })}
            </span>
          )}
          {pos.unrealized_pnl != null && (
            <span className={cn("num text-xs", pos.unrealized_pnl >= 0 ? "text-pos" : "text-neg")}>
              {t("pnl", {
                pnl: format.number(pos.unrealized_pnl, {
                  style: "currency",
                  currency: pos.currency,
                  maximumFractionDigits: 0,
                  signDisplay: "exceptZero",
                }),
              })}
            </span>
          )}
        </>
      ) : (
        <span className="text-[15px] text-text-3">{t("none")}</span>
      )}
    </div>
  );
}

/** SCR-06 top: everything needed for the decision (ADR-0014 §6). */
export function DecisionHeader({
  run,
  stepCount,
  horizon,
  onHorizon,
  children,
}: {
  run: AnalysisOut;
  stepCount: number;
  horizon: Horizon;
  onHorizon: (h: Horizon) => void;
  children?: React.ReactNode;
}) {
  const t = useTranslations("analysisPage");
  const card = useTranslations("analysisPage.card");
  const actions = useTranslations("analysisPage.action");
  const format = useFormatter();
  const c = run.card;
  const rating = c?.rating ?? run.rating;
  const implied = c?.control.implied_rating;
  const triggers = (c?.upgrade_if?.length ?? 0) + (c?.downgrade_if?.length ?? 0) > 0;

  return (
    <header className="card flex flex-col gap-4 p-4 sm:p-5" aria-label={t("runTitle")}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <Link
          href={`/i/${encodeURIComponent(run.symbol)}`}
          className="num text-[28px] leading-[34px] font-medium text-text no-underline hover:text-accent"
        >
          {run.symbol}
        </Link>
        {run.name && <span className="text-text-2">{run.name}</span>}
        <AnalysisStatusPill status={run.status} />
        <span
          data-testid="analysis-engine"
          className="rounded-full bg-surface-2 px-2 text-xs leading-5 text-text-2"
        >
          {t.has(`engines.${run.engine}`)
            ? t(`engines.${run.engine}` as "engines.etf")
            : run.engine}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)_minmax(0,1fr)]">
        <div className="col-span-2 flex flex-col gap-1.5 md:col-span-1" data-testid="header-action">
          <span className="label">{t("agentsSay")}</span>
          {rating ? (
            <>
              <span
                className="flex flex-wrap items-center gap-2"
                aria-label={t("agentsLabel", {
                  action: actions.has(rating) ? actions(rating as "Buy") : rating,
                })}
              >
                <ActionPill rating={rating} size="lg" />
                {c?.conviction != null && (
                  <span className="num text-[13px] text-text-2" data-testid="header-conviction">
                    {card("conviction")} {card("convictionValue", { n: c.conviction })}
                  </span>
                )}
                {c?.size_class && (
                  <span className="text-[13px] text-text-2">· {card(`range.${c.size_class}`)}</span>
                )}
              </span>
              {t.has(`actionHint.${rating}`) && (
                <p className="text-[13px] text-text-2">
                  {t(`actionHint.${rating}` as "actionHint.Hold")}
                </p>
              )}
              <span className="flex flex-wrap items-center gap-2 text-xs text-text-3">
                <span>{t("englishRating", { rating })}</span>
                {implied && (
                  <span
                    data-testid="control-chip"
                    className={cn(
                      "rounded-full px-2 leading-5 font-medium",
                      implied === rating ? "bg-pos-soft text-pos" : "bg-warn-soft text-warn",
                    )}
                  >
                    {implied === rating
                      ? t("controlAgrees")
                      : t("controlDiffers", {
                          action: actions.has(implied) ? actions(implied as "Buy") : implied,
                        })}
                  </span>
                )}
              </span>
              {c?.confidence === "low" && (
                <p className="rounded-md bg-warn-soft px-3 py-2 text-[13px] text-warn">
                  {card("lowConfidence")}
                </p>
              )}
            </>
          ) : (
            <span className="text-[15px] text-text-3">{t("rating.none")}</span>
          )}
        </div>
        <Price symbol={run.symbol} />
        <Position symbol={run.symbol} />
      </div>

      <section
        className="flex flex-col gap-2"
        aria-label={t("outlook.title")}
        data-testid="outlook"
      >
        <h2 className="text-base font-semibold">{t("outlook.title")}</h2>
        {run.outlook ? (
          <div className="grid gap-3 md:grid-cols-3">
            {run.outlook.horizons.map((h) => (
              <HorizonCard
                key={h.horizon}
                outlook={h}
                selected={h.horizon === horizon}
                onSelect={() => onHorizon(h.horizon)}
              />
            ))}
          </div>
        ) : (
          <p className="text-[13px] text-text-3">{t("outlook.none")}</p>
        )}
        <p className="text-xs text-text-3">{t("outlook.note")}</p>
      </section>

      {c && triggers && (
        <section
          className="flex flex-col gap-3"
          aria-label={t("change.title")}
          data-testid="rating-change"
        >
          <h2 className="text-base font-semibold">{t("change.title")}</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <TriggerList title={t("change.up")} items={c.upgrade_if ?? []} tone="text-pos" />
            <TriggerList title={t("change.down")} items={c.downgrade_if ?? []} tone="text-neg" />
          </div>
          {run.status === "done" && <CreateThesisButton runId={run.id} />}
        </section>
      )}

      {run.caveats.length > 0 && (
        <ul className="flex flex-wrap gap-2" aria-label={t("caveatHint")}>
          {run.caveats.map((cv) => (
            <li
              key={cv}
              className="rounded-full bg-warn-soft px-2.5 text-xs leading-6 font-medium text-warn"
            >
              {t.has(`caveats.${cv}`) ? t(`caveats.${cv}` as "caveats.rumor_only") : cv}
            </li>
          ))}
        </ul>
      )}
      <p className="text-[13px] text-text-2">
        {t("tradeDate")}:{" "}
        <span className="num">
          {format.dateTime(new Date(run.trade_date), { dateStyle: "medium" })}
        </span>
        {" · "}
        {t("stepCount", { count: stepCount })}
      </p>
      {children}
      <p className="rounded-md bg-surface-2 px-3 py-2 text-[13px] text-text-2">{t("opinion")}</p>
    </header>
  );
}
