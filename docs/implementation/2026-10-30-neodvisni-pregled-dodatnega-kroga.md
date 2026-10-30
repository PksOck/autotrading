# BL-218 / BL-220 — končni integrirani pregled

**Datum:** 2026-10-30. **Verdikt: PASS za neposredni izvedbeni krog. A4-1: ADDRESSED.**

V pregledanem končnem paketu nisem našel nove kritične, pomembne ali manjše napake: **0 / 0 / 0**. D1/A1/A2/A4/U1/U2 in ozki popravek BL-220 so sprejemljivi v dogovorjenem obsegu. To je ocena kode tega kroga, ne potrditev celotne osnovne izdaje, živih finančnih podatkov ali dovoljenje za merge/push/deploy.

## Obseg in metoda

Osnova je `d0ceebf4cb28cb8919d23e00f2c419fa9c41d802`. Pregledan je paket `final-review.diff`, SHA256 `26959bc48e1297cc75913f68f25568508a9b4da6c2ef31bfa47bff2522153fce`, zajet pri HEAD `744a4aeb850dac2d7b5ce10a8afb4fa985b4156e` z dodatnimi delovnimi spremembami in novimi datotekami. Vključuje commite `9edbdf2`, `8f95e97`, `744a4ae` ter končni outbox/demo/dokumentarni diff. Med pregledom je integrator nespremenjeno produktno vsebino shranil še v `6cd2488` in `0db305d`; preverjeni končni produktni HEAD je `0db305d2746a0e6de07ae0e0b0279ccd0eb7d5d5`. Zaključna dokumentacija nastaja posebej in ni samodejno zajeta v tem produktu/testnem rezu.

Prebrani so bili izvedbeni SPEC in plan, projektna navodila, obstoječi omejeni pregledi, poročila izvajalcev in ledger. Dodatni vpogled zunaj diff je bil omejen na konkretne pogodbe `gate`/`review_gate`, trajni izvor, `mark_dispatched`/finalizacijo in `EntityLink`. Stari celotni razpon `1855eb8..c55e37d` ni bil ponovno pregledan. Prejšnji Claudov pregled ostaja zgodovinski vir odprtih pogojev.

Predvideni Astra pregled se zaradi omejitve uporabe ni začel; to poročilo je dejanski končni neodvisni pregled Sol. Pregledovalec ni spreminjal izvorne kode, indeksa ali HEAD, ni poganjal dodatnih testov, klical ponudnikov ali pošiljal sporočil. Edina ustvarjena datoteka je to poročilo.

## A4-1 — zaključena pomembna ugotovitev prejšnjega pregleda

**Mesto:** `services/api/preza/services/automation.py:283`, regresija `services/api/tests/test_automation_outbox_fairness.py:119`.

Prejšnji `tasks-review.md` je pravilno zahteval spremembo: ORM posodobitev po naložitvi starega pending kandidata bi lahko po čakanju na execution zaklep prepisala sočasni running claim. Novi zapis je atomaren `UPDATE` z obema pogojema `id` in `state='pending'`, uporablja `RETURNING` in preveri prazen rezultat. `synchronize_session=False`, odsotnost ORM prirejanja izvedbi in invalidacija uspešno spremenjenih polj preprečujejo poznejši brezpogojni flush starega objekta. Advisory/cursor lock še naprej serializira samo dostavljalce; popravek pravilno varuje tudi tekmovanje z delavcem.

Regresija uporablja tri prave DB seje, pravi `claim` in preverjanje blokiranja z `pg_blocking_pids`. Pokrije prav sporni vrstni red: kandidat prebran, claim drži running zaklep, politika potrjena z novo revizijo, terminalizacija čaka, claim potrjen. Izvajalčev RED je bil `skipped != running`; isti primer in legitimni stale-pending primer sta po popravku zelena. Končni API zagon ju vključuje. **A4-1 je odpravljen; ni preostale zahteve za spremembo iz tega pregleda.**

## Skladnost in prednosti

