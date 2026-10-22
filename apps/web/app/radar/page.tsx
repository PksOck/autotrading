import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { RadarView } from "@/components/radar/RadarView";

/** SCR-02 Radar (BL-049). */
export default async function RadarPage() {
  const t = await getTranslations("radar");
  return (
    <>
      <PageHeader title={t("title")} kicker="SCR-02" description={t("subtitle")} />
      <Suspense>
        <RadarView />
      </Suspense>
    </>
  );
}
