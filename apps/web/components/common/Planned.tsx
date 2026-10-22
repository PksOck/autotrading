import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { navItem } from "@/lib/nav";

/** CMP-17 empty state for screens that arrive in a later milestone. */
export async function Planned({ navKey }: { navKey: string }) {
  const t = await getTranslations();
  const item = navItem(navKey);
  const screen = `${item.screen} ${t(`nav.${item.key}`)}`;
  return (
    <section className="card mx-auto mt-10 flex max-w-xl flex-col items-start gap-3 p-8">
      <span className="num rounded-full bg-accent-soft px-2 text-xs leading-5 font-medium text-accent">
        {item.milestone}
      </span>
      <h1 className="text-xl leading-7 font-semibold">{t("planned.title")}</h1>
      <p className="text-text-2">{t("planned.body", { screen, milestone: item.milestone ?? "" })}</p>
      <Link href="/" className="text-accent">
        ← {t("planned.back")}
      </Link>
    </section>
  );
}
