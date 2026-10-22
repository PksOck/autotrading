import { expect, test } from "@playwright/test";

test("portfolio lists demo positions and demo badge", async ({ page }, info) => {
  test.skip(info.project.name === "phone", "desktop flow");
  await page.goto("/portfolio", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { level: 1, name: "Portfelj" })).toBeVisible();
  await expect(page.getByText("demo podatki").first()).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Teža" })).toBeVisible();
  const table = page.getByRole("table").first();
  await expect(table.getByText("VWRA").first()).toBeVisible();
  await expect(table.getByText("MSFT").first()).toBeVisible();
});

test("watchlist: add and remove a symbol", async ({ page, request }, info) => {
  test.skip(info.project.name === "phone", "desktop flow");
  // make the test re-runnable: drop any pre-existing NVDA entry
  const res = await request.get("/api/watchlist");
  expect(res.ok()).toBeTruthy();
  const items: { id: number; symbol: string }[] = await res.json();
  for (const it of items.filter((i) => i.symbol === "NVDA")) {
    expect((await request.delete(`/api/watchlist/${it.id}`)).ok()).toBeTruthy();
  }

  await page.goto("/portfolio?tab=watchlist", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: "Aktivna" })).toBeVisible();
  await page.getByLabel("Simbol", { exact: true }).fill("NVDA");
  await page.getByLabel("Opomba ali teza").fill("E2E test teza");
  await page.getByRole("button", { name: "Dodaj na watchlisto" }).click();

  const active = page.locator("section", { has: page.getByRole("heading", { name: "Aktivna" }) }).last();
  await expect(active.getByText("NVDA").first()).toBeVisible();

  await active.locator("li, tr, article, div").filter({ hasText: "NVDA" }).filter({
    has: page.getByRole("button", { name: "Odstrani" }),
  }).last().getByRole("button", { name: "Odstrani" }).click();
  await expect(page.getByText("Odstranjeno z watchliste")).toBeVisible();

  const after: { symbol: string }[] = await (await request.get("/api/watchlist")).json();
  expect(after.some((i) => i.symbol === "NVDA")).toBe(false);
});

test("instrument page renders chart and key data", async ({ page }, info) => {
  test.skip(info.project.name === "phone", "desktop flow");
  await page.goto("/i/MSFT", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { level: 1, name: "MSFT" })).toBeVisible();
  await expect(page.getByText("Ključni podatki").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Analiziraj" })).toBeVisible();
  await expect(page.locator("canvas").first()).toBeVisible();
  await page.getByRole("button", { name: "3M", exact: true }).click();
  await expect(page.locator("canvas").first()).toBeVisible();
});

test("unknown instrument shows not-found text", async ({ page }, info) => {
  test.skip(info.project.name === "phone", "desktop flow");
  await page.goto("/i/ZZZZ");
  await expect(page.getByText("Instrumenta ZZZZ ni v bazi.")).toBeVisible();
});

test("phone: portfolio has no horizontal overflow", async ({ page }, info) => {
  test.skip(info.project.name !== "phone", "phone only");
  await page.goto("/portfolio", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { level: 1, name: "Portfelj" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
});
