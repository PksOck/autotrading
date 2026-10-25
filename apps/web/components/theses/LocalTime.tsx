"use client";

import { useSyncExternalStore } from "react";
import { useFormatter, useTranslations } from "next-intl";

const subscribe = () => () => {};
const browserZone = () => Intl.DateTimeFormat().resolvedOptions().timeZone;
const serverZone = () => undefined;

/** Override the app's server timezone with the viewer's timezone after hydration. */
export function LocalTime({ value }: { value: string }) {
  const zone = useSyncExternalStore(subscribe, browserZone, serverZone);
  const format = useFormatter();
  const t = useTranslations("thesis");
  return (
    <time dateTime={value}>
      {zone
        ? format.dateTime(new Date(value), {
            dateStyle: "medium",
            timeStyle: "short",
            timeZone: zone,
          })
        : t("loading")}
    </time>
  );
}
