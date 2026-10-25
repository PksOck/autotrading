import { expect, test } from "@playwright/test";
import { analysis, asOf, claim, revision, summary, thesis } from "../test/thesis-fixtures";
import type { ThesisClaimStatusChange, ThesisOut, ThesisRevisionPatch } from "../lib/api/types";

/** Shell queries (status, portfolio, watchlist) get empty but well-shaped answers. */
function shellResponse(url: string) {
  const path = new URL(url).pathname;
  if (path === "/api/watchlist") return [];
  if (path === "/api/portfolio")
    return {
      as_of: asOf,
      base_currency: "EUR",
      total_value: null,
      positions: [],
      cash: [],
      last_sync: null,
    };
  return { services: [], as_of: asOf };
}

test("theses: list, explicit draft save and confirm, claim evidence and history without a backend", async ({
  page,
  baseURL,
}) => {
  let detail: ThesisOut = {
    ...thesis,
    revisions: [{ ...revision, status: "draft", confirmed_at: null }],
  };
  let statusBody: ThesisClaimStatusChange | undefined;
  await page.route("**/api/**", (route) =>
    route.fulfill({ json: shellResponse(route.request().url()) }),
  );
  await page.context().addCookies([{ name: "locale", value: "en", url: baseURL! }]);
  await page.route("**/api/theses**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() === "PATCH") {
      const body = request.postDataJSON() as ThesisRevisionPatch;
      expect(body.expected_version).toBe(1);
      detail = {
        ...detail,
        revisions: [
          {
            ...detail.revisions[0]!,
            claims: [
              {
                ...claim,
                statement: body.claims[0]!.statement!,
                invalidated_if: body.claims[0]!.invalidated_if ?? null,
              },
            ],
          },
        ],
      };
      await route.fulfill({ json: detail.revisions[0] });
    } else if (path.endsWith("/confirm")) {
      detail = {
        ...detail,
        revisions: [{ ...detail.revisions[0]!, status: "active", confirmed_at: asOf }],
      };
      await route.fulfill({ json: detail.revisions[0] });
    } else if (path.endsWith("/status")) {
      statusBody = request.postDataJSON() as ThesisClaimStatusChange;
      const updated = {
        ...detail.revisions[0]!.claims![0]!,
        status: statusBody.to_status,
        events: [
          {
            id: "event",
            claim_id: claim.id,
            from_status: claim.status,
            to_status: statusBody.to_status,
            actor: "user" as const,
            rationale: statusBody.rationale,
            evidence: statusBody.evidence ?? [],
            source: "manual",
            as_of: asOf,
            created_at: asOf,
          },
        ],
      };
      detail = { ...detail, revisions: [{ ...detail.revisions[0]!, claims: [updated] }] };
      await route.fulfill({ json: updated });
    } else if (path === "/api/theses") {
      await route.fulfill({
        json: [{ ...summary, active_revision_version: null, latest_draft_id: revision.id }],
      });
    } else {
      await route.fulfill({ json: detail });
    }
  });
  await page.goto("/theses");
  await page.getByRole("link", { name: /MSFT Microsoft/ }).click();
  await expect(page).toHaveURL(new RegExp(`/theses/${thesis.id}`));
  await page
    .getByRole("textbox", { name: "Statement", exact: true })
    .fill("Revenue remains stable");
  await expect(page.getByRole("button", { name: "Confirm revision", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByRole("button", { name: "Confirm revision", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Confirm revision", exact: true }).click();
  await expect(page.getByText("Revenue remains stable", { exact: true })).toBeVisible();
  await page.getByText("Change claim status", { exact: true }).click();
  await page.getByRole("combobox", { name: "New status", exact: true }).selectOption("weakening");
  await page.getByLabel("Rationale", { exact: true }).fill("Await official confirmation");
  await page.getByRole("button", { name: "Add evidence", exact: true }).click();
  await page.getByLabel("Source", { exact: true }).fill("Forum");
  await page.getByLabel("As of, your local time", { exact: true }).fill("2026-10-25T12:00");
  await page.getByLabel("Reference", { exact: true }).fill("post:1");
  await page.getByLabel("Rumour, unconfirmed", { exact: true }).check();
  await page.getByRole("button", { name: "Save status", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Saved." })).toBeVisible();
  expect(statusBody?.expected_status).toBe("open");
  expect(statusBody?.evidence?.[0]?.is_rumor).toBe(true);
  await page.getByText("Event history, 1 event", { exact: true }).click();
  await expect(page.getByText("post:1", { exact: true })).toBeVisible();
  await expect(page.getByText("Rumour, unconfirmed", { exact: true })).toBeVisible();
});

test("analysis: draft creation is an explicit action and also accepts an existing draft", async ({
  page,
  baseURL,
}) => {
  let creations = 0;
  await page.context().addCookies([{ name: "locale", value: "en", url: baseURL! }]);
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/theses/drafts") {
      creations += 1;
      expect(route.request().postDataJSON()).toEqual({ analysis_run_id: analysis.id });
      await route.fulfill({ status: 200, json: { ...revision, status: "draft" } });
    } else if (path.startsWith("/api/analyses/")) await route.fulfill({ json: analysis });
    else if (path.startsWith("/api/theses/"))
      await route.fulfill({ json: { ...thesis, revisions: [{ ...revision, status: "draft" }] } });
    else await route.fulfill({ json: shellResponse(route.request().url()) });
  });
  await page.goto(`/analysis/${analysis.id}`);
  await expect(
    page.getByRole("button", { name: "Create thesis draft", exact: true }),
  ).toBeVisible();
  expect(creations).toBe(0);
  await page.getByRole("button", { name: "Create thesis draft", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/theses/${thesis.id}`));
  await expect(page.getByRole("textbox", { name: "Statement", exact: true })).toBeVisible();
  expect(creations).toBe(1);
});
