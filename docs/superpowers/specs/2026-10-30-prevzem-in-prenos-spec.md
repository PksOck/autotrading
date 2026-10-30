# S-H · Prevzem izdaje in ločen prenos

**Status: NEXT-SPEC / CONDITIONAL PROPOSAL.** 2026-10-30. BL-214/215. Priprava izdaje, združitev M in namestitev D so ločeni dogodki z ločenimi dokazi. Dokument ne podeli dovoljenja za merge/push, namestitev :3000, žive ponudniške klice ali SMTP sporočila. :3100 je samo ločen predogled.

Podlage: [R6](../plans/2026-10-30-dodatni-krog-claude-izvedba.md), [dodatni SPEC](./2026-10-30-dodatni-krog-claude-spec.md), [glavni načrt H](../plans/2026-10-30-zakljucevanje-odprtih-sklopov.md). Dokumentarna osnova statičnega ogleda je `d0ceebf4cb28cb8919d23e00f2c419fa9c41d802`; to ni samodejno končni release/testirani SHA. Pred vsako izdajo se manifest pripravi znova.

## 1. Zahteve in izdajni manifest

| ID | Zahteva | Izhod / vrata |
|---|---|---|
| SH-01 | Izberi točen obseg izdaje in osnovo: source SHA, target SHA, merge-base, lokalni dirty diff, sočasno Claudovo delo, migracijski head in slike. Brez prepisovanja tujega dela ali samodejnega čiščenja vej. | Release manifest, seznam konfliktov in lastnikov. |
| SH-02 | Vsako izdajno zahtevo označi `proved`, `accepted_gap` ali `blocked` z dokazom/lastnikom; accepted_gap zahteva zavesten sprejem konkretne omejitve. Finančno napačen import, dvojni plačljivi dispatch ali nedelujoč gate niso kozmetična sprejeta vrzel. | Matrika spodaj + odprti pogoji. |
| SH-03 | Natančen novi testni paket pripada izbranemu SHA in izolirani DB. Zapiši ukaze, datum/čas, pass/fail/skip in razlog skipa, ne recikliraj zgodovinskih 554/221/155. | Novi izhodi R1–R5/R6; neodvisen pregled brez odprtih blokad. |
| SH-04 | Predogled :3100 pokaže ready/empty/error/partial/stale/unknown, signalni Peek in pravo analizo z ohranjeno študijo; SL/EN, telefon/tipkovnica/fokus. Demo podatki so sintetični. | Datirane slike/API ID/parametri brez novih analiz ali sporočil zaradi prikaza. |
| SH-05 | Popis migracij 0016–0020 in vseh poznejših dejansko izbranih, dependencies, upgrade/downgrade in podatkovne izgube. ID se preverijo proti aktualni drugi veji. | Testna kopija + preverjen rollback; pripravljene migracije niso že živo izvedene. |
| SH-06 | Obnovljivost pred prvo živo migracijo vključno z 0016–0020. | [S-F5](./2026-10-30-varnostne-kopije-restore-spec.md) restore_verified za konkretno kopijo/rez podatkov. |
| SH-07 | Ob združevanju prenesi manjkajoči S-014 iz potrjenega osnovnega checkouta z izvorom/hash; preveri, da ne prepišeš novejših vnosov. | Dokumentarni diff; v tem podkoraku se shared SESSIONS ne ureja. |
| SH-08-M | Pred dejansko združitvijo preveri uporabnikovo pooblastilo za konkretni merge, trenutno osnovo in sočasno delo. Priporočilo pregledovalca ni uporabnikovo pooblastilo. | Ločen merge zapis; zeleni M ne pomeni D ali push. |
| SH-09-D | Za namestitev :3000 pridobi **novo izrecno potrditev uporabnika** za konkreten obseg po predstavljenem dokaznem/rollback paketu. | Ločen deployment zapis s potrditvijo, uro, source/target in smoke. |
| SH-10 | Inventura starih BL-011/013/174, prekrivanja BL-193/194 in datiranih podatkovnih številk. Brez novih dokazov status ostane odprt; nadomestna naloga dobi povezavo, ne avtomatski done. | Matrika izvornega opisa → aktualno dejstvo → dokaz → preostalo. |

Release manifest vsebuje tudi seznam aktivnih vrst/run/review/dispatched/sending/unknown, policy/control revizije, backup_id, restore evidence, povratne image digest in podatkovni rez. Ne vsebuje connection stringov, SMTP gesel ali zasebnih XML. Pregled zgodovine/root README sam ne potrdi trenutnega runtime.

