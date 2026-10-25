# ADR-0012: Tedenski pregled tez daje predloge, status trditve spremeni samo uporabnik
**Status:** sprejeto · **Datum:** 2026-10-25 · **Seja:** S-006

## Kontekst
Zasnova (research §5.6) predvideva, da tedenski pregled vsako trditev teze označi kot drži, šibi ali ovržena, ovržena trditev pa ustvari `Signal(kind="thesis_break")`. Pri BL-100 smo se odločili, da status trditve spremeni samo uporabnik z razlogom in dokazom (ADR-0006). Sprožilci iz kartice odločitve so besedilo, zato izpolnjen pogoj `downgrade_if` še ne pomeni ovržene trditve.

## Odločitev
- **Pregled ustvari predlog, ne spremembe.** Za vsako trditev aktivne različice nastane `thesis_claim_review_proposal` s predlaganim statusom (`confirmed`, `weakening`, `broken` ali brez predloga, ko dokazi ne zadoščajo), razlogom in dokazi. `ThesisClaim.status` in dogodki trditve ostanejo nespremenjeni, dokler uporabnik predloga ne sprejme. Sprejem gre skozi obstoječo pot spremembe statusa z `actor = "user"` in preveri, da se status in zadnji dogodek od pregleda nista spremenila. Zavrnitev zahteva razlog in trditve ne spremeni.
- **Kje in kdaj:** delavec `agents` (`thesis_tracker`), en klic vloge `cloud-deep` na pregled. Nedeljski tek ob 06:15 UTC, dnevni tek ob 06:20 UTC pobere izpuščene in na novo potrjene različice. Največ en pregled na različico in ISO teden (`unique(revision_id, week_start)`).
- **Vhod:** novice, filingi in sporočila za javnost iz `news_item` za simbol instrumenta od zadnjega uspešnega pregleda (prvič 30 dni). Največ 30 virov, od tega do 10 mest za uradne vire. Posnetek vhoda se shrani k pregledu.
- **Dokazi:** model sme citirati samo ID-je iz posnetka (`news_item:<id>`). Neznan ali izmišljen ID zavrne celoten izhod. Vir, čas, URL in oznako govorice izpolni koda iz posnetka, nikoli model. Uradnost določi koda: EDGAR filing ali sporočilo za javnost iz dovoljenega vira. Družbena omrežja so vedno govorica.
- **Signal:** predlog `broken` z vsaj enim citiranim uradnim dokazom, ki ni govorica, ustvari `thesis_break` (vir `agent`, smer navzdol, horizont meseci, moč 0,8 kot prioriteta, ne verjetnost) in obvestilo prek obstoječega `notify`. Besedilo jasno pove, da gre za predlog pregleda. Predlog samo z govoricami ali neuradnimi viri signala ne ustvari. Zavrnitev predloga zapre njegov odprt signal.
- **Napake:** ob napaki vloge, prekoračenem času ali neveljavnem izhodu pregled dobi status `failed` brez predlogov in signalov. Pregled brez novih virov (`done_no_evidence`) modela ne kliče.

## Posledice
- Migracija 0013 doda tabeli `thesis_review` in `thesis_claim_review_proposal`, obstoječih podatkov ne spreminja.
- SCR-09 prikaže predlog ločeno od dejanskega statusa trditve, z gumboma Sprejmi (z izrecno potrditvijo) in Zavrni (z razlogom).
- Uradnost potrdi izvor dokaza, ne pravilnosti presoje modela. Oznaka govorice je na ravni dogodka (`Event.is_rumor`), zato je politika za neuradne vire konservativna.
- `max_jobs = 1` v delavcu agentov pomeni, da dolga globoka analiza lahko zamakne pregled.

## Zavrnjene možnosti
- **Samodejna sprememba statusa trditve:** v nasprotju z ADR-0006 in odločitvijo BL-100.
- **Signal šele ob sprejemu predloga:** uporabnik bi za možen zlom teze izvedel šele, ko odpre SCR-09.
- **Parsanje pragov iz sprožilcev:** sprožilci so besedilo modela; izračun ali negiranje bi bila krhka in bi številke računal model.
