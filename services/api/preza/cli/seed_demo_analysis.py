"""Demo deep analyses (M4) for SCR-06: one finished run, one still running.

The texts imitate what the agents write; numbers that the screen shows as facts come
from the stored snapshot, not from these texts.
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, select

from preza.db import get_sessionmaker
from preza.models import AnalysisRun, AnalysisStep, Instrument

SOURCE = "demo"

MARKET = """### Tržna slika ASML
- Cena je pod 50- in 200-dnevnim povprečjem; trend je od poletja navzdol, zadnja dva tedna se je umiril.
- RSI(14) je blizu spodnje meje nevtralnega območja, prodajni pritisk pojenja.
- MACD histogram se zožuje, kar pogosto pomeni konec padajočega zamaha, ne pa še obrata.
- Volumen pri zadnjih padcih je bil nižji kot pri julijskem padcu.

**Povzetek:** tehnično gre za umirjanje po padcu, ne za potrjen obrat. Vstop po delih je smiselnejši od enkratnega."""

NEWS = """### Novice in makro
- Uradno sporočilo za javnost: nov večji naročilni posel za EUV opremo (vir: sporočilo za javnost, 18. 10.).
- [NEPOTRJENO] Na Redditu se širi govorica o prevzemu manjšega dobavitelja; uradnega vira ni, zato je ne upoštevam kot dejstvo.
- Sektor polprevodniške opreme je v zadnjem mesecu padel skupaj s trgom; razlog so izvozne omejitve in previdnejše napovedi kupcev.

**Povzetek:** padec je predvsem sektorski. Edina podjetniška novica je pozitivna in uradna."""

FUNDAMENTALS = """### Temeljni podatki
- Vrednotenje (P/E, EV/EBIT) je pod 5-letnim mediano, FCF donos nad njo (vir: Finnhub, posnetek ob analizi).
- Bruto marža ostaja visoka, bilanca brez neto dolga.
- Odvisnost od nekaj velikih kupcev ostaja glavno tveganje.

**Povzetek:** podjetje je na zgodovinsko nižjem vrednotenju brez znakov poslabšanja poslovanja."""

BULL = """Bull: Padec je sektorski, ne podjetniški. Naročila so uradno potrjena, vrednotenje je pod 5-letnim povprečjem, bilanca je čista. Za dolgoročnega vlagatelja je to cona, kjer se splača začeti graditi pozicijo."""

BEAR = """Bear: Trend je še vedno navzdol in izvozne omejitve se lahko zaostrijo. Nižje vrednotenje je lahko upravičeno, če kupci zamaknejo naročila. Ne bi lovil dna pred naslednjim četrtletnim poročilom."""

PLAN = """### Načrt raziskovalnega vodje
Argument bull strani je močnejši pri temeljih, bear pri času vstopa. Priporočam postopen vstop: prvi del zdaj, preostanek po potrditvi, da cena drži nad dnom zadnjih tednov ali po poročilu."""

TRADER = """### Predlog trgovca
Postopen nakup v treh delih, prvi takoj, drugi in tretji ob nadaljnjem padcu ali po poročilu. Stop pod zadnjim dnom.

FINAL TRANSACTION PROPOSAL: **OVERWEIGHT**"""

AGGRESSIVE = """Aggressive: Vrednotenje je redko tako ugodno; večji prvi del je upravičen."""
CONSERVATIVE = """Conservative: Pozicija v ASML je že del portfelja. Povečanje naj ostane majhno, dokler trend ne obrne."""
NEUTRAL = """Neutral: Postopen vstop z jasnim stopom uravnoteži obe strani. Velikost naj sledi lestvici iz Vstopov."""

DECISION = """### Končna odločitev
**Rating**: Overweight

Povečaj pozicijo postopoma, v skladu z lestvico vstopov. Razlogi: sektorski padec ob nedotaknjenih temeljih, uradno potrjena naročila, vrednotenje pod 5-letnim povprečjem. Govorice o prevzemu niso del utemeljitve.

