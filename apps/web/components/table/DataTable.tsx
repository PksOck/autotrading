"use client";

import { useCallback, useMemo, useSyncExternalStore, type ReactNode } from "react";
import { useTranslations } from "next-intl";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { normalizePreferences, type TableViewPreferences } from "@/lib/view-state";
import { cn } from "@/lib/cn";

export type ColumnDefinition<T> = {
  id: string;
  label: string;
  required?: boolean;
  defaultVisible?: boolean;
  numeric?: boolean;
  width?: number;
  sortable?: boolean;
  render: (row: T) => ReactNode;
};

/** Values arrive in server sort order; the table owns only local presentation preferences. */
export function DataTable<T>({
  module,
  columns,
  rows,
  rowKey,
  label,
  profiles = [],
}: {
  module: string;
  columns: ColumnDefinition<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  label: string;
  profiles?: { label: string; columns: string[] }[];
}) {
  const t = useTranslations("table");
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const key = `preza.view.${module}.v1`;
  const subscribe = useCallback((listener: () => void) => {
    window.addEventListener("storage", listener);
    window.addEventListener("preza-view", listener);
    return () => {
      window.removeEventListener("storage", listener);
      window.removeEventListener("preza-view", listener);
    };
  }, []);
  const snapshot = useCallback(() => {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  }, [key]);
  const raw = useSyncExternalStore(subscribe, snapshot, () => null);
  const preferences = useMemo(() => normalizePreferences(raw, columns), [raw, columns]);
  const save = (next: TableViewPreferences) => {
    try {
      localStorage.setItem(key, JSON.stringify(next));
      window.dispatchEvent(new Event("preza-view"));
    } catch {
      /* Storage may be disabled; data remains available. */
    }
  };
  const change = (values: Record<string, string | null>) => {
    const next = new URLSearchParams(params.toString());
    for (const [key, value] of Object.entries(values)) {
      if (value === null) next.delete(key);
      else next.set(key, value);
    }
    router.replace(`${pathname}?${next}`, { scroll: false });
  };
  const ordered = preferences.column_order
    .map((id) => columns.find((c) => c.id === id)!)
    .filter((c) => c && preferences.columns.includes(c.id));
  const page = Math.max(1, Number(params.get("page")) || 1);
  const pageSize = 25;
  const pages = Math.max(1, Math.ceil(rows.length / pageSize));
  const safePage = Math.min(page, pages);
  return (
    <section className="card min-w-0" aria-label={label}>
      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        <span className="mr-auto text-sm text-text-3">{t("results", { count: rows.length })}</span>
        {profiles.map((profile) => (
          <button
            key={profile.label}
            type="button"
            className="h-12 rounded-md border border-border px-2 text-xs"
            onClick={() =>
              save({
                ...preferences,
                columns: [
                  ...new Set([
                    ...profile.columns,
                    ...columns.filter((c) => c.required).map((c) => c.id),
                  ]),
                ],
              })
            }
          >
            {profile.label}
          </button>
        ))}
        <button
          type="button"
          className="h-12 rounded-md border border-border px-3 text-xs"
          onClick={() => {
            const defaults = normalizePreferences(null, columns);
            save({
              ...preferences,
              columns: defaults.columns,
              column_order: defaults.column_order,
            });
          }}
        >
          {t("standard")}
        </button>
        <label className="text-xs text-text-3">
          {t("density")}{" "}
          <select
            aria-label={t("density")}
            value={preferences.density}
            onChange={(event) =>
              save({
                ...preferences,
                density: event.target.value as TableViewPreferences["density"],
              })
            }
            className="h-12 rounded-md border border-border bg-surface px-2"
          >
            <option value="comfortable">{t("comfortable")}</option>
            <option value="compact">{t("compact")}</option>
          </select>
        </label>
        <details className="relative">
          <summary className="flex min-h-12 cursor-pointer items-center rounded-md border border-border px-3 text-sm">
            {t("columns")}
          </summary>
          <div className="absolute right-0 z-30 mt-2 max-h-[65vh] w-80 overflow-auto rounded-md border border-border bg-surface p-3 shadow-float">
            <p className="mb-2 text-xs text-text-3">{t("local")}</p>
            {preferences.column_order.map((id, index) => {
              const column = columns.find((c) => c.id === id)!;
              if (!column) return null;
              return (
                <div
                  key={id}
                  className="flex flex-wrap items-center gap-1 border-b border-border py-2 text-sm"
                >
                  <label className="flex min-h-12 min-w-0 flex-1 items-center gap-2">
                    <input
                      type="checkbox"
                      checked={preferences.columns.includes(id)}
                      disabled={column.required}
                      onChange={(event) =>
                        save({
                          ...preferences,
                          columns: event.target.checked
                            ? [...preferences.columns, id]
                            : preferences.columns.filter((c) => c !== id),
                        })
                      }
                    />
                    {column.label}
                  </label>
                  <button
                    type="button"
                    aria-label={t("moveUp", { column: column.label })}
                    disabled={index === 0}
                    onClick={() => {
                      const order = [...preferences.column_order];
                      [order[index - 1], order[index]] = [order[index]!, order[index - 1]!];
                      save({ ...preferences, column_order: order });
                    }}
                    className="h-12 w-12 disabled:opacity-30"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    aria-label={t("moveDown", { column: column.label })}
                    disabled={index === preferences.column_order.length - 1}
                    onClick={() => {
                      const order = [...preferences.column_order];
                      [order[index], order[index + 1]] = [order[index + 1]!, order[index]!];
                      save({ ...preferences, column_order: order });
                    }}
                    className="h-12 w-12 disabled:opacity-30"
                  >
                    ↓
                  </button>
                  <label className="flex min-h-12 items-center gap-1 text-xs">
                    <input
                      type="checkbox"
                      checked={preferences.pinned_columns.includes(id)}
                      onChange={(event) =>
                        save({
                          ...preferences,
                          pinned_columns: event.target.checked
                            ? [...preferences.pinned_columns, id]
                            : preferences.pinned_columns.filter((c) => c !== id),
                        })
                      }
                    />
                    {t("pin")}
                  </label>
                  <input
                    type="number"
                    aria-label={t("width", { column: column.label })}
                    min={64}
                    max={640}
                    step={16}
                    value={preferences.column_widths[id] ?? column.width ?? 140}
                    onChange={(event) =>
                      save({
                        ...preferences,
                        column_widths: {
                          ...preferences.column_widths,
                          [id]: Number(event.target.value),
                        },
                      })
                    }
                    className="h-12 w-16 rounded border border-border bg-surface px-1 text-xs"
                  />
                </div>
              );
            })}
            <button
              type="button"
              onClick={() => save(normalizePreferences(null, columns))}
              className="mt-3 h-12 rounded-md border border-border px-3"
            >
              {t("reset")}
            </button>
          </div>
        </details>
      </div>
      <div className="max-w-full overflow-x-auto" tabIndex={0} aria-label={label}>
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-surface-2">
              {ordered.map((column) => (
                <th
                  key={column.id}
                  scope="col"
                  aria-sort={
                    params.get("sort") === column.id
                      ? params.get("direction") === "desc"
                        ? "descending"
                        : "ascending"
                      : "none"
                  }
                  className={cn(
                    "whitespace-nowrap px-3 py-2 text-left text-xs text-text-3",
                    column.numeric && "text-right",
                  )}
                  style={{ minWidth: preferences.column_widths[column.id] ?? column.width ?? 140 }}
                >
                  {column.sortable ? (
                    <button
                      type="button"
                      className="min-h-12"
                      onClick={() =>
                        change({
                          sort: column.id,
                          direction:
                            params.get("sort") === column.id && params.get("direction") !== "desc"
                              ? "desc"
                              : "asc",
                          page: null,
                        })
                      }
                    >
                      {column.label}{" "}
                      {params.get("sort") === column.id
                        ? params.get("direction") === "desc"
                          ? "↓"
                          : "↑"
                        : "↕"}
                    </button>
                  ) : (
                    column.label
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice((safePage - 1) * pageSize, safePage * pageSize).map((row) => (
              <tr key={rowKey(row)} className="border-t border-border hover:bg-surface-2">
                {ordered.map((column, index) => (
                  <td
                    key={column.id}
                    className={cn(
                      "px-3 align-top",
                      preferences.density === "compact" ? "py-2" : "py-4",
                      column.numeric && "num text-right",
                      preferences.pinned_columns.includes(column.id) && "sticky z-10 bg-surface",
                    )}
                    style={
                      preferences.pinned_columns.includes(column.id)
                        ? {
                            left: ordered
                              .slice(0, index)
                              .filter((c) => preferences.pinned_columns.includes(c.id))
                              .reduce(
                                (sum, c) =>
                                  sum + (preferences.column_widths[c.id] ?? c.width ?? 140),
                                0,
                              ),
                          }
                        : undefined
                    }
                  >
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={ordered.length} className="p-6 text-text-3">
                  {t("empty")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="flex items-center justify-end gap-3 border-t border-border p-3 text-sm">
          <button
            type="button"
            className="min-h-12 px-2"
            disabled={safePage <= 1}
            onClick={() => change({ page: String(safePage - 1) })}
          >
            {t("previous")}
          </button>
          <span>{t("page", { page: safePage, pages })}</span>
          <button
            type="button"
            className="min-h-12 px-2"
            disabled={safePage >= pages}
            onClick={() => change({ page: String(safePage + 1) })}
          >
            {t("next")}
          </button>
        </div>
      )}
    </section>
  );
}
