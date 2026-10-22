import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { EntriesView } from "@/components/entries/EntriesView";

/** SCR-03 Vstopi (BL-064). */
export default async function EntriesPage() {
  const t = await getTranslations("entriesPage");
  return (
    <>
      <PageHeader title={t("title")} kicker="SCR-03" description={t("subtitle")} />
      <Suspense>
        <EntriesView />
      </Suspense>
    </>
  );
}
