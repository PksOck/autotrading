# Neodvisen UX/UI pregled Preže

**Datum:** 2026-10-28 · **Pregledovalec:** podagent Astra · **Status:** zaključen neodvisni pregled in večji predlog UX/UI, brez implementacije; celoviti živi prevzem še ni izveden. Posodobljeno po uporabnikovi potrditvi: več funkcionalnih informacij, manj obsežne kontrole, prilagodljivi stolpci po aplikaciji.

## Obseg in dokazna meja

**Veljavna pregledana osnova:** `1855eb8d37a6257d3b096ca055d0d9c665a4a20e` v `C:\Users\Jan\Documents\Claude-autotrading\.claude\worktrees\preverjanje-podatkovnih-povezav-53ab37`. Glavna mapa pri `c0c15ae` je bila začetna, zastarela osnova. Po odkritju razlike je bil pregled ponovno usklajen: prebrani S-013 do S-008, aktualni PLAN/BACKLOG/DESIGN, seznam 197 spremenjenih datotek in relevantne UI/API spremembe med osnovama, nove komponente Analiz, Tez in Uspešnosti, poti API ter ADR-0013 do ADR-0016. Stari citati vrstic spodaj veljajo za začetni pregled; imena komponent in funkcij so merodajna pri novejši osnovi. Pri nespremenjenih datotekah (RadarView, EntriesView, SignalsInbox, PeekPanel, InstrumentPreview, portfolio service, signal/proposal routes, Overview) je enakost med osnovama preverjena z Git diffom.

Pregledane so vse dejanske poti zaslonov in njihove glavne komponente/pogodbe, ne vsaka vrstica celotnega repozitorija. V tej nalogi nisem upravljal brskalnika, izvajal aplikacijskih testov ali sprožil analiz, sinhronizacij in zunanjih klicev.

**K** pomeni dokaz iz kode, **L** pomeni živo opažanje, ki ga je posredoval vodilni agent, **H** pomeni hipotezo za nadaljnji preizkus. L ni moj samostojen preizkus in ne potrjuje vseh robnih primerov. Potreben je ločen dokaz, da strežniški build v celoti ustreza pregledanemu SHA; živi prikaz in trenutna koda se ne smeta nekritično enačiti.

Pregled ne spreminja aplikacije, skupnega BACKLOG ali SESSIONS. Obstoječe spremembe v teh datotekah, `docs/superpowers/` in `graphify-out/` ostanejo nedotaknjene. Nova odobrena arhitekturna odločitev ni bila sprejeta.

## Kaj novejša različica že ima

| Področje | Potrjeno pri `1855eb8` | Posledica za načrt |
|---|---|---|
| Analiza | `DecisionHeader`, 3 `HorizonCard`, `EvidenceSplit`, zložena utemeljitev/kontrola/koraki; bogatejša tabela in mobilne kartice | Ne graditi novih obetov; izboljšati gostoto, izbiro stolpcev, napake in ločitev časa analize od trenutnih podatkov |
| Teze | seznam in detail, osnutek iz analize, urejanje/potrditev, zgodovina dokazov, tedenski pregledi in predlogi sprememb | Teze niso placeholder; izboljšati pregled nad odprtimi spremembami in dolge revizije |
| Uspešnost | horizonti 1/5/20/60, lastni/sistemski signali, skupine in kalibracija; predlog uteži z izrecno potrditvijo | Uspešnost ni placeholder; izboljšati razlago obsega in pot od agregata do izidov |
| Windows/Android | platformna bližnjica, 5 spodnjih ciljev, segmentirani gumbi, brez blur, globalna 48 px dotikalna površina, modalna tipka nazaj | Ne ponavljati že izvedene prenove ADR-0013; kompaktnost izboljšati za miško, 48 px ohraniti na dotiku |
| Portfelj | Flex XML uvoz brez tokena, API `/portfolio/import`, omejitev 10 MB, validacija | Ne predlagati osnovnega uvoza kot nove funkcije; dodati razumljiv povzetek rezultata/pokritosti |
| Watchlista | takojšnji posel za cene ob dodaji | Ne trditi, da so cene šele nočne; prikaz cene, napak in osvežitve še izboljšati |
| Govorice | deterministični klasifikator tudi v Radarju; izboljšana zaščita analiz | Ohraniti; »ni govorica« pa še vedno ni isto kot »uradno potrjeno« v UI |
| Izvajanje analiz | vitki zaporedni delniški tok, poraba po klicih in recovery predolgih zagonov | Ne graditi novega agentskega toka; obstoječe podatke smiselno prikazati |

Aktualni BACKLOG že uporablja **BL-161–187 za druge naloge**. Številke iz starega lokalnega načrta nastavitev/analiz/dividend/Watchliste se zato ne smejo prenesti v izvedbo. V tem poročilu so novi predlogi označeni samo z UX-Axx; pred novim izvedbenim načrtom je potrebna preslikava na dejanski prost razpon trenutne veje.

## Posredovani živi dokazi

Vodilni agent je 2026-10-28 pregledal `http://localhost:3000` v IAB, namizno 1440 × 1000 in začetno ozko približno 544 × 1220. V spodnjih opažanjih ni izvedel mutacij.

| L-ID | Opažanje | Povezava z ugotovitvijo |
|---|---|---|
| L-01 | Pregled kaže vzorčno premoženje 248.310 USD in vzorčni zemljevid; portfelj je prazen, brez sinhronizacije | UX-A01/A07 |
| L-02 | »Novo danes« kaže vzorčne MSFT/SMH/KSTL; živa zavihka Novo in Spremljam v Signalih sta prazna | UX-A01 |
| L-03 | Radar ima več deset dolgih vrstic s celotnimi povzetki in oznako »Potrjeno«; izbrani NATH ima vir star približno dva dni, vrstica kaže le 14:00 | UX-A02/A03 in kompaktna tabela UX-A17 |
| L-04 | Vstopi imajo en ASML, zemljevid približno 300 px za eno točko; vzrok »Neznano« ob besedilu »Teza drži«, vrednotenje manjka, cena v vrstici nima valute | UX-A06; logične resničnosti teze ne sklepamo samo iz tega opažanja |
| L-05 | Analiza `b9563231-1438-4744-acbc-b7b14c18e023` že kaže trenutno ceno/pozicijo in tri horizonte. Cena je z 28. 10., analiza s 27. 10., dokazi s 26. 10.; ločitev časov je šibka. Velik blok surove ponudniške napake ostaja | UX-A11 |
| L-06 | Predlogi vsebujejo več kot deset podobnih neuspelih AMD/NVDA kartic in surov poškodovan JSON | UX-A14; podobnost kartic sama ne dokazuje podvojenih ID-jev ali napake idempotence |

Dodatna opažanja vodilnega agenta: **L-07**, mobilni Radar pri 390 × 844 po izboru drugega dogodka GETY spremeni podrobnosti, vendar so pod celotnim seznamom, približno 20.959 CSS px od vrha dokumenta; trenutni pomik je 451 px, brez dialoga ali pomika do podrobnosti. Dve vrstici glave merita približno 118 px, filtri porabijo velik del preostalega prvega zaslona. **L-08**, instrument WM kaže neznano valuto/borzo/ISIN, cena pa je označena z USD oziroma $; manjka ime podjetja, dejanji »Analiziraj«/»Globoka analiza« nista jasno ločeni. **L-09**, Teze in Uspešnost sta v živi aplikaciji že prisotna, Nastavitve in Opcije ostajajo načrtovane. **L-10**, uporabnikov poznejši uvoz je napolnil pravi Portfelj; L-01 je dokaz prejšnjega praznega stanja, ne trenutne vsebine računa. Osebnih zneskov novega uvoza poročilo ne hrani. Ločena demo instanca na vratih 3100 ni bila dosegljiva (connection refused). **L-11**, mobilni »Več« odpre iskalno paleto z dolgim seznamom instrumentov pred navigacijo. Vodilni agent je na Radarju preveril temno temo in jo vrnil na sistemsko; to ni dokaz vseh zaslonov v obeh temah.

