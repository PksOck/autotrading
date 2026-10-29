# Celovita nadgradnja uporabniške izkušnje Preže — načrt izvedbe

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or, if the user chooses delegation, superpowers:subagent-driven-development. Implement one independently reviewable task at a time; do not infer implementation approval from this planning document.

**Cilj:** Preža postane gost, prilagodljiv in razumljiv raziskovalni delovni prostor: uporabnik hitro primerja instrumente, vidi kaj se je spremenilo, razume dokaze in nadzoruje obdelave.

**Arhitektura:** Nadgradimo obstoječe zaslone in skupne komponente, ne zamenjamo aplikacije. Enotne pogodbe virov/časov/stanj, tabel in URL filtrov podpirajo module; razporejanje ter izračuni ostanejo v zaledju. Vsak sklop se dostavi samostojno in preveri na izoliranem demo skladu.

**Sklad:** obstoječi Next.js 16, React 19, TypeScript strict, TanStack Query, Radix, Motion, next-intl, FastAPI/Pydantic v2, SQLAlchemy/Alembic, PostgreSQL in arq.

**Specifikacija:** ta dokument vsebuje predlagano zasnovo in izvedbene sklope; temelji na uporabnikovih zahtevah 2026-10-28, DESIGN/VOICE/BRAND, ADR-0004/0006/0009/0011/0013/0014 ter neodvisnem [pregledu Astra](../../research/2026-10-28-astra-ux-review.md). Prejšnji [ožji načrt](./2026-10-28-nastavitve-analize-portfelj.md) je dopolnilno tehnično gradivo; njegove BL-161–171 oznake so zastarele in se ne smejo prenesti v aktualni backlog.

## 1. Obseg, podlaga in status

**To je velik načrt UX/UI, ne izvedba.** Uporabnik je po kratkem preusmerjanju v manjše popravke izrecno popravil obseg nazaj na celovit UX/UI načrt. Nobena aplikacijska sprememba ni del tega dokumenta. Oblikovna pravila v DESIGN se spremenijo ob potrditvi oziroma izvedbi izbranega sklopa; ta dokument jih še ne nadomesti.

Aktualna pregledana koda je Claude veja `claude/preverjanje-podatkovnih-povezav-53ab37`, commit `1855eb8`, pod `.claude/worktrees/preverjanje-podatkovnih-povezav-53ab37/`. Osnovni `master` na `c0c15ae` je starejši. Claudov `.env.example` ima nepovezano lokalno spremembo; ne prevzemamo je. Pred izvedbo ponovno preveri HEAD, delovna drevesa in aktivne agente. Ne prepisuj sprememb vzporednih sej.

Pregled z brskalnikom je potekal na odprti aplikaciji `http://localhost:3000`. Ločeni demo `http://localhost:3100`, definiran v `infra/docker-compose.demo.yml`, je zavrnil povezavo. Zato to ni trditev o popolnem testu namenskega demo sklada. Aplikacija na :3000 se je med sejo posodobila in dobila podatke portfelja; opažanja so časovni posnetki, ne zamrznjen benchmark. Osebni zneski, računi in vsebine izpisov niso prepisani v ta dokument.

Namizni pregled: 1440 × 1000. Ciljni telefonski pregled: 390 × 844; pregledana Radar in navigacija, z vzorčnim preklopom svetle/temne/sistemske teme ter povrnitvijo na sistemsko. Vsi zasloni v obeh temah in na vseh širinah še niso testirani. To je prevzemna obveznost, ne opravljeno preverjanje.

**Pregled načrta (Claude, 2026-10-28, commit `1855eb8`) in uporabnikove odločitve:**

- Trditve iz §2 so preverjene v kodi: napačen filter signalov ([`routes/signals.py`](../../../services/api/preza/routes/signals.py) filtrira in omeji pred označitvijo poteka), povezave `peek=signal:` v Vstopih, obvestilih in Telegramu, ADR-0013 48 px, omejitev seznama analiz na 100 in sort samo po datumu.
- Uporabnik je potrdil: oba hrošča se popravita **pred** valovi UX kot ločeni nalogi BL (§8, Val −1).
- Demo sklad :3100 obstaja in je bil ustavljen, ne pokvarjen. UX-01 je zagon, preverjanje in scenariji, ne nova gradnja.
- Dividende: vir je Flex izpis, ki ga uporabnik razširi z dodatnimi sekcijami (§9a). Prihodnji donos se izračuna deterministično iz trenutnih pozicij.
- Watchlista in lastne pozicije dobita isto preverjanje podatkovnih virov (UX-00, §9a) pred tabelami.
- Predloge ADR (§12) zapiše Astra v ločeni seji; ta načrt vsebuje Claudovo mnenje.
- Načrt je kopiran na Claude vejo; kopija v osnovnem checkoutu na `master` (`c0c15ae`) je starejša. Vnos BL-188 v tamkajšnjem nezapisanem BACKLOG se ob prenosu doda na tej veji, da se BACKLOG ne spre z BL-182–187.

**Pomembno glede ID-jev:** na aktualni veji so BL-161–187 že zasedeni. Ta načrt uporablja neodvisne oznake UX-01–UX-20. Ob začetku implementacije se naloge preslikajo na tedaj proste BL-ID-je. S tem ne rezerviramo številk mimo sočasnega dela.

## 2. Glavne ugotovitve z dokazom

