import { expect, test } from "@playwright/test";

test("track record: horizons, your proposals apart, calibration", async ({ page }) => {
  await page.goto("/track-record", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { level: 1, name: "Uspešnost" })).toBeVisible();
  await expect(page.getByText("Vir: izidi signalov")).toBeVisible();
  await expect(page.getByText("Alfa proti CSPX")).toBeVisible();
  await expect(page.getByTestId("origin-user").getByText("Tvoji predlogi")).toBeVisible();
  await expect(page.getByTestId("origin-system").getByText("Sistemski signali")).toBeVisible();
  await expect(page.getByRole("meter")).toHaveCount(5);

  // A 1-day horizon has an outcome for every seeded past signal.
  const request = page.waitForResponse((r) => r.url().includes("/api/track-record?horizon_days=1"));
  await page.getByText("1 d", { exact: true }).click();
  expect((await request).ok()).toBe(true);
  await expect(page.getByRole("radio", { name: "1 d" })).toBeChecked();
});
