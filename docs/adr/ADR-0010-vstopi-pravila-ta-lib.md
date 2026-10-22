# ADR-0010: Vstopi: pravila s TA-Lib, signal samo z nedotaknjeno tezo
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-004

## Kontekst
M3 mora povedati, kdaj je kakovostna delnica ali ETF na dobri ceni, in ločiti "poceni z razlogom" od "začasno poceni" (research §5.3). Številke (cone, stop, lestvica, vrednotenje) morajo biti deterministične (AGENTS.md §3.3), vzrok padca pa je presoja.

## Odločitev
- **Indikatorji v backendu s TA-Lib** (`ta-lib` ≥ 0.6.5 ima kolesa z vgrajeno C knjižnico, zato v Dockerju ni sistemske odvisnosti). Spletna aplikacija ostane na trading-signals. Test `tests/test_indicator_parity.py` primerja oba na skupnem posnetku (`pnpm --dir apps/web gen:indicator-fixture`). SMA in RSI se ujemata od prve vrednosti; ATR ima drugačen začetek (trading-signals šteje razpon prve sveče, TA-Lib začne svečo kasneje), razlika po Wilderjevem glajenju izgine, zato ga primerjamo po 100 svečah.
- **Pravila so konfiguracija** v `services/api/preza/entries/rules.yaml` z `version`. Pragove spreminjamo tam, ne v kodi.
- **Cona:** sidro je testirana podpora (SMA200 ali 52-tedenski minimum), sicer cena, ko se sproži pravilo, sicer SMA200 (raven, na katero čakamo). Širina ±0,5 ATR, stop 1,5 ATR pod cono.
- **Lestvica** začne pri nižji od zgornje meje cone in trenutne cene (nobenega limita nad trgom), koraki po 1 ATR, nikoli pod stopom.
- **Signal `entry`** nastane samo, ko je cena v coni ali pod njo **in** `dip_analyst` oceni vzrok kot trg, sektor ali začasno **in** teza drži. Temeljni vzrok pri poziciji v portfelju da `thesis_break`. Brez modela ni signala (kandidat je viden, vzrok "čaka na analizo"). Zavrnjen signal se ne ponovi, dokler cena ne zapusti območja ("daleč").
- **`dip_analyst`**: `local-reason`, ob nedosegljivosti `cloud-quick`. Ponovna analiza po 3 dneh ali ob novem dogodku. Govorice same ne morejo utemeljiti temeljnega vzroka.
- **Vrednotenje** iz Finnhub `/stock/metric` (P/E, EV/EBIT, FCF donos proti 5-letni zgodovini), tedensko. Polja še niso preverjena na pravem omrežju (BL-066).
- **Izidi signalov** (1/5/20/60 trgovalnih dni, alfa proti `BENCHMARK_SYMBOL`, privzeto SPY) se računajo vsak delavnik ob 22:40 UTC.

## Posledice
- Docker slika API vključuje numpy in TA-Lib kolesa (~10 MB).
- Za UCITS portfelj je SPY samo referenca (`tradable_for_user = false`); primerjalni indeks lahko zamenjaš v `.env`.
- Kalibracija pragov (M5) bo primerjala izide po `rules.yaml` verziji.

## Zavrnjene možnosti
- **Lastni indikatorji v Pythonu** (stanje M1): brez neodvisne reference; TA-Lib je industrijski standard.
- **pandas-ta:** težja odvisnost (pandas) in manj stabilne definicije.
- **Signal ob vsakem zadetku pravila:** preveč šuma in "poceni z razlogom" bi izgledalo kot priložnost.
