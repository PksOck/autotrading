# SESSIONS.md: dnevnik delovnih sej

Najnovejša seja je na vrhu. Vsaka seja ima ID `S-xxx`, datum, cilj, rezultat, odločitve in odprta vprašanja. Predloga je na dnu.

---

## S-017 · 2026-10-29 · Pregledna nadgradnja in ločen demo

**Cilj:** Izvesti potrjene nadgradnje in pripraviti pregled, ob zadnji izrecni omejitvi uporabnika brez prepisa okolja :3000.

**Narejeno:** BL-195–201 v veji `feat/uxui-demo-upgrade`: skupni DataMeta/read modeli in nastavljive tabele; zadnji popolni posnetek po računu; filtri zadnjih uspešnih analiz; razumljivi predlogi/retry; podrobnosti Radar/Vstopi/Signali; dividendne evidence in pokritost; politike procesov, urniki, globalna pavza, paketni predogled/kvota/sledi; Pregled iz baze ter varna dopolnitev identitete. Migracije 0016–0018 in generirani OpenAPI/TS. Astra je pregledala integracijo; popravljeni ročni zagoni ob globalni pavzi, izrecna izjema okna, časovna vez odprtih dividend ter nevarnost nepopolnih pozicijskih vrstic. Docker demo :3100 ima ločene sintetične scenarije.

**Preverjanje:** API 521, agents 218, web 143 uspešnih testov; Playwright 54 uspešnih/10 predvideno preskočenih/0 neuspešnih. TypeScript, ESLint, Ruff/mypy in SL/EN (1162 ključev). Produkcijska gradnja spletnega dela v Linux Dockerju; Windows SWC omejitev ostaja. Ročno preverjene nastavitve in watchlista pri širini 768 brez prelivanja celotne strani. Natančen obseg in omejitve: [pregled sprememb](./docs/implementation/2026-10-29-pregled-sprememb.md).

**Odločitve:** ADR-0017–0020 zapisani za pregledno izvedbo. Novi paket analiz privzeto izklopljen, obstoječi procesi ohranijo svoj urnik. Uporabnik je pred objavo izrecno zahteval pregled in novo potrditev: **:3000 ne posodabljaj**, niti z že zgrajenimi slikami. Preverjeno samo za branje: web/API :3000 imata prvotni sliki in čas zagona 2026-10-28. Claudov izvorni checkout ostaja nedotaknjen. Brez živih analiz ali množičnega refresha zaradi demo pregleda.

**Odprto:** BL-193 živa pokritost fundamentov, BL-194 neznana vrsta/valuta; BL-202 resnični razširjeni Flex in metadata; BL-203 preostali UX ter 200-% povečava; BL-204 trajen ključ oddaje osnutka; BL-205 dodatni robovi Flex gotovine/valute. Dividendna XML pogodba je sintetično preizkušena, ne potrjena z zasebnim razširjenim izpisom. Celoten prvotni načrt zato ni označen kot v celoti zaključen.

**Naslednji korak:** Uporabniški pregled :3100 in dopolnitve. Pred vsakim prenosom :3000 pridobi novo izrecno potrditev uporabnika ter preveri sočasno Claudovo vejo, aktivne analize in aktualno kopijo. Vejo in worktree ohrani.

---

## S-016 · 2026-10-29 · Izvedba Vala −1: signali in podatkovna inventura

**Cilj:** Po potrditvi »Ja gremo v delo« izvesti FIX-A, FIX-B in read-only UX-00 iz potrjene specifikacije.

**Narejeno:**
- BL-190 / `0720806`: skupna normalizacija poteka new/watching pred filtri/limitom; accepted/dismissed ostaneta odločitev uporabnika. Pred popravkom 4 ciljni testi padejo, po njem regresije in celotna zbirka uspejo.
- BL-191: GET `/signals/{uuid}`, neodvisen od filtrov in prvih 100 zapisov; read-only detail v PeekPanel, status/govorica/vir/čas/dokazila, 404/422/napaka/ponovitev. Ločen query cache, invalidacija list/detail in generirana OpenAPI/TS pogodba. Close odstrani samo peek z replace; browser Back ohrani obstoječo navigacijo.
- Svež neodvisni pregled veje je odkril odsotnost vrnitve fokusa. Popravek je preverjen z najprej rdečim in nato zelenim brskalniškim testom Close/Escape/Back za isti sprožilec. Obstoječi 48px touch CSS je ohranjen.
- BL-192: [poročilo](./docs/research/2026-10-29-izvedljivost-metrik.md), JSON matrika in read-only SQL. Cilji: 26 portfelj + 10 watchlista, brez preseka; fundamenti 0/36, cene 35/36, valuta 27/36, ETF profil 0/2. Edini fundament v bazi je zunaj ciljnih seznamov. Ni bilo množičnega refresha ali klicev ponudnika.
- Preverjeno: API **467 testov**, web **126 testov**, Playwright **10/10** (desktop in 390×844 touch; SL/EN; direktni URL, Entries→signal→Back, fokus, Escape, instrument predogled, brez mutacij); Ruff, mypy strict domain, ESLint, TypeScript, 847 i18n ključev, produkcijski Docker build. Podrobnosti ukazov in okolja so v [prevzemu](./docs/research/2026-10-29-val-minus-1-prevzem.md).

**Odločitve:** Delo v namenski veji `fix/signal-read-contracts` na obstoječem izoliranem checkoutu `1855eb8`; Opusov načrt ostaja kopija iz `28f2990`. Celoten načrt ni samodejno implementiran: podatkovna vrata za naslednji val so v raziskavi. DESIGN posodobljen za signalni PeekPanel. Brez novih ADR ali migracije sheme.

**Odprto:** Prevzem commitov v aktualno Claudovo vejo in objava v demo še nista izvedena. Windows SWC ima težavo z varnostjo predpomnilnika; enakovreden produkcijski build je preverjen v ločenem Dockerju. Opozorila API o zastarelih knjižničnih API-jih ostajajo. BL-193–196 so nove ločene naloge, ne prikrito opravljene spremembe.

