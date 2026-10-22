"""Telegram long-polling bot: `python -m preza.cli.telegram_bot` (ADR-0007).

Answers only the configured chat (TELEGRAM_CHAT_ID), except /start, which reveals the chat id
so the user can configure it.
"""

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_sessionmaker
from preza.models import Proposal
from preza.notify.service import handle_callback
from preza.notify.telegram import TelegramClient, TelegramError

log = logging.getLogger("preza.telegram_bot")
TICKER = re.compile(r"^\$?[A-Za-z]{1,5}(?:[.-][A-Za-z]{1,2})?,?$")
Enqueue = Callable[[str], Awaitable[None]]


def parse_predlog(text: str) -> tuple[list[str], str]:
    """`/predlog MSFT ORCL why cloud grows` -> (["MSFT", "ORCL"], "why cloud grows").

    Leading tokens count as tickers while they are written in upper case.
    """
    tokens = text.split()[1:]
    symbols: list[str] = []
    while tokens and TICKER.match(tokens[0]) and tokens[0].lstrip("$").rstrip(",").isupper():
        symbols.append(tokens.pop(0).lstrip("$").rstrip(","))
    return sorted(set(symbols)), " ".join(tokens)


async def enqueue_analysis(proposal_id: str) -> None:
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    try:
        await pool.enqueue_job("analyze_proposal_job", proposal_id)
    finally:
        await pool.aclose()


async def handle_update(
    session: AsyncSession,
    client: TelegramClient,
    update: dict[str, Any],
    settings: Settings,
    enqueue: Enqueue = enqueue_analysis,
) -> None:
    allowed = settings.telegram_chat_id
    sl = not settings.default_locale.lower().startswith("en")
    if "callback_query" in update:
        answer = await handle_callback(session, update, allowed)
        if answer:
            await client.answer_callback(update["callback_query"]["id"], answer)
        return
    message = update.get("message")
    if not isinstance(message, dict):
        return
    chat_id = str((message.get("chat") or {}).get("id", ""))
    text = str(message.get("text", "")).strip()
    command = text.split(maxsplit=1)[0].split("@")[0].lower() if text else ""
    if command == "/start":
        reply = (
            f"Tvoj chat ID je {chat_id}. Vpiši ga v TELEGRAM_CHAT_ID."
            if sl
            else f"Your chat ID is {chat_id}. Put it into TELEGRAM_CHAT_ID."
        )
        await client.send_message(chat_id, reply)
        return
    if not allowed or chat_id != str(allowed):
        return
    if command == "/predlog":
        symbols, hypothesis = parse_predlog(text)
        if not symbols:
            usage = (
                "Uporaba: /predlog SIMBOL kratka teza" if sl else "Usage: /predlog SYMBOL thesis"
            )
            await client.send_message(chat_id, usage)
            return
        proposal = Proposal(
            symbols=symbols,
            hypothesis=hypothesis,
            source_text=text,
            depth="quick",
            save_to="reserve",
        )
        session.add(proposal)
        await session.commit()
        await enqueue(str(proposal.id))
        names = ", ".join(symbols)
        await client.send_message(
            chat_id,
            f"Predlog za {names} je v analizi. Rezultat bo v aplikaciji."
            if sl
            else f"Proposal for {names} is being analyzed. The result will appear in the app.",
        )


async def run() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    client = TelegramClient(settings.telegram_bot_token)
    offset: int | None = None
    try:
        while True:
            try:
                updates = await client.get_updates(offset)
            except TelegramError as exc:
                log.warning("getUpdates failed: %s", exc)
                await asyncio.sleep(5)
                continue
            for update in updates:
                offset = int(update["update_id"]) + 1
                try:
                    async with get_sessionmaker()() as session:
                        await handle_update(session, client, update, settings)
                        await session.commit()
                except Exception:
                    log.exception("update %s failed", update.get("update_id"))
    finally:
        await client.aclose()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())


if __name__ == "__main__":
    main()
