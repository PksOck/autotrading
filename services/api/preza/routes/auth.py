"""Owner login; no registration, password recovery or user enumeration."""

import hmac

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, SecretStr, ValidationError
from starlette.concurrency import run_in_threadpool

from preza.config import get_settings
from preza.services import owner_access as access

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/activity", status_code=204)
async def activity() -> Response:
    # Middleware touches only authenticated unsafe requests after checking Origin.
    return Response(status_code=204)


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(max_length=256)


@router.get("/session")
async def session_state(request: Request) -> dict[str, bool]:
    settings = get_settings()
    return {
        "enabled": settings.requires_auth,
        "authenticated": not settings.requires_auth
        or await access.authenticated(request.cookies.get(access.cookie_name(settings)), settings),
    }


@router.post("/login")
async def login(request: Request, response: Response) -> dict[str, bool]:
    settings = get_settings()
    if not settings.requires_auth or not access.configured(settings):
        raise HTTPException(503, "auth_not_configured")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 4096:
            raise HTTPException(413, "body_too_large")
    try:
        credentials = Credentials.model_validate_json(bytes(body))
    except ValidationError:
        raise HTTPException(400, "invalid_credentials") from None
    if not await access.reserve_attempt():
        raise HTTPException(429, "login_throttled", headers={"Retry-After": "900"})
    assert settings.owner_password_hash is not None
    valid = await run_in_threadpool(
        access.verify_password,
        credentials.password.get_secret_value(),
        settings.owner_password_hash.get_secret_value(),
    )
    if not valid or not hmac.compare_digest(
        credentials.username.encode(), settings.owner_username.encode()
    ):
        raise HTTPException(401, "invalid_credentials")
    token = await access.create_session(settings)
    response.set_cookie(
        access.cookie_name(settings),
        token,
        max_age=settings.auth_session_hours * 3600,
        httponly=True,
        secure=settings.app_env == "production" or settings.app_base_url.startswith("https://"),
        samesite="strict",
        path="/",
    )
    return {"authenticated": True}


@router.post("/logout", status_code=204)
async def logout(request: Request) -> Response:
    settings = get_settings()
    await access.revoke(request.cookies.get(access.cookie_name(settings)))
    response = Response(status_code=204)
    response.delete_cookie(
        access.cookie_name(settings),
        path="/",
        httponly=True,
        secure=settings.app_env == "production" or settings.app_base_url.startswith("https://"),
        samesite="strict",
    )
    return response