**Naslednji korak:** Najprej uskladiti prevzem z aktualno Claudovo vejo; nato BL-193/194 in read pogodba BL-195 pred širjenjem stolpcev. Rešitev /proposals, filtri analiz, nastavitve urnikov in dividendni zavihek sledijo svojim valovom potrjenega načrta.

---

## S-015 · 2026-10-29 · SPEC po Opusovem pregledu načrta

**Cilj:** Prevzeti posodobljeni načrt iz Claudove veje, preveriti komentarje in začeti konkretno specifikacijo brez implementacije.

**Narejeno:**
- Prevzeta bajtno enaka kopija načrta iz `28f2990`, SHA256 `030CD7F3293E558FD21ADCBEB9750B00A58384CB9E117F5DDC638CDF259B32BF`, ter spremljevalna Astra revizija/ožji osnutek. Izvorna Claudova veja in njena nepovezana `.env.example` sprememba ostaneta nedotaknjeni.
- Dodani [glavni SPEC](./docs/superpowers/specs/2026-10-28-celovita-uxui-spec.md), [podrobni Val −1](./docs/superpowers/specs/2026-10-28-val-minus-1-spec.md) in [presoja Opusovih komentarjev](./docs/superpowers/specs/2026-10-28-opus-komentarji.md). Dokumenti definirajo prioritetna FIX-A/B, read-only UX-00, pogodbe UI/API, podatkovno kakovost in odvisnosti vseh valov.
- Upoštevane Astrove pripombe: lokalno ponavljanje urnika z IANA cono, podatkovna razpoložljivost ločeno od React/transport stanj, dividendna osnova/izvor polja, ločen cash ledger in accrual snapshot, neveljavnost deljenja osebnih prejemkov s trenutno količino, varna neposredna signalna povezava in ohranitev obstoječega zapisovanja poteka.
- Uradne reference IBKR pregledane 2026-10-29: Open/Change Dividend Accruals in Financial Instrument Information; XML konkretnega izpisa še ni potrjen. Preverjanje žive pokritosti ali ponudniških pravic ni bilo izvedeno; Opusov 1/46 ostane datiran izvorni podatek.
- BACKLOG usklajen z BL-188 (prevzet načrt) in BL-189 (dokumentarni osnutek SPEC). Izvedbenih statusov nismo označili kot končanih.

**Odločitve:** Samo predlagane izvedbene pogodbe in njihove utemeljitve. Formalni ADR-0017–0020 ostanejo predlog za ločeno sejo Astre, brez podvajanja številk. Ta SPEC ne spreminja DESIGN ali aplikacijskega obnašanja.

**Odprto:** Astra je posredovala tehnične pripombe, celotnega ponovnega pregleda končnih datotek pa zaradi omejitve uporabe ni zaključila; ne trdimo neodvisne odobritve. Obstoječi nesleden `services/api/tests/test_signal_expiry.py` je iz prejšnjega koraka in ni popravljen ali odstranjen. Izolirana koda ostaja `1855eb8`; ni commita/združitve, namestitve, podatkovnega uvoza ali novega testnega/LLM zagona v tem dokumentarnem koraku.

**Naslednji korak:** Pregled SPEC, nato samostojna izvedba FIX-A/B in read-only UX-00. Pred posegi ponovno preveriti aktivno osnovo in proste BL-ID-je; pri UI sklopih najprej prototip in pogodbe, pri dividendah razširjen anonimiziran Flex vzorec.

---

## S-013 · 2026-10-28 · Vitka zaporedna analiza delnice

**Cilj:** BL-167: manj žetonov na analizo delnice, vsak klic pod 16 tisoč vhodnih žetonov. Čim več dela opravi koda, AI samo presodi in združi.

