import { expect, test } from "@playwright/test";
import { signal, signalId } from "../test/signal-fixtures";

const studyUrl =
  "/track-record?horizon=5&from=2026-09-01&to=2026-10-01&filter=keep&tag=one&tag=two";
const submitted = {
  source: "all",
  available_from: "2026-09-01",
  available_to: "2026-10-01",
  horizon_sessions: 20,
  cost_bps: "17.5",
  min_strength: "0.35",
  signal_status: "watching",
  limit: 75,
};
const savedAnalysis = {
  id: signalId,
  symbol: "MSFT",
  name: "Controlled saved opinion",
  engine: "stock",
  trade_date: "2026-10-01",
  status: "done",
  rating: "Hold",
  caveats: [],
  created_at: "2026-10-01T10:00:00Z",
  started_at: "2026-10-01T10:00:00Z",
  finished_at: "2026-10-01T12:00:00Z",
  locale: "en",
  hypothesis: null,
  decision: "Stored fixture opinion",
  reports: {},
  models: {},
  error: null,
  data_sources: {},
  card: null,
  outlook: null,
  steps: [],
};
const rows = (["signal", "analysis"] as const).map((source) => ({
  id: signalId,
  source,
  symbol: "MSFT",
  origin: "fixture",
  direction: "up",
  available_at: "2026-10-01T12:00:00Z",
  record_status: source === "signal" ? "watching" : "done",
  currency: "USD",
  entry_price: "100",
  exit_price: "110",
  entry_date: "2026-10-02",
  exit_date: "2026-10-29",
  entry_source: "fixture",
  exit_source: "fixture",
  gross_return_pct: "10",
  net_return_pct: "9.6325",
  skip_reason: null,
}));

const copy = {
  en: {
    title: "Test saved signals and opinions",
    calculate: "Calculate from stored records",
    close: "Close preview",
    newTab: "Opens in a new tab",
  },
  sl: {
    title: "Testiranje shranjenih signalov in mnenj",
    calculate: "Izračunaj iz shranjenih zapisov",
    close: "Zapri predogled",
    newTab: "Odpre se v novem zavihku",
  },
};

