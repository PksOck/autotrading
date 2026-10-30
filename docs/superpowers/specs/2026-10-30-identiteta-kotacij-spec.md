# S-C · Minimalna identiteta kotacij

**Status: NEXT-SPEC / CONDITIONAL PROPOSAL.** 2026-10-30. BL-214, BL-194 in samo prekrivajoči del BL-174. Dejanska ciljna populacija in brokerjeve identitete še niso osvežene; zgodovinski opis »devet unknown« ni novo potrjeno število. Brez produktne izvedbe ali ponudniških klicev.

Podlage: [priprava SPEC](./2026-10-30-odprti-sklopi-priprava-spec.md), [glavni načrt C](../plans/2026-10-30-zakljucevanje-odprtih-sklopov.md), [S-B](./2026-10-30-flex-dividende-pogodba-spec.md). Statični ogled na osnovi `d0ceebf4cb28cb8919d23e00f2c419fa9c41d802`: `services/api/preza/services/identity.py:enrich_identity` preverja instrument_id, simbol, expected_updated_at in dvoumnost; Finnhub profil namenoma ne dopolni vrste/trgovalne valute. To zaščito ohrani.

## 1. Rezultat in izbrani minimalni pristop

Uporabnik vidi potrjeno kotacijo ali konkretno vrzel in lahko bere obstoječe podatke tudi pri unknown. Minimalni predlog je dopolnitev iz dokazljivega brokerjevega vira za točno izbrani instrument_id, s predogledom in sledjo. Simbol ni ključ identitete, ISIN ni dokaz iste borzne kotacije; valuta poročanja družbe ni trgovalna valuta.

Samodejni izbor prvega zadetka profila ni dovoljen. Splošen urejevalnik identitet, združevanje zgodovinskih instrumentov in množičen refresh fundamentov so izven tega SPEC. Če za konkreten instrument ni primernega brokerjevega dokaza, ostane unresolved; dodaten ročni vnos z neodvisnim dokazom zahteva dopolnitev pogodbe in pregled, ne tihega ugibanja.

## 2. Zahteve in pogodba

| ID | Vedenje in invariant | Dokaz |
|---|---|---|
| SC-01 | Read-only inventura targetov portfelj/watchlista: instrument_id, simbol, conid, ISIN, borza/MIC če potrjena, trgovalna valuta, kind, source/as_of, updated_at ter razlog vrzeli. Objavi dejansko število z datumom; brez računskih identifikatorjev v javnem demu. | F-C01 |
| SC-02 | Identiteta zahteva ujemanje izrecnega conid in brokerjevega tipa/valute/borze; ISIN pomaga potrditi instrument, ne določi borze sam. Konflikt že potrjenih polj blokira spremembo. | F-C02 |
| SC-03 | Predogled predlaga samo manjkajoča polja, vrne old/new, source, source_as_of, evidence_hash, expected_updated_at. Ime borze se ne reže; preslikava display-name → borza/MIC mora biti izrecna in dokazana. | F-C03 |
| SC-04 | Potrditev po uporabnikovem predogledu preveri revizijo pod DB zaklepom, append-only zapiše actor/čas/reason/old/new/evidence in atomarno dopolni isti instrument_id. Zastarela revizija vrne 409 `identity_conflict`, dvoumen kandidat brez sprememb `identity_ambiguous`. | F-C04 |
| SC-05 | Sprememba opisa ne revalvira zgodovinskih pozicij/cash, ne preveže analysis_run/signal/bar na drugo kotacijo in ne spreminja valut zgodovinskih zneskov. | F-C05 |
| SC-06 | SL/EN pokažeta confirmed/unresolved/conflict in source/as_of, ki ne pomenita transportnega loading/error. Unknown valuta ostane »ni potrjeno«, brez privzete USD. Napaka ne prepreči branja obstoječega instrumenta. | F-C06 |
| SC-07 | BL-174 razdeli dokazno: identiteta → BL-194; fundamentals/sync_run audit → BL-193 in bodoči S-D. Nobenega starega BL ne zapri samo zaradi prekrivanja besedila. | Inventurni zapis z dokazom obeh poddelov |

