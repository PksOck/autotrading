"""Deterministic stock facts. No model calls and no network access."""

from __future__ import annotations

import csv
import re
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, Field

from preza.domain.quality import quality_parts, quality_score
from preza.domain.valuation import valuation_bands
from preza.entries.indicators import compute, last
from preza_agents.deep_research.snapshot import DataSnapshot, NewsRow
from preza_agents.deep_research.vendor_local import RUMOR_MARK
from preza_agents.stock_analyst.numbers import PERCENT, text_numbers

MAX_DIGEST = 3000
MAX_REGISTER = 6500
# Market-wide news is context, not evidence about the instrument: few items, never official.
MAX_MACRO_ITEMS = 5
METRICS = (
    "pe",
    "ev_ebit",
    "fcf_yield",
    "roe_pct",
    "gross_margin_pct",
    "net_margin_pct",
    "revenue_growth_pct",
    "debt_to_equity",
    "dividend_yield_pct",
    "payout_ratio_pct",
)
LABELS = {
    "sl": {
        "market": "Tehnična slika",
        "fundamentals": "Temeljni podatki",
        "news": "Novice",
        "source": "Vir",
        "none": "Temeljni podatki niso na voljo (no fundamentals).",
        "insiders": "Število prijav Form 4",
        "global": "Svetovne novice",
        "close": "Zaključna cena",
        "return": "Donos",
        "distance": "Oddaljenost",
        "high_52w": "52-tedenski vrh",
        "low_52w": "52-tedensko dno",
        "volume": "Povprečni volumen",
        "statements": "Izbrani izkazi SEC EDGAR",
        "price_date": "Datum zaključne cene",
        "price_only": "Donosi ne vključujejo dividend.",
    },
    "en": {
        "market": "Technical picture",
        "fundamentals": "Fundamentals",
        "news": "News",
        "source": "Source",
        "none": "No fundamentals available.",
        "insiders": "Form 4 filing count",
        "global": "Global headlines",
        "close": "Close",
        "return": "Return",
        "distance": "Distance",
        "high_52w": "52-week high",
        "low_52w": "52-week low",
        "volume": "Average volume",
        "statements": "Selected SEC EDGAR statements",
        "price_date": "Price date",
        "price_only": "Returns are price-only, not total returns.",
    },
}


class Digest(BaseModel):
    text: str = Field(max_length=MAX_DIGEST)
    source: str
    as_of: date
    numbers: dict[str, Decimal] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    id: str = Field(max_length=16)
    kind: Literal["market", "fundamental", "statement", "news", "filing", "insider", "macro"]
    source: str
    as_of: date | datetime
    url: str | None = None
    accession: str | None = None
    confirmed: bool
    official: bool = False
    text: str = Field(max_length=600)
    numbers: dict[str, Decimal] = Field(default_factory=dict)

    def render(self) -> str:
        status = "confirmed" if self.confirmed else RUMOR_MARK
        link = f"; {self.url or self.accession}" if self.url or self.accession else ""
        return (
            f"[{self.id}] {self.kind}; {self.source}; as_of: {self.as_of}; "
            f"{status}{link}: {self.text}"
        )


class EvidenceRegister(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)

    def render(self) -> str:
        return "\n".join(item.render() for item in self.items)

    def sources_md(self) -> str:
        return "\n".join(["### Sources", *[f"- {item.render()}" for item in self.items]])


