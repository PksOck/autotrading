# ADR-0008: Instrumenti: ameriške delnice + UCITS ETF-ji
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-002

## Kontekst
Uporabnik je mali vlagatelj iz EU pri IBKR. Zaradi uredbe PRIIPs (obvezen KID) ameriški ETF-ji (npr. SMH, VOO, XLE) za male vlagatelje v EU niso na voljo. Ameriške delnice so na voljo.

## Odločitev
- **Delnice:** ameriške (NYSE, NASDAQ) in po potrebi evropske.
- **ETF-ji:** samo **UCITS** (LSE, Xetra, Euronext), seznam v konfiguraciji univerzuma. Ameriški ETF-ji se uporabljajo samo kot **referenca** (npr. sektorski benchmark za odziv cene), nikoli kot predlog za nakup.
- Instrument ima `domicile`, `ucits: bool`, `tradable_for_user: bool`, borzo in valuto (USD, EUR, GBP). UI predlaga samo instrumente s `tradable_for_user = true`.
- Valuta se prikazuje v valuti kotacije. Preračun v EUR je samo informativen in označen.

## Posledice
- ETF profili (BL-027) se berejo pri izdajateljih UCITS (iShares, Vanguard, Xtrackers, Invesco, VanEck) in prek IBKR contract details.
- Isti indeks ima lahko več UCITS različic (akumulacijska/distribucijska, valuta). Prednost ima tista, ki jo uporabnik že ima.
