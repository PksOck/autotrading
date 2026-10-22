# SESSIONS.md: dnevnik delovnih sej

Najnovejša seja je na vrhu. Vsaka seja ima ID `S-xxx`, datum, cilj, rezultat, odločitve in odprta vprašanja. Predloga je na dnu.

---

## S-002 · 2026-10-22 · Napreden UX, ročni predlogi, M0

**Cilj:** odločitve iz pregleda prototipov, napreden React UX, ročni predlogi, mejnik M0.

**Narejeno:**
- Pravila: DESIGN §8 (motion sistem MO-01–MO-10), §9 (povezovanje LX-01–LX-08), §10 (pregledi OV-01–OV-07), §11 (ročni predlogi, SCR-12, CMP-30). ADR-0008 (UCITS), ADR-0009 (Motion UX). Ime Preža in model Qwen 3.8 27B (4-bit) potrjena.
- **M0 zgrajen:**
  - `services/api`: FastAPI, `/health`, `/system/status` (sonde za 7 servisov s časovno omejitvijo), Alembic (Timescale + pgvector), arq worker, izvoz OpenAPI. 6 testov, ruff, mypy strict.
  - `apps/web`: Next.js 16 lupina (stranski meni z drsnim indikatorjem, spodnja navigacija na telefonu, glava s stanjem sistema), svetla/temna/sistemska tema brez utripa, SL/EN (next-intl, 220+ ključev, preverjanje enakosti), ⌘K paleta, kukalo v URL, EntityLink s predogledom, navzkrižno poudarjanje, AnimatedNumber, Treemap, PulseTimeline, Funnel, RegimeStrip, Sparkline, kartice signalov z razširitvijo in razveljavitvijo, obrazec za ročne predloge, stran `/ux`. 9 enotskih testov, 6 e2e testov (Playwright, namizje + telefon).
  - `infra`: Docker Compose (postgres, redis, litellm, api, worker, web, ib-gateway v profilu `broker`), LiteLLM 5 vlog s fallbacki.
  - CI (GitHub Actions): API, web (i18n, tipi API, lint, tipi, testi, build, e2e), preverjanje compose.
- Najdena in popravljena napaka hidracije: Node in Chromium različno ločita 4-mestna števila v slovenščini, zato `useGrouping: "always"`.

**Odločitve (uporabnik):** UCITS ETF-ji, ime Preža, Qwen 3.8 27B 4-bit, napreden React UX z animacijami in povezanimi pogledi, ročni predlogi v analizo.

**Odprto:**
- Celoten `docker compose up` v tem okolju ni bil preizkušen (ni Docker daemona); posamezni servisi, build in e2e so preizkušeni (BL-160).
- Imena modelov OpenCode Go v `.env` preveri na `/models` (BL-011).
- BL-012, BL-013, BL-016 so na tvoji strani (GPU naprava, Claude kredit, Tailscale).

**Naslednji korak:** BL-160 (zagon na tvojem strežniku), nato M1: Flex, IB Gateway, svečke, Portfelj (SCR-08), Instrument (SCR-05).

---

## S-001 · 2026-10-22 · Analiza, zasnova, pravila, prototipi

**Cilj:** izbrati osnovo iz odprtokodnih repojev, zasnovati rešitev, postaviti pravila projekta in UI prototipe.

**Narejeno:**
- Analiza 6 kandidatov: LEAN, TradeMaster, trading-signals, TradingAgents, Vibe-Trading in IBKR API-ji → [`docs/research/2026-10-22-analiza-kandidatov.md`](./docs/research/2026-10-22-analiza-kandidatov.md).
- Podrobna zasnova in seznam prevzemov → [`docs/research/2026-10-22-zasnova-resitve.md`](./docs/research/2026-10-22-zasnova-resitve.md).
- Prejšnja koda premaknjena na vejo `legacy`. Na delovni veji je nova struktura monorepa.
- Pravila: README, AGENTS, BRAND, VOICE, DESIGN, PLAN, BACKLOG, SESSIONS, ADR-0001 do ADR-0007.
- Osnova i18n: `apps/web/messages/sl.json` in `en.json`.
- UI prototipi na Artifact platnu (BL-003): 7 zaslonov + tokeni, preklop teme in jezika, povezave med zasloni. Kopija v `design/canvas/`.
- Pregled starega projekta `PksOck/trading-list` (PHP): samo izkušnje in model podatkov → [`docs/research/2026-10-22-trading-list-prevzem.md`](./docs/research/2026-10-22-trading-list-prevzem.md). Novi BL-018, BL-032, BL-033, BL-088, BL-089.

**Odločitve (uporabnik):**
- Dolgoročno trgovanje, občasno kratkoročno in opcije. Podatki v realnem času niso potrebni.
- Fokus: priložnosti iz novic in špekulacij ter dobre (ponovne) vstopne točke, za delnice in ETF-je.
- Docker lokalno. GPU naprava v LAN s 24 GB VRAM, Qwen 3.8 27B (4-bit).
- Naročnine: Claude **Pro**, OpenAI, OpenCode. IBKR PRO.
- Radar v treh pogledih: Novi predlogi (širše), Watchlista, Portfelj.
- Obvestila prek Telegrama.
- Slovenščina privzeto, preklop na angleščino. Svetla in temna tema.
- Stari projekt ni predloga: gradimo na novo in bolje.

**Odprto:**
- Točna verzija lokalnega modela in hitrost triaže (BL-012).
- Višina Claude Pro Agent SDK kredita (BL-013).
- Delovno ime "Preža": potrdi ali zamenjaj (BRAND.md §1).
- Pregled prototipov (BL-004).
- Dostopnost ameriških ETF-jev za EU malega vlagatelja (BL-018). Prototipi zato uporabljajo UCITS ETF-je (VWRA, EQQQ, IUES).

**Naslednji korak:** BL-004 (pregled prototipov), nato M0 (BL-006 do BL-016).

---

## Predloga

```markdown
## S-xxx · LLLL-MM-DD · <kratek cilj>

**Cilj:**
**Narejeno:** (z referencami BL-xxx, commit/PR)
**Odločitve:** (+ ADR-xxxx, če nastane)
**Odprto:**
**Naslednji korak:**
```
