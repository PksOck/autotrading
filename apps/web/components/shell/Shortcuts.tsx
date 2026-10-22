"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { NAV } from "@/lib/nav";
import { openProposalComposer } from "@/stores/proposals";

const isTyping = (target: EventTarget | null) =>
  target instanceof HTMLElement &&
  (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

/** LX-07: `g <key>` navigation and `+` for a new proposal. */
export function Shortcuts() {
  const router = useRouter();

  useEffect(() => {
    let pendingG = 0;
    const onKey = (event: KeyboardEvent) => {
      if (event.metaKey || event.ctrlKey || event.altKey || isTyping(event.target)) return;
      if (event.key === "+") {
        event.preventDefault();
        openProposalComposer();
        return;
      }
      if (event.key === "g") {
        pendingG = Date.now();
        return;
      }
      if (Date.now() - pendingG < 800) {
        const target = NAV.find((n) => n.shortcut === event.key);
        if (target) router.push(target.href);
        pendingG = 0;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router]);

  return null;
}
