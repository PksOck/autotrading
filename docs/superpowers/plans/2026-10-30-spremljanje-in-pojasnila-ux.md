# Spremljanje in pojasnila — izvedbeni plan naslednjega UX kroga

> **For agentic workers:** uporabi superpowers:subagent-driven-development ali superpowers:executing-plans. Vsak spodnji rez ima lasten testni in pregledni izhod.

**Status:** T1/BL-224 izveden in preverjen v S-026, glej [dokaze](../../implementation/2026-10-31-pomoc-in-hierarhija-podatkov.md). T2–T6 so naslednji rezi, njihove funkcije še niso izvedene. BL-223 ima svoj [ozki plan](./2026-10-30-kompaktni-portfelj-izvedba.md) in dejanski dokaz ločeno. Odgovora uporabnika sta vključena: tudi lastne ideje brez analize, več meril odvisno od ciljnega trajanja investicije.

**Goal:** Uporabnik iz vsake raziskovalne strani razume, kaj vidi, doda konkretno mnenje ali lastno idejo v spremljanje in pri Tezi vidi, kaj jo podpira ter kaj zahteva odločitev.

**Architecture:** Ohranimo Next.js/Radix/next-intl in FastAPI/SQLAlchemy/arq. Skupna uredniška pomoč in manj stalnega besedila; nova trajna zbirka in verzionirane ročne ideje sta ločeni od signalnih statusov, analiz in Watchliste. Najprej jasen bralni model Tez, nato omejene pogodbe meril, katerih podatki so dejansko podprti.

**Tech Stack:** TypeScript/React, TanStack Query, Radix, Tailwind tokeni, Vitest/Playwright; Python 3.12, Pydantic v2, PostgreSQL/Timescale, Alembic, pytest.

**Spec:** [UXH/UXP/UXT/UXM in F-UX01–13](../specs/2026-10-30-spremljanje-in-pojasnila-ux-spec.md). [Raziskava Tez](../../research/2026-10-30-teze-uporabniski-potek-raziskava.md), [raziskava Uspešnosti](../../research/2026-10-30-uspesnost-in-povezave-raziskava.md).

## Global Constraints

- :3000, živih podatkov in Claudovega checkouta ne spreminjaj. Nova shema samo z migracijo po takratnem head; dokazi na izolirani sintetični bazi, generirani OpenAPI/TS iz dejanskega routerja.
- Nobeno Dodaj/Osveži/Pomoč/Shrani idejo/aktivacija teze ne odda naročila, ne pošilja sporočil ali samodejno kliče novega modela. Obstoječi procesni switch/okna/kvote, govorice in človeška potrditev ostanejo.
- Vse finančne številke iz preverjenih virov ali determinističnega Decimal izračuna. Neznano ni 0, uporabnikov prag ni potrjeno finančno dejstvo, datum danes ni datum podatka.
- SL/EN iz messages, obstoječi tokeni, 48 px na dotik, tipkovnica/fokus/Back, telefon in 200-% povečava. Vidna opozorila niso skrita v pomoči.
- Dejanski uporabnikov horizont je ločen od urnika pregleda in od 1/5/20/60 sej obstoječe študije. Polni portfeljski backtester BL-216 in A3/A5 nista zaključena s tem planom.
- Arhitekturne razširitve so predlog tega dokumenta; pred posameznim podatkovnim rezom dokončaj navedeno pogodbo z vzorci/testi. Ne implementiraj le navideznih kartic za manjkajoče podatke.

## Review Focus

