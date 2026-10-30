# S-F5a · Nastavitve varnostnih kopij

**Status: PREGLEDAN PREDLOG SPEC, brez implementacije.** 2026-10-30. BL-222, povezava BL-017/214/215. Uporabnik: »Nastavimo v nastavitvah kako pogosto in kam. Trenutno še nikamor. Običajno na enak disk.« Razširjenega dejanskega Flex vzorca trenutno ni; ta funkcija ga ne potrebuje in ne zapira Flex dokaznih vrat. [Neodvisni dokumentarni pregled PASS](../../implementation/2026-10-30-neodvisni-pregled-nastavitev-kopij.md), vse tri ugotovitve odpravljene; testi spodaj so zahteve prihodnje izvedbe.

Podlage: [S-F5](./2026-10-30-varnostne-kopije-restore-spec.md), [S-H](./2026-10-30-prevzem-in-prenos-spec.md), [izvedbeni plan](../plans/2026-10-30-nastavitve-varnostnih-kopij.md), ADR-0001/0019. Velja za lokalni Docker Compose sklad, PostgreSQL 17/Timescale/pgvector, API FastAPI, SQLAlchemy/Alembic, arq in obstoječi SCR-11 Nastavitve.

## 1. Obseg in razmerje do S-F5

Sprejeta uporabniška smer je nastavljiva pogostost in cilj, dovoljen tudi isti disk. **SF5-01 zahteva ločenega diska je za ta obseg nadomeščena:** kopija na istem disku je dovoljena, vendar ne ščiti pred odpovedjo tega diska, izgubo celotnega računalnika ali dogodkom, ki prizadene oba imenika. Ločena mapa ali Docker volumen sama ne pomenita ločenega fizičnega diska. UI prikaže to omejitev stalno ob cilju; če topologija ni dokazljiva, napiše »Fizična ločitev diskov ni preverjena«. Druge SF5 zahteve, zlasti izoliran restore dokaz pred migracijo, ostanejo.

Privzeto `enabled=false`, `target_id=null`: nič se ne kopira, nič se ne pošilja in noben cilj se ne ugiba. Prvi rez pokrije eno SQL bazo aplikacije na en izbran lokalni cilj, ročno kopijo, dnevni/tedenski urnik, retention in stanje. Ne vključuje oblačne sinhronizacije, SMB prijav, upravljanja diskov, polne slike računalnika, Redis/agentsdata arhiva, izvoza poverilnic, prenosa datotek v brskalnik ali samodejne obnove. Redna kopija ne ustavlja živih delavcev; predmigracijski mirni rez in restore po S-F5 sta ločen postopek.

Trenutno stanje je preverjeno samo statično: `infra/README.md`, `infra/docker-compose.yml`, `services/api/Dockerfile` in `infra/scripts/` ne vsebujejo backup/restore izvedbe; obstoječa `collect-analysis.sh` zbira analizo/dnevnike in ni kopija baze. SCR-11 ima že obrazce z revision konfliktom (`components/settings/SettingsView.tsx`, `EmailSettings.tsx`); `domain/automation.py:next_slots` uporablja IANA cono, UTC in fold=0. To so vzorci za izvedbo, ne obstoječa backup funkcija.

## 2. Pogodba nastavitev in uporabniški potek

**BK-01:** SCR-11 dobi zložljiv razdelek »Varnostne kopije« z obrazcem, Shrani, Zavrzi, »Preveri mapo« in »Ustvari kopijo zdaj«. Brez novega zaslona. Prikaže shranjeno/ne-shranjeno spremembo, spor različice, napako dostopa, naslednji načrtovani termin, zadnji poskus, zadnjo uspešno kopijo, zadnji dokaz obnove in omejitev istega diska. Shrani ali Preveri mapo ne sproži kopije. UI nima gumba »Obnovi produkcijo«.