**Narejeno:**
- ADR-0016: koda pripravi povzetke trga, temeljev in novic ter register dokazov. Trije analitiki tečejo zaporedno, sledita bik in medved ter en odločevalec, ki pri delnicah nadomesti kartico in preverjanje hipoteze. Lokalni povzetek je neobvezen.
- `budget.py`: ocena vhoda, delovna meja 12 tisoč, trda 16 tisoč, meje izhoda po vlogah (6000, 10.000, 2000). Poraba po klicih se shrani v `models.usage`. API in UI prikažeta nov zapis modelov.
- Preverjanje številk: številke brez opore v registru postanejo `[?]`. Obdobja (tudi »200-dnevno«, »20- in 50-dnevnega«), datumi (»30. junija 2026«) in predznak, izražen z besedo (»padec«, »odtok«), niso več napačno označeni.
- Prvi živi tek je padel s praznim odgovorom: splošne novice so izrinile dejstva o AMD, model ni vedel, katero podjetje analizira, MiniMax pa ne upošteva `response_format`. Popravki: prednostni red v registru, splošne novice (`G`) največ 5 in nikoli uradne, polje `instrument`, shema tudi v sistemskem pozivu, višje meje izhoda.
- Živi tek AMD (`b782bf65`) je uspel: 6 klicev, okoli 76 tisoč žetonov namesto 353 tisoč (−78 %), največji vhod okoli 8,4 tisoč, 6,5 minute namesto 42.
- AMD ni imel temeljev in ne novic o podjetju, ker ni na watchlisti in ga nimaš v portfelju. Finnhub novice in temelje dobijo samo ti simboli, temelje samo ob nedeljah. Zdaj analiza delnice pred začetkom sama naloži manjkajoče ali več kot 7 dni stare temelje in novice Finnhub za ta simbol. Novice gredo samo v posnetek analize, ne v bazo, da jih radar pozneje še vedno obdela. Pri analizi za datum, starejši od 3 dni, se nič ne naloži, ker bi to pomenilo pogled v prihodnost.
- Sklad je bil ponovno zgrajen in zagnan.
- Ponovni tek AMD (`0098df84`) je padel, ker je medved vrnil 6 citatov namesto največ 4. Zdaj shema modelu še vedno sporoča kratke meje, sprejme pa do 16 citatov in 6 točk. Nič se ne reže pred preverjanjem govoric; na javne meje kartice se skrajša šele po njem (neodvisni pregled je pokazal, da bi rezanje lahko skrilo govorico za nakupom).
- Preverjanje številk sprejme "3-, 6-mesečni" ter "RSI 14", "ATR 14" in "SMA 200" s presledkom. "RSI 70", "ATR 14 %" in "SMA 200 000" se še vedno preverjajo.
- Napaka pri nalaganju temeljev ali novic ne pusti več analize v stanju `running`: zapis temeljev je v savepointu, vsaka napaka pa se samo zabeleži.
- Tek AMD `9d4dfe69` (pred popravki pregleda): uspel, Underweight, 0 `[?]` (prej 57), temelji Finnhub prisotni, 248 novic, 6 klicev, okoli 46 tisoč vhodnih in 48 tisoč izhodnih žetonov, 8 minut. Klica medveda in odločevalca sta potrebovala popravni poskus; vsak posamezen klic je pod 16k.
- Preverjeno: agenti 192 testov z bazo, ruff, mypy; API 289 testov z bazo, ruff.
- Tek AMD `3bd633f4` na končni različici: uspel, Overweight, 248 novic, temelji Finnhub z današnjim datumom, 6 klicev brez popravnih poskusov, okoli 38 tisoč vhodnih in 38 tisoč izhodnih žetonov, 5,6 minute. En `[?]` (odstotek rasti prihodkov, ki ga ni med dejstvi) in opozorilo `unverified_numbers`: preverjanje številk deluje, kot mora.
- BL-177: `sweep_runs` zaključi tek v stanju `running` kot `failed`, ko je starejši od časovne omejitve opravila (3 h + 15 min) in arq zanj nima več živega opravila. Samo starost ne zadošča: tek `b063971d`, prekinjen ob ustavitvi sklada, je arq po zagonu ponovil z izvirnim `started_at` in se je končal `done`. Implementacija in pregled prek OpenCode Sol, preverjeno: agenti 198 testov z bazo, ruff, mypy; poizvedba stanja opravila in pometanje na živem Redisu.
- BL-175: determinističen klasifikator govoric `preza.domain.rumor.looks_like_rumor` (angleški in slovenski izrazi za nepotrjene posle, pripis anonimnim virom, `- sources` na koncu naslova). Velja za shranjene in sveže neuradne novice v posnetku; sporočila za javnost in vloge (filing) se po besedilu ne razvrščajo, zastavica radarja ostane. Pregled Sol je zahteval širši nabor izrazov in ožja sprožilca `speculation` in `in talks`; oboje popravljeno. Preverjeno: API 332 testov z bazo in 94 testov klasifikatorja, agenti 214 testov z bazo (vključno z `Buy` → `Hold` pri nepotrjenem prevzemu), ruff, mypy; na 538 shranjenih novicah označi 1 ("two sources say"). Popravek po pregledu ni dobil drugega pregleda.
- BL-178: radar uporablja isti klasifikator. Neuradna novica z obotavljivim besedilom označi nov dogodek kot govorico, priključitev k obstoječemu dogodku zastavico ohrani (grozdenje ni potrditev). Triaža LLM determinističnega znaka ne more več preglasiti; potrdi ga samo sporočilo za javnost ali vloga. Signal, ki pade pod prag zaradi kazni za govorico, ni več prikazan kot potrjen (`new` → `watching`). Seznam uradnih vrst je zdaj samo v `preza.domain.rumor`. Implementacija in dva pregleda prek OpenCode Sol.
- BL-168: odjemalec LLM pošlje `max_completion_tokens` za oblačne vloge in `max_tokens` za lokalne, rok odjemalca je 540 s (proxy 600 s). `finish_reason=length` je zdaj ločena napaka `output_truncated` brez popravnega poskusa; neveljavna shema po popravku je `schema_validation_failed`, obe se zapišeta v porabo. Razmišljanja ni mogoče izklopiti, ker MiniMax-M3.1-Flash zavrne `thinking=disabled`, zato izhodne meje vključujejo žetone razmišljanja. Živo preverjeno prek LiteLLM: omejitev 16 žetonov upoštevajo `cloud-quick`, `local-fast` in `local-reason` z obema imenoma parametra (`finish_reason=length`, 16 izhodnih žetonov), torej zdrži tudi ob fallbacku.
- Preverjeno: API 425 testov z bazo, agenti 216 testov z bazo, ruff, format, mypy; sklad (api, agents) ponovno zgrajen. Ni preverjeno: celoten radar na živih novicah in uveljavljanje `json_schema` pri MiniMax (BL-181).
- BL-179: pregled teze ohrani kodo `output_truncated` ali `schema_validation_failed`, ostale napake LLM ostanejo `role_unavailable`. Implementacija prek OpenCode Sol, preverjeno: agenti 218 in API 428 testov z bazo, ruff, mypy.
- Nove ideje v BACKLOG: spremljani viri (osebe, YouTube, Instagram, spletne strani; BL-182 do BL-185) in predlog iz posnetka zaslona s potrditvijo simbolov in hitro analizo (BL-186).
- BL-187: na Portfelju gumb Uvozi Flex XML za izpis, prenesen iz IBKR, deluje brez tokena. API `POST /portfolio/import` sprejme surovo telo XML (do 10 MB), neveljavno datoteko zavrne s kodo `flex_invalid` brez vsebine datoteke in ponoven uvoz iste datoteke ne podvoji poslov. Implementacija prek OpenCode Sol (tek se je ustavil, dokončal glavni agent). Pregled Sol je našel, da spletni proxy vsako telo pošlje kot JSON in da se telo bere v celoti pred preverjanjem velikosti; oboje popravljeno (proxy posreduje tip XML, API bere tok do 10 MB). Popravek je naredil glavni agent, ker ponudnik Sol ni imel kvote. Preverjeno: API 447 in web 118 testov, ruff, eslint, tsc.

**Odločitve:** ADR-0016. TradingAgents za delnice ni več v uporabi (odstranitev BL-171).