1. Datum/svežina/vir se lahko premaknejo, ne pa izgubijo; povsem prazen makro nabor in API napaka sta različni stanji (T1).
2. Isti signal/analiza/ideja po izgubi odgovora ali dveh zavihkih ostane isto članstvo/aktivacija; noben lažen zgodovinski čas napovedi (T3/T4).
3. Osebni filter in točen tip+UUID se uveljavita pred COUNT/LIMIT, ne po prvi strani; podobna mnenja niso neodvisne naložbe (T4).
4. Zadnji pregled teze ni zadnje urejanje, pending agentov predlog ni potrjena odločitev in besedilni downgrade pogoj ni že ovrženje (T5).
5. Neprimerljivi forward/TTM/valute/obdobja in manjkajoči podatki ne dobijo zelene potrditve; 60 sej ni zaključek večletne teze (T2/T6).

## Prednost in ločeni izhodi

| Vrstni red | BL / rez | Izhod |
|---|---|---|
| Že ozek poseg | BL-223 | Nižje horizontalne vrstice; samostojno dokazano, ne čaka nove podatkovne sheme. |
| 1 | BL-224 / T1 | Pomoč in čistejša hierarhija v vseh pogledih, datum v nogi, brez izgube opozoril. |
| 2, vzporedna raziskava | BL-228 / T2 | Dokazana in poimenovana metoda izidov; brez tihih zgodovinskih popravkov. |
| 3 | BL-225 / T3–T4 | Celoten tok izvorno mnenje ali lastna ideja → trajno spremljanje → pravilen izid. |
| 4 | BL-226 / T5 | Uporaben seznam/ustvarjanje/pregled Tez nad današnjimi dokazi, ne prazna nova tema. |
| 5 | BL-227 / T6 | Potrjene meritve glede na horizont in enota/čas/baseline; samo podprti kazalniki. |
| Zaključek | T7 | Dokazni paket, neodvisni pregled, :3100 za uporabnika; :3000 še zadržan. |

## T1: Skupna pomoč in manj odvečnega besedila [BL-224]

**Datoteke:** nov `apps/web/components/common/PageHelp.tsx`, po potrebi `DataDetails.tsx`, `lib/page-help.ts`; obstoječi `PageHeader.tsx`, `Icon.tsx`, `shell/{Sidebar,CommandPalette}.tsx`, nov `shell/LocalDate.tsx`, vse produktne `app/**/page.tsx`, `overview/{LiveOverview,PortfolioTreemapCard,PulseTimeline,Funnel}.tsx`, messages in ustrezni testi. Drugi moduli se spreminjajo samo tam, kjer se preseli statično pojasnilo, ne poslovna logika.

**Vmesnik:** `PageHeader({title,actions,helpKey,...})` dobi tipizirani ključ iz uredniškega registra. `PageHelp({pageKey})` odpre obstoječim vzorcem skladen dialog/panel z `useBackToClose`; brez novega query/filter stanja in brez modela. `DataDetails({label,children})` je dostopen razkritveni vzorec za lokalno provenienco; error/stale/rumor ostanejo zunaj. Začrtana imena so predlog, ki ga preflight uskladi z obstoječimi izvozi.

- [x] Napiši vedenjske teste `opens_help_without_network`, `back_escape_restore_opener_and_preserve_filters`, `missing_macro_compact_is_distinct_from_error`, `data_warning_not_hidden_with_method`, `local_date_hydrates_and_rolls_over`; potrdi pričakovani RED. CSS razredov ne testiraj kot nadomestilo uporabnosti.
- [x] Uvedi eno pomoč ob naslovih in štiri kratke uredniške sklope UXH-02 za vse poti v matriki SPEC. Odstrani razvojne SCR kickerje s produktnih strani, dolge podvojene uvode prestavi v pomoč. Povezave v pomoč ne sprožijo dejanja brez izrecnega klika.
- [x] Premakni današnji lokalni datum v navigacijsko nogo; telefon dobi dostop v Več/pomoči. Ohrani datum vira ob podatku, demo trak in vidne vrzeli. Pokrij polnoč/DST s kontrolirano uro; brez server/client mismatch.
- [x] Pregled makro konteksta preuredi po UXH-04. Semantike in vsebine obstoječih vizualizacij ne odstrani; legende skrajšaj v kratek ključ, polna razlaga v pomoč.
- [x] Vitest/tsc/ESLint/i18n; E2E vsaka produktna pot SL/EN × desktop/phone, 200-% povečava in nested Peek/help. Preveri tudi ohranitev neoddanega predloga. Commit `feat(ux): add contextual page help and compact metadata [BL-224]`.