Živa pokritost tega podagenta je omejena na posredovana opažanja. Ni samostojno upravljal ali testiral UI. Celovito mobilno pot, Android Back, izpad API, obnovitev Watchliste, filtre vseh zaslonov in večračunske/FX primere je treba prevzeti posebej. Prisotnost Tez/Uspešnosti v živi aplikaciji ne potrjuje vseh njunih mutacij. Ni trditve, da je celotna testna matrika že uspešna.

## Glavna ugotovitev

Preža že ima primerno osnovo: mirne barve, jasen simbol, i18n, različici teme, URL za del izbire, ločene analize in signalni nabiralnik, navedbe virov ter deterministične numerične podatke. Največ koristi prinese dokončanje teh temeljev: odprta povezava mora pokazati pravi objekt, manjkajoči podatek ne sme postati vzorec ali ničla, uporabnik pa mora razlikovati med zdravim servisom, svežimi podatki in končano nalogo.

Priporočam celovito prenovo uporabniških poti in gostote informacij z ohranitvijo znamke, barv in dokaznih pravil. Skupna kompaktna tabela, manjša namizna orodna vrstica, prilagodljivi stolpci in jasne podrobnosti naj povežejo aplikacijo. Semantične popravke podatkov in navigacije vključiti v iste poti, da boljši prikaz ne utrdi napačnih informacij. Zaenkrat niso potrebni novi meniji za trgovalne strategije, splošni workflow urejevalnik ali zgodnejši razvoj M6/M7.

Prioritete v tem dokumentu:

- **P1:** napačna interpretacija podatkov, napačen ciljni objekt ali izguba podatkov pri razveljavitvi; pred vsakodnevno uporabo.
- **P2:** ovira pri pogostem opravilu, manjka opazen status ali navigacijski kontekst; naslednja izdaja uporabnosti.
- **P3:** izpopolnitev po odpravi glavnih ovir.

## Razmerje do obstoječega načrta

[Stari osnutek nastavitev, analiz, portfelja in Watchliste](../superpowers/plans/2026-10-28-nastavitve-analize-portfelj.md) že pokriva rezultate in retry Predlogov, filtre Analiz, urnike procesov, paketne analize, dividendno evidenco ter podatke in izbirne stolpce Watchliste. Vsebinske zahteve je treba ponovno vključiti v en skupen načrt po aktualni kodi, brez prenosa zasedenih BL identifikatorjev. Ta dokument jih dopolnjuje; stari osnutek ni izvršljiv načrt za trenutno vejo.

| Že pokrito | Dopolnitev iz tega pregleda |
|---|---|
| Rezultati in ponovitev Predlogov | Prepoznaven izbrani instrument, ohranitev osnutka in izvornega dogodka; skupna pogodba napak tudi v drugih modulih |
| Filtri seznama Analiz | Povratek v prejšnji filtrirani seznam, status povezave v podrobnosti in razumljiv povzetek zaključene analize |
| Nastavitve procesov | Zdravje servisa ločiti od zdravja opravila in svežine podatkov; status dostopen na telefonu |
| Računi in posnetki | Isto pravilno izbiro posnetkov uporabiti v običajnem prikazu Portfelja in Radarju, ne samo v paketih/dividendah |
| Prilagodljiva Watchlista | Razveljavitev mora ohraniti prvotno ceno/datum dodaje in vsa polja; ureditev obstoječih opomb in oznak |
| BL-052, Pregled | Dokončanje resničnih podatkov je že odprta naloga; ni nova funkcija |

Spodnji identifikatorji **UX-A01–UX-A17** so lokalne reference tega predloga, ne rezervirani BL ID-ji. Vodilni agent naj po uskladitvi obsega doda dejanske BL naloge brez podvajanja že odprtih.

## Pregled zaslonov in konkretni predlogi

### UX-A01 · Pregled `/` · P1 · K

**Dokaz:** `apps/web/app/page.tsx:10–46` uporablja vzorčne `REGIME`, `PULSE_EVENTS`, `SIGNALS`, `FUNNEL` poleg živih `PortfolioTreemapCard`, `PortfolioValue` in `InZoneCard`. Glava sicer nosi oznako vzorčnega pogleda. `PortfolioValue.tsx:13–29` pri odsotnem `total_value` pokaže vzorčno vrednost 248.310 in vzorčno spremembo. `PortfolioTreemapCard.tsx` pri praznih pozicijah uporabi `INSTRUMENTS`. `InZoneCard.tsx` ne loči napake API od praznega rezultata. Vzorčne kartice imajo uporabniška dejanja; »Zavrzi« je tam lokalno stanje, ne stanje pravega signala.

**Posledica:** začetni zaslon ne poda zanesljivega odgovora, kaj je danes res novo. Oznaka na vrhu ne razloži mešanega izvora posameznih kartic. Napaka ali prazen portfelj lahko pokažeta premoženje, ki uporabniku ne pripada.

**Predlagano vedenje:** običajni Pregled prikazuje samo dejanske podatke, stare uspešno naložene podatke z opozorilom ali pojasnjeno praznino. Vzorci ostanejo na `/ux` oziroma v izrecnem demonstracijskem načinu. Glavni vrstni red: »Potrebuje pregled« (novi signali, napake, zastarelo), stanje portfelja, pomembni dogodki, kandidati v coni. Neizvedeni režim/lijak sta začasno odstranjena ali jasno neaktivna; ne izmišljamo njunih API metrik. Število in kartice novih signalov izvirajo iz istega filtra kot Signali.

**Odvisnosti:** dokončanje BL-052, pogodba popolnosti portfelja UX-A07, skupno stanje kartic UX-A12. Za vsako živo agregacijo definirati obdobje in status, npr. »novi« proti »ustvarjeni danes«.

**Prevzem:** z istim fiksnim API naborom se Pregled in Signali ujemata; prazna baza, HTTP 503 in delni portfelj nikoli ne pokažejo vzorčne vrednosti; napaka Vstopov ne postane »ni kandidatov«; tudi po izgubi povezave ostane izvor vsake vidne kartice jasen.

### UX-A02 · Radar `/radar` · P1 · K

**Dokaz:** `RadarView.tsx:75` išče `?event=` samo v trenutno filtriranem seznamu, nato brez opozorila izbere prvi dogodek. Seznam je omejen na pogled in privzetih sedem dni; API za neposreden dogodek že obstaja v `routes/radar.py`. `radar_views.py:61–75` omeji kandidatski nabor pred filtriranjem po portfelju/watchlisti, zato veljaven dogodek lahko ostane zunaj nabora. Tip in najmanjša ocena sta lokalno stanje, ne URL. V seznamu je prikazana le ura, čeprav dogodki pokrivajo več dni.

**Predlagano vedenje:** pri podanem ID-ju neposredno naložiti točno dogodek. Če ni v izbranem pogledu ali obdobju, ga vseeno odpreti z oznako »Zunaj trenutnega filtra« in ohraniti seznam. Če ne obstaja, prikazati »Dogodek ni na voljo«, nikoli nadomestnega. Filtri tip/ocena/obdobje/razvrščanje v URL; preprosto »Po pomembnosti / Najnovejši«. Pri uri pokazati tudi datum oziroma dnevne skupine. Vire razkriti vse prek »Pokaži vse vire«, ker je zdaj seznam odrezan na šest.

**Odvisnosti:** skupna pogodba globokih povezav UX-A04; pogled in filtre uporabiti v podatkovni poizvedbi pred omejitvijo; determinističen vrstni red z ID-jem; paginacija/»Naloži več« in označena omejitev rezultatov. Ne filtrirati samo prvih 100 prenesenih dogodkov.