| Dokaz | Opaženo | Posledica za načrt |
|---|---|---|
| Živo + koda | Pregled uporablja vzorčni režim, utrip, lijak in del signalov; dejanski signalni nabiralnik je bil prazen | Resnično, vzorčno, manjkajoče in napaka morajo biti ločena stanja; brez tihega nadomestila podatkov |
| Živo | Predlogi izpisujejo surovi poškodovani JSON, analize pa velik blok tehnične napake ponudnika | Uporabniško sporočilo, ločena diagnostika, jasen neuspeh in ponovni poskus |
| Živo | Watchlista porabi velik del vrstice za tri gumbe; nima stolpcev o vrednotenju/dividendah | Nastavljiva tabela, gostota, podatkovni profili, navpična kratka dejanja |
| Živo | Analize že imajo tabelo, tri horizonte in dokaze za/proti; še vedno veliko ponovljenih instrumentov | Obstoječe komponente izboljšamo s filtri, zadnjim uspešnim zagonom, razlago razhajanj in kontekstom časa |
| Živo | Vstopi pri enem kandidatu kažejo zelo velik zemljevid; vzrok je »Neznano«, ob njem pa »Teza drži« | Prilagodljiva višina vizualizacije in ločena gotovost vzroka/stanja teze |
| Živo na telefonu | Izbor drugega dogodka v Radarju spremeni podrobnosti, a te ostanejo za celotnim seznamom, več kot 20.000 CSS px pod vidnim območjem | Mobilni detail kot ločen zaslon ali celozaslonska plošča, ne vsebina za dolgim seznamom |
| Živo | Instrument WM nima izpolnjene valute/borze/imena, glava pa prikazuje dolarski znak | Identiteta kotacije in eksplicitna neznana valuta, brez ugibanja prikaza |
| Živo + koda | Portfelj ima večvalutne/večračunske vrstice in gotovino, brez primerne izbire računov v tabeli | Konsolidirani in računski pogled, pojasnjena osnova vrednosti in dnevne spremembe |
| Živo | Teze in Uspešnost delujeta; Nastavitve in Opcije sta rezervirana zaslona | Ne načrtujemo ponovne izdelave M5; Nastavitve razvijemo, Opcije ostanejo kasnejši M6 |
| Koda | Signalne povezave uporabljajo `peek=signal:...`, predogled podpira instrument; fallback izbire Radarja/Vstopov lahko zamenja zahtevan objekt | Najprej popravimo identiteto in navigacijo do dokaza |
| Regresijski dokaz na izolirani bazi | Filter `/signals?status=new&limit=1` lahko vrne `status=expired` | V načrt vključimo pogodbeno pravilnost pred filtri/paginacijo; popravek v tej seji ni izveden |

Prevodne ali tržne trditve iz novic med pregledom niso bile finančno preverjene. Preverjali smo prikaz in pot do vira, ne njihove resničnosti.

## 3. Predlagana smer in alternative

| Možnost | Kaj prinese | Omejitev |
|---|---|---|
| Samo manjši gumbi in dodatni stolpci | Hitro izboljšanje gostote | Ne popravi napačnih povezav, vzorčnih nadomestkov, napak in avtomatike |
| **Postopna nadgradnja obstoječe aplikacije po uporabniških poteh** | Enoten vzorec primerjave, dokaza in dejanja; manj ponavljanja; varna dostava po sklopih | Zahteva uskladitev API in UI pogodb |
| Celoten nov terminal oziroma prenova od začetka | Največ svobode postavitve | Podvoji delujoče funkcije, poveča migracijo in odloži uporabno izboljšanje |

Priporočilo je srednja pot. Ohranimo mirno identiteto Preže, obstoječe barve in tipografijo ter izboljšujemo vsebino, hierarhijo, gostoto in pot od informacije do raziskave. Nov meni se doda le, kadar ima samostojno pogosto opravilo.

## 4. Informacijska arhitektura in glavne poti

Namizna navigacija ohrani znane poti, lahko pa jih vizualno združi:

- **Dnevno delo:** Pregled, Radar, Vstopi, Signali.
- **Raziskava:** Predlogi, Analize, Teze.
- **Moje naložbe:** Portfelj in Uspešnost.
- **Upravljanje:** Nastavitve; sistemske težave dosegljive tudi iz glave.
- Opcije z jasno oznako »V pripravi«; ne ustvarjamo navidezno delujočega M6.

Portfelj obdrži `?tab=positions|watchlist` in dobi `analyses|dividends`; izpostavljenost je sprva panel Pozicij, ne peti prazen zavihek. Obstoječe povezave ostanejo veljavne.

Pet poti, po katerih preverjamo uspeh:

1. Pregled → nov dogodek → uradni vir → instrument → predlog/analiza → nazaj z ohranjenimi filtri.
2. Watchlista → primerjava izbranih metrik → predogled → analiza → spremljanje izida.
3. Analiza → kaj se je spremenilo → dokazi → osnutek teze → uporabnikova potrditev → pregled teze.
4. Portfelj → pokritost analiz ali dividende → posamezen instrument/knjižba → povratek na isti račun in obdobje.
5. Opozorilo ali Telegram → točen signal → dokazi → uporabnikova odločitev; brez zamenjave objekta in brez oddaje naročila.

Mobilno ohranimo obstoječih pet spodnjih mest. »Več« odpre kratek navigacijski seznam; paleta iskanja ostane ločeno orodje. Obstoječih Ctrl+K in prilagoditev za Android/Windows ne implementiramo ponovno.

## 5. Pravila skozi celotno aplikacijo

### 5.1 Podatek, ocena in kakovost

Vsak blok razlikuje **izmerjeno dejstvo**, **deterministični izračun**, **oceno modela** in **uporabnikovo trditev**. Vir, čas podatka in način izračuna so dosegljivi iz vrednosti. »Pridobljeno ob« ni »tržni podatek do«.

Pogodba `DataMeta`: `source`, `as_of`, `fetched_at`, `availability`, `reason_code`, po potrebi `coverage` in `basis`. Stanja so `loading|ready|empty|error|stale|partial`; neznano ni nič in neuspešna poizvedba ne pomeni, da uporabnik nima pozicije. Datum posnetka analize ostane zgodovinski; današnja cena je ločen blok.

Osnova cen se navede kot zadnja zaključna cena, datum seje in valuta. Pri P/E označimo TTM ali forward obdobje; dividendni znesek potrebuje valuto in TTM/letno indicirano/zadnje izplačilo. ETF ne dobi podjetniških kazalnikov brez namenskega vira.

### 5.2 Tabele in primerjava

Enoten `ColumnDefinition` register: ID, prevod, podatkovni ključ, format, širina, možnost sortiranja in uporabnost za delnico/ETF. `TableViewPreferences`: version, vidni in pripeti stolpci, vrstni red, širine in gostota. Izbor stolpcev je po modulu, ne ena vsiljena postavitev za vse zaslone. Razvrščanje ni v lokalnih preferencah: URL je njegov edini vir resnice.