## 2. Matrika vseh 14 pripomb pregleda

S-023 ima novi [dokaz neposrednih šestih popravkov](../../implementation/2026-10-30-izvedba-dodatnega-kroga.md). Spodnja tabela določa zahtevane dokaze in preostale pogoje; ni trditev, da se že dokazani popravek ponovno izvaja. Izdajni manifest jih poveže na točen SHA.

| Pregled ID | Lastnik zahteve / dokaz | Zahtevani dokaz / preostali pogoj |
|---|---|---|
| D1 | Neposredni SPEC R-D1/T-D1; [S-B SB-02/07](./2026-10-30-flex-dividende-pogodba-spec.md) ohrani regresijo | Potreben novi dokaz trenutnega kroga, vključno z legitimnim novejšim praznim snapshotom. |
| A1 | Neposredni R-A1/T-A1; [S-G1 F-G05](./2026-10-30-lastnistvo-in-idempotentnost-spec.md) | Switch pred vsakim dejanskim transportom, manual/usage regresija. |
| A2 | Neposredni R-A2/T-A2; S-G1 F-G05 | Reprodukcija z DB lock wait, po-commit gate in manual dovoljenji; samo statični sum ni done. |
| A4 | Neposredni R-A4/T-A4 in migracija 0020; S-G1 F-G05 | Omejeno delo, fairness/restart, arq retention in concurrent enqueue dokaz. |
| U1 | Neposredni R-U1/T-U; SH-04 | Analiza na pravilnem /analysis/{id}, brez nepodprtega analysis Peek. |
| U2 | Neposredni R-U2/T-U; SH-04 | Signal → close/Escape/Back ohrani parametre/rezultat/fokus in ne ponovi backtest POST. |
| D2 | S-B SB-01/03, F-B04 | Dejanski anonimizirani `Re` in potrjena semantika; do reprodukcije verjetna ugotovitev. |
| D3 | S-B SB-07, F-B09 | Preveriti dejansko besedilo in complete/partial/missing brez domnevne trditve o 0. |
| F1 | S-B SB-06/10, F-B07/08 | Dokazana baza računa/FX par, migracija/backfill; ne mešati USD/EUR baz. |
| B5 | S-B SB-02, F-B02/03; BL-205 | BASE_SUMMARY-only ni izrecno prazna popolna gotovina; manjkajoča valuta ni USD. |
| A3 | S-G1 SG-01/05–08, F-G01/02 | Trajni owner in concurrent redelivery, brez ponovnega plačljivega dispatcha. |
| A5 | S-G1 SG-02/05–08, F-G03/04 | Drug executor, heartbeat/restart in dokaz smrti starega ownerja; živ owner ostane nedotaknjen. |
| R1 | S-G1 SG-03/09, F-G06 | SQL članstvo pred LIMIT; upravičeni dogodek za >limit*3 tujimi. |
| E1 | Obstoječa SMTP/ADR-0021 pogodba; glavni načrt F1/BL-212; SH-02/09 | Resnična povezava/dostava še nepreverjena; prejemnik/vsebina in izrecno dovoljenje posebej. Do takrat kanal izklopljen oziroma izrecno izvzet, fake testi niso dokaz dostave. |

BL-204 ima posebej S-G1 SG-04/10/11/F-G07–09; ni nadomestilo A3/A5. Minimalna identiteta je [S-C SC-01–07](./2026-10-30-identiteta-kotacij-spec.md). Ostali D/E/F/G/I/J/K ostajajo v glavnem načrtu; njihove skice ne zadržujejo neposrednih šestih popravkov. Če je neka napaka izven izbranega merga, mora manifest to izrecno navesti in preprečiti napačno trditev o zaključeni osnovni izdaji.

## 3. Vrata preverjanja

| Področje | Novi dokaz |
|---|---|
| API | pytest na izolirani Postgres z dejansko vključenimi DB testi; ruff check + format check; mypy preza; ciljne D1/A4 in povezane regresije. |
| Agents | pytest + ruff/format/mypy; fake transport in deterministične concurrent bariere za A1/A2, nato lastniški testi ob izvedbi S-G1. |
| Pogodbe | `python -m preza.cli.export_openapi openapi.json` po API README, nato `pnpm gen:api`; čisti pregled razlik generiranih datotek. |
| Web | Vitest, TypeScript, ESLint brez opozoril, check-messages SL/EN. |
| Build/E2E | Linux build samo preza-demo; Playwright z BASE_URL :3100 in dokazi pravega href/target ter ohranitve stanja/fokusa. Namenoma preskočen scenarij ni opravljen dokaz. |
| Podatki | Izbrana migracijska veriga upgrade/varen downgrade/restore in read-only smoke na kopiji; dokazi S-B/S-C za finančne pogoje. |

