"use client";

import { useTranslations } from "next-intl";
import { Tooltip } from "radix-ui";
import Link from "next/link";
import { useSystemStatus } from "@/lib/api/hooks";
import type { ServiceState } from "@/lib/api/types";

const SHOWN = ["ib_gateway", "ibkr_flex", "ollama", "litellm"] as const;

const DOT: Record<ServiceState, string> = {
  up: "bg-pos",
  degraded: "bg-warn",
  down: "bg-neg",
  unconfigured: "bg-text-3",
};

/** CMP-02: health of the services the user cares about, refreshed every 30 s. */
export function SystemStatus() {
  const t = useTranslations("system");
  const { data, isError } = useSystemStatus();

  if (isError) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-warn" role="status">
        <span className="h-2 w-2 rounded-full bg-warn" />
        {t("unreachable")}
      </span>
    );
  }

  return (
    <>
      <Link
        href="/settings"
        className="inline-flex min-h-10 items-center gap-1 text-xs text-text-3 lg:hidden"
        aria-label={t("statusLabel")}
      >
        <span
          className={`size-2 rounded-full ${data?.services.some((s) => s.state === "down" || s.state === "degraded") ? "bg-warn" : "bg-text-3"}`}
        />
        {t("statusLabel")}{" "}
        {data
          ? `${data.services.filter((s) => s.state === "up").length}/${data.services.length}`
          : "…"}
      </Link>
      <ul
        aria-label={t("statusLabel")}
        className="hidden items-center gap-3.5 text-xs text-text-2 lg:flex"
      >
        {SHOWN.map((id) => {
          const service = data?.services.find((s) => s.id === id);
          const state = service?.state;
          return (
            <li key={id}>
              <Tooltip.Root>
                <Tooltip.Trigger asChild>
                  <span tabIndex={0} className="inline-flex items-center gap-1.5 rounded-sm">
                    <span
                      className={`h-2 w-2 rounded-full ${state ? DOT[state] : "animate-pulse bg-border"}`}
                    />
                    {t(id)}
                  </span>
                </Tooltip.Trigger>
                <Tooltip.Portal>
                  <Tooltip.Content
                    sideOffset={6}
                    className="card z-50 px-3 py-2 text-xs shadow-float"
                  >
                    {state ? t(`state.${state}`) : "…"}
                    {service?.latency_ms != null && (
                      <span className="num text-text-3"> · {service.latency_ms} ms</span>
                    )}
                    {service?.detail && <span className="text-text-3"> · {service.detail}</span>}
                  </Tooltip.Content>
                </Tooltip.Portal>
              </Tooltip.Root>
            </li>
          );
        })}
      </ul>
    </>
  );
}
