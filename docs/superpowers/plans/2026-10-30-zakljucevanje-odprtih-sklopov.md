# Enotni načrt zaključevanja odprtih sklopov Preže

> **For agentic workers:** Pri kasnejši izvedbi uporabi superpowers:subagent-driven-development ali superpowers:executing-plans. Najprej pripravi in preveri SPEC posameznega sklopa. Ta načrt sam ne dovoljuje produktne izvedbe, zunanjega pošiljanja ali prenosa na :3000.

**Goal:** Popisati vse še odprte in delno zaključene naloge, odpraviti nejasne statuse ter določiti pot raziskava → SPEC → izvedba → dokaz → uporabniški prevzem.

**Architecture:** Ohranimo obstoječi FastAPI/SQLAlchemy/arq in Next.js. Podatkovne pogodbe, procesne politike, metapodatki in revizijske varovalke iz ADR-0017–0022 ostanejo osnova. Novih storitev, ponudnikov, tabel ali priklopov ne uvajamo zgolj zato, da zapolnimo prazne kartice.

**Tech Stack:** Python 3.12, Pydantic v2, PostgreSQL/Timescale, Alembic, arq/Redis, LiteLLM vloge; Next.js/TypeScript, next-intl, Vitest/Playwright, Docker Compose.

**Spec:** Obstoječi [celoviti SPEC](../specs/2026-10-28-celovita-uxui-spec.md) in ADR-0017–0022. [Priprava naslednjih SPEC](../specs/2026-10-30-odprti-sklopi-priprava-spec.md) določa manjkajoče pogodbe; dokument še ni končni odobreni izvedbeni SPEC.

**Osnova:** veja `feat/uxui-demo-upgrade`, produktni commit `bd33131`, S-018. Inventura spodaj je dokumentarni posnetek BACKLOG, ne nova potrditev živih povezav ali ponudniških pravic.

## 1. Kaj je zaključeno in česa ne ponavljamo

Izvedeni so standardni pogledi, osnovni izbirni stolpci/barve/trendi, osnovne politike procesov, glavno stikalo avtomatskih modelov, SMTP nastavitve in transport s ponarejenimi testi, sintetične teze, osnovna študija shranjenih signalov/mnenj ter dividendna evidenca na strogo podprti sintetični pogodbi. BL-195–201 in BL-206–210 se ne odpirajo znova kot povsem nova izvedba.

To še ne potrjuje živih vhodnih podatkov, popolnosti vseh kazalnikov, dejanske SMTP dostave, celotnega backtesterja, vseh dostopnostnih kombinacij ali namestitve na :3000. Pri delni nalogi zapremo samo dokazani del in ohranimo preostalo delo.

## 2. Skupne omejitve

- :3100 ostane ločen sintetični demo; :3000 in Claudova veja ostaneta nespremenjena do nove izrecne potrditve. Gradnja slike, uspešen test ali pripravljena migracija niso dovoljenje za prenos.
- Broker ostane read-only. M7 zahteva ločeno odobritev; noben signal, backtest ali potrditev teze ne odda naročila.
- Denar Decimal/numeric in decimalni nizi na novih mejah. Neznano ni nič, neznana valuta ni USD. Vsako dejstvo ima vir, čas, osnovo in stanje pokritosti.
- LLM samo interpretira prek obstoječih vlog. Nova raziskovanja ne smejo samodejno vklopiti plačljivega ponudnika, naročnine, prejemnika ali zgodovinskega ponavljanja agentov.
- Skrivnosti in zasebni Flex/XML ostanejo zunaj repoja, posnetkov zaslona, dnevnikov in promptov. Vzorci za testske pogodbe so očiščeni in izrecno označeni.
- Uporabniški filtri/izbor/sort ostanejo v URL; predstavitvene preference so verzionirane. SL/EN, teme, 48px dotik in ohranitev fokusa veljajo za vsak spremenjen pogled.
- Testi z bazo uporabljajo ločene baze. Živi SMTP/Telegram/LLM preizkusi imajo vnaprej določen obseg in ločeno dovoljenje za dejansko pošiljanje ali porabo.

## 3. Prednost in odvisnosti

