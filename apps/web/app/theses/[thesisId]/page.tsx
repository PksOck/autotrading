import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/common/PageHeader";
import { ThesisDetail } from "@/components/theses/ThesisDetail";

export default async function Page({ params }: { params: Promise<{ thesisId: string }> }) {
  const { thesisId } = await params;
  const t = await getTranslations("thesis");
  return (
    <>
      <PageHeader title={t("title")} kicker="SCR-09" />
      <ThesisDetail thesisId={thesisId} />
    </>
  );
}
