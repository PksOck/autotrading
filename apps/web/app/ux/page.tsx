import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/common/PageHeader";
import { UxDemos } from "@/components/ux/UxDemos";

/** Living style guide for DESIGN.md §2 and §8–§10 (BL-019). */
export default async function UxPage() {
  const t = await getTranslations("ux");
  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} sample />
      <UxDemos />
    </>
  );
}
