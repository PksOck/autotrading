import { expect, test } from "@playwright/test";

test("legacy stock URLs redirect to the canonical instrument URL", async ({ page }) => {
  await page.goto("/stocks/AMZN");
  await expect(page).toHaveURL(/\/instruments\/AMZN$/);
});

test("instrument charts expose ranges, summaries, theme support, and responsive layout", async ({ page }) => {
  await page.goto("/instruments/AMZN");
  await expect(page.getByText("$217.35", { exact: true })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Data provenance" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Price history" })).toBeVisible();
  await expect(page.getByText(/observations:/)).toBeVisible();
  await expect(page.getByText("Volume shown below price")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Annual financials" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Revenue trend in USD millions" }).first()).toBeVisible();

  for (const range of ["1M", "6M", "1Y", "5Y", "MAX"]) {
    const button = page.getByRole("button", { name: range, exact: true });
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true");
  }

  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.getByRole("button", { name: "Use light theme" })).toBeVisible();

  const overflows = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflows).toBe(false);
});