def _short_text(text: str, limit: int) -> str:
    """Keep complete sentences only; an oversized unbroken item is omitted."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept: list[str] = []
    for sentence in sentences:
        if len(" ".join([*kept, sentence])) > limit:
            break
        kept.append(sentence)
    return " ".join(kept)


def _num(value: Decimal, locale: str) -> str:
    text = f"{value:,.2f}"
    return text.replace(",", " ").replace(".", ",").replace(" ", ".") if locale == "sl" else text


def _decimal(value: object) -> Decimal | None:
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _digest(
    snapshot: DataSnapshot,
    kind: str,
    source: str | None,
    lines: list[str],
    numbers: dict[str, Decimal],
    locale: str,
    as_of: date | None = None,
) -> Digest:
    t = LABELS.get(locale, LABELS["en"])
    stamp = as_of or snapshot.as_of
    shown_source = source or "unknown"
    if len(shown_source) > 120:
        shown_source = "sources listed in the evidence register"
    header = f"### {t[kind]} · {snapshot.symbol}\n{t['source']}: {shown_source}; as_of: {stamp}\n"
    body: list[str] = []
    remaining = MAX_DIGEST - len(header)
    for line in "\n".join(lines).splitlines():
        if len(line) + 1 > remaining:
            continue
        body.append(line)
        remaining -= len(line) + 1
    return Digest(
        text=header + "\n".join(body),
        source=source or "unknown",
        as_of=stamp,
        numbers=numbers,
    )


def market_digest(snapshot: DataSnapshot, locale: str = "en") -> Digest:
    t = LABELS.get(locale, LABELS["en"])
    bars = sorted((b for b in snapshot.bars if b.day <= snapshot.as_of), key=lambda b: b.day)
    numbers: dict[str, Decimal] = {}
    labels: dict[str, str] = {
        "close": t["close"],
        "high_52w": t["high_52w"],
        "low_52w": t["low_52w"],
    }
    if bars:
        close = bars[-1].close
        numbers["close"] = close
        for period, days in (("1w", 5), ("1m", 21), ("3m", 63), ("6m", 126), ("1y", 252)):
            if len(bars) > days and bars[-1 - days].close > 0:
                key = f"return_{period}_pct"
                numbers[key] = (close / bars[-1 - days].close - 1) * 100
                labels[key] = f"{t['return']} {period} %"
        series = compute(
            [float(b.high) for b in bars],
            [float(b.low) for b in bars],
            [float(b.close) for b in bars],
        )
        for key, value in (
            ("sma50", last(series.sma50)),
            ("sma200", last(series.sma200)),
            ("rsi14", last(series.rsi14)),
        ):
            if value is not None:
                numbers[key] = Decimal(str(value))
                if key.startswith("sma") and value > 0:
                    numbers[f"distance_{key}_pct"] = (close / Decimal(str(value)) - 1) * 100
                    labels[f"distance_{key}_pct"] = f"{t['distance']} {key.upper()} %"
        atr = last(series.atr14)
        if atr is not None and close > 0:
            numbers["atr_pct"] = Decimal(str(atr)) / close * 100
            labels["atr_pct"] = "ATR14 %"
        year = [b for b in bars if b.day > snapshot.as_of - timedelta(days=365)]
        if year:
            for key, extreme in (
                ("high_52w", max(b.high for b in year)),
                ("low_52w", min(b.low for b in year)),
            ):
                numbers[key] = extreme
                if extreme > 0:
                    numbers[f"distance_{key}_pct"] = (close / extreme - 1) * 100
                    labels[f"distance_{key}_pct"] = f"{t['distance']} {t[key].lower()} %"
        for days in (20, 90):
            volumes = [b.volume for b in bars[-days:] if b.volume is not None]
            if volumes:
                numbers[f"avg_volume_{days}d"] = Decimal(sum(volumes)) / len(volumes)
                labels[f"avg_volume_{days}d"] = f"{t['volume']} {days}d"
        long_volume = numbers.get("avg_volume_90d")
        if long_volume and "avg_volume_20d" in numbers:
            numbers["volume_20d_vs_90d"] = numbers["avg_volume_20d"] / long_volume
    lines = [f"- {labels.get(k, k)}: {_num(v, locale)}" for k, v in numbers.items()]
    if bars:
        lines.append(f"{t['price_date']}: {bars[-1].day}; {t['price_only']}")
    return _digest(
        snapshot,
        "market",
        snapshot.bars_source,
        lines,
        numbers,
        locale,
        bars[-1].day if bars else None,
    )


def statement_lines(statements: dict[str, str]) -> list[str]:
    """SEC tables are CSV with ascending periods, not Markdown tables.

    Preserve unit comments and use identical last-four column indices for the
    header and every row. Do not turn an unavailable cell into a numeric zero.
    """
    selected: list[str] = []
    pattern = re.compile(
        r"revenue|income|profit|assets|liabilities|equity|cash|eps|expenditure", re.I
    )
    for kind, text in sorted(statements.items()):
        raw_lines = text.splitlines()
        try:
            rows = list(
                csv.reader(line for line in raw_lines if line.strip() and not line.startswith("#"))
            )
        except csv.Error:
            continue
        if len(rows) < 2 or len(rows[0]) < 2:
            continue
        indices = [0, *range(max(1, len(rows[0]) - 4), len(rows[0]))]
        selected.append(f"{kind} [sec_edgar; USD millions unless row states otherwise]")
        selected.append(" | ".join(rows[0][i] for i in indices))
        used = 0
        for row in rows[1:]:
            if row and pattern.search(row[0]):
                selected.append(" | ".join(row[i] if i < len(row) else "" for i in indices))
                used += 1
                if used >= 6:
                    break
    return selected


def fundamentals_digest(
    snapshot: DataSnapshot,
    locale: str = "en",
    statements: dict[str, str] | None = None,
) -> Digest:
    t = LABELS.get(locale, LABELS["en"])
    metrics: dict[str, Any] = snapshot.fundamentals or {}
    if snapshot.fundamentals_as_of and snapshot.fundamentals_as_of > snapshot.as_of:
        metrics = {}
    numbers = {k: v for k in METRICS if (v := _decimal(metrics.get(k))) is not None}
    lines = [f"- {k}: {_num(v, locale)}" for k, v in numbers.items()]
    if not numbers:
        lines.append(t["none"])
    clean = {k: float(v) for k, v in numbers.items()}
    history = {
        k: [(d, v) for d, v in rows if d <= snapshot.as_of]
        for k, rows in snapshot.fundamentals_history.items()
    }
    bands = valuation_bands(clean, history, snapshot.fundamentals_as_of or snapshot.as_of)
    for key, band in bands.items():
        for part in ("p20", "median", "p80", "percentile"):
            numbers[f"{key}_{part}"] = Decimal(str(getattr(band, part)))
        lines.append(
            f"- {key} p20 / median / p80: {_num(numbers[f'{key}_p20'], locale)} / "
            f"{_num(numbers[f'{key}_median'], locale)} / {_num(numbers[f'{key}_p80'], locale)}; "
            f"percentile: {_num(numbers[f'{key}_percentile'], locale)}"
        )
    parts = quality_parts(clean)
    score = quality_score(clean)
    for key, value in {
        **{f"quality_{k}": v for k, v in parts.items()},
        "quality_score": score,
    }.items():
        if value is not None:
            numbers[key] = Decimal(str(value))
            lines.append(f"- {key}: {_num(numbers[key], locale)}")
    if statements:
        lines.extend(
            [
                f"\n{t['statements']} [sec_edgar; as_of: {snapshot.as_of}]",
                *statement_lines(statements),
            ]
        )
    return _digest(
        snapshot,
        "fundamentals",
        snapshot.fundamentals_source,
        lines,
        numbers,
        locale,
        snapshot.fundamentals_as_of if metrics else None,
    )


def news_digest(snapshot: DataSnapshot, locale: str = "en") -> Digest:
    t = LABELS.get(locale, LABELS["en"])
    current = [n for n in snapshot.news if n.published_at.date() <= snapshot.as_of]
    insiders = [n for n in current if n.filing_form in ("4", "4/A")]
    lines = [f"{t['insiders']}: {len(insiders)} [sec_edgar; as_of: {snapshot.as_of}]"]
    seen: set[str] = set()

    def headlines(rows: list[NewsRow], limit: int, summaries: bool = True) -> list[str]:
        result = []
        for n in rows:
            title = re.sub(r"\W+", " ", n.title.casefold()).strip()
            if (
                title in seen
                or n.filing_form in ("4", "4/A")
                or n.published_at.date() > snapshot.as_of
            ):
                continue
            seen.add(title)
            mark = f" {RUMOR_MARK}" if n.is_rumor else ""
            title_text = _short_text(n.title, 400)
            if not title_text:
                continue
            line = f"- {n.published_at.date()} [{n.source}]{mark} {title_text}"
            if summaries and n.summary:
                summary = _short_text(n.summary, 160)
                if summary:
                    line += f": {summary}"
            result.append(line)
            if len(result) >= limit:
                break
        return result

    ordered = sorted(
        current,
        key=lambda n: (
            n.is_rumor or RUMOR_MARK in n.title + (n.summary or ""),
            n.kind not in ("press_release", "filing", "filings"),
            -n.published_at.timestamp(),
        ),
    )
    local = headlines(ordered, 12)
    global_rows = headlines(
        sorted(snapshot.global_news, key=lambda n: n.published_at, reverse=True), 5, False
    )

    # Reserve room for global context rather than letting local summaries consume it.
    def fit_lines(rows: list[str], limit: int) -> str:
        fitted: list[str] = []
        for row in rows:
            if sum(len(r) + 1 for r in fitted) + len(row) + 1 > limit:
                break
            fitted.append(row)
        return "\n".join(fitted)

    global_text = fit_lines([t["global"], *global_rows], 1100)
    local_budget = 2650 - len(global_text) - len(lines[0])
    lines += [fit_lines(local, local_budget), global_text]
    known_global = [n for n in snapshot.global_news if n.published_at.date() <= snapshot.as_of]
    sources = ", ".join(sorted({n.source for n in current + known_global}))
    return _digest(
        snapshot, "news", sources, lines, {"form4_count": Decimal(len(insiders))}, locale
    )


def evidence_register(
    snapshot: DataSnapshot,
    digests: list[Digest],
    statements: dict[str, str] | None = None,
    *,
    max_chars: int = MAX_REGISTER,
    control: dict[str, Any] | None = None,
) -> EvidenceRegister:
    """Assign deterministic IDs before trimming whole items, never renumber survivors."""
    items: list[EvidenceItem] = []
    for prefix, kind, digest in zip(
        ("M", "F", "I"), ("market", "fundamental", "insider"), digests, strict=True
    ):
        for index, (key, number) in enumerate(sorted(digest.numbers.items()), 1):
            items.append(
                EvidenceItem(
                    id=f"{prefix}{index}",
                    kind=kind,
                    source="sec_edgar" if kind == "insider" else digest.source,
                    as_of=digest.as_of,
                    confirmed=True,
                    official=kind == "insider" or digest.source == "sec_edgar",
                    text=f"{key}: {number:.2f}",
                    numbers={key: number},
                )
            )
    control_numbers = {
        **{k: v for k, v in (control or {}).items() if not isinstance(v, dict)},
        **{f"component_{k}": v for k, v in (control or {}).get("components", {}).items()},
    }
    for index, (key, raw) in enumerate(sorted(control_numbers.items()), 1):
        if (control_number := _decimal(raw)) is not None:
            items.append(
                EvidenceItem(
                    id=f"C{index}",
                    kind="fundamental",
                    source="deterministic_control",
                    as_of=snapshot.as_of,
                    confirmed=True,
                    text=f"control_{key}: {control_number}",
                    numbers={key: control_number},
                )
            )
    statement_context = ""
    periods = ""
    for index, line in enumerate(statement_lines(statements or {}), 1):
        if "[sec_edgar; USD millions unless row states otherwise]" in line:
            statement_context = line
            periods = ""
            continue
        if not periods:
            periods = line
            continue
        fact = f"{statement_context}; periods: {periods}; {line}"
        if len(fact) <= 600:
            items.append(
                EvidenceItem(
                    id=f"S{index}",
                    kind="statement",
                    source="sec_edgar",
                    as_of=snapshot.as_of,
                    confirmed=RUMOR_MARK not in fact,
                    official=True,
                    text=fact,
                    numbers=text_numbers(
                        line.partition(" | ")[2],
                        unit="percent" if PERCENT.search(line.partition(" | ")[0]) else None,
                    ),
                )
            )

    def rumor(row: NewsRow) -> bool:
        return row.is_rumor or RUMOR_MARK in row.title + (row.summary or "") + row.source

    def priority(row: NewsRow) -> tuple[bool, bool, float, str, str, str]:
        return (
            rumor(row),
            row.kind not in ("press_release", "filing", "filings"),
            -row.published_at.timestamp(),
            row.source,
            row.url,
            row.summary or "",
        )

    unique: dict[str, tuple[NewsRow, bool]] = {}
    for macro, feed in ((False, snapshot.news), (True, snapshot.global_news)):
        for row in feed:
            if row.published_at.date() > snapshot.as_of:
                continue
            identity = re.sub(r"\W+", " ", row.title.casefold()).strip()
            if identity not in unique or (
                unique[identity][1] == macro and priority(row) < priority(unique[identity][0])
            ):
                unique[identity] = (row, macro)
    rows = sorted(
        unique.values(),
        key=lambda pair: (
            pair[0].published_at,
            pair[0].source,
            pair[0].url,
            pair[0].title,
            pair[0].summary or "",
            pair[0].is_rumor,
        ),
    )
    counts: dict[str, int] = {}
    for row, macro in rows:
        news_kind: Literal["insider", "filing", "news", "macro"] = (
            "macro"
            if macro
            else "insider"
            if row.filing_form in ("4", "4/A")
            else ("filing" if row.kind in ("filing", "filings") else "news")
        )
        prefix = {"insider": "A", "filing": "D", "news": "N", "macro": "G"}[news_kind]
        counts[prefix] = counts.get(prefix, 0) + 1
        title = _short_text(row.title, 400)
        if not title:
            continue
        summary = _short_text(row.summary or "", 600 - len(title) - 2)
        text = title + (f": {summary}" if summary else "")
        items.append(
            EvidenceItem(
                id=f"{prefix}{counts[prefix]}",
                kind=news_kind,
                source=row.source,
                as_of=row.published_at,
                url=row.url or None,
                confirmed=not rumor(row),
                official=not macro and row.kind in ("press_release", "filing", "filings"),
                text=text,
                numbers=text_numbers(text),
            )
        )
    # Structured facts about the instrument first, then its own news, market-wide news last.
    tier = {
        "market": 0,
        "fundamental": 0,
        "insider": 0,
        "statement": 1,
        "filing": 2,
        "news": 2,
        "macro": 3,
    }
    items.sort(
        key=lambda item: (
            tier[item.kind],
            not item.confirmed,
            not item.official,
            -(
                item.as_of
                if isinstance(item.as_of, datetime)
                else datetime.combine(item.as_of, time.min, tzinfo=UTC)
            ).timestamp(),
            item.id,
        )
    )
    retained: list[EvidenceItem] = []
    used = macro_count = 0
    for item in items:
        if item.kind == "macro":
            if macro_count >= MAX_MACRO_ITEMS:
                continue
        size = len(item.render()) + (1 if retained else 0)
        if used + size <= max_chars:
            retained.append(item)
            used += size
            macro_count += item.kind == "macro"
    return EvidenceRegister(items=retained)
