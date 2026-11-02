import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, vi } from "vitest";
import en from "@/messages/en.json";
import type { AutomationControl, AutomationPolicy } from "@/lib/api/automation";
import { AutomationSettings } from "./AutomationSettings";

const policy = (key: string, enabled = true): AutomationPolicy => ({
  process_key: key,
  revision: 7,
  enabled,
  schedule_kind: "daily",
  local_time: "09:30",
  timezone: "UTC",
  interval_minutes: 60,
  weekdays: [0, 2, 4],
  window_start: "08:00",
  window_end: "16:00",
  cap: 5,
  scope: "portfolio",
  next_runs: ["2026-11-02T09:30:00Z"],
});
let control: AutomationControl;
let policies: AutomationPolicy[];
let writes: { path: string; body: Record<string, unknown> }[];
let failure: string;
let controlReadFailure: boolean;
let policyReadFailure: boolean;
let held: Promise<void> | null;
let readHold: Promise<void> | null;
let client: QueryClient;

beforeEach(() => {
  control = { revision: 3, paused: false, automatic_analyses_enabled: false };
  policies = [
    policy("radar"),
    policy("entries"),
    policy("batch_analyses", false),
    policy("digest"),
  ];
  writes = [];
  failure = "";
  controlReadFailure = false;
  policyReadFailure = false;
  held = null;
  readHold = null;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, init?: RequestInit) => {
      const path = String(input).replace("/api", "");
      if (!init?.method && path === "/automation/policies" && readHold) await readHold;
      if (policyReadFailure && path === "/automation/policies" && !init?.method)
        return Response.json({ detail: "unavailable" }, { status: 503 });
      if (controlReadFailure && path === "/automation/control" && !init?.method)
        return Response.json({ detail: "unavailable" }, { status: 503 });
      if (init?.method === "PATCH") {
        const body = JSON.parse(String(init.body));
        writes.push({ path, body });
        if (held) await held;
        if (path === failure)
          return Response.json({ detail: "revision_conflict" }, { status: 409 });
        if (path === "/automation/control") {
          control = { ...body, revision: body.revision + 1 };
          return Response.json(control);
        }
        const key = path.split("/").at(-1);
        policies = policies.map((row) =>
          row.process_key === key ? { ...row, ...body, revision: body.revision + 1 } : row,
        );
        return Response.json(policies.find((row) => row.process_key === key));
      }
      return Response.json(
        path === "/automation/control" ? control : path === "/automation/policies" ? policies : [],
      );
    }),
  );
  client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  });
});

it("keeps the global pause when changing model permission", async () => {
  control = { revision: 3, paused: true, automatic_analyses_enabled: false };
  mount();
  const models = screen.getByRole("switch", { name: "Allow automatic model analyses" });
  await waitFor(() => expect(models).not.toBeDisabled());
  fireEvent.click(models);
  await waitFor(() => expect(models).toBeChecked());
  expect(writes[0]?.body).toEqual({ revision: 3, paused: true, automatic_analyses_enabled: true });
  expect(screen.getByRole("switch", { name: "All automation" })).not.toBeChecked();
});

it("fails closed when controls cannot be loaded", async () => {
  controlReadFailure = true;
  mount();
  expect(await screen.findByRole("alert")).toBeVisible();
  expect(screen.getByRole("switch", { name: "All automation" })).toBeDisabled();
  expect(screen.getByRole("switch", { name: "All automation" })).not.toBeChecked();
  expect(writes).toEqual([]);
});

it("locks an open editor during its quick toggle and does not replace a newer editor on completion", async () => {
  let release!: () => void;
  held = new Promise((resolve) => {
    release = resolve;
  });
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Edit schedule for Radar" }));
  fireEvent.click(screen.getByRole("switch", { name: "Enable module Radar" }));
  await waitFor(() => expect(screen.getByLabelText("Schedule")).toBeDisabled());
  fireEvent.click(screen.getByRole("button", { name: "Edit schedule for Entries" }));
  fireEvent.change(screen.getByLabelText("Schedule"), { target: { value: "interval" } });
  fireEvent.change(screen.getByLabelText("Interval in minutes"), { target: { value: "120" } });
  release();
  await waitFor(() =>
    expect(screen.getByRole("switch", { name: "Enable module Radar" })).not.toBeChecked(),
  );
  expect(screen.getByLabelText("Interval in minutes")).toHaveValue(120);
  expect(screen.getByRole("region", { name: "Entries" })).toBeVisible();
});