**Odprto:**
- Razmišljanje MiniMax je okoli polovice izhodnih žetonov (BL-168).
- Kartica je imela prepričanje 6 in oceno Hold, odločitev pa Overweight.
- Novice Finnhub se ne klasificirajo kot govorice (BL-175). Poraba ne beleži števila poskusov (BL-176).

**Naslednji korak:** BL-176 ali BL-174; za BL-182 in BL-186 najprej odločitev o virih in vlogi za slike.

---

## S-012 · 2026-10-27 · Kalibracija uteži, LiteLLM in cene na watchlisti

**Cilj:** BL-103, popraviti padlo analizo (LiteLLM) in hitrejše cene na watchlisti.

**Narejeno:**
- BL-103 (ADR-0015): predlog uteži iz izidov (Wilsonov interval, krčenje proti osnovi, meje 0,50–1,50), tabela `signal_weight_set` (migracija 0015), `GET/POST /calibration`, potrditev samo z `{"confirm": true}`, utež pomnoži moč novih signalov radarja in pravil. SCR-10 ima razdelek »Predlog uteži«.
- BL-097: analiza je padla po 24 minutah, ker OpenCode Go zavrne klice brez seje OpenCode, nadomestni klici pa so se ponavljali. `cloud-quick` in `cloud-deep` sta zdaj na MiniMax, timeout 600 s za `cloud-deep`, brez ponavljanja ob timeoutu. Ponovna analiza AMD je uspela (42 min, 15 korakov).
- BL-166: dodajanje na watchlisto takoj sproži prenos cen; prej so prišle šele ob 21:30 UTC ob delavnikih. ELF, O, UNH, NVO in MSFT so dobili cene in ceno ob dodajanju.
- Živi sklad: varnostna kopija v `preza-backups`, migraciji 0014 in 0015 uveljavljeni.
- Preverjeno: API 289 testov, ruff, mypy; web vitest, tsc, eslint; e2e SCR-10 na demo skladu (namizje in telefon).

**Odločitve:** ADR-0015. Glave `x-opencode-session` ne ponarejamo.

**Odprto:** poraba žetonov pri analizi je previsoka (BL-167).

**Naslednji korak:** BL-167.

---

## S-011 · 2026-10-27 · Uspešnost in zaključek M5

**Cilj:** zaključiti preostale naloge M5: BL-163, BL-161 in BL-102 (SCR-10).

**Narejeno:**
- BL-163: `vendor_local` piše CSV z `
` na vseh platformah, zato se golden kontrolne vsote ujemajo tudi na Windows.
- BL-161: različica osnutka teze ima `edit_count` in `edited_at` (migracija 0014). Urejanje pošlje `expected_edit_count`; zastarelo urejanje vrne 409 `revision_edit_conflict` s prijaznim sporočilom. `updated_at` zdaj upošteva tudi urejanja.
- BL-102: `GET /track-record` (domena `track_record.py` je čista in brez I/O) in zaslon SCR-10. Zadetki in donos so v smeri signala, alfa je proti indeksu, shranjenemu ob izidu. Tvoji predlogi (`manual` ali s `proposal_id`) se merijo ločeno. Kalibracija ima 5 razredov moči. Pod 10 izidi je številka označena.
- Proxy `app/api/[...path]` je imel seznam dovoljenih poti brez `track-record`; dodano.
- Oznake mejnika v navigaciji so odstranjene pri izvedenih zaslonih (Vstopi, Teze, Uspešnost).
- Demo seed doda 14 preteklih signalov; izidi se izračunajo iz demo sveč proti CSPX.
- Preverjeno: API z bazo 281 testov, ruff, mypy; web tsc, eslint, vitest 108; e2e na demo skladu 34 uspešnih in 10 preskočenih; telefon brez vodoravnega drsenja.
- Neodvisnega pregleda ni bilo, ker OpenCode Sol nima kvote.

**Odločitve:** SCR-10 kalibracijo samo prikaže. Predlog novih uteži je ločena naloga (BL-103) in zahteva tvojo potrditev.

**Odprto:**
- Živa baza potrebuje migracijo 0014, ko se živi sklad zgradi iz te veje.
- Osnutek teze ASML čaka tvojo potrditev, BL-097 je tvoja odločitev, IB še ni povezan.

**Naslednji korak:** BL-103 kalibracija uteži, nato M6.

---

## S-010 · 2026-10-27 · Demo sklad za e2e

**Cilj:** e2e naj teče zeleno na vzorčnih podatkih, brez posega v živo bazo (BL-162).

**Narejeno:**
- `infra/docker-compose.demo.yml`: ločen projekt `preza-demo` z lastno bazo, Redisom, API-jem in webom na `127.0.0.1:3100`. Brez LiteLLM, workerja, agentov in obvestil. Yahoo, Stooq in RSS so izklopljeni.
- `infra/scripts/demo-stack.sh` (`up`, `seed`, `stop`).
- `seed_demo` se brez `PREZA_DEMO_DB=1` ustavi, ker pobriše vse vstope in signale pravil.
- Demo analize imajo v posnetku sveče in temeljne podatke, zato so obeti (ADR-0014) izpolnjeni.
- Besedilo praznega portfelja in README-ji kažejo na nov ukaz.
- e2e na demo skladu: 32 uspešnih in 10 namerno preskočenih (delitev telefon/namizje). Prej je bilo 13 neuspešnih.
- Neodvisnega pregleda ni bilo, ker OpenCode Sol nima kvote.

**Odločitve:** vzorčni podatki samo v ločenem skladu, nikoli v živem (`preza`).

**Odprto:**
- Ob `--repeat-each` z več delavci se kopije testa watchliste (NVDA) med seboj motijo. Običajen zagon ni prizadet.
- Na disku C: sprosti prostor (97 %).
- Osnutek teze ASML čaka tvojo potrditev, BL-097 je tvoja odločitev, IB še ni povezan.

**Naslednji korak:** naslednja naloga M5.

---

## S-009 · 2026-10-27 · Analiza za odločitev

