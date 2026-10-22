"""Translation of event summaries into the user's language (`local-fast`, BL-055).

The English summary stays canonical; translations are stored per locale and shown with a
"translated" mark. A failed translation is not an error: the UI falls back to English.
"""

from preza.domain.radar import TranslationBatch
from preza.llm.client import Llm, LlmUnavailableError
from preza.models import Event
from preza.radar.prompts import LANGUAGE_NAMES, TRANSLATE_SYSTEM, translate_user

BATCH = 8


async def translate_events(events: list[Event], llm: Llm, locale: str) -> int:
    """Fills `summary_i18n[locale]` for events that lack it. Returns how many were translated."""
    language = LANGUAGE_NAMES.get(locale)
    if language is None or locale == "en":
        return 0
    todo = [e for e in events if e.summary and locale not in (e.summary_i18n or {})]
    done = 0
    for start in range(0, len(todo), BATCH):
        chunk = todo[start : start + BATCH]
        try:
            result = await llm.complete_json(
                "local-fast",
                TRANSLATE_SYSTEM.format(language=language),
                translate_user([(e.id, e.summary or "") for e in chunk]),
                TranslationBatch,
            )
        except LlmUnavailableError:
            break  # the local model is down; the next run retries
        by_id = {t.id: t.text.strip() for t in result.value.items if t.text.strip()}
        for event in chunk:
            if text := by_id.get(event.id):
                event.summary_i18n = {**(event.summary_i18n or {}), locale: text}
                done += 1
    return done
