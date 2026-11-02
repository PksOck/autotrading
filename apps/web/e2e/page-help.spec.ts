import { expect, test } from "@playwright/test";

for (const locale of ["sl", "en"] as const) {
  test(`page help covers every screen, restores filters and focus (${locale})`, async ({
    page,
    context,
    request,
  }, info) => {
    test.setTimeout(120_000);
    await context.addCookies([
      { name: "locale", value: locale, url: String(info.project.use.baseURL) },
    ]);
    const writes: string[] = [];
    await context.route("**/api/**", async (route) => {
      // Session validation uses the isolated demo API, independently of business fixtures.
      if (new URL(route.request().url()).pathname === "/api/auth/session") return route.continue();
      if (route.request().method() !== "GET") {
        writes.push(route.request().url());
        return route.abort();
      }
      return route.continue();
    });
    const analyses = await (await request.get("/api/analyses")).json();
    const theses = await (await request.get("/api/theses")).json();
    expect(analyses.length).toBeGreaterThan(0);
    expect(theses.length).toBeGreaterThan(0);
    const routes = [
      "/",
      "/radar?view=watchlist",
      "/entries",
      "/signals?status=watching",
      "/proposals",
      "/analysis",
      `/analysis/${analyses[0].id}`,
      "/portfolio?tab=watchlist",
      "/i/ASML",
      "/theses",
      `/theses/${theses[0].id}`,
      "/track-record?horizon=5&filter=keep",
      "/settings",
      "/options",
      "/ux",
    ];
    const helpName = locale === "sl" ? /^Pomoč za / : /^Help for /;
    const closeName = locale === "sl" ? "Zapri pomoč" : "Close help";
    for (const path of routes) {
      await test.step(path, async () => {
        await page.goto(path);
        const trigger = page.getByRole("button", { name: helpName });
        await expect(trigger).toHaveCount(1);
        await expect(trigger).toBeVisible();
        const original = page.url();
        await trigger.click();
        const dialog = page.getByRole("dialog");
        await expect(dialog).toBeVisible();
        for (const name of locale === "sl"
          ? ["Kaj lahko naredim?", "Od kod so podatki?", "Kaj je treba upoštevati?"]
          : ["What can I do?", "Where do the data come from?", "What should I know?"]) {
          await expect(dialog.getByRole("heading", { name, exact: true })).toBeVisible();
        }
        await expect(dialog.getByRole("button", { name: closeName })).toBeFocused();
        await page.keyboard.press("Escape");
        await expect(dialog).toHaveCount(0);
        await expect(trigger).toBeFocused();
        expect(page.url()).toBe(original);
      });
    }
    await page.goto("/portfolio?tab=watchlist");
    const trigger = page.getByRole("button", { name: helpName });
    await trigger.click();
    await page.goBack();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(trigger).toBeFocused();
    await expect(page).toHaveURL(/portfolio\?tab=watchlist$/);
    expect(writes).toEqual([]);
  });
}

test("overview keeps warnings and contextual details at desktop 200% reflow and narrow phone width", async ({
  page,
}, info) => {
  await page.goto("/");
  const market = page.getByRole("region", { name: /Tržni dan/ });
  await expect(market.getByText("Ni preverjenih tržnih kazalnikov")).toBeVisible();
  await expect(market.getByRole("heading", { name: "VIX", exact: true })).toHaveCount(0);
  await market.getByLabel("Podatki in razlaga", { exact: true }).click();
  await expect(market.getByText("VIX", { exact: true })).toBeVisible();
  await expect(market.locator("time").first()).toHaveAttribute("datetime", /.+/);
  if (info.project.name === "phone") {
    await page.getByRole("button", { name: "Več", exact: true }).click();
    await expect(page.getByRole("dialog").getByLabel("Danes", { exact: true })).toBeVisible();
    await page.keyboard.press("Escape");
  } else {
    await expect(page.getByLabel("Danes", { exact: true })).toBeVisible();
  }
  // Desktop: halve CSS pixels for 200% zoom-equivalent reflow. Phone: supported 320px layout.
  // Document CSS zoom and a sub-320 mobile viewport do not reproduce browser text zoom.
  const viewport = page.viewportSize()!;
  await page.setViewportSize({
    width: Math.max(320, Math.floor(viewport.width / 2)),
    height: Math.floor(viewport.height / 2),
  });
  await page.getByRole("button", { name: "Pomoč za Pregled", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  const size = await dialog.boundingBox();
  expect(size).not.toBeNull();
  expect(size!.x).toBeGreaterThanOrEqual(0);
  expect(size!.x + size!.width).toBeLessThanOrEqual(page.viewportSize()!.width + 1);
  await expect(dialog.getByRole("button", { name: "Zapri pomoč" })).toBeVisible();
});

test("help inside an instrument preview closes before the preview and preserves its URL", async ({
  page,
}) => {
  await page.goto("/portfolio?tab=watchlist&peek=instrument%3AASML&keep=one");
  const preview = page.getByRole("dialog");
  const trigger = preview.getByRole("button", { name: "Pomoč za ASML", exact: true });
  await trigger.click();
  const help = page.getByRole("dialog", { name: "O strani: ASML" });
  await expect(help).toBeVisible();
  await page.goBack();
  await expect(help).toHaveCount(0);
  await expect(page.getByRole("dialog")).toHaveCount(1);
  await expect(trigger).toBeFocused();
  await expect(page).toHaveURL(/tab=watchlist&peek=instrument%3AASML&keep=one$/);
  await trigger.click();
  await expect(help.getByRole("button", { name: "Zapri pomoč" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(help).toHaveCount(0);
  await expect(page.getByRole("dialog")).toHaveCount(1);
  await expect(trigger).toBeFocused();
});

test("opening help preserves an unsubmitted proposal without a write", async ({
  page,
  context,
}) => {
  const writes: string[] = [];
  await context.route("**/api/**", async (route) => {
    // Session validation uses the isolated demo API, independently of business fixtures.
    if (new URL(route.request().url()).pathname === "/api/auth/session") return route.continue();
    if (route.request().method() !== "GET") {
      writes.push(route.request().url());
      return route.abort();
    }
    return route.continue();
  });
  await page.goto("/proposals");
  const propose = page.getByRole("button", { name: "Predlog", exact: true });
  await propose.click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("textbox").first().fill("ASML");
  await dialog.locator("textarea").first().fill("My saved draft remains unchanged");
  await dialog.getByRole("button", { name: "Prekliči", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await page.getByRole("button", { name: "Pomoč za Predlogi", exact: true }).click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await propose.click();
  await expect(dialog.getByRole("textbox").first()).toHaveValue("ASML");
  await expect(dialog.locator("textarea").first()).toHaveValue("My saved draft remains unchanged");
  expect(writes).toEqual([]);
});
