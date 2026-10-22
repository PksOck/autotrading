"use client";

import { useTranslations } from "next-intl";
import { quotaReached, useAnalysisQuota } from "@/lib/api/hooks";

/** "Danes X od Y" deep analyses; hidden when there is no limit (BL-093). */
export function AnalysisQuotaLine() {
  const t = useTranslations("analysisPage");
  const { data } = useAnalysisQuota();
  if (!data || data.limit <= 0) return null;
  return (
    <p className="mb-3 text-[13px] text-text-2" data-testid="analysis-quota">
      {t("quota", { used: data.used, limit: data.limit })}
      {quotaReached(data) && <span className="ml-2 text-warn">{t("launch.limitReached")}</span>}
    </p>
  );
}
