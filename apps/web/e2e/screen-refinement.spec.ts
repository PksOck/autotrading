import { expect, test } from "@playwright/test";

for (const locale of ["sl", "en"] as const) {
  test(`read-only filters, reserve, calendar and thesis states (${locale})`, async ({
    page,
    context,
    request,
  }, info) => {
    test.setTimeout(90_000);
    await context.addCookies([
      { name: "locale", value: locale, url: String(info.project.use.baseURL) },
    ]);
    const writes: string[] = [];
    await context.route("**/api/**", async (route) => {
      if (route.request().method() !== "GET") {
        writes.push(route.request().url());
        return route.abort();
      }
      return route.continue();
    });
    await page.goto("/proposals?keep=one");
    const filter = page.getByLabel(locale === "sl" ? "Stanje predloga" : "Proposal status", {
      exact: true,
    });
    await filter.selectOption("done");
    await expect(page).toHaveURL(/keep=one&status=done/);
    const search = page.getByLabel(
      locale === "sl" ? "Simbol ali hipoteza" : "Symbol or hypothesis",
      { exact: true },
    );
    await search.fill("unmatched-refinement-check");
    await search.press("Enter");
    await expect(page).toHaveURL(/q=unmatched-refinement-check/);
    await expect(
      page.getByText(
        locale === "sl" ? "Ni predlogov za izbrani filter." : "No proposals match these filters.",
      ),
    ).toBeVisible();

    await page.goto("/portfolio?tab=watchlist");
    const reserve = page.locator("details").filter({
      has: page.locator("summary", { hasText: locale === "sl" ? "Zaloga idej" : "Idea reserve" }),
    });
    await expect(reserve).toHaveCount(1);
    await expect(reserve).not.toHaveAttribute("open");
    await reserve.locator(":scope > summary").press("Enter");
    await expect(reserve).toHaveAttribute("open", "");
    await expect(reserve.getByRole("table")).toBeVisible();

    await page.goto("/portfolio?tab=dividends");
    const calendar = page.getByRole("region", {
      name: locale === "sl" ? "Dividendni koledar" : "Dividend calendar",
      exact: true,
    });
    await expect(calendar).toBeVisible();
    const months = calendar.getByRole("button", { pressed: false });
    await expect(months).toHaveCount(12);
    await expect(months.first()).toHaveAccessibleDescription(/.+/);
    await months.first().click();
    await expect(calendar.getByRole("button", { pressed: true })).toHaveCount(1);
    if (process.env.SHOTS_DIR)
      await calendar.screenshot({
        path: `${process.env.SHOTS_DIR}/${info.project.name}-calendar-${locale}.png`,
      });

    const theses = await (await request.get("/api/theses")).json();
    expect(theses.length).toBeGreaterThan(0);
    const active = theses.find(
      (row: { active_revision_version?: number | null }) => row.active_revision_version != null,
    );
    expect(active).toBeTruthy();
    await page.goto(`/theses/${active.id}`);
    const states = page.locator(
      `dl[aria-label="${locale === "sl" ? "Stanja aktivne teze" : "Active thesis states"}"]`,
    );
    await expect(states.locator("dt")).toHaveCount(5);
    await expect(states.locator("dd")).toHaveCount(5);
    expect(writes).toEqual([]);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth),
    ).toBeLessThanOrEqual(1);
  });
}

test("overview snapshot date and link share a compact desktop footer", async ({ page }, info) => {
  await page.goto("/");
  const card = page
    .locator("section")
    .filter({ has: page.getByRole("heading", { name: "Vrednost portfelja", exact: true }) });
  await expect(card.locator("time")).toBeVisible();
  await expect(card.getByText("Pozicije po valuti · ocena")).toBeVisible();
  if (info.project.name === "desktop") {
    const date = (await card.locator("footer time").boundingBox())!;
    const link = (await card.locator("footer a").boundingBox())!;
    expect(link.x).toBeGreaterThan(date.x + date.width);
    expect(Math.abs(link.y - date.y)).toBeLessThanOrEqual(2);
  }
  if (process.env.SHOTS_DIR)
    await page.screenshot({ path: `${process.env.SHOTS_DIR}/${info.project.name}-overview.png` });
});

test("overview count cards keep separate lines and treemap tiles stay inside their card", async ({
  page,
}) => {
  await page.goto("/", { waitUntil: "networkidle" });
  const count = page
    .locator("a.card")
    .filter({ has: page.getByRole("heading", { name: "Novo", exact: true }) });
  const label = (await count.locator("h2").boundingBox())!;
  const value = (await count.locator("p.num").boundingBox())!;
  expect(value.y).toBeGreaterThanOrEqual(label.y + label.height);
  const card = page
    .locator("section")
    .filter({ has: page.getByRole("heading", { name: /^Portfelj danes/ }) });
  const tile = card.getByRole("button", { name: /^VWRA,/ });
  await expect(tile).toBeVisible();
  await expect
    .poll(async () => {
      const outer = (await card.boundingBox())!;
      const inner = (await tile.boundingBox())!;
      return inner.y + inner.height - outer.y - outer.height;
    })
    .toBeLessThanOrEqual(0);
});
