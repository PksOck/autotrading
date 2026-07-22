import { expect, test } from "@playwright/test";

test("legacy stock URLs redirect to the canonical instrument URL", async ({ page }) => {
  await page.goto("/stocks/AMZN");
  await expect(page).toHaveURL(/\/instruments\/AMZN$/);
});

test("instrument charts expose ranges, summaries, theme support, and responsive layout", async ({ page }) => {
  await page.goto("/instruments/AMZN");
  await expect(page.getByText("$217.35", { exact: true })).toBeVisible();
  await expect(page.getByText("AMZN · NASDAQ · USD", { exact: true })).toBeVisible();
  await expect(page.getByText("Fixture current", { exact: true })).toBeVisible();

  const provenance = page.getByRole("complementary", { name: "Data provenance" });
  await expect(provenance.getByText("Source: Illustrative fixture data", { exact: true })).toBeVisible();
  await expect(provenance.locator('time[datetime="2026-07-22T12:00:00Z"]')).toHaveText(
    "7/22/2026, 12:00:00 PM UTC",
  );

  await expect(page.getByRole("heading", { name: "Price history" })).toBeVisible();
  await expect(page.getByText(/observations:/)).toBeVisible();
  await expect(page.getByText("Volume shown below price")).toBeVisible();

  const chartFrame = page.getByTestId("price-volume-chart-frame");
  await expect(chartFrame).toBeVisible();
  await expect(chartFrame).toHaveAttribute("data-range", "1Y");
  await expect(chartFrame).toHaveAttribute("data-volume", "shown");

  const annualFinancials = page.getByRole("heading", { name: "Annual financials" }).locator("xpath=ancestor::section");
  await expect(annualFinancials.getByText("USD millions", { exact: true })).toBeVisible();
  await expect(annualFinancials.getByRole("img", { name: "Revenue trend in USD millions" })).toBeVisible();

  for (const range of ["1M", "6M", "1Y", "5Y", "MAX"]) {
    const button = page.getByRole("button", { name: range, exact: true });
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await expect(chartFrame).toBeVisible();
    await expect(chartFrame).toHaveAttribute("data-range", range);
  }

  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.getByRole("button", { name: "Use light theme" })).toBeVisible();

  const overflows = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflows).toBe(false);
});
