import { expect, test } from "@playwright/test";

test("valuation scenarios recompute and refuse dangerous input", async ({ page }) => {
  await page.clock.install({ time: new Date("2026-07-23T20:05:00Z") });
  await page.goto("/instruments/AMZN");

  await expect(page.getByRole("heading", { name: "Valuation scenarios" })).toBeVisible();
  const result = page.getByRole("region", { name: "Valuation result" });
  await expect(result.getByText(/per-share estimate/i)).toBeVisible();
  const before = await result.textContent();

  await page.getByRole("button", { name: "Optimistic", exact: true }).click();
  await expect(page.getByRole("button", { name: "Optimistic", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(await result.textContent()).not.toBe(before);
  await expect(page.getByText(/estimate — not a recommendation/i)).toBeVisible();

  await page.getByLabel(/terminal growth \(%\)/i).fill("10");
  await expect(page.getByText(/terminal growth must stay below the discount rate/i)).toBeVisible();
  await expect(result).not.toBeVisible();
});

test("watchlist toggle persists and the watchlist page manages symbols", async ({ page }) => {
  await page.clock.install({ time: new Date("2026-07-23T20:05:00Z") });
  await page.goto("/instruments/AMZN");

  const toggle = page.getByRole("button", { name: /add amzn to watchlist/i });
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  await toggle.click();
  await expect(page.getByRole("button", { name: /remove amzn from watchlist/i })).toHaveAttribute(
    "aria-pressed",
    "true",
  );

  await page.reload();
  await expect(page.getByRole("button", { name: /remove amzn from watchlist/i })).toBeVisible();

  await page.getByRole("link", { name: "Watchlist" }).click();
  await expect(page).toHaveURL(/\/watchlist$/);
  await expect(page.getByRole("link", { name: /amazon\.com/i })).toHaveAttribute(
    "href",
    "/instruments/AMZN",
  );

  await page.getByRole("button", { name: /remove amzn from watchlist/i }).click();
  await expect(page.getByText(/your watchlist is empty/i)).toBeVisible();
});
