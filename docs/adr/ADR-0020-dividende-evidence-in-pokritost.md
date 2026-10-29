# ADR-0020: Ločene dividendne evidence in izrecna pokritost

- Datum: 2026-10-29
- Status: sprejeto za izvedbo BL-198; živa razširjena pogodba XML ostaja dokazna vrzel

## Kontekst

Osebni prejemki ne dokazujejo distribucije na današnjo enoto pozicije. Obračunana
upravičenja niso prejeta gotovina, odsotna sekcija pa ne dokazuje ničelnih prejemkov.
Obstoječi uvoz izvirnega XML ne hrani. Razširjen očiščen uporabnikov vzorec ni na voljo.

Uradna referenca potrjuje pomen polj, ne celotne uporabljene XML sheme:

- [Cash Transactions](https://www.ibkrguides.com/reportingreference/reportguide/cash%20transactionsfq.htm): podpisani zneski in vrste denarnih knjižb.
- [Open Dividend Accruals](https://www.ibkrguides.com/reportingreference/reportguide/open%20dividend%20accrualsfq.htm): količina pred ex-date, gross rate in bruto/neto obračun.
- [Change in Dividend Accruals](https://www.ibkrguides.com/reportingreference/reportguide/change%20in%20dividend%20accrualsfq.htm): `Re` lahko pomeni popravek, preklic ali razveljavitev ob izplačilu; sam ne dokazuje gotovine.

## Odločitev

1. Denarne knjižbe so nespremenljiva evidenca z enoličnostjo
   `(broker, account_id, transaction_id)`. Enaka ponovitev ne doda gotovine;
   neskladna vsebina zavrne celoten uvoz. Nov datum ponovnega izvoza ni sprememba knjižbe.
2. Odprti obračuni imajo ločen naravni ključ instrumenta/dogodka in dnevni posnetek.
   Spremembe se hranijo kot `change:<code>` in niso del gotovinskih vsot. Zadnja
   prisotna odprta sekcija računa velja tudi, če je prazna. Neskladna revizija istega
   dnevnega naravnega ključa zahteva razrešitev; ne prepišemo zgodovine.
3. Pokritost se hrani po računu, sekciji, poročanem obdobju in dnevnem posnetku.
   Stanja so `missing`, `partial`, `complete`; `complete` pomeni uvoz podprte sekcije,
   ne neodvisne potrditve celotne brokerjeve evidence. Datum `as_of` je UTC meja
   poročanega `toDate` (`as_of_basis=statement_report_date_utc_boundary`). Neznane
   časovne cone `whenGenerated` ne razglasimo za UTC čas pridobitve.
4. Zneski ostanejo `Decimal`, denarni stolpci so `numeric(28,10)`, API jih vrne kot
   decimalne nize. JSONB ohrani validirano vsebino in izvor; ni arhiv zasebnega XML.
   Manjkajoč davek ali FX ostane `null`. Davek povezujemo samo z eksplicitnim
   action ID ter računom/instrumentom/valuto. Nepovezani odtegljaji ostanejo vidni.
5. Projekcija uporablja samo preverjeno indicirano letno distribucijo ali izrecno
   potrjen TTM na enoto. Osebna zgodovina prejemkov, dividendni donos in trenutna
   količina niso nadomestek za DPS. Brez osnove je razlog `incomplete_history`.
   Potrjen akumulacijski razred ima nič ocene gotovine iz sklada, pretekle knjižbe
   pa ostanejo. Projekcija ne uporablja FX iz stare osebne knjižbe.
6. Fizične XML oblike so stroga podprta pogodba, preizkušena s sintetičnimi primeri.
   Osebni XML ni shranjen v repozitoriju. Nepodprti tagi/polja dobijo vrzel;
   `FinancialInstrumentInformation` je za zdaj zaznana sekcija, vsebina pa ostane
   `instrument_metadata_not_ingested`. Uporabnik vidi omejitev in navodila za ponovni
   zasebni uvoz. Nismo potrdili vseh dejanskih konfiguracij IBKR izvoza.

## Posledice

Denar, odprta upravičenja in prihodnja bruto ocena imajo ločene poglede in se ne
seštevajo. Pretekli denar prodanih instrumentov je ohranjen. Podatkovne vrzeli ostanejo
vidne. Za širšo produkcijsko pokritost je potreben zasebni očiščen razširjen izpis ter
potrditev njegovih tagov, identitet, referenc in valutne osnove. To je odprta integracijska
omejitev, ne dovoljenje za ugibanje podatkov ali proizvodnjo lažnega denarnega toka.
