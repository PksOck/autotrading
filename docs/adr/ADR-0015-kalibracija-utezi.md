# ADR-0015: Kalibracija uteži iz izidov signalov
**Status:** sprejeto · **Datum:** 2026-10-27 · **Seja:** S-012

## Kontekst
SCR-10 (BL-102) meri, kako uspešni so signali po vrsti in viru. Če se vir dolgo izkazuje slabše ali bolje od povprečja, naj ima njegov signal manj ali več moči. Hkrati velja ADR-0006: sistem ne sme sam spremeniti, kako odloča, brez človekove potrditve. Majhni vzorci so tudi hrupni in bi uteži premikali brez razloga.

## Odločitev
1. **Uteži so na skupino `vrsta:vir`.** Prilagodljivi sta samo priložnosti `catalyst:radar` in `entry:rule`. Opozorila na tveganje (`exit_warning`, `thesis_break`) in tvoji predlogi se nikoli ne utežijo navzdol: zgrešeno opozorilo stane več kot šum.
2. **Predlog računa deterministična koda** (`preza/domain/calibration.py`, brez LLM):
   - osnova je delež zadetkov vseh sistemskih signalov pri izbranem horizontu (tvoji predlogi ne štejejo);
   - skupina z manj kot 10 izidi ostane pri trenutni uteži (`low_sample`);
   - sprememba se predlaga samo, ko 95 % Wilsonov interval deleža zadetkov skupine ne vsebuje osnove;
   - nova utež = (zadetki + 10 · osnova) / (n + 10) / osnova, zaokrožena na 0,01 in omejena na [0,50; 1,50].
3. **Utež pomnoži moč novega signala pred pragom** (`radar/signals.py`, `entries/service.py`), rezultat ostane v [0; 1]. Obstoječi signali se ne preračunajo.
4. **Sprememba samo z izrecno potrditvijo.** Stanja kompleta: `proposed`, `active`, `rejected`, `superseded`. Aktiven je največ en komplet. Potrditev zahteva `{"confirm": true}`. Ponovni predlog zastari starejšega (409 `not_pending`). Če so se aktivne uteži od predloga spremenile, potrditev vrne 409 `stale_proposal`. Predlog brez spremembe se ne da potrditi (422 `no_changes`).
5. Komplet hrani `basis` (celoten izračun), zato je pozneje vidno, iz katerih izidov je utež nastala.

## Posledice
- Uteži se premikajo počasi in samo ob dovolj velikem, statistično jasnem odmiku.
- SCR-10 ima razdelek »Predlog uteži« z dvostopenjsko potrditvijo.
- Migracija 0015 doda tabelo `signal_weight_set`.
- Brez potrjenega kompleta vsak vir šteje z 1,00, kar je enako kot pred BL-103.
