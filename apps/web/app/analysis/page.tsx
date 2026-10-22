import { getTranslations } from "next-intl/server";
import Link from "next/link";
import { AnalysisRunList } from "@/components/analysis/AnalysisRunList";
import { PageHeader } from "@/components/common/PageHeader";

/** Index of deep-analysis runs; the detail is SCR-06 at /analysis/[runId] (BL-085). */
export default async function AnalysesPage() {
  const t = await getTranslations("analysisPage");
  return (
    <>
      <PageHeader title={t("title")} kicker="SCR-06" description={t("subtitle")} />
      <section className="card overflow-hidden" aria-label={t("indexLabel")}>
        <AnalysisRunList />
      </section>
      <p className="mt-4 text-[13px]">
        <Link href="/entries" className="text-accent">
          {t("emptyAction")} →
        </Link>
      </p>
    </>
  );
}
