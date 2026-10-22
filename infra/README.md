# infra: Docker Compose in konfiguracija

```bash
cp ../.env.example ../.env            # izpolni vrednosti
docker compose up -d --build          # jedro: postgres, redis, litellm, api, worker, web
docker compose --profile broker up -d # + IB Gateway (M1, Read-Only API)
docker compose logs -f api
```

| Servis | Slika / vir | Opomba |
|---|---|---|
| `postgres` | `timescale/timescaledb-ha:pg17` (pg + Timescale + pgvector) | volumen `pgdata` |
| `redis` | `redis:7-alpine` | vrste in pub/sub |
| `litellm` | `ghcr.io/berriai/litellm:main-stable` | `litellm/config.yaml`: 5 vlog, fallbacki (ADR-0004) |
| `api` | `services/api/Dockerfile` | ob zagonu `alembic upgrade head` |
| `worker` | ista slika kot `api` | `arq preza.worker.WorkerSettings` |
| `web` | `apps/web/Dockerfile` (kontekst = koren repoja) | objavljen samo na `WEB_BIND` (privzeto 127.0.0.1) |
| `ib-gateway` | `ghcr.io/gnzsnz/ib-gateway:stable`, profil `broker` | `READ_ONLY_API=yes`, brez objavljenih portov |

Ollama teče na ločeni GPU napravi v LAN (`OLLAMA_BASE_URL`), model `LOCAL_MODEL` (Qwen 3.8 27B, 4-bit). Skrivnosti so samo v `.env` (ni v repoju).

`claude-runner` (M4) in `notify` (Telegram, M2) se dodata v svojih mejnikih.

Ref: ADR-0001, BL-006, BL-011, BL-016, BL-023.