**Prevzem:** povezava do dogodka pred več kot sedmimi dnevi, dogodka iz drugega pogleda in dogodka zunaj prvih 300 kandidatov odpre pravi ID; osvežitev ohrani filtre; neveljaven ID pokaže napako; čez več dni sta čas in vrstni red razumljiva.

### UX-A03 · Radar: pomen »Potrjeno« · P1 · K

**Dokaz:** `RadarView.tsx:185,219` pokaže »Potrjeno« vedno, ko je `is_rumor === false`. `domain/radar.py` v `EventOut` nima posebnega statusa uradne potrditve. `radar/cluster.py` že uporablja deterministični klasifikator govorice. `radar/triage.py` uporablja uradni vir pri obravnavi govoric, toda navadna negovorica ni nujno uradno potrjena trditev.

**Predlagano vedenje:** ločiti »Uradni vir«, »Novica«, »Nepotrjeno« in »Čaka na presojo«. Zelena potrditev zahteva navedbo konkretnega uradnega vira. Pri oceni pokazati kratek opis, da gre za prioritizacijo raziskave, ne verjetnost donosa. Podrobnosti lahko ločijo deterministično reakcijo cene od modelskih ocen pomembnosti in novosti.

**Odvisnosti:** nova izpeljana pogodba potrditve iz dejanskih virov; točen pomen stanj uskladiti z obstoječim pravilom govoric, ne sklepati potrditve samo iz odsotnosti zastavice. Če se stanje hrani, sledi migracija. Cenovno reakcijo še vedno računa deterministična logika; modelske ocene ostanejo jasno označene.

**Prevzem:** neobdelan članek, običajna novica brez uradnega vira, govorica in dogodek z uradnim filingom dobijo različne ustrezne oznake. Zelena oznaka vedno omogoča odpreti njen dokaz.

### UX-A04 · Signali, Vstopi, Telegram in kukalo · P1 · K

**Dokaz:** `EntriesView.tsx:245` ter `services/api/preza/notify/telegram.py` ustvarjata `/signals?peek=signal:{id}`. `PeekPanel.tsx:57–63` prikazuje samo instrumente, ostali tipi dobijo »ni najdeno«. `entities.ts` sicer dovoljuje še signal, dogodek, analizo, tezo in predlog. `SignalOut` že ima `event_id`, `proposal_id` in dokaze, a kartica jih ne poveže v sled. API trenutno nima samostojnega `GET /signals/{id}`.

**Predlagano vedenje:** signal odpre lastni prikaz po ID-ju, tudi če ni v trenutnem zavihku ali prvih 100 vrsticah. Prikaže simbol, stanje, veljavnost, razlago in dokaze ter povezavo na izvorni dogodek/predlog; cenovne ravni samo, ko imajo tudi pravilno valuto in čas. Na telefonu se odpre celozaslonski panel, na namizju kukalo. Zdaj podprte tipe uskladiti s tipom URL, ne oglaševati praznega splošnega mehanizma. Za analizo uporabiti obstoječo polno stran.

**Odvisnosti:** `GET /signals/{id}`, skupna navigacija entitet, API identiteta instrumenta pri več kotacijah. Zgodovina kukala mora biti določena: `history.back()` danes lahko pri neposrednem prihodu zapusti aplikacijo. Varna notranja vrnitev brez zgodovine naj zapre panel in ostane na osnovnem seznamu.

**Prevzem:** dejanska Telegram povezava neposredno odpre pravi signal; deluje sprejet, zavržen, potekel in starejši signal zunaj prve strani; Escape/zapri vrne fokus; nazaj deluje po odpiranju iz seznama in po neposrednem prihodu; signal ne kaže napačnega objekta ali praznega instrumentnega kukala.

### UX-A05 · Signali `/signals` · P2 · K

**Dokaz:** `SignalsInbox.tsx:16` ima štiri statuse brez `expired`; ni prikaza vrste/obsega, čeprav API že podpira `kind`. `routes/signals.py:59–69` filtrira po statusu pred naknadnim prehodom poteklih zapisov v `expired`. `setStatus` čaka `mutateAsync` brez obravnave napake, dejanja pa nimajo blokade med zahtevo. »Spremljaj« spremeni status signala, ne watchliste instrumenta.

**Predlagano vedenje:** jasen nabiralnik z Novo/Spremljam/Sprejeto/Arhiv, kjer sta zavrženo in poteklo razločljiva. Uporabiti URL filtre za tip in simbol ter smiselno razvrščanje. Ob »Sprejmi« kratko besedilo »Označi kot izbrano raziskovalno idejo. Naročilo se ne odda.« Spremljanje signala in dodajanje instrumenta na watchlisto imata različni imeni. Med zahtevo zakleniti samo zadevno vrstico; ob napaki ohraniti stanje in ponuditi ponovitev; razveljavitev vrne prejšnji status.

**Odvisnosti:** učinkovito stanje poteka določiti pred filtrom v SQL ali s trajnim procesom in pravilnim bralnim pogojem; paginacija in štetje na celotnem filtriranem naboru. Nobene povezave na oddajo naročil.

**Prevzem:** potekel signal se ne pojavi pod »Novo«, njegov globoki URL ostane veljaven; dva hitra klika ne ustvarita dveh sprememb; HTTP 409/503 ne izgine brez pojasnila; razveljavitev ne prepiše novejšega nasprotujočega stanja brez preverjanja.

### UX-A06 · Vstopi `/entries` · P1/P2 · K in H

**Dokaz K:** `EntriesView.tsx:285–292` hrani filter lokalno in pri `?symbol=` zunaj filtra samodejno izbere prvo drugo vrstico. Seznam navaja ceno brez valute. Podrobnosti pri `thesis_intact !== false` ob obstoječi razlagi pokažejo nedotaknjeno tezo, torej tudi pri `null`. Filter »v coni« vključuje tudi `below`; enak širši izbor uporablja kartica na Pregledu. `LadderTable.tsx` sprejme decimalno vejico z enostavno zamenjavo, nima izrecne validacije lokaliziranih vnosov ali prikaza ostanka po zaokrožitvi delnic.

**Predlagano vedenje:** ohraniti izbrani simbol iz povezave, četudi je »brez aktivnih pravil«, in to pojasniti. Ločiti »V coni« od »Pod cono«; pod stopom mora biti stanje izrecno opozorilno, ne zgolj najugodnejša cena. `thesis_intact` je tri-stanjski: drži/ne drži/ni ocenjena. Cena v vrstici vedno vsebuje valuto ali vidno skupno valutno oznako. Lestvica ostane raziskovalni izračun, z validacijo zneska, pravilno valuto, delitvijo proračuna in ostankom; brez trditev o dejansko izvršljivem naročilu.

**Dokaz K in L-07 za Radar, H za enako mobilno posledico Vstopov:** na telefonu podrobnosti po izbiri niso dovolj vidne, ker se `aside` izriše za celotnim seznamom (`EntriesView.tsx:369`). Enaka ureditev je na Radarju. Preveriti na dolgem seznamu, nato uporabiti skupni mobilni panel ali jasno premakniti fokus na detail z možnostjo vrnitve v isto vrstico. Namizni dvojni stolpec ostane.

**Odvisnosti:** UX-A04/A12; pravilo stop/cona določiti v deterministični domeni; lokalizirano parsiranje in decimalni izračun, ne LLM. Pri dostopnosti ne siliti uporabe grafa: enako izbiro zagotovi seznam.

**Prevzem:** neposreden URL do neaktivnega simbola ne odpre drugega; `null` nikoli ne pomeni potrjene teze; EUR/USD primeri imajo valuto; veljaven lokaliziran znesek deluje, napačen vnos pokaže napako; na 390 px izbor 30. vrstice odpre vidne podrobnosti in omogoči vrnitev.

### UX-A07 · Portfelj `/portfolio` · P1 · K

