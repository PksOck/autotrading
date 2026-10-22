import { expect, test } from "@playwright/test";

test("instrument page links its entry zone to the Entries screen", async ({ page }, info) => {
  test.skip(info.project.name === "phone", "desktop flow");
  await page.goto("/i/COST", { waitUntil: "domcontentloaded" });
  const link = page.getByRole("link", { name: /Odpri v Vstopih/ });
  await expect(link).toBeVisible();
  await expect(link).toHaveAttribute("href", "/entries?symbol=COST");
  await expect(page.getByRole("button", { name: "Cona" })).toHaveAttribute("aria-pressed", "true");
});
