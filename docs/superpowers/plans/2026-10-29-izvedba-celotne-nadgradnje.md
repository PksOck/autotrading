# Izvedba celovite nadgradnje in demo prevzem

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Izvajanje je potrjeno z uporabnikovim »Kar nadaljuj da pokrijemo vse in nato posodobimo demo«. Ne odpiraj znova že potrjenih odločitev.

**Goal:** Izvesti preostale uporabniške poti potrjenega načrta in objaviti preverjen demo za pregled.
**Architecture:** Obstoječi FastAPI/Next.js ostaneta osnova. Štirje neodvisni sklopi uporabljajo dodajne API pogodbe; integrator ureja skupne registracije, generirane tipe, prevode in demo. Novi urniki izklopljeni, broker read-only, brez samodejnih naročil.
**Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy/Alembic, PostgreSQL/arq, Next.js 16, React 19, next-intl, TanStack Query.
**Spec:** `docs/superpowers/specs/2026-10-28-celovita-uxui-spec.md` in izvorni načrt `2026-10-28-celovita-uxui-nadgradnja.md`.

## Globalne omejitve

**Posodobitev po uporabnikovem navodilu 2026-10-29:** objavi samo ločen pregled :3100. **Ne prepisuj :3000**, ne združuj Claudove veje in ne zaženi že zgrajenih slik brez nove izrecne potrditve. Izvedeno stanje ter odprti deli so avtoritativno zapisani v `docs/implementation/2026-10-29-pregled-sprememb.md` in S-017; spodnji izvorni checklist ne pomeni, da so vsa dokazna vrata zaključena.

- DataMeta loči vir/obdobje/pridobitev ter availability od transportnega stanja. Null ni nič, neznana valuta ni USD.
- Denar Decimal/numeric; nova denarna polja decimalni niz + valuta. LLM samo interpretira.
- Preference stolpcev lokalne/verzionirane, deljivi filtri/izbor/sort v URL. Obvezna identiteta in opozorila ostanejo vidni, touch 48px.
- Skrivnosti in zasebni izpisi ostanejo zunaj repoja. Izvirni Claudov checkout in njegova .env.example sprememba ostaneta nedotaknjena.
- TDD za vedenjske spremembe. Vsak izvajalec zabeleži RED/GREEN; DB zbirke uporabljajo ločene testne baze. Generirane tipe in skupne prevode ureja integrator.

## Review focus

- Več računov z različnimi posnetki in prazen novi posnetek ne oživita prodanih pozicij.
- Zadnja uspešna analiza se izbere pred limitom; statusna napaka ni veljaven sklep ali signal.
- Dva schedulerja, Redis izpad, DST in nočno okno ne podvojijo zagona ali obidejo kvote/pavze.
- Dividende, odtegljaj in accrual se ne seštejejo dvojno; manjkajoč davek/FX ni nič.
- Telefon, neposredni URL, brskalniški Back, pokvarjene preference in API izpad ohranijo pravi predmet ter uporabnikov vnos.

## Naloga A: podatkovna osnova, skupne tabele in portfelj (integrator)

**Datoteke:** domain metadata, services/portfolio/fundamentals/watchlist/instruments, portfolio/watchlist UI, nov `components/table/`, `lib/view-state.ts`, lupina in Pregled. Dodatne sheme/migracije po potrebi.
**Proizvaja:** primerljive read podatke brez N+1 refresha, source/as_of za metrike, lokalne preference, računski pogled, stolpce/vrstni red/gostoto, varen prikaz cen.

- [ ] Testi različnih datumov računov, neznane valute, praznih metrik in pokvarjenih preferenc najprej padejo.
- [ ] Implementiraj identiteto/DataMeta, osveževanje z audit izidi ter read model metrik.
- [ ] Implementiraj nastavljive Pozicije/Watchlisto, kratka dejanja in ohranjen undo; osnova za tri reprezentativne postavitve v demo.
- [ ] Odstrani tihe sample fallbacke, popravi mobilni status/Več in neznane teze/identitete.
- [ ] Preveri enotske, API in brskalniške poti, shrani ločene commite.

