# Izvedbeni SPEC: dodatni krog po Claudovem pregledu

**Datum:** 2026-10-30 · **Osnova:** `c55e37d` · **Naloge:** BL-218 in del BL-214; dokumentarni prevzem BL-219.

**Status:** konkretna pogodba za naslednji izvedbeni krog; implementacija in novi regresijski dokazi še niso izvedeni. Uporabnikov »Go« v tem koraku potrjuje vključitev pripomb v plan/SPEC, ne merge, pošiljanja sporočil ali deploya.

**Vir:** [Claudov pregled](../../implementation/2026-10-30-claude-pregled-9ec9e88.md). Poročilo ohranjamo kot zgodovinski dokaz, ne spreminjamo njegovih ocen v naknadne rezultate.

## 1. Obseg in razdelitev

| Pripomba | Ta krog | Preostali SPEC / pogoj |
|---|---|---|
| D1 | Popravek izgubljene pokritosti ob ponovnem uvozu | S-B še vedno zahteva dejanski očiščen Flex |
| A1 | Varovalo pred vsakim HTTP poskusom, tudi popravljanjem JSON | Ne nadomešča skupnega časovnega roka BL-180 |
| A2 | Preverjanje po rezervaciji/zaklepu in varovan samodejni pregled teze | Reprodukcija dirke obvezna, ker je pregled to označil kot verjetno napako |
| A4 | Poštena in omejena dostava dovoljenih izvedb outboxa | Brez spreminjanja ročnih dovoljenj ali samodejnih plačljivih ponovitev |
| U1, U2 | Pravilne povezave in ohranitev trenutne študije | Trajna ohranitev po reloadu ostane ločena nadgradnja; to ni BL-204 |
| D2 | Predpisan dokaz in pogodba v S-B, ne ugibana obdelava `Re` | Ločiti open snapshot od change/reversal; očiščen dejanski primer |
| D3 | V S-B izrecno ločiti complete/partial/missing tudi v glavi | Ne razglasiti partial za dokaz vseh prejemkov |
| F1 | Blokada pravilnega konsolidiranja v S-B | Bazna valuta računa in FX cilj morata biti znana in enaka zahtevani bazi |
| B5 | S-B/BL-205 | BASE_SUMMARY-only ne sme pomeniti popolnega praznega stanja |
| A3, A5 | S-G1, pred varnim prevzemom procesov | Živ lastnik proti opuščenemu klicu; `running` sam ne dovoljuje ponovitve ali zaključka |
| R1 | Samostojni manjši popravek, S-G1 / podatkovno filtriranje | Članstvo v Radar pogledu pred LIMIT, ne `limit*3` pred članstvom |
| E1 | S-F/BL-212, dokaz pred vklopom kanala | Pravi SMTP samo za odobreno vsebino/prejemnika; fake testi niso prava dostava |

Predzdružitveni minimum je D1/A1/A2/A4/U1/U2. To ne pomeni, da so starejše finančne napake sprejemljive za živo objavo. F1/B5, D2 in A3/A5 ostanejo izrecno razrešeni ali kot konkretne blokade ustreznega obsega izdaje. Dokument o izdaji ne sme razglasiti napačne finančne vsote za kozmetično omejitev.

## 2. Skupne pogodbe

- Ohrani finančno semantiko, Decimal, source/as_of in ločitev manjkajočega od ničle. Ni novih ponudnikov ali LLM vlog.
- Vsi modeli tečejo prek LiteLLM. Tekoč HTTP klic se lahko dokonča; naslednji, vključno s popravnim poskusom, mora ponovno pridobiti dovoljenje.
- Ročni izvor/izjema okna izhajata iz obstoječe strežniško ustvarjene trajne izvedbe, ne iz poljubnega uporabniškega parametra. Revizija in kvota ostaneta veljavni.
- Noben popravek ne sproži nove analize, SMTP/Telegram sporočila ali avtomatsko omogoči procesa ob migraciji.
- Sprememba sheme zahteva novo zaporedno migracijo po dejanskem trenutnem headu; obstoječih migracij 0016–0019 ne prepisujemo. Za neposrednih šest popravkov nova shema ni privzeti cilj.
- UI besedila so SL/EN, obstoječi URL parametri in fokus se ohranijo. Rezultat študije je vezan na oddane parametre, ne na kasnejši osnutek obrazca.

## 3. R-D1: odsotna sekcija ni izbris prejšnjega dokaza

**Lastništvo:** `services/api/preza/services/dividends.py`, po potrebi parser in testi pogodbe.