**Cilj:** stran analize naj pokaže samo tisto, kar potrebuješ za odločitev (uporabnikova pripomba: preveč podatkov naenkrat, "Underweight" ni razumljiv, manjkajo obeti po obdobjih).

**Narejeno:**
- ADR-0014: obeti za kratko (do 3 mesecev), srednje (~1 leto) in dolgo obdobje (3+ let) računa deterministična koda iz posnetka podatkov (`domain/outlook.py`). Agenti jih ne ocenjujejo. Vsak dokaz ima vir, čas, vrednost in prag.
- API: `AnalysisOut.outlook`, `AnalysisSummary.conviction` in `outlook_brief`.
- Web (BL-165): glava z dejanjem v navadnem jeziku ("Zmanjšaj delež" namesto "Underweight"), prepričanjem, trenutno ceno in pozicijo; tri kartice obetov; dokazi za rast levo in proti desno; "Ocena gre gor/dol, če". Utemeljitev, kontrolna ocena in koraki analitikov so zloženi, koraki so razvrščeni po agentu. `/analysis` ima tabelo s stolpci za dejanje, obdobja, za/proti, prepričanje in delnice v portfelju, na telefonu pa kartice.
- Testi: API 223, web 103 enotskih, tsc, eslint in i18n so čisti. Preverjeno v brskalniku na živi analizi ASML (namizje in 375 px, brez prelivanja). e2e: 19 uspešnih in 13 neuspešnih, vsi neuspešni potrebujejo vzorčne podatke, ki jih živa baza nima (BL-162).
- Neodvisnega pregleda ni bilo, ker OpenCode Sol nima kvote.
- Docker Desktop se je sesul (containerd SIGBUS, disk C: 97 % poln). Pomagalo je zaporedje `docker desktop stop`, `wsl --shutdown`, `docker desktop start`.

**Odločitve:** ADR-0014.

**Odprto:**
- BL-162: e2e potrebuje vzorčne podatke, ker test ASML preverja vzorčne vrednosti.
- Na disku C: sprosti prostor, sicer se Docker lahko spet sesuje.
- Osnutek teze ASML čaka tvojo potrditev, BL-097 je tvoja odločitev, IB še ni povezan.

**Naslednji korak:** BL-162 (vzorčni podatki za e2e), nato naslednja naloga M5.

---

## S-008 · 2026-10-25 · Oblikovanje za Android in Windows

**Cilj:** vmesnik naj na Androidu in Windows ne deluje kot aplikacija za Apple (uporabnikova pripomba).

**Narejeno:**
- ADR-0013: en platformno nevtralen vmesnik, kjer se platformi razlikujeta, sledi Material 3 (dotik) in Fluent 2 (miška).
- Web (BL-164): oznaka bližnjice `Ctrl K` (`⌘K` samo na macOS, skrita na dotiku), skupni `SegmentedButtons` (obrobljena skupina M3 namesto drsnika iOS), brez `backdrop-blur` (polna glava, temna prosojna plast), obrobljena polja, kritično dušene vzmeti, 48 px na dotik, navigacijska vrstica M3 s 5 cilji (Vstopi pod Več), polmeri 4/8/12, tanki drsniki, spletni manifest in barva teme, sistemska tipka nazaj zapre paleto ukazov in okno predloga.
- Reviewer (Sol) je našel napako v zgodovini kukala (`?peek=`): kukalo smo vrnili na prejšnje vedenje (`router.push`, nemodalno), ker ga tipka nazaj že zapre. `useBackToClose` velja samo za prekrivni plasti, ki nista v URL-ju.
- Testi: web 98 enotskih, e2e 19 uspešnih, 10 preskočenih (vzorčni podatki, BL-162). tsc, eslint, i18n čisti. Vsebnik `web` je na novi sliki.

**Odločitve:** ADR-0013.

**Odprto:**
- Preveri na pravem telefonu Android (namestitev kot aplikacija, tipka nazaj) in v Edge na Windows.
- Osnutek teze ASML še čaka tvojo potrditev; BL-097 ostaja tvoja odločitev; IB še ni povezan.

**Naslednji korak:** naslednja naloga M5 iz BACKLOG.

---

## S-007 · 2026-10-25 · BL-101 tedenski pregled tez

**Cilj:** tedenski pregled tez s predlogi in signalom `thesis_break` (ADR-0012).

**Narejeno:**
- API: tabeli `thesis_review` in `thesis_claim_review_proposal` (migracija 0013), posnetek vhoda z do 30 viri (10 mest za uradne), uradnost določi koda (EDGAR, `rss:prnewswire` z gostiteljem), družbena omrežja so vedno govorica. Predlog `broken` z vsaj enim uradnim citatom brez govorice ustvari `thesis_break` (prioriteta 0,8). Sprejem gre skozi obstoječo spremembo statusa z `actor = "user"`, 409 ob spremembi trditve; zavrnitev zahteva razlog in zapre odprt signal.
- Agents: `thesis_tracker` z nedeljskim tekom ob 06:15 UTC in dnevnim ob 06:20 UTC, en klic `cloud-deep` (4000 izhodnih žetonov, 660 s), brez odprte transakcije med klicem, `failed_unknown` po prekinitvi brez ponovnega klica.
- Web: predlogi na SCR-09 ločeno od dejanskega stanja trditve, sprejem z izrecno potrditvijo, zavrnitev z razlogom, SL/EN.
- Testi: API 269 (z DB na izolirani bazi), agents 68 (z DB), web 79 enotskih, e2e teze 8.
- Migracija 0013 na živi bazi (varnostna kopija `C:/Users/Jan/Documents/preza-backups/preza-pre-0013-20261025T193625Z.dump`, pisci ustavljeni, reviewer APPROVE). Vse storitve so na novi sliki iz te veje.

**Odločitve:** ADR-0012 (pregled ustvari predlog, status trditve spremeni samo uporabnik).

