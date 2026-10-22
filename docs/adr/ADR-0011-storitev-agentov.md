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
- **ETF analitik (BL-083):** za `kind = etf` API ustvari zagon z `engine = "etf"`. To ni LangGraph graf, ampak preprost async cevovod v istem delavcu. Deterministična koda izračuna dejstva: profil sklada (TER, indeks, distribucija, top pozicije, sektorji), tehnično sliko s TA-Lib, utež v portfelju in prekrivanje z obstoječimi pozicijami. Prekrivanje se računa "skozi" ETF-je v portfelju po top pozicijah. Nato dva klica vlog: `cloud-quick` povzame temo in gonila, `cloud-deep` da oceno z utemeljitvijo. Profil sklada osveži tedenski cron `refresh_etf_profiles` (Yahoo `funds_data`, samo za ETF-je v portfelju in na seznamu opazovanja) v tabelo `etf_profile`. Brez profila dobi zagon opozorilo `no_profile`.
- **Hipoteza uporabnika (BL-090):** globok ročni predlog obdrži hitro presojo in hkrati ustvari zagon agentov s hipotezo. Agenti analizirajo instrument kot običajno, nato en klic `cloud-deep` prebere poročila in hipotezo izrecno potrdi, delno potrdi, ovrže ali reče, da je poročila ne naslovijo. Hipoteze ne damo v graf, da agentov ne usmerja (potrditvena pristranskost).
- **Kartica odločitve (BL-089):** po zagonu koda izračuna kontrolno oceno iz posnetka: kakovost poslovanja iz ROE, neto marže, rasti prihodkov in zadolženosti (utež 0,25, BL-088), vrednotenje proti lastni 5-letni zgodovini (0,15), trend (0,15) in tveganje prek ATR (0,15). Uteži se normalizirajo na komponente s podatki. Iz ocene izpelje implicirano oceno. Klic `cloud-quick` napiše sprožilce (`upgrade_if`, `downgrade_if`), prepričanje 1–10 in `delta_note` proti prejšnjemu zagonu. Razred velikosti (majhna < 2 %, normalna 2–4 %, povečana 4–6 %) določi koda iz ocene in prepričanja. Razlika vsaj dveh stopenj med oceno agentov in implicirano oceno zniža zaupanje, omeji velikost na majhno in doda opozorilo `control_disagrees`; ocene agentov ne spremeni.
- **Odpornost:** TradingAgentsove SQLite kontrolne točke (`checkpoint_enabled`) v `AGENTS_HOME` nadaljujejo prekinjen zagon. Zagon, shranjen ob nedosegljivem Redisu, vsakih 5 minut pobere `sweep_runs`.

## Posledice
- Preusmeritev neposrednih klicev je vezana na notranjost v0.7.0. Test `tests/test_deep_run.py` požene cel graf s skriptiranim modelom na fiksnem posnetku in pade, če nova verzija klic premakne ali če kaj uide na Yahoo.
- Docker gradi `agents` iz korena repozitorija (potrebuje `services/api`) in potrebuje `git`.
- Yahoo `funds_data` za UCITS kotacije (LSE, Xetra) še ni preverjen na pravem omrežju. Top pozicije pokrijejo le del sklada (`holdings_coverage`), zato je prekrivanje spodnja meja.

## Zavrnjene možnosti
- **TradingAgents v API sliki:** podvoji velikost slike in veže API na pandas 3 in LangGraph.
- **Vendor, ki med zagonom bere bazo:** orodja tečejo v nitih, sinhrona povezava bi podvojila sloj baze, rezultat pa ne bi bil ponovljiv.
- **Redis pub/sub za korake:** več gibljivih delov brez koristi pri enem uporabniku.