| Val | Namen | Paketi | Izhodni pogoj |
|---|---|---|---|
| V0 | Uskladitev dejanskega stanja in SPEC | A | Za vsako odprto nalogo dokaz, lastnik, paket in merilo zaključka; brez slepih statusov done |
| V1 | Zanesljiv uvoz in identiteta | B, C | Neveljaven/nepopoln uvoz ne izbriše ali napačno ovrednoti portfelja; kotacije nedvoumne |
| V2 | Dejanski podatki in predvidljivi procesi | D, E | Metrike/makro/ETF imajo potrjene pogodbe; omejitve in poraba vidne, ali je vrzel izrecno sprejeta |
| V3 | Povezave, uporabnost in zaščita stanja | F, G | Povezave preizkušene v dogovorjenem obsegu, brez dvojnih oddaj; ciljna UX matrika preverjena |
| V4 | Priprava prevzema | H | Zelen dokazni paket, preizkušen restore, usklajene veje, uporabniški pregled; prenos še zadržan |
| V5 | Nadaljnja analitika in novi viri | I, J | Lastni SPEC ter ločeni podatkovni/licenčni/stroškovni pogoji; ne blokirata osnovne izdaje |
| V6 | Opcije in morebitna naročila | K | Ločena M6/M7 mejnika in odobritve; nikoli skrito vključena v UX objavo |

B in C se uskladita glede instrumentne identitete; D temelji na njuni potrjeni pogodbi. E in G sta lahko pripravljena vzporedno v neprekrivajočih se datotekah. F potrebuje E za urnike/pravila dostave. H zahteva zaključene obvezne popravke B/C/G in izrecen seznam sprejetih preostalih vrzeli D/E/F. Celotni opcijski modul, družbena omrežja in poln backtester niso pogoj za osnovno izdajo.

## 4. Paketi za izvedbo po SPEC

### A. Ponovna inventura in priprava specifikacij

**Naloge:** BL-213 (ta dokument), BL-214; pregled vseh ID-jev v §9. **Datoteke:** BACKLOG.md, SESSIONS.md, PLAN.md, obstoječi načrti/SPEC/ADR, dokumenti dejanskega prevzema.

- [ ] A1: Primerjaj aktualni HEAD, delovno drevo, izvorno Claudovo vejo in uporabljene migracije samo za branje. Razliko vnesi kot datiran dokaz; ne združuj vej.
- [ ] A2: Vsak status doing/next/later razvrsti kot manjkajoče, delno, izvedeno-brez-živega-dokaza, zastarel opis ali namerno odloženo. Število devetih unknown instrumentov in zgodovinske ocene žetonov ponovno izmeri, ne prepiši kot današnje stanje.
- [ ] A3: Posebej preveri BL-011/013 (prejšnji živi MiniMax dokazi), BL-027 (ETF profili), BL-052 (nov Pregled), BL-058 (lokalni urniki), BL-172 (vidnost usage) in BL-174 (prekrivanje z BL-193/194). Poveži nadomestne dokaze, brez podvajanja implementacije.
- [ ] A4: Pripravi SPEC dokumente iz spremljevalne priprave; odprta dejstva vira naj dobijo preizkus, predpostavka pa jasno oznako predloga. Nato razbij paket na majhne naloge z natančnimi vmesniki in testi.

**Končano:** vsak odprt ID ima paket in preizkusljiv izhod; vsak izvedbeni korak ima veljaven SPEC. Nova arhitekturna odločitev dobi naslednji prost ADR šele ob dejanski odločitvi.

### B. Flex, gotovina in dividende

**Naloge:** BL-202, BL-205; ohranitev BL-022/187/198/209. **Koda:** `services/api/preza/broker/{flex,dividends}.py`, `services/{portfolio,dividends,dividend_controls}.py`, `domain/{portfolio,dividends}.py`, `models_dividends.py`, migracije in `apps/web/components/portfolio/PortfolioDividends.tsx`.

- [ ] B1: Zasebno pridobi minimalen očiščen vzorec dejanskih sekcij Cash Transactions, Open/Change Dividend Accruals, pozicij in instrumentnih identifikatorjev. V SPEC zapiši konkretna polja, različice in meje dokazov.
- [ ] B2: Najprej regresije za BASE_SUMMARY-only, odsotno valuto, lot-only, manjkajočo/poškodovano sekcijo, več računov/datumov, izrecno prazno popolno sekcijo in zavrnitev celotne transakcije. Dokaz: ne izgubi se prejšnji veljavni posnetek in ni privzete napačne valute.
- [ ] B3: Potrdi poslovne identitete dividend: ponovitev, isti ID/druga vsebina, storno, delno plačilo, več davkov, nepovezan odtegljaj, isti simbol na različnih kotacijah, prodan instrument, prazni novi obračuni. Pravila primerjave ne smejo napačno potrditi izplačila na podlagi samega datuma/simbola.
- [ ] B4: Določi podprto vsebino FinancialInstrumentInformation, podatkovno migracijo in zgodovino popravkov. Datum poročila, generiranja in pridobitve ostanejo ločeni.
- [ ] B5: Projekcija po uvozu dobi obdobje, potrjeno DPS osnovo, datum/količino pozicije, svežino in pojasnilo negotovosti. Brez DPS/koledarja ni izmišljene mesečne dividende. Nov uvoz primerja pričakovano s potrjenim; odsotna knjižba sama ni preklic ali ničla.