Predlagan vmesnik brez uvedbe obstoječe nepreverjene poti: interna Pydantic objekta `IdentityCandidate` in `IdentityConfirmation`; izvedbeni plan določi, ali obstoječi `/instruments` identity endpoint razširi ali doda ločeno pot. Zahtevana polja kandidata so zgoraj; confirmation vsebuje `instrument_id`, `expected_updated_at`, `candidate_hash` in reason. Kandidata ponovno validiraj ob potrditvi; browser ne določa source/as_of. No-op je uspeh z nič spremembami, isti kandidat/ista revizija ne dodaja podvojene revizijske sledi. Poljubna sprememba že potrjenih polj je konflikt, ne implicitna poprava zgodovine.

Stanja: `unresolved → candidate → confirmed`; konflikt `candidate → conflict → refreshed_candidate`; brez dokaza nazaj unresolved. Stanje candidate ni dokazljivo potrjena identiteta. Večnapravna sočasnost uporablja obstoječi updated_at oziroma novo eksplicitno revizijo, če izvajalec dokaže potrebo. Noben DB zaklep ne traja čez omrežni klic.

## 3. Podatkovna sprememba in omejitve

Preveri, ali obstoječa provenance zadošča za zgodovino; če ne, predlagaj append-only tabelo popravkov in novo naslednjo migracijo po dejanskem head. Ne dodajaj generičnega statusa v več modelov brez definicije. Backfill neznanih polj je dovoljen samo za preverjene kandidate; shrani seznam zadetih instrument_id in stare/nove vrednosti za povratek. Brez spajanja ključev, odstranjevanja vrstic ali prevrednotenja starega portfelja.

Predlog omejenega dela: inventura po keyset straneh po 100 instrumentov; predogled/potrditev ene kotacije na zahtevo. Noben GET ne sproži ponudniškega refresha; kvote in strošek novih virov so S-D. Izvoz vzorca za identiteto uporablja anonimiziran Flex iz S-B; ne bere .env ali zasebnih izpisov po lastni presoji.

## 4. Fixtures in vrata

- F-C01: datirana sintetična populacija mixed known/unknown; izhod vsebuje vse targete in konkretne razloge, brez trditve o dejanskem trenutnem številu.
- F-C02: en simbol na dveh borzah/valutah, isti ISIN na dveh kotacijah, drug conid; napačen kandidat ne dopolni niti vrste niti valute.
- F-C03: profil z valuto poročanja in predolgim imenom borze; valuta ostane unknown, ni truncation ali domnevnega MIC.
- F-C04: dva predogleda iste revizije, prva potrditev uspe, druga 409; dvakratno pošiljanje uspešne potrditve ne ustvari dvojne sledi. Posebej candidate-hash mismatch.
- F-C05: instrument z obstoječimi pozicijami, bar in analysis; pred/po ostanejo vsi FK in zgodovinski zneski/valute isti.
- F-C06: SL/EN, telefon, tipkovnica; vir/čas/vrzel ostanejo vidni pri napaki in refreshu.

Vrata: pytest identity/instruments/read-model regresije, ruff/mypy, po spremembi API generiranje OpenAPI/TS in Vitest; omejeni Playwright samo :3100. Vse uporablja fake provider in izolirano DB. Za dejansko zaprtje BL-194 potrebuje vsaka osvežena ciljna kotacija dokaz ali izrecno sprejeto nerešenost; sintetični fixture ne potrdi osebnih kotacij.

**Odprto:** trenutni seznam targetov, dejanski FinancialInstrumentInformation/AccountInformation format, mapiranje borz, zadostnost revizijske sheme ter sprejem obsega nerazrešenih kotacij. Do takrat veljajo obstoječe varovalke; dokument ni odobritev novega vira ali ročnega prepisa identitete.
