"use client";

import { useFormatter, useTranslations } from "next-intl";
import { useState } from "react";
import { SegmentedButtons } from "@/components/common/SegmentedButtons";
import { useTrackRecord } from "@/lib/api/hooks";
import type { TrackRecordOut, TrackStat } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { formatChange, formatNumber, formatShare } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

const HORIZONS = ["1", "5", "20", "60"] as const;
type Horizon = (typeof HORIZONS)[number];

const changeClass = (value: string | null | undefined) =>
  value == null ? "text-text-3" : Number(value) > 0 ? "text-pos" : Number(value) < 0 ? "text-neg" : "text-text-2";

function LowSample({ min }: { min: number }) {
  const t = useTranslations("trackRecord");
  return (
    <span title={t("lowSampleHint", { min })} className="rounded-full bg-warn-soft px-1.5 text-xs leading-5 font-medium whitespace-nowrap text-warn">
      {t("lowSample")}
    </span>
  );
}

function useFormats() {
  const locale = useAppLocale();
  return {
    share: (v: string | null | undefined) => (v == null ? "—" : formatShare(locale, Number(v))),
    change: (v: string | null | undefined) => (v == null ? "—" : formatChange(locale, Number(v))),
    number: (v: string | number, digits = 0) => formatNumber(locale, Number(v), digits),
  };
}

function Summary({ data }: { data: TrackRecordOut }) {
  const t = useTranslations("trackRecord");
  const f = useFormats();
  const { overall } = data;
  const tiles = [
    { label: t("hitRate"), hint: t("hitRateHint"), value: f.share(overall.hit_rate), tone: "text-text" },
    { label: t("avgReturn"), hint: t("avgReturnHint"), value: f.change(overall.avg_return_pct), tone: changeClass(overall.avg_return_pct) },
    {
      label: data.benchmark ? t("avgAlpha", { benchmark: data.benchmark }) : t("avgAlphaPlain"),
      hint: t("avgAlphaHint"),
      value: f.change(overall.avg_alpha_pct),
      tone: changeClass(overall.avg_alpha_pct),
    },
    {
      label: t("measured"),
      hint: t("pending", { count: data.pending }),
      value: t("measuredValue", { measured: data.measured, total: data.signals_total }),
      tone: "text-text",
    },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {tiles.map((tile) => (
        <div key={tile.label} className="card flex flex-col gap-1 p-4">
          <span className="text-xs text-text-3">{tile.label}</span>
          <span className={cn("num text-2xl font-semibold", tile.tone)}>{tile.value}</span>
          <span className="text-xs text-text-3">{tile.hint}</span>
        </div>
      ))}
    </div>
  );
}

function StatLine({ stat, min }: { stat: TrackStat; min: number }) {
  const t = useTranslations("trackRecord");
  const f = useFormats();
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-[13px] sm:grid-cols-4">
      <dt className="text-text-3">{t("count")}</dt>
      <dd className="num flex items-center gap-2">
        {stat.count}
        {stat.low_sample && <LowSample min={min} />}
      </dd>
      <dt className="text-text-3">{t("hitRate")}</dt>
      <dd className="num">{f.share(stat.hit_rate)}</dd>
      <dt className="text-text-3">{t("avgReturn")}</dt>
      <dd className={cn("num", changeClass(stat.avg_return_pct))}>{f.change(stat.avg_return_pct)}</dd>
      <dt className="text-text-3">{t("avgAlphaPlain")}</dt>
      <dd className={cn("num", changeClass(stat.avg_alpha_pct))}>{f.change(stat.avg_alpha_pct)}</dd>
    </dl>
  );
}

function Origins({ data }: { data: TrackRecordOut }) {
  const t = useTranslations("trackRecord");
  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-semibold">{t("originTitle")}</h2>
      <div className="grid gap-3 md:grid-cols-2">
        {data.by_origin.map((o) => (
          <div key={o.origin} data-testid={`origin-${o.origin}`} className="card flex flex-col gap-3 p-4">
            <h3 className="font-medium">{t(`origin.${o.origin}`)}</h3>
            <StatLine stat={o} min={data.min_sample} />
          </div>
        ))}
      </div>
    </section>
  );
}

