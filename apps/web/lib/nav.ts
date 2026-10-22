/** Navigation and screen inventory (DESIGN.md §4). `milestone` marks screens not built yet. */
export type NavItem = {
  href: string;
  key: string;
  screen: string;
  milestone?: string;
  main?: boolean;
  shortcut?: string;
};

export const NAV: NavItem[] = [
  { href: "/", key: "overview", screen: "SCR-01", main: true, shortcut: "o" },
  { href: "/radar", key: "radar", screen: "SCR-02", main: true, shortcut: "r" },
  { href: "/entries", key: "entries", screen: "SCR-03", milestone: "M3", main: true, shortcut: "e" },
  { href: "/signals", key: "signals", screen: "SCR-04", main: true, shortcut: "s" },
  { href: "/proposals", key: "proposals", screen: "SCR-12" },
  { href: "/analysis", key: "analyses", screen: "SCR-06" },
  { href: "/portfolio", key: "portfolio", screen: "SCR-08", main: true, shortcut: "p" },
  { href: "/theses", key: "theses", screen: "SCR-09", milestone: "M5" },
  { href: "/options", key: "options", screen: "SCR-07", milestone: "M6" },
  { href: "/track-record", key: "trackRecord", screen: "SCR-10", milestone: "M5" },
  { href: "/settings", key: "settings", screen: "SCR-11", milestone: "M1" },
];

export function navItem(key: string): NavItem {
  const item = NAV.find((n) => n.key === key);
  if (!item) throw new Error(`unknown nav item ${key}`);
  return item;
}

export const isActive = (href: string, pathname: string) =>
  href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
