import { getFormatter, getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { LiveOverview } from "@/components/overview/LiveOverview";

export default async function OverviewPage() {
  const t = await getTranslations("overview");
  const format = await getFormatter();
  return (
    <>
      <PageHeader
        title={t("title")}
        kicker={format.dateTime(new Date(), {
          weekday: "long",
          day: "numeric",
          month: "long",
          year: "numeric",
        })}
      />
      <Suspense>
        <LiveOverview />
      </Suspense>
    </>
  );
}