**Odprto:**
- Prvi živi pregled bo v nedeljo ob 06:15 UTC oziroma ob dnevnem teku, ko bo potrjena aktivna različica (osnutek ASML še čaka tvojo potrditev).
- Štirje regresijski testi agents padejo samo na Windows zaradi CRLF kontrolnih vsot (v Linux kontejnerju uspejo), BL-163.
- BL-097 ostaja tvoja odločitev.

**Naslednji korak:** oblikovanje za Android in Windows (BL-164).

---

## S-006 · 2026-10-25 · Živi viri podatkov in začetek M5 Teze

**Cilj:** preveriti žive povezave iz `.env` (IB še ni povezan), popraviti ugotovljeno in začeti M5.

**Narejeno:**
- Preverjeni viri: Finnhub, Yahoo, EDGAR (po vpisu e-pošte), PR Newswire RSS, Telegram. GlobeNewswire (403) in Business Wire (prazen vir) odstranjena, ker nista brezplačna (BL-059).
- notify ne izpisuje več Telegram žetona (`httpx` na WARNING), log očiščen. Migracija 0010 (`news_item.external_id` daljši za URL guid) na živi bazi.
- BL-034: Stooq privzeto izklopljen (JS izziv, ki ga ne obidemo).
- BL-066: EV/EBIT iz `evRevenue / operatingMargin` (Finnhub ne vrne `ebitTTM`); MSFT 25,7, 27 letnih točk.
- BL-091: Yahoo `funds_data` za UCITS: pozicije in sektorji za vse, TER manjka za Vanguard, `categoryName` vedno prazen.
- BL-095, BL-096: TER in ime indeksa iz `ucits_etfs.yaml` (KIID izdajatelja ima prednost pred Yahoo, z lastnim `ter_source`/`ter_as_of`, migracija 0011). VWRA/VWCE 0,14 % iz Vanguard KIID 2026-07-28.
- BL-100 končan: modeli teze, različice, trditve in dogodki (migracija 0012), API (osnutek iz končane analize, urejanje osnutka, izrecna potrditev, status trditve z razlogom in dokazi), SCR-09 seznam in podrobnosti, gumb "Ustvari osnutek teze" na SCR-06. Živi preizkus: osnutek teze ASML iz zagona `26e4dff1…` (6 trditev) čaka na tvoj pregled in potrditev.
- Migraciji 0011 in 0012 na živi bazi (varnostna kopija `C:/Users/Jan/Documents/preza-backups/preza_pre0012_20261025.dump`, pisci ustavljeni, reviewer APPROVE).
- BL-092: globoka analiza ASML uspešna prek MiniMax v 1501 s (Underweight, 6 sprožilcev). LiteLLM padci: `cloud-quick` → `cloud-deep` → `local-fast`.
- Testi web: 58 enotskih, e2e teze 4 (Playwright z `CHROMIUM_PATH` na chromium-1234; `analysis.spec.ts` potrebuje demo podatke, BL-162).
- Delo je delegirano OpenCode Sol agentom (general, architect), diff in teste je preveril glavni agent.

**Odločitve:** teza nastane šele na klik iz končane analize, sprožilci ostanejo besedilo (brez negiranja in parsanja številk), potrditev različice ne potrdi trditev, status trditve spremeni samo uporabnik z razlogom in dokazom.

**Odprto:**
- BL-097: `cloud-quick` (OpenCode Go) zavrača klice brez glave `x-opencode-session`; zdaj gre prek MiniMax. Potrebna je tvoja odločitev o ponudniku.
- BL-161: `expected_version` pri urejanju osnutka preverja različico, ne urejanj (spletni vmesnik pošlje samo spremenjene trditve).
- IB Gateway ni povezan (BL-023). Seznam spremljanja je prazen, zato Radar ne daje signalov.

**Naslednji korak:** BL-101 tedenski pregled tez in signal `thesis_break`.

---

## S-005 · 2026-10-22 · M3 zaključek in M4 Globoka analiza

**Cilj:** BL-068 do BL-070 in mejnik M4 (samostojno, brez uporabnika).

**Narejeno:**
- BL-068: signali `entry` in vrstica vstopov v Telegramu. BL-069: cona, stop in lestvica na grafu instrumenta. BL-070: kartica "V coni" na Pregledu.
- BL-080 do BL-082: nova storitev `services/agents` (paket `preza_agents`, lasten arq delavec na `arq:agents`). TradingAgents v0.7.0 iz gita, modeli prek LiteLLM vlog, `vendor_local` servira posnetek naše baze (brez Yahooja), koraki v `analysis_step`, SSE z `Last-Event-ID` (ADR-0011).
- BL-083: ETF analitik (profil sklada, prekrivanje skozi ETF-je v portfelju, TA-Lib, dva klica vlog), tedenska osvežitev profilov.
- BL-085: SCR-06 Analiza in CMP-12 AgentTimeline v živo, gumb "Globoka analiza" na instrumentu (Sonnet subagent).
- BL-090: globok ročni predlog ustvari zagon agentov s hipotezo; po zagonu jo en klic izrecno potrdi ali ovrže. Panel "Tvoja hipoteza".
- BL-089: kartica odločitve: deterministična kontrolna ocena, prepričanje, razred velikosti, sprožilci, `delta_note`. Razlika z oceno agentov zniža zaupanje (`control_disagrees`).
- BL-093: dnevni limit globokih analiz (privzeto 6) s prikazom porabe.
- BL-086: regresijski testi na 5 fiksnih posnetkih z "golden" datotekami.
- BL-088: kakovost poslovanja in dividende iz Finnhuba, kakovost v kontrolni oceni.
- Testi: API 162, agenti 31, web 18 enotskih, e2e 22.

**Odločitve:** ADR-0011 (ločena storitev agentov, lokalni vendor, SSE iz tabele, ETF cevovod, hipoteza po zagonu, kartica odločitve).

**Odprto:**
- BL-092: živi zagon prek LiteLLM z OpenCode Go/MiniMax (klici orodij, čas, cena). Prvi pravi preizkus M4.
- BL-091: Yahoo `funds_data` za UCITS kotacije. BL-066: nova polja Finnhuba. BL-059: viri novic.
- BL-023 živi IB Gateway, BL-160 zagon na tvojem strežniku.