Obstoječi ključ coverage je račun/sekcija/obdobje/as_of, razvrščanje revizij uporablja snapshot_version. V tem krogu ohranimo obstoječi ključ in pomen, ne izpeljemo nove brokerjeve identitete.

| Shranjeno | Novi uvoz istega ključa | Zahtevano |
|---|---|---|
| ni zapisa | missing | Zapiši manjkajočo pokritost, ne ustvarjaj gotovine/obračunov |
| partial/complete | missing | Ohrani zadnji dejanski payload in row_keys; ne skrij obveznosti |
| missing | partial/complete iste ali novejše revizije | Sprejmi dejanski dokaz |
| partial/complete | podprta sekcija s starejšo revizijo | Ohrani novejši dokaz |
| partial/complete | podprta izrecno prazna novejša sekcija | Prazni posnetek je avtoritativen; stari odprti obračuni izginejo iz aktivnega pogleda |

Enaka ponovitev ostane idempotentna. Neskladna vsebina iste identitete knjižbe ali accruala ostane konflikt celotne transakcije; sprememba pogoja coverage upserta ne sme izključiti teh varoval. Slabo oblikovane sekcije ne smejo biti tiho pretvorjene v prazno complete.

**Prevzem T-D1:** dva uvoza isti račun/isti dan/obdobje, prvi z odprtim obračunom, drugi brez sekcije; GET še pokaže prvotni obračun in dokaz pokritosti. Dodatno: prvi missing → drugi complete, replay, starejši complete ter novejši izrecno prazen complete. Prazna sekcija mora res nadomestiti odprto stanje; zato prepoved vseh coverage posodobitev ni pravilen popravek.

## 4. R-A1: dovoljenje pred vsakim poskusom transporta

**Lastništvo:** `preza/llm/client.py`, `llm/automatic.py`, njihovi protokoli in scripted testi.

Predlagan interni vmesnik, ki ga mora izvedba dosledno tipizirati:

```python
AttemptGuard = Callable[[], Awaitable[None]]
# keyword-only razširitev LiteLlmClient.complete_json:
before_attempt: AttemptGuard | None = None
```

Osnovni Llm protokol ostane združljiv; za varovan avtomatski transport se uvede eksplicitna razširjena pogodba (npr. AttemptGuardedLlm). Produkcijski AutomaticLlm mora uporabiti transport, ki hook dejansko podpira. Ne podati keyworda slepo v stare implementacije in ne ponoviti neuspelo varovanega klica brez varovala kot fallback. Testni dvojnik naj hook podpira ali izrecno simulira transport brez notranjih ponovitev.

- Hook se čaka neposredno pred vsakim `_post` poskusom v zanki, vključno z drugo JSON/schema popravo. Ne pripne se kot globalna mutable nastavitev skupnega klienta, ki bi spremenila ročne klice.
- Zavrnitev prepreči HTTP; ohrani že porabljene žetone/stroške in dejansko število izvedenih transportov. Odločitev pred drugim HTTP ne sme poročati dveh izvedenih klicev.
- Uvedi jasno kodo `automatic_analyses_disabled` za nadzorovan stop. Ne preslikaj je v veljavno mnenje, nevtralni sklep ali priporočilo; obstoječih truncation/schema kod ne izgubi.
- Manual brez hooka ohrani dosedanje vedenje in kvoto. Embedding pred svojim transportom še naprej preveri dovoljenje.
- Hook ni atomski preklic že začetega HTTP; obljuba je novo preverjanje neposredno pred naslednjim poskusom. Ne držati DB zaklepa čez modelni HTTP.

**Prevzem T-A1:** scripted transport vrne neveljaven prvi odgovor in vmes izklopi kontrolo; drugi HTTP se ne zgodi. Vključena kontrola dopušča popravo; manual poprava ostane dovoljena. Dodatno izklop pred prvim klicem (0 HTTP), ohranitev `max_output_tokens`, usage prvega klica in razlog ustavitve. Test uporablja fake transport, ne dejanskih modelov.

## 5. R-A2: varovan pregled teze po čakanju na zaklep

**Lastništvo:** `services/agents/preza_agents/thesis_tracker/runner.py`, worker in veljavna trajna dovoljenja pregleda.

- Pred rezervacijo ostanejo obstoječa varovala. Po morebitnem čakanju v `mark_dispatched` in commitu je neposredno pred transportom potrebno novo preverjanje dovoljenja.
- Za avtomatski pregled se uporabi varovan klient iz R-A1, da se kontrola preveri tudi pri notranji popravi odgovora. Ročni pregled je določen z validirano trajno izvedbo, ne s poljubnim ctx flagom.
- Manual ob globalni pavzi/izklopu samodejnih analiz ostane mogoč, če je že dovoljen po politiki, reviziji in izrecni izjemi okna. Avtomatsko izven okna se ne predstavlja kot manual.
- Blokiran prehod po rezervaciji, vendar pred prvim HTTP, mora imeti sledljiv razlog in znano ničelno porabo za ta poskus. Ne ostane v `running` in ne sproži samodejne ponovitve. Ne zaključuj drugega še živega lastnika kot prekinjenega.

