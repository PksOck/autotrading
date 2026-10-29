# UX-00: izvedljivost stolpcev portfelja in watchliste

Preverjeno 29. 10. 2026, 05:50–06:04 UTC; BL-192. Vir: agregatne poizvedbe `BEGIN READ ONLY` v demo `preza-postgres-1/preza`, koda te veje in izvorna testna pogodba. Brez osveževanja, klicev ponudnika, spreminjanja nastavitev ali objave računov/količin. [Strojna matrika](./2026-10-29-izvedljivost-metrik.json) vsebuje definicije, stanje in omejitve vsake metrike. Čas preverjanja ni datum poročanja ponudnika.

## Dejanska pokritost

Pozicije so deduplicirane po instrument ID iz **zadnjega posnetka vsakega računa**, samo quantity != 0; watchlista vključuje active in reserve. Presek je prazen. Trenutno je vseh 10 vnosov watchliste active; reserve nima primerov. Zadnji datum pozicij je 23. 10. 2026. Pregled je inventura shranjenega demo stanja, ne potrditev današnjega stanja pri brokerju.

| Populacija / vrsta | Cilji | Dnevne cene / vsaj dve svečki | Znana valuta | Fundamenti | ETF profil |
|---|---:|---:|---:|---:|---:|
| Portfelj / delnica | 25 | 24 | 25 | 0 | ni relevantno |
| Portfelj / ETF | 1 | 1 | 1 | ni relevantno | 0 |
| Watchlista / unknown | 9 | 9 | 0 | 0 | ni ugotovljeno |
| Watchlista / ETF | 1 | 1 | 1 | ni relevantno | 0 |

Vseh 35 instrumentov s svečkami ima zadnjo na 28. 10. 2026. Raziskovalna meja svežine je 4 koledarske dni za cene in 8 za tedenske fundamente; to ni trgovalni koledar ali SLA izdelka. V celotni bazi je **1 zapis fundamentov za instrument zunaj obeh ciljnih seznamov**. Njegov dividendni donos in payout sta null. Števec »1/46 instrumentov« zato prikrije dejstvo, da je pokritost uporabnikovih ciljev s fundamenti 0/36. ETF profila ni nikjer v bazi. Dva ciljna ETF-ja sta označena UCITS, vendar politika acc/dist ni shranjena; dividendne in nedividendne delnice iz teh podatkov niso zanesljivo razločljive.

## Kje se podatki izgubijo

- Finnhub ključ je v tekočem workerju nastavljen (preverjena samo prisotnost, brez izpisa vrednosti). Opravilo `fundamentals` je nastavljeno ob nedeljah 06:10 UTC, `run_at_startup=False`; upload Flex sproži cene, ne fundamentov. Zadnji upload je 28. 10. 2026. To je verjetna razlaga odsotnosti novega prenosa, **ni dokazan vzrok**: razpoložljivi zadnji dnevniški izsek ne vsebuje teka fundamentov, opravilo pa nima podrobnega `sync_run` zapisa.
- Dejanska funkcija `fundamentals` in urnik sta prebrana tudi iz tekočega workerja. Celoten `worker.py` ima drugačen hash od izhodišča te veje; pregledana funkcija in urnik se ujemata. `services/fundamentals.py` ima enak SHA256 `13bdbce2b54e5c3dc7b096d86946466fb531489b47b8bdd133bb64ee342e6a93`. Ni domneve, da je celotno demo okolje na istem commitu.
- Pot `user_symbols → find_by_symbol → refresh_fundamentals → Finnhub` preskoči ETF, **ne preskoči unknown**. BL-174 zato ni dokazan glavni vzrok. `find_by_symbol` prednostno izbere uporabnikovo kotacijo, vendar je simbol manj natančna identiteta od instrument ID. Sedanji `user_symbols` in `get_portfolio` uporabljata globalni zadnji datum; raziskava uporablja datum po računu. Trenutni podatki imajo en datum, zato tu razlika ni opažena; za več računov je to ločeno tveganje.
- Napake vira ločujejo kvoto, unauthorized, HTTP in prazne podatke. Brez konkretnega dnevniškega dokaza ne trdimo, da gre za kvoto, naročnino ali napačen ključ. News Finnhub napaka ni dokaz napake `/stock/metric`. Nobena metrika ni označena entitlement_required.
- `PositionOut` nima fundamentov; `WatchlistOut` ima lastni cilj, last_close in spremembo od dodaje, nima dnevne spremembe/fundamentov/valute. `InstrumentDetail` vrne ceno, dnevno spremembo in vir/čas. Shranjena vrednost zato še ne pomeni stolpca v trenutnem API/UI. Noben tih N+1 refresh ob izrisu tabele.