**Naslednji korak:** BL-092 na tvojem strežniku (`docker compose up agents`), nato M5 Teze (sprožilci iz kartice odločitve postanejo trditve teze).

---

## S-004 · 2026-10-22 · Prevodi in M3 Vstopi

**Cilj:** BL-055 in mejnik M3 (samostojno, uporabnik ne more poganjati na svojem računalniku).

**Narejeno:**
- BL-055: povzetki dogodkov in razlogi signalov se prevedejo v jezik uporabnika (`local-fast`, en klic za do 8 povzetkov). Angleški izvirnik ostane kanoničen, prevod ima oznako "prevedeno" in izvirnik ob prehodu z miško. Telegram uporablja prevod.
- BL-060: pravila vstopov v `rules.yaml`, indikatorji s TA-Lib, test enakosti s trading-signals (Haiku subagent je pripravil posnetek).
- BL-061: pasovi vrednotenja (P/E, EV/EBIT, FCF donos proti 5 letom) iz Finnhuba in DCF iz veje `legacy` (Sonnet subagent).
- BL-062: `dip_analyst` (vzrok padca, `local-reason` → `cloud-quick`), dnevni tek vstopov ob 22:00 UTC, signal `entry` samo z nedotaknjeno tezo, `thesis_break` za temeljni vzrok pri poziciji.
- BL-063: lestvica postopnega nakupa (40/30/30, koraki po 1 ATR, nikoli nad trgom ali pod stopom).
- BL-064: SCR-03 Vstopi z zemljevidom vstopov (OV-05), cono in stopom (CMP-07), vzrokom (CMP-10), pravili, vrednotenjem in lestvico z zneskom (CMP-15). Preverjeno na namizju, telefonu in v temni temi.
- BL-065: izidi signalov po 1/5/20/60 dneh z alfo, MFE in MAE (Sonnet subagent), `/entries/outcomes`.
- Demo: vstopi z demo vrednotenjem in demo vzroki; ponovni seed zamenja demo Radar in vstope.
- Testi: API 151, web 11 enotskih, e2e 13.

**Odločitve:** ADR-0010 (TA-Lib, pravila kot konfiguracija, politika signalov za vstope).

**Odprto:** BL-066 polja Finnhuba na pravem omrežju; BL-059 viri novic; BL-023 živi IB Gateway; BL-160 zagon na tvojem strežniku.

**Naslednji korak:** M4 Globoka analiza (TradingAgents) ali manjše naloge BL-068 do BL-070.

---

## S-003 · 2026-10-22 · M1 in M2 v oblaku, brez uporabnika

**Cilj:** nadaljevati samostojno (uporabnik ne more poganjati na svojem računalniku).

**Odločitve (uporabnik):** Claude ni v cevovodu (brez API), `cloud-deep` = MiniMax z rezervo OpenCode Go. OpenCode Go modeli so javni. Tailscale je na vseh napravah. Ollama modele uporabnik določi kasneje. Za manjše naloge uporabljam manjše subagente (Sonnet, Haiku).

**Narejeno (M1):**
- API: pogodba virov + skupni testni nabor, usmerjevalnik s kvotami in rezervo (IB Gateway → Yahoo → Stooq), IBKR Flex odjemalec in parser (ponovni poskusi ob 1019, omrežne napake kot FlexError), tabele in migracija 0002 (hypertable na Timescale), UCITS seznam, `/instruments`, `/bars`, `/portfolio`, `/portfolio/sync`, `/watchlist`, arq opravila (Flex 05:15 UTC, sveče 21:30 UTC), demo podatki (`seed_demo`).
- Web: Portfelj (toplotni zemljevid, tabela, gotovina, sinhronizacija, stanje zadnje sinhronizacije), Watchlista (dve ravni, opombe, od dodaje, razveljavitev), Instrument (sveče, SMA50/200, volumen, RSI, ATR, 52-t. vrh/dno, lokaliziran graf), kukalo, predogled in ⌘K na pravem API.
- Testi: API 30 (vključno z integracijskimi na Postgres in preizkusom na TimescaleDB), web 11 enotskih, e2e 11 (Sonnet subagent je dodal 5 in našel napako v ⌘K, popravljeno).
- Preverjeno: migracije na TimescaleDB (hypertable), pot API → Redis → worker, napaka pri Flex sinhronizaciji se zapiše in prikaže.

**Narejeno (M2):**
- Viri novic: RSS/Atom, Finnhub, SEC EDGAR (napisal Sonnet subagent, 25 testov). Cevovod Radarja: shranjevanje po kanoničnem URL, grozdenje (vektorji ali besede), triaža z `local-fast`, odziv cene (z) in pozornost, ocena priložnosti, signali; govorica ostane "spremljaj" do uradne potrditve.
- API: `/radar/events` (trije pogledi), `/signals`, `/proposals` (analiza predloga: številke izračuna koda, model presodi hipotezo).
- Telegram bot (napisal Sonnet subagent): obvestila s tihimi urami in dnevnim limitom, gumbi, `/predlog`, jutranji povzetek.
- Web: Radar, Signali, Predlogi na pravem API.
- Napake, ki so jih našli testi in posnetki zaslona: proxy ni prepuščal novih poti; `POST /proposals` je vedno vrnil 500; manjkajoči Redis je zrušil zahtevo. Vse popravljeno.
- Testi: API 87, web 11 enotskih, e2e 11.

**Omejitve okolja (ne repoja):** omrežna politika blokira opencode.ai, api.minimax.io, sec.gov, stooq.com, Yahoo in ghcr.io bloke; Docker Hub omejuje (429), Googlov mirror deluje; build kontejnerji nimajo proxyja, zato slik API/web tu ni bilo mogoče zgraditi. Živih podatkov tu ni bilo, testi uporabljajo ročno sestavljene posnetke formatov.

**Odprto:** BL-023 živi IB Gateway, BL-027 ETF holdings, BL-011 imena modelov, celoten `docker compose up` na tvojem strežniku (BL-160).

