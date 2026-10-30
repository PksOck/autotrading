# BL-222 — omejeni neodvisni pregled SPEC/plana

**Končni dokumentarni izid: PASS.** Vse tri prvotne ugotovitve so **ADDRESSED**; ni preostale zahtevane spremembe iz tega pregleda. Produktna implementacija ni pregledana ali zatrjevana.

## Omejeni ponovni pregled popravkov

Ponovno preverjene so samo tri ugotovitve spodaj v zamrznjenem SPEC in planu; brez ponovnega celotnega pregleda ali runtime dela.

| Ugotovitev | Status | Preverjeni popravek |
|---|---|---|
| 1 — manual pri enabled=false | **ADDRESSED** | SPEC vrstice 62/66 določajo zaupanja vreden origin scheduled/manual, enabled pogoj samo za scheduled ter aktualno revision in ponovno target preverbo za oba. Sprememba revision preskoči še pending stari namen; tekoči uporablja svoj snapshot. F-BK04:101 in plan T3:81/83 izrecno zahtevata en manual fake dump pri enabled=false, nič scheduled dumpov ter blokado ob stale revision/neveljavnem cilju za oba. |
| 2 — trajnost imeniške objave | **ADDRESSED** | SPEC:74 in plan T2:69/71 določajo file fsync → partial-directory fsync → rename → final-parent fsync → SQL checksum_verified/retention. Napaka ali nepodprta imeniška durability operacija pomeni publish_failed brez retention; redelivery preveri tudi parent fsync. F-BK06:103 in imenovana testa zajameta vrstni red ter napaki obeh imeniških fsync. |
| 3 — podatki za retention | **ADDRESSED** | Plan T2:67 loči BackupArtifact od popolnega BackupRetentionEntry v T4:91. Vhod vsebuje ID, source/target/root, UTC čase, snapshot cono, stanja, pins, hasha in ownership preverbo; nepopolno/nepreverjeno se ne briše. Čisti izbor je brez I/O (T4:94), z zaščitami in stabilnim `(finished_at, backup_id)` vrstnim redom. SPEC BK-08:80 ter testi T4:93 se ujemajo: stari datum/ISO teden izhaja iz cone konkretne kopije in ga nova politika ne reinterpretira. |

Vsi navedeni testi so **zahteve prihodnje izvedbe**, ne trditev o izvedenih testih. PASS potrjuje dokumentarni pogodbi in plan v pregledanem obsegu; ne pomeni implementiranega BL-222 ali dovoljenja za aktivacijo/deploy/restore.

## Prvotne ugotovitve — zgodovinski zapis, vse odpravljene

1. **Important — ročni zagon pri izključenem urniku ima nasprotujočo worker pogodbo.** SPEC `docs/superpowers/specs/2026-10-30-nastavitve-varnostnih-kopij-spec.md:22` izrecno dovoljuje manual kopijo pri enabled=false, vrstica 62 pa zahteva ponovni enabled/revision pregled brez izjeme glede izvora, vrstica 66 celo pravi, da enabled=false ustavi kopije. T3 plana (vrstica 83) te razlike ne razreši. Izvedba, ki sledi temu guardu dobesedno, sprejeti manual namen preskoči. Določite, da enabled pogojuje samo scheduled/catch-up namene; manual ima ekspliciten origin in ponovno preverbo revision/target/readiness, ki ga izključen urnik ne zavrne. Dodajte test `manual_backup_runs_while_schedule_disabled` ter ohranite test, da disabled ne materializira scheduled slotov. Pojasnite tudi, kako sprememba revision po sprejetem manual namenu vpliva na njegov snapshot; ni treba uvajati novega obsega.

2. **Important — atomarna objava še nima polne meje trajnosti pred retention.** SPEC vrstica 74 in T2 plana vrstici 71/73 zahtevata fsync podatkov/manifesta in nato rename, ne določita pa fsync začasnega imenika in nadrejenega imenika po rename. Sam fsync datotek in atomarni rename ne zagotavljata, da po izpadu sistema preživi tudi nova imeniška povezava; če SQL že označi checksum_verified in retention pobriše prejšnjo kopijo, je mogoče izgubiti obe. Zapišite zaporedje file fsync → temporary-directory fsync → same-filesystem rename → parent-directory fsync → SQL uspeh/retention. Če platforma/backend take trajnosti ne podpira, naj vrne varen publish/durability neuspeh in ne sproži retention. Razširite fake fsync test z napako zadnjega parent fsync: prejšnja kopija ostane in ni cleanup. To dopolni že načrtovano atomarno objavo, ne zahteva nove funkcije.

