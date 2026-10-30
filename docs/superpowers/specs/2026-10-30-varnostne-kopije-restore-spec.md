# S-F5 · Varnostne kopije in dokaz obnove

**Status: NEXT-SPEC / CONDITIONAL PROPOSAL.** 2026-10-30. BL-017/214; odvisnost BL-215. Ta priprava ne izdeluje kopije žive baze, ne bere skrivnosti in ne izvaja migracij. Cilj kopij, pravice, hramba in dovoljen obnovitveni cilj še niso potrjeni.

Podlage: [glavni načrt F5/H](../plans/2026-10-30-zakljucevanje-odprtih-sklopov.md), [neposredni SPEC §8](./2026-10-30-dodatni-krog-claude-spec.md), [S-H](./2026-10-30-prevzem-in-prenos-spec.md). **Zavezujoča omejitev:** uspešna obnova na ločeni bazi je predpogoj pred prvo živo migracijo, tudi pred že pripravljenimi **0016–0020**. Sam dump ali zelen demo ni dokaz obnovljivosti.

**Dopolnitev S-024 po uporabnikovem odgovoru:** lokacija in pogostost bosta nastavljivi v aplikaciji; cilj še ni izbran, uporabnik običajno uporablja isti disk. Zahteva ločenega diska iz stare SF5-01 je s tem nadomeščena: dovoljen je isti disk, jasno pa je prikazano, da taka kopija ne ščiti pred njegovo odpovedjo. Ločena obnovitvena baza ostaja obvezna. [BL-222 SPEC nastavitev](./2026-10-30-nastavitve-varnostnih-kopij-spec.md) in [izvedbeni plan](../plans/2026-10-30-nastavitve-varnostnih-kopij.md) določata konfigurabilnost; ne predstavljata že izdelanih kopij.

## 1. Pogodba kopije

| ID | Zahteva |
|---|---|
| SF5-01 | Izbrani cilj je dovoljena mapa z omejenimi pravicami; isti fizični disk je dovoljen po uporabnikovi odločitvi S-024. Cilj ne sme biti živi podatkovni imenik/volumen baze. UI pojasni omejitev istega diska; ločen disk/NAS je možnost. Manifest vsebuje backup_id, UTC started_at/finished_at, source alias brez gesel, app/git SHA, image digest, PostgreSQL/Timescale/pgvector verzije, Alembic revision, velikost in SHA256 kopije, format in izhodno kodo. |
| SF5-02 | Kopija vsebuje konsistentno DB shemo/podatke in potrebne razširitve; dokumentira potrebne vloge/pravice ter ločeno obnovljivo konfiguracijo. Gesel/ključev ne vključuj v manifest ali repo. Izguba Redis ne sme ustvariti ponovnega dispatcha; za trajne namene je resnica SQL, negotovost transporta pa ostane ohranjena. |
| SF5-03 | Predlagana politika rednih kopij: ponoči 02:00 Europe/Ljubljana, največ en uspešen backup na lokalni datum tudi ob DST; 14 dnevnih in 8 tedenskih uspešnih kopij. Izbris samo po preverjeni novi kopiji in samo pod potrjenim backup root. RPO predlog 24 h, RTO cilj 60 min, oba do meritve/izbire lastnika **nepotrjena**. |
| SF5-04 | Pred prenosom sveža kopija po zadržanju piscev/ustavitvi prevzema novih poslov in preverbi aktivnih opravil. Kopija mora pripadati točni izbrani bazi/reviziji/izdaji; po obnovitvenem preizkusu ostane izvor do migracije brez novih poslovnih zapisov ali se izdela in preveri nova kopija. |
| SF5-05 | Obnova teče v novem izoliranem PostgreSQL cilju z ustreznimi razširitvami, brez dostopa do SMTP/Telegram/modelov/brokerja in brez samodejno zagnanih delavcev. Ime/volumen/port cilja se preverijo proti izvornemu; cilj nikoli ni :3000 ali njegov volumen. |
| SF5-06 | Dokaz obnove preveri podatke: shema/revision, FK/unique, računi/posnetki, izvorne valute/Decimal, coverage/cash/accrual, osnutki/predlogi, analize/reviews, process_policy/execution, nejasne email dostave in outbox cursor če ga kopija že vsebuje. Pred/po popis vključuje število vrstic in stabilne kontrolne vsote iz istega konzistentnega posnetka. |
| SF5-07 | Uspeh pomeni uporabne podatke po read-only API smoke ter uspešnih reprezentativnih poizvedbah; popoln byte hash dumpa sam ne zadošča. Zasebni rezultati ostanejo v omejenem dokaznem prostoru, javno poročilo ima anonimizirane ID/števila. |
| SF5-08 | Napaka dump/checksum/restore/smoke ali nedosegljiv cilj pomeni `failed` in blokado migracije. Ohraniti zadnjo znano uporabno kopijo. Lokalna napaka je vidna v dnevniku/stanju; pošiljanje opozorila po SMTP/Telegram zahteva ločeno pooblastilo in ni samodejen del tega dokumenta. |

