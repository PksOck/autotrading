import { expect, test } from "@playwright/test";

test("positions return to a customizable standard view with dated trends and signed changes", async ({
  page,
}) => {
  await page.goto("/portfolio");
  const positions = page.getByRole("region", { name: "Pozicije", exact: true });
  await positions.getByRole("button", { name: "Vrednotenje", exact: true }).click();
  await expect(positions.getByRole("columnheader", { name: /Forward P\/E/ })).toBeVisible();
  await positions.getByRole("button", { name: "Standardno", exact: true }).click();
  for (const column of ["Količina", "Vrednost", "Teža", "Nerealiziran P/L", "Dnevna sprememba"]) {
    await expect(positions.getByRole("columnheader", { name: new RegExp(column) })).toBeVisible();
  }
  await expect(positions.getByText("Do 30 trgovalnih dni").first()).toBeVisible();
  await expect(positions.locator(".text-pos").first()).toBeVisible();
  await positions.getByRole("button", { name: "Dividende", exact: true }).click();
  await positions.getByRole("button", { name: "Standardno", exact: true }).click();
  await page.reload();
  await expect(positions.getByRole("columnheader", { name: /Količina/ })).toBeVisible();
});

test("overview restores explanations and demo theses have real detail examples", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Tržni dan/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Portfelj danes" })).toBeVisible();
  await expect(page.getByText(/Vsaka pika je dogodek/)).toBeVisible();
  await expect(page.getByRole("meter").first()).toBeVisible();
  await page.goto("/theses");
  await expect(page.getByText("MSFT", { exact: true })).toBeVisible();
  await expect(page.getByText("ORCL", { exact: true })).toBeVisible();
  await expect(page.getByText("COST", { exact: true })).toBeVisible();
});

test("settings expose master switch and SMTP; saved-record testing requires explicit calculation", async ({
  page,
}) => {
  await page.goto("/settings");
  await expect(
    page.getByRole("switch", { name: "Dovoli samodejne analize z modeli" }),
  ).toBeVisible();
  await expect(page.getByLabel("Izberi proces za urejanje")).toHaveValue("radar");
  await page.locator("summary").filter({ hasText: "E-poštna obvestila" }).click();
  await expect(page.getByRole("textbox", { name: /^Prejemniki/ })).toBeVisible();
  await expect(page.getByRole("checkbox", { name: "Omogoči e-poštna obvestila" })).toBeDisabled();
  await page.goto("/track-record");
  const calculation = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/backtest") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Izračunaj iz shranjenih zapisov" }).click();
  const response = await calculation;
  expect(response.ok()).toBe(true);
  expect((await response.json()).completed).toBeGreaterThan(0);
  await expect(page.getByText(/izmerjenih ·/)).toBeVisible();
});
