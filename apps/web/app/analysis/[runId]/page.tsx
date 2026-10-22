import { getTranslations } from "next-intl/server";
import { AnalysisView } from "@/components/analysis/AnalysisView";
import { PageHeader } from "@/components/common/PageHeader";

/** SCR-06 Analiza (BL-085). */
export default async function AnalysisPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const t = await getTranslations("analysisPage");
  return (
    <>
      <PageHeader title={t("runTitle")} kicker="SCR-06" />
      <AnalysisView runId={runId} />
    </>
  );
}
