import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/common/PageHeader";
import { ProposalList } from "@/components/proposals/ProposalList";

/** SCR-12 (DESIGN.md §11). Local list until the proposals API exists (BL-053, BL-054). */
export default async function ProposalsPage() {
  const t = await getTranslations();
  return (
    <>
      <PageHeader title={t("nav.proposals")} kicker="SCR-12" description={t("proposal.previewNote")} />
      <ProposalList />
    </>
  );
}