- Gumb »Stolpci«, prednastavitve, ponastavitev, razvrščanje, filtriranje, števec zadetkov in paginacija.
- Pripet instrument in ozek stolpec dejanj; pomembni zneski desno, monospace; brez obveznih mini grafov v vsaki vrstici.
- Prva izdaja shrani preference lokalno v versioniran ključ po modulu. Jasno velja za ta brskalnik; če se kasneje zahteva mednapravno usklajevanje, se doda preverjen uporabniški profil v bazi, ne navidezni račun.
- Filtri/izbor/stran/razvrščanje so v URL, ker se morajo obnoviti ob vrnitvi in deliti; gostota in stolpci so preference. Ob spremembi filtrov se stran ponastavi. Filtrira se celoten nabor na strežniku, ne samo prvih 30 rezultatov.
- Opozorila govorica, neuspeh, zastarelost in delni podatki ostanejo ob identiteti vrstice tudi ob skritju povezanega stolpca; osebni pogled jih ne sme odstraniti.
- Manjkajoče številke na koncu obeh smeri razvrščanja; denarnih številk različnih valut ne primerjaj brez iste osnove.
- Na telefonu ne stiskamo vseh stolpcev. Kartica ali zmanjšan izbor odpre dodatne metrike; opcijski horizontalni scroll je znotraj tabele, ne celotne strani.

### 5.3 Dejanja, gostota in stanja

Namizna manjša dejanja 28–32 px; običajna 36–40 px. Obstoječi ADR-0013 zahteva **48 px za dotik**, zato to ohranimo tudi pri kompaktni gostoti. To nadomesti starejši predlog 44 px v ožjem načrtu. Pri Watchlisti pripravimo dve različici: v udobnem/razširjenem prikazu kratki gumbi navpično po uporabnikovem predlogu; v kompaktni tabeli eno vidno primarno dejanje in meni preostalih. Trije navpični gumbi bi sami zahtevali vsaj 84–96 px višine oziroma 144 px na dotiku, zato jih ne obljubljamo znotraj 32–40 px vrstice. Rednih dejanj ne skrijemo samo ob hoverju. Končno postavitev uporabnik preveri na prototipu pred širjenjem vzorca.

Vsaka mutacija pokaže pending na pravem objektu, prepreči dvojni klik in ob napaki ohrani prejšnje podatke. Razveljavitev obnovi isti ID, čas dodaje, ceno dodaje, oznake in opozorila; novo ustvarjanje ni enakovredna razveljavitev. Tekoči proces ni lažno označen »končano« po oddaji v vrsto.

Tehnična napaka se preslika v kratko prevedeno sporočilo z dejanjem in korelacijskim ID. Diagnostika je razširljiva in očiščena; noben surov odgovor ponudnika ali interni naslov ni osnovni uporabniški rezultat.

### 5.4 Mobilno, tipkovnica in grafi

Pri Radarju/Vstopih: namizje seznam in podrobnosti, telefon podrobnosti kot zaslon z »Nazaj na rezultate« ter ohranjenimi filtri/scrollom. Dialog ima fokus, Escape, vidno zapiranje in varen gumb Nazaj; brez več prekrivnih dialogov in vsebine pod spodnjo navigacijo.

Zgoščena glava telefona ohrani iskanje, eno glavno dejanje in status. Jezik/tema sta dosegljiva v meniju oziroma nastavitvah; sprememba razporeditve ne odstrani možnosti. Graf dobi berljiv besedilni povzetek; pri enem kandidatu je kompaktnejši in se lahko razširi. Vsi grafi ne potrebujejo iste višine.

Kontrast in pomen barv sledita tokenom. Fokus, semantika tabel, puščice zavihkov, obvestila `aria-live`, reduced-motion in 200-% povečava so prevzemni pogoji. Gostota ne sme pomeniti slabše čitljivosti.

## 6. Nadgradnje po zaslonih

### Pregled `/`

Prva vrstica: stanje podatkov, novosti za pregled, stanje portfelja, procesi/analize v teku. »Novo danes« temelji na resničnem lokalnem dnevu in istem naboru signalov kot nabiralnik. Ob praznini pokaže, kaj še ni teklo in kam naprej; ne izmisli priložnosti. Tržni režim in lijak sta podatkovna modula z dokazljivo metodologijo, sicer jasno neaktivna ali demo. Uporabnik lahko module skrije in spremeni njihov vrstni red; ta možnost pride po pravilnosti podatkov.

### Radar `/radar`

Kompaktni tok s kratkim naslovom in največ dvema vrsticama povzetka, datumskimi skupinami in razliko med objavo ter zadnjo posodobitvijo. Filtri: obseg, simbol, tip dogodka, čas, vir, status potrditve, ocena; napredni filtri se zložijo. Shrani poglede »Moje pozicije«, »Watchlista«, »Novo od zadnjega pregleda«. Pojem »Potrjeno« zahteva dokaz uradne potrditve, ni samo `not is_rumor`. Detajl pokaže izvorno in prevedeno besedilo, povezave, povezane instrumente in razlog pomembnosti za uporabnika. Pripet objekt se pridobi po ID neodvisno od strani/filtra.

### Vstopi `/entries`

Kompakten seznam najprej odgovori »zakaj je tu«, oddaljenost do cone, valuta, svežina in stanje teze. Zemljevid je dopolnilni, prilagodljiv številu kandidatov. Ločimo neznan vzrok, odsotno tezo in potrjeno nedotaknjeno tezo. Lestvica ima valuto, pojasnjeno razmerje in stanje nezadostnega zneska; brez nove logike za samodejna naročila. Izbirni stolpci: cena, od vrha, ATR do cone, pravila, vrednotenje, vzrok, teza, zadnja analiza.

### Signali `/signals`