**Naslednji korak:** M3 Vstopi (pravila, vzrok padca, lestvica) in BL-055, BL-056.

---

## S-002 · 2026-10-22 · Napreden UX, ročni predlogi, M0

**Cilj:** odločitve iz pregleda prototipov, napreden React UX, ročni predlogi, mejnik M0.

**Narejeno:**
- Pravila: DESIGN §8 (motion sistem MO-01–MO-10), §9 (povezovanje LX-01–LX-08), §10 (pregledi OV-01–OV-07), §11 (ročni predlogi, SCR-12, CMP-30). ADR-0008 (UCITS), ADR-0009 (Motion UX). Ime Preža in model Qwen 3.8 27B (4-bit) potrjena.
- **M0 zgrajen:**
  - `services/api`: FastAPI, `/health`, `/system/status` (sonde za 7 servisov s časovno omejitvijo), Alembic (Timescale + pgvector), arq worker, izvoz OpenAPI. 6 testov, ruff, mypy strict.
  - `apps/web`: Next.js 16 lupina (stranski meni z drsnim indikatorjem, spodnja navigacija na telefonu, glava s stanjem sistema), svetla/temna/sistemska tema brez utripa, SL/EN (next-intl, 220+ ključev, preverjanje enakosti), ⌘K paleta, kukalo v URL, EntityLink s predogledom, navzkrižno poudarjanje, AnimatedNumber, Treemap, PulseTimeline, Funnel, RegimeStrip, Sparkline, kartice signalov z razširitvijo in razveljavitvijo, obrazec za ročne predloge, stran `/ux`. 9 enotskih testov, 6 e2e testov (Playwright, namizje + telefon).
  - `infra`: Docker Compose (postgres, redis, litellm, api, worker, web, ib-gateway v profilu `broker`), LiteLLM 5 vlog s fallbacki.
  - CI (GitHub Actions): API, web (i18n, tipi API, lint, tipi, testi, build, e2e), preverjanje compose.
- Najdena in popravljena napaka hidracije: Node in Chromium različno ločita 4-mestna števila v slovenščini, zato `useGrouping: "always"`.

**Odločitve (uporabnik):** UCITS ETF-ji, ime Preža, Qwen 3.8 27B 4-bit, napreden React UX z animacijami in povezanimi pogledi, ročni predlogi v analizo.

**Odprto:**
- Celoten `docker compose up` v tem okolju ni bil preizkušen (ni Docker daemona); posamezni servisi, build in e2e so preizkušeni (BL-160).
- Imena modelov OpenCode Go v `.env` preveri na `/models` (BL-011).
- BL-012, BL-013, BL-016 so na tvoji strani (GPU naprava, Claude kredit, Tailscale).

**Naslednji korak:** BL-160 (zagon na tvojem strežniku), nato M1: Flex, IB Gateway, svečke, Portfelj (SCR-08), Instrument (SCR-05).

---

## S-001 · 2026-10-22 · Analiza, zasnova, pravila, prototipi

**Cilj:** izbrati osnovo iz odprtokodnih repojev, zasnovati rešitev, postaviti pravila projekta in UI prototipe.

**Narejeno:**
- Analiza 6 kandidatov: LEAN, TradeMaster, trading-signals, TradingAgents, Vibe-Trading in IBKR API-ji → [`docs/research/2026-10-22-analiza-kandidatov.md`](./docs/research/2026-10-22-analiza-kandidatov.md).
- Podrobna zasnova in seznam prevzemov → [`docs/research/2026-10-22-zasnova-resitve.md`](./docs/research/2026-10-22-zasnova-resitve.md).
- Prejšnja koda premaknjena na vejo `legacy`. Na delovni veji je nova struktura monorepa.
- Pravila: README, AGENTS, BRAND, VOICE, DESIGN, PLAN, BACKLOG, SESSIONS, ADR-0001 do ADR-0007.
- Osnova i18n: `apps/web/messages/sl.json` in `en.json`.
- UI prototipi na Artifact platnu (BL-003): 7 zaslonov + tokeni, preklop teme in jezika, povezave med zasloni. Kopija v `design/canvas/`.
- Pregled starega projekta `PksOck/trading-list` (PHP): samo izkušnje in model podatkov → [`docs/research/2026-10-22-trading-list-prevzem.md`](./docs/research/2026-10-22-trading-list-prevzem.md). Novi BL-018, BL-032, BL-033, BL-088, BL-089.

**Odločitve (uporabnik):**
- Dolgoročno trgovanje, občasno kratkoročno in opcije. Podatki v realnem času niso potrebni.
- Fokus: priložnosti iz novic in špekulacij ter dobre (ponovne) vstopne točke, za delnice in ETF-je.
- Docker lokalno. GPU naprava v LAN s 24 GB VRAM, Qwen 3.8 27B (4-bit).
- Naročnine: Claude **Pro**, OpenAI, OpenCode. IBKR PRO.
- Radar v treh pogledih: Novi predlogi (širše), Watchlista, Portfelj.
- Obvestila prek Telegrama.
- Slovenščina privzeto, preklop na angleščino. Svetla in temna tema.
- Stari projekt ni predloga: gradimo na novo in bolje.

**Odprto:**
- Točna verzija lokalnega modela in hitrost triaže (BL-012).
- Višina Claude Pro Agent SDK kredita (BL-013).
- Delovno ime "Preža": potrdi ali zamenjaj (BRAND.md §1).
- Pregled prototipov (BL-004).
- Dostopnost ameriških ETF-jev za EU malega vlagatelja (BL-018). Prototipi zato uporabljajo UCITS ETF-je (VWRA, EQQQ, IUES).

**Naslednji korak:** BL-004 (pregled prototipov), nato M0 (BL-006 do BL-016).

---

## Predloga

```markdown
## S-xxx · LLLL-MM-DD · <kratek cilj>

**Cilj:**
**Narejeno:** (z referencami BL-xxx, commit/PR)
**Odločitve:** (+ ADR-xxxx, če nastane)
**Odprto:**
**Naslednji korak:**
```
