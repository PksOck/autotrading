# Dopolnitve po uporabniškem pregledu

2026-10-29 · S-018 · `feat/uxui-demo-upgrade`

Objavljeno samo na [ločenem :3100](http://localhost:3100). Okolje :3000 uporablja prvotni aplikacijski sliki; v tej seji ni bilo njegove migracije ali posodobitve. Docker je po vmesni ustavitvi ponovno zagnal uporabnik.

| Pripomba | Izvedena dopolnitev |
|---|---|
| Pregled je izgubil informacije | Vrnjen Portfelj danes s treemapom in dnevno barvo, moč/vrsta signalov, 7-dnevni Radar z razlago velikosti/barv/govoric in povezavo do dogodka ter lijak z enotno 30-dnevno kohorto. Tržne kartice so vrnjene, manjkajoči dejanski viri ostanejo jasno označeni. |
| Po Vrednotenju/Dividendah ni povratka | V vsaki skupni tabeli vedno dosegljiv profil Standardno; vrne privzete stolpce/vrstni red, uporabnik lahko stolpce nato dopolni. |
| Količina/cena/vrednost/teža/P&L/danes | Standardne Pozicije ohranijo te podatke, ločijo datum posnetka od zadnje dnevne spremembe in dodajo trend ter stanje vstopne cone. |
| Manjkajo barve in obdobje mini grafov | Dobiček/izguba, dnevna sprememba in od dodaje imajo predznak/puščico ter zeleno/rdečo barvo. Mini trend vsebuje do 30 shranjenih dnevnih sveč, število sej, dejanski prvi/zadnji datum in vir. |
| Dividende so druga tema | Isti card/tabela sistem kot Pozicije, nastavljivi stolpci gotovine in uskladitev, barve, stikalo ocen ter razkritje pokritosti. Ocene kažejo datum posnetka pozicije in ostanejo ločene od knjižb. |
| Kontrole ob novem uvozu | Bruto obračun in podpisana bruto izplačila se primerjajo le ob izrecni isti referenci dogodka, računu, instrumentu in valuti. Vidno ujemanje, razlika ali čakanje; odtegljaj ni bruto izplačilo. Konflikt knjižbe zavrne uvoz, ne prepiše zgodovine. |
| Ni primerov tez | Sintetični MSFT aktivna, ORCL osnutek in COST z opozorilom ter dokazno sledjo. Ponovitev seed ne podvoji ali ponastavi uporabniških sprememb. Vstop je varovan s PREZA_DEMO_DB=1. |
| Testiranje signalov/mnenj | Na Uspešnosti read-only izračun iz shranjenih signalov in končnih mnenj. Nastavljivi vir/obdobje/horizont/stroški/moč/stanje, natančni datumi/cene in preskoki. Brez novih LLM klicev ali sprememb signalov. |
| Nastavitve so preobsežne | Glavno stikalo avtomatskih analiz, izbor procesa z razlago in zložljivimi podrobnostmi; podatkovni procesi ločeni od raziskovalnih. Napredna globalna pavza, paket in zgodovina so postopno razkriti. |
| SMTP in več naslovov | Do 20 validiranih prejemnikov, izbor novih signalov/dnevnega povzetka/končanih analiz, stanje čakalne vrste in negotovih dostav. SMTP/TLS poverilnice samo na strežniku; brez konfiguracije pošiljanje izklopljeno. |

## Kje preveriti

- [Pregled](http://localhost:3100/), [Pozicije](http://localhost:3100/portfolio), [Watchlista](http://localhost:3100/portfolio?tab=watchlist), [Dividende](http://localhost:3100/portfolio?tab=dividends).
- [Teze](http://localhost:3100/theses), [Uspešnost in testiranje](http://localhost:3100/track-record), [Nastavitve](http://localhost:3100/settings).
- Po objavi osveži že odprt zavihek, da naloži novo različico spletnega dela.

## Preverjanje in meje

Celotna API zbirka: **547 uspešnih**, nato **32 ciljnih testov** zadnjih kontrol/popravil uspešnih. Celoten agentski del na končni različici: **221 uspešnih**. Web: **155 uspešnih**, TypeScript/ESLint ter **1290** SL/EN ključev. Ruff/mypy uspešna za 135 API in 23 agentskih modulov. Docker web/API build uspešen, demo migracija **0019 (head)**. Brskalniška zbirka: 59 uspešnih, 10 predvideno preskočenih, en numerični neuspeh meritve 48px (47,99997px). Po preverjanju CSS min-width/min-height 48px in podpikselni toleranci je vseh 16 ciljnih poti uspešnih na telefonu in namizju, vključno z vsemi novimi povratnimi pripombami in signalnimi povezavami.

Neodvisni pregled je našel in popravil nadaljnje avtomatske modelne klice po izklopu, pavzo med SMTP dostavami, izgubo ročnega dovoljenja v otroških pregledih tez ter neomejeno branje zgodovine za testiranje. Dodatne regresije varujejo ročni pregled pred deduplikacijo z blokiranim avtomatskim poslom in pred posegom v sočasno aktivno rezervacijo.

Še odprto: dejanski viri VIX/US10Y/DXY; SPY/SMA200 zahteva nedvoumno kotacijo in 200 shranjenih dnevnih zaključkov. Sintetični dividendni XML ni dokaz vseh živih oblik zasebnega Flex izpisa. SMTP je preizkušen s ponarejenim transportom, ne z resnično dostavo; treba je konfigurirati povezavo na strežniku, potem izrecno omogočiti izbrane prejemnike. Celovit backtester portfelja/ponovno zgodovinsko izvajanje agentov ni del te prve različice.

Nova stikala veljajo samo tam, kjer je nova koda nameščena. **Na :3000 še niso na voljo in v tej seji niso ustavila njegovih obstoječih delavcev.** Prenos tja zahteva novo uporabnikovo potrditev. V tej seji ni bilo pravih e-poštnih sporočil, živih LLM analiz ali naročil.