Tveganja: zaostritev izvoznih omejitev, zamik naročil velikih kupcev, nadaljevanje padajočega trenda."""

FINISHED_STEPS: list[tuple[str, str, str | None, str]] = [
    ("system", "status", "started", ""),
    ("market", "tool", "get_verified_market_snapshot(curr_date=…, look_back_days=30)", ""),
    ("market", "tool", "get_indicators(indicator=rsi, look_back_days=30)", ""),
    ("market", "tool", "get_indicators(indicator=macdh, look_back_days=30)", ""),
    ("news", "tool", "get_news(start_date=…, end_date=…)", ""),
    ("news", "tool", "get_global_news(look_back_days=7, limit=10)", ""),
    ("fundamentals", "tool", "get_fundamentals(curr_date=…)", ""),
    ("market", "report", "market_report", MARKET),
    ("news", "report", "news_report", NEWS),
    ("fundamentals", "report", "fundamentals_report", FUNDAMENTALS),
    ("bull", "debate", "investment_debate_state", BULL),
    ("bear", "debate", "investment_debate_state", BEAR),
    ("research_manager", "report", "investment_plan", PLAN),
    ("trader", "report", "trader_investment_plan", TRADER),
    ("aggressive", "debate", "risk_debate_state", AGGRESSIVE),
    ("conservative", "debate", "risk_debate_state", CONSERVATIVE),
    ("neutral", "debate", "risk_debate_state", NEUTRAL),
    ("portfolio_manager", "decision", None, DECISION),
    ("system", "status", "done", ""),
]

RUNNING_STEPS = FINISHED_STEPS[:8]

# Shape of the decision card (BL-089); the control numbers here are demo values.
CARD = {
    "rating": "Overweight",
    "control": {
        "score": 0.21,
        "coverage": 1.0,
        "components": {"valuation": 0.55, "technical": -0.5, "risk": 0.2},
        "weights": {"valuation": 0.4, "technical": 0.15, "risk": 0.15},
        "implied_rating": "Overweight",
    },
    "confidence": "normal",
    "conviction": 6,
    "size_class": "normal",
    "upgrade_if": [
        "Cena zapre nad 200-dnevnim povprečjem in tam ostane dva tedna.",
        "Četrtletno poročilo potrdi rast naročil.",
    ],
    "downgrade_if": [
        "Zaostritev izvoznih omejitev za EUV opremo.",
        "Cena pade pod dno zadnjih tednov.",
    ],
    "delta_note": None,
    "previous": None,
}


def _snapshot(symbol: str, as_of: date) -> dict[str, object]:
    """Same bars and fundamentals as seed_demo, so the outlook (ADR-0014) has data."""
    from preza.cli.seed_demo import STOCKS, demo_bars, demo_fundamentals

    price = next(p for s, _, _, p in STOCKS if s == symbol)
    current, history = demo_fundamentals(symbol, as_of)
    return {
        "as_of": as_of.isoformat(),
        "bars": [
            {
                "day": b.day.isoformat(),
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": b.volume,
            }
            for b in demo_bars(symbol, price)
        ],
        "bars_source": SOURCE,
        "fundamentals": current,
        "fundamentals_history": history,
        "fundamentals_source": SOURCE,
        "fundamentals_as_of": as_of.isoformat(),
    }


async def seed_analyses() -> None:
    async with get_sessionmaker()() as session:
        await session.execute(
            delete(AnalysisRun).where(AnalysisRun.models["quick"].astext == SOURCE)
        )
        today = datetime.now(UTC).date()
        now = datetime.now(UTC)
        runs = [
            ("ASML", "done", FINISHED_STEPS, now - timedelta(hours=3)),
            ("NVDA", "running", RUNNING_STEPS, now - timedelta(minutes=4)),
        ]
        for symbol, status, steps, started in runs:
            instrument = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
            if instrument is None:
                continue
            done = status == "done"
            run = AnalysisRun(
                instrument_id=instrument.id,
                engine="tradingagents",
                trade_date=today,
                status=status,
                locale="sl",
                rating="Overweight" if done else None,
                decision=DECISION if done else None,
                reports=(
                    {
                        "market_report": MARKET,
                        "news_report": NEWS,
                        "fundamentals_report": FUNDAMENTALS,
                        "investment_plan": PLAN,
                        "trader_investment_plan": TRADER,
                        "final_trade_decision": DECISION,
                    }
                    if done
                    else {"market_report": MARKET}
                ),
                caveats=[],
                card=CARD if done else None,
                snapshot=_snapshot(symbol, today),
                models={"quick": SOURCE, "deep": SOURCE},
                created_at=started,
                started_at=started,
                finished_at=started + timedelta(minutes=11) if done else None,
            )
            session.add(run)
            await session.flush()
            for seq, (agent, kind, title, content) in enumerate(steps, 1):
                session.add(
                    AnalysisStep(
                        run_id=run.id,
                        seq=seq,
                        agent=agent,
                        kind=kind,
                        title=title,
                        content=content,
                        created_at=started + timedelta(seconds=35 * seq),
                    )
                )
        await session.commit()
    print("demo analyses: ASML (done), NVDA (running)")
