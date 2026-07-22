import { expect, test } from "@playwright/test";

test("search opens the canonical AMZN instrument page", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("searchbox", { name: /symbol or company/i }).fill("Amazon");
  await page.getByRole("link", { name: /amazon.com/i }).click();
  await expect(page).toHaveURL(/\/instruments\/AMZN$/);
  await expect(page.getByRole("heading", { name: /amazon.com, inc./i })).toBeVisible();
});