**Končano:** pogodba potrjena na očiščenem dejanskem vzorcu, idempotenca/rollback/regresije zelene, UI razloči potrjeno/ocenjeno/neznano. Nepodprta oblika ima razloženo vrzel. Davčno svetovanje in avtomatsko ugibanje popravkov nista rezultat tega sklopa.

### C. Kotacija in identiteta

**Naloge:** BL-194, relevantni del BL-174. **Koda:** `services/identity.py`, `services/instruments.py`, `routes/instruments.py`, `domain/market.py`, `components/instrument/InstrumentFacts.tsx`.

- [ ] C1: Za vsako dejansko nerešeno kotacijo preveri instrument_id/conid/ISIN/borzo/valuto/vrsto in primernost vira. Valuta poročanja družbe ni trgovalna valuta; isti ISIN ne pomeni iste kotacije.
- [ ] C2: SPEC naj odloči, ali zadostuje preverjen brokerjev vir ali potrebujemo ročni popravek z dokazom. Ročni popravek zahteva predogled spremembe, revizijo in sled, ne tihega prepisa zgodovine.
- [ ] C3: Regresije za dvojni simbol, napačen profil, konflikt različice, neznano vrsto/valuto in spremembo povezave ob obstoječih pozicijah/analizah.

**Končano:** vsaka ciljna kotacija je potrjena ali izrecno nerešena z razlogom; pri dvoumnosti ni obogatitve napačnega instrumenta. Osnovni pogledi ostanejo dostopni tudi z nerešeno identiteto.

### D. Fundamentali, ETF in makro podatki

**Naloge:** BL-193, BL-027, BL-211 in del BL-052/174; poznejši BL-067/094 gresta v I. **Koda:** `fundamentals/finnhub.py`, `services/{fundamentals,market_context}.py`, `routes/overview.py`, `services/agents/preza_agents/etf_analyst/{profile,exposure}.py`, `universe/ucits_etfs.yaml`, `components/overview/LiveOverview.tsx`.

- [ ] D1: Omejena ciljna populacija portfelj/watchlista, zadnji uspešni tek in izid na instrument. Pred množičnim refreshom ugotovi razlog nizke pokritosti in dostopne kvote; neuspeh ni dokaz plačljivosti.
- [ ] D2: Za P/E TTM, forward P/E, EV/EBIT, FCF donos, dividendni donos, DPS in payout navedi vir/polje/enoto/obdobje/osnovo/stalen identifikator. Med indicirano in TTM osnovo ni tihega prehoda. Če polja ni, je izhod potrjena vrzel ali predlog novega vira z njegovo ceno/pravicami.
- [ ] D3: ETF: TER/holdingi/sektorji/države/distribucijski razred ter look-through pokritost imajo datum in vir; prekrivanja ne štejejo istega holdinga dvakrat. Zastarele/različno datirane uteži ostanejo označene.
- [ ] D4: SPY/SMA200, VIX, US10Y in DXY: potrdi identiteto serije, tržno območje, enote, koledar, zamik, minimalno zgodovino, pravice in svežino. Definicija režima se ne uvede brez determinističnih pragov v SPEC.
- [ ] D5: Pogodbeni testi posnetkov in en omejen živi preizkus dogovorjenega vira; read GET ne kliče ponudnika. Vzorec demo ni dokaz žive pokritosti.

**Končano:** objavljena matrika dejanske pokritosti in provenience; ni napačnih zamenjav kazalnikov. Tržne kartice prikazujejo potrjeno vrednost ali jasno sprejeto manjkajočo povezavo.

### E. Procesi, poraba, modeli in časovne omejitve

**Naloge:** BL-011/012/013, BL-169/170/172/176/180/181, lokalni čas BL-058. **Koda:** `preza/llm/client.py`, `llm/automatic.py`, `radar/pipeline.py`, `entries/dip.py`, `automation_worker.py`, `services/automation.py`; `preza_agents/budget.py`, `preza_agents/worker.py` in `stock_analyst/analyst.py`; UI Analize/Nastavitve.

