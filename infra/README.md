# infra: Docker Compose in konfiguracija

```bash
cp ../.env.example ../.env                                   # izpolni vrednosti
docker compose --env-file ../.env up -d --build              # jedro: postgres, redis, litellm, api, worker, web
docker compose --env-file ../.env --profile broker up -d     # + IB Gateway (Read-Only API), nato IB_GATEWAY_ENABLED=true
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

## Demo sklad za e2e (BL-162)

`docker-compose.demo.yml` je ločen projekt `preza-demo` z lastno bazo, brez LiteLLM, workerja in zunanjih virov. Web teče na `http://127.0.0.1:3100`. `seed_demo` pobriše vse vstope in signale pravil, zato teče samo tu (zahteva `PREZA_DEMO_DB=1`).

```bash
scripts/demo-stack.sh up      # build, zagon, demo podatki
scripts/demo-stack.sh seed    # ponovno naloži demo podatke
scripts/demo-stack.sh stop    # ustavi, baza ostane
# v apps/web:
BASE_URL=http://127.0.0.1:3100 pnpm exec playwright test
```

## Preizkus globoke analize (BL-092)

1. V `.env` izpolni `LITELLM_MASTER_KEY`, `OPENCODE_API_KEY`, `MINIMAX_API_KEY` in imena modelov (`OPENCODE_QUICK_MODEL`, `MINIMAX_MODEL`).
2. `docker compose --env-file ../.env up -d --build` (storitev `agents` je del jedra).
3. V brskalniku odpri instrument (npr. `/i/ASML`, ob odprtju se naložijo sveče) in klikni "Globoka analiza".
4. Ko se konča: `scripts/collect-analysis.sh` zapakira zagon in dnevnike v `infra/analysis-<id>.tar.gz`. Ključe iz dnevnika LiteLLM odstrani, pred pošiljanjem pa arhiv vseeno preglej.
