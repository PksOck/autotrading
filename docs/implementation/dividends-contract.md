# Dividende: podprta pogodba in preverjanje

Izvedba BL-198, ADR-0020. Zasebni razširjeni izpis uporabnika ni bil dosegljiv.
Spodnje oblike so **sintetična testna pogodba**, ne trditev o vseh dejanskih izvozih IBKR.
Uradne reference in dokazne omejitve so navedene v ADR-0020.

## Parser

`preza.broker.dividends.parse_dividend_statement(xml) -> DividendStatement` bere
`FlexStatement` z `accountId`, `fromDate`, `toDate`. Podprt datum je `YYYYMMDD` ali
`YYYY-MM-DD`; po podpičju je lahko čas. `as_of` pomeni dnevno UTC mejo poročanega datuma,
ne izmišljenega trenutka generiranja ali pridobitve.

| Sekcija / vrstica | Obvezno | Opcijsko |
|---|---|---|
| `CashTransactions/CashTransaction` | `transactionID`, `type`, `amount`, `currency`, `dateTime` ali `reportDate` | `accountId`, `symbol`, `conid`, `actionID`, `settleDate`, `fxRateToBase` |
| `OpenDividendAccruals/OpenDividendAccrual` | `currency`, `exDate`, `conid` ali `symbol` | `accountId`, `actionID`, `payDate`, `quantity`, `grossRate`, `grossAmount`, `tax`, `netAmount`, `fxRateToBase` |
| `ChangeInDividendAccruals/ChangeInDividendAccrual` | enako kot odprti obračun | enako + `code` |
| `FinancialInstrumentInformation` | zaznava prisotnosti | vsebina ostane vidna kot delna pokritost; ne ugibamo manjkajoče valute ali identitete |

Vrste gotovine: `Dividends`, `Payment In Lieu Of Dividends`, `Payment In Lieu`,
`Withholding Tax` (neobčutljivo na velikost). Druge običajne gotovinske vrste (vplačilo,
obresti) ne sodijo v dividendno evidenco. Nepodprta dividendna vrsta ali vrstica dobi
vrzel. Manjkajoč transactionID ne dobi izmišljenega ID-ja. NaN/Infinity ni denar.
Opisov transakcij ne uporabljamo za sklepanje o davku, identiteti ali vrsti.

FX se ohrani s poročano osnovo. Ker ta pogodba še ne potrjuje identitete osnovne
valute, API ne prikazuje pretvorjene vsote, tudi če je sam `fxRateToBase` prisoten.
Posamezne originalne valute ostanejo pravilno ločene.

## Povezava uvoza

`FlexStatement.dividends` vsebuje izhod parserja. `store_statement` pokliče
`store_dividend_data(session, parsed)` v isti transakciji kot pozicije/gotovino.
To pokrije datotečni uvoz in nočno Flex sinhronizacijo. Napačna ponovna vsebina iste
identitete zavrne celotno transakcijo; zunanji XML ni arhiviran.

`GET /portfolio/dividends` podpira `account_id`, `currency`, `from_date`, `to_date`.
Datumi filtrirajo cash po knjižnem datumu ter accrual po pay-date (sicer ex-date).
Projekcija ostaja pogled trenutnih pozicij in prihodnjih 12 mesecev.

## Primer za izoliran demo

Uporabite samo sintetične račune/simbole. `tests.test_dividends.xml` in `event`
generirata sintetični prejem 100, podpisan storno -20, povezan davek -15 ali
nepovezan davek. Dodajte odprt obračun bruto 20 s prihodnjim pay-date in prazno
novejšo odprto sekcijo za dokaz izpraznitve. Noben obračun se ne prišteje cash vsoti.

Za projekcijo dodajte `DividendProjectionBasis` z validiranim `ProjectionBasis`
v `payload` in enako `annual_per_share` v numeric stolpcu. `basis=indicated_annual`,
`source=synthetic_issuer`, DPS 4, trenutna količina 25 pomeni bruto oceno 100.
Za akumulacijski razred uporabite `basis=accumulating_share_class`, brez DPS.
Za nepodprt instrument ne dodajte osnove: UI prikaže `incomplete_history`.

## Izvedeno preverjanje

- RED: manjkajoč parser/domain modul; GREEN: 8 pogodb/izračunov.
- RED: manjkajoč frontend modul; GREEN: error/retry ter vrzeli/URL filtri.
- Ločena baza `codex_dividends_test`: idempotenca/konflikt, več računov, prazen
  nov posnetek, prodan instrument, akumulacijski razred in valutni filter.
- Testni fixture je v kodi izrecno sintetičen. V repozitoriju ni pristnih računov,
  zneskov ali razširjenega osebnega XML. Živa popolna pogodba ostaja nepreverjena.