**Dokaz:** `services/portfolio.py:131–168` izbere globalno največji datum pozicij, ne zadnjega po računu. Vsota uporablja le znane pretvorjene vrednosti in gotovino v osnovni valuti; `PortfolioOut` nima oznake popolnosti. Pozicijska polja nimajo ID-ja računa/instrumenta; React vrstice uporablja `key={p.symbol}`. `PositionsPanel.tsx:141` količino zaokroži na nič decimalk. Toplotni zemljevid manjkajočo dnevno spremembo pretvori v 0. Postavka »Danes« temelji na zadnjih dveh svečah brez lastnega datuma v odgovoru.

**Predlagano vedenje:** vrhnja vsota navede obseg računov, valuto, čas posnetka in popolnost. Ob nepopolnih FX podatkih pokazati »Znani del vrednosti« in izključene postavke oziroma vsote po valutah; ne predstavljati delne vsote kot celotne. Zadnje posnetke obravnavati po računih tudi pri praznem računu. Frakcijske delnice ohranijo smiselno natančnost. Manjkajoča sprememba v treemapu je nevtralno »ni podatka«, ne 0 %. Ločiti datum Flex pozicije od datuma tržne spremembe.

**Odvisnosti:** skupna podatkovna rešitev s predlogom posnetkov po računih, posebej potrditev praznega posnetka in več računov; `PositionOut` dobi stabilno identiteto in provenance; agregacije ostanejo `Decimal`. Popraviti tudi prikaz v kukalu in Pregledu, sicer ostane ista napaka drugje.

**Prevzem:** dva računa z različnima datumoma, isti simbol na dveh računih, gotovina brez pozicij, manjkajoč FX, tujevalutna gotovina ter količina 0,25; vsak ima pravilen prikaz obsega/popolnosti, brez izgubljene vrstice in brez lažne ničle. Različna časa cene in Flex posnetka sta vidna.

### UX-A08 · Portfelj: sinhronizacija · P2 · K

**Dokaz:** `usePortfolioSync` po potrditvi uvrstitve sproži eno invalidacijo. `usePortfolio` nima namenskega spremljanja tega opravila, gumb pa je onemogočen samo med HTTP zahtevo (`PositionsPanel.tsx:80`). API vrne `job_id`, `SyncInfo` pa nima ID-ja oziroma trenutnega stanja, s katerim bi UI zanesljivo spremljal ta zahtevek.

**Že obstaja:** XML uvoz z validacijo in omejitvijo velikosti. Dopolnitev naj pokaže rezultat z datumom posnetka, številom uvoženih/izpuščenih zapisov in razlogi ter ponovljivim povzetkom; ne izdelovati drugega uvoznika.

**Predlagano vedenje:** ločiti »V vrsti«, »Uvažam«, »Končano« in »Ni uspelo« za konkretni zahtevek. Zadnji uspešni posnetek ostane viden. Po zaključku samodejno osvežiti podatke; ob neuspehu ohraniti dostop do starega posnetka in navesti učinek napake. Večkratni klik naj ne postavi več enakih uvozov.

**Odvisnosti:** uporabiti `ProcessExecution` iz predloga procesov, ne drugega vzporednega sistema zgodovine. Ročna sinhronizacija in periodično opravilo delita identiteto/varovala.

**Prevzem:** počasen uvoz, neuspeh in ponovno odprtje strani imajo pravilen vidni status; uspeh posodobi stran brez ponovnega ročnega klika; kratka potrditev »v vrsti« se ne predstavlja kot končan uvoz.

### UX-A09 · Watchlista `/portfolio?tab=watchlist` · P1/P2 · K

**Dokaz:** `WatchlistPanel.tsx:32–37` in `WatchButton.tsx:18–21` razveljavita brisanje z novim POST. `services/watchlist.py:76` ob novem vnosu ponovno določi ceno dodaje; datum nastane znova. Ponovna dodaja ne ohrani vseh polj, pri WatchButton tudi oznak ne. Zato razveljavitev lahko spremeni donos »Od dodaje«. Pogodba že podpira opombo, oznake, ciljno ceno in pregledano, UI pa opombe po dodaji ne ureja. Napaka začetnega GET ni posebej prikazana.

**Predlagano vedenje:** razveljavitev obnovi isti zapis z isto zgodovinsko osnovo in vsemi metapodatki. Dodati »Uredi« za obstoječo opombo/oznake in premislek o že podprti ciljni ceni; ne ponujati navidezno aktivnih cenovnih obvestil, dokler izvajalni proces ni potrjen. Gumb z oznako »Na watchlisti« naj jasno nakaže, da je to stanje, odstranitev pa naj bo izrecno dejanje. Za ponovni pregled omogočiti tudi povratek v »Ni pregledano«.

**Odvisnosti:** dopolniti predlog prikaza Watchliste z dejansko obnovitvijo (npr. mehko brisanje in restore), ne zgolj kozmetičnim toastom. Predlog podatkov Watchliste ostane lastnik dodatnih metrik. Ureditev obrazca naj uporabi isti izbirnik instrumenta kot Predlogi.

**Prevzem:** primerjaj celoten zapis pred brisanjem in po razveljavitvi, vključno z `added_at`, `added_price`, `source`, `tags`, opombo, ciljem, opozorili in `reviewed_at`; donos ostane enak. Ob neuspeli obnovitvi jasno pojasnilo, ne lažna potrditev. GET 503 ima vidno sporočilo in ponovitev.

### UX-A10 · Instrument `/i/[symbol]` in iskanje · P1/P2 · K

**Dokaz:** `InstrumentView.tsx:70–87` posebej obravnava le 404 in uporablja USD, če valuta manjka. Odsotna zaključna cena lahko ostane prikazana kot skeleton. Napaka sveč pade v »ni sveč«. Cena glave prihaja iz `useInstrument`, prikazana provenance pa lahko iz ločeno osveženih `bars` (`:121–129`); po osvežitvi sveč se glava ne invalidira. `routes/instruments.py:44,69` uporablja `fetched_at` kot `as_of`, torej čas pridobitve, ne datum sveče. Iskanje vrne borzo, a identiteta/ključ in odprtje sta zgolj simbol (`CommandPalette.tsx:60,96`, `find_by_symbol`). Pri več kotacijah izbrana borza zato ni zagotovljena.

**Predlagano vedenje:** ena razpoznavna glava instrumenta: simbol, polno ime, borza, valuta, zadnja zaključna cena in njen datum. »Pridobljeno« je dodatni čas, ne nadomestilo za tržni datum. Cena in označen vir izvirata iz istega posnetka. Neznana valuta ostane neznana; neznan tip ni delnica. Iskalnik pokaže kotacijo, uporabnikova izbira se prenese s stabilnim ID-jem v nadaljnje korake. »Analiziraj« ponuja jasno izbiro hitre/standardne/globoke analize, pri globoki pokaže porabo kvote v navadnem besedilu, ne le v tooltipu. Povezava »Vse analize« ohrani instrument.

**Odvisnosti:** API identiteta kotacije ter ločena `market_as_of`/`fetched_at`; uskladitev s predlogom filtrov Analiz in podatkov Watchliste; obstoječi instrumentni URL ohraniti združljiv, dvoumnost rešiti izrecno. Za prvi korak ni potrebna nova finančna analitika. ETF profil in osnovni fundamenti so kasnejša vsebina samo iz preverjenih API virov.

**Prevzem:** en simbol z dvema borzama odpre izbrano kotacijo; cena in datum se po osvežitvi ujemata; 500, prazne sveče, manjka cena, neznan tip in neznana valuta imajo različna pravilna stanja; skeleton ne ostane po zaključenem neuspehu.

### UX-A11 · Analize `/analysis` in `/analysis/[runId]` · P1/P2 · K in L-05

**Že obstaja:** kartica odločitve, trije horizonti, deterministični dokazi, manjkajoči podatki, časovnice in zložene podrobnosti. Seznam ima bogate namizne stolpce ter mobilne kartice. Ne izdelovati novega povzetka ali novih horizonov vzporedno z njimi.