| Polje politike | Pogodba in predlagana privzeta vrednost |
|---|---|
| `revision` | Nenegativno celo število, CAS pri PATCH; zastarela revision → 409 brez sprememb. |
| `enabled` | false; upravlja samo redni urnik. Ročna kopija ob izključenem urniku je dovoljena po uspešni ponovni preverbi cilja. |
| `target_id` | null ali alias strežniško dovoljenega, priklopljenega korena; ni URL ali shell ukaz. |
| `relative_dir` | `preza`; neobvezna podmapa dovoljenega korena, 1–240 znakov; pravila BK-03. |
| `schedule_kind` | `manual|daily|weekly`; začetni predlog daily, neaktiven do vklopa. |
| `timezone`, `local_time` | IANA cona `Europe/Ljubljana`, HH:MM `02:00`; uporabnik lahko spremeni. |
| `weekday` | Celo število 0–6 (ponedeljek–nedelja), predlog 6; uporablja samo weekly. |
| `retain_daily`, `retain_weekly` | Celi števili 1–365 in 0–52, predlog **14 dnevnih + 8 tedenskih**; uporabnik ju lahko spremeni. |

Predlogi urnika/hrambe so tehnične privzete vrednosti, ne že potrjene uporabniške številke. Ni dodatnega vprašanja za retention pred pripravo izvedbe. Vklop zahteva veljavno politiko, obstoječ dovoljen cilj in svež preizkus dostopa pri shranjevanju; isti disk ni razlog za zavrnitev. Za vsak dejanski zagon se dostop ponovno preveri. Nastavitev nove mape ne pomeni dovoljenja za pregled celotnega diska.

**BK-02 / API predlog:**

- `GET /backups/settings` vrne politiko, dovoljene target aliase/oznake, konfiguriranost, varne razloge in naslednjih pet terminov UTC; GET ne preverja s pisanjem in ne izvaja dumpa.
- `PATCH /backups/settings` sprejme zgornja polja, prepove neznana polja in uveljavi revision CAS. Ne sprejema DSN, gesel, ukazov ali poti programov.
- `POST /backups/validate-target` sprejme `target_id, relative_dir`; ustvari omejen preizkus runnerjeve mape, ne kopira podatkov; vrne 202 + operation_id. `GET /backups/target-validations/{id}` vrne `queued|checking|passed|failed`, readiness ali varen error_code. Začasni testni zapis je naključen, brez vsebine baze, in se odstrani samo sam. Preverba ni trajno zagotovilo prihodnjih pravic/prostora.
- `POST /backups/runs` sprejme `request_id UUID, revision`; ustvari trajni manual namen s snapshotom shranjene politike ter vrne 202 + run_id. Enak request_id/payload → isti run; drugačen payload → 409. Ne-shranjene spremembe zahtevajo najprej Shrani. En aktivni backup na source/target je dovolj; konkurenten drugi namen dobi 409 `backup_already_active`.
- `GET /backups/runs?limit=...` in `GET /backups/runs/{id}` vrneta največ 100 javnih statusov z UTC časi, velikostjo, hashom, fazo preverjanja in varnimi napakami. Noben endpoint ne vrne vsebine dumpa ali skrivnosti.

Omejeni preizkus mape in dump sta delo runnerja, ne dolg blokirajoč HTTP request. Vrnjena tipa preverbe in kopije sta izrecna v generiranem OpenAPI, UI ne ugiba uspeha iz samega 202. Za vklop politike PATCH zahteva še veljavno uspešno preverbo istega target_id/podmape, staro največ 5 minut; pri izvajanju se cilj preveri znova. Strežniška sprememba allowed root/markerja preverbo razveljavi.

Vse spremembe uporabljajo obstoječi omejeni dostop aplikacije prek lokalnega/Tailscale okolja. Ni javnega porta, Docker API ali splošnega oddaljenega upravljanja. Besedila SL/EN gredo izključno v messages; datum prek obstoječega Intl prikaza, velikost/števila iz deterministične kode. Ročni klik pokaže queued → creating → izid; izpad runnerja ne prikaže »kopija izdelana«.

## 3. Mapa na gostitelju in omejen runner

**BK-03:** človek/operater ob namestitvi nastavi dovoljen host root in ga izrecno bind-mounta v backup runner; host pot in container pot sta različni. Primer je samo dokumentacijski: `D:\Preza-backups` ↔ `/backups/local`; nobena dejanska pot še ni izbrana. UI izbira `target_id` in podmapo pod že dovoljenim korenom; ne more ustvariti novega mounta ali poljubnega host dostopa. Za novo lokacijo zunaj korena je potreben omejen namestitveni korak in nato je cilj na voljo v Nastavitvah.