- [ ] E1: Ponovno preveri dejanske LiteLLM vloge, konfiguracijo/fallback in pravice, brez vnosa skrivnosti v SPEC. Benchmark lokalnega modela: pretok/latenca/napake, vrsta, število sočasnih klicev in preverjen proračun; naziv modela iz starega backlog ni trenutna konfiguracija.
- [ ] E2: Cache triaže po vsebini in verziji pravil/modela/jezika; nov član ne razveljavi nepovezanega vsega. Spremenjen povzetek razveljavi svoj prevod. Regresije cache-hit/miss, spremenjen dokaz in govorica → uradni vir.
- [ ] E3: Vhodi Vstopov, skupni timeout z vsemi popravnimi poskusi in prekinitve. Določi absolutni rok, ne le HTTP timeouta. Izklop avtomatike ustavi naslednje klice, ročni zagon ostane ločen; ob izpadu/restartu ni dvojnega plačljivega poskusa.
- [ ] E4: Usage loči logični korak, dejanske poskuse, vhod/izhod, model/vlogo, ceno če je potrjena in neznano ceno. UI ne sme seštevka dveh poskusov razglasiti za posamezen predolg vhod.
- [ ] E5: Preveri dejansko podporo strukturiranim odgovorom s kontrolnim primerom: sprejet parameter ni dokaz uveljavljene sheme. Ne spreminjaj ponudnika brez zapisanega razloga in odobrenega stroška.
- [ ] E6: Lokalni urniki jutranjega povzetka in druge politike: Europe/Ljubljana, zima/poletje, DST/nočno okno, preview naslednjih zagonov, stop/pause/manual, ključi deduplikacije ter recovery. Brez avtomatskega omogočanja urnikov zaradi migracije.

**Končano:** ponovljivi izidi brez nepotrebnih LLM klicev, vidni proračuni/razlogi blokade in pravilni lokalni zagoni. Izmerjene vrednosti zamenjajo stare ocene v backlogu šele po dokazu.

### F. SMTP, Telegram, dostop in varnostne kopije

**Naloge:** BL-212, BL-057/058, BL-016/017/023. **Koda:** `services/email.py`, `routes/email.py`, `notify/*`, CLI Telegram, `infra/docker-compose.yml`, `.env.example`, obstoječi broker/infra skripti.

- [ ] F1: SMTP: konfiguracija TLS/STARTTLS, več prejemnikov, revizije, omejitve in vrste obvestil; pred dejanskim testnim sporočilom določiti prejemnika/vsebino in pridobiti izrecno dovoljenje. Preveriti dostavo, zavrnitev prejemnika, timeout, pavzo, preklic in negotovo dostavo brez avtomatskega podvajanja.
- [ ] F2: Odločitev SPEC o dnevnem povzetku: kohorta, lokalna ura, jezik, največja količina, izbor prejemnikov/kanalov, filter starih/poteklih zapisov in vedenje ob prvem vklopu. Ne pošiljati nenaročenega zgodovinskega zaostanka.
- [ ] F3: Telegram besedila skozi prevode, pravilni deep linki in obstoječe omejitve uporabnika. Integracijski testi s fake transportom; živi preizkus posebej dovoljen.
- [ ] F4: Potrdi Tailscale/HTTPS/telefon in read-only IB Gateway tam, kjer se uporabljata. UI ne sme izpostaviti poverilnic. Omrežni dostop ali broker profil se ne vključi z dokumentarnim korakom.
- [ ] F5: Načrt rednih kopij, hramba, ločen cilj, dovoljenja in obveščanje o napaki. Dejanski restore na ločeni bazi je obvezni dokaz; enkratni dump ni redno varnostno kopiranje.

**Končano:** vsak izbrani kanal ima dokaz in kontroliran izklop; dostop in restore preverjena. Nepovezan kanal ostane izklopljen, lahko je izrecno izvzet iz prve objave.

### G. Uporabnost, ohranitev stanja in popoln pregled UI

**Naloge:** BL-203/204, BL-005/160 ter preverba BL-052/172. **Koda:** `components/table/*`, `lib/view-state.ts`, `components/proposals/ProposalComposer.tsx`, `routes/proposals.py`, ostali zasloni in SL/EN.

- [ ] G1: Oddaja osnutka ima trajen request ID, ki preživi reload/izgubljeni odgovor. Vsebinski popravek po oddaji je nov zahtevek; isti ključ/druga vsebina je konflikt. Ponovi brez ustvarjanja dodatne analize ali porabe kvote.
- [ ] G2: Poimenovani uporabniški profili, kopiranje/brisanje/reset, verzioniranje in obvezna opozorila. Določi lokalni obseg; večnapravna sinhronizacija ni implicitna zahteva.
- [ ] G3: Primerjava izbranih kotacij s primerljivimi osnovami/valutami/obdobji; neprimerljivo ostane označeno. Enoten iskalnik/filter/sort celotnega nabora pred paginacijo, brez sortiranja samo trenutne strani.
- [ ] G4: Instrument/analiza: paneli delnica proti ETF, snapshot proti trenutnim dejstvom, vir/čas/pomanjkljivosti, poraba, prehodi iz portfelja, Radarja in tez. Najprej inventura manjkajočih zahtev starega SPEC, ne samovoljna nova zasnova.
- [ ] G5: Matrika vseh pomembnih zaslonov: 390×844, 768×1024, 1440×1000; SL/EN; svetla/temna/sistemska; tipkovnica/fokus/Back/Escape; 200% povečava in reduced-motion; loading/empty/error/partial/stale/ready, pending/conflict/undo. Namerno preskočeni testi ne dokazujejo nepreverjene kombinacije.