**Dokaz:** `DecisionHeader` pridobi trenutno ceno z ločenim `useBars`, pozicijo z `usePortfolio`; ti podatki niso posnetek ob analizi. Trenutna cena v glavi nima jasne valute. Različni časi analize, dokazov in cene so v živem primeru slabo ločeni. Ob nenaloženem/okvarjenem portfelju ni varno sklepati, da instrumenta nimamo. `AnalysisView` še vedno izpiše `run.error` neposredno, hipotezo pokaže šele ob rezultatu presoje in se vrača na goli seznam. `AgentTimeline` ob izgubi SSE spremeni piko, besedilo obdelave pa ne pojasni odklopa. Horizont podrobnosti je lokalno stanje. API seznama podpira omejen nabor filtrov; bogate tabele ni mogoče prilagoditi.

**Predlagano vedenje:** ohraniti obstoječo hierarhijo odločitve, pod njo ločiti »Analiza z dne …, dokazi do …« in »Trenutno: cena … valuta, datum …; pozicija iz posnetka …«. Svežih cen ne predstavljati kot dokazov stare analize. Neznana pozicija ostane neznana. Seznam dobi URL filtre (instrument, status, ocena, datum, globina, v portfelju/watchlisti), izbiro stolpcev in pogled »Zadnja zaključena na instrument« ob ločeni vidni čakalni vrsti. Privzeta tabela pokaže simbol, status, čas in tri horizonte; razlage/kontraargumenti so razširljivi. Neuspeh ima kratko prevedeno razlago, diagnostiko v zaprtem razdelku in varno ponovitev. Med izvajanjem ločiti vrsto, delo, povezavo in dokazani zastoj; hipoteza ostane vidna od začetka. Vrnitev ohrani seznam in položaj.

**Odvisnosti:** UX-A10/A12/A17, strežniški filtri pred paginacijo, pogodba napak, podatki o stanju opravila. Uporabiti obstoječo porabo klicev za prikaz dejansko porabljenega, ne obljubljenega stroška. Enoten pomen ocene med `run.rating` in `card.rating` ter zgodovinske razlike naj se preveri na shranjenih primerih; morebitnega razhajanja ne prikriti z izbiro ene vrednosti v UI. Brez izmišljenega ETA ali odstotka napredka.

**Prevzem:** obstoječe tri kartice ohranijo vsebino; primer s tremi različnimi datumi je nedvoumen; HTTP napaka portfelja ne pokaže »ni v portfelju«; odklop SSE je besedilno viden; hipoteza je vidna v vrsti; dolg ponudniški error ne prevzame strani; filters/columns/back delujejo po osvežitvi. Primerjava s prejšnjo analizo uporabi že obstoječi `card.previous`.
### UX-A12 · Vsi zasloni: skupna stanja, svežina in dejanja · P1/P2 · K

**Dokaz:** DESIGN §5 zahteva izolirano nalaganje, praznino, zastarelost, napako in delne podatke. Dejanska obravnava je različna: Watchlista GET napake nima; InstrumentPreview pri ne-404 napaki ostane skeleton, pri nenaloženem Portfelju pa lahko pokaže »ni v portfelju«; InZoneCard napako obravnava kot brez kandidatov. Mutacije in razveljavitve se razlikujejo med SignalCard, WatchButton in WatchlistPanel.

**Predlagano vedenje:** uvesti majhen skupni vzorec kartice z ločenimi `loading`, `ready`, `empty`, `error`, `stale`, `partial`. Ob sekundarni napaki ohraniti zadnje podatke in pokazati »Osvežitev ni uspela«. Praznina loči »Ni podatkov«, »Ni zadetkov za filtre«, »Vir še ni nastavljen« in »Opravilo še ni teklo«, vsaka s konkretnim dejanjem. Mutacija ima pending na vrstici, znano prevedeno napako, varno ponovitev in pošteno razveljavitev. Svežina je po tipu podatka: EOD sveče, Flex posnetek, fundamenti in analiza nimajo istega praga.

**Odvisnosti:** skupna pogodba napak z `code` in uporabniškim razlogom; po potrebi vir/čas/popolnost na posameznem bloku, ne samo na strani. `null` ni 0 in ne pomeni »nima pozicije«. Skupni `DataState` ne sme postati generična komponenta z desetinami nepovezanih možnosti; graditi iz resničnih stanj treh ključnih zaslonov.

**Prevzem:** pogodbeni nabor vseh šestih stanj na Pregledu, Instrumentu, Watchlisti, Radarju in Portfelju; lokalizirana sporočila SL/EN; brez vzorčnih nadomestkov, neskončnih skeletonov ali izginulih podatkov ob začasni napaki.

### UX-A13 · Lupina, Nastavitve in mobilni prikaz · P2 · K in L-07/L-09

**Že obstaja:** ADR-0013, pet spodnjih ciljev, platformna Ctrl/⌘ bližnjica, segmentirani gumbi, 48 px dotikalne površine pri `pointer: coarse` in zapiranje modalov s tipko nazaj. Teh izboljšav ne predlagamo znova.

**Dokaz:** `SystemStatus` je še skrit pod `lg`, Nastavitve so `Planned`. `checks.py` za Flex/Telegram potrdi konfiguracijo, TCP Gateway preverjanje pa ne dokazuje prijavljenega API. Globalno pravilo 48 px velja tudi za povezave; vpliv na gostoto mobilnih dokazov je treba preveriti. Mobilna glava in filtri Radarja zavzamejo velik del prvega zaslona, izbrane podrobnosti ostanejo pod seznamom. `Shortcuts` ne izvaja vseh bližnjic, opisanih v DESIGN; dokument in dejansko pomoč je treba uskladiti.

**Predlagano vedenje:** namizna glava z naslovom, kontekstom in eno kompaktno vrstico dejanj; sekundarni opis ni stalna dodatna vrstica na telefonu. Mobilno vidni aktivni filtri in en gumb »Filtri«, celoten obrazec se odpre ločeno. »Več« naj odpre kratek navigacijski seznam; iskalna paleta ostane ločena, da dolgi zadetki instrumentov ne potisnejo navigacije iz dosega. Status sistema je dosegljiv tudi na telefonu in odpre Nastavitve → Povezave. Tam ločiti konfiguracijo, dosegljivost, zadnji uspešen tek, svežino in posledico. Nastavitve → Procesi naj uporabijo gosto tabelo opravil z urnikom, časovnim pasom, zadnjim/naslednjim tekom in statusom; podrobnosti/zgodovina v stranskem panelu. Samodejne analize ostanejo izrecno vključljive z obsegom, omejitvijo porabe in dokaznim stanjem. Opcije so jasno načrtovane; Teze/Uspešnost ostanejo običajna delujoča cilja.

**Odvisnosti:** UX-A04/A12/A17 in ponovno usklajen načrt procesov. Kompaktni namizni gumbi 32–36 px so skladni s trenutno smerjo ADR; na dotiku ohraniti najmanj 48 px. Besedilnih virov ne spremeniti v nepotrebno velike samostojne gumbe; pravo dotikalno območje preveriti v kontekstu. Ohraniti vidni fokus, semantiko zavihkov in reduced motion.

**Prevzem:** pri 390 × 844 ima uporabnik naslov, ključni filter in več kot en kratek zapis brez velikih praznin; izbor odpre vidne podrobnosti. Status, Watchlista in Analize so dosegljivi brez tipkanja. Tipkovnica, Android Back in 200 % povečava ohranijo celotno pot. »Konfigurirano« ne trdi »uvoz je uspel«.

### UX-A14 · Predlogi `/proposals` in sestavljalnik · P1/P2 · K in L-06

