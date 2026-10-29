# SPEC v0.1: Val −1, signalni pogodbi in preverjanje virov

**Status:** pripravljeno za pregled pred izvedbo. **Datum dopolnitve:** 2026-10-29. **Naloga:** BL-189. **Podlaga:** [celoviti SPEC](./2026-10-28-celovita-uxui-spec.md) in Opusov načrt pri `28f2990`.

Val −1 sestavljajo trije ločeno pregledljivi rezultati. FIX-A in FIX-B popravita obstoječi pogodbi; UX-00 je samo raziskava. Ne čakajo na DataMeta, novo tabelo, novo identiteto vseh instrumentov ali delujoč demo stack. Specifikacija ne ustvarja novih migracij ali produkcijskih klicev.

## A. FIX-A: potek signalov pred filtrom in limitom

### Problem in obstoječe vedenje

`services/api/preza/routes/signals.py:list_signals` najprej izbere vrstice po shranjenem statusu in omeji nabor, nato med serializacijo spremeni potekle `new`/`watching` v `expired`. Zato `/signals?status=new&limit=1` lahko vrne `expired` in porabi edino mesto. `/signals?status=expired` pred prvim branjem teh vrstic ne najde. `db.get_session` zahtevo že commita, zato sedanje spremembe poteka niso samo začasne spremembe prikaza.

Obstoječi osnutek `services/api/tests/test_signal_expiry.py` potrdi prvi primer, ni pa celotna regresijska pokritost. Test ostaja neizvedena spremljevalna datoteka iz prejšnjega koraka, ne dokaz popravka.

### Zahtevana pogodba

Za en `now` v UTC na zahtevo je pravilo:

```text
expired := stored_status in {new, watching}
           AND expires_at is not null
           AND expires_at < now
```

Meja ostane strogo `<`, skladno s sedanjo kodo; točno ob `expires_at == now` se status še ne spremeni. Čas zajamemo enkrat, ne za vsako vrstico posebej. Sprejeto, zavrnjeno in že poteklo ostanejo nedotaknjeni; odsoten rok ne poteče.

Predlagana minimalna izvedba ohrani današnje zapisovanje poteka: z eno pogojno posodobitvijo normaliziraj potekle odprte signale v isti request transakciji **pred** status/kind poizvedbo in limitom. Normalizacija se ne omeji samo na trenutno stran ali izbrano vrsto. Pri sočasnem eksplicitnem sprejemu pogoj na aktualnem statusu ne sme prepisati `accepted` v `expired`. Ne uvajaj alternativnega izračunanega statusa samo v enem odjemalcu.

`GET /signals` ohrani array `list[SignalOut]`, obstoječe query parametre in zgornjo mejo; poslovnih polj se ne preimenuje. Razvrščanje dopolni s stabilnim tie-break `id DESC` ob `created_at DESC`, da izenačeni časi ne preskakujejo rezultatov. Spremembo omejitev/nov pagination envelope obravnava kasnejši UX-09, ne ta popravek.

Predlagani skupni vmesnik v `services/api/preza/services/signals.py`:

```python
async def expire_open_signals(session: AsyncSession, now: datetime) -> None: ...
```

Kliče ga list endpoint in novi detail endpoint FIX-B. Ne commita sam; transakcijo upravlja obstoječa request odvisnost. ORM identity map ne sme vrniti starega statusa po bulk update.

`PATCH /signals/{id}` ostane v tem sklopu eksplicitna uporabniška sprememba z obstoječim rumor guardom. FIX-A ne doda novega pravila, da poteklega nikoli ni mogoče sprejeti: sprejem je evidenca ideje, ne naročilo. Če uporabnik izrecno nastavi `new`/`watching` ob preteklem roku, naslednje branje avtomatsko vrne `expired`; to se zabeleži kot obstoječa domena za ločeno presojo UX-09, ne kot trajna aktivacija. Testi morajo prikazati to mejo namesto tihe spremembe PATCH semantike.

### Datoteke in preverjanje

Spremeni `services/api/preza/routes/signals.py`; dodaj `services/api/preza/services/signals.py`; dopolni `services/api/tests/test_signal_expiry.py` in obstoječi `test_api_m2.py` le, kjer je potrebno. Brez frontend sprememb, ADR ali migracije za ta popravek.

