import Link from "next/link";
import { getTranslations } from "next-intl/server";

export default async function NotFound() {
  const t = await getTranslations();
  return (
    <section className="card mx-auto mt-10 max-w-xl p-8">
      <h1 className="text-xl font-semibold">404</h1>
      <p className="mt-2 text-text-2">{t("peek.notFound")}</p>
      <Link href="/" className="mt-4 inline-block text-accent">
        ← {t("planned.back")}
      </Link>
    </section>
  );
}
