"use client";

import Link from "next/link";
import { HoverCard } from "radix-ui";
import type { ReactNode } from "react";
import { InstrumentPreview } from "@/components/common/InstrumentPreview";
import { cn } from "@/lib/cn";
import { encodeEntity, type EntityRef } from "@/lib/entities";
import { usePeek } from "@/lib/use-peek";
import { useFocusStore } from "@/stores/focus";

type Props = { entity: EntityRef; children?: ReactNode; className?: string };

/**
 * CMP-19: every entity is clickable (LX-01). Hover shows a preview (CMP-20) and
 * cross-highlights the entity elsewhere (LX-03); click opens the peek panel (LX-02).
 */
export function EntityLink({ entity, children, className }: Props) {
  const { hrefFor } = usePeek();
  const key = encodeEntity(entity);
  const setHovered = useFocusStore((s) => s.setHovered);
  const highlighted = useFocusStore((s) => s.hovered === key);

  const link = (
    <Link
      href={hrefFor(entity)}
      scroll={false}
      onMouseEnter={() => setHovered(key)}
      onMouseLeave={() => setHovered(null)}
      onFocus={() => setHovered(key)}
      onBlur={() => setHovered(null)}
      className={cn(
        "rounded-sm text-text underline decoration-border decoration-1 underline-offset-4 transition-colors duration-[var(--dur-fast)] hover:decoration-accent",
        highlighted && "bg-accent-soft decoration-accent",
        entity.kind === "instrument" && "num font-medium",
        className,
      )}
    >
      {children ?? entity.id}
    </Link>
  );

  if (entity.kind !== "instrument") return link;

  return (
    <HoverCard.Root openDelay={300} closeDelay={80}>
      <HoverCard.Trigger asChild>{link}</HoverCard.Trigger>
      <HoverCard.Portal>
        <HoverCard.Content
          sideOffset={8}
          collisionPadding={12}
          className="card z-50 w-72 p-4 shadow-float data-[state=open]:animate-[fadeIn_var(--dur-base)_var(--ease-standard)]"
        >
          <InstrumentPreview symbol={entity.id} />
        </HoverCard.Content>
      </HoverCard.Portal>
    </HoverCard.Root>
  );
}
