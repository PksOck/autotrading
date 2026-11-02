import { expect, test } from "@playwright/test";

for (const locale of ["sl", "en"] as const) {
  test(`automation quick controls preserve schedules and drafts without submitting jobs (${locale})`, async ({
    page,
    context,
    request,
  }, info) => {
    const baseURL = String(info.project.use.baseURL);
    await context.addCookies([{ name: "locale", value: locale, url: baseURL }]);
    let control = { revision: 4, paused: false, automatic_analyses_enabled: false };
    let policies = await (await request.get("/api/automation/policies")).json();
    policies = policies.map((row: { process_key: string }) => ({
      ...row,
      enabled: row.process_key !== "batch_analyses",
    }));
    const original = structuredClone(
      policies.find((row: { process_key: string }) => row.process_key === "radar"),
    );
    const writes: { path: string; method: string; body: Record<string, unknown> }[] = [];
    await context.route("**/api/**", async (route) => {
      const req = route.request();
      const path = new URL(req.url()).pathname;
      if (req.method() !== "GET") {
        const body = req.postDataJSON();
        writes.push({ path, method: req.method(), body });
        if (req.method() === "PATCH" && path === "/api/automation/control") {
          control = { ...body, revision: body.revision + 1 };
          return route.fulfill({ json: control });
        }
        if (req.method() === "PATCH" && path === "/api/automation/policies/radar") {
          policies = policies.map((row: { process_key: string }) =>
            row.process_key === "radar" ? { ...row, ...body, revision: body.revision + 1 } : row,
          );
          return route.fulfill({
            json: policies.find((row: { process_key: string }) => row.process_key === "radar"),
          });
        }
        return route.abort();
      }
      if (path === "/api/automation/control") return route.fulfill({ json: control });
      if (path === "/api/automation/policies") return route.fulfill({ json: policies });
      return route.continue();
    });
    await page.goto("/settings");
    const main = page.getByRole("switch", {
      name: locale === "sl" ? "Vsa avtomatika" : "All automation",
      exact: true,
    });
    await expect(main).toBeChecked();
    const section = page.getByRole("region", {
      name: locale === "sl" ? "Procesi in urniki" : "Processes and schedules",
      exact: true,
    });
    await expect(section.getByRole("switch")).toHaveCount(policies.length + 2);
    await main.click();
    await expect(main).not.toBeChecked();
    expect(writes[0]!.body).toEqual({
      revision: 4,
      paused: true,
      automatic_analyses_enabled: false,
    });
    await main.click();
    await expect(main).toBeChecked();
    const radar = page.getByRole("switch", {
      name: locale === "sl" ? "Omogoči modul Radar" : "Enable module Radar",
      exact: true,
    });
    await radar.click();
    await expect(radar).not.toBeChecked();
    expect(writes[2]!.body).toMatchObject({
      revision: original.revision,
      enabled: false,
      schedule_kind: original.schedule_kind,
      timezone: original.timezone,
      weekdays: original.weekdays,
      window_start: original.window_start,
      window_end: original.window_end,
    });
    await page
      .getByRole("button", {
        name: locale === "sl" ? "Uredi urnik: Radar" : "Edit schedule for Radar",
        exact: true,
      })
      .click();
    const editor = page.getByRole("region", { name: "Radar", exact: true });
    await editor
      .getByLabel(locale === "sl" ? "Urnik" : "Schedule", { exact: true })
      .selectOption("daily");
    const time = editor.getByLabel(locale === "sl" ? "Lokalna ura" : "Local time", { exact: true });
    await time.fill("10:15");
    await expect(radar).toBeDisabled();
    await main.click();
    await expect(main).not.toBeChecked();
    await expect(time).toHaveValue("10:15");
    await editor
      .getByRole("button", { name: locale === "sl" ? "Shrani" : "Save", exact: true })
      .click();
    await expect(radar).toBeEnabled();
    expect(writes.at(-1)!.body).toMatchObject({
      enabled: false,
      schedule_kind: "daily",
      local_time: "10:15",
      weekdays: original.weekdays,
      window_start: original.window_start,
      window_end: original.window_end,
    });
    expect(writes.every((row) => row.method === "PATCH" && !row.path.endsWith("/run"))).toBe(true);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth),
    ).toBeLessThanOrEqual(1);
    if (process.env.SHOTS_DIR)
      await section.screenshot({
        path: `${process.env.SHOTS_DIR}/${info.project.name}-automation-${locale}.png`,
      });
  });
}

test("portfolio exposes daily and YTD estimates with an explicit missing baseline", async ({
  page,
}) => {
  await page.route("**/api/portfolio*", async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    body.ytd_move = {
      amount: null,
      reason: "missing_year_start",
      basis: "held_positions_ytd_constant_reported_fx",
    };
    body.ytd_native = [
      {
        currency: "USD",
        position_count: 1,
        amount: null,
        reason: "missing_year_start",
        basis: "held_positions_ytd_constant_reported_fx",
      },
    ];
    await route.fulfill({ json: body });
  });
  await page.goto("/portfolio");
  const summary = page.getByRole("region", { name: "Cenovni premik pozicij", exact: true });
  await expect(summary).toBeVisible();
  await summary.getByLabel("Obdobje premika", { exact: true }).selectOption("ytd");
  await expect(
    summary
      .getByText("Ni primerljive zaključne cene pred začetkom tega leta.", { exact: true })
      .first(),
  ).toBeVisible();
  await summary.getByLabel("Obdobje premika", { exact: true }).selectOption("day");
  await expect(summary.getByText("Ločeno po izvornih valutah", { exact: true })).toBeVisible();
});