**Prevzem T-A2:** deterministična bariera/zaklep zadrži dispatch; druga povezava izklopi kontrolo pred sprostitvijo. Po sprostitvi ni modelnega klica. Dodaj avtomatsko JSON popravo z izklopom, dovoljeni manual zunaj okna, neveljavno članstvo/revizijo izvedbe in konkurenčno aktivno rezervacijo. Sam mock enega predhodnega gate brez zaklepa ne potrdi tega scenarija.

## 6. R-A4: blokirane izvedbe ne izstradajo dovoljenih

**Lastništvo:** `services/api/preza/services/automation.py:deliver_pending`, ProcessExecution/ProcessPolicy/AutomationControl, Redis enqueue dvojnik.

- Izbor upošteva pending stanje, zapadlost, politiko/revizijo, manual/automatic in izjemo okna. Meja 100 ne sme biti uporabljena nad nefiltriranimi blokiranimi vrsticami.
- Trajno zastarela revizija se zaključi kot `skipped` z razlogom, brez modelnega klica. Trenutni `disabled`, `paused`, `outside_window` in `analyses_disabled` so začasni: ne smejo trajno uničiti dovoljenega ročnega zahtevka ali dokazati uspeha.
- Prednostna izvedba: izračun dovoljenih kombinacij procesa/izvora/okna in filtriranje pred omejitvijo, nato omejeno keyset pregledovanje dostave. Cursor ne temelji samo na času; vez je `(scheduled_for, id)`.
- Posamezen tick ima največ 100 novih dostav in največ 1000 pregledanih kandidatov. Če je potrebna nadaljevalna točka med ticki za poštenost, jo izvedba trajno shrani in preveri po restartu; ne uporabljaj samo procesnega pomnilnika. Če to zahteva shemo, se pred kodi pripravi natančna migracijska dopolnitev SPEC.
- Že dostavljen/dedupliran pending posel, Redis nedosegljivost in neveljavna revizija ne smejo trajno preprečiti napredovanja drugih kandidatov. Ohranjen job_id in claim ostaneta zaščita pred dvojno izvedbo, ne povečuj job ID samo zaradi ponovnega enqueue.
- Gate se ponovno preveri ob prevzemu. Sočasna schedulerja ne izvedeta istega namena dvakrat. Ne uvajati slepega plačljivega retryja.

**Prevzem T-A4:** 100 blokiranih in 1 dovoljena izvedba → dovoljena dostavljena v istem ticku. Nadalje: 100 enako časovno označenih zapisov, začasna pavza → resume, stara revizija → skipped, manual override, že enqueued prvi blok, Redis failure/recovery, dve dostavljalni zanki ter več kot 1000 kandidatov z dokazom končnega napredovanja. Poizvedbe/delo imajo zgornjo mejo; samo odstranitev LIMIT ni popravek.

## 7. R-U1/U2: pravilni cilji in ohranitev študije

**Lastništvo:** `apps/web/components/track-record/BacktestPanel.tsx` in njegovi testi; obstoječi EntityLink/usePeek.

Izbrana majhna izvedbena usmeritev (presoja izvajalca, ne nova uporabnikova oblikovna zahteva):

- `source=signal`: obstoječi `EntityLink` odpre signalni Peek z mehko navigacijo, ohrani pot/parametre in trenutni rezultat. Close/Escape odstranita samo peek, browser Back pravilno obnovi predhodni URL in fokus.
- `source=analysis`: Next Link na `/analysis/{id}` v novem zavihku z `rel=noopener noreferrer` ter prevedeno oznako novega zavihka. Tako uporabnik vidi pravi obstoječi zaslon analize, trenutna študija pa ostane v prvotnem zavihku. Ne ustvarjaj nepodprtega `peek=analysis`.
- Ne odpiri celotne analize s polno navigacijo v istem zavihku, dokler stanje izračuna ni trajno shranjeno. Sprememba osnutka obrazca ne sme preimenovati že izračunanih rezultatov.
- Uporabi interni ID analize/signala iz vrstice, ne simbol ali prvi rezultat iskanja. Različna vira z enakim UUID imata še vedno ločena cilja.

