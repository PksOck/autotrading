# services/api: FastAPI

Domena, podatki in deterministična logika. **Brez LLM klicev v request poti** (ti tečejo v workerju).

## Zagon

```bash
uv sync
uv run uvicorn preza.main:app --reload          # http://localhost:8000/docs
uv run arq preza.worker.WorkerSettings          # worker (potrebuje Redis)
uv run alembic upgrade head                     # migracije (potrebuje Postgres + Timescale)
uv run pytest -q && uv run ruff check . && uv run mypy
uv run python -m preza.cli.export_openapi openapi.json   # nato v apps/web: pnpm gen:api
```

Nastavitve so v `preza/config.py` (okoljske spremenljivke, glej `.env.example`).

## Struktura

```text
preza/
  config.py      nastavitve (pydantic-settings)
  main.py        FastAPI aplikacija
  db.py          SQLAlchemy engine in Base
  worker.py      arq worker in razpored opravil
  domain/        Pydantic modeli (system.py; Signal, Event ... od M1)
  system/        sonde stanja servisov (CMP-02)
  routes/        REST (+ SSE od M4)
  cli/           orodja (izvoz OpenAPI)
migrations/      Alembic (0001: timescaledb + pgvector)
tests/
```

Prihaja po mejnikih: `data/`, `ingest/` (M1), `radar/`, `signals/`, `proposals/` (M2), `entries/` (M3), `options/` (M6). Ref: PLAN.md §5, ADR-0002.

## API (M0)

| Pot | Opis |
|---|---|
| `GET /health` | proces živi |
| `GET /system/status` | stanje Postgres, Redis, LiteLLM, Ollama, IB Gateway, Flex, Telegram (z zakasnitvijo) |
