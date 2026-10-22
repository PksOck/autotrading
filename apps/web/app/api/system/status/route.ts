/** Proxies the FastAPI status endpoint so the browser never talks to the API host directly. */
export const dynamic = "force-dynamic";

export async function GET() {
  const base = process.env.API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${base}/system/status`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    return Response.json(await response.json(), { status: response.status });
  } catch {
    return Response.json({ error: "api_unreachable" }, { status: 503 });
  }
}