Enoten nabiralnik s statusi vključno s poteklimi/vsemi, števci, simbolom, virom, tipom in horizontom. Povezava iz Telegrama odpre pravilen signal, ne splošnega seznama. Razširitev pokaže rationale/evidence, razliko signal vs predlog vs analiza. Prvo množično dejanje je zavrnitev z razveljavitvijo; sprejem posameznega signala ohrani omejitev govoric in nikoli ne pomeni naročila. »Pregledano« za signale še ni domenski status in se ne doda kot sinonim zavrnitve ali sprejema; ločen read-state je poznejša izrecna odločitev. Filtriranje statusov mora upoštevati potek pred paginacijo.

### Predlogi `/proposals`

Zgodovina ima instrumente, hipotezo, globino, stanje hitre presoje in globokih analiz, rezultat, vir, čas in naslednje dejanje. Več podprtih instrumentov dobi sledljivo povezavo do vsake analize. Napačen izhod modela ni verdict. Retry je omejen/idempotenten, ponavljajoče kartice pa se najprej raziščejo po ID-jih, ne brišejo po besedilu. Obrazec ohrani osnutek, potrdi kotacijo/valuto, pokaže posledico globine in izvor dogodka. Slika kot vhod se naveže na obstoječi BL-186; OCR ni predpogoj za osnovno UX nadgradnjo.

### Instrument `/i/[symbol]` in predogled

Glava: simbol, polno ime, kotacija/borza, valuta, vrsta, zadnja cena in tržni datum. Primarno »Nov predlog«, sekundarno »Globoka analiza« z razlago obsega/kvote; odpravimo dva nejasna gumba »Analiziraj«. Raziskovalni zavihki/paneli: Pregled, Vrednotenje in kakovost, Dividende, Dogodki in signali, Analize in teza. Obstoječi graf, kazalniki in ETF profil se ponovno uporabijo. Predogled je kratek povzetek iste pogodbe, ne druga različica številk. Primerjava 2–4 instrumentov z enakimi metrikami je poznejša nadgradnja po podatkovni pogodbi, ne nenačrtovana nova analitična platforma.

### Analize `/analysis`, `/analysis/[id]`

Ohranimo obstoječe tri horizonte in dokaze za/proti. Seznam dobi stanje, zadnjo uspešno na instrument, obseg portfelj/watchlista, datum, stolpce in spremljanje vrste. Razvrstitev zadnje uspešne se izvaja v bazi pred paginacijo. Podrobnosti najprej pokažejo zaključek, omejitve podatkov, kaj se je spremenilo in razlog razhajanja med agentom ter determinističnimi dokazi. Današnja cena in takratni posnetek sta jasno ločena; obe komponenti imata svoj čas. Tehnični koraki/poraba so sekundarni razširljivi del, ne celotna prva stran. Poraba uporabi obstoječi BL-172, štetje poskusov BL-176.

### Portfelj — Pozicije

Nadgradimo delujoč Flex XML uvoz BL-187, ne dodajamo ga znova. Izbira računov, konsolidirano po instrumentu ali po računu, cenovna/osnovna valuta, vir in datum posnetka ter FX pokritost. Neznane pretvorbe ne izginejo iz domnevno celotne vrednosti. Količine ohranijo frakcije; gotovina se združi ali označi po računih. Treemap in tabela temeljita na istem naboru. Izbirni stolpci: količina, nabavna cena, cena/čas, tržna vrednost, teža, P/L znesek/%, dnevna sprememba, dividendni donos, datum/ocena analize in stanje teze. Ne mešamo Flex vrednosti ob starem posnetku z današnjimi spremembami brez navedbe časovne osnove.

### Portfelj — Watchlista

Nastavljiva tabela z osnovno/vrednotenjsko/dividendno prednastavitvijo. Stolpci: cena/valuta, dnevna sprememba, P/E TTM, Forward P/E z obdobjem, denarna dividenda na delnico z osnovo, donos %, payout %, FCF donos, ROE, rast/marža/dolg, cilj, opomba, od dodaje, pregledano in zadnja analiza. Najpogostejši podatki so vidni brez odpiranja instrumenta. Dejanja manjša in navpična; razveljavitev ohrani zgodovino. Aktivna in zaloga idej ostaneta; skupine/oznake postanejo uporabni filtri. Vsebinski vir podatka se najprej preveri, UI ne izmišlja praznih metrik.

### Portfelj — Analize in Dividende

Analize: pokritost aktualnih pozicij, stare/manjkajoče analize, ročni paket, stanje avtomatike in preusmeritev na isti rezultat. Dividende: prejeta bruto izplačila, znani odtegljaji in neto, valuta, obdobje pokritosti, mesečni pregled, letni/računski filter ter originalne knjižbe. Prihodnji koledar in indikativni prihodek sta ločena od prejetega. Akumulacijski ETF ni gotovinsko izplačilo. Pri manjkajočem FX ali davku pokažemo delno vsoto; bruto/neto nista zamenljiva. Davčna napoved in izračun davčnih obveznosti nista vključena.

### Teze `/theses`, `/theses/[id]`

Obstoječi osnutki, potrjevanje različic in tedenski pregledi ostanejo. Seznam dobi status/račun/portfelj, zadnji pregled, datum naslednjega in »potreben pregled«. Ničelni števci aktivnih trditev pri osnutku se zamenjajo z razlago, da še ni aktivne različice. Detajl najprej aktivna teza in odprti predlogi sprememb; zgodovina različic in stari pregledi zloženi. Pogoji veljavnosti/ovržbe se vizualno ločijo; potrjevanje ostane eksplicitno z zaščito verzijskega konflikta. Skupni nabiralnik čakajočih pregledov je filter nad Tezami, ne nov glavni modul.

### Uspešnost `/track-record`

Obstoječe izide, horizonte in kalibracijo dopolnimo z URL stanjem, obdobjem, virom, vzorcem, pokritostjo in metodo. Obdobje privzeto filtrira datum nastanka signala (kohorta), izbrani horizont pa pripadajoči zrel izid; UI poimenuje obe osnovi in prešteje nezrele/izključene. Agregat odpre iste izvorne signale/izide. Jasno ločimo sistemske signale, lastne predloge in dejansko uspešnost portfelja. Pri praznem vzorcu je glavna razlaga, kdaj bodo izidi merljivi; velik panel kalibracije postane sekundaren. Napaka pri nalaganju potrjenih uteži se ne spremeni v trditev »uteži še niso potrjene«. Kalibracija ohrani lastno konfigurirano časovno in populacijsko osnovo, ki je prikazana ob predlogu; sprememba horizonta ali obdobja poročila je ne spremeni tiho. Vpliv predloga pred potrditvijo ostane pojasnjen.

