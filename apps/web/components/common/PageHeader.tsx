import { getTranslations } from "next-intl/server";
import type { ReactNode } from "react";

export async function PageHeader({
  title,
  kicker,
  description,
  sample,
  actions,
}: {
  title: string;
  kicker?: string;
  description?: string;
  sample?: boolean;
  actions?: ReactNode;
}) {
  const t = await getTranslations("header");
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        {kicker && <div className="label">{kicker}</div>}
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-[28px] leading-[34px] font-semibold">{title}</h1>
          {sample && (
            <span className="rounded-full bg-warn-soft px-2 text-xs leading-5 font-medium text-warn">{t("sample")}</span>
          )}
        </div>
        {description && <p className="mt-1.5 max-w-3xl text-text-2">{description}</p>}
      </div>
      {actions}
    </div>
  );
}
