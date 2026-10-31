# S-025 · Kompaktni portfelj in naslednji UX krog

**Izhodišče:** `6a9f07c`, produktni rez `4c54d0c`, veja `feat/uxui-demo-upgrade`. Zahteva in raziskava začeti 2026-10-30. Dokument loči dejansko izvedeni BL-223 od predloga naslednjih BL-224–228. [SPEC](../superpowers/specs/2026-10-30-spremljanje-in-pojasnila-ux-spec.md), [plan naslednjega kroga](../superpowers/plans/2026-10-30-spremljanje-in-pojasnila-ux.md), [ozki izvedbeni plan](../superpowers/plans/2026-10-30-kompaktni-portfelj-izvedba.md).

## Izvedeno: Pozicije in Watchlista [BL-223]

Graf je desno ob identiteti v isti celici. Odstranjeno je podvajanje splošnega obdobja, ostaneta dejansko število sej in datumski razpon. Vir/čas sta v native details, dostopnem prek tipkovnice in dotika z 48 px ciljem. Imena, račun/borza/valuta, cona, barve in kakovostne oznake ostanejo; nobene fiksne višine ali rezanja opozoril. Lokalni ID stolpcev/profili in preference se ne ponastavijo.

Prva dejanska DOM meritev dema pred spremembo: VWRA/EQQQ **217,25 px**, MSFT **201,25 px**. Po prvem premiku **132,40625 / 132,40625 / 129 px**; ozek popravek le razmikov leve skupine da prve tri običajne vrstice **129 px**. Graf x=485, identiteta x=269, zato je v isti vodoravni skupini desno. Watchlistin že obstoječ razmik med dvema 48 px dejanjema bi dal 133 px; odstranjen je samo 4 px razmik, cilji ostanejo.

Višinski cilj ≤130 px velja za primerljiv namizni pogled pri 100 %. Telefon ohrani naravno rast večjega besedila/opozoril; ne zmanjšuje se pisave ali tarč samo zaradi namizne številke. Vodoravno drsi tabela znotraj okvirja, cela stran ne preteče. Native razkritje lahko namerno razširi vrstico; to ni rezano.

## Dokazi

| Preverjanje | Rezultat |
|---|---|
| Ciljni Vitest | 6 passed v treh datotekah. Novi compact test najprej RED, potem GREEN; preveri dejansko obdobje in dostopno razkritje provenience, ne kopije CSS razredov. |
| Celotni web po zadnjem viru | **181 passed / 44 datotek**; TypeScript in celotni ESLint exit 0; i18n **1302 ključev**. |
| Oblikovanje | Ciljni Prettier in git diff --check uspešna. |
| Linux build | Uspešen po zadnji spremembi; osvežen samo :3100. |
| Ciljni Playwright | **23 passed / 5 namernih skipov**, 28 primerov. Štirje novi primeri za Pozicije/Watchlisto × desktop/phone preverijo položaj grafa, namizno višino, datum, Enter razkritje vira/časa in odsotnost page overflow. Obstoječi add/remove, Standardno/profili, barve in vrzeli ostanejo zeleni. |
| Celotni Playwright | **80 passed / 10 namernih skipov**, 90 primerov, exit 0, 3,3 minute. |
| Neodvisni pregledi | T1 in končni povezani produktni pregled **PASS**; prihodnji SPEC/plan po dveh dopolnitvah **PASS**, UX-R1/R2 ADDRESSED. [Končno poročilo](./2026-10-30-neodvisni-pregled-kompaktnega-portfelja-in-plana.md). Astra ni zaključila zaradi omejitve uporabe, pregled je prevzel neodvisni SOL. |

Prvi ciljni browser sklop je imel 19 pass / 5 skip / 4 fail. En watchlistin gap je bil dejanski majhen razlog za 133 px. Novo namizno merilo je test po pomoti uporabil tudi na telefonu; usklajeno je s prvotnim desktop obsegom, telefon še vedno preveri vsebino/dostopnost/overflow. Obstoječi remove test je imel po dodatnem razkritju preširok locator `summary`; zdaj izrecno izbere »Dejanja«. Nobena odstranjevalna ali obnovitvena trditev ni odstranjena. Ponovni ciljni sklop je zelen.