### Nastavitve `/settings`

Razdelki: Videz in prikaz; Podatki in povezave; Procesi in urniki; Samodejne analize; Modeli in omejitve; Obvestila; Spremljani viri. Enotno shranjevanje, validacija, neshranjene spremembe, povrnitev in izid shranjevanja. Stanje sistema loči konfigurirano/povezano/zadnji uspešni tek/svežina. Nobene skrivnosti v UI odgovorih. Vloge LiteLLM ostanejo obvezne; urejevalnik neposrednih ponudniških klicev ni del predloga.

Procesi dobijo vklop, interval ali lokalni dnevni/tedenski urnik, dneve, časovno okno, timezone, zadnji/naslednji tek, razlog odloga in globalno pavzo novih avtomatskih začetkov. Že tekoči tek se dokonča. Avtomatske analize: portfelj/aktivna watchlista/izbor, svežina, cap cikla in dneva, preskok aktivnih instrumentov. Najprej predogled ciljev in učinkov; privzeto izklopljeno. Tehnična podrobnost schedulerja je v ožjem načrtu; obstoječi croni in recovery se ne izvajajo dvojno.

### Opcije in oblikovni sistem

Opcije ostanejo M6 z razumljivim razlogom/obsegom; finančnih strategij in naročil ne dodajamo v UX nadgradnjo. `/ux` postane interni katalog novih tabel, gumbov, stanj, barv, mobilnih panelov in primerov SL/EN z demonstracijskimi podatki. Razvojni SCR/M identifikatorji se umaknejo v razvojni način; niso uporabnikova glavna navigacijska razlaga.

## 7. Izvedbeni sklopi in odvisnosti

Vsak sklop: najprej pogodba in reprezentativen neuspešen test; nato najmanjša implementacija; API/OpenAPI generiranje, kadar je potrebno; ciljna vizualna kontrola; posodobljena DESIGN/VOICE dokumentacija; samostojen commit/PR. Spodnje poti so glede na aktualni repo, ne starejši master.

| ID | Rezultat in glavne datoteke | Odvisnosti | Konkretni prevzem |
|---|---|---|---|
| FIX-A | Filter signalov: potek se upošteva v poizvedbi pred `status` filtrom in limitom (`routes/signals.py`), test regresije | brez; takoj | `/signals?status=new` nikoli ne vrne `expired`; limit šteje samo ujemajoče |
| FIX-B | Povezava do signala: `?peek=signal:<id>` odpre ta signal, tudi če ni na prvi strani ali ima drug status; odsoten ID pokaže »ni najden«, ne prve vrstice | brez; takoj | Test za Vstope, obvestila in Telegram povezavo; Playwright za en scenarij |
| UX-00 | Podatkovna izvedljivost za pozicije in Watchlisto (§9a): katere metrike vir dejansko vrne, pokritost v živi bazi, kaj manjka | brez; vzporedno s FIX | Tabela metrika → vir → stanje (da / delno / ne / plačljivo); odločitev, kateri stolpci gredo v UX-14 in UX-13 |
| UX-01 | Demo za pregled: obstoječi `infra/docker-compose.demo.yml` in `infra/scripts/demo-stack.sh` zaženi, preveri in dopolni s scenariji | ne blokira FIX ali UX-00 | Izoliran :3100, očitna demo oznaka, noben produkcijski volumen/ključ, znan HEAD, scenariji success/failure/partial/stale |
| UX-02 | Metapodatki in prazna stanja: domain sheme, routes, `components/common/`, `InstrumentPreview` | UX-01 | Napaka ni praznina, null ni 0, `as_of` ni `fetched_at`; vsa stanja na treh prvih zaslonih |
| UX-03 | Identiteta in pravilne globoke povezave: `PeekPanel`, `use-peek`, Radar/Entries/Signals, Telegram poti | UX-02/11a | Telegram odpre točen signal; odsoten ID ne odpre prve vrstice; Back obnovi URL in scroll |
| UX-04 | Skupne tabele/filtri/preference: nov `components/table/`, `lib/view-state.ts`, `lib/column-definitions.ts` | UX-02 | Stolpci/vrstni red/gostota po modulu, ponastavitev, numeric sort samo iz URL, klaviatura, brez hidracijskega utripa; obvezna opozorila ostanejo ob skritih stolpcih |
| UX-05 | Lupina, status, dejanja in telefon: `components/shell/`, `globals.css`, `lib/nav.ts` | UX-02/03 | »Več« pokaže navigacijo pred simboli; 48px dotik; status na telefonu; kompaktna glava; ADR-0013 ohranjen |
| UX-06 | Resnični Pregled: `app/page.tsx`, `components/overview/`, agregacijski API | UX-02/03 | Isti števci signalov kot nabiralnik, demo ne prepiše napake; moduli kažejo vir in obseg |
| UX-07 | Uporaben Radar: `components/radar/`, `routes/radar.py`, `services/radar_views.py` | UX-03/04/05 | Datum/vir/potrjenost, kompaktni povzetki, URL filtri in detail po ID; telefon detail takoj dosegljiv |
| UX-08 | Vstopi za primerjavo: `components/entries/`, `routes/entries.py` | UX-03/04/05 | Seznam/zemljevid/telefon isti instrument; neznana teza ne piše »drži«; valuta vidna; en kandidat ne zasede polovice strani |
| UX-09 | Signalni nabiralnik: `routes/signals.py`, `components/signals/`, `SignalCards` | UX-03/04 | Potek pred paginacijo; statusi/števci pravilni; pending in undo; rumor guard velja tudi za skupna dejanja |
| UX-10 | Predlogi in obrazec: `proposals/analyze.py`, worker/routes/domain, `components/proposals/`, store | UX-02/03/04 | Surova napaka ne postane sklep; osnutek preživi zaprtje; retry brez dvojnih zapisov; več simbolov sledljivih |
| UX-11 | Podatkovna kartica instrumenta: `routes/instruments.py`, `services/instruments.py`, `components/instrument/`; 11a minimalna identiteta, 11b paneli | 11a: UX-02, BL-174; 11b: UX-03/11a | Polno ime/borza/valuta ali eksplicitna vrzel; pretekla/današnja cena ločeni; delnice in ETF imajo smiselne metrike |
| UX-12 | Seznam in odločitev analiz: `routes/analyses.py`, `components/analysis/`, domain | UX-03/04/11a | Zadnja uspešna pred limitom, >100 zapisov, stabilni tie-break ID; obstoječi horizonti ostanejo; smiselni razlagi časa in nestrinjanja |
| UX-13 | Pozicije in računi: `services/portfolio.py`, domain, `PositionsPanel`, `PortfolioView` | UX-04/11 | Dva računa, frakcije in FX vrzeli; vidna osnova skupne vrednosti; obstoječ XML uvoz ostane |
| UX-14 | Watchlista z metrikami: fundamentals adapter/domain/services, `components/watchlist/` | UX-04/11a | Forward P/E ni TTM; dividenda valuta/osnova; shranjeni stolpci; preverjena kompaktna/razširjena dejanja; undo ohrani added_at/price/tags/alerts |
| UX-15 | Teze in pregled sprememb: thesis routes/service, `components/theses/` | UX-03/04/12 | Aktivna različica pred zgodovino; osnutek nima lažnih ničel; konflikt različice ne izgubi vnosa; pregled ima diff/dokaz |
| UX-16 | Uspešnost z razlago: track-record/calibration API in komponente | UX-03/04/09 | URL obdobje/horizont, drilldown po agregatu, stanje prazno vs napaka uteži, manual/system ločena |
| UX-17 | Nastavitve povezav/modelov/obvestil/prikaza in viri | UX-02/05, BL-182–185 | Nastavitve z dejanskim API, error/pending/dirty state; status ni le konfiguriran ključ; ne obljublja neizvedenega social konektorja |
| UX-18 | Urniki, avtomatika in portfeljske analize: nov automation modul in UI | UX-12/13/17 | Preview obsega, DST okno čez polnoč, globalna pavza, atomarna kvota, brez dvojnega termina pri dveh workerjih, Redis recovery |
| UX-19 | Dividende: razširjen Flex parser (§9a), nov domain/model/servis/API, `PortfolioDividends` | UX-02/04/13; uporabnik razširi Flex Query | Očiščen Flex vzorec z dodatnimi sekcijami, idempotenten uvoz, storno/davek/FX vrzeli; prejeto, napovedano (accrual) in ocenjeno ločeno; ocena = količina × dividenda na delnico z navedeno osnovo |
| UX-20 | Celovit prevzem, dokumentacija in odprava neskladij | vsi vključeni sklopi | Vseh 5 uporabniških poti, stanja, SL/EN, 390/768/1440, teme, 200% zoom, a11y, regresije in ročni prevzem |

