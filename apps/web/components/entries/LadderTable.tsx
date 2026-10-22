"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { formatMoney, formatNumber } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

/** CMP-15: staged buying ladder. Levels come from the API; the budget split is plain arithmetic. */
export function LadderTable({
  levels,
  currency,
}: {
  levels: { price: number; weight: number }[];
  currency?: string | null;
}) {
  const t = useTranslations("entriesPage.ladder");
  const locale = useAppLocale();
  const [budget, setBudget] = useState("");
  const amount = Number(budget.replace(",", "."));
  const hasBudget = Number.isFinite(amount) && amount > 0;
  if (!levels.length) return <p className="text-[13px] text-text-3">{t("none")}</p>;
  return (
    <div className="flex flex-col gap-2">
      <table className="w-full text-[13px]">
        <thead className="text-left text-xs text-text-3">
          <tr>
            <th className="py-1 font-normal">{t("level")}</th>
            <th className="py-1 font-normal">{t("share")}</th>
            <th className="py-1 text-right font-normal">{t("limit")}</th>
            {hasBudget && <th className="py-1 text-right font-normal">{t("quantity")}</th>}
          </tr>
        </thead>
        <tbody className="num">
          {levels.map((lv, i) => (
            <tr key={lv.price} className="border-t border-border">
              <td className="py-1.5">{i + 1}</td>
              <td className="py-1.5">{formatNumber(locale, lv.weight * 100, 0)} %</td>
              <td className="py-1.5 text-right">
                {currency
                  ? formatMoney(locale, lv.price, currency)
                  : formatNumber(locale, lv.price, 2)}
              </td>
              {hasBudget && (
                <td className="py-1.5 text-right">
                  {formatNumber(locale, Math.floor((amount * lv.weight) / lv.price), 0)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      <label className="flex items-center gap-2 text-xs text-text-3">
        {t("budget")}
        <input
          inputMode="decimal"
          value={budget}
          onChange={(e) => setBudget(e.target.value)}
          placeholder="5000"
          className="num h-8 w-28 rounded-md border border-border bg-surface px-2 text-[13px] text-text"
        />
        {currency}
      </label>
      <p className="text-xs text-text-3">{t("note")}</p>
    </div>
  );
}
