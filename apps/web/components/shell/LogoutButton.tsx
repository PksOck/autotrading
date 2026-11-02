"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { signalSessionEnd } from "@/lib/client-access";

export function LogoutButton() {
  const t = useTranslations("ownerLogin");
  const query = useQueryClient();
  const [failed, setFailed] = useState(false);
  return (
    <div>
      <button
        type="button"
        className="min-h-10 px-3 text-xs text-text-2"
        onClick={async () => {
          setFailed(false);
          try {
            const response = await fetch("/api/auth/logout", { method: "POST" });
            if (!response.ok) throw new Error("logout_failed");
            query.clear();
            signalSessionEnd();
            window.location.replace("/login");
          } catch {
            setFailed(true);
          }
        }}
      >
        {t("logout")}
      </button>
      {failed && (
        <span role="alert" className="text-xs text-warn">
          {t("logoutFailed")}
        </span>
      )}
    </div>
  );
}
