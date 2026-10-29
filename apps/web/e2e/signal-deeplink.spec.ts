import { expect, test } from "@playwright/test";
import { signal, signalId } from "../test/signal-fixtures";

test.beforeEach(async ({ page }, info) => {
  if (info.project.name === "phone") await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === `/api/signals/${signalId}`) return route.fulfill({ json: signal });
    if (path === "/api/signals") return route.fulfill({ json: [] });
    if (path === "/api/entries")
      return route.fulfill({
        json: [
          {
            symbol: "MSFT",
            name: "Microsoft",
            kind: "stock",
            currency: "USD",
            held: true,
            watched: false,
            as_of: "2026-10-29",
            price: 400,
            state: "in_zone",
            anchor: "sma200",
            rules: [{ rule: "drawdown", values: { drawdown_pct: -10 } }],
            zone_low: 390,
            zone_high: 410,
            stop: 370,
            atr: 5,
            distance_atr: 0,
            drawdown_pct: -10,
            valuation: {},
            ladder: [],
            cause: null,
            thesis_intact: null,
            dip_rationale: null,
            dip_evidence: [],
            dip_model: null,
            analyzed_at: null,
            signal_id: signalId,
            source: "fixture",
            updated_at: signal.created_at,
          },
        ],
      });
    if (path === "/api/instruments/MSFT")
      return route.fulfill({
        json: {
          symbol: "MSFT",
          name: "Microsoft",
          kind: "stock",
          exchange: "NASDAQ",
          currency: "USD",
          isin: null,
          ucits: false,
          tradable_for_user: true,
          last_close: 400,
          change_pct: 1,
          provenance: null,
        },
      });
    return route.fulfill({ status: 503, json: { detail: "fixture_unavailable" } });
  });
});

for (const locale of ["sl", "en"]) {
  test(`direct signal link stays in app on close and Escape (${locale})`, async ({
    page,
  }, info) => {
    const mutations: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("/api/") && request.method() !== "GET")
        mutations.push(request.method());
    });
    await page
      .context()
      .addCookies([{ name: "locale", value: locale, url: String(info.project.use.baseURL) }]);
    await page.goto(`/signals?status=watching&filter=keep&peek=signal:${signalId}`);
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByRole("heading", { name: "MSFT" })).toBeVisible();
    await expect(
      dialog.getByText(locale === "sl" ? "Nepotrjeno" : "Unconfirmed", { exact: true }),
    ).toBeVisible();
    const close = dialog.getByRole("button", {
      name: locale === "sl" ? "Zapri predogled" : "Close preview",
    });
    await expect(close).toBeVisible();
    if (info.project.name === "phone") {
      const box = await close.boundingBox();
      expect(box?.height).toBeGreaterThanOrEqual(48);
      expect(box?.width).toBeGreaterThanOrEqual(48);
    }
    await expect(dialog.getByRole("link", { name: "Original source" })).toHaveAttribute(
      "href",
      "https://example.test/news",
    );
    await close.click();
    await expect(page).toHaveURL(/\/signals\?status=watching&filter=keep$/);
    await expect(dialog).toHaveCount(0);
    await page.goto(`/signals?filter=keep&peek=signal:${signalId}`);
    await expect(dialog).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page).toHaveURL(/\/signals\?filter=keep$/);
    expect(mutations).toEqual([]);
  });
}

test("entry signal link opens detail and browser Back restores the entry URL", async ({ page }) => {
  const entryUrl = "/entries?symbol=MSFT&view=portfolio&filter=all";
  await page.goto(entryUrl);
  const link = page.getByRole("link", { name: "Odpri signal", exact: true });
  await expect(link).toBeVisible();
  await link.click();
  await expect(page.getByRole("dialog").getByRole("heading", { name: "MSFT" })).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(new RegExp(entryUrl.replaceAll("?", "\\?")));
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Odpri signal", exact: true })).toBeVisible();
});

test("instrument preview remains available", async ({ page }) => {
  await page.goto("/signals?peek=instrument:MSFT");
  await expect(page.getByRole("dialog")).toContainText("Microsoft");
});

test("closing a same-page preview restores keyboard focus to its opener", async ({ page }) => {
  await page.goto("/entries?symbol=MSFT");
  const opener = page.getByRole("link", { name: "MSFT", exact: true });
  await expect(opener).toBeVisible();
  for (const action of ["close", "escape", "back"]) {
    await opener.focus();
    await opener.press("Enter");
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    if (action === "close") await dialog.getByRole("button", { name: "Zapri predogled" }).click();
    else if (action === "escape") await page.keyboard.press("Escape");
    else await page.goBack();
    await expect(dialog).toHaveCount(0);
    await expect(opener).toBeFocused();
  }
});
