"use client";

import { useState } from "react";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  function toggleTheme() {
    const nextDark = !dark;
    setDark(nextDark);
    document.documentElement.classList.toggle("dark", nextDark);
    localStorage.setItem("theme", nextDark ? "dark" : "light");
  }

  return (
    <button type="button" className="theme-toggle" onClick={toggleTheme}>
      {dark ? "Use light theme" : "Use dark theme"}
    </button>
  );
}
