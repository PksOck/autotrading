"""Single-owner authentication. Tokens are opaque; only their digests leave memory."""

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import bcrypt
from sqlalchemy import delete, text

from preza.config import Settings
from preza.db import get_sessionmaker
from preza.models_auth import LoginThrottle, OwnerSession


def hash_password(password: str) -> str:
    if not 14 <= len(password) <= 256:
        raise ValueError("password_length")
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=5)
    return f"scrypt-v1${salt}${digest.hex()}"


def valid_hash(value: str) -> bool:
    if re.fullmatch(r"\$2[aby]\$(?:1[0-6])\$[./A-Za-z0-9]{53}", value):
        return True
    parts = value.split("$")
    return (
        len(parts) == 3
        and parts[0] == "scrypt-v1"
        and len(parts[1]) == 32
        and len(parts[2]) == 128
        and all(c in "0123456789abcdef" for c in parts[1] + parts[2])
    )


def verify_password(password: str, encoded: str) -> bool:
    if not valid_hash(encoded) or len(password) > 256:
        return False
    if encoded.startswith(("$2a$", "$2b$", "$2y$")):
        raw = password.encode()
        if len(raw) > 72:
            return False
        try:
            return bcrypt.checkpw(raw, encoded.encode("ascii"))
        except ValueError:
            return False
    _, salt, expected = encoded.split("$")
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=5)
    return hmac.compare_digest(digest.hex(), expected)


def configured(settings: Settings) -> bool:
    origin = urlsplit(settings.app_base_url)
    return bool(
        settings.owner_password_hash
        and valid_hash(settings.owner_password_hash.get_secret_value())
        and settings.owner_username.strip()
        and origin.hostname
        and not origin.username
        and not origin.password
        and origin.path in {"", "/"}
        and not origin.query
        and not origin.fragment
        and (origin.scheme == "https" or settings.app_env != "production")
    )


def cookie_name(settings: Settings) -> str:
    return "__Host-preza_session" if settings.app_env == "production" else "preza_session"


def credential_version(settings: Settings) -> str:
    value = settings.owner_password_hash.get_secret_value() if settings.owner_password_hash else ""
    return hashlib.sha256(f"{settings.owner_username}:{value}".encode()).hexdigest()


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def authenticated(token: str | None, settings: Settings, *, touch: bool = False) -> bool:
    if not token or len(token) != 64 or not configured(settings):
        return False
    now = datetime.now(UTC)
    async with get_sessionmaker()() as db:
        row = await db.get(OwnerSession, digest_token(token), with_for_update=True)
        if row is None:
            return False
        if (
            row.expires_at <= now
            or row.last_seen_at <= now - timedelta(minutes=settings.auth_idle_minutes)
            or row.credential_version != credential_version(settings)
        ):
            await db.delete(row)
            await db.commit()
            return False
        if touch:
            row.last_seen_at = now
            await db.commit()
        return True


async def reserve_attempt() -> bool:
    """A global cap deliberately ignores attacker-controlled forwarding/IP headers."""
    now = datetime.now(UTC)
    async with get_sessionmaker()() as db:
        await db.execute(text("SELECT pg_advisory_xact_lock(73160623, 1)"))
        row = await db.get(LoginThrottle, "owner")
        if row is None:
            row = LoginThrottle(key="owner", attempts=0, window_start=now)
            db.add(row)
        if row.window_start <= now - timedelta(minutes=15):
            row.window_start, row.attempts = now, 0
        if row.attempts >= 5:
            return False
        row.attempts += 1
        await db.commit()
    return True


async def create_session(settings: Settings) -> str:
    token = secrets.token_hex(32)
    now = datetime.now(UTC)
    async with get_sessionmaker()() as db:
        await db.execute(delete(OwnerSession).where(OwnerSession.expires_at <= now))
        db.add(
            OwnerSession(
                token_hash=digest_token(token),
                credential_version=credential_version(settings),
                expires_at=now + timedelta(hours=settings.auth_session_hours),
                last_seen_at=now,
            )
        )
        await db.commit()
    return token


async def revoke(token: str | None) -> None:
    if token:
        async with get_sessionmaker()() as db:
            await db.execute(
                delete(OwnerSession).where(OwnerSession.token_hash == digest_token(token))
            )
            await db.commit()