## T2: Metode Uspešnosti in statična razlika neutral [BL-228]

**Datoteke:** `services/api/preza/domain/{outcome,backtest}.py`, `services/{outcomes,track_record,backtest}.py`, njuni testi; UI `TrackRecord.tsx`, `BacktestPanel.tsx`, ADR-0022 in nov ADR samo ob sprejeti spremembi metode.

- [ ] Dodaj reproducibilne fixture za isti signal, same-day/next-day vstop, `up/down/neutral/unknown`, stroške, 20 shranjenih sej in nerazpoložljiv benchmark. Najprej zabeleži dejanske stare rezultate, ne popravi jih mimogrede.
- [ ] Dokaži, katere producer poti lahko shranijo neutral izid; na izolirani DB izmeri primer, živih vrstic ne prepisuj. Če dejanski uporabniški podatki še niso dovoljeni/dosegljivi, je obseg vpliva neznan, ne 0.
- [ ] Pred popravilom določi verzionirano metodo in politiko za stare vrstice: ohranitev legacy rezultata z oznako ali izrecna migracija/backfill z obnovitvenimi vrati. Nevtralni cenovni izid v novi metodi ostane preskok po ADR-0022.
- [ ] UI mora že ob T1 razločiti globalno statistiko in novo študijo; T4 ne sme njunih števil združiti. Ciljni pytest in DB regresije, neodvisni pregled metode in morebitnega backfilla, šele nato sprememba kode/ADR. Ločen commit `fix(outcomes): ... [BL-228]` s točnim končnim obsegom.

## T3: Trajne lastne ideje in zbirka [BL-225]

**Nove odgovornosti:** `services/api/preza/domain/research_tracking.py`, `models_research_tracking.py`, `services/research_tracking.py`, `routes/research_tracking.py`, nova migracija; testi `test_research_tracking_db.py`/`test_research_ideas_db.py`. Sledi sedanjemu single-user deploymentu, brez izmišljenega sistema uporabnikov.

**Predlagana pogodba:**

- `ResearchIdea` in `ResearchIdeaRevision`: instrument FK, revision, draft/active/archived, smer/razlog/horizont/ciljni datum, create/activation UTC in nespremenljiv snapshot aktivirane različice. Osnutek ima edit CAS; nova vsebinska verzija po aktivaciji ne prepiše stare. Za prvi cenovni rez dodatna poslovna merila ostanejo označeno besedilna, strukturirane primerjave šele T6.
- `ResearchFollow`: točno ena tipizirana FK na signal, analysis run ali idea revision, unique članstvo na vsakem tipu/ID, original_available_at, first_saved_at, archived_at, revision in snapshot mnenja. Brez generičnega visečega UUID brez preverljivega vira. Mutacije imajo durable idempotence in audit dogodke. Ponovno dodajanje arhiviranega obnovi isti predmet/sled.
- `GET /research-tracking` (bounded/paginiran), `PUT /research-tracking/membership` z `kind,id,expected_revision?,request_id`, `PATCH /research-tracking/{id}` za arhiviraj/obnovi, `POST /research-ideas` za idempotentni osnutek, `PATCH /research-ideas/{id}/draft`, `POST /research-ideas/{id}/activate` za atomsko aktivacijo+članstvo, `GET` po znanem request/idea ID za obnovo. Ne sprejemaj source timestamp ali DSN/provider parametrov iz odjemalca. Točne poti/zahteve pred implementacijo objavi v OpenAPI fixture, ne na slepo kopiraj predlogov v UI.

