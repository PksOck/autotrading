# infra: Docker Compose in konfiguracija

| Servis | Slika / vir | Opomba |
|---|---|---|
| `postgres` | `timescale/timescaledb-ha` (pg16 + pgvector) | volumen `data/postgres` |
| `redis` | `redis:7` | vrste in pub/sub |
| `litellm` | `ghcr.io/berriai/litellm` | `litellm/config.yaml`: vloge, proračuni |
| `ib-gateway` | `gnzsnz/ib-gateway` | `READ_ONLY_API=yes`, samo v internem omrežju |
| `api`, `worker`, `claude-runner`, `notify` | lasten Dockerfile (`services/*`) | |
| `web` | lasten Dockerfile (`apps/web`) | |

Ollama teče na ločeni GPU napravi v LAN (`OLLAMA_BASE_URL`). Skrivnosti so v `infra/secrets/` (ni v repoju) ali `.env`.

Ref: ADR-0001, BL-006, BL-011, BL-016, BL-023.
