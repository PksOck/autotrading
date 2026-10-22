"""Telegram Bot API client, message formatting and sending policy (ADR-0007, VOICE §5)."""

import html
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

import httpx

API = "https://api.telegram.org"
TZ = ZoneInfo("Europe/Ljubljana")


class TelegramError(Exception):
    """Network or API failure. Messages never contain the bot token."""


class TelegramClient:
    def __init__(self, token: str, client: httpx.AsyncClient | None = None):
        self._token = token
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=15)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _call(
        self, method: str, payload: dict[str, Any], read_timeout: float | None = None
    ) -> Any:
        url = f"{API}/bot{self._token}/{method}"
        try:
            response = await self._client.post(
                url,
                json=payload,
                timeout=read_timeout if read_timeout is not None else httpx.USE_CLIENT_DEFAULT,
            )
        except httpx.HTTPError as exc:
            # httpx messages may embed the URL (and so the token): report the type only.
            raise TelegramError(f"{method}: network error ({type(exc).__name__})") from None
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code != 200 or not isinstance(body, dict) or not body.get("ok"):
            description = body.get("description", "") if isinstance(body, dict) else ""
            raise TelegramError(
                f"{method}: HTTP {response.status_code} {str(description)[:200]}".strip()
            )
        return body.get("result")

    async def send_message(
        self, chat_id: str, text: str, buttons: list[list[dict[str, Any]]] | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        result = await self._call("sendMessage", payload)
        return result if isinstance(result, dict) else {}

    async def get_updates(
        self,
        offset: int | None,
        timeout: int = 30,  # noqa: ASYNC109 (Telegram long-poll seconds)
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"],
        }
        if offset is not None:
            payload["offset"] = offset
        result = await self._call("getUpdates", payload, read_timeout=timeout + 10)
        return list(result) if isinstance(result, list) else []

    async def answer_callback(self, callback_id: str, text: str) -> None:
        await self._call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})


KIND_LABELS = {
    "sl": {
        "catalyst": "Katalizator",
        "entry": "Vstop",
        "exit_warning": "Opozorilo za izstop",
        "thesis_break": "Zlom teze",
        "options_idea": "Ideja za opcije",
    },
    "en": {
        "catalyst": "Catalyst",
        "entry": "Entry",
        "exit_warning": "Exit warning",
        "thesis_break": "Thesis break",
        "options_idea": "Options idea",
    },
}
RUMOR_PREFIX = {"sl": "Nepotrjeno.", "en": "Unconfirmed."}
STRENGTH_LABEL = {"sl": "Moč", "en": "Strength"}
OPEN_LABEL = {"sl": "Odpri", "en": "Open"}
WATCH_LABEL = {"sl": "Spremljaj", "en": "Watch"}
DISMISS_LABEL = {"sl": "Zavrzi", "en": "Dismiss"}
MAX_RATIONALE = 220


def _lang(locale: str) -> str:
    return "en" if locale.lower().startswith("en") else "sl"


def fmt_num(value: float, locale: str, digits: int = 2) -> str:
    text = f"{value:.{digits}f}"
    return text.replace(".", ",") if _lang(locale) == "sl" else text


def kind_label(kind: str, locale: str) -> str:
    return KIND_LABELS[_lang(locale)].get(kind, kind)


def _clean(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip().replace("!", ".")
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return html.escape(text, quote=False)


def format_signal(
    signal_symbol: str,
    kind: str,
    rationale: str,
    strength: float,
    is_rumor: bool,
    url: str,
    locale: str,
) -> str:
    """At most 4 lines: header, rationale and strength, link."""
    lang = _lang(locale)
    head = f"{html.escape(signal_symbol, quote=False)} · {kind_label(kind, lang)}"
    if is_rumor:
        head = f"{RUMOR_PREFIX[lang]} {head}"
    body = f"{_clean(rationale, MAX_RATIONALE)} {STRENGTH_LABEL[lang]} {fmt_num(strength, lang)}"
    lines = [head, body]
    if url:
        lines.append(f"{OPEN_LABEL[lang]}: {html.escape(url, quote=False)}")
    return "\n".join(lines)


def signal_buttons(signal_id: object, locale: str, app_base_url: str) -> list[list[dict[str, Any]]]:
    lang = _lang(locale)
    return [
        [
            {
                "text": OPEN_LABEL[lang],
                "url": f"{app_base_url.rstrip('/')}/signals?peek=signal:{signal_id}",
            },
            {"text": WATCH_LABEL[lang], "callback_data": f"w:{signal_id}"},
            {"text": DISMISS_LABEL[lang], "callback_data": f"x:{signal_id}"},
        ]
    ]


class Decision(StrEnum):
    SEND_NOW = "send_now"
    DEFER_TO_DIGEST = "defer_to_digest"
    SKIP = "skip"


@dataclass(frozen=True)
class NotificationPolicy:
    """Quiet hours 22:00-07:00 local, at most 5 per local day (ADR-0007)."""

    quiet_start: int = 22
    quiet_end: int = 7
    daily_limit: int = 5
    urgent_strength: float = 0.9
    min_strength: float = 0.0

    def is_quiet(self, now: datetime) -> bool:
        hour = now.astimezone(TZ).hour
        return hour >= self.quiet_start or hour < self.quiet_end

    @staticmethod
    def local_day_start(now: datetime) -> datetime:
        local = now.astimezone(TZ)
        return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)

    def decide(
        self, kind: str, strength: float, held: bool, now: datetime, sent_today: int
    ) -> Decision:
        if kind == "thesis_break" and held:
            if self.is_quiet(now) and strength < self.urgent_strength:
                return Decision.DEFER_TO_DIGEST
            return Decision.SEND_NOW  # bypasses the daily limit
        if strength < self.min_strength:
            return Decision.SKIP
        if self.is_quiet(now) or sent_today >= self.daily_limit:
            return Decision.DEFER_TO_DIGEST
        return Decision.SEND_NOW
