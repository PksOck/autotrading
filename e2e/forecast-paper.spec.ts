import { expect, test } from "@playwright/test";

test("instrument page shows the next-close forecast section", async ({ page }) => {
  await page.clock.install({ time: new Date("2026-07-23T20:05:00Z") });
  await page.goto("/instruments/AMZN");

  await expect(page.getByRole("heading", { name: "Next-close forecast" })).toBeVisible();
  await expect(page.getByText(/naive last/i).first()).toBeVisible();
  expect(await page.title()).toContain("AMZN");
});

test("paper simulator shows portfolio, audit trail, and risk copy", async ({ page }) => {
  await page.goto("/paper");

  await expect(page.getByRole("heading", { name: "Paper trading simulator" })).toBeVisible();
  await expect(page.getByText(/final equity/i)).toBeVisible();
  await expect(page.getByRole("table")).toBeVisible();
  await expect(page.getByText(/kill switch/i).first()).toBeVisible();
});
