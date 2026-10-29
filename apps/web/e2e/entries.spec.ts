import { expect, test } from "@playwright/test";

test("entries: map, list, detail with cause and ladder", async ({ page }, info) => {
  await page.goto("/entries", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { level: 1, name: "Vstopi" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Zemljevid vstopov" })).toBeVisible();

  const list = page.getByRole("region", { name: "Kandidati za vstop" });
  await expect(list.getByRole("button").first()).toBeVisible();
  await list.getByRole("button", { name: /MSFT/ }).click();
  await expect(page).toHaveURL(/symbol=MSFT/);

  const detail = page.getByRole(info.project.name === "phone" ? "dialog" : "complementary", {
    name: "Podrobnosti vstopa",
  });
  await expect(detail.getByText("Vzrok padca")).toBeVisible();
  await expect(detail.getByText("Sprožena pravila")).toBeVisible();
  if (info.project.name === "phone") return;

  // The budget split is plain arithmetic in the browser: a quantity column appears.
  await detail.getByLabel("Znesek").fill("10000");
  await expect(detail.getByRole("columnheader", { name: "Kosov" })).toBeVisible();

  await page.getByRole("button", { name: /^Vse \d+/ }).click();
  await expect(list.getByRole("button", { name: /EQQQ/ })).toBeVisible();
  await page.getByRole("tab", { name: "Portfelj" }).click();
  await expect(page).toHaveURL(/view=portfolio/);
});