| Test | Podatki | Pričakovano |
|---|---|---|
| A01 | novejši potekel new, starejši veljaven new, limit=1 | samo starejši z statusom new |
| A02 | ista kombinacija za watching | samo veljaven watching |
| A03 | status=expired, v bazi new/watch z rokom v preteklosti | najdeni brez predhodnega list branja |
| A04 | brez filtra, različni statusi | konsistentni statusi, accepted/dismissed ostaneta |
| A05 | expires_at=null, preteklost, now, prihodnost | poteče samo preteklost |
| A06 | filter kind skrije nekatere zapise | štetje limita samo po ujemajočih, potek se ne izgubi |
| A07 | ponovljen GET in nova seja | stabilen ID/status, potek zapisan v bazi |
| A08 | enak created_at, različna ID | ponovljiv tie-break |
| A09 | eksplicitno accepted/dismissed ob preteklem roku | avtomatski potek uporabniške odločitve ne spremeni |
| A10 | rumor PATCH accepted | obstoječi 409 ostane; brez poslovnega obvoda |

Preverjanje: v `services/api` najprej `uv run pytest tests/test_signal_expiry.py -q` na izolirani bazi, nato ustrezne signalne/rumor teste in celoten API suite; `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`. Pred implementacijo se vsaj A01/A03 izkažeta za neuspešna iz pravega razloga; preskočeni DB testi niso uspeh. Testna baza ni `preza` produkcijske namestitve in je namensko ločena od drugih agentov.

**Zaključek A:** pogodbeni testi z bazo uspešni, diff omejen na signalni potek, brez UI ali novih statusov. Commit po dejanski dodelitvi BL-ID-ja.

## B. FIX-B: signal po neposredni povezavi

### Problem

`entities.ts` zna dekodirati `signal`, Vstopi in Telegram že pošiljajo `?peek=signal:<uuid>`, `PeekPanel` pa naloži samo instrument. Branje prve strani signalov s statusnim filtrom ni pravilna rešitev za detail. `history.back()` pri neposrednem vstopu lahko pošlje uporabnika iz aplikacije.

### API in hook

Dodaj `GET /signals/{signal_id}` z `signal_id: UUID` in nespremenjenim `SignalOut`:

- 200: točen signal ne glede na trenutno stran, filter ali poslovni status.
- 404: `detail=signal_not_found` za veljaven, neobstoječ UUID.
- 422: obstoječa validacija FastAPI za neveljaven UUID.
- Po samodejnem poteku isti status kot list endpoint pri istem trenutku po pravilu FIX-A. Signal lahko ostane prikazan kot expired; ni izbrisan zaradi statusa.
- Samo samodejni potek je dovoljen stranski učinek po sedanji pogodbi; odpiranje ne pomeni sprejema, zavrnitve, dodajanja na watchlisto ali naročila.

V `apps/web/lib/api/hooks.ts` dodaj `keys.signal(id)` in `useSignal(id: string | null)` z ločenim ključem od seznama. Query je disabled za null/neveljaven ID. Detail 404/422 ne ponavlja v nedogled. Uspešna obstoječa mutacija invalidira detail in vse signalne sezname; podatkov dveh ID-jev ne deli pod enim query key.

Izvoz API uporablja obstoječi `services/api/preza/cli/export_openapi.py` in `pnpm --filter web gen:api`. `schema.d.ts` je generiran. Adapter `types.ts` se sklicuje na generirano shemo po vzorcu repozitorija.

### Read-only komponenta

Nova `apps/web/components/signals/SignalDetail.tsx` dobi `signalId: string`. `PeekPanel` za `kind=signal` uporabi to komponento, obstoječi instrumentni predogled ostane enak. Ne gradimo novega globalnega entity sistema ali obvezne migracije simbolov na ID.

Prikaz: naslov instrumenta, vrsta, vir, smer/horizont, dejanski status, govorica, rationale, evidence s povezavami, čas nastanka/rok in pot na instrument. Razširjena poslovna dejanja niso del FIX-B. Cena/valuta se ne izmišljata, če ju `SignalOut` nima. Vse oznake SL/EN iz messages.

Stanja: skeleton, naloženo, 404, neveljaven ID, začasna napaka s ponovitvijo. Napaka ne odpre drugega signala. Ob zamenjavi ID se ne prikaže prejšnji signal pod novim naslovom. Opozorila govorice/expired ostanejo vidna.

