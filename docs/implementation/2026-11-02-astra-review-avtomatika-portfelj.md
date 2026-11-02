# Astra pregled avtomatike in portfelja

Datum: 2026-11-02. Pregled od osnove4842514, še necommitane spremembe BL-232/233. Uporabnik je izrecno zahteval dodatni pregled z Astro. Model gpt-6-astra, high; samo branje kode in dokazil, brez testov, omrežja, sprememb ali posega v3000.

## Preostale ugotovitve

1. **P2, statična ugotovitev za popravek/preverjanje:** MarketContext.tsx absolutno postavi vir/čas pod mini graf v DataTable overflow-x-auto. Pri zadnji vrstici je razkritje lahko navpično odrezano ali zahteva notranje navpično drsenje; z-index ne odpravi clippinga. Predlog: portal/popover ali prikaz v običajnem toku, ki poveča samo izrecno odprto vrstico. Potreben browser dokaz zadnje vrstice, ozkega zaslona in vodoravnega pomika. Astra brskalniške reprodukcije ni izvajala.
2. **Podatkovna omejitev YTD:** isti ponudnik začetne in zadnje cene ni dokaz usklajene osnove ob splitu. Osveževanje starih cen trenutno ne dokazuje retroaktivne uskladitve. Prikaz je cenovna ocena trenutnih količin, ne dejanski donos računa; opozorilo je v pomoči. Pred oznako preverjene primerljivosti potrebujemo dokaz corporate-action/adjustment osnove oziroma izrecno nepreverjeno stanje. Brez lažnega skupnega EUR donosa ali NAV trditve.
3. **Preostali brskalniški preverjanji:** zadnji ciljni zagon7/10 uspešnih. Avtomatika uspešna vSL/EN na namizju/telefonu, Pozicije uspešno kompaktne; Watchlista še preseže interno ciljno višino105px, YTD test pa preveč strogo predpostavlja manjkajočo začetno ceno kot prvo napako namesto zastarele zadnje cene. Za UI test uporabiti determinističen sintetični odgovor, podatkovno matematiko že preverja DB test. Meja105px je interna testna izbira, ne obljuba iz SPEC; imen/opozoril ne smemo rezati zaradi nje.

## Potrjeno odpravljeno

- SOLevi pregledi so odkrili izgubo osnutka ob počasnem hitrem preklopu/reloadu, vključno z A→B→A. Instance tokeni sedaj varujejo dirty/save/reload/quick completion;11 komponentnih testov avtomatike vključuje zapoznele odgovore. Astra ni našla nove P1/P2 v stanjih avtomatike.
- Znani409 blokira naslednji zapis do uspešnega izrecnega branja; neuspešen refetch ne šteje predpomnjenih podatkov za svežo revizijo in ne izbriše osnutka.
- YTD pomoč ne govori več o zadnjih dveh zaključkih.
- Timeout urejevalnika Radar ni dokaz izgubljenega editorja: browser snapshot pokaže odprt omogočen combobox. Dodani izrecni dostopni imeni Urnik/Obdobje premika; ponovljeni testi avtomatike so uspešni.

## Dokazi in stanje pred zaključkom

API619 uspešnih +1 pogojni Redis skip,19 obstoječih opozoril. Ruff229/mypy137 čista, generirana OpenAPI/TS reproducibilna. Celotni splet213/51 uspešnih; zadnji ožji komponentni zagon19 uspešnih. Končni celotni brskalnik po novih spremembah še ni zelen in ni zaključen. Prejšnji ciljni24 zagon16/24 je nadomestil ponovljeni ožji10 zagon7/10.

Samo demo3100 API/web je posodobljen; brez reseeda ali spremembe3000. Sliki3000 ostajata web4eaf458ee… in API973f535ba…. Spremembe tega kroga še niso commitane ali poslane na GitHub. Za nadaljevanje preberi .superpowers/sdd/2026-11-01-enostavna-avtomatika/progress.md in povezani SPEC/plan. Začasna sintetična DB preza-ux-nov01-settings-test (3898d35e…, port26163) je po API testih še za odstranitev.

## Zaključna dopolnitev po odpravi

Uporabnik je zahteval odpravo. [Zaključni dokazi](./2026-11-02-zakljucek-avtomatika-portfelj.md): vir/čas v običajnem toku, last-row browser RED/GREEN, YTD brez preverjene split osnove varno neznan in BL-234 za podatkovni vir. Astra ponovni pregled brez novih pomembnih produktnih ugotovitev, datumski selector testa popravljen. Končni API620+1skip, web213/51, browser106+12namernihskipov. Namenska testna DB je odstranjena. Prvotni odprti zapis zgoraj je zgodovina pregleda, ne končno stanje.
