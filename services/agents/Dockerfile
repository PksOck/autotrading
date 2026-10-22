# Built from the repo root: the agents package depends on services/api by path.
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir "uv>=0.9,<1"
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app/services/agents

COPY services/api /app/services/api
COPY services/agents/pyproject.toml services/agents/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY services/agents .
RUN uv sync --frozen --no-dev

ENV PATH="/app/services/agents/.venv/bin:$PATH"
CMD ["arq", "preza_agents.worker.WorkerSettings"]
