"""Project the immutable reservation into bounded, explicitly untrusted prompt data."""

import json
from typing import Any

from preza.services.thesis_reviews import MAX_CLAIMS, MAX_EVIDENCE, MAX_INPUT_BYTES


class InputLimitError(ValueError):
    pass


def prompt_data(snapshot: dict[str, Any]) -> str:
    claims = snapshot["claims"]
    evidence = snapshot["evidence"]
    if not 0 < len(claims) <= MAX_CLAIMS or len(evidence) > MAX_EVIDENCE:
        raise InputLimitError("snapshot_limit")
    data = {
        "symbol": snapshot["symbol"],
        "locale": snapshot.get("locale", "en"),
        "claims": [
            {
                "claim_id": c["claim_id"],
                "statement": c["statement"],
                "invalidated_if": c.get("invalidated_if"),
                "upgrade_if": c.get("upgrade_if")
                or (c.get("original_text") if c.get("trigger_kind") == "upgrade" else None),
                "downgrade_if": c.get("downgrade_if")
                or (c.get("original_text") if c.get("trigger_kind") == "downgrade" else None),
            }
            for c in claims
        ],
        "evidence": [{k: e[k] for k in ("ref", "title", "excerpt")} for e in evidence],
    }
    # The reservation already bounds the full snapshot. Never silently omit an ID
    # or change persisted coverage after dispatch if that contract is violated.
    encoded = json.dumps(data, ensure_ascii=False)
    if len(encoded.encode("utf-8")) > MAX_INPUT_BYTES:
        raise InputLimitError("input_limit")
    return encoded
