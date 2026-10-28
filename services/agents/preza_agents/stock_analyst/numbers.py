"""Numeric tokens and units shared by fact extraction and claim validation."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Literal

Unit = Literal["plain", "percent"]
NUMBER = re.compile(r"[-+]?(?:\d+(?:[.,\u00a0\u202f ]\d{3})*(?:[.,]\d+)?|[.,]\d+)(?:[eE][-+]?\d+)?")
PERCENT = re.compile(r"\s*(?:%|pct\b|odstotk\w*)", re.I)
# "RSI 14" names the indicator; only its usual windows, so "RSI 70" is still a level,
# and a following %, decimal or digit group ("ATR 14 %", "SMA 200 000") makes it a value.
INDICATOR = re.compile(
    r"\b(?:(?:SMA|EMA)\s(?:20|50|100|200)|(?:RSI|ATR)\s14"
    r"|SMA\d+|EMA\d+|RSI\d*|ATR\d*|Q[1-4])\b"
    r"(?![.,]\d|[.,\u00a0\u202f ]\d{3}\b|\s*(?:%|pct\b|odstot))",
    re.I,
)
# Explicit, bounded horizons. These are labels, not claimed market levels.
PERIOD_UNITS = {
    400: r"days?|dni|dan|d|dnevn\w*",
    52: r"weeks?|tednov|teden|tedna|tednih|tedensk\w*",
    36: r"months?|mesec|meseca|mesecev|mesece|meseci|mesecih|m|mesečn\w*",
    12: r"quarters?|četrtletje|četrtletji|četrtletij|četrtletn\w*",
    10: r"years?|leto|leti|let|letn\w*",
}
# "20- in 50-dnevno", "3-, 6-mesečni", "20- or 50-day": the first number borrows the
# second one's unit.
JOINED = r"(?:-\s*(?:,|in|ali|oziroma|oz\.|and|or|to)\s*(\d+))?"
PERIODS = [
    (maximum, re.compile(rf"(?<![\w.,+-])(\d+){JOINED}[- ]?(?:{units})\b", re.I))
    for maximum, units in PERIOD_UNITS.items()
]
MONTHS = (
    r"januar\w*|februar\w*|mar(?:ec|ca|cu|ch)|april\w*|maj(?:a|u)?|may|jun\w*|jul\w*"
    r"|avgust\w*|august|septemb\w*|oktob\w*|octob\w*|novemb\w*|decemb\w*"
)
# Calendar dates name a day, not a level: "30. junija 2026", "June 30, 2026", "30 June".
DATE = re.compile(
    rf"\b\d{{1,2}}\.?\s*(?:{MONTHS})\b(?:,?\s+\d{{4}}\b)?"
    rf"|\b(?:{MONTHS})\s+\d{{1,2}}\b(?:,?\s+\d{{4}}\b)?",
    re.I,
)
FACT_METADATA = re.compile(
    r"https?://\S+|www\.\S+"
    r"|\b\d{4}[-/]\d{2}[-/]\d{2}(?:T[\d:.+Z-]+)?\b"
    r"|\b\d{1,2}[./]\d{1,2}[./]\d{4}\b"
    r"|\b\d{10}-\d{2}-\d{6}\b"
    r"|\b[A-Z]+\d+\b"
    r"|\b[a-zA-Z]\w*_\w*\d\w*\b"
    r"|\b(?:ID|CIK|accession(?:\s+number)?)\s*[:=#]?\s*\d[\w-]*\b"
    r"|\bForm\s+\d+(?:-[A-Z])?(?:/A)?\b",
    re.I,
)


def variants(raw: str) -> set[Decimal]:
    raw = raw.replace("\u00a0", "").replace("\u202f", "").replace(" ", "").lstrip("+")
    if "," in raw and "." in raw:
        decimal_mark = "," if raw.rfind(",") > raw.rfind(".") else "."
        group_mark = "." if decimal_mark == "," else ","
        candidates = {raw.replace(group_mark, "").replace(decimal_mark, ".")}
    elif "," in raw or "." in raw:
        separator = "," if "," in raw else "."
        candidates = {raw.replace(separator, ".")}
        if re.fullmatch(r"-?\d{1,3}(?:[.,]\d{3})+", raw):
            candidates.add(raw.replace(separator, ""))
    else:
        candidates = {raw}
    values = set()
    for text in candidates:
        try:
            values.add(Decimal(text))
        except ArithmeticError:
            pass
    return values


def unit_after(text: str, end: int) -> Unit:
    return "percent" if PERCENT.match(text, end) else "plain"


def fact_unit(key: str) -> Unit:
    # Valuation bands retain the metric's unit; its percentile rank does not.
    metric = re.sub(r"_(?:p20|median|p80)$", "", key)
    return "percent" if metric.endswith("_pct") or metric == "fcf_yield" else "plain"


def numeric_claims(text: str, *, facts: bool = False) -> list[re.Match[str]]:
    ignored = [m.span() for m in INDICATOR.finditer(text)]
    ignored.extend(m.span() for m in DATE.finditer(text))
    for maximum, pattern in PERIODS:
        ignored.extend(
            m.span()
            for m in pattern.finditer(text)
            if int(m[1]) <= maximum and int(m[2] or 0) <= maximum
        )
    if facts:
        ignored.extend(m.span() for m in FACT_METADATA.finditer(text))
    return [
        m
        for m in NUMBER.finditer(text)
        if not any(start < m.end() and m.start() < end for start, end in ignored)
    ]


def text_numbers(text: str, *, unit: Unit | None = None) -> dict[str, Decimal]:
    """Extract values from retained source text, never its provenance headers."""
    numbers: dict[str, Decimal] = {}
    for index, match in enumerate(numeric_claims(text, facts=True)):
        suffix = "_pct" if (unit or unit_after(text, match.end())) == "percent" else ""
        for variant, value in enumerate(sorted(variants(match.group()))):
            numbers[f"fact_{index}_{variant}{suffix}"] = value
    return numbers
