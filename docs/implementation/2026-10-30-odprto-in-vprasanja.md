# Kaj je še odprto in kateri odgovori so potrebni

**Datum:** 2026-10-30, S-024. **Izhodišče:** `21a0b3d`. Končan je neposredni dodatni krog BL-218/220; celotni UX/podatkovni načrt ni končan. [Dokazi S-023](./2026-10-30-izvedba-dodatnega-kroga.md), [register SPEC](../superpowers/specs/2026-10-30-odprti-sklopi-priprava-spec.md).

Po zaključku BL-204/221 in dodanem BL-222 je datirani popis BACKLOG: **108 done, 6 doing, 16 next, 27 later** (157 nalog, 49 odprtih; vključuje tudi prihodnja M6/M7 in odloženi obseg). To ni število napak trenutne izdaje. Naslednji seznam loči izvedeno, izvedljivo brez novih odgovorov in odvisno od dejanskih vhodov.

## Nadaljevanje brez novih uporabnikovih odločitev

| Prednost / naloga | Kaj se uredi | Dokaz zaključka |
|---|---|---|
| Izvedeno: R1 / BL-221 | Radar najprej izbere dogodke portfelja/watchliste/discover in jih šele nato omeji; stara napaka omejenega prefiksa odpravljena. | 15 ciljnih realnih DB testov vseh pogledov, stabilen vrstni red, brez N+1 in brez spremembe exact-ID podrobnosti; pregled PASS. |
| Izvedeno: BL-204 | Ista oddaja predloga ostane ista po reload/izgubljenem odgovoru. Zamrznjena oddaja je ločena od novega urejanega osnutka. | API sprejem/konflikt, 29 povezanih enotskih in 12 novih E2E testov; dva prava zavihka, SL/EN in telefon, Back/fokus; pregled PASS. |
| Naslednje: BL-222 / S-F5a | Nastavitve lokacije, pogostosti in hrambe varnostnih kopij, ročni zagon ter jasno stanje. Isti disk dovoljen, privzeto neizbrano/izklopljeno. | [SPEC](../superpowers/specs/2026-10-30-nastavitve-varnostnih-kopij-spec.md) in [plan](../superpowers/plans/2026-10-30-nastavitve-varnostnih-kopij.md) imata [dokumentarni PASS](./2026-10-30-neodvisni-pregled-nastavitev-kopij.md). Produktna izvedba, kopije in dejanski restore še odprti. |
| Naslednje: A3/A5 | Zanesljivo lastništvo analiz in pregledov tez: druga dostava ne ponovi plačljive verige in ne zaključi živega izvajalca. | Najprej natančna tehnična pogodba instance/lastnika, nato dva prava izvajalca, DB bariere, restart in dokaz konca starega dela. Sam čas/Redis TTL ni dovolj. To je tehnična naloga, ne vprašanje uporabniku o interni arhitekturi. |
| Nato: BL-203 in paket G | Poimenovani profili, primerjava vrstic, enotno iskanje, preostali paneli, popolnejši preizkus 200-% povečave/dostopnosti. | Posamezni majhni izvedbeni SPEC, primerljivi podatki in UX matrika. Osnovni pogledi/stolpci so že izvedeni. |
| Nato: paketa D/E | Dejanska pokritost fundamentalov/ETF/makro, predpomnilnik triaže, skupni roki in pregled dejanskih vlog/porabe. | Datirana inventura, preslikava polj/enot/pravic/kvot, fake pogodbe ter omejen izrecno dogovorjen živi dokaz. Stare številke in nazivi modelov niso trenutna meritev. |

Za prvi dve zaključeni nalogi veljata [izvedbeni plan](../superpowers/plans/2026-10-30-radar-trajna-oddaja.md) in [dokazni zapis](./2026-10-30-radar-in-trajna-oddaja-dokazi.md). S-G1 je pogojen po podsklopih: R1/BL-204 ne potrebujeta nove lease sheme ali finančnega vzorca. A3/A5 se ne označita rešena z njunimi testi.

## Konkretna vprašanja in prejeti odgovori

