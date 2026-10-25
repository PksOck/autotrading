/** Small stroke icon set (no emoji, no icon font). Decorative unless `label` is given. */
const PATHS: Record<string, string> = {
  check: "M5 12l4 4L19 6",
  overview: "M3 3h7v7H3zM14 3h7v4h-7zM14 11h7v10h-7zM3 14h7v7H3z",
  radar: "M12 3a9 9 0 1 0 9 9M12 7.5a4.5 4.5 0 1 0 4.5 4.5M12 12l6-6",
  entries: "M4 18l5-6 4 3 7-9M15 6h5v5",
  signals: "M4 12h4l2-6 4 12 2-6h4",
  proposals: "M12 5v14M5 12h14",
  portfolio: "M4 7h16v12H4zM9 7V5h6v2",
  analyses: "M4 5h16v10H9l-5 4zM8 9h8M8 12h5",
  theses: "M5 4h14v16H5zM8 9h8M8 13h8M8 17h5",
  options: "M4 19c4 0 6-14 16-14M4 12h16",
  trackRecord: "M5 19V9M12 19V5M19 19v-7",
  settings:
    "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM4 12h2M18 12h2M12 4v2M12 18v2M6.3 6.3l1.4 1.4M16.3 16.3l1.4 1.4M6.3 17.7l1.4-1.4M16.3 7.7l1.4-1.4",
  search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM16 16l4 4",
  sun: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.4 1.4M17.6 17.6 19 19M5 19l1.4-1.4M17.6 6.4 19 5",
  moon: "M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z",
  system: "M3 5h18v11H3zM8 20h8M12 16v4",
  more: "M5 12h.01M12 12h.01M19 12h.01",
  ux: "M4 4h7v7H4zM13 13h7v7h-7zM16.5 4a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7zM4 20l3.5-6 3.5 6z",
};

export function Icon({ name, size = 18, label }: { name: string; size?: number; label?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={label ? undefined : true}
      role={label ? "img" : undefined}
      aria-label={label}
    >
      <path d={PATHS[name] ?? ""} />
    </svg>
  );
}
