export const THEME_PREFERENCES = ["system", "light", "dark"] as const;
export type ThemePreference = (typeof THEME_PREFERENCES)[number];
export const THEME_COOKIE = "theme";

export function isThemePreference(value: string | undefined): value is ThemePreference {
  return THEME_PREFERENCES.includes(value as ThemePreference);
}

/** `data-theme` is only set for an explicit choice; "system" lets the CSS media query decide. */
export function applyTheme(preference: ThemePreference) {
  const root = document.documentElement;
  if (preference === "system") delete root.dataset.theme;
  else root.dataset.theme = preference;
}

export const THEME_EVENT = "preza:theme";

export function nextThemePreference(current: ThemePreference): ThemePreference {
  return current === "system" ? "light" : current === "light" ? "dark" : "system";
}

/** Applies and persists a preference, and tells every toggle on the page. */
export function setThemePreference(preference: ThemePreference) {
  applyTheme(preference);
  document.cookie = `${THEME_COOKIE}=${preference}; path=/; max-age=31536000; samesite=lax`;
  window.dispatchEvent(new CustomEvent<ThemePreference>(THEME_EVENT, { detail: preference }));
}

export function readThemePreference(): ThemePreference {
  const match = document.cookie.match(new RegExp(`(?:^|; )${THEME_COOKIE}=([^;]+)`));
  const value = match?.[1];
  return isThemePreference(value) ? value : "system";
}
