# services/api: FastAPI

Domena, podatki in deterministična logika. **Brez LLM klicev v request poti** (ti tečejo v workerju).

## Zagon

```bash
uv sync
uv run uvicorn preza.main:app --reload          # http://localhost:8000/docs
uv run arq preza.worker.WorkerSettings          # worker (potrebuje Redis)
uv run alembic upgrade head                     # migracije (potrebuje Postgres + Timescale)
uv run python -m preza.cli.load_universe       # UCITS ETF-ji iz preza/universe/ucits_etfs.yaml
../../infra/scripts/demo-stack.sh up           # demo podatki v ločenem skladu (:3100); seed_demo briše vstope
TEST_DATABASE_URL=postgresql+asyncpg://... uv run pytest -q   # vključi integracijske teste
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
  data/          pogodba virov, kvote, usmerjevalnik, ponudniki (ibkr, yahoo, stooq)
  broker/        IBKR Flex (samo branje)
  services/      instrumenti, sveče, portfelj, watchlista
  universe/      seznam UCITS ETF-jev
migrations/      Alembic (0001: timescaledb + pgvector)
tests/
```

Prihaja po mejnikih: `radar/`, `signals/`, `proposals/` (M2), `entries/` (M3), `options/` (M6). Ref: PLAN.md §5, ADR-0002.

## API

| Pot | Opis |
|---|---|
| `GET /health` | proces živi |
| `GET /system/status` | stanje Postgres, Redis, LiteLLM, Ollama, IB Gateway, Flex, Telegram (z zakasnitvijo) |
| `GET /instruments?q=` | iskanje instrumentov (simbol, ime) |
| `GET /instruments/{symbol}` | podrobnosti, zadnje zaprtje, dnevna sprememba, izvor podatka |
| `GET /instruments/{symbol}/bars?range=1m\|3m\|1y\|2y\|5y` | dnevne sveče; ob zastarelosti dopolni iz virov (IB Gateway → Yahoo → Stooq) |
| `GET /portfolio` | zadnji posnetek pozicij iz IBKR Flex, teže, gotovina, zadnja sinhronizacija |
| `POST /portfolio/sync` | postavi sinhronizacijo Flex v vrsto (409, če Flex ni nastavljen) |
| `GET/POST /watchlist`, `PATCH/DELETE /watchlist/{id}` | watchlista z dvema ravnema |