## 8. Vrstni red dostave

**Val −1 — takojšnji popravki in preverjanje virov:** FIX-A, FIX-B in UX-00. Hrošča sta napaki v obstoječi pogodbi in ne čakata demo sklada ali `DataMeta`. UX-00 je samo raziskava in ne spreminja aplikacije. Vzporedno uporabnik razširi Flex Query (§9a).

**Val 0 — zanesljiva podlaga:** UX-01/02, nato UX-11a in UX-03 (UX-03 gradi na FIX-B). UX-11a je samostojna minimalna pogodba internega ID/kotacije/valute in eksplicitne neznanosti, povezana z BL-174; ne zahteva kasnejših raziskovalnih panelov UX-11b. Najprej demo, podatkovna stanja in točna identiteta povezav. Brez tega so novi stolpci samo lepši prikaz negotovih podatkov.

**Val 1 — vsakodnevna uporabnost:** UX-04/05 ter UX-14, UX-12 in UX-10 nad minimalno pogodbo UX-11a. To neposredno odgovarja na uporabnikove težave: Watchlista, filtri analiz, neuspešni Predlogi, gumbi in mobilna navigacija. Raziskovalni paneli UX-11b sledijo ločeno; ne blokirajo osnovnih tabel.

**Val 2 — povezani moduli:** UX-06/07/08/09/11/13/15/16. Dosleden Pregled, Radar in Vstopi, signalni tok, kakovost portfelja in jasni pregledi tez/izidov.

**Val 3 — nadzor obdelav:** UX-17/18. Prvo nastavitve in pošten status, nato urniki, paketne analize in avtomatika. Nov avtomatski proces je ob dostavi izklopljen.

**Val 4 — dividendni pogled in skupni prevzem:** UX-19/20. Dividende lahko tečejo kot ločen sklop po UX-13, če so podatki že na voljo; niso odvisne od dokončane avtomatike.

To niso časovne obljube. Po vsakem valu uporabnik pregleda konkreten demo in lahko spremeni prioritete. Ne prenavljamo vseh zaslonov v enem PR. Delujoče obstoječe funkcije se ponovno uporabijo.

## 9. Podatkovne in izvedbene pogodbe, ki jih UI potrebuje

- **Seznami:** filtri, determinističen sort, pagination/cursor in total/has_more iz iste poizvedbe; obstoječih odzivov ne lomimo nenapovedano. Razširitev pod novim endpointom ali združljivim ovojem zahteva uskladitev vseh odjemalcev/Telegrama.
- **Instrument:** stabilen ID poleg simbola, valuta/borza/vrsta in kakovost identifikacije. Neznani tip ne dobi samodejno USD. Simbol ostane za stare povezave; dvoumnost je eksplicitna.
- **Analize:** snapshot, latest/current blok in poslovna stanja so ločeni; poizvedba »zadnja uspešna« najprej status, nato instrument particija, nato limit. Ne spreminjamo obstoječe logike agentov samo zaradi postavitve.
- **Napake:** code, retryable, correlation_id, user-safe details; agent usage/error_code iz obstoječih BL-168/179 se ohrani. Dodatni popravni LLM klici niso brezplačna UX rešitev.
- **Preference:** lokalne po modulu z migracijo verzije; URL je vir resnice za deljivo stanje, TanStack query ključ vsebuje vse strežniške filtre.
- **Urniki:** trajne politike/izvedbe, stabilen execution ID, atomaren claim, skupna kvota vseh načinov zagona in ponovni pregled politike pred začetkom. Recovery ni obvoz izklopa; začeto opravilo lahko konča zunaj okna.
- **Dividendni dogodki:** originalna valuta, datum knjiženja, broker ID + račun, bruto/odtegljaj/storno in pokrito obdobje; Decimal/numeric. Letna yield metrika ni dokaz osebne prejete dividende.
- **Spremljani viri in slike:** uporabimo obstoječe naloge BL-182–186. UI lahko prikaže konfiguracijo in stanje podpore, ne pa obljubi delujočega YouTube/Instagram/OCR toka pred izvedbo konektorja.

