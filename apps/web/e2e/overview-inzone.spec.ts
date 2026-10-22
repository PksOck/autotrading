import { expect, test } from "@playwright/test";

test("overview: In zone card shows entry candidates and links to entries", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  const card = page.getByRole("region", { name: "V coni" });
  await expect(card).toBeVisible();
  await expect(card.getByRole("img", { name: "Zemljevid vstopov" })).toBeVisible();
  await expect(card.getByRole("link", { name: /COST/ })).toBeVisible();
  await card.getByRole("link", { name: /COST/ }).click();
  await expect(page).toHaveURL(/\/entries\?symbol=COST/);
});
