"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ApiError } from "@/lib/api/client";
import { useCreateAnalysis } from "@/lib/api/hooks";

/** "Globoka analiza": starts a deep run (stock or ETF engine) and opens SCR-06. */
export function LaunchAnalysisButton({ symbol }: { symbol: string }) {
  const t = useTranslations("analysisPage.launch");
  const router = useRouter();
  const create = useCreateAnalysis();
  const cls =
    "h-10 rounded-md border border-border px-4 font-medium hover:bg-surface-2 disabled:cursor-not-allowed disabled:text-text-3 disabled:hover:bg-transparent";

  return (
    <button
      type="button"
      disabled={create.isPending}
      className={cls}
      onClick={() =>
        create.mutate(
          { symbol },
          {
            onSuccess: (run) => router.push(`/analysis/${run.id}`),
            onError: (error) => {
              const detail = error instanceof ApiError ? error.detail : "";
              toast.error(
                detail === "instrument_not_found" ? t("notFound") : t("failed"),
              );
            },
          },
        )
      }
    >
      {create.isPending ? t("starting") : t("button")}
    </button>
  );
}
