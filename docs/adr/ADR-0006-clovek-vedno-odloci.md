# ADR-0006: Človek vedno odloči, brez samodejnih naročil
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-001

## Kontekst
LLM odločitve niso ponovljive, backtesti agentov so pristranski (model "pozna" preteklost), napaka pri naročilu pa pomeni realno izgubo.

## Odločitev
- Sistem **nikoli** ne odda naročila brez izrecne potrditve uporabnika za to konkretno naročilo.
- IB Gateway teče z **Read-Only API** do mejnika M7. Za API se uporablja **ločen IBKR uporabnik** brez pravic za dvige.
- M7 začne na **paper računu**. Prehod na živi račun zahteva nov ADR na podlagi podatkov iz M5.
- Varovala v M7: samo limit naročila, seznam dovoljenih simbolov, največja velikost in dnevna izpostavljenost, kill switch, dvojna potrditev, revizijska sled.

## Posledice
- Vrednost sistema je v kakovosti signalov in razlag, ne v hitrosti izvedbe.
