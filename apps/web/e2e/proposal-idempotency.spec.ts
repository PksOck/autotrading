import { expect, test, type BrowserContext, type Page } from "@playwright/test";
import en from "../messages/en.json" with { type: "json" };
import sl from "../messages/sl.json" with { type: "json" };

const key = "preza.proposal.draft.v2";
type Body = Record<string, unknown> & { request_id: string };

async function controlledApi(context: BrowserContext, acceptLostResponse: boolean) {
  const posts: Body[] = [];
  const reads: string[] = [];
  const records = new Map<string, Body>();
  const unexpectedMutations: string[] = [];
  await context.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/proposals" && request.method() === "POST") {
      const body = request.postDataJSON() as Body;
      posts.push(body);
      if (posts.length === 1) {
        if (acceptLostResponse) records.set(body.request_id, body);
        return route.abort("failed");
      }
      records.set(body.request_id, body);
      return route.fulfill({
        status: 202,
        json: { ...body, id: body.request_id, status: "queued" },
      });
    }
    if (request.method() !== "GET") unexpectedMutations.push(`${request.method()} ${path}`);
    if (path.startsWith("/api/proposals/")) {
      const id = path.split("/").at(-1)!;
      reads.push(id);
      const found = records.get(id);
      return found
        ? route.fulfill({ json: { ...found, id, status: "queued" } })
        : route.fulfill({ status: 404, json: { detail: "proposal_not_found" } });
    }
    if (path === "/api/proposals") return route.fulfill({ json: [] });
    return route.fulfill({ status: 503, json: { detail: "controlled_fixture_unavailable" } });
  });
  return { posts, reads, records, unexpectedMutations };
}

async function visit(page: Page) {
  const ready = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/proposals",
  );
  await page.goto("/proposals");
  await ready;
}

async function open(page: Page, label: string) {
  await page.locator("header").getByRole("button", { name: label, exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
}

for (const locale of ["sl", "en"] as const) {
  const copy = locale === "sl" ? sl : en;
  for (const accepted of [true, false]) {
    test(`saved proposal survives reload after ${accepted ? "accepted" : "unaccepted"} lost response (${locale})`, async ({
      page,
      context,
    }, info) => {
      await context.addCookies([
        { name: "locale", value: locale, url: String(info.project.use.baseURL) },
      ]);
      const fake = await controlledApi(context, accepted);
      await visit(page);
      await open(page, copy.header.propose);
      await page.getByLabel(copy.proposal.symbols, { exact: true }).fill("msft, AMD msft");
      await page.getByLabel(copy.proposal.hypothesis, { exact: true }).fill("Original idea");
      await page.getByRole("button", { name: copy.proposal.submit, exact: true }).click();
      await expect(page.getByRole("status")).toContainText(copy.proposal.durable.unknown);
      expect(fake.posts).toHaveLength(1);
      const original = fake.posts[0]!;
      expect(original.symbols).toEqual(["AMD", "MSFT"]);
      await page.reload();
      await open(page, copy.header.propose);
      await page.getByLabel(copy.proposal.hypothesis, { exact: true }).fill("Edited after reload");
      await page.goBack();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(
        page.locator("header").getByRole("button", { name: copy.header.propose, exact: true }),
      ).toBeFocused();
      await open(page, copy.header.propose);
      await expect(page.getByLabel(copy.proposal.hypothesis, { exact: true })).toHaveValue(
        "Edited after reload",
      );
      expect(fake.posts).toHaveLength(1);
      const check = page.getByRole("button", { name: copy.proposal.durable.check, exact: true });
      await expect
        .poll(async () => (await check.boundingBox())?.height ?? 0)
        .toBeGreaterThanOrEqual(48);
      await check.click();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      expect(fake.records.size).toBe(1);
      expect(fake.posts).toHaveLength(accepted ? 1 : 2);
      if (!accepted) expect(fake.posts[1]).toEqual(original);
      expect(fake.reads.every((id) => id === original.request_id)).toBe(true);
      expect(fake.unexpectedMutations).toEqual([]);
      const stored = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)!), key);
      expect(stored.operation).toMatchObject({
        state: "acknowledged",
        request_id: original.request_id,
        proposal_id: original.request_id,
      });
      expect(stored.fields.hypothesis).toBe("Edited after reload");
      await open(page, copy.header.propose);
      await expect(
        page.getByRole("button", { name: copy.proposal.durable.newIntention, exact: true }),
      ).toBeVisible();
      await page
        .getByRole("button", { name: copy.proposal.durable.newIntention, exact: true })
        .click();
      await expect(
        page.getByRole("button", { name: copy.proposal.submit, exact: true }),
      ).toBeVisible();
      expect(fake.posts).toHaveLength(accepted ? 1 : 2);
    });
  }
}