| ID | Manjkajoči vhod | Prejeti odgovor / naslednji korak | Trenutna meja |
|---|---|---|---|
| Q-FLEX | Dejanski podprt izvozni format, finančni popravki in baza računa | Uporabnik razširjenega izpisa še nima. Ponovno vprašanje o isti poti ni potrebno. Ko bo pripravljen, naj vključuje CashReport, AccountInformation, FinancialInstrumentInformation in Open/Change Dividend Accruals; primer `Re`, če obstaja. | S-B ostane pogojen; sintetični testi ne potrdijo dejanskih dividend. Iz nastavitev se ne ugiba zgodovinske bazne valute ali pomena `Re`. |
| Q-BACKUP | Izbrana lokacija, pogostost in hramba | Uporabnik želi lokacijo in pogostost nastavljati v aplikaciji; cilj trenutno ni izbran, običajno isti disk. BL-222 pripravi pogodbo za nastavitve, privzeto izklopljeno, s predlogom nastavljive hrambe 14 dnevnih in 8 tedenskih kopij. | Isti disk je dovoljen, vendar ne ščiti pred njegovo odpovedjo. Ni pisanja zasebne kopije na neizbran cilj. Ločen sintetični preizkus obnove ostane mogoč; dokaz dejanske obnove je pogoj pred prvo živo migracijo. |
| Q-SMTP | Ustvarjen predal, lokalno geslo in prejemniki | Uporabnik je navedel `sh10.neoserv.si` in bo šele ustvaril `preza@zavadlal.com`. Preverjena uradna navodila določajo SMTP 465 s TLS in avtentikacijo s celotnim naslovom predala. Geslo samo lokalno; prejemniki še niso določeni. | To je predvidena konfiguracija, ne obstoječ ali preizkušen račun. Kanal ostane izklopljen; ni povezovanja ali testnega sporočila. Po ustvaritvi predala in konfiguraciji se ločeno določi dejanski test dostave. |

Vsi trije odgovori so prejeti; izvedbeni pogoji so delno odprti, kot je zapisano zgoraj. [Uradna navodila Neoserv](https://www.neoserv.si/podpora/splosne-informacije-o-eposti), preverjeno 2026-10-30: vrata 465, SSL/TLS, zahtevana avtentikacija; ime uporabnika je celoten naslov. `https://` ni del SMTP imena strežnika. Obstoj tega predala, pripadnost strežniku in dejanska dostava niso preverjeni. Pretečen čas ni privolitev ali podatek. Notranjih vprašanj o SQL/zaklepih/lastništvu ne prelagamo na uporabnika.

## Preostale meje SPEC in objave

- **S-B / BL-202/205:** D2/D3/F1/B5, resnične dividendne identitete/korekcije, FX izvor/cilj in konservativen backfill, popolnost gotovine. D1 je popravljen, vendar ne nadomesti tega sklopa.
- **S-C / BL-194 ter del BL-174:** dejanska inventura nerešenih kotacij in dokaz conid/borze/valute/vrste. Stara številka devet ni današnje preverjeno stanje. Podatkovne pravice/vzroki praznih metrik sodijo še v BL-193/S-D.
- **S-F5 / BL-017:** redne kopije in dejanski dokaz obnove, ne samo pripravljen runbook. **S-H / BL-215:** končni izdajni paket, aktualna druga veja/aktivne vrste, S-014, migracije/rollback ter ločeni dovoljenji za združitev in namestitev.
- **BL-212:** pravi SMTP dokaz po konfiguraciji in posebnem dovoljenju; zelen fake test ni dostava.
- **Kasnejši ločeni obseg:** polni portfeljski backtester BL-216, dodatni viri/OCR, M6 opcije ter M7 naročila imajo lastne SPEC/odobritve. Trenutna študija shranjenih signalov/mnenj je izvedena, ne polni portfeljski simulator.

:3000 ostane nespremenjen. Napredek na :3100, pripravljena migracija ali končan podsklop niso dovoljenje za živo izdajo. Odgovori na tri vprašanja prav tako ne pomenijo samodejnega pošiljanja e-pošte ali prenosa aplikacije.
