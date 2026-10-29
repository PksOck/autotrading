export type PreferenceColumn = { id: string; required?: boolean; defaultVisible?: boolean };
export type TableViewPreferences = {
  version: 1;
  columns: string[];
  column_order: string[];
  column_widths: Record<string, number>;
  pinned_columns: string[];
  density: "comfortable" | "compact";
};

export function normalizePreferences(
  raw: string | null,
  definitions: PreferenceColumn[],
): TableViewPreferences {
  const ids = definitions.map((column) => column.id);
  const defaults = definitions
    .filter((column) => column.required || column.defaultVisible !== false)
    .map((column) => column.id);
  let value: Record<string, unknown> = {};
  try {
    const parsed = raw ? JSON.parse(raw) : null;
    if (parsed?.version === 1) value = parsed;
  } catch {
    /* Recover local preferences without affecting data. */
  }
  const list = (key: string, fallback: string[]) =>
    Array.isArray(value[key])
      ? [
          ...new Set(
            (value[key] as unknown[]).filter(
              (id): id is string => typeof id === "string" && ids.includes(id),
            ),
          ),
        ]
      : fallback;
  const columns = list("columns", defaults);
  for (const column of definitions)
    if (column.required && !columns.includes(column.id)) columns.push(column.id);
  const order = list("column_order", ids);
  for (const id of ids) if (!order.includes(id)) order.push(id);
  const widths: Record<string, number> = {};
  if (value.column_widths && typeof value.column_widths === "object")
    for (const [id, width] of Object.entries(value.column_widths)) {
      if (ids.includes(id) && typeof width === "number" && Number.isFinite(width))
        widths[id] = Math.max(64, Math.min(640, width));
    }
  return {
    version: 1,
    columns,
    column_order: order,
    column_widths: widths,
    pinned_columns: list(
      "pinned_columns",
      definitions
        .filter((c) => c.required)
        .slice(0, 1)
        .map((c) => c.id),
    ),
    density: value.density === "compact" ? "compact" : "comfortable",
  };
}