- [ ] RED: `same_reference_two_tabs_one_membership`, `typed_id_collision_is_distinct`, `missing_or_running_analysis_rejected`, `archive_restore_keeps_original_time`, `activate_lost_response_one_revision_one_member`, `stale_edit_keeps_draft`, `manual_time_cannot_be_backdated`, `save_creates_no_run_signal_transport`.
- [ ] Zapiši finalne Pydantic/FK/check/unique pogodbe in takrat naslednjo migracijo po head. Transakcija aktivacije nastavi available_at po DB času in članstvo skupaj; zamrznjeno telo/request_id omogoči obnovo po izgubi odgovora. Klic istega request_id z drugo vsebino je 409.
- [ ] Dodaj SQL storitve/router z omejenimi seznami, revision CAS in varnimi napakami. Izračun/podatkovni refresh ni del shranjevanja; ne izberi neznane valute/borze. Instrument mora biti razrešen ali uporabnik dobi jasen razlog za ustavitev aktivacije.
- [ ] Dokaži na pravem izoliranem Postgresu dve povezavi/sočasen klik in izgubljen 202 odgovor; štejejo članstva/različice, 0 analiz/signalov/modelov/obvestil. Migracija gor/dol na sintetičnih podatkih, Ruff/mypy, regenerirani OpenAPI/TS. Commit `feat(tracking): persist personal ideas and research membership [BL-225]`.

## T4: Sklenjen uporabniški tok in izidi izbora [BL-225]

**Datoteke:** nov `apps/web/components/tracking/{FollowResearchButton,IdeaComposer,MyTracking}.tsx`, `lib/api/tracking.ts`, verzionirana lokalna shramba ideje; obstoječi `TrackRecord.tsx`/`BacktestPanel.tsx`, `signals/{SignalDetail,SignalsInbox}.tsx`, `analysis/{AnalysisView,DecisionHeader}.tsx`, `proposals/ProposalList.tsx`, raziskovalne podrobnosti in instrument. API `domain/backtest.py`, `services/backtest.py` in njuni testi. Ne izmišljaj `AnalysisDetail.tsx`: trenutni podrobni prikaz je AnalysisView/DecisionHeader.

**Vmesnik:** tipizirani `ResearchRecordRef` za `signal|analysis|idea_revision`; en skupni gumb bere/shrani članstvo. Mine/Signals/Study v URL z ohranitvijo starih neposrednih povezav. `BacktestRequest` doda izrecno selection `all|mine|single`; single je en tip+UUID, mine je SQL podpoizvedba aktivnih članstev v scope. Legacy request brez selection ostane all in njegov `source=all` vsebuje samo signale in končne analize; ideje so dovoljene samo za mine/single, ne širijo starega union/count/povprečja. Rezultati imajo metodo/čas/cene/stroške/preskoke in isto identiteto. Mine dodatno loči nerešene/nepreverljive preglede tez od privzetega imenovalca; izrecna vključitev vseh razkrije obseg in ločeno šteje te zapise. Legacy all ohrani metodo, jasno označi prisotnost pending pregledov.

