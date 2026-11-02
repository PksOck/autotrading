# ADR-0026: Denarne ocene samo z dokazljivo valuto in datumom

**Status:** sprejeto v pregledni veji · **Datum:** 2026-11-01 · **Seja:** S-027

## Kontekst

Uporabnik želi dnevni premik portfelja in mesečni dividendni prihodek. Uvožene količine so posnetek, svečke imajo druge datume, obstoječi Position pa hrani fx_rate_to_base brez dokazila o ciljni valuti. Letna dividendna ocena ne vsebuje potrjenega urnika nakazil. Kozmetična razdelitev teh podatkov bi ustvarila navidezno natančne dnevne/mesečne zneske.

## Odločitev

- Dnevni prikaz je ocena cenovnega premika istih uvoženih količin med zadnjima dvema zaključkoma. Odstotek ima isto osnovo pri obeh cenah. Gotovina, posli in dnevni vpliv FX niso vključeni; to ni izmerjena sprememba vrednosti celotnega računa.
- Konsolidirana tuja valuta zahteva dokaz ciljne valute FX. Ker ga trenutni uvoz še ne hrani, odgovor ostane neznan. Uporaben nadomestni prikaz so izvorne valute posebej, brez pretvorbe in brez seštevanja njihovih odstotkov. Skupina z vrzeljo ostane vidna. Valuta pozicije mora ustrezati valuti instrumenta.
- Vse količine v skupini potrebujejo razrešeno identiteto, sveže in usklajene pare pozitivnih cen. Short pozicije še niso podprte. Delni rezultat ni skupni rezultat; ničla je dovoljena samo kot dejanski izračun.
- Koledar uporablja datum knjižbe za prejeti denar in pay_date za odprti obračun. Brez datuma ostane nerazporejeno. Bruto, neto in valute so ločeni; vsote so Decimal na strežniku. Podatkovni razpon izbranih knjižb ne omeji dokazov za preprečevanje dvojnega štetja iste odprte akcije.
- Prejeti denar in odprti obračun iste akcije zahtevata uskladitev; ne štejeta kot dve plačili. Letna ocena trenutnih količin ostane ločena in se ne deli z 12.

## Posledice

Dokler uvoz ne hrani preverjene osnovne valute, tuje pozicije nimajo skupne dnevne ocene v EUR. To ne popravlja stare predpostavke FX pri obstoječi vrednosti portfelja; podatkovna razširitev ostaja odprta. Prihodnji koledar je lahko redek: nov vir objavljenih datumov potrebuje svojo pogodbo in preverjanje. Zasebni razširjeni Flex XML ostaja nepreverjen (BL-202).

## Dopolnitev S-028, 2026-11-02: letna osnova

Izbirnik Dan/YTD ob vrednosti portfelja ostane cenovna ocena istih trenutnih količin. YTD potrebuje zaključek pred1. januarjem tekočega UTC leta (največ7 dni prej), isti vir in dokaz usklajenosti začetne/zadnje cene ob korporativnih dejanjih. Isti ponudnik ni dokaz usklajenosti ob splitu. Ker model Bar ne hrani takega dokazila, produkcijski YTD ostane neznan z razlogom unverified_price_basis; ni zgolj odstotek z opozorilom. Interni basis_verified je privzeto false in se ne nastavi samo na podlagi imena ponudnika. Sintetični preverjeni primer potrjuje Decimal izračun, ne pokritosti živega vira. Pridobitev dokazljive zgodovine je ločena BL-234.

## Zavrnjene možnosti

Ne privzamemo, da je vsak FX uvoz v uporabnikovi nastavljeni valuti. Ne uporabljamo delne vsote kot premika portfelja. Ne enačimo ex-date z datumom prejema in ne pretvorimo letne ocene v izmišljen mesečni urnik.