Izvedbeni plan določi runtime/ukaze po README za dejanski sistem, brez ponovne namestitve ali branja živih gesel zaradi testa. Delno ciljno preverjanje je sprejemljivo samo z jasno navedenim obsegom in razlogom, brez prikrivanja neuspelih celotnih zbirk. Priprava teh petih dokumentov ne predstavlja novih uspešnih produktnih testov.

## 4. Stanja izdaje in kontroliran prenos

`draft → evidence_ready → reviewed → merge_authorized → merged` je M. `merged → deployment_prepared → deployment_authorized → deploying → smoke_verified` je D. Vsako manjkajoče finančno/lastniško/obnovitveno dejstvo pomeni `blocked` za odvisni korak. `reviewed` ali `merged` ne preskoči nove deployment_authorized.

Predlagani runbook D (izvaja se šele po ločeni odobritvi):

1. Potrdi točne slike/shemo in brez novih konfliktov. Popiši aktivne vrste, analize, reviews in sporočila; zadrži nova prevzemanja. Že dispatchanih ne ponavljaj in ne označuj mrtvih brez lastniškega dokaza.
2. Kontrolirano ustavi pisce in dokončaj/razjasni aktivne posle, določi podatkovni rez. Izdelaj svežo kopijo in uspešno obnovi po S-F5 **pred** kakršnokoli prvo živo migracijo 0016–0020 ali poznejšo. Ob novih zapisih po kopiji ponovno uskladi rez/dokaz.
3. Ustavi stare API/worker writerje; odobren migrator izvede izbrano verigo. Volumni/poverilnice ostanejo vezani na preverjeni cilj; nikoli ne zaženi demo seed na živi bazi.
4. Zaženi združljivi novi API/web s še zadržanimi samodejnimi prevzemi. Preveri read-only smoke: zdravje, portfelj/valute/provenienca, coverage, signali/analize/predlogi, politike in stanje vrst. Ne ustvarjaj testnih plačljivih analiz ali sporočil.
5. Delavce sprosti samo po pravilnih gate/policy revizijah ter preverjenih lastništvih in ročnih namenih. Ločeni review sporočil ali SMTP test nista implicitni del tega koraka. Zabeleži končno stanje :3000/slike/revision.

Rollback triggerji: napačna valuta/izguba posnetka, podvajanje dispatcha, schema/API nezdružljivost, neuspešen smoke ali nejasno stanje aktivnih poslov. Najprej zadrži nadaljnje writerje/transport, zajemi sled, nato obnovi preizkušeno kopijo in ustrezne stare slike po dogovorjenem rezu. Če po rezu obstajajo novi zapisi, je potreben njihov varen popis/uskladitev; slepi restore jih lahko izgubi in ni samodejno dovoljen. Downgrade ni nadomestilo povratka podatkov. Dokaz povratka: read-only smoke in istovetnost pričakovanih podatkov/vrst, brez ponovitve negotovih dostav.

## 5. Prevzemne situacije in odprta dejstva

- F-H01: source/target se med pripravo spremenita → release manifest postane stale in se osveži, brez prepisa drugega dela.
- F-H02: zeleni neposredni testi + manjkajoč dejanski Flex/lease dokaz → neposredni popravek ima dokaz, celotni paket B/G1 in osnovna izdaja ostaneta odprta.
- F-H03: zeleni M brez D dovoljenja ali brez restore → :3000 ostane nespremenjen; preza-demo ostane izoliran.
- F-H04: padec med migracijo/novim API zagonom → preizkušen povratek slik/podatkov in noben dvojni aktivni posel.
- F-H05: legacy BL opis se prekriva z novo nalogo → status se spremeni samo ob dokazu manjkajočega poddela, zgodovinska števila so označena z datumom.

Odprti vhodi: končni testirani SHA in drug checkout, S-014 izvor, trenutna živa revizija/aktivne vrste, dejanski Flex z `Re`/bazami, cilj backup/restore, worker liveness pogodba in ločena dovoljenja M/D. Ta dokument ne trdi, da je karkoli od tega že potrjeno ali izvedeno. BL-215 se zapre za pripravljen in pregledan dokazni paket; dejanski prenos ima svoj ločen zapis ter datum.