### Zapiranje, Nazaj in dostopnost

Ob normalnem odprtju iz seznama se ohranijo vsi drugi URL parametri in scroll. Brskalniški Nazaj zapre pravkar dodani preview. Pri neposrednem vstopu Close odstrani samo `peek` s `replace` na isti aplikacijski poti; ne uporablja slepega `history.back()`. Ne odloča na podlagi samega `history.length`, ker lahko zgodovina vsebuje drugo spletno mesto. UI »Nazaj« v predogledu je omogočen le, kadar imamo lastno preverjeno notranjo predogledno zgodovino; sicer deluje kot zapiranje z varnim fallbackom.

Fokus se ob odprtju premakne na naslov/zapiranje in ob zaprtju vrne sprožilcu, kadar ta obstaja. Na telefonu je vsebina dosegljiva in pomična, spodnja navigacija ne zakrije zapiranja/evidence; Escape deluje. Ohranijo se obstoječi ADR-0013 touch/back mehanizmi; ne doda se drugega vzporednega `popstate` handlerja.

### Datoteke in testi

API: `routes/signals.py`, skupni servis iz A, `tests/test_signal_detail.py`, OpenAPI. Web: `components/common/PeekPanel.tsx`, novi `components/signals/SignalDetail.tsx`, `lib/api/hooks.ts`, adapter tipi, messages SL/EN, potrebna ciljana sprememba `lib/use-peek.ts`, novi `components/signals/SignalDetail.test.tsx` in `e2e/signal-deeplink.spec.ts`. Pred pisanjem frontend kode obvezno preberi `apps/web/AGENTS.md` in ustrezni lokalni Next vodič.

| Test | Pričakovano |
|---|---|
| B01: signal ni med prvimi 100 ali je accepted/dismissed | detail še vedno vrne pravi ID |
| B02: potekel new/watch | detail in list se strinjata po normalizaciji A |
| B03: veljaven neobstoječ/neveljaven UUID | 404/422 in ustrezno UI stanje, brez fallback zapisa |
| B04: rumor | badge in izvorni evidence ostaneta; nobena mutacija se ne sproži |
| B05: Telegram neposredni URL | detail se odpre; Close ostane v aplikaciji |
| B06: Entries povezava, nato browser Back | prejšnji simbol/filter/scroll se obnovi |
| B07: hitro odpiranje dveh ID | brez prelivanja starega detaila in napačnega query cache |
| B08: API nedosegljiv | napaka/ponovi, ne not-found ali neskončen skeleton |
| B09: instrument preview | obstoječa pot ostane delujoča |
| B10: 390×844, tipkovnica, SL/EN | dostopen dialog, Escape, fokus in 48px cilj zapiranja |

Playwright uporablja mock/fixture podatke ali izolirano demo bazo, ne dejanskih Telegram sporočil in ne spreminja živega statusa. Minimalno testira neposredni signalni URL in vrnitev iz ene obstoječe povezave. Vse tri proizvajalce (Vstopi, notify, Telegram) pokrije pogodbeni test oblike URL.

**Zaključek B:** API/detail/UI testi in regenerirani tipi usklajeni, noben nov analysis job/order/watchlist mutation, ostale entitete nespremenjene. UX-03 kasneje ponovno uporabi ta endpoint, ne uvaja drugega.

## C. UX-00: preverjanje virov Pozicij in Watchliste

### Obseg in rezultat

Rezultat je slovensko poročilo `docs/research/<datum>-izvedljivost-metrik.md`, strojno berljiva očiščena matrika in vzorci ponudniške pogodbe. Ne spreminja sheme, parserja, seznama pozicij ali produkcijske konfiguracije. V tem koraku se ne izvede množični refresh vseh instrumentov.

Cilji: unija aktualnih odprtih pozicij po računu in obeh watchlist ravni, deduplicirana po internem instrument ID. Analitika javnega poročila uporablja agregate; zasebni račun/velikost pozicije ne sodita v fixtures. Vzorec vključuje dividendno delnico, nedividendno delnico, unknown instrument, UCITS akumulacijski in distribucijski razred, če so na voljo. Če tip manjka, to napiši, ne ustvarjaj lažnega živega primera.

### Matriki

`MetricCapabilityRow`: `metric_key`, `instrument_kind`, `provider`, `endpoint`, `source_field`, `unit`, `basis`, `period_end`, `status`, `evidence_ref`, `checked_at`, `limitations`.

