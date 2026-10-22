import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";
import sl from "@/messages/sl.json";
import { DEFAULT_LOCALE, LOCALE_COOKIE, isLocale } from "./config";

type Messages = { [key: string]: string | Messages };

// sl.json is the source of truth; a key missing in en.json falls back to Slovenian.
function withFallback(base: Messages, override: Messages): Messages {
  const out: Messages = { ...base };
  for (const [key, value] of Object.entries(override)) {
    const current = out[key];
    out[key] =
      typeof value === "object" && typeof current === "object" ? withFallback(current, value) : value;
  }
  return out;
}

export default getRequestConfig(async () => {
  const raw = (await cookies()).get(LOCALE_COOKIE)?.value;
  const locale = isLocale(raw) ? raw : DEFAULT_LOCALE;
  const messages =
    locale === DEFAULT_LOCALE
      ? sl
      : withFallback(sl, (await import(`@/messages/${locale}.json`)).default as Messages);
  return { locale, messages, timeZone: "Europe/Ljubljana" };
});