Koren mora obstajati in imeti pri namestitvi določen marker/ID, ki se ujema z dovoljeno konfiguracijo. Manjkajoči mount ali napačen marker pomeni `target_unavailable`; runner ne ustvari rezervne mape na svojem sistemskem disku. Dovoljene podmape lahko ustvari z omejenimi pravicami. Sprejemljivost poti preverita API in runner z enakimi pravili:

- Zavrni absolutne podmape, `..`, NUL/kontrolne znake, sheme URL, alternativne tokove in poti zunaj izbranega korena. Niz poti je podatek, nikoli del shell stavka.
- Razreši pravi koren in vse obstoječe komponente ter zavrni symlink/junction/reparse prehod izven njega; tik pred ustvarjanjem/rename/retention ponovi varno preverbo. Target koren ni writable nepooblaščenim drugim uporabnikom, da se ne odpre zamenjava poti med preverbo in uporabo.
- Ne sprejemaj ukaza, executable, Docker servisa, DSN ali poljubnih pg_dump opcij iz UI. Programske argumente sestavi koda kot argv, brez shell=True. Docker socket ni priklopljen; API nima pravic za docker exec.

**BK-04:** ločeni omejeni backup worker uporablja obstoječi Python/arq/SQL stack in združljiva `pg_dump`/`pg_restore` orodja za source PG17; osnovna API slika jih trenutno nima. Izvedba doda ločen build target/službo, ne namešča programov skozi uporabniški obrazec. Source povezava ima samo potrebne pravice za konsistenten izvoz, ne migracijskih DDL pravic. Njegov kontrolni dostop sme zapisovati samo backup nastavitve/namene/status. Ne dobi LiteLLM, IBKR, SMTP, Telegram ali agent tokenov. Skrivnosti poveže operater strežniško, brez izpisa argv/env/DSN v API ali dnevnike. Združljivost major verzije orodij/razširitev se preveri pred dumpom in izoliranim restore.

Če runner ni nameščen, UI pove »Izvajalnik kopij ni nastavljen«; politike se ne da omogočiti. Dodajanje runnerja ne pomeni dovoljenja, da se v tem dokumentarnem koraku zažene na :3000 ali kopira zasebna baza.

## 4. Urnik in trajnost namenov

**BK-05:** vsi zapisi in termini v SQL so UTC; uporabniška IANA cona določa civilni datum/uro. Daily in weekly uporabljata obstoječo semantiko `next_slots`: jesenska ponovljena ura samo prvi pojav (`fold=0`), spomladanska neobstoječa ura se preskoči. UI prikaže naslednji resničen termin in pojasnilo preskoka. Dnevno 02:00 zato ob prehodu na poletni čas ne jamči največ 24 h med kopijama; RPO 24 h ostane cilj, dokler ni meritev in ustrezen izbran urnik.

Redni tick enkrat na minuto materializira en trajni slot `(source_alias, target_id, scheduled_for UTC)`; sprememba revision ali restart ne ustvarita drugega namena istega slota. Dodatno dnevna/tedenska civilna identiteta prepreči dvojni avtomatski uspeh za isti lokalni datum/izbrani teden, tudi po spremembi ure isti dan. Namen ima trajni `origin=scheduled|manual`, ki ga določi tick oziroma ročni endpoint, ne poljubno vhodno polje uporabnika. Manual zahteva je ločena in lahko isti dan zavestno izdela dodatno kopijo. Pred začetkom scheduled namen zahteva `enabled=true`; manual namen ta pogoj izpusti, tako da shranjena konfiguracija z `enabled=false` dovoljuje ročno kopijo. **Oba izvora** še vedno zahtevata ujemanje aktualne revision/snapshota in ponovno preverjeno dovoljeno mapo, marker, pravice ter prostor. Sprememba nastavitev stare še pending namene označi skipped, ne kopira na nekdanjo mapo.

