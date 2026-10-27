/**
 * Same-origin proxy to the FastAPI service, so the browser never needs the API host (ADR-0001).
 * Only known resource prefixes are forwarded.
 */
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const ALLOWED = new Set(["system", "instruments", "portfolio", "watchlist", "radar", "signals", "proposals", "entries", "analyses", "theses", "track-record"]);

async function forward(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  if (!path.length || !ALLOWED.has(path[0]!)) return Response.json({ detail: "not_found" }, { status: 404 });

  const base = process.env.API_URL ?? "http://localhost:8000";
  const url = `${base}/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;
  const hasBody = !["GET", "HEAD"].includes(request.method);
  const wantsStream = request.headers.get("accept")?.includes("text/event-stream") ?? false;
  const headers: Record<string, string> = {};
  if (hasBody) headers["content-type"] = "application/json";
  const lastEventId = request.headers.get("last-event-id");
  if (lastEventId) headers["last-event-id"] = lastEventId;
  try {
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: hasBody ? await request.text() : undefined,
      cache: "no-store",
      // SSE lives as long as the run does: no timeout, but stop when the browser disconnects.
      signal: wantsStream
        ? request.signal
        : AbortSignal.any([request.signal, AbortSignal.timeout(30_000)]),
    });
    const contentType = response.headers.get("content-type") ?? "application/json";
    if (response.status === 204) return new Response(null, { status: 204 });
    if (contentType.includes("text/event-stream") && response.body) {
      return new Response(response.body, {
        status: response.status,
        headers: {
          "content-type": contentType,
          "cache-control": "no-cache, no-transform",
          "x-accel-buffering": "no",
        },
      });
    }
    return new Response(await response.text(), {
      status: response.status,
      headers: { "content-type": contentType },
    });
  } catch {
    return Response.json({ detail: "api_unreachable" }, { status: 503 });
  }
}

export { forward as GET, forward as POST, forward as PATCH, forward as DELETE };
