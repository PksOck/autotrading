"""Short committed DB phases around one bounded cloud-deep logical call."""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError

from preza.db import get_sessionmaker
from preza.domain.thesis_review import ReviewBatch
from preza.llm.client import LlmUnavailableError
from preza.services import thesis_reviews as reviews
from preza_agents.thesis_tracker.context import InputLimitError, prompt_data
from preza_agents.thesis_tracker.prompts import PROMPT_VERSION, SYSTEM, user_prompt

MAX_OUTPUT_TOKENS = 4000
JOB_TIMEOUT_S = 660


def usage(result: Any) -> dict[str, Any]:
    return {
        key: getattr(result, key, default)
        for key, default in (
            ("attempts", 0),
            ("prompt_tokens", 0),
            ("completion_tokens", 0),
            ("cost", None),
            ("model", None),
        )
    }


async def thesis_review(ctx: dict[str, Any], revision_id: str, week_start: str) -> str:
    review_id = None
    accounting: dict[str, Any] = {}
    try:
        async with asyncio.timeout(JOB_TIMEOUT_S):
            now = datetime.now(UTC)
            if reviews.week_start(now).isoformat() != week_start:
                return "obsolete_week"
            async with get_sessionmaker()() as session:
                review, _created = await reviews.reserve_review(
                    session, uuid.UUID(revision_id), cutoff=now, prompt_version=PROMPT_VERSION
                )
                review_id = review.id
                status, dispatched, snapshot = review.status, review.dispatch_at, review.snapshot
                await session.commit()
            if status in reviews.TERMINAL:
                return status
            if dispatched is not None:
                return await _fail(review_id, "interrupted", unknown=True)
            data = prompt_data(snapshot)
            async with get_sessionmaker()() as session:
                review = await reviews.mark_dispatched(session, review_id)
                status = review.status
                await session.commit()
            if status in reviews.TERMINAL:
                return status
            # No session or transaction remains open during the external call.
            accounting = {"attempts": 1}
            result = await ctx["llm"].complete_json(
                "cloud-deep",
                SYSTEM,
                user_prompt(data),
                ReviewBatch,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            )
            accounting = usage(result)
            batch = ReviewBatch.model_validate(result.value)
            reviews.validate_batch(snapshot, batch)
            async with get_sessionmaker()() as session:
                review = await reviews.finalize_review(session, review_id, batch, **accounting)
                status = review.status
                await session.commit()
            return status
    except LlmUnavailableError as exc:
        accounting = usage(exc)
        code = "role_unavailable"
    except TimeoutError:
        code = "timeout"
    except ValidationError:
        code = "invalid_output"
    except InputLimitError:
        # reserve_review is the authoritative skipped_limits gate. A malformed
        # legacy reservation must fail closed, never dispatch an oversized prompt.
        code = "internal_error"
    except ValueError:
        code = "invalid_references"
    except HTTPException as exc:
        if exc.status_code in (404, 409):
            return "conflict"
        raise
    except Exception:
        # Keep unexpected provider or persistence details out of review records.
        # The failed transaction's context has already rolled back and closed.
        code = "internal_error"
    if review_id is None:
        return "failed"
    # Failure persistence is a short cleanup transaction after the deadline.
    return await _fail(review_id, code, **accounting)


async def _fail(review_id: uuid.UUID, code: str, **kwargs: Any) -> str:
    async with get_sessionmaker()() as session:
        review = await reviews.fail_review(session, review_id, code, **kwargs)
        status = review.status
        await session.commit()
    return status
