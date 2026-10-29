import { expect, test } from "@playwright/test";

test("watchlist profiles and density survive reload, warnings remain visible", async ({ page }) => {
  await page.goto("/portfolio?tab=watchlist");
  const active = page.getByRole("region", { name: "Aktivna", exact: true });
  await active.getByRole("button", { name: "Vrednotenje", exact: true }).click();
  await expect(active.getByRole("columnheader", { name: /P\/E TTM/ })).toBeVisible();
  await expect(active.getByRole("columnheader", { name: /Forward P\/E/ })).toBeVisible();
  await active.getByLabel("Gostota", { exact: true }).selectOption("compact");
  await page.reload();
  await expect(active.getByLabel("Gostota", { exact: true })).toHaveValue("compact");
  await expect(active.getByRole("columnheader", { name: /P\/E TTM/ })).toBeVisible();
  await expect(page.getByText("Nepopolna identiteta", { exact: true })).toBeVisible();
});

test("dividends keep cash, accruals and estimates distinct with visible coverage", async ({
  page,
}) => {
  await page.goto("/portfolio?tab=dividends");
  await expect(page.getByRole("heading", { name: "Prejeta gotovina", exact: true })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Odprte obračunane dividende", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: /Ocena naslednjih 12 mesecev/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pokritost uvoza" })).toBeVisible();
  await page.getByLabel("Valuta", { exact: true }).selectOption("USD");
  await expect(page).toHaveURL(/dvCurrency=USD/);
  await expect(page.getByText(/Zasebni razširjeni izpis IBKR še ni preverjen/)).toBeVisible();
});

test("batch preview explains disabled automation without submitting analysis", async ({ page }) => {
  await page.goto("/portfolio?tab=analyses");
  const requests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/batch/run")) requests.push(request.url());
  });
  await page.getByRole("button", { name: "Predogled", exact: true }).click();
  await expect(page.getByRole("link", { name: "MSFT", exact: true })).toHaveAttribute(
    "href",
    "/i/MSFT",
  );
  await expect(page.getByText(/Pred sprejemom omogoči proces/)).toBeVisible();
  expect(requests).toEqual([]);
});

test("settings expose individual processes and portfolio analysis filters restore from URL", async ({
  page,
}) => {
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Nastavitve", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Procesi in urniki", exact: true })).toBeVisible();
  await expect(page.getByLabel("Časovni pas IANA").first()).toHaveValue("UTC");
  await page.goto("/analysis?status=done&latest=true");
  await expect(page.getByRole("checkbox", { name: /Zadnja za vsak instrument/ })).toBeChecked();
  await expect(page.getByRole("combobox", { name: "Vsa stanja" })).toHaveValue("done");
});