## 9a. Podatkovni viri za pozicije, Watchlisto in dividende

### Stanje temeljnih podatkov (preverjeno 2026-10-28)

Adapter [`fundamentals/finnhub.py`](../../../services/api/preza/fundamentals/finnhub.py) bere `GET /stock/metric?metric=all` (brezplačni paket). V živi bazi ima temeljne podatke **1 od 46 instrumentov** (25 delnic, 11 ETF, 10 `unknown`); edini zapis je `unknown`. Pri njem sta `dividend_yield_pct` in `payout_ratio_pct` prazna. Pokritost je zato prvi problem, ne prikaz: UX-00 ugotovi, zakaj tedenski posel ne zajame pozicij in Watchliste (povezava z BL-174).

| Metrika | Vir | Stanje |
|---|---|---|
| P/E TTM, P/FCF (FCF donos), EV/EBIT, ROE, bruto/neto marža, rast prihodkov, dolg/kapital | Finnhub `metric` | Že zajeto v `metrics`; pokritost v bazi skoraj nič |
| Dividendni donos (indiciran/TTM), payout | Finnhub `metric` | Zajeto; pri edinem zapisu prazno. Preveri na delnicah z dividendo |
| Dividenda na delnico (TTM/letno) | Finnhub `dividendPerShare*` | Ni zajeto; preveri, ali brezplačni paket vrne polje |
| Forward P/E | Finnhub? | Ni zajeto, ni preverjeno. Če ga vir ne da, stolpca ni; ne računamo ga iz LLM |
| Ciljna cena analitikov | Finnhub `price-target` | Verjetno plačljiv endpoint; preveri, sicer izpusti ali pusti kot uporabnikov vnos »cilj« |
| ETF (UCITS) metrike | Finnhub | Pričakovano brez podjetniških metrik; ETF dobi profil, TER in dividendno politiko iz drugega vira ali vrzel |
| Cena, dnevna sprememba, valuta | obstoječi bars / Flex `markPrice` | Na voljo; navedi datum seje in vir |

Isti nabor stolpcev velja za Pozicije (UX-13) in Watchlisto (UX-14). UX-00 vrne tabelo z dejanskim stanjem po simbolih iz portfelja in Watchliste ter predlog privzetih stolpcev; UI ne dobi stolpca, ki je za večino vrstic prazen.

### Razširitev Flex izpisa (uporabnik v IBKR)

Trenutni parser ([`broker/flex.py`](../../../services/api/preza/broker/flex.py)) bere `OpenPosition`, `Trade` in `CashReportCurrency`. Za dividende v Flex Query dodaj sekcije (natančna imena polj potrdi na vzorcu pred parserjem):

| Sekcija IBKR | Namen | Ključna polja |
|---|---|---|
| Cash Transactions (tipi Dividends, Payment In Lieu Of Dividends, Withholding Tax) | Prejeta bruto izplačila, odtegljaji, storna | `transactionID`, `accountId`, `conid`, `symbol`, `isin`, `currency`, `fxRateToBase`, `dateTime`, `settleDate`, `reportDate`, `amount`, `type`, `description`, `actionID` |
| Open Dividend Accruals (po želji še Change in Dividend Accruals) | Napovedana, še neizplačana dividenda | `conid`, `symbol`, `exDate`, `payDate`, `quantity`, `grossRate`, `grossAmount`, `tax`, `netAmount`, `currency` |
| Financial Instrument Information | Identiteta kotacije (pomaga BL-174/UX-11a) | `conid`, `isin`, `description`, `listingExchange`, `currency`, `assetCategory`, `subCategory` |

Obdobje izpisa naj pokrije vsaj zadnjih 12 mesecev, sicer ocena iz preteklih izplačil nima osnove. Uporabnik po razširitvi naloži nov izpis prek obstoječega uvoza BL-187; očiščen vzorec (brez zneskov in računov) postane test fixture.

### Prihodnji dividendni donos

Tri ločene številke, vse deterministične, nobena iz LLM:

1. **Prejeto:** vsota Cash Transactions po obdobju, bruto in znani neto, po valuti; pretvorba v osnovno valuto samo z `fxRateToBase` iz izpisa, sicer vrzel.
2. **Napovedano:** Open Dividend Accruals (ex-date že mimo, izplačilo prihaja).
3. **Ocena za 12 mesecev:** trenutna količina × dividenda na delnico. Osnova je vidna: zadnjih 12 mesecev iz Flex izplačil ali indicirana letna iz vira. Označeno kot ocena, ločeno od prejetega; ob spremembi količine se preračuna. Akumulacijski ETF ima 0 z razlogom, ne vrzeli.

## 10. Kako bomo preverili izboljšanje

Pri demo prevzemu so vhodni podatki vedno enaki. Zabeleži začetno stanje, zahtevane korake, ali uporabnik pride do pravilnega objekta in ali razume osnovo številke. Časa nalaganja iz tega nezamrznjenega pregleda ne uporabljamo kot benchmark.

