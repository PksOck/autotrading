import { cookies } from "next/headers";
import { SettingsView } from "@/components/settings/SettingsView";
import { THEME_COOKIE, isThemePreference } from "@/lib/theme";

export default async function Page() {
  const stored = (await cookies()).get(THEME_COOKIE)?.value;
  return <SettingsView theme={isThemePreference(stored) ? stored : "system"} />;
}