**Prevzem T-U:** izračun iz signalne in analizne vrstice; pravo href/cilj, klik signal → close/Escape/Back ohrani oddane parametre in vse rezultate ter ne ponovi POST /backtest. Analiza se odpre na pravilnem `/analysis/{uuid}`, prvotni zavihek je nespremenjen. Preveri SL/EN, modifiers/new-tab, telefon in tipkovnico. Test zgolj obstoja href ne nadomesti preverjanja ohranitve študije.

## 8. Pogodbe za naslednje SPEC in pogoje izdaje

### S-B: D2/D3/F1/B5 in dejanski Flex

- D2 zahteva fixture z `ChangeInDividendAccrual` `Re`. Ne obravnavaj vsakega `Re` kot negativnega denarja ali novega pričakovanega bruto zneska in ne odstrani vseh popravkov brez potrjenega pomena. Loči spremembo upravičenja, preklic, poravnavo in cash. Reprodukcija ostane odprta do dokaza.
- D3: oznaka popolne potrditve temelji samo na `complete`. `partial` mora pokazati vrzeli in poročano obdobje, `missing` ne dokazuje ničelnih prejemkov. Preveriti dejansko sedanje besedilo, saj oznaka »izpis do« ni nujno trditev o popolnosti.
- F1: FX mora imeti izvorno in ciljno valuto ter osnovo računa. Zneski v bazah USD in EUR se ne seštejejo kot ista baza. Stari zapisi brez dokazane ciljne valute ostanejo unknown/missing_fx; backfill ne ugiba. Nova shema/migracija/backfill in fixture dveh računov sta obvezni del S-B.
- B5: BASE_SUMMARY-only ni izrecno prazen izvirnovalutni cash snapshot. Odsotne valute ali nepopolne sekcije ne prepišejo zadnjega veljavnega stanja.
- Očiščen dejanski razširjeni XML je kritični vhod. D1 je mogoče popraviti in sintetično dokazati prej; to še ne zapre BL-202 ali celotnega paketa B.

### S-G1: A3/A5/R1

- `running` ni dovolj za nov plačljiv klic niti za oznako failed_unknown. Dokazati lastništvo/lease/heartbeat in dejansko živost opravila; redelivery živega lastnika ne spremeni ali ponovi dela.
- Opuščen dispatch dobi terminalno negotovo stanje s sledjo, brez slepe ponovitve; pri API AnalysisRun upoštevaj obstoječi dovoljeni status in ločeno kodo razloga, ne uvajaj nepodprte statusne vrednosti samo po besedilu pregleda.
- A5 test potrebuje drug executor, iztečen heartbeat in restart; živega lastnika ni dovoljeno zaključiti. A3 test: dvakrat dostavljen isti run naredi največ en plačljiv dispatch.
- R1: članstvo portfelja/watchliste v SQL pred sortiranim LIMIT; test z več kot `limit*3` tujih dogodkov in ustreznim dogodkom zadaj. Obstoječa exact-ID detail pot ostane nedotaknjena.
- Trajna oddaja predloga BL-204 je povezana, a drugačna pogodba od ponovnega prevzema že ustvarjenega opravila; oba dobita ločene teste.

### Obnovljivost in prevzem

Backup/restore je pred katerokoli prvo živo migracijo, tudi pred že pripravljenimi 0016–0019. Enkratni dump brez restore ni dokaz povratka. Ob združevanju uskladiti manjkajoči S-014 iz osnovnega checkouta brez prepisovanja drugih sej. Stari statusi BL-011/013/174 se zaprejo samo po dokazu in s povezavo na nadomestno nalogo; ne samodejno po priporočilu.

**M — združitev:** ločen pregled kode in zelen dokazni paket ter preverjena osnova/sočasno delo; avtorizacija združitve se preveri v uporabniških navodilih, ne izpelje iz pregledovalčevega »merge takoj«.

**D — namestitev :3000:** ločena nova izrecna potrditev uporabnika, fresh backup/restore dokaz, preverjene aktivne vrste, migracijski/rollback plan in smoke. Zelena M ne pomeni odobrene D.

## 9. Izhodni dokazni paket

Za vsako ID pripombe: najprej padajoči reprodukcijski test, popravek, uspešen isti test in širša regresija. A2/A5/D2 ohranijo oznako »verjetno/nepreverjeno« do ustrezne reprodukcije, ne prepišejo se samodejno v potrjeno napako ali done.

Koda/testi/napake/prevodi in generirane pogodbe morajo biti skladni. Zabeležiti točen testirani commit, bazo, ukaze in izide; prejšnjih Claudovih 554/221/155 ne predstavljati kot nov rezultat tega kroga. Noben test ne uporablja žive baze ali resničnih modelov/prejemnikov.
