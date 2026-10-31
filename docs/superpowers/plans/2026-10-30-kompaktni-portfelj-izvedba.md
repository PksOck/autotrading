# Kompaktne vrstice portfelja — izvedbeni plan

> **For agentic workers:** uporabi superpowers:subagent-driven-development ali superpowers:executing-plans za ta ozek uporabniško določen popravek.

**Goal:** Premakniti mini graf desno ob identiteto instrumenta ter zmanjšati običajne vrstice brez izgube obdobja, cone, barv ali opozoril.

**Architecture:** Obstoječa symbol celica ostane ista; dvostolpčna notranja postavitev razdeli identiteto in graf. Ne dodamo novega podatkovnega stolpca ali ponastavimo lokalnih preferenc. PriceTrend dobi kompaktno predstavitev za tabeli Pozicije/Watchlista, njegova podatkovna pogodba ostane.

**Tech Stack:** Next.js/React/TypeScript, Tailwind tokeni, next-intl, Vitest/Playwright.

**Spec:** Uporabnikov označeni posnetek 2026-10-30: graf naj se premakne izpod identitete v desni prostor. Pred posegom je na :3100 prva vrstica visoka 217,25 px; meritev je DOM na vidni tabeli, ne ocena iz slike. To ne odobri širše prenove Tez ali novih statističnih pogodb.

## Omejitve in vmesnik

- BL-223, osnova `6a9f07c`, izolirani obstoječi worktree. :3000 brez sprememb, brez migracije, novih ponudnikov, LLM ali spreminjanja zasebnih podatkov.
- Datoteke: `apps/web/components/portfolio/{PositionsPanel,MarketContext}.tsx`, `components/watchlist/WatchlistPanel.tsx`; ustrezni obstoječi testi. Root ureja skupne prevode/dokumentacijo, če potrebno.
- Identiteta ostane v levi skupini: simbol, ime, račun/borza/valuta, cona, kakovost. Graf je desno, s časovno osnovo in dejanskim datumskim razponom. Dolgo ime je lahko skrajšano v vrstici, polno mora ostati dosegljivo. Opozoril ne reži ali skrij.
- `PriceTrend({trend, compact?: boolean})`; privzeti pogled ostane podprt, compact ne ponavlja obeh vrstic »do 30 dni« in »30 dni«. Dejanski vzorec/obdobje, vir in čas ostanejo dosegljivi, brez ugibanja fiksnega meseca.
- Novi slovenski/angleški napisi, če potrebni, samo prek messages; ne spremeni številk, cen ali pozitivnih/negativnih barv. Brez ročnega urejanja generirane API pogodbe.
- Integracijski dokaz zajame tudi obstoječo navpično skupino Actions na watchlisti: 4 px razmik med dvema 48 px ciljema povzroči 133 px vrstico. Dovoljena je odstranitev samo tega razmika, ne zmanjšanje ciljev. E2E izbira dejanj mora po novem ločiti summary Dejanja od summary obdobja grafa. Višinski cilj 130 px velja za primerljiv desktop, na telefonu ostanejo merila vsebine, položaja in odsotnosti page overflow.
- Obstoječi ID stolpcev/profili/preferences in stanje URL ostanejo. Tabela se po potrebi drsi znotraj svojega okvirja; ne ustvari vodoravnega drsenja cele strani na telefonu.

## T1: Premik in kompaktni kontekst

- [x] Preglej obstoječi render; obstoječe obdobje/cona/vidne kakovostne oznake so merilo, ne nova domena.
- [x] Dodaj samo smiselno regresijo za compact prikaz, ki ob preoblikovanju ne izgubi dejanskega števila/razpona/provenience; preveri pričakovani RED pred implementacijo. Pri zgolj CSS premiku ne piši testa, ki le ponavlja razrede.
- [x] Spremeni notranjo horizontalno postavitev v obeh tabelah in dodaj compact način. Naravna višina za opozorila ostane; ne uporabljaj fiksne višine/overflow hidden za celotno vrstico.
- [x] Ciljni obstoječi testi, tsc, ESLint in Prettier. Neodvisni task pregled diff in vsebinskih invariantov.

## T2: Integracija in dokaz

- [x] Root preveri celotne spletne teste in uspešen Linux demo build. Osveži samo :3100.
- [x] DOM/screenshot na širokem prikazu: graf je desno od identitete v isti vodoravni skupini, prva običajna vrstica cilj največ 130 px pri 100-% povečavi; pri več opozorilih je dovoljena naravna rast.
- [x] Preveri watchlisto, izbirne profile/Standardno, barve, manjkajoči trend in telefon brez page overflow; polno ime/razpon/vir/čas ostanejo dosegljivi tudi brez miške.
- [x] Zapiši rezultate, končni neodvisni pregled, BL-223/SESSIONS/DESIGN in commit. Širši novi UX plan ostane ločen od izvedbe tega malega popravka.