**Končano:** konkretni uporabniški scenariji, slike in API dokaz za isti predmet; veljavni 48px cilji, brez izgube osnutka ali zakritih dejanj. Status BL-005 lahko zapremo kot nadomeščen z implementiranimi/pregledanimi zasloni, ne z navideznim novim prototipiranjem.

### H. Integracija, prevzem in zadržani prenos

**Naloga:** BL-215; povezave na B–G in BL-160. **Dokazi:** poročilo razlik vej, seznam migracij, matrika zahtev/testov, varnostna kopija/restore, release in rollback zapis.

- [ ] H1: Primerjaj aktualno Claudovo vejo s pregledno vejo; potrdi izbrano osnovo, prekrivajoče spremembe in prostost ID migracij. Ena naloga ima enega lastnika; ne prepisuj aktivnega subagenta.
- [ ] H2: Popolni preverjeni API/agents/web testi, i18n, lint/tipi, generirani OpenAPI/TS, Linux build, migracijski upgrade/downgrade na testni kopiji. Celotne zelene zbirke ali natančno dokumentiran cilj dopolnilnih testov, brez prikrivanja neuspehov.
- [ ] H3: Na :3100 pokaži success/failure/partial/stale/unknown primere; zasebni podatki niso demo. Omejen preizkus z dejanskimi podatki poteka samo v dogovorjenem ločenem okolju; ne ustvari signalov/sporočil zgolj za UI dokaz.
- [ ] H4: Za vsako release zahtevo označi izpolnjeno, sprejeto vrzel ali blokado. Finančno napačen uvoz, dvojna plačljiva oddaja ali nedelujoče varovalo niso sprejemljiva kozmetična vrzel.
- [ ] H5: Pripravi konkreten načrt prenosa: aktivne analize/vrste, fresh backup, zaporedje API/migracije/delavci/web, nespremenjeni volumni/poverilnice, smoke testi in rollback slik/sheme/podatkov. Destruktivna migracija nima samoumevnega downgrade povratka.
- [ ] H6: Uporabniški pregled in nova izrecna potrditev prenosa :3000 sta zadnji korak. Do takrat ni merge/deploy/push zgolj zaradi zaključenega dokumenta.

**Končano:** pripravljena in pregledana izdaja, ločeno od dejansko odobrenega/prenesenega stanja. Če se prenos pozneje izvede, potrebuje svoj zapis dokazov, ne ponovne oznake tega načrta kot dovoljenja.

### I. Napredna analitika, raziskovanje in backtesting

**Naloge:** BL-067/087/094/171 in nov BL-216 (poln backtester). Osnova že izveden BL-210/ADR-0022 se ne nadomešča brez regresij.

- [ ] I1: SPEC polnega backtesterja: point-in-time podatki, delitve/dividende, delistane kotacije, trgovalni koledarji, benchmark/FX, zdrs/provizije/likvidnost/izposoja/davki po izrecnem obsegu, prekrivanje signalov, pozicijska pravila/gotovina in reproducibilen snapshot parametrov/vhodov.
- [ ] I2: Loči študijo dogodkov, portfeljsko simulacijo in prihodnje zgodovinsko ponovno izvajanje agentov. Zadnje potrebuje ločeno stroškovno odobritev in dokaz brez uhajanja prihodnjih podatkov; trenutna privzeta pot ostane brez novih LLM klicev.
- [ ] I3: Sektorski benchmark, sorodna podjetja/odkupi in znanje agentov dobijo vir, čas, dokaz primerljivosti in kontrolo govoric; niso prosto pripete interpretacije.
- [ ] I4: BL-171 najprej preveri dejansko pot delnic. Odstranitev knjižnice/grafa je ločen refaktor z inventuro še uporabljenih ETF/snapshot/regresijskih delov, brez brisanja aktivnih odvisnosti po starem opisu.

**Končano:** ločeno odobren analitski SPEC in ponovljivi matematični/časovni testi; vizualno lep rezultat ni dokaz trgovalne veljavnosti.

### J. Dodatni viri, slike in zgodovinski uvozi

**Naloge:** BL-033/042/182–186; BL-084 ostane namensko odložen. Vsak vir ima lasten priklop in ne vpliva na osnovno izdajo.

