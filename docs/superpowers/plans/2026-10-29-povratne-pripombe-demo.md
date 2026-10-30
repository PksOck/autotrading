# Dopolnitve po uporabniškem pregledu demo okolja

> Izvajanje: superpowers:subagent-driven-development; dopolnitev že potrjene izvedbe na isti izolirani veji. Uporabnik zahteva nadaljevanje in minimalna vprašanja. :3000 ostane nedotaknjen do nove potrditve.

## Zasnova in odločitve

Ohranimo obstoječo aplikacijo in vrnemo uporabne vizualizacije na preverjenih podatkih. Popoln povratek na vzorčno glavno stran bi prikril dejanske podatkovne vrzeli; prazna poenostavljena stran je izgubila uporabno orientacijo. Izbrana izvedbena presoja: prejšnja postavitev z dejanskimi podatki in izrecnimi vrzelmi.

Standardni portfelj ima identiteto, količino, ceno, vrednost, težo, nerealizirano in danes. Standard je vedno dosegljiv kot profil; uporabnik lahko dodaja stolpce. Mini trend vsebuje do 30 shranjenih dnevnih sveč, dejanski datumski razpon in stanje vrzeli. Plus/minus ima predznak in semantično barvo. Status cone je iz podatkov Vstopov, ne iz ugibanja.

Dividende prevzamejo kartice/tabele portfelja. Potrjene knjižbe ostanejo ločene od odprtih upravičenj in ocen iz zadnje potrjene osnove. Čas uvoza ni dokaz izplačila. Novi uvoz ponovno preveri dejstva; konfliktov identitet ali zneskov ne prepisujemo. Brez koledarja izplačil ne izmišljamo mesečnih dogodkov.

Uporabnik je potrdil SMTP in prvo testiranje shranjenih signalov/mnenj brez novih plačljivih LLM klicev. SMTP poverilnice so samo strežniške; več naslovov in vrste obvestil so validirane nastavitve. Med razvojem ne pošiljamo e-pošte.

Testiranje je študija ločenih dogodkov, ne simulacija celotnega portfelja: signal/mnenje postane znano ob created_at oziroma finished_at, vstop šele na naslednjem trgovalnem dnevu po UTC dnevu razpoložljivosti, izstop po izbranem številu shranjenih sej. Strošek na vsako stran v bazičnih točkah; delne zgodovine, nevtralne smeri in manjkajoči zaključki imajo razloge preskoka. Ni reinvestiranja, leverage, namišljenih poslov ali prepisovanja zgodovinskih izidov. Pristranskost preživelih, revizije cen in manjkajoča korporativna dejanja morajo biti vidni.

## Naloge

- [x] BL-206: Standardni profil, barve, trend z obdobjem, cona; regresije za povratek iz Vrednotenja/Dividend in neprikrito neznano stanje.
- [x] BL-207: Pregled trga, Portfelj danes, signalna moč/barve, razloženi Radar 7 dni in lijak s pravilno kohorto; brez vzorčnega fallbacka.
- [x] BL-208: Poenostavljene nastavitve z zložljivimi procesi/razlago, glavno stikalo samodejnih analiz, SMTP več prejemnikov; testi blokiranja in validacije.
- [x] BL-209: Dividendna oblikovna uskladitev in nadzori potrjeno/ocena, primeri tez (aktivna/osnutek/opozorilo) v izključno sintetičnem demu.
- [x] BL-210: Deterministično testiranje shranjenih signalov in končnih mnenj agentov; nastavljiv horizont/strošek/vir/obdobje, izidi in preskoki z dejanskimi datumi.
- [x] Integracija: fragmenti SL/EN, OpenAPI/TS, modeli/routerji/migracije, testne baze ločene, Docker build in objava samo :3100, brskalniški pregled desktop/telefon.
- [x] Prevzem: DESIGN/BACKLOG/SESSIONS in pregled sprememb; navesti omejitve in dejansko izvedene preizkuse. Brez posodabljanja :3000.

## Preverjanje

Pred spremembo vedenja ciljna regresija najprej pade; potem popravek in ciljni test. Matematični testi pokrijejo smer/ceno/datum/stroške in nepopolno zgodovino. DB testi ne tečejo vzporedno v isti bazi. SMTP testi uporabljajo ponarejen transport, nobenega resničnega sporočila. Demo seed mora biti ponovljiv in varovan s PREZA_DEMO_DB=1; nov zagon ne sme izbrisati uporabniških produkcijskih podatkov.

## Končni prevzem

Izvedeno v S-018, podrobnosti in dejanski testi v docs/implementation/2026-10-29-dopolnitve-po-pregledu.md. Viri makro podatkov, resnični razširjeni Flex in dejanska SMTP povezava ostajajo izrecne vrzeli, ne potrjeni rezultati. :3000 ni posodobljen.