## Pogodba metrik in stolpcev

Obstoječi `tests/fixtures/finnhub_metric.json` je ročno sestavljena pogodba, ne anonimiziran živ odgovor. Parser zna obdelati TTM P/E, EV/EBIT, FCF donos, ROE, marže, rast, dolg/kapital, dividendni donos in payout; vsak je v JSON matriki vezan na konkretna polja. Podatki so v ciljni populaciji prazni, zato ti stolpci še niso primerni kot privzeti.

Dividende zahtevajo posebno previdnost: `dividendYieldIndicatedAnnual` in `currentDividendYieldTTM` imata različno osnovo; payout preklopi med TTM in annual. Parser predpostavlja odstotke, ne shrani izbranega fallbacka in ne dobi datuma konca poročila. `as_of` pri fetchu pomeni današnji datum pridobitve; ni dokaz obdobja. Nova pogodba mora shraniti osnovo, period_end, source_field in stanje, preden prikaže primerljivo dividendno tabelo. Starim zapisom ne pripisuj osnove za nazaj. `debt_to_equity` potrebuje preverjeno skalo, ne samodejne oznake %.

Forward P/E in dividenda na delnico nista razčlenjena ali shranjena; ostajata nepreverjena oziroma neopažena. TTM ni forward nadomestek. Dividenda iz yield × današnja cena ni preverjena DPS. Lastni cilj `target_price` obstaja, a ni izpolnjen pri nobenem cilju; analitikova ciljna cena je drug pojem. ETF TER/indeks/distribucija imajo model, TER tudi lasten vir in datum. Vzorec YAML vsebuje nepreverjene kotacije; to ni dokaz profila za uporabnikova ETF-ja.

**Izvedljiv začetni profil:** portfelj obdrži simbol/ime, količino, vrednost, težo, P/L ter jasno loči ceno iz Flex posnetka od zadnjega close. Watchlista lahko prikaže simbol/ime, zadnji close, spremembo od dodaje, raven in opombo; valuta pri unknown mora biti prikazana kot manjkajoča, dokler identiteta ni potrjena. Za dnevno spremembo in valuto watchliste je potrebna skupna read pogodba brez osveževanja po vrsticah. Izbirni profili »vrednotenje«, »kakovost«, »dividende« in »ETF« pridejo po izboljšanju pokritosti ter prikazujejo manjkajoče podatke z razlogom. Izbira stolpcev ne prikriva prazne baze.

## Dividende v portfelju in Flex

Predlagani zavihek Portfelj → Dividende naj loči **dejanska izplačila**, **napovedana izplačila** in **oceno prihodka**. Trenutne pozicije niso zgodovinsko upravičenje do dividende. Pred razvojem uvoza je treba na zasebnem reprezentativnem izvozu potrditi sekcije Cash Transactions (dividende, davčni odtegljaji, ustrezne oznake), Change in Dividend Accruals/Open Dividend Accruals in Corporate Actions; to so zahteve prihodnjega parserja, ne že podprta pogodba ali zagotovilo posamezne Flex konfiguracije. Potrebni so znesek, valuta, tip, datumi, identiteta instrumenta in stabilen ID za deduplikacijo. Davka ne sklepamo iz razlike brez dokazila.

Sedanji parser bere samo OpenPosition, Trade in CashReportCurrency; neznane sekcije zavrže, uvozna pot ne arhivira izvirnega XML. Uporabnik naj svoj izvoz zasebno ohrani za ponovni uvoz po UX-19. Sedanji upload ni arhiv za prihodnje pridobivanje dividend.

## Naslednje izvedbene naloge

1. Dodati auditen ročni/urni refresh fundamentov z rezultatom na instrument, zadnjim uspehom in jasnim razlogom preskoka; najprej omejen vzorec, nato uporabniško nadzorovan obseg. Raziskava ga ni izvedla.
2. Odpraviti nepopolno identiteto devetih unknown vnosov in preveriti valuto/kotacijo; ne privzeti USD.
3. Dodati skupen read model za stolpce z izvorom in časom; ločena pogodba osnove dividendnih metrik in preverjanje živih vzorcev sta predpogoj dividendnih ocen.
4. Preveriti zadnji snapshot po računu v obstoječih servisih z ločenim regresijskim testom; trenutna raziskava ne spreminja portfelja.

UX-00 je zaključen kot inventura in določitev vrzeli. Podatkovni pogoj za privzete fundamentalne/dividendne stolpce še ni izpolnjen; nadaljnji val potrebuje te ločene popravke.
