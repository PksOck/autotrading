# ADR-0025: Ločene metode izidov brez prepisovanja zgodovine

**Status:** sprejeto v pregledni veji · **Datum:** 2026-10-31 · **Seja:** S-026

## Kontekst

BL-228 reproducira razliko med shranjenimi SignalOutcome in študijo ADR-0022 na istem sintetičnem zapisu. Stari izračun uporabi prvi zaključek na UTC datum signala ali pozneje, izstop N shranjenih sej pozneje in nobenih stroškov. Vsako smer razen `down`, tudi `neutral`, obravnava kot dolgo. Njegov manjkajoči benchmark ostane null. Študija izbere prvi zaključek strogo po UTC datumu razpoložljivosti, odšteje strošek obeh nominalov in nevtralno/neznano smer preskoči. Zato odstotki in imenovalci niso zamenljivi.

Stare vrstice nimajo shranjene verzije metode ali cenovnega posnetka. Trenutna koda ni dokaz o izvoru vsake zgodovinske vrstice. Živih uporabnikovih podatkov v tem krogu ne beremo; dejanski obseg vpliva je neznan.

## Odločitev

- Globalni izidi in njihovi API povzetki imajo `method_id=legacy-unversioned`. Oznaka pošteno opisuje neoznačeno zgodovino, ne pripiše izmišljene verzije starim vrsticam. Matematika in obstoječi producent ostaneta nespremenjena, vključno z zgodovinsko obravnavo neutral; UI to omejitev pojasni in je ne združi z novo študijo.
- Vsak nov izračun študije ADR-0022 vrne `method_id=saved-record-after-utc-close-v1`. To verzionira deterministično metodo tega izračuna, ne zagotavlja point-in-time nespremenljivosti ali prilagoditve zgodovinskih cen.
- Sprememba vstopnega pravila, razlage smeri, štetja sej ali stroškov zahteva novo identiteto metode in ohranitev karakterizacijskih testov v1.
- Pogodba API doda opisano identiteto metode. Stare povezave, filtri, `source=all` in izbor signalov/zaključenih analiz ohranijo isti pomen; ni novih idej v legacy obsegu. UI uporabi kratek opis in dosegljive podrobnosti, ne tehnične oznake v glavnem toku.
- Ni tihe migracije, retroaktivnega popravljanja datumov ali stroškov, ponovnega računanja SignalOutcome ali odstranjevanja neutral vrstic. Novi osebni izbor T3–T4 uporablja verzionirano študijo in izrecne preskoke.
- Morebitna zamenjava globalnega producenta zahteva ločeno migracijo z vrstično identiteto, ohranjenim legacy rezultatom, ločenimi imenovalci/preskoki in obnovitvenimi vrati. Nov izračun ne more tiho nadomestiti starega.

## Posledice

Obstoječa statistika ostane reprodukcija starega prikaza z jasno omejitvijo; označitev ni popravek njenega matematičnega pomena. Testi zajamejo smeri, isti/naslednji trgovalni dan, 20 shranjenih sej, stroške in neznani benchmark ter na izolirani bazi dejanski nevtralni signal. Cenovna študija ni sestavljeni donos portfelja ali dokaz kakovosti agentove celotne strategije.

## Zavrnjene možnosti

Tiho spremeniti `neutral` v preskok v obstoječem producentu bi pustilo mešanico starih in novih imenovalcev. Pripisati v1 vsem zgodovinskim vrsticam bi izmišljeno potrdilo njihovo metodo. Masovni backfill brez arhiva, cenovnih posnetkov in restore dokaza ni del dovoljenega pregleda.
