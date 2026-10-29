import { getTranslations } from "next-intl/server";
import Link from "next/link";
import { AnalysisQuotaLine } from "@/components/analysis/AnalysisQuotaLine";
import { AnalysisIndex } from "@/components/analysis/AnalysisRunList";
import { Suspense } from "react";
import { PageHeader } from "@/components/common/PageHeader";

/** Index of deep-analysis runs; the detail is SCR-06 at /analysis/[runId] (BL-085). */
export default async function AnalysesPage() {
  const t = await getTranslations("analysisPage");
  return (
    <>
      <PageHeader title={t("title")} kicker="SCR-06" description={t("subtitle")} />
      <AnalysisQuotaLine />
      <section className="card overflow-hidden" aria-label={t("indexLabel")}>
        <Suspense><AnalysisIndex /></Suspense>
      </section>
      <p className="mt-4 text-[13px]">
        <Link href="/entries" className="text-accent">
          {t("emptyAction")} →
        </Link>
      </p>
    </>
  );
}
