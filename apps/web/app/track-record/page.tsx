import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/common/PageHeader";
import { TrackRecord } from "@/components/track-record/TrackRecord";

/** SCR-10 Uspešnost (BL-102). */
export default async function TrackRecordPage() {
  const t = await getTranslations("trackRecord");
  return (
    <>
      <PageHeader title={t("title")} kicker="SCR-10" description={t("subtitle")} />
      <TrackRecord />
    </>
  );
}