**Dokaz:** živi seznam podobnih AMD/NVDA neuspelih kartic je obsežen; surov poškodovan JSON in ponudniške napake preglasijo pomen predloga. To samo po sebi ne dokazuje podvojenega ID-ja. `ProposalComposer` uporablja prost vnos simbolov in ekstrakcijo `$...` iz vira, brez stabilne potrditve kotacije. Odprtje lahko ponastavi besedilo; različne nastavitve ostanejo v stanju. Iz Radarja dobi povzetek brez polne povezave na izvorni dogodek.

**Predlagano vedenje:** seznam postane kompaktna tabela z instrumentom, kratko hipotezo, časom, stanjem hitrega/globokega dela in enim glavnim naslednjim dejanjem. Polni izhod je v podrobnostih. Povezani poskusi so zložljiva zgodovina, združena po dejanskem izvornem predlogu, nikoli samo po simbolu. Filtri »V delu / Potrebuje ukrep / Zaključeno / Vse« in iskanje, brez samodejnega skrivanja neuspehov. Ločiti neuspešno preverjanje od neuspele analize. Retry ustvari sledljiv poskus z istim izvorom, prejšnjega ne izbriše; že tekočega ne zažene ponovno. Sestavljalnik ima potrjene žetone kotacij, ohranjen osnutek, izrecno zavrženje, viden cilj shranitve in porabo/omejitev globine. Predlog iz dogodka ohrani ID ter dokazne povezave.

**Odvisnosti:** UX-A10/A11/A12/A17, pogodba rezultatov in poskusov iz posodobljenega funkcijskega načrta; aktualni BACKLOG ima porabo/poskuse že deloma načrtovane. Več simbolov mora imeti izrecno semantiko enega predloga ali ločenih analiz; ne predpostaviti enega rezultata za vse. Brez dodatnega LLM klica samo za oblikovanje.

**Prevzem:** 30 neuspešnih predlogov ostane preglednih; vsebina stare napake se odpre na zahtevo; povezani poskusi so dokazljivo povezani. Ponovno odprtje ohrani osnutek, 422 označi pravo polje brez izgube vnosa, dvoumen simbol zahteva izbiro kotacije. Stanje in rezultat vsakega dela ostaneta razumljiva, povezava do vira deluje.

### UX-A15 · Teze `/theses` in podrobnosti · P2 · K, prisotnost potrjena L-09

**Že obstaja:** osnutki/revizije, urejanje in potrditev, zgodovina dokazov, tedenski pregledi, predlogi sprememb in varovala sočasnega urejanja. `expected_version`/`edit_count`, eksplicitna potrditev, dokazi ter status zadostnosti presoje so dobre osnove in ostanejo.

**Dokaz:** `ThesisList` kaže kartice s petimi števci stanj, tudi ničelnimi; lokalni filter po simbolu sproži poizvedbe med tipkanjem, paginacija nima skupnega obsega. `ThesisDetail` naloži vse strani pregledov/predlogov in pokaže obsežno zgodovino revizij, pregledov in trditev. Tehnični modeli/ID-ji in obrazci zapolnijo glavni tok. Za pregled vseh tez z odprtimi predlogi manjka skupen seznam.

**Predlagano vedenje:** privzeta kompaktna tabela: instrument, aktivna različica, stanje trditev, odprte spremembe, zadnji pregled in naslednji smiseln korak. Filtri »Potrebuje pregled«, »V portfelju«, status in simbol v URL; ničelnih značk ne ponavljati. Detail ima aktivno tezo na vrhu, nato odprte predloge sprememb; zgodovina/revizije/tehnični podatki so zloženi in postopno naloženi. Trditve imajo jasno vidno stanje, dokaz, pogoj razveljavitve in veljavnost; urejanje se odpre za izbrano trditev. Pred potrditvijo kratek dejanski diff. Zavrnitev zahteva razlog šele v odprtem dejanju. Ne združevati več odločitev v nepregleden množični »potrdi vse«.

**Odvisnosti:** API povzetek odprtih predlogov/zadnjih pregledov po tezi, strežniški filtri ter strani zgodovine. Ločiti naložen seznam od globalnega števila. Ponovno uporabiti že dobre vzorce napak in dokazov v Tezah za druge module.

**Prevzem:** teza s 100 pregledi se odpre s preglednim aktivnim stanjem in ne naloži vse zgodovine; uporabnik najde vse čakajoče predloge prek seznama. Podrobnosti stare revizije ostanejo dosegljive. Sočasna sprememba sproži vidni konflikt; nezadostni dokaz ne dobi potrditve. Potrditev/revizija ohranita obstoječa varovala in sled.

### UX-A16 · Uspešnost `/track-record` · P2 · K, prisotnost potrjena L-09

**Že obstaja:** horizonti 1/5/20/60 dni, velikost vzorca, opozorilo nizkega vzorca, lastni/sistemski signali, skupine, kalibracija in ročno potrjevanje predloga uteži. Ne uvajamo nove metodologije ali merila donosa.

**Dokaz:** horizont je lokalno stanje, skupine so fiksna tabela brez poti do izidov. API vrne agregate, ne podrobnih sestavnih izidov. `WeightProposal` ob napaki/nalaganju kalibracije nima polne ločitve od dejanskih privzetih uteži; operativni predlog je blizu osnovnega poročila. Izbrani horizont poročila lahko uporabnik napačno razume kot osnovo predloga kalibracije.

**Predlagano vedenje:** trajni URL za horizont in izrecen obseg »izmerjeni / še nezreli / izključeni« z razlago že obstoječih pravil. Skupina odpre pripadajoče izide, njihove datume, vir in izračun; nizek vzorec ostane viden. Operativno kalibracijo prestaviti v jasno ločen zložljiv razdelek ali zavihek z dejanskimi aktivnimi utežmi, časom, podlago predloga in razliko. Izpad kalibracije nikoli ne pomeni »privzete uteži«. Ročna potrditev/zavrnitev ostane izrecna.

**Odvisnosti:** API drilldown izidov z enako metodologijo kot agregati, pogodba populacije/izključitev in kalibracijskega nabora. V datumskem filtru ni dovolj spremeniti prikaza; najprej definirati, ali se filtrira čas nastanka ali datum izida. Ne oglaševati agregata kot prihodnje uspešnosti.

**Prevzem:** vsota izidov izbrane skupine reproducira prikazano n in merilo; manjkajoči izidi imajo pojasnilo. 1/5/20/60 so obnovljivi v URL; izpad kalibracije je napaka, ne privzeto stanje. Potrditev jasno kaže, katere uteži in katera osnova se spreminjajo, ne glede na trenutno izbran horizont poročila.

### UX-A17 · Skupna kompaktna tabela in nastavljivi stolpci · P2, osrednja uporabnikova zahteva · K/L

**Problem:** iste vrste podatkov so razporejene med visoke kartice, velike orodne vrstice in fiksne tabele. Radar prikazuje dolge povzetke, Watchlista skriva zadnjo ceno v nevidnem besedilu, Analize imajo bogate a nespremenljive stolpce. S tem uporabnik vidi premalo primerljivih informacij in preveč ponovljenih gumbov.

**Predlagano vedenje:** en vizualni sistem seznama, uporabljen postopno. Orodna vrstica ima iskanje in aktivne filtre levo, »Stolpci«, »Gostota« in ponastavitev desno. Namizna privzeta vrstica približno 40 px, kompaktna 32–36 px pri enovrstičnih podatkih; večvrstične vsebine niso prisilno odrezane brez razkritja. Primarna dejanja 32–36 px, redka dejanja v jasnem meniju; dotikalna površina ostane 48 px. Naslov/povzetek največ dve vrstici v seznamu, celota v podrobnostih. Lepljiva glava in identiteta instrumenta, številke poravnane desno, vidna valuta, smiselna decimalna natančnost, brez ponavljanja praznih značk.

