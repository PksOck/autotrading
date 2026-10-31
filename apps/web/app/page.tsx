import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { LiveOverview } from "@/components/overview/LiveOverview";

export default async function OverviewPage() {
  const t = await getTranslations("overview");
  return (
    <>
      <PageHeader title={t("title")} helpKey="overview" />
      <Suspense>
        <LiveOverview />
      </Suspense>
    </>
  );
}
