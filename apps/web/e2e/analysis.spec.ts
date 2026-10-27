import { expect, test } from "@playwright/test";

async function runId(request: import("@playwright/test").APIRequestContext, symbol: string) {
  const runs = (await (await request.get("/api/analyses")).json()) as {
    id: string;
    symbol: string;
  }[];
  const run = runs.find((r) => r.symbol === symbol);
  if (!run) throw new Error(`no demo analysis for ${symbol}`);
  return run.id;
}

test("analysis: finished ASML run shows decision header, outlook and folded details", async ({
  page,
  request,
}) => {
  await page.goto(`/analysis/${await runId(request, "ASML")}`);
  await expect(page.getByRole("heading", { level: 1, name: "Analiza" })).toBeVisible();
  await expect(page.getByTestId("action-pill").first()).toHaveText("Povečaj delež");
  await expect(page.getByTestId("header-conviction")).toContainText("6/10");
  await expect(page.getByTestId("header-price")).toBeVisible();
  await expect(page.getByTestId("header-position")).toBeVisible();
  await expect(page.getByText("mnenje agentov")).toBeVisible();

  for (const h of ["short", "medium", "long"])
    await expect(page.getByTestId(`horizon-${h}`)).toBeVisible();
  await expect(page.getByTestId("horizon-medium")).toHaveAttribute("aria-pressed", "true");
  await page.getByTestId("horizon-short").click();
  await expect(page.getByTestId("horizon-short")).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("evidence-split")).toBeVisible();

  const change = page.getByTestId("rating-change");
  await expect(change.getByText("Ocena gre gor, če")).toBeVisible();
  await expect(change.getByText("Ocena gre dol, če")).toBeVisible();

  const decision = page.getByTestId("decision-panel");
  await decision.getByText("Utemeljitev agentov").click();
  await expect(decision.getByText("Povečaj pozicijo postopoma")).toBeVisible();

  await page.getByText("Kontrolna ocena").click();
  const card = page.getByTestId("decision-card");
  await expect(card.getByTestId("conviction")).toHaveText("6/10");
  await expect(card.getByTestId("size-class")).toContainText("2–4 % portfelja");
  await expect(card.getByText("na podlagi 100 % uteži")).toBeVisible();
  await expect(card.getByTestId("low-confidence")).toHaveCount(0);

  await page
    .getByTestId("steps-section")
    .getByText(/Koraki analitikov/)
    .click();
  const timeline = page.getByTestId("agent-timeline");
  await expect(timeline.getByRole("heading", { name: "Debata" })).toBeVisible();
  await timeline.locator('[data-testid="analyst-group"][data-agent="market"] summary').click();
  const expand = timeline.getByRole("button", { name: "Razširi: Tržno poročilo" });
  await expect(expand).toHaveAttribute("aria-expanded", "false");
  await expand.click();
  await expect(timeline.getByRole("button", { name: "Skrči: Tržno poročilo" })).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await expect(timeline.getByText("Volumen pri zadnjih padcih")).toBeVisible();
  await expect(page.getByTestId("phase-live")).toHaveCount(0);
});

test("analysis: running NVDA run shows live state and its 8 steps", async ({ page, request }) => {
  await page.goto(`/analysis/${await runId(request, "NVDA")}`);
  await expect(page.getByTestId("analysis-status")).toHaveAttribute("data-status", "running");
  await expect(page.getByTestId("phase-live")).toBeVisible();
  await expect(page.getByTestId("agent-timeline")).toHaveAttribute("data-step-count", "8");
  await expect(page.getByTestId("decision-panel")).toContainText("Odločitev bo na voljo");
  await expect(page.getByTestId("decision-card")).toHaveCount(0);
});

test("analysis: instrument page lists runs and offers deep analysis", async ({ page }, info) => {
  await page.goto("/i/ASML");
  const latest = page.getByRole("region", { name: "Zadnje globoke analize" });
  await expect(latest.getByRole("link").first()).toBeVisible();
  await expect(latest.getByText("Povečaj")).toBeVisible();
  await page.goto("/analysis");
  await expect(page.getByRole("link", { name: /ASML/ })).toBeVisible();
  await expect(page.getByTestId("analysis-quota")).toHaveText(/Danes \d+ od \d+/);
  if (info.project.name === "phone") return;
  await page.goto("/i/EQQQ");
  await expect(page.getByRole("button", { name: "Globoka analiza" })).toBeEnabled();
});
