# PLAN.md

Povzetek sprejetega načrta. Podrobna utemeljitev je v [`docs/research/2026-10-22-zasnova-resitve.md`](./docs/research/2026-10-22-zasnova-resitve.md), primerjava kandidatov v [`docs/research/2026-10-22-analiza-kandidatov.md`](./docs/research/2026-10-22-analiza-kandidatov.md), izkušnje iz starega projekta v [`docs/research/2026-10-22-trading-list-prevzem.md`](./docs/research/2026-10-22-trading-list-prevzem.md).

## Trenutno: različica0.2.0 in zasebni dostop (S-030)

[Objavljena predizdaja v0.2.0](https://github.com/PksOck/autotrading/releases/tag/v0.2.0) ima uspešen celotni CI in preverjanje taga. [Plan različic/bcrypt](./docs/superpowers/plans/2026-11-02-razlicice-in-bcrypt.md), [CHANGELOG](./CHANGELOG.md) in [navodila izdaj](./CONTRIBUTING.md) povezujejo VERSION, pakete, UI/health in preverjanje tagov. Zasebna namestitev3300 z HTTPS8443 je zagnana in anonimni dostop zaklenjen. Lastnik ohrani trenutna pravila Tailscale, zato omrežni dostop ni omejen samo na en telefon. Dejanska prijava in prvi uvoz podatkov sta uporabnikov sprejemni korak.

## Predhodno: YTD, lastniška prijava in GitHub predaja (S-029)

Izvedeni BL-234/235/237/238: [YTD SPEC](./docs/superpowers/specs/2026-11-02-ytd-podatki-in-predaja-spec.md), [varnostni SPEC](./docs/superpowers/specs/2026-11-02-zasebni-dostop-design.md), [dokazi in sprejemni pregled](./docs/implementation/2026-11-02-ytd-varnost-predaja.md). Številčni demo YTD ima izrecen sintetični vir. Živi IBKR zajem ni potrjen, potrebuje read-only Gateway in pravice; FX ostaja dokazna omejitev. GitHub master push je odobren; :3000 ni. BL-239 ostaja operativno odprt do priklopa lokalne konfiguracije gesla in testa dostopa. V S-030 uporabnik za zdaj ohrani trenutna Tailscale pravila, zato se ozka politika S26 ne uveljavi; obstoječi Serve443→8090 se ohrani.

## Predhodno: poenostavljena avtomatika in strnjen portfelj (S-028)

[Plan BL-232/233](./docs/superpowers/plans/2026-11-01-enostavna-avtomatika.md) vključuje popravke SOL/Astra pregleda. [Dokazi](./docs/implementation/2026-11-02-zakljucek-avtomatika-portfelj.md) ločijo izvedeno UI/varovala od še nedostopnega številčnega produkcijskega YTD. BL-234 potrebuje dokazljivo prilagojeno zgodovino cen; isti ponudnik ni dokaz. BL-235 je ločen predlog jasnejših opozoril o zastarelosti. Samo3100,3000 ostane nespremenjen.

## Predhodno: prostornost, Predlogi in dividendni koledar (S-027)

[SPEC](./docs/superpowers/specs/2026-11-01-prostornost-in-dividendni-koledar-spec.md) in [plan](./docs/superpowers/plans/2026-11-01-prostornost-in-dividendni-koledar.md) pokrivata BL-229/230: široke tabele, filtre Predlogov, zložljivo zalogo, dnevno oceno s preverljivo valuto in mesečni/letni dividendni koledar. [Dokazi in meje](./docs/implementation/2026-11-01-prostornost-in-koledar-dokazi.md). Samo demo :3100, :3000 ostane nespremenjen. [Laboratorij SPEC](./docs/superpowers/specs/2026-11-01-laboratorij-financnih-kazalnikov-spec.md) je pripravljen za naslednji modul: uporabnik želi oboje, najprej zgodovinske kazalnike in potem testiranje pravil. BL-231 je pripravljena specifikacija, implementacija je še next. BL-225/226/227 in spodnji pogoji backup/Flex/SMTP ostajajo odprti.

## Predhodno: uporabniški UX krog spremljanja in pojasnil (S-026)

Po novih posnetkih uporabnika je izveden ozek BL-223: graf desno ob identiteti Pozicij/Watchliste, običajne namizne vrstice z 217,25 na 129 px, ohranjen dejanski razpon in dostopen vir/čas. [Dokazi S-025](./docs/implementation/2026-10-30-kompaktni-portfelj-in-ux-plan.md) ločijo ta delujoči popravek na :3100 od novih načrtovanih funkcij.

Pripravljena sta [SPEC](./docs/superpowers/specs/2026-10-30-spremljanje-in-pojasnila-ux-spec.md) in [izvedbeni plan](./docs/superpowers/plans/2026-10-30-spremljanje-in-pojasnila-ux.md) za BL-224–228: pomoč ob naslovih/manj stalnih opisov, osebno spremljanje iz drugih strani **in lastne ideje brez analize**, uporabne Teze ter več meril glede na trajanje investicije. Uporabnik je oba poudarjena obsega potrdil. T1/BL-224 je izveden: pomoč na vseh straneh in v predogledu, lokalni datum v nogi, strnjen manjkajoči makro kontekst ter jasna ločitev metod. [Dokazi S-026](./docs/implementation/2026-10-31-pomoc-in-hierarhija-podatkov.md). T2/BL-228 je prav tako preverjen: ločeni metodi, pošteno neoznačena zgodovina in noben backfill ([dokazi](./docs/implementation/2026-10-31-metode-uspesnosti.md), ADR-0025). Naslednji je celoten tok idej/članstva T3–T4. Osebno spremljanje in nove Teze še niso izvedeni. Stara globalna statistika se ne razširi ali prepiše tiho; meritve Tez potrebujejo ločen podatkovni SPEC. BL-222/backup in preostale podatkovne/lastniške vrzeli ostajajo odprti; :3000 ostane nespremenjen.

## Predhodno: zaključena Radar/idempotenca in naslednji SPEC (S-024)

BL-221/R1 in BL-204 sta izvedena v pregledni veji in samo na :3100: članstvo Radarja pred omejitvijo rezultatov, trajna oddaja predloga čez reload/izgubljen odgovor, varovanje novega osnutka drugega zavihka ter Back/fokus. [Dokazi S-024](./docs/implementation/2026-10-30-radar-in-trajna-oddaja-dokazi.md) vsebujejo API 597 + 1 pogojni skip, web 180 in Playwright 76 + 10 namernih skipov; končni povezani pregled PASS. To ne zapre A3/A5, za katera je pripravljena [tehnična raziskava](./docs/implementation/2026-10-30-lastnistvo-raziskava.md).

Naslednji neodvisni izvedbeni korak je BL-222: [SPEC varnostnih kopij v Nastavitvah](./docs/superpowers/specs/2026-10-30-nastavitve-varnostnih-kopij-spec.md) in [plan](./docs/superpowers/plans/2026-10-30-nastavitve-varnostnih-kopij.md) imata dokumentarni neodvisni PASS. Pot/pogostost/hramba bodo nastavljivi; isti disk je dovoljen z jasno omejitvijo, privzeto izklopljeno/neizbrano. Funkcija še ni implementirana. [Prejeti odgovori in odprto delo](./docs/implementation/2026-10-30-odprto-in-vprasanja.md): razširjenega Flex še ni, SMTP predal šele načrtovan, lokacija kopij še neizbrana. Pred prvo živo migracijo ostaja dejanski restore dokaz in nova izrecna potrditev :3000.

## Predhodni neposredni dodatni krog po Claudovem pregledu (S-023)

[Izvedbeni SPEC dodatnega kroga](./docs/superpowers/specs/2026-10-30-dodatni-krog-claude-spec.md) in [izvedbeni plan](./docs/superpowers/plans/2026-10-30-dodatni-krog-claude-izvedba.md) sta za neposredni BL-218 izvedena: D1/A1/A2/A4/U1/U2 in dodatna dirka A4-1 imajo končni neodvisni PASS ter [dokaze S-023](./docs/implementation/2026-10-30-izvedba-dodatnega-kroga.md). Vse ostale pripombe so vezane na nove pogojne NEXT-SPEC S-B/S-F5/S-G1/S-C/S-H. Združitev in namestitev sta ločena koraka; :3000 še vedno zahteva novo izrecno potrditev in backup/restore pred živo migracijo.

[Enotni načrt odprtih sklopov](./docs/superpowers/plans/2026-10-30-zakljucevanje-odprtih-sklopov.md) povezuje vse odprte/delne/odložene BL naloge v pakete A–K. [Register naslednjih SPEC](./docs/superpowers/specs/2026-10-30-odprti-sklopi-priprava-spec.md) povezuje pet pripravljenih pogojnih dokumentov; dejanski Flex, FX in živost delavcev potrebujejo dodatne dokaze pred odvisno izvedbo. Sledijo podatkovni viri, procesi, povezave in UX. M6/M7 ter polni backtester so ločeni od osnovne izdaje.

Pregledna nadgradnja in uporabniške dopolnitve so na ločenem demu :3100. **:3000 ostane nespremenjen do nove izrecne potrditve uporabnika.** Aktualni obseg/testi so v [dopolnitvah po pregledu](./docs/implementation/2026-10-29-dopolnitve-po-pregledu.md); naslednje naloge BL-193/194, BL-202–205 in BL-211/212. Pripravljene Docker slike niso dovoljenje za zagon na :3000.

## 1. Cilj

Zaznati **(a) priložnost iz novic, filingov in špekulacij** ter **(b) dobro (ponovno) vstopno točko** za kakovostne delnice in ETF-je. Uporabnik je dolgoročni vlagatelj pri IBKR, ki občasno kupi kratkoročno ali uporabi opcije. Podatki v realnem času niso potrebni.

## 2. Okvirni pogoji (potrjeno v S-001)

| Tema | Odločitev |
|---|---|
| Gostovanje | Docker Compose lokalno, dostop prek Tailscale ([ADR-0001](./docs/adr/ADR-0001-docker-lokalno.md)) |
| Lokalni LLM | ločena naprava v LAN, **24 GB VRAM**, Ollama, **Qwen 3.8 27B, 4-bitna kvantizacija** (potrjeno) |
| Oblačni LLM | **MiniMax** (API ključ), **OpenCode Go** (javni modeli, API ključ), **OpenAI** naročnina (ChatGPT prijava v TradingAgents). **Claude ni v avtomatiziranem cevovodu** (brez API, potrjeno v S-003) |
| Omrežje | Tailscale je nameščen na vseh napravah (strežnik, GPU naprava, telefon) |
| Broker | IBKR PRO: Flex Web Service + IB Gateway (Read-Only API) + ib_async |
| Univerzum | trije pogledi: **Novi predlogi** (S&P 500 + Nasdaq 100 + izbrani ETF-ji), **Watchlista**, **Portfelj** |
| Obvestila | Telegram bot (long polling, brez javnega webhooka) |
| Jezik | slovenščina privzeto, preklop na angleščino (next-intl) ([ADR-0005](./docs/adr/ADR-0005-i18n-sl-privzeto.md)) |
| Tema | svetla in temna, privzeto po sistemu |
| Prejšnja koda | veja `legacy` (samo za branje). Stari PHP projekt `trading-list` je vir izkušenj, ne predloga ([prevzem](./docs/research/2026-10-22-trading-list-prevzem.md)) |
| Instrumenti | ameriške delnice + **UCITS ETF-ji** (potrjeno, [ADR-0008](./docs/adr/ADR-0008-instrumenti-ucits.md)) |
| UX | napreden React UX: gibanje (Motion), povezani pogledi, kukalo, ⌘K, pregledne vizualizacije ([ADR-0009](./docs/adr/ADR-0009-napredni-ux-motion.md), DESIGN.md §8–§10) |
| Ročni predlogi | uporabnik lahko sam pošlje simbol, hipotezo ali novico v analizo (DESIGN.md §11) |

## 3. Arhitektura

```text
 Tailscale ─► web (Next.js) ──REST/SSE──► api (FastAPI)
                                            │
     ┌──────────────┬──────────────┬────────┼─────────────┬───────────────┐
     ▼              ▼              ▼        ▼             ▼               ▼
 postgres        redis          worker   (rezerva)       broker          notify
 Timescale       vrste,         (arq)    Agent SDK       ib_async ─►     Telegram
 pgvector        pub/sub        ingest,                  ib-gateway      bot
                                radar,                   (read-only)
                                agenti
                                   │
                                   ▼
                               litellm ──► Ollama (GPU naprava v LAN)
                                       ──► OpenCode · OpenAI (ChatGPT prijava)
```

Odločitve: [ADR-0002](./docs/adr/ADR-0002-python-backend-nextjs-frontend.md) (sklad), [ADR-0003](./docs/adr/ADR-0003-tradingagents-kot-odvisnost.md) (TradingAgents), [ADR-0004](./docs/adr/ADR-0004-llm-vloge-litellm.md) (LLM vloge), [ADR-0006](./docs/adr/ADR-0006-clovek-vedno-odloci.md) (brez samodejnih naročil), [ADR-0007](./docs/adr/ADR-0007-telegram-obvestila.md) (Telegram).

## 4. LLM vloge (prilagojeno tvoji opremi)

| Vloga | Model | Naloge | Obseg |
|---|---|---|---|
| `embed` | Ollama `bge-m3` ali `nomic-embed-text` (~1 GB VRAM) | vektorji novic, grozdenje | vse novice |
| `local-fast` | Ollama Qwen 3.8 27B (4-bit), *brez razmišljanja* | triaža novic (JSON), tikerji, tip dogodka, sentiment, povzetek | stotine na dan |
| `local-reason` | isti model, *z razmišljanjem* | prvi prehod analize vzroka padca, ETF tema, prevodi povzetkov | desetine na dan |
| `cloud-quick` | OpenCode Go (GLM / Kimi / DeepSeek, javni seznam na `/models`) | analitiki in debata v TradingAgents | nekaj zagonov na dan |
| `cloud-deep` | **MiniMax** (OpenAI-kompatibilen API) → rezerva OpenCode Go (najmočnejši model) | končne odločitve, opcijski strateg, tedenski pregled tez | dnevni proračun |

TradingAgents lahko za `deep` uporabi tudi ChatGPT naročnino (njihova prijava "Sign in with ChatGPT"), kar je izbira v nastavitvah analize (M4). Claude ostaja izven sistema. `services/claude_runner` je odložen in se doda samo, če se kasneje odločiš za Claude Agent SDK.

**Opomba o VRAM:** 27B Q4 zasede ~16 do 18 GB. Ob embed modelu ostane ~5 GB za kontekst, zato je vzporednost 1 do 2 zahtevi. Če triaža ne dohaja (S&P 500 ustvari veliko novic), dodamo manjši model iste družine za `local-fast` (BL-012).

## 5. Cevovodi

0. **Ročni predlogi** (`services/api/proposals`): obrazec, ⌘K, Telegram `/predlog` → vrsta analiz z izbrano globino (hitro / standardno / globoko) → signal `source=manual`, ki hipotezo potrdi ali ovrže.
1. **Ingest** (`services/api/ingest`): IBKR EOD svečke in opcijske verige (zakasnjeno), Flex (portfelj), SEC EDGAR (8-K, Form 4, 13D/G), Finnhub (novice, koledar poročil), RSS (sporočila za javnost), Reddit/StockTwits (samo watchlista + kandidati), yfinance (fallback, ETF holdings), FRED.
2. **Radar** (`services/api/radar`): normalizacija → embed → grozdenje v dogodke → triaža (`local-fast`) → deterministični kontekst (odziv cene, pozornost) → ocena priložnosti → eskalacija → signal `catalyst` → Telegram.
3. **Vstopi** (`services/api/entries`): pravila (trend, pullback, podpora, padec od vrha, pasovi vrednotenja, insiderji) → `dip_analyst` (`local-reason` → `cloud-quick` pri dvomu) → signal `entry` ali `thesis_break` → lestvica postopnega nakupa.
4. **Globoka analiza** (`services/agents/deep_research`): TradingAgents (delnice), naš ETF analitik (ETF), SSE v UI.
5. **Teze** (`services/agents/thesis_tracker`): tedenski pregled prek `cloud-deep`.
6. **Opcije** (`services/api/options` + `services/agents/options_strategist`): CSP, covered call, call spread, protective put. Izračuni so deterministični.
7. **Izidi** (`services/api/signals/outcomes.py`): donos po 1, 5, 20 in 60 dneh, alfa, kalibracija.

## 6. Mejniki

| ID | Mejnik | Rezultat (definicija "končano") | Naloge |
|---|---|---|---|
| **M0** | Temelji | `docker compose up` zažene vse servise. LiteLLM odgovori na vseh 5 vlog. CI je zelen. Lupina UI (SL/EN, tema) z UX temelji: motion tokeni, ⌘K, kukalo, animirane številke, pregledne komponente na vzorčnih podatkih | BL-001–BL-019 |
| **M1** | Podatki + portfelj | Flex in EOD svečke v bazi. SCR-08 Portfelj in SCR-05 Instrument (osnova) delujeta. Watchlista v bazi | BL-020–BL-039 |
| **M2** | Radar | dogodki za tri poglede, triaža lokalno, ocena, SCR-02 in SCR-04, Telegram obvestila | BL-040–BL-059 |
| **M3** | Vstopi | pravila, `dip_analyst`, SCR-03, lestvica, beleženje izidov | BL-060–BL-079 |
| **M4** | Globoka analiza | TradingAgents adapter, ETF analitik, SCR-06 v živo | BL-080–BL-099 |
| **M5** | Teze + uspešnost | SCR-09, SCR-10, kalibracija uteži | BL-100–BL-119 |
| **M6** | Opcije | veriga, payoff, strateg, SCR-07 | BL-120–BL-139 |
| **M7** | Naročila s potrditvijo | osnutki naročil, varovala, najprej paper račun | BL-140–BL-159 |

**Uporabna verzija (M0 do M3): ~7 do 9 tednov.**

## 7. Kaj prevzamemo iz odprtokodnih projektov (povzetek)

| Repo | Prevzamemo | Način |
|---|---|---|
| TradingAgents | celoten agentski graf za delnice, SSE pretakanje, sheme odločitev, portfelj kot kontekst | odvisnost, zaklenjena verzija |
| Vibe-Trading | read-only IBKR konektor, opcijska matematika in UI ideje, Markdown znanje za agente, varovala naročil | prepis izbranih delov (MIT) |
| LEAN | koncept Insight → naša shema `Signal`, ločitev Alpha/Portfolio/Risk/Execution | ideja |
| trading-signals | indikatorji na grafih v brskalniku | odvisnost |
| legacy (naš) | pogodba virov podatkov, kvote, prikaz izvora, validacija, risk gate, DCF | prepis v Python |

Podrobno (datoteke, poti): research §3.
