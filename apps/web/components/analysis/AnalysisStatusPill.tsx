import { useTranslations } from "next-intl";
import type { AnalysisStatus } from "@/lib/api/types";
import { cn } from "@/lib/cn";

const STYLE: Record<AnalysisStatus, string> = {
  queued: "bg-surface-2 text-text-2",
  running: "bg-accent-soft text-accent",
  done: "bg-pos-soft text-pos",
  failed: "bg-neg-soft text-neg",
};

export function AnalysisStatusPill({
  status,
  className,
}: {
  status: AnalysisStatus;
  className?: string;
}) {
  const t = useTranslations("analysisPage.status");
  return (
    <span
      data-testid="analysis-status"
      data-status={status}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 text-xs leading-5 font-medium",
        STYLE[status],
        className,
      )}
    >
      {status === "running" && (
        <span className="size-1.5 rounded-full bg-accent motion-safe:animate-pulse" />
      )}
      {t(status)}
    </span>
  );
}
