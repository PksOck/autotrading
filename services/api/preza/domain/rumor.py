"""Deterministic English and Slovenian hedging detection for news evidence."""

import re

# Filings and press releases are the confirming sources; their wording is never treated as hedging.
OFFICIAL_KINDS = frozenset({"press_release", "filing"})

_PATTERNS = tuple(
    re.compile(r"\b(?:" + phrase + r")\b", re.IGNORECASE)
    for phrase in (
        r"reportedly",
        r"according\s+to\s+(?:people|persons|sources)(?:\s+familiar)?",
        r"people\s+familiar\s+with\s+the\s+matter",
        r"sources\s+(?:say|said)",
        r"(?:is|are)\s+said\s+to",
        r"rumou?r(?:s|ed)?",
        r"unconfirmed",
        r"(?:takeover|merger|acquisition|deal|bid|buyout)\s+speculation",
        r"speculation\s+(?:that|about|over)\b[\s\S]*?"
        r"\b(?:takeover|merger|acquisition|deal|bid|buyout)",
        r"in\s+(?:(?:early|advanced|exclusive)\s+)?talks\s+(?:to|with|over|for|about)",
        r"nears\s+(?:a\s+)?deal",
        r"in\s+discussions\s+to",
        r"considering\s+(?:(?:a|an|the)\s+)?(?:takeover|bid|acquisition|sale)",
        r"(?:explores|exploring)\s+(?:a\s+)?sale",
        r"(?:explores|exploring)\s+options\s+including\s+(?:a\s+)?sale",
        r"(?:explores|exploring)\s+strategic\s+alternatives",
        r"approached\s+(?:by\s+potential\s+buyers|about\s+(?:a\s+)?takeover)",
        r"people\s+with\s+knowledge",
        r"person\s+familiar",
        r"people\s+briefed",
        r"anonymous\s+sources",
        r"(?:weighs|weighing)\s+(?:a\s+)?(?:bid|offer|sale|deal)",
        r"domnevno",
        r"neuradno",
        r"po\s+(?:neuradnih\s+)?navedbah\s+virov",
        r"govoric\w*",
        r"naj\s+bi",
        r"v\s+pogovorih\s+za\s+prevzem\w*",
        r"v\s+pogajanjih\s+za\s+nakup\w*",
        r"razmišlja\s+o\s+prevzem\w*",
        r"preučuje\s+(?:možnost\s+)?prodaj\w*",
        r"po\s+poročanju\s+\w+\s+virov",
    )
)
_SOURCE_SUFFIX = re.compile(r"[-—:,]\s*sources?\s*$", re.IGNORECASE)


def looks_like_rumor(title: str, summary: str | None) -> bool:
    """Flag hedging in either field without inferring confirmation or intent."""
    return any(
        _SOURCE_SUFFIX.search(text) or any(pattern.search(text) for pattern in _PATTERNS)
        for text in (title, summary or "")
    )


def item_is_rumor(kind: str, title: str, summary: str | None) -> bool:
    """Classify hedging only for non-official news kinds."""
    return kind not in OFFICIAL_KINDS and looks_like_rumor(title, summary)