| Sklop | Končna ocena in konkretna podlaga |
|---|---|
| D1 | `services/api/preza/services/dividends.py:105` ohrani omejitev različice in blokira degradacijo partial/complete v missing, pri tem pa pusti veljaven novejši izrecno prazen snapshot. Ohranjeni so payload/row_keys, ledger konflikti in meje računov. DB regresije preverjajo tudi starejši replay po praznem snapshotu. |
| A1 | `services/api/preza/llm/client.py:173` čaka varovalo neposredno pred vsakim `_post`, tudi pred JSON popravo. Zavrnjeni poskus ne šteje kot izveden HTTP; že porabljeni žetoni in Decimal strošek ostanejo ohranjeni, pred prvim transportom je strošek znano 0. Razširjeni protokol je izrecen in ni nevarovanega fallbacka ali mutacije skupnega klienta. |
| A2 | `services/agents/preza_agents/thesis_tracker/runner.py:95` ponovno preveri celotni trajni `review_gate` po dispatch commitu in pred vsakim transportom. Ročna izjema izhaja iz shranjene izvedbe, članstva, tedna in revizije politike. Zavrnitev se konča z varno kodo ter dejansko porabo; CAS konflikt drugega lastnika ga ne zaključi. Pravi DB lock test pri `test_thesis_attempt_guard_db.py:181` dokazuje odpravo prvotne dirke. |
| A4 | `services/api/preza/services/automation.py:205` filtrira upravičene/zastarele zapadle pending namene pred LIMIT, nadaljuje po stabilnem paru in omeji delo na 100 novih dostav ter 1000 kandidatov. Singleton preživi restart, zaključek cikla omogoči ponovno obravnavo starejših/resumiranih namenov. `automation_worker.py:159` zdaj potrdi transakcijo kurzorja. Migracija 0020 in model se ujemata; prejšnje migracije ostanejo ohranjene. |
| U1/U2 | `apps/web/components/track-record/BacktestPanel.tsx:243` uporabi obstoječi signalni Peek; analiza pri `:250` odpre pravo pot z natančnim ID v novem zavihku, z varnim rel in SL/EN oznako. Enak UUID različnih virov ostane ločen. E2E preveri rezultate in osnutek, Close/Escape/Back, fokus, modifierje, pravo analizo in odsotnost novega POST. |
| BL-220 | `services/api/preza/cli/seed_demo.py:445` popravi konkretno neveljavno sintetično EvidenceRef z obveznim `kind`. `services/api/tests/test_demo_track_signals.py:15` odpre vseh 14 determinističnih ID skozi pravi detail API. API ne dobi fallbacka, ki bi prikril slabe podatke. |

Integracija ne uvaja novega plačljivega retryja: outbox ohrani isti job ID/claim, A1/A2 ponovno preverita dovoljenje na dejanskem transportu, manual vedenje pa ostane ločeno. Testi ne preverjajo samo vrnjenih mock razlogov: obstajajo dejanski DB zaklepi, restart novega engine/session in realni arq dokaz ponovne dostave istega še pending namena po začasni blokadi. Omejen sintetični demo popravek ne širi obsega v spremembo žive baze.

## Dokazi in njihove meje

Rezultati spodaj so iz poročil izvajalcev/integratorja; niso novi zagoni pregledovalca. Končni `final-api-tests.log` sem prebral in potrjuje **585 passed, 18 warnings, 396.50 s**, brez neuspehov/preskokov. Ta zadnji zagon vključuje realni Redis primer, A4-1 dirko in vseh 14 demo ID. Opozorila so obstoječe Starlette/httpx ter SQLAlchemy ARRAY deprecations.

- D1: štiri začetne reprodukcijske napake, nato 21 zelenih ciljnih testov.
- A1: 42 zelenih ciljnih testov; A2 pravi DB lock RED → 33 zelenih ciljnih testov; celotni agents 229 zelenih.
- A4: prvotni realni Redis ciljni sklop 23 zelenih; po A4-1 23 zelenih in en izrecno izločen Redis primer v ciljnem zagonu. Zadnji celotni API ga znova vključi, zato ni vrzeli zaradi tega izločanja.
- Web: 156 zelenih, uspešni lint/tipi/i18n in preverjena generirana pogodba; Linux build API/web. E2E 64 uspešnih, 10 obstoječih projektno odvisnih preskokov; vsi štirje novi SL/EN × desktop/phone primeri uspešni. Preskoki niso predstavljeni kot opravljeni scenariji.
- Ročni CUA dokaz integratorja: 27 vrstic študije → pravi zgodovinski signalni Peek → Close ohrani 27 vrstic. Popravljenih samo 14 točno določenih sintetičnih vrstic, brez reset/reseed; demo migracija 0020. Nespremenjeni digesti :3000 so integratorjev dokaz izolacije, ne moj novi pregled vsebnikov.