- [ ] J1: Pred SPEC preveri sedanji uradni način dostopa, kvoto, pravice, zasebnost in strošek za izbrani vir. Stari opisi omejitev YouTube/Instagram/StockTwits niso današnja preverjena pogodba.
- [ ] J2: Spremljani viri imajo lastnika/aktivnost/urnik, deduplikacijo, zdravstveno stanje, izvorne trditve in dokazno pot. Neuradna vsebina ostane govorica, dokler je ne potrdi primeren uradni vir.
- [ ] J3: Slika/OCR: ekstrakcija je osnutek, uporabnik potrdi simbole/kontekst pred oddajo. Določiti retention, anonimizacijo, napake prepoznave, lokalno ali slikovno LiteLLM vlogo in proračun. Številke s slike niso potrjena dejstva.
- [ ] J4: Neobvezen uvoz iz trading-list: preslikava identitet, suhi pregled, deduplikacija in rollback; ne prepiše obstoječih tez ali pozicij. Claude SDK runner se ne uvaja, dokler uporabnik ne spremeni izrecne odložitve BL-084.

**Končano:** dokumentiran podprt priklop ali razlog odložitve. Dostop do ene testne objave ne potrdi vseh računov/vsebin.

### K. Opcije in naročila kot ločena mejnika

**Naloge:** M6 BL-120–123; M7 BL-140–142. **Pogoji:** ločen SPEC, novo arhitekturno preverjanje in obstoječa pravila AGENTS/ADR-0006.

- [ ] K1: M6: zakasnjene verige, pogodbe/expiry/multiplikatorji/likvidnost, deterministični payoff/Greeks/verjetnosti z omejitvami in preverjenimi matematičnimi primeri. Strateg interpretira; LLM ne proizvaja številk kot dejstva.
- [ ] K2: Usmeri starejši opis `options_strategist (Claude)` skozi sedanje LiteLLM vloge; ne uvajaj izključenega ponudnika po starem tekstu.
- [ ] K3: M7 šele po ločeni odobritvi: osnutek, guards, sled in dvojna potrditev na paper računu; prehod na živi račun je dodatna ločena odločitev. Izvedba ni del zaključevanja UX ali podatkovnih popravkov.

**Končano tega načrta za K:** zahteve in odložene meje so popisane. Opcije/naročila niso označeni done samo zato, ker imajo plan ali placeholder stran.

## 5. Potrebni vhodi in ravnanje brez njih

| Vhod | Potrebuje | Če ni na voljo |
|---|---|---|
| Očiščen dejanski razširjeni Flex | B/C | Sintetična pogodba ostane označena; ni trditve o živem uvozu |
| Identitete spornih kotacij | C/D | Ohraniti unknown/dvoumnost, prikazati konkretno vrzel |
| Dostop do ponudnika/pravice/kvote | D/E/J | Pripraviti fixture/adapter in poročilo, ne izmišljati pokritosti ali kupiti dostopa |
| Dejanska SMTP povezava in odobren prejemnik | F | Pošiljanje izklopljeno; fake testi se lahko dokončajo |
| Izbrani cilj kopij/dostopna testna baza | F/H | Brez dokaza restore objava nima potrjene obnovljivosti |
| Aktualno stanje sočasnega Claudovega dela | A/H | Samo primerjava, brez združevanja ali prepisa |
| Izbor obsega polnega backtesterja/novih virov/M6/M7 | I/J/K | Zapisati predlog in odložitev; ne širiti osnovne izdaje |

## 6. Oblika vsakega naslednjega SPEC

Namen in uporabniška pot; vključeno/izključeno; trenutni dokazi; vhodne/izhodne pogodbe ter lastništvo resnice; enote/valute/časovne osnove; stanja in prehodi; UI SL/EN; kvote in pravice; napake/sočasnost/idempotenca; migracija in rollback; merljivi scenariji prevzema; odvisnosti in odprte odločitve; sledljivost BL ↔ zahteva ↔ datoteka ↔ test ↔ dokaz. Podrobnosti določa spremljevalna priprava SPEC.

## 7. Pregled tveganih primerov

1. Ponovni ali nepopoln Flex ne izbriše veljavnega stanja in ne potrdi napačne gotovine (B).
2. Dve kotaciji istega simbola ne dobita zamenjane valute/metrik/zgodovine (C/D).
3. Izklop med modelnimi klici, DST, Redis izpad in ročni override ne obidejo kvote ali podvojijo plačljivega poskusa (E).
4. Izgubljen odgovor po oddaji/sporočilu ne ustvari dvojnega predloga ali slepega ponovnega SMTP pošiljanja (F/G).
5. Test zgodovinskih mnenj ne uporabi prihodnjih dejstev ali napačno prilagojenih cen kot zanesljiv dokaz donosa (I).

