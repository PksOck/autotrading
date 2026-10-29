# ADR-0017: Metapodatki metrik in skupni bralni modeli

**Status:** sprejeto za pregledno vejo · **Datum:** 2026-10-29 · **Seja:** S-017

## Kontekst

Portfelj in watchlista potrebujeta iste kazalnike, vendar datum prenosa ni fiskalno obdobje, TTM ni forward in neznana valuta ni USD. Zadnji globalni datum pozicij izgubi račune s starejšim izpisom.

## Odločitev

- `DataMeta` loči vir, izvorno polje, osnovo, obdobje, datum trga, pridobitev, razpoložljivost in zastarelost. `MetricValue` vrne decimalni niz z enoto in metapodatki. Manjkajoče vrednosti ostanejo null z razlogom.
- Skupni `market_context` bere shranjene podatke v paketih. GET ne sproža ponudniških klicev. Forward P/E se ne nadomešča s P/E TTM; dividendni donos ni denarni DPS.
- Zadnji celotni posnetek se izbira po računu. Deklariran prazen posnetek nadomesti prejšnje pozicije; odsotna sekcija ni prazen posnetek. Brez potrjenega FX konsolidirana vrednost ostane nepopolna.
- Dopolnitev identitete je izrecna, preveri instrument ID in verzijo ter ne prepisuje znanih polj. Finnhubova valuta poročanja ni dokaz valute trgovanja.

## Posledice

Prikazi ostanejo uporabni ob delni pokritosti. Stari podatki brez dokazljive osnove ne dobijo izmišljene svežine. Živa zapolnitev vrzeli in razrešitev neznanih kotacij sta ločeni nalogi.
