import Link from "next/link";

import { ThemeToggle } from "@/components/theme/theme-toggle";

export function AppHeader() {
  return (
    <header className="app-header">
      <Link className="brand" href="/">Northstar Research</Link>
      <nav aria-label="Primary navigation">
        <Link href="/">Home</Link>
        <Link href="/methodology">Methodology</Link>
      </nav>
      <ThemeToggle />
    </header>
  );
}