Po izpadu se izdela največ ena nadomestna redna kopija za zadnji zapadli slot, ne cel niz zgodovinskih dumpov; ostali dobijo skipped/coalesced. Redis je samo dostava; namen in rezultat sta SQL. Pending se ponovno dostavi z istim ID. Interrupted creating se najprej uskladi z lastnim `.partial`/končnim manifestom; ne prepisuje uspešnega finala in ne ponovi starega dela ob neznano aktivnem runnerju. Med dumpom velja enoličen aktivni prevzem ter ujemanje instance/claim tokena za status in objavo. Stale čas sam ni dokaz konca procesa; brez dokaza prenehanja ostane interrupted/recovery_pending brez paralelnega pisanja ali brisanja. Ta mala pogodba ne razširi S-G1 plačljive analize.

Glavna pavza modelov in izklop avtomatskih analiz **ne ustavita varnostnih kopij**. Njihov enabled=false ustavi redni urnik in še pending scheduled namene; ne blokira izrecnih manual namenov z veljavno revision in ciljem. Že izdelujoča kopija se varno dokonča po svojem snapshotu. Sprememba poti ali hrambne politike med dumpom začne veljati za naslednji namen, ne preusmeri obstoječe datoteke.

## 5. Vsebina, atomarna objava in hramba

**BK-06:** prvi rez je konsistenten PostgreSQL custom-format dump izbrane baze (`pg_dump --format=custom`, brez owner/ACL gesel/global role dumps), manifest JSON in kontrolni popis. Vsebuje SQL podatke, potrebne za aplikacijo, vključno s portfeljem, nastavitvami, predlogi in sledmi procesov/negotovih dispatchov. To je zasebna vsebina. Ne obljubljaj »brez občutljivih podatkov«: uporabniška besedila lahko vsebujejo zasebne vnose. Ne dodajaj `.env`, `infra/secrets`, poverilnic, ponudniških dnevnikov, Redis AOF, agentsdata ali surovih zasebnih Flex datotek. Obnovljiva neskrivna konfiguracija pomeni različice/identifikatorje in dokumentirane korake; ključe in gesla obnovi operater ločeno. Kopija sama zato še ni celoten disaster-recovery paket.

Dump in popis morata pripadati istemu konzistentnemu snapshotu: read-only koordinator izvozi PostgreSQL snapshot, pg_dump in deterministične kontrolne poizvedbe ga uporabijo pred koncem koordinatorja. Nikoli ne prikaži primerjave štetij iz različnih časov kot dokaz enakosti. Podaljšana read-only transakcija ni ustavitev piscev. Preveri vpliv na prostor/obremenitev v izoliranem testu.

Vsak namen uporabi svoj `backup_id UUID` in `.partial-<id>` imenik v izbranem korenu. Po uspešnem dump exit=0, preverbi formata (`pg_restore --list`), velikosti in SHA256 se zapiše manifest. Vrstni red trajne objave je obvezen: flush/fsync vseh datotek, **fsync začasnega imenika**, atomarni rename na istem filesystemu v končni `<UTC>-<id>`, nato **fsync nadrejenega imenika končnega imena**. Šele po zadnjem uspešnem fsync se zapiše checksum_verified in je dovoljena retention. Napaka ali nepodprta imeniška durability operacija ne pomeni uspeha in ne sproži brisanja; varen izid je publish_failed. Končni imenik vsebuje dump in manifest; ne nastane final z napol napisanim manifestom. Ponovna dostava ob najdenem finalu preveri njegov backup_id/hash ter izvede manjkajočo durability preverbo/fsync parenta, preden zaključi isti SQL namen. Nepreverjen ali tuj imenik se ne prepiše.

Manifest: schema_version, backup_id, source alias brez DSN, policy revision, UTC started_at/finished_at, logical scheduled_for, urnik/timezone, app/git SHA in image digest (unknown ostane unknown), PostgreSQL/Timescale/pgvector različice, Alembic revision, dump format/size/SHA256, redacted exit code, snapshot kontrolna števila/vsote ter scope izključitev. Manifest ne vsebuje gesel/ključev, poizvedbenih rezultatov s portfeljskimi vrsticami ali polnih stderr izhodov. Hash manifest datoteke se zapiše v SQL izid, ne v isti manifest sam vase.