## Naloga B: analize, predlogi, Radar/Vstopi/Signali in raziskovalni pogledi

**Lastništvo:** routes/services/domain analyses/proposals/radar/entries/signals ter njihovi UI; skupne datoteke hooks/messages/main/types/model registration samo po dogovoru z integratorjem.
**Proizvaja:** pravilno zadnjo uspešno analizo, user-safe napake in retry, URL filtre, točno izbiro/detail na telefonu, vidne opozorilne statuse; ohrani Teze/Uspešnost in dopolni potrebne vrzeli.

- [ ] RED: status→particija→sort→limit, >100 zapisov, neveljaven proposal izhod, manjkajoč izbran ID.
- [ ] Implementacija API in UI z ločenim stanjem podatkov/napake, ohranjenimi osnutki in dokazi.
- [ ] Testi in navodila za vključitev fragmentov prevodov; brez posega v kvoto mimo naloge C.

## Naloga C: politike procesov, nastavitve, urniki in paketne analize

**Lastništvo:** novi automation domain/models/service/routes, nastavitveni UI in API hook modul; worker policy integracija, kvota v services/analyses skupaj z izvajalcem B; migracija rezervirana po dogovoru.
**Proizvaja:** revision guard, omogoči/ustavi posamezen proces, globalna pavza, IANA časovna okna/DST, preview/zagon paketa in izvedbene sledi, dostava/recovery ter transakcijska kvota.

- [ ] RED: DST/nočno okno, sočasni claim/kvota, onemogočen proces, Redis recovery, scope paketa.
- [ ] Zapiši arhitekturne odločitve z razlogi; implementiraj durable politike in izvedbe ter worker gate.
- [ ] Nastavitve imajo pending/dirty/conflict/error in brez skrivnosti; novi urniki izklopljeni.
- [ ] API/unit testi in frontend; integrator doda portfolio analyses tab ter generirane tipe.

## Naloga D: dividende in Flex

**Lastništvo:** dodatni dividend domain/models/service/routes/parser modul in `PortfolioDividends`; minimalen hook v obstoječi Flex import poti po uskladitvi.
**Proizvaja:** ločeno cash/accrual/coverage in deterministično projekcijo z razlogi vrzeli; ne trdi, da neobstoječ zasebni vzorec dokazuje živi format.

- [ ] Preveri uradne IBKR pogodbe in uporabi označene sintetične fixtures, če razširjen očiščen uporabnikov izpis ni dosegljiv.
- [ ] RED: idempotenca/neskladni ID, storno/odtegljaj, absent vs empty sekcija, prodana pozicija in acc ETF.
- [ ] Implementiraj potrjene XML oblike, izvor/valuto/obdobje, ločene vsote in pokritost; ne sklepa DPS iz osebne gotovine.
- [ ] UI omogoči pregled in jasna navodila za razširjen uvoz; brez lažnih ocen ob manjkajočem viru.

## Integracija in objava (UX-20)

- [ ] Registriraj modele/routerje, zaporedne migracije, združi SL/EN fragmente, generiraj OpenAPI/TS, uredi DESIGN/BACKLOG/SESSIONS.
- [ ] Svež pregled implementacij in celotne veje; odpravi pomembne ugotovitve ter preveri vse zbirke.
- [ ] Dopolni obstoječ izoliran demo :3100 s success/failure/partial/stale scenariji in vidno demo oznako, brez ključev ali produkcijskih volumnov.
- [ ] Preveri 5 uporabniških poti, SL/EN, teme, 390/768/1440 ter zoom/tipkovnico. Zabeleži izvedene teste in materialne omejitve.
- [ ] ZADRŽANO PO NAVODILU UPORABNIKA: prenos na :3000 šele po pregledu/dopolnitvah in novi izrecni potrditvi. Ločen demo :3100 je pripravljen; zasebno okolje ostane nespremenjeno.