test("real IndexedDB serializes tabs without secure-context APIs", async ({
  page,
  context,
}, info) => {
  await context.addCookies([
    { name: "locale", value: "en", url: String(info.project.use.baseURL) },
  ]);
  await context.addInitScript(() => {
    Object.defineProperty(navigator, "locks", { configurable: true, value: undefined });
    Object.defineProperty(crypto, "randomUUID", { configurable: true, value: undefined });
  });
  const fake = await controlledApi(context, true);
  await visit(page);
  await open(page, en.header.propose);
  await page.getByLabel(en.proposal.symbols, { exact: true }).fill("brk.b, AMD");
  await page.getByLabel(en.proposal.hypothesis, { exact: true }).fill("Frozen across tabs");
  await page.getByRole("button", { name: en.proposal.submit, exact: true }).click();
  await expect(page.getByRole("status")).toContainText(en.proposal.durable.unknown);
  const original = fake.posts[0]!;
  expect(original.request_id).toMatch(
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
  );
  const other = await context.newPage();
  await visit(other);
  await open(other, en.header.propose);
  await other.getByLabel(en.proposal.hypothesis, { exact: true }).fill("Other tab edit");
  await expect
    .poll(async () =>
      other.evaluate((key) => JSON.parse(localStorage.getItem(key)!).fields.hypothesis, key),
    )
    .toBe("Other tab edit");
  await Promise.all([
    page.getByRole("button", { name: en.proposal.durable.check, exact: true }).click(),
    other.getByRole("button", { name: en.proposal.durable.check, exact: true }).click(),
  ]);
  await expect
    .poll(async () =>
      page.evaluate((key) => JSON.parse(localStorage.getItem(key)!).operation.state, key),
    )
    .toBe("acknowledged");
  expect(fake.posts).toHaveLength(1);
  expect(fake.records.size).toBe(1);
  expect(fake.reads.every((id) => id === original.request_id)).toBe(true);
  expect(fake.unexpectedMutations).toEqual([]);
  const persisted = await other.evaluate((key) => JSON.parse(localStorage.getItem(key)!), key);
  expect(persisted.operation.canonical_body.hypothesis).toBe("Frozen across tabs");
  expect(persisted.operation.canonical_body.symbols).toEqual(["AMD", "BRK.B"]);
  expect(persisted.fields.hypothesis).toBe("Other tab edit");
});

test("another tab's saved edits survive a single-tab acknowledgement and reload", async ({
  page,
  context,
}, info) => {
  await context.addCookies([
    { name: "locale", value: "en", url: String(info.project.use.baseURL) },
  ]);
  const fake = await controlledApi(context, true);
  await visit(page);
  await open(page, en.header.propose);
  await page.getByLabel(en.proposal.symbols, { exact: true }).fill("AMD");
  await page.getByLabel(en.proposal.hypothesis, { exact: true }).fill("Original idea");
  await page.getByRole("button", { name: en.proposal.submit, exact: true }).click();
  await expect(page.getByRole("status")).toContainText(en.proposal.durable.unknown);
  const other = await context.newPage();
  await visit(other);
  await open(other, en.header.propose);
  await other.getByLabel(en.proposal.symbols, { exact: true }).fill("NVDA");
  await other.getByLabel(en.proposal.hypothesis, { exact: true }).fill("Other tab edit");
  await other.getByLabel(en.proposal.source, { exact: true }).fill("Other source");
  await other
    .getByRole("radiogroup", { name: en.proposal.direction })
    .getByText(en.proposal.down, { exact: true })
    .click();
  await other
    .getByRole("radiogroup", { name: en.proposal.horizon })
    .getByText(en.signal.horizon.years, { exact: true })
    .click();
  await other.getByText(en.proposal.depth.deep, { exact: true }).click();
  await other
    .getByRole("radiogroup", { name: en.proposal.saveTo.label })
    .getByText(en.proposal.saveTo.active, { exact: true })
    .click();
  const edited = {
    symbols: "NVDA",
    hypothesis: "Other tab edit",
    source: "Other source",
    direction: "down",
    horizon: "years",
    depth: "deep",
    saveTo: "active",
  };
  await expect
    .poll(() => other.evaluate((key) => JSON.parse(localStorage.getItem(key)!).fields, key))
    .toEqual(edited);
  // B's complete draft is durable before A alone verifies the old submission.
  await page.getByRole("button", { name: en.proposal.durable.check, exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await open(page, en.header.propose);
  await page.getByRole("button", { name: en.action.cancel, exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await visit(other);
  await open(other, en.header.propose);
  await expect(other.getByLabel(en.proposal.hypothesis, { exact: true })).toHaveValue(
    "Other tab edit",
  );
  expect(await other.evaluate((key) => JSON.parse(localStorage.getItem(key)!).fields, key)).toEqual(
    edited,
  );
  expect(fake.posts).toHaveLength(1);
  expect(fake.records.size).toBe(1);
  expect(fake.unexpectedMutations).toEqual([]);
});
