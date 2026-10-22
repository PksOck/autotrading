import { getFormatter, getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/common/PageHeader";
import { Funnel } from "@/components/overview/Funnel";
import { PortfolioValue } from "@/components/overview/PortfolioValue";
import { PulseTimeline } from "@/components/overview/PulseTimeline";
import { RegimeStrip } from "@/components/overview/RegimeStrip";
import { SignalCards } from "@/components/overview/SignalCards";
import { Treemap } from "@/components/overview/Treemap";
import { FUNNEL, INSTRUMENTS, PULSE_EVENTS, REGIME, SIGNALS } from "@/lib/sample-data";

/** SCR-01 Pregled on sample data until M1/M2 deliver real data. */
export default async function OverviewPage() {
  const t = await getTranslations("overview");
  const format = await getFormatter();
  const today = format.dateTime(new Date(), { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  return (
    <>
      <PageHeader title={t("title")} kicker={today} sample />
      <section aria-label={t("regime")} className="mb-6">
        <RegimeStrip indicators={REGIME} />
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="flex min-w-0 flex-col gap-6">
          <section className="card p-5">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-base font-semibold">{t("treemap")}</h2>
              <p className="text-xs text-text-3">{t("treemapHint")}</p>
            </div>
            <Treemap items={INSTRUMENTS} />
          </section>
          <section className="card p-5">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-base font-semibold">{t("pulse")}</h2>
              <p className="text-xs text-text-3">{t("pulseHint")}</p>
            </div>
            <PulseTimeline events={PULSE_EVENTS} />
          </section>
        </div>

        <aside className="flex min-w-0 flex-col gap-6">
          <PortfolioValue value={248310} change={0.8} />
          <section>
            <h2 className="mb-3 text-xl leading-7 font-semibold">{t("newToday")}</h2>
            <SignalCards signals={SIGNALS} />
          </section>
          <section className="card p-5">
            <h2 className="mb-4 text-base font-semibold">{t("funnel")}</h2>
            <Funnel stages={FUNNEL} />
          </section>
        </aside>
      </div>
    </>
  );
}
