# AGENTS.md: navodila za AI asistente in razvijalce

Ta datoteka velja za vsakogar, ki spreminja repo: za ljudi, Claude Code, Codex, OpenCode ali kateregakoli drugega agenta.

## 1. Vrstni red branja na začetku seje

1. [SESSIONS.md](./SESSIONS.md): zadnja seja (kje smo ostali, odprta vprašanja).
2. [PLAN.md](./PLAN.md): trenutni mejnik.
3. [BACKLOG.md](./BACKLOG.md): naloge trenutnega mejnika s statusom `next` ali `doing`.
4. Glede na nalogo še [DESIGN.md](./DESIGN.md) (UI), [VOICE.md](./VOICE.md) (besedila, pozivi), [BRAND.md](./BRAND.md) (imena) in ustrezen `ADR-xxxx`.
5. `README.md` mape, v kateri delaš.

## 2. Na koncu seje

- V [SESSIONS.md](./SESSIONS.md) dodaj vnos `S-xxx` (predloga je v datoteki).
- V [BACKLOG.md](./BACKLOG.md) posodobi statuse in dodaj nove naloge z naslednjim prostim `BL-xxx`.
- Če si sprejel odločitev, ki jo bo kdo kasneje vprašal "zakaj?", napiši `docs/adr/ADR-xxxx-*.md`.
- Če si spremenil token, komponento ali zaslon, posodobi DESIGN.md.

## 3. Nespremenljiva pravila (varnost in zaupanje)

1. **Nobenega samodejnega naročila.** Koda, ki odda naročilo, obstaja samo v `services/broker/`, gre skozi `guards.py` in zahteva izrecno potrditev uporabnika ([ADR-0006](./docs/adr/ADR-0006-clovek-vedno-odloci.md)).
2. **IB Gateway je v načinu Read-Only API**, dokler mejnik M7 ni odobren.
3. **LLM nikoli ne računa številk**, ki se prikažejo kot dejstvo (cene, Greeks, donosi, vrednotenja). Te računa deterministična koda, LLM jih samo interpretira.
4. **Govorica (`is_rumor`) nikoli ne postane priporočilo za nakup** brez potrditve iz uradnega vira (EDGAR, sporočilo za javnost).
5. **Vsak podatek ima vir in čas** (`source`, `as_of`), vsak signal ima `rationale` in `evidence`.
6. **Skrivnosti nikoli v repo:** `.env` in `infra/secrets/` sta v `.gitignore`. Primere vrednosti piši v `.env.example`.
7. Vsi LLM klici gredo prek **LiteLLM vlog** (`local-fast`, `local-reason`, `embed`, `cloud-quick`, `cloud-deep`), nikoli neposredno na ponudnika ([ADR-0004](./docs/adr/ADR-0004-llm-vloge-litellm.md)).

## 4. Konvencije kode

| Področje | Pravilo |
|---|---|
| Python | 3.12, `ruff` (lint + format), `mypy --strict` za `domain/`, `pytest`. Pydantic v2 za vse meje (API, LLM izhodi, ingest) |
| TypeScript | strict, ESLint + Prettier, Vitest + Testing Library, Playwright za e2e |
| API tipi | FastAPI → OpenAPI → `openapi-typescript` v `apps/web/lib/api/` (generirano, ne urejaj ročno) |
| Baza | SQLAlchemy 2 + Alembic. Migracija za vsako spremembo sheme |
| Čas | v bazi vedno UTC (`timestamptz`), v UI lokalni čas uporabnika |
| Denar | `Decimal` v Pythonu, v bazi `numeric`. Nikoli `float` za zneske |
| i18n | nobenega besedila v komponentah: vse gre prek `apps/web/messages/{sl,en}.json` (glej VOICE.md §6) |
| Testi | vsak ingest vir ima test pogodbe, vsak agentski izhod ima shemo in test na posnetku podatkov |
| Prevzeta koda | prepisano iz tujih repojev označi v glavi datoteke (`# Prirejeno iz: <repo>/<pot> (<licenca>)`) in dodaj v `NOTICE` |

## 5. Git

- Veje: `feat/<mejnik>-<kratko>`, `fix/...`, `docs/...`. `master` je vedno zelen.
- Commit: [Conventional Commits](https://www.conventionalcommits.org/) z ID-jem naloge: `feat(radar): grozdenje novic [BL-023]`.
- Ena naloga `BL-xxx` je en PR, kadar je le mogoče.
- Veja `legacy` hrani prejšnjo Next.js aplikacijo samo za branje. Vanjo ne commitamo.

## 6. Jezik

- Dokumentacija projekta: **slovenščina**.
- Koda, imena spremenljivk, komentarji v kodi, commit sporočila: **angleščina**.
- Pozivi agentom: angleščina (modeli delujejo zanesljiveje). Povzetki za uporabnika se generirajo v jeziku iz nastavitev (VOICE.md §7).