3. **Important — retention funkcija nima določene pogodbe potrebnih metapodatkov.** Plan vrstica 67 definira BackupArtifact z basename/hash/size/checksum fazo, T4 vrstica 91 pa `retention_candidates(list[BackupArtifact], policy) -> list[UUID]`. BK-08 (SPEC vrstica 80) zahteva razvrstitev po uspešnih datumih/ISO tednih, najnovejšo restore_verified kopijo in pins; opisani vhod nima niti eksplicitnega backup_id niti časov, restore/pin stanja oziroma preverjene identitete source/target. Dopolnite BackupArtifact ali določite ločen RetentionRecord z minimalnimi potrebnimi polji in jasnim virom teh podatkov iz preverjenega manifesta/SQL; izračun mora biti čist in ne sme tiho poizvedovati za manjkajočimi podatki. Določite tudi, ali lokalne datume vseh artefaktov preračuna iz časovne cone snapshot politike izvajajočega retention runa (kot predlaga T4:94), da sprememba cone ne pusti dveh interpretacij. Obstoječe retention teste uporabite za dokaz teh vhodov in exact ID nabora izbrisa.

## Sicer skladno

- Uporabnikova izbira istega diska in nastavljive lokacije/pogostosti je dosledno izražena; disabled/unconfigured je privzeto, dejanska mapa ni izmišljena. S-F5 SF5-01 in BL-017/222 sta s tem usklajena; ločeni restore cilj in dejanski predmigracijski dokaz ostaneta obvezna.
- Aktualna Compose datoteka ima PG17 Timescale sklad in imenovan pgdata volumen; API Dockerfile še nima pg_dump/pg_restore in nobena obstoječa backup služba ni predpostavljena. Predlagani ločeni build/worker in vnaprej dovoljen bind root sta izvedljiva. Ne sme uporabiti sedanjega `*api-env`, saj ta vsebuje ponudniške/SMTP/broker poverilnice; SPEC BK-04 to že izrecno prepoveduje.
- Host/container pot, marker, path containment, reparse/symlink zavrnitev, argv brez shell, ACL in odsotnost Docker socketa so določeni. Nova root pot zahteva namestitveno preslikavo; UI dobi alias/podmapo, kar je pošteno omejen obseg izbire poti.
- Urnik se ujema z obstoječim `domain/automation.py:115–149`: UTC shranjevanje, IANA lokalni čas, fold=0 in preskok neobstoječe ure. RPO 24 h ni lažno zagotovljen, weekly/DST/catch-up imajo načrtovane preverljive teste.
- Revision CAS, trajni request_id/nameni, ločeni validation status, bounded seznami ter crash/recovery bariera so konkretno načrtovani. GET ne dumpa in 202 ne pomeni uspešne kopije.
- Konsistenten izvoženi snapshot za dump in kontrolna štetja, checksum/restore razlika, izključitev skrivnosti ter sintetični izolirani restore z onemogočenimi transporti so jasno ločeni. Settings nima produkcijskega restore gumba. Kopija ni predstavljena kot celoten disaster-recovery paket ali kot šifrirana samo zaradi ACL.
- T1–T6 imajo imenovane vmesnike, ciljne teste in integracijska vrata; BL-222 ni označen kot implementiran. S-F5/S-H živa vrata se ne zaprejo s sintetičnim dokazom.

## Meja pregleda

Brani so novi SPEC/plan, S-F5, ustrezni BACKLOG vnosi ter neposredno relevantne statične definicije Settings, urnika, Compose/API slike, migracijskega registra in testnih ukazov. Brez runtime ukazov, DB/dump/restore, branja `.env` ali skrivnosti, produktnih/testnih sprememb, tracked dokumentarnih sprememb, commitov ali deploya. Edini zapis je to scratch poročilo.
