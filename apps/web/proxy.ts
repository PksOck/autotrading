import { NextRequest, NextResponse } from "next/server";
import { PUBLIC_PAGES } from "@/lib/access";

/** UX redirect only; FastAPI independently authorizes every private API request. */
export async function proxy(request: NextRequest) {
  if (PUBLIC_PAGES.has(request.nextUrl.pathname)) return NextResponse.next();
  try {
    const response = await fetch(`${process.env.API_URL ?? "http://localhost:8000"}/auth/session`, {
      headers: { cookie: request.headers.get("cookie") ?? "" },
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(5000),
    });
    if (response.ok && (await response.json()).authenticated === true) return NextResponse.next();
  } catch {
    /* Unavailable authentication fails closed. */
  }
  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/((?!api(?:/|$)|_next/|icon.svg$|favicon.ico$|manifest.webmanifest$).*)"],
};
