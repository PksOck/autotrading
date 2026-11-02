import { expect, test } from "@playwright/test";

const base = process.env.AUTH_TEST_BASE_URL;
test.skip(!base, "Requires the isolated owner-auth Docker test stack, never a real owner account");

test("owner login protects API and page, exposes supporting links, and revokes both tabs", async ({
  page,
  context,
}) => {
  await page.goto(`${base}/portfolio`);
  await expect(page).toHaveURL(`${base}/login`);
  await expect(page.getByRole("heading", { name: "Zasebna prijava" })).toBeVisible();
  for (const href of ["about", "privacy", "terms", "security"]) {
    expect((await page.request.get(`${base}/${href}`)).ok()).toBeTruthy();
  }
  expect((await page.request.get(`${base}/api/portfolio`)).status()).toBe(401);
  expect(
    (
      await page.request.post(`${base}/api/auth/login`, {
        headers: { origin: "https://evil.test" },
        data: {},
      })
    ).status(),
  ).toBe(403);
  await page.getByLabel("Uporabniško ime", { exact: true }).fill("owner");
  await page.getByLabel("Geslo", { exact: true }).fill("synthetic owner browser test password");
  await page.getByRole("button", { name: "Prijavi se", exact: true }).click();
  await expect(page).toHaveURL(`${base}/`);
  await expect(page.getByRole("button", { name: "Odjava", exact: true })).toBeVisible();
  expect((await page.request.get(`${base}/api/portfolio`)).status()).toBe(200);
  // Keep a genuine private history entry to exercise Back after the hard logout redirect.
  await page.goto(`${base}/portfolio`);
  await page.goto(`${base}/settings`);
  const second = await context.newPage();
  await second.goto(`${base}/portfolio`);
  await expect(second.getByRole("heading", { name: "Portfelj", exact: true })).toBeVisible();
  await second.getByRole("button", { name: "Odjava", exact: true }).click();
  await expect(second).toHaveURL(`${base}/login`);
  await expect(page).toHaveURL(`${base}/login`);
  expect((await page.request.get(`${base}/api/portfolio`)).status()).toBe(401);
  await page.goBack();
  await expect(page).toHaveURL(`${base}/login`);
});
