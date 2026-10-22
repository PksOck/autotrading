# ADR-0011: Globoka analiza v ločeni storitvi `agents`, TradingAgents bere posnetek naše baze
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-005

## Kontekst
ADR-0003 določa TradingAgents kot odvisnost z zaklenjeno verzijo. v0.7.0 ni na PyPI, prinaša pandas 3, LangGraph, LangChain in yfinance, svoje podatke pa bere z Yahooja. Mi želimo, da agenti vidijo iste podatke kot preostanek Preže (vir in čas, oznaka govoric), da gredo vsi klici modelov prek LiteLLM (ADR-0004) in da se analiza vidi v živo (CMP-12).

## Odločitev
- **Ločen paket `services/agents`** (`preza_agents`) z lastnim `uv.lock` in lastnim arq delavcem na vrsti `arq:agents` (`max_jobs = 1`). API slika ostane lahka. Paket uporablja modele in nastavitve iz `services/api` (odvisnost po poti).
- **TradingAgents iz gita, oznaka `v0.7.0`** (`[tool.uv.sources]`). Nadgradnja samo, ko gredo regresijski testi skozi.
- **Modela:** ponudnik `openai_compatible`, `backend_url` = LiteLLM, imeni modelov sta naši vlogi (`DEEP_QUICK_ROLE` = `cloud-quick`, `DEEP_DEEP_ROLE` = `cloud-deep`). Rezervne poti ostanejo v LiteLLM.
- **Podatki (`vendor_local`):** pred zagonom zgradimo `DataSnapshot` iz baze (sveče do datuma analize, temeljni podatki, novice 30 dni, Form 4, tržne novice 7 dni) in ga shranimo k zagonu. Vendor `local` je registriran v `VENDOR_METHODS`, štiri neposredne klice Yahooja (`load_ohlcv` v dveh modulih, `get_company_profile`, `get_closes`) preusmerimo na posnetek. Vsak blok besedila navede vir in datum, govorice so označene `[UNCONFIRMED REPORT, not a fact]`. Finančnih izkazov nimamo, zato veriga nadaljuje na `sec_edgar`; makro (FRED) in napovedni trgi (Polymarket) ostanejo njihovi.
- **Analitiki:** tržni, novice, temeljni. Socialnega izpustimo, ker bere Reddit in StockTwits mimo naše oznake govoric.
- **Številke:** tržni analitik dobi TradingAgentsov deterministični "verified snapshot" (stockstats na naših svečah). Prikazane številke na SCR-06 pridejo iz posnetka, ne iz besedila agentov.
- **Pravilo govoric:** ocena Kupi ali Povečaj, ko so v posnetku samo govorice brez uradnega vira, dobi opozorilo `rumor_only`. Globoka analiza ne ustvari signala; oceno in poročilo vidiš, odločiš ti (ADR-0006).
- **Živi prikaz:** delavec vsakih 0,5 s zapiše nove korake (`analysis_step`), API jih streže kot SSE (`/analyses/{id}/events`) z branjem tabele in podpira `Last-Event-ID`. Redis pub/sub iz BL-082 ni potreben: en uporabnik, en zagon naenkrat, zakasnitev 1 s je sprejemljiva, ponovni priklop pa deluje brez dodatne logike.
- **Odpornost:** TradingAgentsove SQLite kontrolne točke (`checkpoint_enabled`) v `AGENTS_HOME` nadaljujejo prekinjen zagon. Zagon, shranjen ob nedosegljivem Redisu, vsakih 5 minut pobere `sweep_runs`.

## Posledice
- Preusmeritev neposrednih klicev je vezana na notranjost v0.7.0. Test `tests/test_deep_run.py` požene cel graf s skriptiranim modelom na fiksnem posnetku in pade, če nova verzija klic premakne ali če kaj uide na Yahoo.
- Docker gradi `agents` iz korena repozitorija (potrebuje `services/api`) in potrebuje `git`.
- ETF analitik (BL-083) še ni narejen; API do takrat ETF zavrne z `etf_analyst_pending`.

## Zavrnjene možnosti
- **TradingAgents v API sliki:** podvoji velikost slike in veže API na pandas 3 in LangGraph.
- **Vendor, ki med zagonom bere bazo:** orodja tečejo v nitih, sinhrona povezava bi podvojila sloj baze, rezultat pa ne bi bil ponovljiv.
- **Redis pub/sub za korake:** več gibljivih delov brez koristi pri enem uporabniku.
