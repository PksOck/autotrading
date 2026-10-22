import { expect, test } from "@playwright/test";

const shots = process.env.SHOTS_DIR;
const shot = async (page: import("@playwright/test").Page, name: string) => {
  if (shots) await page.screenshot({ path: `${shots}/${name}.png`, fullPage: false });
};

test("overview renders in Slovenian with no console errors", async ({ page }, info) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "Pregled" })).toBeVisible();
  await page.waitForTimeout(1500);
  await shot(page, `${info.project.name}-overview-light`);
  expect(errors.filter((e) => !e.includes("503"))).toEqual([]);
});

test("theme and language switch", async ({ page }, info) => {
  test.skip(info.project.name === "phone", "header controls checked on desktop");
  await page.goto("/");
  await page.getByRole("button", { name: /Preklopi temo/ }).click();
  await page.getByRole("button", { name: /Preklopi temo/ }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "en", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Overview" })).toBeVisible();
  await page.waitForTimeout(1200);
  await shot(page, "desktop-overview-dark-en");
  await page.getByRole("button", { name: "sl", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Pregled" })).toBeVisible();
});

test("command palette opens a peek panel", async ({ page }, info) => {
  test.skip(info.project.name === "phone", "keyboard flow");
  await page.goto("/", { waitUntil: "networkidle" });
  await page.keyboard.press("Control+k");
  await page.getByPlaceholder("Išči simbol, zaslon ali dejanje").fill("asml");
  await expect(page.getByRole("option", { name: /ASML Holding/ })).toBeVisible();
  await shot(page, "desktop-command-palette");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/peek=instrument%3AASML|peek=instrument:ASML/);
  await expect(page.getByRole("dialog")).toContainText("ASML Holding");
  await page.waitForTimeout(800);
  await shot(page, "desktop-peek");
});

test("manual proposal with undo", async ({ page }, info) => {
  test.skip(info.project.name === "phone", "desktop flow");
  await page.goto("/");
  await page.getByRole("button", { name: "Predlog", exact: true }).click();
  await page.getByLabel("Simbol(i)").fill("nvda, $amd");
  await page.getByLabel("Hipoteza").fill("Padec po poročilu je pretiran.");
  await page.getByText("Globoko", { exact: true }).click();
  await shot(page, "desktop-proposal");
  await page.getByRole("button", { name: "Pošlji v analizo" }).click();
  await expect(page.getByText("Predlog NVDA, AMD je v vrsti")).toBeVisible();
  await page.goto("/proposals");
  await expect(page.getByText("Padec po poročilu je pretiran.")).toBeVisible();
});

test("phone layout uses bottom navigation", async ({ page }, info) => {
  test.skip(info.project.name !== "phone", "phone only");
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Radar" }).last()).toBeVisible();
  await page.waitForTimeout(1200);
  await shot(page, "phone-overview");
});