**BK-07 / varovanje:** imenik in datoteke so dostopni le potrebnemu runner/operater računu (POSIX owner-only ali enakovreden preverjen host ACL). API ne ponuja prenosa dumpa. Če pravice ni mogoče preveriti/uveljaviti, kopiranje ne steče. Samo filesystem ACL ni šifriranje; ta rez ne uvaja novega upravljanja šifrirnih ključev in ne trdi, da je kopija šifrirana. Šifriranje diska ali prihodnji šifrirani export je ločen dogovor; cilj na istem disku ima še vedno prej opisano omejitev. Zasebni manifest/popisi ostanejo v omejeni mapi, javno poročilo je redigirano.

**BK-08 / retention:** po novi checksum_verified kopiji izračunaj unijo zadnjih `retain_daily` različnih uspešnih lokalnih datumov in zadnjih `retain_weekly` ISO tednov, za vsak datum/teden najnovejši uspešni backup. Datoteke se fizično ne podvajajo za dnevni in tedenski nabor. Vsak kandidat ima preverjene metapodatke backup_id, source/target/root identiteto, final ime, UTC started_at/finished_at, IANA cono svojega policy snapshota, backup/restore stanje, pinned zastavico in hasha dumpa/manifesta. Lokalni datum in ISO leto/teden se izpeljeta iz finished_at v tej shranjeni coni; izbor znotraj skupine in »najnovejši« je determinističen po `(finished_at, backup_id)`. Vedno ohrani najnovejšo uspešno kopijo, najnovejšo uspešno kopijo z restore_state=passed ter izrecno pinned predmigracijske dokaze; to lahko preseže številsko hrambo. Manjkajoči metapodatki ne pomenijo dovoljenja za izbris. Neuspeh ali zgolj ustvarjen dump nikoli ne sproži brisanja.

Brisanje zajame samo lastne final imenike s prepoznanim backup_id/manifestom pod **istim trenutno preverjenim korenom/ciljem**. Ne sledi povezavam, ne briše tujih datotek, osirotelih partial ali prejšnjega cilja po spremembi nastavitev. Partial cleanup in sprostitev pinov sta ločen pregledan poseg. Poln disk ali napaka retention zabeležita varen izid; napaka čiščenja po dobrem dumpu ne preimenuje dobre kopije v manjkajočo ali restore_verified.

## 6. Stanja, napake in dokaz obnove

**BK-09:** status opravila loči `queued|creating|checksum_verified|failed|skipped|interrupted`. `checksum_verified` je uspešno izdelana in preverjena datoteka, **ni dokaz obnove**. `restore_state=not_tested|passed|failed` je ločen, vezan na točen backup_id/dump SHA in izolirani drill. Target validation ima lasten kind/status in ne vpliva na »zadnja uspešna kopija«. Dnevnik vsebuje varen error_code, čase, fazo in ID; nikoli poverilnic ali surove vsebine baze.

Obvezne napake: `backup_unconfigured`, `runner_unavailable`, `target_unavailable`, `path_rejected`, `permission_denied`, `insufficient_space`, `revision_conflict`, `backup_already_active`, `tool_incompatible`, `dump_failed`, `checksum_failed`, `manifest_failed`, `publish_failed`, `retention_failed`, `recovery_pending`. API vrne 409 za konflikt/nekonfiguriranost, 422 za neveljavna polja; okoljska napaka po sprejemu namena je trajni failed izid, ne lažen 202 uspeh. GET povezljivosti ne preverja s poskusnim dumpom. Brez avtomatskih SMTP/Telegram opozoril.

**BK-10:** dokler dejanski cilj ni izbran, se restore preverja samo na sintetičnih podatkih v novem izoliranem testnem skladu, s fake/onemogočenimi modeli/SMTP/Telegram/brokerjem in brez zagnanih aplikacijskih delavcev. Testna obnova ne dobi pravice do :3000, njegove baze, volumna ali skrivnosti. Navadna Settings akcija nikoli ne požene restore.

