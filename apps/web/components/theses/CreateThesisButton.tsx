"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCreateThesisDraft } from "@/lib/api/hooks";
import { thesisErrorKey } from "@/lib/thesis";
import { thesisButton } from "./styles";

export function CreateThesisButton({ runId }: { runId: string }) {
  const t = useTranslations("thesis");
  const router = useRouter();
  const create = useCreateThesisDraft();
  return (
    <div className="card flex flex-col items-start gap-2 p-4">
      <p className="text-[13px] text-text-2">{t("createHint")}</p>
      <button
        className={thesisButton}
        disabled={create.isPending}
        onClick={() =>
          create.mutate(
            { analysis_run_id: runId },
            {
              onSuccess: (revision) =>
                router.push(`/theses/${encodeURIComponent(revision.thesis_id)}`),
            },
          )
        }
      >
        {t(create.isPending ? "creating" : "createDraft")}
      </button>
      {create.error && (
        <p role="alert" className="text-warn">
          {t(thesisErrorKey(create.error))}
        </p>
      )}
    </div>
  );
}
