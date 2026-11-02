import { NextRequest } from "next/server";
import { vi } from "vitest";
import { GET, POST } from "./[...path]/route";

afterEach(() => vi.unstubAllGlobals());

async function forwardedType(contentType: string) {
  const fetch = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
  vi.stubGlobal("fetch", fetch);
  const request = new NextRequest("http://localhost/api/portfolio/import", {
    method: "POST",
    headers: { "content-type": contentType, origin: "http://localhost" },
    body: "<FlexQueryResponse/>",
  });
  await POST(request, { params: Promise.resolve({ path: ["portfolio", "import"] }) });
  return fetch.mock.calls[0]![1].headers["content-type"];
}

it("forwards XML content types for the Flex import", async () => {
  expect(await forwardedType("application/xml")).toBe("application/xml");
  expect(await forwardedType("Text/XML; charset=utf-8")).toBe("text/xml");
});

it("sends every other body as JSON", async () => {
  expect(await forwardedType("text/html")).toBe("application/json");
  expect(await forwardedType("application/xml-evil")).toBe("application/json");
});

it("rejects unsafe origins before contacting the API", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  for (const origin of [undefined, "null", "https://evil.test", "http://localhost.evil.test"]) {
    const response = await POST(
      new NextRequest("http://localhost/api/watchlist", {
        method: "POST",
        body: "{}",
        headers: origin ? { origin } : {},
      }),
      { params: Promise.resolve({ path: ["watchlist"] }) },
    );
    expect(response.status).toBe(403);
  }
  expect(fetch).not.toHaveBeenCalled();
});

it("caps declared and streamed request bodies before forwarding", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const cases: Record<string, string>[] = [
    { "content-length": "1048577", origin: "http://localhost" },
    { origin: "http://localhost" },
  ];
  for (const headers of cases) {
    const response = await POST(
      new NextRequest("http://localhost/api/proposals", {
        method: "POST",
        body: "x".repeat(1048577),
        headers,
      }),
      { params: Promise.resolve({ path: ["proposals"] }) },
    );
    expect(response.status).toBe(413);
  }
  expect(fetch).not.toHaveBeenCalled();
});

it("rejects path normalization bypasses and never follows upstream redirects", async () => {
  const fetch = vi.fn().mockResolvedValue(new Response("{}"));
  vi.stubGlobal("fetch", fetch);
  for (const part of ["..", ".", "../auth", "x\\y", "%2e%2e", "x/y"]) {
    const response = await GET(new NextRequest("http://localhost/api/portfolio"), {
      params: Promise.resolve({ path: ["portfolio", part] }),
    });
    expect(response.status).toBe(404);
  }
  expect(fetch).not.toHaveBeenCalled();
  await GET(
    new NextRequest("http://localhost/api/portfolio", {
      headers: { cookie: "preza_session=synthetic", "x-auth-bypass": "true" },
    }),
    { params: Promise.resolve({ path: ["portfolio"] }) },
  );
  expect(fetch.mock.calls[0]![1]).toMatchObject({
    redirect: "error",
    headers: { cookie: "preza_session=synthetic" },
  });
  expect(fetch.mock.calls[0]![1].headers["x-auth-bypass"]).toBeUndefined();
});

it("forwards auth cookies on login and logout responses", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(null, {
        status: 204,
        headers: { "set-cookie": "preza_session=; Max-Age=0; HttpOnly; SameSite=Strict" },
      }),
    ),
  );
  const response = await POST(
    new NextRequest("http://localhost/api/auth/logout", {
      method: "POST",
      headers: { origin: "http://localhost" },
    }),
    { params: Promise.resolve({ path: ["auth", "logout"] }) },
  );
  expect(response.status).toBe(204);
  expect(response.headers.get("set-cookie")).toContain("Max-Age=0");
  expect(response.headers.get("cache-control")).toBe("no-store");
});
