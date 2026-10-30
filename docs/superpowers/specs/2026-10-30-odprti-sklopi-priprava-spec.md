# Priprava SPEC za odprte sklope

**Status:** vhod in kontrolni seznam za naslednjo specifikacijo; ni odobren izvedbeni SPEC. **Datum:** 2026-10-30. **Osnova:** `bd33131`, ADR-0017–0022 in [enotni načrt](../plans/2026-10-30-zakljucevanje-odprtih-sklopov.md).

## 1. Zaporedje dokumentov

Začnemo s specifikacijami B/C/G1, ker urejajo izgubo podatkov, identiteto in dvojno oddajo. Sledijo D/E/F/G, potem H. I/J/K dobijo svoje dokumente in niso predpogoj za osnovno izdajo. Ena ogromna specifikacija vseh bodočih funkcij ne nadomesti preverjenih pogodb posameznih virov.

| SPEC ID / predlagana datoteka | Kaj mora razrešiti | Naloge / paket |
|---|---|---|
| S-B `2026-10-30-flex-dividende-pogodba-spec.md` | Dejanska XML polja, celovitost sekcij, identitete, korekcije, gotovina/obračun/ocena, rollback | BL-202/205, B |
| S-C `2026-10-30-identiteta-kotacij-spec.md` | Conid/ISIN/borza/valuta/vrsta, dvoumnost, dovoljeni popravki in sled | BL-194/174, C |
| S-D `2026-10-30-pokritost-virov-spec.md` | Fundamentals/ETF/makro: endpoint/polje/osnova/pravice/kvota/svežina/fallback | BL-193/027/211/052, D |
| S-E `2026-10-30-procesi-poraba-in-roki-spec.md` | Dejanske vloge, cache, proračun/poskusi/timeout, on-off-manual, DST/recovery | BL-011/012/013/169/170/172/176/180/181/058, E |
| S-F `2026-10-30-obvestila-in-obnovljivost-spec.md` | SMTP/Telegram vsebina/čas/privolitve, dostava/negotovost, HTTPS/broker read-only, backup/restore | BL-212/057/058/016/017/023, F |
| S-G `2026-10-30-stanje-pogledov-in-dostopnost-spec.md` | Trajna oddaja osnutka, profili/primerjava/iskanje, preostali paneli in celotna UX matrika | BL-203/204/005/160, G |
| S-H `2026-10-30-prevzem-in-prenos-spec.md` | Izbrana izdaja, razlika vej, migracije, podatki/vrste, dokazi, rollback, zadržana odobritev | BL-215, H |
| S-I `2026-10-30-analitika-in-backtesting-spec.md` | Event study proti portfelju/replay, point-in-time, stroški/FX/korporativna dejanja, benchmark | BL-216/067/087/094/171, I |
| S-J `2026-10-30-dodatni-viri-in-ocr-spec.md` | Trenutni podprt dostop/pravice, izvorne trditve, OCR potrditev, retencija, star uvoz | BL-033/042/182–186, J |
| S-K ločena `m6-opcije-spec.md` in `m7-paper-narocila-spec.md` | Matematične pogodbe in uporabniške potrditve, ločeni mejniki | BL-120–123/140–142, K |

Datoteke v tabeli so načrtovani rezultati; še ne obstajajo in niso citati pripravljenih specifikacij. Datum/pot se ob dejanski pripravi lahko spremeni, ID S-B…S-K in povezave BL ostanejo sledljivi.

## 2. Obvezna pogodba za vsako zahtevo

| Polje | Obvezna vsebina |
|---|---|
| ID | Stabilen ID zahteve in pripadajoči BL; zgodovinski opis ni edina specifikacija |
| Uporabniški rezultat | Konkreten sprožilec → pričakovano vidno vedenje, vključeno/izključeno |
| Dokaz trenutnega stanja | Commit, datoteka in test oziroma datiran očiščen vzorec; označiti domnevo |
| Vhod | Tip, identiteta, enota/valuta, obdobje/časovna cona, source/as_of/fetched_at in pravice |
| Izhod | Natančna shema, invarianti, null/zero, decimalni nizi, razpoložljivost in razlog vrzeli |
| Izvor resnice | Broker, tržni vir, determinističen izračun, uporabniška odločitev ali LLM interpretacija |
| Stanja | Dovoljeni prehodi; kdo jih lahko sproži; pending/conflict/error/partial/stale; kaj preživi reload |
| Sočasnost | Naravni ključi, idempotenca, revizija/zaklep, retry/izpad in negotov izid |
| Uporabniški pogled | Besedilo SL/EN, predznaki/barve/enote, datum, vidnost opozoril, tipkovnica/touch |
| Obseg dela | Paginacija/kvote/količina vrstic/rok klica; brez prikritega N+1 ali neomejenega refresha |
| Sprememba podatkov | Migracija/backfill, ohranitev zgodovine, zavrnitev/rollback in obnovljivost |
| Prevzem | Given/When/Then, fixture in natančna trditev; enote/integracija/UI in dovoljen živi dokaz |
| Odprta odločitev | Vpliv, priporočeni predlog, dokaz ki manjka, ter obnašanje dokler ni odgovora |

