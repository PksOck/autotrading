"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

export type EmailPreferences = components["schemas"]["EmailPreferencesOut"];
export function useEmailPreferences() {
  return useQuery({
    queryKey: ["email-preferences"],
    queryFn: () => api.get<EmailPreferences>("/notifications/email"),
  });
}
export function useSaveEmailPreferences() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: components["schemas"]["EmailPreferencesInput"]) =>
      api.send<EmailPreferences>("/notifications/email", "PATCH", body),
    onSuccess: () => client.invalidateQueries({ queryKey: ["email-preferences"] }),
  });
}
