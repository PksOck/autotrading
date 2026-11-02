"use client";

import { useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";

export default function LoginPage() {
  const t = useTranslations("ownerLogin");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username: data.get("username"), password: data.get("password") }),
      });
      if (!response.ok) {
        setError(
          response.status === 429
            ? "throttled"
            : response.status === 503
              ? "notConfigured"
              : "invalid",
        );
        return;
      }
      window.location.replace("/");
    } catch {
      setError("unavailable");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="mx-auto max-w-sm space-y-6 rounded-xl border border-border bg-surface p-6">
      <div>
        <p className="text-sm text-accent">{t("brand")}</p>
        <h1 className="mt-2 text-2xl font-semibold">{t("title")}</h1>
        <p className="mt-2 text-sm text-text-2">{t("description")}</p>
      </div>
      <form onSubmit={submit} className="space-y-4">
        <label className="block text-sm">
          {t("username")}
          <input
            name="username"
            autoComplete="username"
            required
            maxLength={100}
            className="mt-1 min-h-12 w-full rounded-md border border-border bg-surface px-3"
          />
        </label>
        <label className="block text-sm">
          {t("password")}
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
            maxLength={256}
            className="mt-1 min-h-12 w-full rounded-md border border-border bg-surface px-3"
          />
        </label>
        {error && (
          <p role="alert" className="text-sm text-warn">
            {t(error)}
          </p>
        )}
        <button
          disabled={busy}
          className="min-h-12 w-full rounded-md bg-accent px-4 font-medium text-on-accent disabled:opacity-50"
        >
          {t(busy ? "signingIn" : "signIn")}
        </button>
      </form>
      <p className="text-xs text-text-3">{t("private")}</p>
    </section>
  );
}