| Scenarij | Uspeh |
|---|---|
| Poišči zadnjo uspešno analizo instrumenta z več neuspelimi | Dva vsebinska filtra, en pravilen rezultat; ni treba ročno preiskovati vseh tekov |
| Primerjaj dividendni donos in forward P/E Watchliste | Izbor profila/stolpcev, vrednosti z osnovo in manjkajočimi razlogi brez odpiranja vsakega instrumenta |
| Odpri dogodek Radarja na telefonu | Podrobnosti in vir so takoj dosegljivi; Back obnovi seznam/filtre/scroll |
| Odpri signal iz Telegram povezave | Pravi ID, instrument in evidence neodvisno od statusa ali strani |
| Preveri portfeljsko vrednost | Vidni računi, datum in valuta osnove ter nepopolne pretvorbe, frakcijske količine se ne zaokrožijo v drugo pozicijo |
| Neuspešen predlog | Kratka razlaga, ohranjen vnos in nadzorovan retry; nič surovega JSON v vlogi verdicta |
| Nastavi avtomatsko analizo portfelja | Pred shranitvijo uporabnik vidi obseg, omejitve, okno in naslednji čas; nova avtomatika ni sama vklopljena |
| Prejete dividende in prihodnja pričakovanja | Uporabnik brez ugibanja loči prejeti bruto, znani neto, vrzeli in ocenjen prihodnji znesek |

Vsak zaslon preveri loading/empty/error/partial/stale/ready; mutacije pending/success/error/undo. QA matrika: 390 × 844, 768 × 1024, 1440 × 1000, SL/EN, light/dark/system, pointer fine/coarse, tipkovnica in reduced-motion. Pri neizvedenem zaslonu ni izmišljenih rezultatov.

API: pytest s pravo izolirano testno bazo, ruff/format, mypy strict po projektu, migracije in izvožen OpenAPI. Web: generiranje TS, i18n-check, lint, typecheck, Vitest, build in Playwright vseh petih poti. Samo posnetek začetne strani ni e2e prevzem. Načrt sam ni dokaz, da so ti testi že uspešni.

## 11. Kaj ostaja odprto za pregled

Predlagani privzeti stolpci, razpored glavnih modulov in točna gostota so oblikovne odločitve za potrditev na konkretnih predlogih. Še odprt je poudarek dividendnega dela: uporabnik želi dividende, ni pa še določil razmerja med evidenco prejetega in načrtovanjem prihodnjega. Predlagana prva izdaja ima zanesljivo prejeto in samo z virom podprt prihodnji koledar.

Najprej pripravimo tri reprezentativne postavitve: bogata Watchlista, seznam/podrobnosti Analize in mobilni Radar. To so predlogi za reakcijo, ne dovoljenje za implementacijo celotne aplikacije. Po potrditvi vzorcev se razširijo na ostale zaslone. Ta načrt namerno ohrani delujočo poslovno logiko, obstoječe potrditve tez/uteži in omejitev brez samodejnih naročil.

**Samopregled:** vseh 12 SCR zaslonov in `/ux`, lupina, predogled, mobilna navigacija, izvor/čas, tabele/filtri, avtomatika in dividende imajo predlagan cilj in lastnika. Delujoči M5, horizonti analiz, Windows/Android prilagoditve ter Flex XML uvoz so ohranjeni. Pogodbe, QA in faze so določene; dokončanje živega demo in vsa stanja se preverijo v UX-01/20.

## 12. Predlogi ADR (zapiše Astra v ločeni seji)

Vsaka od spodnjih odločitev bo kasneje dobila vprašanje »zakaj?«, zato po AGENTS.md §2 potrebuje ADR. Številke so predlog (zadnji obstoječi je ADR-0016); Astra jih ob zapisu preveri. ADR se zapiše pred sklopom, ki ga uporablja. Spodaj je Claudovo mnenje kot izhodišče, ne sprejeta odločitev.

| Predlog | Sklop | Odločitev, ki jo ADR zapre | Claudovo mnenje |
|---|---|---|---|
| ADR-0017 Pogodba stanja podatkov (`DataMeta`) | UX-02 | Kako vsak odziv pove vir, čas podatka, čas pridobitve, razpoložljivost in razlog vrzeli | Samo dodajna polja v obstoječih odzivih, noben obstoječi odziv se ne preimenuje ali odstrani. En skupni Pydantic model v `domain/`, enaki `reason_code` vrednosti v vseh modulih. `null` pomeni »ne vemo« z razlogom, nikoli 0. Uvajanje po zaslonih, ne v enem PR čez ves API |
| ADR-0018 Tabele, filtri in shranjen pogled | UX-04 | Kaj živi v URL, kaj v lokalnih nastavitvah in kaj na strežniku | URL za filtre, sort, stran in izbor (deljivo, preživi Nazaj). `localStorage` z verzijo po modulu za stolpce, vrstni red in gostoto. Filtriranje in sort na strežniku nad celotnim naborom. Strežniški profil šele, ko uporabnik zahteva več naprav; do takrat ne. Lastna majhna komponenta pred težko knjižnico tabel, če pokrije sort, pripete stolpce in tipkovnico; knjižnico vzemi le, če UX-04 prototip pokaže, da je potrebna |
| ADR-0019 Urniki in samodejne analize | UX-18 | Kje živi urnik, kako se prepreči dvojni zagon in kako se šteje kvota | Politika v Postgresu, arq cron samo »zbudi« preverjanje. Atomaren claim z unikatnim ključem (politika + termin), da dva workerja ne zaženeta istega. Ena kvota za ročne in samodejne zagone (obstoječi `deep_daily_limit`). Časi v uporabnikovem pasu, shranjeni kot UTC z DST pravilom. Nova avtomatika privzeto izklopljena, globalna pavza ustavi samo nove začetke. Pred zapisom read-only presoja `architect` |
| ADR-0020 Dividende: prejeto, napovedano, ocena | UX-19 | Kateri vir je resnica za dividende in kako se računa prihodnji donos | Flex izpis je edini vir prejetega in napovedanega (idempotentno po `transactionID`). Ocena je deterministična (količina × dividenda na delnico) z navedeno osnovo, vedno ločena od prejetega. Brez davčnih izračunov. Pretvorba valut samo z `fxRateToBase` iz izpisa, sicer delna vsota z vrzeljo |

Za FIX-A, FIX-B in UX-00 ADR ni potreben: popravita obstoječo pogodbo oziroma samo preverjata vire.
