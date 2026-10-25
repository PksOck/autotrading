import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/common/PageHeader";
import { ThesisList } from "@/components/theses/ThesisList";

export default async function Page() {
  const t = await getTranslations("thesis");
  return (
    <>
      <PageHeader title={t("title")} description={t("subtitle")} kicker="SCR-09" />
      <ThesisList />
    </>
  );
}