Nastavitve so **po tabeli**: vidnost, vrstni red in širina stolpcev, gostota, smiselno pripenjanje identitete. Najprej lokalno v brskalniku z različico sheme; ne zahtevati uporabniške baze samo za to. Filtri, razvrščanje, stran in izbrani predmet so v URL, zato jih je mogoče deliti. Videz ne sme spreminjati pomena meril. Nepodprt shranjen stolpec se varno izpusti; »Ponastavi pogled« je vedno dosegljiv. Ne dovoliti, da skrit stolpec odstrani nujno opozorilo o govorici, neuspehu ali delnih podatkih: ta ostane ob identiteti oziroma v vrstici. Premik stolpcev je izvedljiv tudi z gumbi/tipkovnico, ne samo z vlečenjem.

| Zaslon | Predlagani privzeti stolpci | Izbirni stolpci / podrobnosti |
|---|---|---|
| Watchlista | instrument, cena + valuta, dnevna sprememba, od dodaje, oznake, pregledano | P/E TTM, forward P/E, dividendni donos/znesek z osnovo, datum dodaje, zadnja analiza, cilj, opomba, vir/čas; samo če pogodba/vir obstajata |
| Portfelj | instrument/račun, količina, cena, vrednost, utež, P/L, čas posnetka | povprečna nabavna, dnevna sprememba s časom, analiza/teza, vir, nepopolnost FX |
| Analize | instrument, status, datum, ocena, kratki/srednji/dolgi horizont | dokazi za/proti, prepričanost, globina/model, poraba, v portfelju, hipoteza |
| Radar | datum/ura, instrument, naslov, vrsta, dokazni status, pomembnost | vir, pozornost, reakcija cene, novost, materialnost; celotni povzetek šele v detailu |
| Signali | instrument, vrsta/smer, stanje, moč, nastanek/potek, kratka razlaga | izvor, zaupanje, cenovne ravni z valuto, povezani dokazi |
| Vstopi | instrument, cena/valuta, cona in oddaljenost, vzrok, stanje teze | vrednotenje, pravila, padec, čas; zemljevid je preklopljiv in pri eni točki majhen |
| Predlogi | instrument, kratka hipoteza, čas, hitri/globoki status, naslednji korak | globina, izvor, zadnji poskus, rezultat, poraba |
| Teze | instrument, aktivna različica, stanje, odprte spremembe, zadnji pregled | lastna oznaka, portfelj/watchlista, zgodovina in iztek trditev |
| Uspešnost | skupina/izvor, n, zadetki, donos, alfa | nizki vzorci, izključeni; izidi prek drilldowna |
| Procesi | proces, vključen, urnik/pas, zadnji/naslednji tek, stanje | trajanje, obseg, poraba, zgodovina in napaka |

Mobilno ne prekopirati vseh namiznih stolpcev v široko tabelo brez izbire: kratek pregled s 3–5 ključnimi polji in razkritjem ter izbirni vodoravni tabelarni pogled z vidnim simbolom. Primarne informacije morajo biti dostopne brez vodoravnega pomikanja. Visoke kartice ostanejo za odločitev ali razlago, ne kot obvezen ovoj vsakega podatkovnega zapisa.

**Odvisnosti:** tipizirane definicije stolpcev ob posamezni domeni in majhen skupen gradnik, ne nov splošen UI okvir. Vzpostaviti najprej na Watchlisti in Analizah; prilagoditve Radarju/Tezam upoštevajo njun pomen. Filtri/razvrščanje morajo delovati na celotnem API naboru pred paginacijo; stabilen ID razreši izenačene vrednosti. Virtualizacija šele po meritvi dolgih naborov.

**Prevzem:** pri 1440 × 900 je predlagani cilj vsaj 12 enovrstičnih zapisov v podatkovnem delu strani brez izgube stanj; cilj potrditi na prototipu z dejanskimi besedili. Sprememba stolpcev preživi osvežitev, ne vpliva na drugo tabelo in se ponastavi. Prehod SL/EN ne pokvari širine ali pomena. Tipkovnica upravlja sortiranje/stolpce/dejanja, bralnik dobi naslove in status. Pri 390 × 844 kontrolniki ne preglasijo podatkov; dotikalni cilji ostanejo 48 px. Začasna napaka, 0, null in delni podatek se jasno razlikujejo.
## Skupni oblikovni vzorci

1. **Povzetek, dokaz, dejanje.** Glava vsakega objekta pove, kaj je, za kateri instrument/čas velja in ali je rezultat popoln. Razlaga sledi pred sekundarno debato. Najpomembnejše dejanje je eno; ostala so jasno sekundarna.
2. **Povezava ima eno identiteto.** URL odpre zahtevan objekt neodvisno od filtra seznama. Ni tihih zamenjav s prvo vrstico. Vrnitev ohrani filtre in položaj. Najprej signal/dogodek/instrument, pozneje razširitev na vse tipe.
3. **Cena potrebuje valuto in tržni datum.** Datum pridobitve in datum opazovanja sta ločena. Dokazi modela imajo svojo starost. Vzorčni in dejanski podatki se ne nadomeščajo samodejno.
4. **Stanje storitve ni stanje naloge.** Zelen TCP/konfiguracijski indikator ne potrjuje trenutne svežine, končane analize ali uspešnega Flex uvoza.
5. **Seznam in podrobnosti delujeta na obeh velikostih.** Namizni dvojni stolpec; mobilno izrecen prikaz podrobnosti z vrnitvijo, ohranjeno vrstico in vidnim naslovom. Tabela se vodoravno pomika le znotraj okvirja in ohrani kontekst simbola.
6. **Vsota pokaže pokritost.** Manjkajoči FX, cene ali čas niso tiho izključeni iz »celote«. Barve nikoli ne ustvarijo lažnega ničelnega podatka.
7. **Razveljavi pomeni obnovi.** Obnovi prejšnji objekt in zgodovinsko osnovo, ne novega približka. Ob sočasni novejši spremembi je konflikt viden.
8. **Kompaktnost je izbira prikaza.** Širina/gostota/stolpci so shranljivi, vendar ne spreminjajo pomena podatkov. Mobilna ciljna površina ostane uporabna.

## Predlagani vrstni red izvedbe

To je predlog večje UX/UI nadgradnje, ne odobritev izvedbe. Najprej enoten načrt z dokaznimi pogodbami in prototipom gostote, nato majhni preverljivi sklopi. Ohraniti trenutno znamko in smiselne komponente; osnovnega agentskega toka, matematičnih meril ali varoval naročil ne prenavljati zaradi videza.

