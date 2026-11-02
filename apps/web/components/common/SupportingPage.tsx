import Link from "next/link";
import { getTranslations } from "next-intl/server";

export async function SupportingPage({
  topic,
}: {
  topic: "about" | "privacy" | "terms" | "security";
}) {
  const t = await getTranslations("supporting");
  return (
    <article className="space-y-5">
      <h1 className="text-2xl font-semibold">{t(`${topic}.title`)}</h1>
      <p className="leading-relaxed text-text-2">{t(`${topic}.intro`)}</p>
      <p className="leading-relaxed text-text-2">{t(`${topic}.detail`)}</p>
      <Link href="/login" className="inline-flex min-h-12 items-center">
        {t("back")}
      </Link>
    </article>
  );
}
