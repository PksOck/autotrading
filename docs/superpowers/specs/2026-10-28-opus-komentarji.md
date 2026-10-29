# Pregled Opusovih komentarjev in prenos v SPEC

**Datum pregleda:** 2026-10-28/29. **Status:** pregledano in preneseno v osnutek; brez sprememb aplikacije.

**Izvor:** [načrt](../plans/2026-10-28-celovita-uxui-nadgradnja.md) pri commitu `28f2990`, kopija SHA256 `030CD7F3293E558FD21ADCBEB9750B00A58384CB9E117F5DDC638CDF259B32BF`. Izvorna Claudova datoteka ostaja nespremenjena. [Glavni SPEC](./2026-10-28-celovita-uxui-spec.md) in [Val −1 SPEC](./2026-10-28-val-minus-1-spec.md) zapisujeta natančnejše pogodbe.

## Prevzete usmeritve

| Komentar | Presoja in dokaz | Prenos |
|---|---|---|
| FIX-A/B pred UX valovi | Potrjeno v routes/signals.py, PeekPanel in proizvajalcih povezav; ne potrebujeta novega DataMeta | Val −1 A/B, ločena naloga/prevzem |
| Demo je obstoječ, ustavljen | Compose in skripta že obstajata; prejšnji connection refused ni dokaz pokvarjenega sklada | UX-01 je zagon/preverjanje scenarijev, ne nova platforma |
| UX-00 pred stolpci Pozicij/Watchliste | Trenutni API fundamentov ne izpostavi v Watchlisti; vir dela kazalnikov obstaja, pokritost ni potrjena | Read-only matriki capability in coverage |
| 1/46 kot pokritost | Opusov časovni posnetek, ne ponovno izmerjeno stanje | Ohranjen kot izvorni dokaz z omejitvijo, noben aktualni procent iz ugibanja |
| Flex za prejeto in accruale | Smiselna evidenčna meja, vendar sekcije še niso v parserju | Ločeni ledger/accrual/coverage modeli; nov uvoz po implementaciji |
| Isti nabor stolpcev za lastne/spremljane instrumente | Skupni registry, vendar modulni osnovni stolpci in enote/posebnosti ETF | Glavni SPEC §5–7; brez ponovnega sestavljanja metrik v vsakem modulu |
| ADR-0017–0020 pred odvisnimi sklopi | Predlogi, ne že sprejeti ADR; številke preveriti ob zapisu | Jasna vrata G-META/TABLE/AUTO/DIV, brez podvajanja Astrove ločene seje |

## Tehnične dopolnitve, ki preprečijo napačno implementacijo

1. **Urnik:** sam UTC ne ohrani lokalnega ponavljanja po DST. SPEC shrani IANA cono, lokalni čas/dneve/okno in politiko gap/fold/misfire; materializirane termine v UTC.
2. **DataMeta:** `loading/error` sta stanji odjemalca; transportna napaka ne izniči zadnjih podatkov. `partial` in `stale` lahko soobstajata. Market date ni fetch timestamp.
3. **Vzrok pokritosti:** UNKNOWN se trenutno poskuša pridobiti, preskoči se ETF. BL-174 je povezan z identiteto, ni dokazan edini vzrok 1/46; potrebno je preverjanje tekov in odgovorov.
4. **Fallback metrik:** dividendYieldIndicatedAnnual/currentDividendYieldTTM in payout TTM/Annual potrebujejo `source_field`/basis/period. Starega zapisa brez osnove ni dovoljeno označiti kot dokazani TTM.
5. **Ocena DPS:** osebni denarni prejemki niso zanesljiva celoletna dividenda na delnico. Deljenje z današnjo količino ni dovoljeno; potrebni so grossRate ali upravičena količina ob dogodku, popolna zgodovina in corporate-action osnova.
6. **Accrual ni cash:** Open Accruals pomeni odprte obračunane dividende, ne celotnega prihodnjega letnega koledarja. Koda Re lahko pomeni popravek, preklic ali razveljavitev ob izplačilu; sama ne dokazuje prejete gotovine.
7. **ID-ji:** cash uporablja račun + transactionID; accrual ima svoj ključ/snapshot, saj transactionID ni zagotovljen za vse sekcije. Manjkajočega ključa ne nadomestimo s simbolom in zneskom brez dokaza enkratnosti.
8. **ETF:** 0 samo pri ocenjenem cash izplačilu potrjeno akumulacijskega razreda z virom/časom. Neznana politika je missing; preteklih cash knjižb ne izničimo.
9. **FX:** FX iz stare knjižbe ni avtomatično veljaven za sedanjo projekcijo. Brez ustrezne osnove pokažemo zneske po valutah/partial subtotal.
10. **Instrument info:** uradni reference pri Financial Instrument Information ne navaja valute. Identiteto združimo po conid z OpenPosition/Trade/Cash; currency te sekcije ni obvezna pred vzorcem.
11. **Izpis pred nadgradnjo parserja:** sedanji Flex uvoz dodatne sekcije zavrže in originala ne hrani. Za poznejši UX-19 je potreben ponovni uvoz zasebno ohranjenega izpisa.
12. **Fixture:** »brez zneskov/računov« pomeni sintetične nadomestne vrednosti in ID-je z ohranjenimi povezavami; ne odstranitve obveznih številčnih polj.
13. **Signalni potek:** današnji GET že zapisuje status prek commit odvisnosti. FIX ohrani to semantiko pred filtrom; accepted/dismissed ne potekata. Nova prepoved eksplicitnega sprejema poteklega signala ni skriti del tega popravka.
14. **Varen Close:** history.length ne dokazuje notranje zgodovine. Pri neposrednem linku Close odstrani peek na isti poti; ne kliče slepega history.back().

## Dokazna podlaga IBKR

Preverjeno z branjem uradnih referenc 2026-10-29; opisi polj še niso dejanski vzorec XML konkretne Flex Query.

- [Open Dividend Accruals](https://www.ibkrguides.com/reportingreference/reportguide/open%20dividend%20accrualsfq.htm): quantity velja pred ex-date, gross rate je dividenda na delnico; sekcija opisuje odprte obračune do plačila.
- [Change in Dividend Accruals](https://www.ibkrguides.com/reportingreference/reportguide/change%20in%20dividend%20accrualsfq.htm): Re pokriva več vzrokov, zato ni samostojen dokaz cash prejema.
- [Financial Instrument Information](https://www.ibkrguides.com/reportingreference/reportguide/financialinstrumentinformationfq.htm): opisuje identifikatorje in kotacijo; polje valute v prikazanem seznamu ni navedeno.

Astrov pregled pred pisanjem SPEC je podal te ugotovitve z dokazi. Njegov poznejši celotni ponovni pregled končnih datotek ni bil zaključen zaradi omejitve uporabe; končni dokumentarni samopregled je opravil glavni agent. To ni zapis neodvisne odobritve celotnega končnega SPEC.

## Preostala dokazna vrata

Ni treba ponovno spraševati o že potrjenih stolpcih ali prioriteti FIX. Pred izvedbo pa ostanejo: dejanska matrika virov UX-00, sintetično anonimiziran razširjen Flex vzorec, obravnava redkih/popravljanih dividendnih dogodkov po tem vzorcu, arhitekturna presoja schedulerja in pregled treh UI postavitev. Ta vrata ne preprečujejo samostojnih FIX-A/B.