Ukazi iz `apps/web`: neposredni lokalni `node node_modules/vitest/vitest.mjs run`, `node node_modules/typescript/bin/tsc --noEmit`, celotni ESLint, i18n script in ciljni Prettier. Playwright ima izrecno `BASE_URL=http://localhost:3100` in lokalni CHROMIUM_PATH; ciljni sklop `portfolio-density`, `portfolio`, `review-feedback`, `ux-upgrade`, nato celota. Preizkusi so na ločenih sintetičnih podatkih, brez novih LLM delavcev ali ponudnikov. API/agents koda ni spremenjena; stari API/agents rezultati niso prikazani kot novi zagoni.

## Pripravljeno za nadaljnjo izvedbo

- **BL-224:** skupna pomoč ob naslovu, manj stalnih opisov, lokalni datum v navigacijski nogi. Demo/govorica/stale/partial/napaka ostanejo vidni; metoda in daljša navodila na klik.
- **BL-225:** lastne ideje brez analize in spremljanje konkretnih obstoječih signalov/končnih analiz iz drugih strani. Trajna ločena zbirka, osnutek/nespremenljiva aktivacija, pošten strežniški čas, brez fake Signal/AnalysisRun ali samodejnih modelov. Stari source=all ne dobi novih idej; Mine ima ločen obseg.
- **BL-226:** bolj berljive Teze nad obstoječimi dokazi, jasen izvorni pogoj, zadnja dejanska preverba, pending odločitve in paginirana zgodovina. Agentov predlog ni potrjeno stanje.
- **BL-227:** več meril glede na dolžino investicije; ločen podatkovni SPEC za začetno/trenutno opažanje, enoto/osnovo/obdobje in neprimerljive podatke. Ciljni horizont, pregledni urnik in test 1/5/20/60 sej so različne stvari.
- **BL-228:** izolirana reprodukcija razlike stare globalne metode (neutral kot long, druga vstopna sveča/stroški) in verzionirana odločitev pred morebitnim popravkom zgodovine.

Oba uporabnikova odgovora sta vključena; ni preostalega vprašanja o tem, ali so lastne ideje potrebne ali ali mora biti enaka predloga za vse horizonte. Posameznih finančnih pragov ali obveznih kazalnikov ni izbral. Pomoč, lastne ideje in Teze **niso implementirane v tem koraku**. Raziskavi [Teze](../research/2026-10-30-teze-uporabniski-potek-raziskava.md) in [Uspešnost](../research/2026-10-30-uspesnost-in-povezave-raziskava.md) navajata kodo in prevzemne scenarije.

Pregled predloga je odpravil dve ozki vrzeli: starega `source=all` ne razširi z idejami in pending/nepreverljive preglede tez v Mine loči od privzetega imenovalca, z izrecno izbiro vključitve vseh. Legacy statistika ostane ločena in označena; zgodovina se ne prepisuje zaradi nove postavitve.

## Okolji in uporaba OpenCode

Demo web: `sha256:80cc2588224579c2256e97838d7fb313c52d15d5e58eb25eb02062414fb56d02`. Demo API ostane `sha256:c2a6a0055ca57e674c98fbd6b270c0d1562525ffb7212d0c01d85ce1895530d7`. Ni nove migracije ali reseeda, ne zaganjamo živega modela/pošte/brokerja.

:3000 web `sha256:4eaf458ee0525197f3800d28ed6d758aaffa70ec23d6bfcf7ddaaff67e06f7c9` in API `sha256:973f535ba8840631e0442f59c346c6b3469a17646f5b338703b50fdc9349e194` se ujemata s predhodnima digestoma; :3000 ostane nedotaknjen, ni merge/push ali žive migracije. BL-222/backup, Flex/FX/SMTP ter A3/A5 niso s tem krogom zaključeni.

Uporabnik je dovolil OpenCode/DeepSeek za raziskavo. Lokalna discovery je potrdila `opencode-go/deepseek-v4.1-flash` ter novo obliko model#variant. Poskus bounded read-only raziskave z izbranimi izseki kode je **avtomatski varnostni pregled zavrnil pred zagonom**: splošno dovoljenje za raziskavo ni bilo prepoznano kot dovoljenje za konkretni izvoz zasebne kode temu zunanjemu prejemniku. Ukaz ni bil obiden/ponovljen drugim kanalom. Raziskavo in pregled so opravili ta seja in interni subagenti; ni rezultata DeepSeek ali trditve, da je requested max dejansko tekel. Skrivnosti ali dejanski finančni podatki niso bili del pripravljenega gradiva.