for (const locale of ["sl", "en"] as const) {
  test(`backtest preserves study through Close, Escape, Back and opens the exact saved analysis (${locale})`, async ({
    page,
    context,
  }, info) => {
    test.setTimeout(60_000);
    const posts: unknown[] = [];
    const otherMutations: string[] = [];
    const analysisReads: string[] = [];
    const text = copy[locale];
    await context.addCookies([
      { name: "locale", value: locale, url: String(info.project.use.baseURL) },
    ]);
    // Context routes cover popups as well: no real analysis, provider, SMTP or write endpoint is called.
    await context.route("**/api/**", async (route) => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      if (path === "/api/backtest" && request.method() === "POST") {
        const parameters = request.postDataJSON();
        posts.push(parameters);
        return route.fulfill({
          json: {
            as_of: "2026-10-29T12:00:00Z",
            source: "fixture",
            parameters,
            total_matching: 2,
            evaluated: 2,
            completed: 2,
            skipped: 0,
            truncated: false,
            mean_gross_return_pct: "10",
            mean_net_return_pct: "9.6325",
            positive_share: "1",
            rows,
          },
        });
      }
      if (request.method() !== "GET") otherMutations.push(`${request.method()} ${path}`);
      if (path === `/api/signals/${signalId}`) return route.fulfill({ json: signal });
      if (path === `/api/analyses/${signalId}`) {
        analysisReads.push(path);
        return route.fulfill({ json: savedAnalysis });
      }
      if (path === "/api/portfolio") return route.fulfill({ json: { positions: [] } });
      if (path === "/api/signals") return route.fulfill({ json: [] });
      return route.fulfill({ status: 503, json: { detail: "controlled_fixture_unavailable" } });
    });
    // The page is server rendered; its first query proves the client tree has mounted.
    const clientReady = page.waitForResponse(
      (response) => new URL(response.url()).pathname === "/api/track-record",
    );
    await page.goto(studyUrl);
    await clientReady;
    const panel = page
      .locator("section")
      .filter({ has: page.getByRole("heading", { name: text.title, exact: true }) });
    await expect(panel).toBeVisible();
    const form = panel.locator("form");
    const selects = form.locator("select");
    const dates = form.locator('input[type="date"]');
    const numbers = form.locator('input[type="number"]');
    await dates.nth(0).fill(submitted.available_from);
    await expect(dates.nth(1)).toHaveAttribute("min", submitted.available_from);
    await dates.nth(1).fill(submitted.available_to);
    await numbers.nth(0).fill(submitted.cost_bps);
    await numbers.nth(1).fill(submitted.min_strength);
    await selects.nth(2).selectOption(submitted.signal_status);
    await numbers.nth(2).fill(String(submitted.limit));
    await panel.getByRole("button", { name: text.calculate, exact: true }).click();
    const results = panel.locator('[aria-live="polite"]');
    await expect(results.locator("tbody tr")).toHaveCount(2);
    expect(posts).toEqual([submitted]);
    const resultText = await results.innerText();
    const signalLink = results.getByRole("link", { name: "MSFT", exact: true });
    const analysisLink = results.getByRole("link", {
      name: new RegExp(`MSFT\\s*\\(${text.newTab}\\)`),
    });
    const signalUrl = new URL(studyUrl, page.url());
    signalUrl.searchParams.set("peek", `signal:${signalId}`);
    await expect(signalLink).toHaveAttribute("href", `${signalUrl.pathname}${signalUrl.search}`);
    await expect(analysisLink).toHaveAttribute("href", `/analysis/${signalId}`);
    await expect(analysisLink).toHaveAttribute("target", "_blank");
    await expect(analysisLink).toHaveAttribute("rel", "noopener noreferrer");

    // Editing the draft never changes the displayed submitted parameters or any result row.
    await selects.nth(0).selectOption("analysis");
    await selects.nth(1).selectOption("60");
    await dates.nth(0).fill("2026-09-02");
    await dates.nth(1).fill("2026-10-02");
    await numbers.nth(0).fill("55.7");
    await numbers.nth(2).fill("123");
    const unchanged = async () => {
      expect(await results.innerText()).toBe(resultText);
      await expect(selects.nth(0)).toHaveValue("analysis");
      await expect(selects.nth(1)).toHaveValue("60");
      await expect(dates.nth(0)).toHaveValue("2026-09-02");
      await expect(dates.nth(1)).toHaveValue("2026-10-02");
      await expect(numbers.nth(0)).toHaveValue("55.7");
      await expect(numbers.nth(1)).toHaveValue("0.35");
      await expect(numbers.nth(2)).toHaveValue("123");
      await expect(selects.nth(2)).toHaveValue("watching");
      expect(posts).toEqual([submitted]);
      expect(otherMutations).toEqual([]);
    };
    for (const action of ["close", "escape", "back"]) {
      await signalLink.focus();
      await signalLink.press("Enter");
      await expect(page).toHaveURL(signalUrl.href);
      const dialog = page.getByRole("dialog");
      await expect(dialog.getByRole("heading", { name: "MSFT", exact: true })).toBeVisible();
      await expect(dialog).toContainText(signal.rationale);
      if (action === "close") await dialog.getByRole("button", { name: text.close }).click();
      else if (action === "escape") await page.keyboard.press("Escape");
      else await page.goBack();
      await expect(dialog).toHaveCount(0);
      await expect(page).toHaveURL(new URL(studyUrl, page.url()).href);
      await expect(signalLink).toBeFocused();
      await unchanged();
    }

    // Modified signal clicks use the anchor's native new-tab URL without disturbing the study.
    const signalPopupPromise = context.waitForEvent("page");
    await signalLink.click({ modifiers: ["ControlOrMeta"] });
    const signalPopup = await signalPopupPromise;
    await expect(signalPopup).toHaveURL(signalUrl.href);
    await expect(
      signalPopup.getByRole("dialog").getByRole("heading", { name: "MSFT" }),
    ).toBeVisible();
    await signalPopup.close();
    await unchanged();

    // Keyboard activation of analysis opens its real existing screen on the exact internal ID.
    const analysisPopupPromise = context.waitForEvent("page");
    await analysisLink.focus();
    await analysisLink.press("Enter");
    const analysisPopup = await analysisPopupPromise;
    await expect(analysisPopup).toHaveURL(new URL(`/analysis/${signalId}`, page.url()).href);
    await expect(analysisPopup.getByText(savedAnalysis.name, { exact: true })).toBeVisible();
    expect(analysisReads).toContain(`/api/analyses/${signalId}`);
    await analysisPopup.close();
    await expect(page).toHaveURL(new URL(studyUrl, page.url()).href);
    await unchanged();
  });
}
