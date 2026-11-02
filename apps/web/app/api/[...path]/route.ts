/**
 * Same-origin proxy to the FastAPI service, so the browser never needs the API host (ADR-0001).
 * Only known resource prefixes are forwarded.
 */
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const ALLOWED = new Set([
  "system",
  "instruments",
  "portfolio",
  "watchlist",
  "radar",
  "signals",
  "proposals",
  "entries",
  "analyses",
  "theses",
  "track-record",
  "calibration",
  "automation",
  "overview",
  "notifications",
  "backtest",
  "auth",
]);

// XML passes through for the Flex statement import; every other body is JSON.
const XML_TYPES = new Set(["application/xml", "text/xml"]);

function forwardedType(contentType: string | null): string {
  const media = (contentType ?? "").split(";")[0]!.trim().toLowerCase();
  return XML_TYPES.has(media) ? media : "application/json";
}

async function forward(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  if (
    !path.length ||
    !ALLOWED.has(path[0]!) ||
    path.some((part) => !part || part === "." || part === ".." || /[\\/%\x00-\x1f]/.test(part))
  )
    return Response.json({ detail: "not_found" }, { status: 404 });

  const base = process.env.API_URL ?? "http://localhost:8000";
  const url = `${base}/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;
  const hasBody = !["GET", "HEAD"].includes(request.method);
  if (
    hasBody &&
    request.headers.get("origin") !==
      (process.env.APP_BASE_URL ?? request.nextUrl.origin).replace(/\/$/, "")
  )
    return Response.json({ detail: "origin_rejected" }, { status: 403 });
  const limit = path.join("/") === "portfolio/import" ? 10 * 1024 * 1024 : 1024 * 1024;
  const declared = Number(request.headers.get("content-length") ?? "0");
  if (!Number.isFinite(declared) || declared < 0 || declared > limit)
    return Response.json({ detail: "body_too_large" }, { status: 413 });
  const wantsStream = request.headers.get("accept")?.includes("text/event-stream") ?? false;
  const headers: Record<string, string> = {};
  const cookie = request.headers.get("cookie");
  if (cookie) headers.cookie = cookie;
  const origin = request.headers.get("origin");
  if (origin) headers.origin = origin;
  if (hasBody) headers["content-type"] = forwardedType(request.headers.get("content-type"));
  const lastEventId = request.headers.get("last-event-id");
  if (lastEventId) headers["last-event-id"] = lastEventId;
  try {
    let body: Uint8Array | undefined;
    if (hasBody && request.body) {
      const reader = request.body.getReader();
      const chunks: Uint8Array[] = [];
      let size = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.length;
        if (size > limit) {
          await reader.cancel();
          return Response.json({ detail: "body_too_large" }, { status: 413 });
        }
        chunks.push(value);
      }
      body = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) {
        body.set(chunk, offset);
        offset += chunk.length;
      }
    }
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: body as BodyInit | undefined,
      redirect: "error",
      cache: "no-store",
      // SSE lives as long as the run does: no timeout, but stop when the browser disconnects.
      signal: wantsStream
        ? request.signal
        : AbortSignal.any([request.signal, AbortSignal.timeout(30_000)]),
    });
    const contentType = response.headers.get("content-type") ?? "application/json";
    const responseHeaders = new Headers({
      "content-type": contentType,
      "cache-control": "no-store",
    });
    if (path[0] === "auth")
      for (const value of response.headers.getSetCookie())
        responseHeaders.append("set-cookie", value);
    const retry = response.headers.get("retry-after");
    if (retry) responseHeaders.set("retry-after", retry);
    if (response.status === 204)
      return new Response(null, { status: 204, headers: responseHeaders });
    if (contentType.includes("text/event-stream") && response.body) {
      return new Response(response.body, {
        status: response.status,
        headers: {
          "content-type": contentType,
          "cache-control": "no-store, no-transform",
          "x-accel-buffering": "no",
        },
      });
    }
    return new Response(await response.text(), {
      status: response.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json({ detail: "api_unreachable" }, { status: 503 });
  }
}

export { forward as GET, forward as POST, forward as PATCH, forward as DELETE };
