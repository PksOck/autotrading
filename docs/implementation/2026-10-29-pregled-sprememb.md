# Nadgradnja Preže: pregled pred potrditvijo

Datum: 2026-10-29 · veja: `feat/uxui-demo-upgrade` · seja: S-017

**Okolje :3000 ostane nespremenjeno.** Uporabnik je izrecno zadržal prenos do pregleda in potrditve. Pregledna različica teče na [ločenem demu :3100](http://localhost:3100) s sintetičnimi podatki in vidno oznako. Ni združena v Claudovo vejo. Gradnja slik sama ni objava; že pripravljene slike `preza-*` se ne smejo samodejno zagnati na :3000.

## Kaj lahko pregledaš

| Pogled | Izvedena sprememba | Kaj preveriti |
|---|---|---|
| [Watchlista](http://localhost:3100/portfolio?tab=watchlist) | Izbirni stolpci, vrstni red, širine, pripenjanje, gostota, profila Vrednotenje/Dividende, krajša dejanja in meni; razveljavitev ohrani prvotni zapis | Izberi stolpce in osveži stran; preveri zastareli ORCL ter neznano identiteto v zalogi idej |
| [Pozicije](http://localhost:3100/portfolio) | Ista osnova tabel, izbor računa, frakcijske količine, datum cene posnetka, ločen zadnji zaključek, opozorilo za manjkajoči FX, zložena izpostavljenost | Primerjaj računa z različnima datumoma; manjkajoči FX ne sme postati nič |
| [Analize](http://localhost:3100/analysis?status=done&latest_per_instrument=true) | Filter uspešnosti in zadnja analiza posameznega instrumenta, deljivi filtri v URL | Novejša neuspešna analiza ne skrije starejše uspešne; obstoječi obeti ostanejo |
| [Portfelj: Analize](http://localhost:3100/portfolio?tab=analyses) | Predogled paketa za portfelj/watchlisto/oboje, omejitev poskusov, razlogi preskokov in skupna kvota | Onemogočeni paket pojasni blokado; predogled ne odda analiz |
| [Predlogi](http://localhost:3100/proposals) | Veljaven strukturiran rezultat ali razumljiva napaka, povezave do analiz posameznih simbolov, ponovni poskus istega predloga, ohranitev osnutka | Brez surovega validacijskega JSON kot zaključka; uspešen in neuspešen primer |
| [Dividende](http://localhost:3100/portfolio?tab=dividends) | Ločeno prejeta gotovina, odprti obračuni in 12-mesečna bruto ocena; račun/valuta/obdobje, vir in pokritost | Demo: bruto 25, davek −3,75, neto 21,25; odprti obračun 5 ni dodatna prejeta gotovina |
| [Nastavitve](http://localhost:3100/settings) | Povezave, globalna pavza, 11 procesov, dnevi, IANA cona, dnevni/intervalni urnik, okna, revizije in sledi | Potek urejanja/preklica, razumevanje omogočenosti proti urniku; novi paket je izklopljen |
| Radar / Vstopi / Signali | Točen izbrani predmet neodvisno od filtriranega seznama, dostopen telefonski detail, povezani predogledi, potekli signali, neznana teza brez lažne potrditve | Odpri neposredne povezave, Escape in Nazaj; neuradna novica ni uradno potrjena |
| Instrument | Identiteta in shranjene metrike z virom/osnovo/časom, izrecna varna dopolnitev imena/borze, neznana valuta brez USD | Dopolnitev ne ugiba vrste ali trgovalne valute iz valute poročanja |
| Uspešnost / Teze | Datumska kohorta signalov in podrobni izidi; kalibracija in zgodovina tez postopno razkriti | Datum kohorte ni datum izračuna izida; sprememba uteži ostane izrecna |
| Pregled / lupina | Pregled bere bazo brez tihega preklopa na vzorčne podatke; stanje storitev tudi na telefonu, navigacija v prazni ukazni paleti | Izpad je napaka, ne vzorčni rezultat; demo oznaka ostane vidna |

## Kaj še ni zaključeno ali dokazano

1. **Živi dividendni format:** parser je preverjen s strogo označenimi sintetičnimi XML primeri. Razširjen zasebni Flex izpis še ni potrjen. Pred prenosom je treba potrditi dejanske tage, identitete, odtegljaje, popravke ter sekcije. `FinancialInstrumentInformation` je zaznan, vsebina še ni uvožena.
2. **Pokritost realnih metrik:** ni bilo množičnega prenosa ponudniških podatkov. Audit fundamentov je dodan, vendar uspešen živi refresh ciljne populacije še ni dokazan. Forward P/E in denarni DPS pri trenutnem viru ostajata vrzel; P/E TTM ali dividendni donos nista nadomestka.
3. **Neznane kotacije:** varen ukaz lahko dopolni ime/borzo ob točnem ujemanju; ne razreši trgovalne valute ali vrste brez primernega vira. Ročni popravek z dokazom še ni izveden.
4. **Širši prvotni načrt:** poimenovani uporabniški profili, primerjava izbranih vrstic, popoln enoten iskalnik vseh tabel, popolna preureditev delniških/ETF panelov in vseh analitskih prikazov še niso zaključeni. Ta izdaja ni izjava, da je vsak UX-00–20 izpolnjen.
5. **Pred prenosom ponovno pregledati robove Flex:** posebej samo `BASE_SUMMARY` brez izvirnih valut in stare privzete valute pri nepopolnih vrsticah. Obstoječe regresije varujejo neveljavne količine, lot-only pozicije, neveljavno gotovino in prazne popolne posnetke; dodatnih oblik ne štejemo za potrjene.
6. **Shranjevanje predloga:** lokalni osnutek je ohranjen; ključ idempotence oddaje ni trajno vezan na osnutek čez ponovno nalaganje strani. To je nadaljnja zaščita pred dvojno oddajo ob izgubljenem odgovoru in ponovnem nalaganju.
7. **Demo izvajanje:** ni ključev, workerjev ali agentskega izvajanja. Pregled nastavitev in predogled paketa delujeta, živih analiz in obvestil v tem okolju ne izvajamo. Polni pregled 200-% povečave in vseh kontrastnih kombinacij še ni opravljen.

## Preverjanje

- API: 521 uspešnih testov, 18 opozoril knjižnic o zastarelih API-jih; izolirana testna baza.
- Agentski del: 218 uspešnih testov; izvajanje logike s sintetičnimi odgovori, brez živih LLM klicev.
- Web: 143 uspešnih testov v 35 datotekah; TypeScript, ESLint in SL/EN preverjanje 1162 ključev uspešni.
- Playwright: 54 uspešnih, 10 predvideno preskočenih, 0 neuspešnih; namizje in telefon. Preverjeni tudi filtri, predlogi, povezave, fokus, watchlista, dividende, nastavitve in onemogočeni paket.
- Izoliran Docker demo API/web zgrajen in zagnan; migracije 0016 → 0017 → 0018 v demo/test okolju. Ročni pregled nastavitev/watchliste pri širini 768 in watchliste pri 1440 brez vodoravnega prelivanja celotne strani; tabela ima lastno drsenje. Shranjen posnetek pregledne watchliste.
- :3000 preverjen samo za branje: web/API še uporabljata prvotni sliki in čas zagona 2026-10-28. Nobene migracije ali ponovnega zagona na tem okolju.

## Potrditev in nadaljevanje

Najprej pregled sprememb ter izbira dopolnitev. Nato popravki in ponovljeno ciljno preverjanje. Prenos na :3000 zahteva novo izrecno uporabnikovo potrditev; ta dokument je ne nadomešča. Pred prenosom ponovno preverimo sočasno Claudovo delo, razliko vej, aktivne analize in aktualno varnostno kopijo. Noben samodejni deploy, merge ali naročilo ni odobreno s tem prevzemom.
