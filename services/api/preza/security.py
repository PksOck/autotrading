"""API-wide authentication, independent of the browser and Next routing."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.responses import JSONResponse

from preza.config import get_settings
from preza.services import owner_access as access

PRIVATE_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


async def protect(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    settings = get_settings()
    path = request.url.path
    public = path in {"/health", "/auth/login", "/auth/session"}
    if settings.requires_auth and path != "/health":
        if not access.configured(settings):
            return JSONResponse(
                {"detail": "auth_not_configured"}, status_code=503, headers=PRIVATE_HEADERS
            )
        if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get(
            "origin"
        ) != settings.app_base_url.rstrip("/"):
            return JSONResponse(
                {"detail": "origin_rejected"}, status_code=403, headers=PRIVATE_HEADERS
            )
        if not public and not await access.authenticated(
            request.cookies.get(access.cookie_name(settings)),
            settings,
            touch=request.method not in {"GET", "HEAD", "OPTIONS"},
        ):
            return JSONResponse(
                {"detail": "authentication_required"}, status_code=401, headers=PRIVATE_HEADERS
            )
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