Vsak primer mora dobiti test v lastniškem paketu. Nedostopen vhod je zapisana blokada konkretnega dokaza, ne razlog za lažen done celotne naloge.

## 8. Merilo zaključka celote

Ni nepokritih odprtih BL ID; izvedene stvari imajo dokaz, odložene obseg/razlog in sprožilni pogoj. Obvezne podatkovne/finančne napake so rešene pred prevzemom. Za izbrano izdajo obstaja zelen preverjen paket, aktualna kopija z restore dokazom ter uporabniški pregled. Dejanska namestitev :3000 je še vedno ločena odločitev.

## 9. Popolna sledljivost odprtega BACKLOG

Spodnja matrika se generira iz vseh vrstic s statusom next/doing/later/blocked ob pripravi dokumenta. Opis, zgodovinski status in paket niso nova trditev o trenutni implementaciji. Zaporedje v §3 ima prednost pred zgodovinskim statusom.

| Naloga | Zgodovinski status | Paket | Predmet preverbe / preostalo delo |
|---|---|---|---|
| BL-005 | later | G | Prototipi še za SCR-04, 08, 09, 10, 12 + mobilna različica SCR-01/02 (zdaj neposredno v React, ne na platnu) |
| BL-011 | doing | E | LiteLLM `config.yaml`: 5 vlog, proračuni, fallbacki; test klica vsake vloge (konfiguracija narejena, živi test na tvojem strežniku) |
| BL-012 | next | E | Ollama na GPU napravi: potrdi model (Qwen ~27B Q4), dodaj embed model, izmeri hitrost triaže (novic/min) |
| BL-013 | next | E | ~~Claude Pro Agent SDK~~ Claude ni v cevovodu (S-003). Namesto tega: MiniMax API ključ in izbira modela za `cloud-deep` |
| BL-016 | next | F | Tailscale na strežniku, HTTPS (Tailscale cert), dostop s telefona (Tailscale je že nameščen na vseh napravah) |
| BL-160 | next | G | Uporabniški pregled M0 lupine na tvojem strežniku (docker compose up) in popravki UX |
| BL-017 | later | F | Varnostne kopije: nočni `pg_dump` v ločen disk |
| BL-023 | doing | F | IB Gateway Docker (`gnzsnz/ib-gateway`, READ_ONLY_API, IBC auto-restart), ločen API uporabnik (compose profil `broker` narejen; živi preizkus na… |
| BL-027 | doing | D | ETF profili: TER, AUM, holdings (izdajatelji CSV / yfinance), sektorji, države (seznam UCITS + ISIN narejen; holdings še ne) |
| BL-033 | later | J | (neobvezno) Uvoz idej in tez iz `trading-list` (MySQL izvoz) |
| BL-042 | later | J | Reddit/StockTwits pozornost (omembe proti 30-dnevni bazi) za watchlisto + kandidate (še ni vira; zdaj samo RSS, Finnhub, EDGAR) |
| BL-052 | doing | D | SCR-01 Pregled (prva verzija) (portfelj in vrednost sta živa; utrip, lijak in režim še vzorčni) |
| BL-057 | later | F | Telegram bot: besedila odgovorov (/start, /predlog, gumbi) v messages, ne v kodi |
| BL-058 | later | E/F | Jutranji povzetek ob 7:30 po lokalnem času (zdaj 05:30 UTC, pozimi 6:30) |
| BL-182 | later | J | Spremljani viri (osebe, kanali, strani): model `watched_source` (vrsta, URL, oznaka, aktivno), API in seznam v nastavitvah. Vse objave so vrste… |
| BL-183 | later | J | YouTube: nove objave kanala prek YouTube Data API (seznam naloženih videov), prepis podnapisov, povzetek `local-fast`/`cloud-quick` s simboli in… |
| BL-184 | later | J | Instagram: uradni Graph API bere tuje račune samo prek lastnega poslovnega računa (Business Discovery), strganje krši pogoje uporabe. Odloči:… |
| BL-185 | later | J | Spletne strani: RSS, kjer obstaja, sicer periodično branje strani s primerjavo vsebine (spoštuj `robots.txt`), nova vsebina gre v isti cevovod kot… |
| BL-186 | later | J | Predlog iz slike: prilepljen posnetek zaslona (CMP-30 v spletu, fotografija v Telegramu) → izluščeni simboli s kratkim kontekstom → uporabnik… |
| BL-067 | later | I | `dip_analyst`: primerjava s sektorskim ETF-jem (ne samo s SPY), sektor iz profila instrumenta |
| BL-084 | later | J / namensko odloženo | (odloženo) `claude_runner` samo, če se kasneje odločiš za Claude Agent SDK |
| BL-087 | later | I | Znanje za agente: prepis izbranih Vibe-Trading skills v `services/agents/knowledge/` |
| BL-094 | later | I | Relativno vrednotenje proti sorodnim podjetjem (Finnhub `/stock/peers`) in odkupi delnic (sprememba števila delnic) |
| BL-169 | next | E | Radar: predpomnilnik triaže po hashu vsebine (danes ob novem članu grozda znova pošlje vse stare, ~450 k žetonov na dan na `local-fast`), prevodi… |
| BL-170 | next | E | Vstopne točke: `analyze_dip` skrajša naslov in povzetek dogodka, da vhod ostane pod 16 k |
| BL-171 | later | I | Odstrani TradingAgents iz poti delnic: knjižnica, `deep_research/` graf in njegovi testi (ostane posnetek in vir EDGAR) |
| BL-172 | later | E | Poraba žetonov v UI: `models.usage` analize prikaži v podrobnostih (klici, vhod, izhod) |
| BL-174 | next | C/D | Ročno dodan instrument (npr. AMD) ima `kind=unknown` brez borze in valute: dopolni podatke iz profila Finnhub; tedenski posel temeljev naj zapiše… |
| BL-176 | next | E | `models.usage` naj pri vsakem klicu zapiše število poskusov; zdaj se vhod popravnega poskusa prišteje in klic na videz preseže 16k |
| BL-180 | later | E | Rok 540 s velja za posamezen HTTP klic; s popravnim poskusom lahko klic `complete_json` traja do dvakrat dlje. Dodaj skupni rok za celoten klic |
| BL-181 | later | E | Preveri, ali MiniMax prek LiteLLM res uveljavi `json_schema` (zdaj ščiti samo lokalno preverjanje in popravni poskus) |
| BL-120 | later | K | Opcijska veriga iz IBKR (zakasnjeno) |
| BL-121 | later | K | Payoff, Greeks, verjetnost (prepis Vibe-Trading `options.ts` / `options_payoff.py`) |
| BL-122 | later | K | `options_strategist` (Claude) + varovala (brez golih callov, likvidnost) |
| BL-123 | later | K | SCR-07 Opcije, CMP-14 |
| BL-140 | later | K | `order_draft`, varovala (`guards.py`, prepis legacy `risk.ts`), revizijska sled |
| BL-141 | later | K | Paper račun: oddaja z dvojno potrditvijo (CMP-18) |
| BL-142 | later | K | Odločitev o prehodu na živi račun (nov ADR) |
| BL-193 | doing | D | Audit refresh fundamentov dodan (izid po instrumentu); uspešen živi refresh in vzrok prazne ciljne populacije ostajata za potrditev |
| BL-194 | next | C | Potrditi kotacijo/valuto/vrsto devetih unknown instrumentov na watchlisti; ne privzeti USD ali napačnega simbola |
| BL-202 | next | B | Potrditi razširjeni zasebni Flex XML, FinancialInstrumentInformation, dividendne identitete/davke/popravke in dejansko pokritost |
| BL-203 | next | G | Nadaljnji UX po pregledu: poimenovani profili, primerjava vrstic, enoten iskalnik, preostali paneli instrumenta/analize, 200-% povečava |
| BL-204 | next | G | Trajno vezati ključ idempotence oddaje predloga na shranjeni osnutek čez reload in izgubljen odgovor |
| BL-205 | next | B | Pred prenosom zapreti dodatne Flex robove: BASE_SUMMARY-only cash in nepopolne vrstice brez potrjene valute |
| BL-211 | next | D | Potrjeni makro podatkovni viri VIX/US10Y/DXY in zadostna zgodovina nedvoumne kotacije SPY; ohraniti čas/vir |
| BL-212 | next | F | Po uporabniški konfiguraciji SMTP izrecno preveriti dejansko dostavo in negotove dostave; med razvojem samo fake transport |
| BL-214 | next | A | Pripraviti in pregledati končne SPEC S-B…S-H za osnovno izdajo ter ločene SPEC odloženih sklopov; zahteve/vmesniki/prevzem brez domnevnih podatkov |
| BL-215 | next | H | Pripraviti usklajen dokazni paket izdaje, razliko Claudove/pregledne veje, backup/restore in rollback; prenos :3000 samo po novi izrecni potrditvi |
| BL-216 | later | I | Ločen SPEC in poznejša izvedba polnega portfeljskega backtesterja s point-in-time podatki, korporativnimi dejanji, stroški in gotovino; ohraniti… |

Kontrola: **49 odprtih vrstic**, vse imajo paket; noben ID ni izpuščen ali samodejno zaključen. BL-213 je dokumentarna naloga in je zaključena ločeno od teh izvedbenih nalog.
