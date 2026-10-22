# Preža

> *Biti na preži*: opazovati, čakati na pravi trenutek.

Interna platforma za **zaznavanje naložbenih priložnosti** v ameriških delnicah in ETF-jih. Spremlja novice, filinge in špekulacije, prepoznava dobre (ponovne) vstopne točke za dolgoročne pozicije in s pomočjo AI agentov pripravi utemeljeno analizo. Odločitev in naročilo pri Interactive Brokers ostaneta vedno tvoja.

**Stanje:** faza 0, pravila in zasnova. Koda še ne obstaja. Prejšnja Next.js aplikacija je na veji [`legacy`](https://github.com/PksOck/autotrading/tree/legacy).

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

### Koda (struktura je pripravljena, vsebina pride po mejnikih)

```text
apps/web/              Next.js frontend (SCR-xx zasloni, i18n sl/en, svetla/temna tema)
services/api/          FastAPI: domena, podatki, Radar, vstopi, signali, opcije, portfelj
services/agents/       agentski cevovodi (TradingAgents adapter, ETF, padec, opcije, teze)
services/claude_runner/ Claude Agent SDK servis (naročniški kredit)
services/broker/       IBKR: ib_async + Flex, varovala
services/notify/       Telegram bot
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
