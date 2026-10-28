import { NextRequest } from "next/server";
import { vi } from "vitest";
import { POST } from "./[...path]/route";

afterEach(() => vi.unstubAllGlobals());

async function forwardedType(contentType: string) {
  const fetch = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
  vi.stubGlobal("fetch", fetch);
  const request = new NextRequest("http://localhost/api/portfolio/import", {
    method: "POST",
    headers: { "content-type": contentType },
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
