"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

type S = components["schemas"];
export type AutomationPolicy = S["PolicyOut"];
export type AutomationPolicyInput = S["PolicyInput"];
export type AutomationBatchInput = S["BatchInput"];
export type AutomationBatchPreview = S["BatchPreview"];
export type AutomationControl = S["ControlInput"];

export function useAutomationPolicies() {
  return useQuery({ queryKey: ["automation", "policies"], queryFn: () => api.get<AutomationPolicy[]>("/automation/policies") });
}
export function useAutomationControl() {
  return useQuery({ queryKey: ["automation", "control"], queryFn: () => api.get<AutomationControl>("/automation/control") });
}
export function useAutomationExecutions() {
  return useQuery({ queryKey: ["automation", "executions"], queryFn: () => api.get<S["ExecutionOut"][]>("/automation/executions"), refetchInterval: 15000 });
}
export function useSaveAutomationPolicy(key: string) {
  const client = useQueryClient();
  return useMutation({ mutationFn: (body: AutomationPolicyInput) => api.send<AutomationPolicy>(`/automation/policies/${key}`, "PATCH", body), onSuccess: () => client.invalidateQueries({ queryKey: ["automation"] }) });
}
export function useSetAutomationControl() {
  const client = useQueryClient();
  return useMutation({ mutationFn: (body: AutomationControl) => api.send<AutomationControl>("/automation/control", "PATCH", body), onSuccess: () => client.invalidateQueries({ queryKey: ["automation"] }) });
}
export function useRunProcess(key: string) {
  const client = useQueryClient();
  return useMutation({ mutationFn: (body: S["RunInput"]) => api.send<{ id: string; state: string }>(`/automation/policies/${key}/run`, "POST", body), onSuccess: () => client.invalidateQueries({ queryKey: ["automation"] }) });
}
export function useBatchPreview() {
  return useMutation({ mutationFn: (body: AutomationBatchInput) => api.send<AutomationBatchPreview>("/automation/batch/preview", "POST", body) });
}
export function useRunBatch() {
  const client = useQueryClient();
  return useMutation({ mutationFn: (body: AutomationBatchInput) => api.send<AutomationBatchPreview>("/automation/batch/run", "POST", body), onSuccess: async () => { await client.invalidateQueries({ queryKey: ["analyses"] }); await client.invalidateQueries({ queryKey: ["automation"] }); } });
}