| Faza | Obseg in predviden rezultat | Odvisnost / pogoj za zaključek |
|---|---|---|
| F0 · uskladitev osnove in prikaza | Potrditi aktualni SHA/built storitev, preveriti že izvedene BL naloge, preslikati stare zahteve po funkciji. Prototip Watchliste, Analiz in mobilnega Radarja z dejanskimi kratkimi/dolgimi ter praznimi/napakami. Določiti pomen statusov in časov | Brez implementacije na zastareli glavni mapi; novo BL oštevilčenje šele po branju aktualnega BACKLOG. Dosegljiv demo s fiksnimi neosebnimi podatki |
| F1 · temelji in prvi gosti tabeli | UX-A12/A17 na Watchlisti in Analizah; URL stanje, shranjeni stolpci, gostota, pravilne napake/praznine. Hkrati P1 popravki lažnih podatkov/valut, obnovitve in globokih povezav iz A01/A04/A09/A10 | Enoten vzorec pokaže resnične podatke, napako, delnost in vir. Brez napačnega objekta, USD kot ugibanja ali izgube osnove Watchliste |
| F2 · iskanje in dnevni pregled | Radar, Signali, Vstopi in Predlogi: kompaktni seznami, vrstni red/filtri/strani, mobilni detail, kratke napake in zgodovina poskusov. Zemljevid Vstopov kot dodatni pogled. Pregled z resnično pozornostjo in brez samodejnih vzorcev | A02/A03/A05/A06/A14, strežniški filtri pred omejitvijo, preverjen pomen potrditve. Pot obvestilo → dokaz → označba → nazaj deluje |
| F3 · portfelj in dokaz odločitev | A07/A08/A10/A11: popolnost po računih/FX, uvoz/sinhronizacija, instrumentna identiteta, časovna razmejitev analize. A15/A16: odprte spremembe tez ter drilldown izidov obstoječe Uspešnosti | Vsote in agregati imajo dokazljivo pokritost; aktivne teze in obstoječe horizonte ohraniti. Vsi sestavni podatki so dosegljivi brez brskanja skozi celotno zgodovino |
| F4 · nastavitve in zahtevane nove vsebine | A13: Povezave/Procesi, urniki in politike ročnih/samodejnih analiz. Ponovno vključiti uporabnikove zahteve po dividendni evidenci in dodatnih Watchlist metrikah iz starega osnutka | Določiti API/source/as_of vsake nove metrike; obstoječi XML uvoz ponovno uporabiti. Dividendni cashflow in pričakovani donos sta različni metriki. Ne pospeševati Opcij M6 ali trgovanja M7 |
| F5 · skupen prevzem | Celotna namizna/mobilna pot, stanja API, SL/EN, temi, tipkovnica/Back, 200 % povečava, shranjeni pogledi, dolgi seznami | Izpolnjeni spodnji scenariji in prevzemi A01–A17; brez sprožanja pravih naročil ali plačljivih analiz samo za UI demonstracijo |

Faze niso en sam velik PR. Paket naj se zaključi po uporabniški poti in vključuje potrebno pogodbo API, dostopnost in dokaz rezultata. Zaupanje/povezave in kompaktne tabele morajo napredovati skupaj; celotna semantična prenova ne sme odložiti uporabnikove glavne zahteve po uporabni gostoti do zadnje faze. Pred vsako izvedbo ponovno preveriti HEAD in lastništvo sprememb zaradi aktivnega drugega agenta.

## Največje še odprte odločitve

| Odločitev | Predlog pregledovalca | Zakaj spremeni izvedbo |
|---|---|---|
| Kaj je prva naloga ob odprtju? | Pregled »kaj zahteva mojo pozornost« iz resničnih podatkov | Določa kartice in privzete filtre brez novih tržnih metrik |
| Privzeta gostota in namizni stolpci | Kompaktna informativna tabela; 2–3 prednastavitve po domeni, nato individualna izbira | Določa prototip in skupne gradnike; ne en univerzalen nabor za vse strani |
| Kje hraniti pogled? | URL za izbor/filtre/razvrščanje, lokalni različeni zapis za stolpce/gostoto; račun šele ob potrebi po več napravah | Omeji obseg prve izvedbe in zagotovi deljive povezave |
| Kaj pomeni »Sprejmi signal«? | Evidenca izbrane raziskovalne ideje, brez naročila | Določa besedila, arhiv in metodologijo izidov |
| Identiteta instrumenta | Kotacija z internim ID, borzo in valuto; simbol je oznaka | Vpliva na iskanje, Watchlisto, analize in večračunski portfelj |
| Delna vsota portfelja | Ločen znani del + izključene postavke | Določa API, prikaz in interpretacijo; ne navidezno poln NAV |
| Kaj jamči »Potrjeno«? | Konkretni uradni vir, naveden ob oznaki | Potrebna dokazna pogodba, ne samo nova barva |
| Mobilni detail | Enoten viden panel oziroma ločena pot z vrnitvijo na isti seznam | Odpravi potrjeno izgubo podrobnosti pod 20.000 px seznama |
| Obnovitev Watchliste | Obnovitev istega zapisa in osnove | Vpliva na migracijo in zgodovinske donose |
| Zadnja analiza v seznamu | Privzet zadnji zaključeni rezultat, tekoči/neuspeli vidni ločeno; preklop na celotno zgodovino | Potrebna definicija statusa in strežniško grupiranje, ne lokalno skrivanje |
| Obseg Uspešnosti in kalibracije | Vidna populacija in datumi; osnovo predloga uteži navesti ločeno od izbranega horizonta poročila | Prepreči napačno interpretacijo že obstoječih agregatov |
| Demo v običajni aplikaciji | Samo izrecen način ali /ux, nikoli samodejno ob praznem API | Zahteva poštena prazna stanja; ločen demo mora biti dejansko dosegljiv |

To so priporočeni privzeti odgovori za pripravo prototipa in izvedbenega načrta, ne dokaz odobrene implementacije. Nerešena vprašanja naj se prikažejo na konkretnem prototipu; uporabniku ni treba vnaprej odločati o notranjih tehničnih podrobnostih.
## Ciljni scenariji za živi prevzem

1. **Obvestilo → dokaz → odločitev:** neposreden Telegram signal, instrument, izvorni dogodek, vrnitev, označitev in razveljavitev. Brez nove analize ali naročila.
2. **Izpad podatkov:** API napaka, počasna zahteva in zastarel uspešni posnetek na Pregledu/Instrumentu/Watchlisti. Preveriti izključno v izoliranem testnem okolju.
3. **Portfelj z robnimi podatki:** frakcije, dva računa, isti simbol, gotovina, neznan FX. Fiksni očiščeni nabor, brez prave sinhronizacije za potrebe UX preizkusa.
4. **Dolg seznam na telefonu:** izbor zadnjega dogodka/kandidata, vidne podrobnosti, vrnitev na isti položaj, dosegljiva razveljavitev in stanje sistema.
5. **Analiza:** že obstoječ zaključen in neuspešen zagon; za SSE uporabiti testni tok z odklopom. Brez plačljivega zagona samo za demonstracijo.
6. **Prilagodljiv pogled:** spremeniti stolpce/gostoto Watchliste in Analiz, osvežiti, deliti filtriran URL, ponastaviti samo en pogled, nato odpreti na telefonu. Obvezna opozorila ostanejo vidna.
7. **Teze in Uspešnost:** obstoječa teza z dolgo zgodovino, odprtim predlogom in konfliktom; agregat z nizkim vzorcem ter njegovi izidi; napaka kalibracije. Mutacije le na fiksnem testnem naboru.
8. **Dostopnost:** tipkovnica, povečava 200 %, SL/EN, svetla/temna tema in reduced motion; testirati dejansko nalogo, ne zgolj odsotnost horizontalnega prelivanja.

Obstoječi testi so koristna osnova, vendar `e2e/shell.spec.ts` npr. preskoči nekaj glavnih mobilnih poti, test z naslovom »manual proposal with undo« pa razveljavitve dejansko ne preverja. Novi testi morajo preverjati zgornje posledice za uporabnika in podatkovne pogodbe, ne samo prisotnosti gumba ali grafa.




## Predaja in omejitve zaključka

Končni neodvisni pregled vsebuje UX-A01–UX-A17, trenutno/predlagano vedenje, prioritete, odvisnosti in prevzeme. Vključena so posredovana živa opažanja L-01–L-11; izvor dokazov je ločen od lastnega branja kode. Glavni izvedbeni dokument je [Celovita UX/UI nadgradnja](../superpowers/plans/2026-10-28-celovita-uxui-nadgradnja.md). Pri njegovem pregledu so bile vodilnemu agentu posredovane konkretne dopolnitve glede vrstnega reda identitete, URL razvrščanja, višine navpičnih dejanj, semantike »pregledano«, osnove Uspešnosti in obveznih opozoril pri skritih stolpcih.

Ta podagent je spreminjal samo ta raziskovalni dokument. Ni izvajal aplikacijskih testov ali spreminjal kode, sheme, skupnega BACKLOG/SESSIONS, nastavitev, uporabnikovih podatkov ali tujih delovnih dreves. Morebitno kasnejšo izvedbo mora odpreti ločena uporabnikova odobritev ob tedaj aktualni kodi.
