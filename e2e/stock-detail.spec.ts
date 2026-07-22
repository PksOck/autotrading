import { expect, test } from "@playwright/test";

test("stock page exposes provenance and financials without page overflow", async ({ page }) => {
  await page.goto("/stocks/AMZN");
  await expect(page.getByText("$217.35")).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Data provenance" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Annual financials" })).toBeVisible();
  const overflows = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflows).toBe(false);
});