- [ ] RED DB: upravičen izbrani zapis za >1000 tujih, COUNT in LIMIT istega scope, neutral/manual brez prihodnjih sej, isti UUID različnih tipov, `legacy_all_unchanged_after_saving_ideas`, `mine_pending_review_separate_denominator`, `include_pending_is_explicit_and_records_review_state`; ohrani read-only cene in bounded nalaganje. Brez filtriranja že izračunane prve strani.
- [ ] Za mine/single dodaj frozen aktivno idea revision z SQL filtrom pred COUNT/ORDER/LIMIT; legacy all union ostane signal+analysis. Ne dodajaj idej v globalni SignalOutcome/kalibracijo. Čakajoč/nepreverljiv predlog teze ostane v Mine ločeno viden, izključen iz privzetega imenovalca. Izrecna vključitev vseh beleži stanje recenzije ob izračunu in ne prepiše prvotnega časa/mnenja. Legacy all ostane vključujoč po stari metodi in dobi jasno oznako pending obsega.
- [ ] RED UI: Save/aktivacija po reload uporablja isto namero, `follow_does_not_accept_signal`, `archived_undo_keeps_origin`, `source_button_picks_exact_finished_run`, `multi_output_proposal_requires_choice`, `own_idea_without_analysis`.
- [ ] Uvedi Nova ideja z osnutkom/pregledom/aktivacijo in človeško razumljivimi časovnimi oznakami. Mine pokaže tudi čaka/preskočeno; vmesni 20/60-sejni rezultat je vidno vmesni za dolgoročno idejo. Možnosti izračuna se razširijo na zahtevo, veljavni parametri ostanejo kratko vidni. Pristranskost izbora je pojasnjena v pomoči in povzetek se imenuje izid izbranih mnenj.
- [ ] E2E: iz Signala in Analize v Mine, lastna ideja brez analize, duplicate/lost-response/two-tabs, arhiviraj+undo, neposredne stare povezave, odpiranje Peek ohrani izračun. SL/EN, telefon, tipkovnica, ni nobene prave porabe. Commit `feat(ux): connect personal tracking across research screens [BL-225]`.

## T5: Teze za odločanje nad obstoječimi dokazi [BL-226]

**Datoteke:** `domain/thesis.py`, `services/theses.py`, `routes/theses.py` in read-only povzetek review/proposal tabel; `ThesisList.tsx`, `ThesisDetail.tsx`, `ThesisReviewProposals.tsx`, `CreateThesisButton.tsx`, `AnalysisThesisAction`, API hooki, messages, ustrezni testi. Najprej uporabi obstoječo zgodovino in snapshot, brez novih meritev.

- [ ] RED read model: `last_review_not_updated_at`, `pending_is_not_applied_status`, `no_evidence_not_confirmed`, `filtered_count_before_limit`, `bounded_history_no_n_plus_one`, `over20_draft_preserved_with_explicit_limit`.
- [ ] Določi bounded DTO za seznam: kratko jedro, active/draft verzija, trenutno potrjeno stanje, pending_count, last_review_attempt/status/input_cutoff, najbližji znani rok. Odsotne vrednosti ostanejo null; stari datum urejanja ne nadomesti pregleda. Stare različice/zgodovina se nalagajo paginirano na zahtevo. Filter/count in seznam sta ista SQL kohorta.
- [ ] Uredi seznam/detail po UXT-01/02, filtri/stran v URL. Osrednja pending odločitev se ne izgubi med obrazci zgodovine. Vir, datum in morebitna govorica pri dokazu ostanejo vidni; tehnični model/UUID sta v razširitvi.
- [ ] Nastanek iz analize pojasni izvirni upgrade/downgrade pogoj, omogoči uporabnikov pregled besedila/horizonta in jasno opozori zamenjavo aktivne različice. Brez avtomatskega negiranja. Za osnutek/aktivacijo >20 ohrani vsebino in pokaži konkretno mejo nepodprtega samodejnega pregleda; ponudi izrecno uporabniško urejanje/združitev ali ročno spremljanje. Ne uvajaj novega limita aktivacije ali skritega pregleda prvih 20, ne spreminjaj obstoječih večjih tez. Podnabor/povečan limit zahtevata drug SPEC.
- [ ] Testiraj vse statusne konflikte/rumor/stale/pending, neshranjeno urejanje, aktivacijo in terminologijo »Osveži« proti »Zaženi pregled«. Obstoječi A1/A2/A4 testi ostanejo; nobene nove trditve o A3/A5. E2E v treh sintetičnih tezah + dolg osnutek, nato commit `feat(theses): prioritize evidence and review decisions [BL-226]`.

## T6: Strukturirana merila po horizontu — podatkovni SPEC pred kodo [BL-227]

