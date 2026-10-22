# ADR-0002: Python backend, Next.js frontend
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-001

## Kontekst
Ključne knjižnice so v Pythonu: TradingAgents (LangGraph), ib_async, TA-Lib, Claude Agent SDK (Python), LiteLLM. Prejšnja aplikacija (veja `legacy`) je bila Next.js + TypeScript.

## Odločitev
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, arq (vrste na Redisu), Pydantic v2.
- **Frontend:** Next.js 16 (App Router), React 19, Tailwind 4, shadcn/ui, TanStack Query, lightweight-charts, trading-signals, next-intl.
- **Pogodba:** OpenAPI iz FastAPI → generirani TS tipi (`openapi-typescript`).
- **Baza:** Postgres 16 + TimescaleDB (svečke) + pgvector (novice).

## Posledice
- Dva jezika. Meja je jasna (OpenAPI), tipi so generirani.
- Indikatorji obstajajo dvakrat (TA-Lib v backendu, trading-signals v frontendu), zato je potreben test enakosti (BL-060).

## Zavrnjene možnosti
- **Vse v TypeScriptu:** ni TradingAgents, ib_async ali Agent SDK ekvivalentov enake zrelosti.
- **Streamlit/Gradio UI:** premalo nadzora nad UX in premalo profesionalen videz.
