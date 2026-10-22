import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { SignalsInbox } from "@/components/signals/SignalsInbox";

/** SCR-04 Signali (BL-050). */
export default async function SignalsPage() {
  const t = await getTranslations("signalsPage");
  return (
    <>
      <PageHeader title={t("title")} kicker="SCR-04" description={t("subtitle")} />
      <Suspense>
        <SignalsInbox />
      </Suspense>
    </>
  );
}
