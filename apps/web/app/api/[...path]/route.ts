/**
 * Same-origin proxy to the FastAPI service, so the browser never needs the API host (ADR-0001).
 * Only known resource prefixes are forwarded.
 */
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const ALLOWED = new Set(["system", "instruments", "portfolio", "watchlist", "radar", "signals", "proposals"]);

async function forward(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  if (!path.length || !ALLOWED.has(path[0]!)) return Response.json({ detail: "not_found" }, { status: 404 });

  const base = process.env.API_URL ?? "http://localhost:8000";
  const url = `${base}/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;
  const hasBody = !["GET", "HEAD"].includes(request.method);
  try {
    const response = await fetch(url, {
      method: request.method,
      headers: hasBody ? { "content-type": "application/json" } : undefined,
      body: hasBody ? await request.text() : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    if (response.status === 204) return new Response(null, { status: 204 });
    return new Response(await response.text(), {
      status: response.status,
      headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
    });
  } catch {
    return Response.json({ detail: "api_unreachable" }, { status: 503 });
  }
}

export { forward as GET, forward as POST, forward as PATCH, forward as DELETE };
