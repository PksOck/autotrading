/**
 * Number formatting helpers on top of Intl (VOICE.md §3). Always pass the active locale.
 * Grouping is forced ("always"): ICU builds disagree on Slovenian 4-digit grouping
 * (Node prints 6120, Chromium 6.120), which would break hydration.
 */
export type AppLocale = "sl" | "en";

const intlLocale = (locale: AppLocale) => (locale === "sl" ? "sl-SI" : "en-US");

export function formatNumber(locale: AppLocale, value: number, digits = 0): string {
  return new Intl.NumberFormat(intlLocale(locale), {
    useGrouping: "always",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatMoney(locale: AppLocale, value: number, currency = "USD", digits = 2) {
  return new Intl.NumberFormat(intlLocale(locale), {
    style: "currency",
    currency,
    useGrouping: "always",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

/** Share 0..1 as an unsigned percentage, e.g. "62 %" (VOICE.md §3). */
export function formatShare(locale: AppLocale, ratio: number, digits = 0): string {
  return new Intl.NumberFormat(intlLocale(locale), {
    style: "percent",
    useGrouping: "always",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(ratio);
}

/** Signed percentage with arrow, e.g. "▲ +2,1 %" / "▼ −3,4 %" (CMP-09). */
export function formatChange(locale: AppLocale, percent: number, digits = 1): string {
  const arrow = percent >= 0 ? "▲" : "▼";
  const formatted = new Intl.NumberFormat(intlLocale(locale), {
    style: "percent",
    signDisplay: "always",
    useGrouping: "always",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
    .format(percent / 100)
    .replace("-", "−");
  return `${arrow} ${formatted}`;
}
