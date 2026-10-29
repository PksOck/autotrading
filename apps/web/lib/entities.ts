/** Entity references used by EntityLink, PeekPanel and deep links (DESIGN.md §9, LX-01/02/08). */
export const ENTITY_KINDS = [
  "instrument",
  "event",
  "signal",
  "analysis",
  "thesis",
  "proposal",
] as const;
export type EntityKind = (typeof ENTITY_KINDS)[number];

export type EntityRef = { kind: EntityKind; id: string };

export function isSignalId(id: string | null): id is string {
  return id !== null && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
}

export function encodeEntity(ref: EntityRef): string {
  return `${ref.kind}:${ref.id}`;
}

export function decodeEntity(value: string | null | undefined): EntityRef | null {
  if (!value) return null;
  const [kind, ...rest] = value.split(":");
  const id = rest.join(":");
  if (!id || !ENTITY_KINDS.includes(kind as EntityKind)) return null;
  return { kind: kind as EntityKind, id };
}