## Naslednje SPEC — sprejemljivi kot pogojni predlogi

Pet novih S-B/S-C/S-F5/S-G1/S-H je ustrezno označenih `NEXT-SPEC / CONDITIONAL PROPOSAL`. Vsebinsko ločijo sedanji popravek, prihodnji predlog in manjkajoč dejanski dokaz. Matrika S-H ohrani vseh 14 starih preglednih ID ter loči M od D.

Posebej pravilno: S-B pri vrstici 34 blokira ugibanje XML poti/pomena `Re`, pri vrstici 43 zahteva ekspliciten FX cilj in ne ugiba backfilla; SB-12 pri vrstici 55 izrecno ostane nova prihodnja coverage pogodba, ne retroaktivna trditev o D1. S-G1 pri vrstici 37 zahteva avtoritativni dokaz živosti/prenehanja in ne izpelje novega dispatcha ali smrti iz samega running/iztečenega heartbeat; AnalysisRun ohrani dovoljen status in ločeno kodo unknown. S-C ne zamenja kotacije po simbolu ali ISIN samem. S-F5 zahteva dejanski restore konkretnega podatkovnega reza pred prvo živo migracijo tudi 0016–0020. S-H pri vrstici 19 zahteva novo izrecno odobritev :3000; zelen pregled je ne nadomesti.

Ti dokumenti so primerni za naslednji pregled/izvedbeni plan po pridobitvi navedenih vhodov. Njihova priprava ne pomeni, da so lease shema, FX preslikava, restore postopek ali živi kanal že izvedeni oziroma preizkušeni.

## Česa ta pregled ne presoja kot rešeno

| Odprto področje | Razlog in obvezna meja |
|---|---|
| D2/D3/F1/B5, BL-202/205 | Dejanski razširjeni očiščeni Flex, semantika popravkov, FX cilji, cash popolnost in dejansko UI besedilo zahtevajo S-B dokaze. D1 in sintetični testi tega ne zaprejo. Ostajajo pogoji odvisnega finančnega obsega izdaje. |
| A3/A5/R1 in BL-204 | Lastništvo po restartu/lease, recovery drugega executorja, Radar članstvo pred LIMIT ter trajni osnutek imajo ločene prihodnje pogodbe/teste v S-G1. A4-1 je odpravljena druga, konkretna dirka; to ni dokaz odprave teh starih vprašanj. |
| E1/BL-212 | Fake transport in zelen API ne dokazujeta prave SMTP dostave. Kanal ostane izklopljen ali izrecno izločen do ločenega dovoljenega dokaza. |
| S-C/BL-193/194/174 | Aktualne ciljne kotacije, brokerjev dokaz identitete in dejanska pokritost niso preverjeni v tem krogu. Stara številka devet ni novo dejstvo. |
| S-F5/S-H/BL-215 | Ni opravljenega živega backup/restore, končne migracijske inventure, pregleda aktivnih poslov ali uporabniškega dovoljenja M/D. Zeleni neposredni popravki teh vrat ne odprejo. |
| Celotni stari feature diff in živa namestitev | Ta pregled je inkrementalen. Ne razglaša ponovnega celovitega pregleda stare veje ali pripravljene osnovne izdaje. |

To so izrecne znane prihodnje meje oziroma blokade ustreznega obsega; ne nove napake tega diff in ne trditve, da so že popravljene. Zaključni S-023, posodobitev statusa BL-218 ter končni dokazni/release zapis še ureja integrator; v tem trenutku nedokončano zaključevanje dokumentacije ni nova produktna napaka. Končni zapis mora navesti končni commit/delovni rez in ohraniti zgornje odprte pogoje.

**Končni sklep:** neposredni integrirani krog lahko preide v zaključno dokumentiranje/prevzem kode brez dodatnega produktnega popravka iz tega pregleda. Pred združitvijo se posebej preverita osnova in pooblastilo; namestitev :3000 ostane ločena in zadržana do svojih dokazov ter nove izrecne potrditve.
