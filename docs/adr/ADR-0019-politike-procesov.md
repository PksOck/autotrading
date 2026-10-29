# ADR-0019: Shranjene politike procesov in paketnih analiz

**Status:** sprejeto za pregledno vejo · **Datum:** 2026-10-29 · **Seja:** S-017

## Kontekst

Obstoječi časovni sprožilci nimajo uporabniškega nadzora. Nov paket analiz potrebuje omejitev poskusov, skupno kvoto in zaščito pred sočasnim zagonom ali izgubo dostave ob izpadu vrste.

## Odločitev

- Politika procesa ima revizijo, omogočenost, IANA cono, dneve, lokalni dnevni ali intervalni urnik in dovoljeno okno. Obstoječi procesi privzeto ohranijo obstoječi urnik UTC; novi paket je onemogočen in samo ročen.
- Globalna pavza prepreči nove samodejne začetke. Tekoče delo se dokonča; izrecni ročni zagon je ločen in še vedno upošteva omogočenost, kvoto in okno, razen izrecne izjeme za okno.
- Nočno okno pripada začetnemu dnevu. Neobstoječa lokalna ura ob prehodu na poletni čas se preskoči, ponovljena se izvede enkrat. Intervali so zasidrani v UTC.
- Izvedba se najprej trajno zapiše v bazo z enoličnim procesom in časovnim mestom. Dostava v vrsto je ponovljiva; zaklep pri prevzemu, heartbeat in recovery preprečujejo sočasno izvedbo istega zapisa.
- Ročne, predlagane in paketne globoke analize uporabljajo isti transakcijski zaklep kvote ter zaščito pred aktivno analizo instrumenta. Predogled ne porabi kvote; sprejem ponovno preveri pogoje.
- Napaka analize sama ne sproži novega plačljivega poskusa. Sledi beležijo izid izvedbe, ne skrivnosti.

## Posledice

Omogočitev procesa in ponavljajoči urnik sta ločeni nastavitvi. V izoliranem demu ni procesnih delavcev ali ponudniških ključev: mogoče je pregledati kontrole in predogled, ne dokazati živih ponudniških izvedb. Nobeno dejanje ne odda naročila.
