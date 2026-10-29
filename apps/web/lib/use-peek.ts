"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { decodeEntity, encodeEntity, type EntityRef } from "./entities";

/** LX-02/LX-08: the peek panel lives in the URL (`?peek=instrument:MSFT`). */
export function usePeek() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const hrefFor = useCallback(
    (ref: EntityRef | null) => {
      const next = new URLSearchParams(params.toString());
      if (ref) next.set("peek", encodeEntity(ref));
      else next.delete("peek");
      const query = next.toString();
      return query ? `${pathname}?${query}` : pathname;
    },
    [params, pathname],
  );

  const open = useCallback(
    (ref: EntityRef) => router.push(hrefFor(ref), { scroll: false }),
    [hrefFor, router],
  );
  const close = useCallback(() => router.replace(hrefFor(null), { scroll: false }), [hrefFor, router]);

  return { current: decodeEntity(params.get("peek")), hrefFor, open, close };
}