## 3. Minimalni obvezni scenariji

- S-B: ponovitev istega XML ne spremeni vsot; neskladen ID zavrne vse; BASE_SUMMARY ali neznana valuta ne izpraznita gotovine; odsotno ni prazno; zaprt obračun ni dokaz gotovinskega plačila; stara FX stopnja ni današnja projekcijska stopnja.
- S-C: dva enaka simbola na različnih borzah ne delita slepo podatkov; potrjen popravek ne spremeni zgodovinskih številk; neprimeren profil ne dopolni vrste/valute.
- S-D: forward P/E ni TTM; dividendni donos ni DPS; manjkajoča pravica ni ugibana iz enega praznega odziva; različno datirane ETF uteži so označene; makro odstotek/instrument/indeks niso zamenljivi.
- S-E: cache-hit ne kliče modela; popravljeni dokazi razveljavijo pravi cache; switch off prepreči naslednji avtomatski klic; manual override ne obide kvote; skupni rok velja tudi za popravljanje izhoda; DST ne podvoji zagona.
- S-F: pri spremembi prejemnikov/pavzi sredi vrste se preverijo aktualna pravila; nejasna SMTP dostava se ne ponovi na slepo; vklop ne pošlje neodobrenega arhiva; restore pokaže dejanske uporabne podatke.
- S-G: izgubljen odgovor + reload + ponovi ohrani en predlog/analizo; isto request ID/druga vsebina je konflikt; pokvarjen profil vrne obvezne stolpce; filtre/sort/povratek in fokus obnovimo; 200% in telefon ne zakrijeta dejanj.
- S-H: migracija in padec sredi prenosa imata preizkušen povratek; aktivni posli niso podvojeni; :3000 ne spreminjamo pred izrecno potrditvijo.
- S-I: zapis na času t ne vidi kasnejšega poročila ali preživelega univerzuma kot tedanje resnice; delitve/dividende niso dvojno štete; prekrivajoči signali in gotovina sledijo izbranim pravilom; povprečje izidov ni kumulativni donos portfelja.
- S-J/K: vir brez pravic ostane odložen; OCR zahteva potrditev; govorica ni priporočilo; matematični izračun je determinističen; uporabniška potrditev signala ni naročilo.

## 4. Kdaj je SPEC pripravljen za izvedbo

- [ ] Vse zahteve iz pripadajočega paketa/BL imajo ID in dokazni scenarij; nič ni izpuščeno zgolj zato, ker trenutno ni podatka.
- [ ] Pogoji, domneve in preverjena dejstva so ločeni. Neodgovorjeno vprašanje, ki spremeni finančno semantiko ali dovoljenja, prepreči odvisni izvedbeni korak; neodvisno delo lahko nadaljuje.
- [ ] API/model/migracija/UI se strinjajo o identiteti, enotah, času in null vrednosti. Predlagan podpis ne navaja tipa, ki ga noben korak ne definira.
- [ ] Pregledovalec preveri scenarije, sočasnost in obseg; pripombe so rešene ali zapisane kot sprejete meje. Pri večjem viru se uporabi neodvisna raziskava z omejenim obsegom in brez skrivnosti.
- [ ] Uporabniku je predstavljen konkreten obseg in ostanejo ohranjene njegove že sprejete odločitve. Odobritev SPEC ne odobri SMTP sporočila, naročnine, merge/deploy :3000 ali M7.
- [ ] Iz SPEC nastane podroben izvedbeni plan z natančnimi datotekami/vmesniki in test → popravek → preverjanje. Šele ta korak lahko vodi produktno izvedbo.

**Naslednji dokument:** najprej S-B skupaj s S-C in S-G1 (trajna oddaja), ob upoštevanju inventure A. Ta priprava potrjuje popolnost obsega za pisanje; ne potrjuje še dobavljenih finančnih pogodb ali živega priklopa.