function Groups({ data }: { data: TrackRecordOut }) {
  const t = useTranslations();
  const f = useFormats();
  if (data.by_group.length === 0) return null;
  const label = (prefix: string, key: string) => (t.has(`${prefix}.${key}`) ? t(`${prefix}.${key}`) : key);
  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-semibold">{t("trackRecord.groupsTitle")}</h2>
      <div className="card overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead className="text-left text-xs text-text-3">
            <tr className="border-b border-border">
              <th className="px-4 py-2 font-medium">{t("trackRecord.kind")}</th>
              <th className="px-4 py-2 font-medium">{t("trackRecord.source")}</th>
              <th className="px-4 py-2 text-right font-medium">{t("trackRecord.count")}</th>
              <th className="px-4 py-2 text-right font-medium">{t("trackRecord.hitRate")}</th>
              <th className="px-4 py-2 text-right font-medium">{t("trackRecord.avgReturn")}</th>
              <th className="px-4 py-2 text-right font-medium">{t("trackRecord.avgAlphaPlain")}</th>
            </tr>
          </thead>
          <tbody>
            {data.by_group.map((g) => (
              <tr key={`${g.kind}-${g.source}`} className="border-b border-border last:border-0">
                <td className="px-4 py-2">{label("signal.kind", g.kind)}</td>
                <td className="px-4 py-2 text-text-2">{label("signalsPage.source", g.source)}</td>
                <td className="num px-4 py-2 text-right">
                  <span className="inline-flex items-center gap-2">
                    {g.low_sample && <LowSample min={data.min_sample} />}
                    {g.count}
                  </span>
                </td>
                <td className="num px-4 py-2 text-right">{f.share(g.hit_rate)}</td>
                <td className={cn("num px-4 py-2 text-right", changeClass(g.avg_return_pct))}>{f.change(g.avg_return_pct)}</td>
                <td className={cn("num px-4 py-2 text-right", changeClass(g.avg_alpha_pct))}>{f.change(g.avg_alpha_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/** Hit rate per strength bucket: a calibrated system hits more often at higher strength. */
function Calibration({ data }: { data: TrackRecordOut }) {
  const t = useTranslations("trackRecord");
  const f = useFormats();
  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 className="font-semibold">{t("calibrationTitle")}</h2>
        <p className="text-[13px] text-text-3">{t("calibrationHint")}</p>
      </div>
      <ul className="card flex flex-col gap-3 p-4">
        {data.calibration.map((b) => {
          const range = t("strengthRange", { low: f.number(b.strength_low, 1), high: f.number(b.strength_high, 1) });
          return (
            <li key={b.strength_low} className="grid grid-cols-[6.5rem_1fr_auto] items-center gap-3 text-[13px]">
              <span className="text-text-2">{range}</span>
              <span
                role="meter"
                aria-label={t("hitRateIn", { range })}
                aria-valuemin={0}
                aria-valuemax={1}
                aria-valuenow={b.hit_rate == null ? undefined : Number(b.hit_rate)}
                className="relative h-2 overflow-hidden rounded-full bg-surface-2"
              >
                {b.hit_rate != null && (
                  <span className="absolute inset-y-0 left-0 rounded-full bg-accent" style={{ width: `${Number(b.hit_rate) * 100}%` }} />
                )}
              </span>
              <span className="num flex items-center justify-end gap-2">
                {b.count > 0 && b.low_sample && <LowSample min={data.min_sample} />}
                <span className="w-12 text-right">{f.share(b.hit_rate)}</span>
                <span className="w-16 text-right text-text-3">{t("countShort", { count: b.count })}</span>
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/** SCR-10 Track record (BL-102): how past signals turned out, by horizon. */
export function TrackRecord() {
  const t = useTranslations("trackRecord");
  const format = useFormatter();
  const [horizon, setHorizon] = useState<Horizon>("20");
  const { data, isLoading, error, refetch } = useTrackRecord(Number(horizon));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <SegmentedButtons
          label={t("horizon")}
          value={horizon}
          onChange={setHorizon}
          options={HORIZONS.map((h) => ({ value: h, label: t("horizonDays", { days: Number(h) }) }))}
          className="w-full max-w-xs"
        />
        {data && (
          <span className="text-xs text-text-3">
            {t("sourceLine")}
            {data.as_of && (
              <>
                {" · "}
                <time dateTime={data.as_of}>{format.relativeTime(new Date(data.as_of), new Date())}</time>
              </>
            )}
          </span>
        )}
      </div>
      {isLoading && <div className="card h-40 animate-pulse" />}
      {error && (
        <div className="card flex flex-col items-start gap-2 p-6">
          <p className="text-warn">{t("error")}</p>
          <button type="button" onClick={() => void refetch()} className="h-9 rounded-md border border-border px-3 font-medium hover:bg-surface-2">
            {t("retry")}
          </button>
        </div>
      )}
      {data && data.measured === 0 && (
        <p className="card p-6 text-text-3">{t("empty", { days: data.horizon_days, pending: data.pending })}</p>
      )}
      {data && data.measured > 0 && (
        <>
          {data.overall.low_sample && (
            <p className="rounded-md bg-warn-soft px-4 py-3 text-[13px] text-warn">{t("lowSampleBanner", { min: data.min_sample })}</p>
          )}
          <Summary data={data} />
          <Origins data={data} />
          <Groups data={data} />
          <Calibration data={data} />
        </>
      )}
    </div>
  );
}