Statusi: supported / partial / not_observed / unsupported / entitlement_required / unverified. `entitlement_required` zahteva dokaz dejanske zavrnitve ali preverjeno ponudniško dokumentacijo; odsotno polje ali 403 brez razlage ne pomenita samodejno »plačljivo«.

`CoverageRow`: `population` (portfolio/watchlist/both), `instrument_kind`, `target_count`, `observed_count`, `fresh_count`, `unknown_identity_count`, `checked_at`, `source_snapshot`. Števec iz Opusovega starega posnetka ni aktualna poizvedba. Loči pokritost podatka od tega, ali se pojavi na API/UI.

Metrike: cena/dnevna sprememba/valuta; P/E TTM, forward P/E, EV/EBIT, FCF donos; ROE, marže, rast prihodkov, dolg/kapital; dividendni donos z osnovo, payout, dividenda na delnico; lastni cilj; ETF TER/indeks/distribucijska politika. Analyst target ni isto kot uporabnikov cilj in ni predpogoj prve izdaje.

### Preiskava po korakih

- [ ] Z read-only poizvedbami popiši aktualne instrumente, identiteto, metapodatke in čas fundamentov. Upoštevaj, da `Position` vsebuje zgodovino snapshotov.
- [ ] Preveri nastavljeno vlogo vira in zadnje dejanske teke/log razloge; ne izpisuj tokena ali celotnega request URL. `fundamentals()` ne zapisuje podrobnega sync_run, zato odsoten zapis sam ne dokaže, da opravilo ni teklo.
- [ ] Preveri pot `user_symbols → find_by_symbol → refresh_fundamentals → Finnhub`. UNKNOWN se v sedanjem servisu poskusi pridobiti; preskoči se ETF. BL-174 sam po sebi ni dokazan vzrok nizke pokritosti.
- [ ] Loči nezagnano opravilo, nepravilno konfiguracijo, nedosegljivost, kvoto, prazno polje, dvoumni simbol in napačen prikaz. Pri vsakem zaključku navedi dokaz ali označi hipotezo.
- [ ] Najprej uporabi že shranjene payload fixture. Če je nujen živi klic, omeji na reprezentativni vzorec in zabeleži obseg; brez množičnega prenosa ali novih plačljivih naročnin. Prazni/nepreverjeni endpointi ostanejo vrzeli.
- [ ] Preveri `source_field` in osnovo vsakega dividend/payout fallbacka ter mersko skalo (% proti deležu). Sodobnega fetch datuma ne označi kot datum poročila. Starih zapisov brez osnove ne backfillaj z ugibanjem.
- [ ] Predlagaj izvedljiv privzeti profil in opcijske stolpce za oba pogleda. Forward P/E brez dokaza je unverified, ne nadomestni TTM.
- [ ] Navedi, katere nove Flex sekcije uporabnik potrebuje, in omejitev starega uvoza: sedanji parser neznane sekcije zavrže, izvirnega XML pa ne arhivira. Uporabnik ga zasebno ohrani in po nadgradnji UX-19 ponovno uvozi; trenutni upload ni shranjen material za prihodnji parser.

### Prevzem UX-00

Vsaka zahtevana metrika ima stanje, izvor ali razlog nedokazanosti, oba pogleda imata primerljivo pokritost, predlagani stolpci so izvedljivi in ne tiho pretežno prazni. Nobene obljube, da so forward P/E, dividenda na delnico ali nove Flex sekcije že na voljo. Izvedbeni popravki pokritosti so nove ločene naloge z dokazanim vzrokom; raziskava jih ne izvaja prikrito.

## D. Predaja

Najprej zaključi A in B kot ločena popravka; C se lahko izvaja neodvisno. Ob prevzemu v novo vejo se BL-ID-ji preverijo v aktualnem backlogu. Specifikacija BL-189 ni rezervacija tujih sočasnih ID-jev.

Ohranijo se pravila: brez naročil, broker read-only, LLM samo prek vlog, sheme za meje, denar Decimal/numeric, viri in čas, SL/EN, izvorni dokumenti/uporabnikovi izpisi brez spreminjanja. Ta dokument je SPEC; njegovi neoznačeni testni pogoji niso trditev, da so popravki ali preverjanja že izvedeni.