Polja manifest/recovery poročila so strukturiran JSON brez skrivnosti. Časi so UTC; lokalna cona velja le za urnik. Številke pri starih/neznanih tabelah niso dopolnjene iz zgodovinskega poročila; manjkajoč popis pomeni failed verification, ne 0.

## 2. Stanja in izvedbeni postopek

Kopija: `planned → creating → created → checksum_verified → restore_verified`; poljubni neuspeh `→ failed`. `created` ni obnovitveni dokaz. Redne kopije lahko dobijo kasnejši ločeni restore drill, vendar mora konkretna predmigracijska kopija imeti svoj dokaz ali preverjeno enakovredno obnovitveno verigo po izrecno pregledanem postopku. Prvi živi prenos brez restore dokaza je blokiran.

Obnova: `target_verified → isolated → restored → data_verified → smoke_verified`; šele zadnje odpre vrata H. Vsak korak ima UTC čas, operator, ukaz/izhodno kodo, alias cilja in evidence_hash. Predlagan skupni tehnični rok drilla 2 h; prekoračitev zabeleži, ne prekini tako, da izgubiš dokaz kopije, ter ne razglasi RTO 60 min dosežen.

1. Izberi dovoljen source/target, backup root in razpoložljiv prostor; preveri različice in potrebne razširitve brez izpisa poverilnic. Popiši aktivne analize, reviews in dispatch stanja.
2. Za predmigracijski rez zaustavi sprejem novih avtomatskih poslov in kontrolirano izprazni ali zadrži delavce. Že dispatchanih ne ubij/ponavljaj brez pogodbe [S-G1](./2026-10-30-lastnistvo-in-idempotentnost-spec.md). Do razjasnitve ostane prenos zadržan.
3. Izdelaj konsistentno kopijo; pripadajoče kontrolne vsote/štetja pridobi iz istega DB snapshot oziroma med dogovorjenim mirovanjem piscev. Ločeno zajemi image/config identifikatorje brez skrivnosti.
4. Obnovi na izoliran nov cilj, preveri razširitve, podatke in read-only API. Modelni/sporočilni transport je fake ali omrežno onemogočen; produkcijski tokeni se ne kopirajo v demo.
5. Na obnovljeni kopiji posebej preveri upgrade skozi izbrane 0016–0020 in morebitne nove odobrene migracije; nato downgrade, kjer je varen, in ponovno obnovo stare kopije. Zabeleži, kateri povratek ohrani podatke in kateri izgubi nova polja.
6. Pripravi release manifest in časovno mejo veljavnosti kopije; dejansko spreminjanje :3000 zahteva ločeno novo izrecno odobritev uporabnika po S-H.

## 3. Obvezni fixture in prevzem

| ID | Scenarij in merljiva trditev |
|---|---|
| F-F501 | Sintetična DB z več računi/valutami, Decimal, delnim coverage, predlogom, aktivnim/negotovim run in email unknown → dump/restore → enaka števila/kanonične vsote in noben odhodni klic. |
| F-F502 | Poškodovan ali odrezan dump / napačna SHA → ni restore_verified, predhodna kopija ostane. |
| F-F503 | Napačna verzija razširitve ali manjkajoča vloga → jasna napaka pred smoke, prenos blokiran. |
| F-F504 | Cilj se razreši v isti DB/volumen kot vir → zavrnitev še pred obnovo. |
| F-F505 | Padec sredi upgrade izbrane verige 0016–0020 → obnovitev stare kopije + ustreznih slik vrne uporabne podatke; downgrade sam ni samoumeven dokaz. |
| F-F506 | Izgubljen Redis in ponovno zagnani delavci na kopiji → trajni namen je vidljiv, dispatchan plačljivi/sporočilni poskus se ne ponovi. |
| F-F507 | Neuspešna nočna kopija, poln disk, DST podvojena ura in retention → ohranitev stare uspešne kopije, eno dnevno opravilo, sled napake, nič nepooblaščenih sporočil. |

Vrata pred implementacijo dejanskega zajema zasebne baze: potrjen cilj/dovoljenja/hramba in pregled runbooka. Neodvisna izvedba nastavitev in sintetični preizkusi BL-222 ne potrebujejo še izbrane zasebne mape. Vrata pred živo migracijo: uspešen dejanski drill v dogovorjenem izoliranem okolju, kontrolni podatki, izmerjen čas in pregledan rollback. Testna sintetična zbirka potrjuje postopek; ne potrdi, da je današnja živa baza že obnovljiva. V tem koraku niso izvedeni nobeni backup/restore ali migracijski ukazi.

**Odprte blokade:** dejanski backup disk/cilj, kdo dostopa do šifrirane kopije in kako obnovi ključe/konfiguracijo, razpoložljiva testna DB, pričakovani RPO/RTO, inventura žive sheme in aktivnih poslov. BL-017 ostane odprt do rednih kopij in restore dokaza; pripravljen dokument ga ne zaključi.
