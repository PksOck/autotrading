# Preža

> *Biti na preži*: opazovati, čakati na pravi trenutek.

Interna platforma za **zaznavanje naložbenih priložnosti** v ameriških delnicah in ETF-jih. Spremlja novice, filinge in špekulacije, prepoznava dobre (ponovne) vstopne točke za dolgoročne pozicije in s pomočjo AI agentov pripravi utemeljeno analizo. Odločitev in naročilo pri Interactive Brokers ostaneta vedno tvoja.

[![CI](https://github.com/PksOck/autotrading/actions/workflows/ci.yml/badge.svg)](https://github.com/PksOck/autotrading/actions/workflows/ci.yml)

**Različica: 0.2.0 — razvojna izdaja za testiranje.** [Izdaje](https://github.com/PksOck/autotrading/releases) · [Spremembe](CHANGELOG.md) · [Varnost](SECURITY.md) · [Razvoj in verzioniranje](CONTRIBUTING.md)

## Kaj je na voljo

Radar, vstopne cone, signali in predlogi, globoke analize, portfelj/watchlista z nastavljivimi stolpci, dividendni koledar, teze, študija shranjenih signalov, procesni urniki in lastniška prijava. UI je slovenski/angleški s svetlo/temno temo. IBKR povezava ostaja read-only; naročil ne oddajamo samodejno.

YTD prikazuje cenovni premik trenutnih količin iz enega preverljivega zajema, ne celotnega donosa računa. Sintetični demo in dejanski podatki so ločeni; vrzeli ostanejo vidne. Še odprti so razširjeno spremljanje lastnih idej, merila tez, laboratorij finančne zgodovine ter dejanska dokazila Flex/FX/SMTP/backup. Trenutno stanje določata [PLAN](PLAN.md) in [BACKLOG](BACKLOG.md), ne oznaka izdaje sama.

## Zagon in dostop

- **Pregledni demo:** ločen sklad na127.0.0.1:3100 s sintetičnimi podatki. [Navodila](infra/README.md). `seed_demo` briše demo zapise; nikoli ga ne uporabi na zasebni bazi.
- **Zasebna namestitev:** [koraki prijave, Docker in HTTPS/Tailscale](docs/implementation/2026-11-02-zasebni-dostop-navodila.md). Ločen overlay3300 ohrani že zagnani3000. Geslo/hash sodi v lokalno ignorirano konfiguracijo. Produkcija brez nastavljenega lastnika in HTTPS izvora ostane zaklenjena.
- **Razvoj:** v services/api `uv sync --frozen` in `uv run uvicorn preza.main:app --reload`; v korenu `pnpm install --frozen-lockfile` in `pnpm dev`. Podrobnosti imajo README posameznih storitev.

Tailscale Serve naj posreduje na loopback; ne odpiraj WEB_BIND=0.0.0.0 kot nadomestila za pravilno zaščito. Objavljena GitHub koda ne zamenja že zagnanega dema ali zasebne baze.

---

## Kje kaj najdeš

### Pravila projekta (beri najprej)

| Datoteka | Vsebina | Kdaj jo bereš |
|---|---|---|
| [BRAND.md](./BRAND.md) | ime, pozicioniranje, načela, pomen barv, imena modulov | ko poimenuješ nekaj novega |
| [VOICE.md](./VOICE.md) | ton, slovenska pravila, glosar SL/EN, formati števil in datumov, i18n | ko pišeš besedilo v UI, obvestila ali pozive agentom |
| [DESIGN.md](./DESIGN.md) | design tokeni (svetla/temna), tipografija, komponente, zasloni `SCR-xx`, stanja, dostopnost | ko gradiš UI |
| [PLAN.md](./PLAN.md) | arhitektura, cevovodi, LLM vloge, mejniki `M0`–`M7` | ko se odločaš, kaj in kako graditi |
| [BACKLOG.md](./BACKLOG.md) | naloge `BL-xxx` po mejnikih, s statusom | ko izbiraš naslednje delo |
| [SESSIONS.md](./SESSIONS.md) | dnevnik delovnih sej `S-xxx`: kaj je bilo narejeno in odločeno | na začetku in koncu vsake seje |
| [AGENTS.md](./AGENTS.md) | navodila za AI asistente in razvijalce: konvencije, vrstni red branja | vedno, preden spreminjaš repo |

### Odločitve in raziskave

- [`docs/adr/`](./docs/adr/): arhitekturne odločitve `ADR-xxxx` (zakaj je nekaj tako, kot je)
- [`docs/research/`](./docs/research/): analize odprtokodnih kandidatov in podrobna zasnova (vir za PLAN)

### Koda

```text
apps/web/              Next.js frontend (SCR-xx zasloni, i18n sl/en, svetla/temna tema)
services/api/          FastAPI: domena, podatki, Radar, vstopi, signali, opcije, portfelj
services/agents/       agentski cevovodi (TradingAgents adapter, ETF, padec, opcije, teze)
services/api/preza/broker/  IBKR Flex read-only uvoz
services/api/preza/notify/  obvestila in Telegram
infra/                 Docker Compose, LiteLLM, IB Gateway, Postgres
design/                povezave na UI prototipe (Artifact platno) in izvozi
```

Vsaka mapa ima svoj `README.md` z namenom, mejami in povezavami na `BL-xxx`.

---

## Konvencije sklicevanja

| Predpona | Pomen | Primer | Kje živi |
|---|---|---|---|
| `M0`–`M7` | mejnik | `M2 Radar` | PLAN.md |
| `BL-xxx` | naloga v backlogu | `BL-021` | BACKLOG.md |
| `ADR-xxxx` | arhitekturna odločitev | `ADR-0004` | docs/adr/ |
| `SCR-xx` | zaslon v UI | `SCR-02 Radar` | DESIGN.md + platno |
| `CMP-xx` | UI komponenta | `CMP-03 SignalCard` | DESIGN.md |
| `S-xxx` | delovna seja | `S-001` | SESSIONS.md |

Commit sporočila in PR-ji navajajo ID-je, npr. `feat(radar): triaža novic z Ollamo [BL-022]`.

**Opozorilo:** sistem ne daje naložbenih nasvetov in ne oddaja naročil samodejno. Vsi signali so raziskovalni pripomočki.