it("preserves a rejected schedule draft until an explicit revision reload", async () => {
  failure = "/automation/policies/radar";
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Edit schedule for Radar" }));
  fireEvent.change(screen.getByLabelText("Schedule"), { target: { value: "interval" } });
  fireEvent.change(screen.getByLabelText("Interval in minutes"), { target: { value: "120" } });
  fireEvent.click(screen.getByRole("button", { name: "Save" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/changed/i);
  expect(screen.getByLabelText("Interval in minutes")).toHaveValue(120);
  expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  expect(writes).toHaveLength(1);
  policyReadFailure = true;
  fireEvent.click(screen.getByRole("button", { name: "Load latest revision" }));
  await waitFor(() => expect(screen.getAllByRole("alert").length).toBeGreaterThan(1));
  expect(screen.getByLabelText("Interval in minutes")).toHaveValue(120);
  policyReadFailure = false;
  fireEvent.click(screen.getByRole("button", { name: "Load latest revision" }));
  await waitFor(() => expect(screen.getByLabelText("Schedule")).toHaveValue("daily"));
  expect(writes).toHaveLength(1);
});
afterEach(() => {
  client.clear();
  vi.unstubAllGlobals();
});
function mount() {
  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
        <AutomationSettings />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

it("exposes the master switch and resumes without changing model permission or module choices", async () => {
  mount();
  const master = await screen.findByRole("switch", { name: "All automation" });
  await waitFor(() => expect(master).toBeChecked());
  expect(screen.getByRole("switch", { name: "Allow automatic model analyses" })).not.toBeChecked();
  expect(
    screen.getByRole("switch", { name: "Enable module Recurring analysis batch" }),
  ).not.toBeChecked();
  fireEvent.click(master);
  await waitFor(() => expect(master).not.toBeChecked());
  expect(writes[0]).toEqual({
    path: "/automation/control",
    body: { revision: 3, paused: true, automatic_analyses_enabled: false },
  });
  fireEvent.click(master);
  await waitFor(() => expect(master).toBeChecked());
  expect(writes[1]!.body).toEqual({
    revision: 4,
    paused: false,
    automatic_analyses_enabled: false,
  });
  expect(policies.find((row) => row.process_key === "batch_analyses")?.enabled).toBe(false);
  expect(writes.every((row) => row.path === "/automation/control")).toBe(true);
});

it("persists only enabled with the existing revision and schedule, without an optimistic success or run", async () => {
  let release!: () => void;
  held = new Promise((resolve) => {
    release = resolve;
  });
  mount();
  const toggle = await screen.findByRole("switch", { name: "Enable module Radar" });
  fireEvent.click(toggle);
  await waitFor(() => expect(toggle).toBeDisabled());
  expect(toggle).toBeChecked();
  expect(toggle).toBeDisabled();
  fireEvent.click(toggle);
  expect(writes).toHaveLength(1);
  release();
  await waitFor(() => expect(toggle).not.toBeChecked());
  expect(writes[0]!.body).toEqual({
    revision: 7,
    enabled: false,
    schedule_kind: "daily",
    local_time: "09:30",
    timezone: "UTC",
    interval_minutes: 60,
    weekdays: [0, 2, 4],
    window_start: "08:00",
    window_end: "16:00",
    cap: 5,
    scope: "portfolio",
  });
  expect(writes[0]!.path).toBe("/automation/policies/radar");
});

it("requires a fresh control read after a conflict before allowing another write", async () => {
  failure = "/automation/control";
  mount();
  const master = screen.getByRole("switch", { name: "All automation" });
  await waitFor(() => expect(master).not.toBeDisabled());
  fireEvent.click(master);
  await screen.findByRole("alert");
  expect(master).toBeChecked();
  expect(master).toBeDisabled();
  fireEvent.click(master);
  expect(writes).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Reload settings" }));
  await waitFor(() => expect(master).not.toBeDisabled());
  expect(writes).toHaveLength(1);
});

it("locks a delayed discard read and keeps a newer editor when that read finishes", async () => {
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Edit schedule for Radar" }));
  let release!: () => void;
  readHold = new Promise((resolve) => {
    release = resolve;
  });
  fireEvent.click(screen.getByRole("button", { name: "Discard draft" }));
  await waitFor(() => expect(screen.getByLabelText("Schedule")).toBeDisabled());
  fireEvent.click(screen.getByRole("button", { name: "Edit schedule for Entries" }));
  fireEvent.change(screen.getByLabelText("Schedule"), { target: { value: "interval" } });
  fireEvent.change(screen.getByLabelText("Interval in minutes"), { target: { value: "120" } });
  release();
  await waitFor(() => expect(client.isFetching()).toBe(0));
  expect(screen.getByLabelText("Interval in minutes")).toHaveValue(120);
  expect(screen.getByRole("button", { name: "Edit schedule for Radar" })).toBeDisabled();
  expect(writes).toEqual([]);
});

it("ignores an obsolete reload after closing and reopening the same module", async () => {
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Edit schedule for Radar" }));
  let release!: () => void;
  readHold = new Promise((resolve) => {
    release = resolve;
  });
  fireEvent.click(screen.getByRole("button", { name: "Discard draft" }));
  await waitFor(() => expect(screen.getByLabelText("Schedule")).toBeDisabled());
  fireEvent.click(screen.getByRole("button", { name: "Edit schedule for Entries" }));
  fireEvent.click(screen.getByRole("button", { name: "Edit schedule for Radar" }));
  fireEvent.change(screen.getByLabelText("Schedule"), { target: { value: "interval" } });
  fireEvent.change(screen.getByLabelText("Interval in minutes"), { target: { value: "120" } });
  release();
  await waitFor(() => expect(client.isFetching()).toBe(0));
  expect(screen.getByLabelText("Interval in minutes")).toHaveValue(120);
  expect(screen.getByRole("button", { name: "Edit schedule for Entries" })).toBeDisabled();
});

it("keeps a rejected module toggle unchanged and requires an explicit refresh instead of retrying", async () => {
  failure = "/automation/policies/radar";
  mount();
  const toggle = await screen.findByRole("switch", { name: "Enable module Radar" });
  fireEvent.click(toggle);
  expect(await screen.findByRole("alert")).toHaveTextContent(/changed/i);
  expect(toggle).toBeChecked();
  expect(toggle).toBeDisabled();
  expect(writes).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Reload module Radar" }));
  await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
  expect(writes).toHaveLength(1);
});

it("retains an unsaved editor through a global toggle and preserves hidden restrictions on save", async () => {
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Edit schedule for Radar" }));
  fireEvent.click(screen.getByText("Additional restrictions", { exact: true }));
  const timezone = screen.getByRole("textbox", { name: "IANA time zone" });
  fireEvent.change(timezone, { target: { value: "Europe/Ljubljana" } });
  expect(screen.getByRole("switch", { name: "Enable module Radar" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Edit schedule for Entries" })).toBeDisabled();
  fireEvent.click(screen.getByRole("switch", { name: "All automation" }));
  await waitFor(() =>
    expect(screen.getByRole("switch", { name: "All automation" })).not.toBeChecked(),
  );
  expect(timezone).toHaveValue("Europe/Ljubljana");
  fireEvent.click(screen.getByRole("button", { name: "Save" }));
  await waitFor(() => expect(writes).toHaveLength(2));
  expect(writes[1]!.body).toMatchObject({
    revision: 7,
    enabled: true,
    timezone: "Europe/Ljubljana",
    weekdays: [0, 2, 4],
    window_start: "08:00",
    window_end: "16:00",
  });
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Edit schedule for Entries" })).not.toBeDisabled(),
  );
});
