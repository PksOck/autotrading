import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { PortfolioView } from "@/components/portfolio/PortfolioView";

/** SCR-08 Portfelj (BL-028). */
export default async function PortfolioPage() {
  const t = await getTranslations("portfolio");
  return (
    <>
      <PageHeader title={t("title")} helpKey="portfolio" />
      <Suspense>
        <PortfolioView />
      </Suspense>
    </>
  );
}