Pred prvo dejansko migracijo še vedno velja S-F5: dovoljen dejanski source/cilj, sveža ustrezna kopija, uspešen izoliran restore prav te vsebine, shema/razširitve/FK/unique ter kanonična števila/vsote, read-only smoke in pregledan rollback. Hash ali zelen sintetični test tega ne nadomestita. RPO/RTO ostaneta nepotrjena do meritev; funkcija nastavitve ne zapre BL-017/215 sama.

## 7. Prevzemni scenariji

| ID | Preverljiva trditev, samo fake/sintetično do izbire cilja |
|---|---|
| F-BK01 | Čista migracija → disabled, target null; več tickov/restartov in GET → 0 dumpov. Ročni klik brez konfiguracije jasno zavrnjen. |
| F-BK02 | Shrani veljavno lokalno mapo/urnik/14+8; stale revision/unknown polja → 409/422 brez sprememb. Same disk dovoljen in razlaga vidna v SL/EN. |
| F-BK03 | Host/container mapping, manjkajoči mount/marker, `..`, absolutna podmapa, symlink/junction, presledki/Unicode, shell metaznaki → dovoljena varna mapa ali zavrnitev brez ukaza zunaj argv in brez pisanja zunaj root. |
| F-BK04 | Dnevni/tedenski urnik z UTC, fold=0, manjkajočo 02:00, restartom in spremembo revision; 1 avtomatski namen na civilni slot, omejen catch-up, brez LLM pavze kot skritega backup stikala. Konfiguriran manual namen pri enabled=false izdela eno kopijo; scheduled pri enabled=false ne; neveljavna revision/cilj blokirata oba. |
| F-BK05 | Dva klika/izgubljen odgovor/Redis down → isti request_id/run; isti ID druga vsebina → 409; dva runnerja/bariera → en final in nobeno sočasno brisanje. |
| F-BK06 | Fake dump exit≠0, odrezana datoteka, poln disk, napaka fsync datotek/začasnega imenika/končnega parenta, rename/manifest ter padec pred/po final rename → noben delni final, prejšnja dobra kopija ostane; redelivery uskladi isti ID. Zajet vrstni red potrdi oba imeniška fsync; brez njiju ni checksum_verified ali retention. |
| F-BK07 | Sintetična PG17+razširitve DB → konsistenten dump/popisi → izolirani restore in enake kanonične vsote/FK/unique/Decimal; 0 zunanjih transportov. Napačen source/target ali verzija → restore zavrnjen. |
| F-BK08 | 30 dni/10 tednov/napake/pinned/restore_verified → unija 14 dnevnih +8 tedenskih, zaščitene kopije ostanejo; tuj imenik, partial, symlink in prejšnji root ostanejo nedotaknjeni. |
| F-BK09 | API/manifest/log vsebujejo samo varne podatke; testni credential marker nikjer v njih ali argv. Dump je izrecno zaseben; ACL napaka blokira. |
| F-BK10 | Nastavitve na telefonu/namizju, SL/EN, tipkovnica, nalaganje/napaka/409/queued; checksum uspeh ne prikaže restore uspeha, reload ohrani status in ni gumba za živo obnovo. |

## 8. Preostali vhodni podatki in meje dovoljenja

Za pripravo ali izolirano sintetično izvedbo ni treba ponovno spraševati o retention ali zahtevati zasebnega Flex vzorca. **Pred aktivacijo dejanskega kopiranja** mora uporabnik izbrati konkretno host mapo/koren; operater preveri pravice/mount/prostor in preslikavo. Zdaj je ni, zato ostane funkcija disabled/unconfigured. Kdo lahko dostopa do zasebne kopije in kako so ločeno obnovljene skrivnosti, se potrdi ob tej namestitvi. Pot/frekvenca se nato urejata v Nastavitvah v okviru dovoljenega korena.

Dokument ni dovoljenje za prebiranje poverilnic, kopijo žive baze, restore, novo povezavo, migracijo, zagon runnerja ali spremembo :3000/:3100. Implementacija, sprejem, deploy in dejanski restore drill so ločene stopnje; ta korak pripravi samo SPEC/plan.
