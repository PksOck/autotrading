# ADR-0023: Trajni kurzor omejene dostave opravil

**Status:** sprejeto za pregledno vejo · **Datum:** 2026-10-30 · **Seja:** S-023 · **Naloga:** BL-218 / A4

## Kontekst

Omejitev prvih 100 pending opravil lahko izstrada poznejše dovoljeno opravilo. Sam filter politik ne zadostuje: že dostavljena in deduplicirana opravila ostanejo pending do prevzema. Branje celotne vrste bi imelo neomejeno delo, procesni kurzor pa bi po restartu izgubil napredek.

## Odločitev

- Pred LIMIT filtriramo upravičene kombinacije procesa, izvora in okna ter trajno zastarele revizije. Začasna blokada ohrani pending namen, zastarela revizija postane skipped.
- Migracija 0020 doda interni singleton `automation_outbox_cursor` s stabilnim parom `(scheduled_for, execution_id)` in indeks nad `(state, scheduled_for, id)`. Par je hkrati prisoten ali odsoten in ni FK na pozneje očiščeno izvedbo.
- Transakcijski poskusni advisory lock in row lock omogočita enega dostavljalca brez čakanja drugega, tudi ob inicializaciji kurzorja. Kurzor potrdi klicatelj skupaj s spremembami dostave.
- Tick pregleda največ 1000 kandidatov in sprejme največ 100 novih dostav. Napredovanje preživi restart; naslednji prehod po koncu ponovno zajame starejše ali ponovno omogočene namene.
- Identiteta posla in atomarni worker claim ostaneta zaščita pred dvojnim delom. Dostava ne pomeni ponovitve že začetega modelnega klica. Obstoječa ničelna arq retencija omogoča ponovno dostavo istega še pending namena po odpravi začasne blokade.

## Posledice

Potrebujemo novo interno tabelo in potrjeno transakcijo po dostavi. Vrstni red je pošten med prehodi, ni pa zagotovilo trenutnega začetka vsakega opravila. Varovalke se ponovno preverijo ob claim in pred zunanjim modelnim poskusom. Migracija je v tem krogu uporabljena samo na ločenih testnih in sintetični demo bazi; živa namestitev ostane ločen prevzem z backup/restore.