**Prvi rezultat:** ločen `docs/superpowers/specs/<datum>-merila-tez-in-idej-spec.md` in majhen plan podprtih kazalnikov. Odvisnosti: obstoječi MetricValue/DataMeta, podatkovna pokritost BL-193/194/211, skladnost osnove teze in ročne ideje iz T3/T5. Ne začni z univerzalnim prostoprogramirljivim pravilnikom.

- [ ] Izberi najmanjši dokazljivo podprt nabor za kratko/srednje/dolgo obdobje iz UXM tabele. Za vsak tip pripravi source_field, unit/currency/basis/fiscal period/as_of in fixture. Zapiši tudi zavrnjene/nepodprte kazalnike; ne obljubi fundamentalov, ki jih vir ne daje.
- [ ] Dokončaj verzioniran Criterion/Observation in nespremenljivi activation baseline; metrike/dogodki/manual evidence se ne predstavljajo za enak numerični kriterij. Opažanja/restatement so append-only, primerjave Decimal in po izrecnem comparatorju, ne parsanje LLM teksta.
- [ ] RED fixture: `basis_mismatch_not_comparable`, `fx_or_unit_change_not_threshold_match`, `missing_stale_not_zero`, `restatement_keeps_baseline`, `criterion_edit_new_version`, `long_horizon_not_completed_at60`, `review_cadence_does_not_enable_llm`.
- [ ] Po neodvisnem pregledu podatkovnega SPEC implementiraj le izbrane metrike, z migracijo/pogodbo/zgodovino in testirano omejeno pridobitvijo opažanj. UI primerja Začetno / Zadnje / Sprememba / Dokaz / Naslednja preverba. Izpolnjeni prag in veljavni status teze ostaneta ločena.
- [ ] Različni horizonti ponudijo izbirne predloge meril, brez default-all in brez fiksnega števila meril. Uporabnik jih pred aktivacijo uredi. Lastne ideje lahko uporabljajo iste kriterije, vendar ne ustvarijo samodejne uradne teze. Commit šele za dejanski podprt obseg `feat(theses): add verified horizon criteria ... [BL-227]`.

## T7: Končni dokaz in pregled

- [ ] Preglej vsako zahtevo F-UX01–13 proti konkretnim izvedenim testom in označi delne vrzeli. Nedokončan T6 ni prikazan kot delujoč samo z novim obrazcem.
- [ ] Preveri potrebne API/agents/web regresije glede na dejanski diff; generirani API tipi, lint/typecheck/i18n, Linux build. Browser matrika vse strani, svetla/temna, SL/EN, desktop/phone, 200 %, missing/partial/error/rumor/pending/stale. Zapiši dejanske rezultate in namerne skip razloge, ne starih številk.
- [ ] Neodvisen povezan pregled nespremenljive identitete/časov, primerljivosti izidov, provenience in človeških odločitev. Ozke popravke po pregledu ponovno preveri; ne razširjaj paketa brez novega plana.
- [ ] Posodobi DESIGN/VOICE po dejanskih UI spremembah, SESSIONS/BACKLOG/ADR po resničnih odločitvah in pripravi uporabniški pregled :3100 s posnetki. Lokalni commit ni deploy ali GitHub push.
- [ ] BL-222, Flex/FX, dejanska SMTP dostava in predmigracijski restore imajo svoje pogoje in ostanejo sledljivi. :3000 zahteva novo izrecno potrditev, ki je ta UX plan ne daje.

## Naslednji konkreten korak

BL-223 in T1/BL-224 sta zaključena. Naslednji korak je dokaz T2 na izoliranih podatkih; T3/T4 morata skupaj dobaviti ročne ideje in obstoječa mnenja, ker je uporabnik to izrecno zahteval. T5 uporabi današnje dokaze, T6 pa zahteva ločen natančen podatkovni SPEC. Dodatna uporabniška vprašanja niso potrebna za imena tabel/gumbov; dejansko zasebno konfiguracijo/namestitev se razreši šele ob aktivaciji.
