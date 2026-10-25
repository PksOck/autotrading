# services/agents: agentski cevovodi

Vsi LLM klici gredo prek LiteLLM vlog (ADR-0004). Vsak izhod ima Pydantic shemo in test na posnetku podatkov. Zasnova: [ADR-0011](../../docs/adr/ADR-0011-storitev-agentov.md).

| Mapa | Namen | Vloga | Mejnik |
|---|---|---|---|
| `preza_agents/deep_research/` | TradingAgents adapter (`adapter.py`), `vendor_local.py`, posnetek podatkov (`snapshot.py`), časovnica korakov (`timeline.py`) | cloud-quick / cloud-deep | M4 |
| `preza_agents/worker.py` | arq delavec na vrsti `arq:agents`, globoka analiza in discovery pregledov tez | | M4/M5 |
| `etf_analyst/` | ETF: profil, prekrivanje, tema, odločitev | local-reason → cloud-deep | M4 (BL-083) |
| `options_strategist/` | izbira opcijske strukture (številke računa koda) | cloud-deep | M6 |
| `preza_agents/thesis_tracker/` | tedenski pregled tez in predlogi statusov | cloud-deep | M5 |
| `knowledge/` | Markdown znanje za pozive (prirejeno iz Vibe-Trading skills, MIT) | | M4 (BL-087) |

`dip_analyst` (M3) živi v `services/api/preza/entries/dip.py`, ker je majhen in teče v API delavcu.

## Lokalno

```bash
cd services/agents
uv sync
uv run pytest -q                       # cel graf s skriptiranim modelom, brez omrežja
TEST_DATABASE_URL=postgresql+asyncpg://preza:preza@localhost:5433/preza_test uv run pytest -q
uv run arq preza_agents.worker.WorkerSettings
```

## Tedenski pregled tez (BL-101)

`preza_agents/thesis_tracker/` uporablja izkljucno vlogo `cloud-deep` in poziv
`thesis-review-v1`. Discovery tece v nedeljo ob 06:15 UTC, dnevni catch-up ob
06:20 UTC pa pobere izpuscene preglede in nove aktivne razlicice. Delavec ima
izrecen casovni pas UTC in `max_jobs=1`. Globoka analiza lahko pregled zamakne,
zato urnik ni jamstvo casa izvedbe.

Vsaka aktivna razlicica dobi loceno opravilo z ID-jem
`thesis-review:<revision_id>:<week_start>`. Zacetek ISO tedna je ponedeljek v UTC;
baza zagotavlja en pregled na razlicico in teden. Discovery pobere tudi nedokoncane
rezervacije. Opravilo iz prejsnjega tedna ne sprozi novega tedenskega klica.

Omejitve so 20 trditev, 30 virov, 32 KiB serializiranega vhoda, 4000 izhodnih
tokenov na HTTP poskus in 660 s za delo pred zapisom napake. Storitev API ob
rezervaciji skrajsa besedila, nikoli ID-jev ali provenance; prevelik vhod oznaci
`skipped_limits`. Posnetek po rezervaciji ostane nespremenjen. Brez dokazov je
izid `done_no_evidence`, brez klica LLM in brez predloga confirmed.

Rezervacija, dispatch in zakljucek so locene kratke transakcije. Med LLM klicem
ni odprte transakcije. En logicni klic lahko v skupnem odjemalcu opravi najvec dva
HTTP poskusa zaradi popravka JSON. Agents ne dodaja ponovitev ali fallbackov.
Uporaba in dejanski, lahko neznani strosek se preneseta v pregled. Ob timeoutu
nedokoncani odjemalec ne vrne delne porabe; zapisani poskusi so tedaj spodnja meja.

Napake vloge, timeout in neveljavni izhodi pomenijo `failed` z varno kodo, brez
delnih predlogov ali signalov. Ponovni zagon po shranjenem dispatchu pomeni
`failed_unknown`, nikoli novega LLM klica v istem tednu. Prekinjeno rezervacijo
pred dispatchom je mogoce nadaljevati. Zamenjana aktivna razlicica pomeni `stale`.
Po izteku 660 s sledi kratka transakcija za zapis napake; ob nedosegljivi bazi
obnovitev ostane naloga naslednjega discovery. Prenos natancne porabe prek
prekinitve zunanjega klica ni zagotovljen.

Izhod je samo predlog. Storitev API preveri vse ID-je in citate ter odloca o
objavi signalov. Status trditve se ne spremeni brez uporabnikove potrditve.
Besedilni sprozilec ni ovrzena trditev; dvoumnost zahteva insufficient in null.
Testa `test_thesis_review.py` in `test_thesis_review_worker.py` uporabljata posnete
JSON podatke ter ponaredke LLM in transakcij, brez omrezja ali baze.

## Regresijski testi (BL-086)

`tests/regression/` požene pet fiksnih posnetkov (rast in poceni, padec in drago, samo govorica, kratka zgodovina, ETF) in primerja determinističen del zagona z datotekami v `golden/`: besedilo vsakega podatkovnega orodja (kontrolna vsota in prve vrstice), zaporedje korakov, opozorila in kontrolno oceno. Pred nadgradnjo TradingAgents morajo iti skozi (ADR-0003). Po nameravani spremembi:

```bash
UPDATE_GOLDEN=1 uv run pytest tests/regression   # nato preglej diff v golden/ kot kodo
```

Pozivi so v angleščini, poročila v jeziku uporabnika (`output_language`, VOICE.md §7).
