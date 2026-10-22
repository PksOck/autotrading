"""Daily entry run: rules → valuation → dip analysis → ladder → signal (M3, research §5.3).

Entry signals need a cause that keeps the long-term case intact (market, sector, transient).
A fundamental cause on a held position becomes a `thesis_break` signal instead.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.radar import Direction, Horizon, SignalKind, SignalSource, SignalStatus
from preza.entries.config import EntryRules, load_rules
from preza.entries.dip import DipCause, analyze_dip, recent_events
from preza.entries.indicators import compute
from preza.entries.ladder import build_ladder
from preza.entries.rules import Evaluation, EventFact, ZoneState, evaluate
from preza.llm.client import Llm, LlmUnavailableError
from preza.models import Bar, EntryCandidate, Event, Fundamentals, Instrument, Signal
from preza.services.fundamentals import bands_for, bands_json
from preza.services.instruments import find_by_symbol
from preza.services.radar_views import user_symbols

log = logging.getLogger(__name__)

ENTRY_CAUSES = {DipCause.MARKET, DipCause.SECTOR, DipCause.TRANSIENT}
REANALYZE_AFTER = timedelta(days=3)
OPEN_STATUSES = {SignalStatus.NEW.value, SignalStatus.WATCHING.value}
EXPIRY_DAYS = 30


@dataclass
class EntryRun:
    evaluated: int = 0
    active: int = 0
    analyzed: int = 0
    signals: int = 0
    errors: dict[str, str] = field(default_factory=dict)


def _d(value: float | None, places: str = "0.0001") -> Decimal | None:
    return None if value is None else Decimal(str(value)).quantize(Decimal(places))


async def _bars(session: AsyncSession, instrument_id: int, limit: int = 400) -> list[Bar]:
    rows = await session.scalars(
        select(Bar)
        .where(Bar.instrument_id == instrument_id, Bar.interval == "1d")
        .order_by(Bar.day.desc())
        .limit(limit)
    )
    return list(rows)[::-1]


def _facts(events: list[Event], today: date) -> list[EventFact]:
    return [
        EventFact(
            event_type=e.event_type,
            is_rumor=e.is_rumor,
            materiality=None if e.materiality is None else float(e.materiality),
            sentiment=None if e.sentiment is None else float(e.sentiment),
            reaction_z=None if e.reaction_z is None else float(e.reaction_z),
            age_days=(today - e.last_seen_at.date()).days,
        )
        for e in events
    ]


async def _month_change(session: AsyncSession, instrument: Instrument | None) -> float | None:
    if instrument is None:
        return None
    closes = [float(b.close) for b in await _bars(session, instrument.id, 23)]
    return (closes[-1] / closes[0] - 1) * 100 if len(closes) >= 22 else None


def _rules_json(ev: Evaluation) -> list[dict[str, object]]:
    return [
        {"rule": h.rule.value, "values": {k: round(v, 4) for k, v in h.values.items()}}
        for h in ev.hits
    ]


def _needs_analysis(candidate: EntryCandidate, ev: Evaluation, events: list[Event]) -> bool:
    if not ev.active:
        return False
    if candidate.analyzed_at is None:
        return True
    newer = any(e.last_seen_at > candidate.analyzed_at for e in events)
    return newer or datetime.now(UTC) - candidate.analyzed_at > REANALYZE_AFTER


async def _upsert_signal(
    session: AsyncSession, candidate: EntryCandidate, ev: Evaluation, held: bool
) -> bool:
    cause = DipCause(candidate.cause) if candidate.cause else None
    in_reach = ev.state in (ZoneState.IN_ZONE, ZoneState.BELOW)
    if cause in ENTRY_CAUSES and candidate.thesis_intact and in_reach:
        kind, direction = SignalKind.ENTRY, Direction.UP
    elif cause == DipCause.FUNDAMENTAL and held:
        kind, direction = SignalKind.THESIS_BREAK, Direction.DOWN
    else:
        if ev.state == ZoneState.FAR:
            candidate.signal_id = None  # left the zone: the next visit may signal again
        return False

    signal = await session.get(Signal, candidate.signal_id) if candidate.signal_id else None
    if signal is not None and (signal.status not in OPEN_STATUSES or signal.kind != kind.value):
        return False  # the user already decided on this visit to the zone
    created = signal is None
    if signal is None:
        signal = Signal(
            instrument_id=candidate.instrument_id,
            kind=kind.value,
            source=SignalSource.RULE.value,
            horizon=Horizon.MONTHS.value,
            status=SignalStatus.NEW.value,
            expires_at=datetime.now(UTC) + timedelta(days=EXPIRY_DAYS),
        )
        session.add(signal)
    signal.direction = direction.value
    signal.strength = Decimal(str(round(min(1.0, 0.35 + 0.15 * len(ev.hits)), 4)))
    signal.confidence = None
    signal.entry_low, signal.entry_high = candidate.zone_low, candidate.zone_high
    signal.stop = candidate.stop if kind == SignalKind.ENTRY else None
    signal.rationale = candidate.dip_rationale or ", ".join(h.rule.value for h in ev.hits)
    signal.rationale_i18n = {}
    signal.evidence = [
        {"kind": "indicator", "label": f"rule:{h.rule.value}", "ref_id": h.rule.value}
        for h in ev.hits
    ] + [{**e, "kind": "event"} for e in candidate.dip_evidence]
    signal.is_rumor = False
    await session.flush()
    candidate.signal_id = signal.id
    return created


async def evaluate_instrument(
    session: AsyncSession,
    instrument: Instrument,
    llm: Llm | None,
    rules: EntryRules,
    held: bool,
    benchmark_change: float | None,
    locale: str,
    run: EntryRun,
) -> EntryCandidate | None:
    bars = await _bars(session, instrument.id)
    if not bars:
        return None
    series = compute(
        [float(b.high) for b in bars], [float(b.low) for b in bars], [float(b.close) for b in bars]
    )
    today = bars[-1].day
    events = await recent_events(session, instrument.symbol)
    fundamentals = await session.get(Fundamentals, instrument.id)
    bands = bands_for(fundamentals) if fundamentals is not None else {}
    valuation = bands_json(bands) if bands else {}
    cheap_share = valuation.get("summary") if valuation else None
    ev = evaluate(
        series,
        instrument.kind,
        rules,
        _facts(events, today),
        cheap_share if isinstance(cheap_share, float) else None,
    )
    if ev is None:
        return None
    run.evaluated += 1
    run.active += ev.active

    candidate = await session.get(EntryCandidate, instrument.id)
    if candidate is None:
        candidate = EntryCandidate(instrument_id=instrument.id, source=bars[-1].source)
        session.add(candidate)
    candidate.as_of = today
    candidate.price = bars[-1].close
    candidate.rules = _rules_json(ev)
    candidate.state = ev.state.value if ev.state else None
    candidate.anchor = ev.anchor
    candidate.zone_low, candidate.zone_high = _d(ev.zone_low, "0.01"), _d(ev.zone_high, "0.01")
    candidate.stop, candidate.atr = _d(ev.stop, "0.01"), _d(ev.atr)
    candidate.distance_atr, candidate.drawdown_pct = _d(ev.distance_atr), _d(ev.drawdown_pct)
    candidate.valuation = valuation
    candidate.source = bars[-1].source
    candidate.updated_at = datetime.now(UTC)
    ladder = (
        build_ladder(
            candidate.zone_high,
            candidate.atr,
            candidate.stop,
            rules.ladder.weights,
            rules.ladder.step_atr,
        )
        if candidate.zone_high is not None and candidate.atr
        else []
    )
    candidate.ladder = [{"price": str(lv.price), "weight": str(lv.weight)} for lv in ladder]
    if not ev.active:
        candidate.cause = candidate.thesis_intact = candidate.dip_rationale = None
        candidate.dip_evidence, candidate.dip_model, candidate.analyzed_at = [], None, None

    if llm is not None and _needs_analysis(candidate, ev, events):
        month = (series.close[-1] / series.close[-22] - 1) * 100 if len(series.close) > 22 else None
        facts: dict[str, object] = {
            "as_of": today.isoformat(),
            "price": round(ev.price, 2),
            "drawdown_from_52w_high_pct": round(ev.drawdown_pct, 2),
            "change_1m_pct": None if month is None else round(float(month), 2),
            "benchmark_change_1m_pct": None
            if benchmark_change is None
            else round(benchmark_change, 2),
            "rsi14": None if ev.rsi14 is None else round(ev.rsi14, 1),
            "price_vs_sma200_pct": None
            if not ev.sma200
            else round((ev.price / ev.sma200 - 1) * 100, 2),
            "rules_hit": [h.rule.value for h in ev.hits],
            "valuation_cheap_share": cheap_share,
            "held": held,
        }
        try:
            result = await analyze_dip(llm, instrument, facts, events, locale)
            verdict = result.value
            by_id = {e.id: e for e in events}
            candidate.cause = verdict.cause.value
            candidate.thesis_intact = verdict.thesis_intact
            candidate.dip_rationale = verdict.rationale
            candidate.dip_evidence = [
                {"label": by_id[i].title[:300], "ref_id": str(i)} for i in verdict.evidence
            ]
            candidate.dip_model = result.model
            candidate.analyzed_at = datetime.now(UTC)
            run.analyzed += 1
        except LlmUnavailableError as exc:
            run.errors["dip_analyst"] = str(exc)[:200]

    run.signals += await _upsert_signal(session, candidate, ev, held)
    await session.flush()
    return candidate


async def rebuild_entries(
    session: AsyncSession,
    llm: Llm | None,
    locale: str = "sl",
    benchmark_symbol: str = "SPY",
    rules: EntryRules | None = None,
) -> EntryRun:
    rules = rules or load_rules()
    run = EntryRun()
    held, watched = await user_symbols(session)
    benchmark_change = await _month_change(session, await find_by_symbol(session, benchmark_symbol))
    for symbol in sorted(held | watched):
        instrument = await find_by_symbol(session, symbol)
        if instrument is None:
            continue
        await evaluate_instrument(
            session, instrument, llm, rules, symbol in held, benchmark_change, locale, run
        )
    return run
