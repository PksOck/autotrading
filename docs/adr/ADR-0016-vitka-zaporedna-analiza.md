# ADR-0016: Vitka zaporedna analiza delnice in meja 16k vhodnih žetonov
**Status:** sprejeto · **Datum:** 2026-10-27 · **Seja:** S-013

## Kontekst
Globinska analiza delnice je tekla na grafu TradingAgents in je porabila okoli 353 tisoč žetonov MiniMax na analizo. Glavni razlogi:
- analitiki so v vsakem od največ 20 krogov orodij znova poslali CSV in indikatorje;
- okoli 55 tisoč znakov poročil je šlo v sedem poznejših korakov, nato še v kartico in preverjanje hipoteze;
- strukturiran klic pri MiniMax pogosto pade, zato sledi še en klic s prostim besedilom.

Lokalni model (dirigent-64k) sprejme največ okoli 16 tisoč vhodnih žetonov na klic. Uporabnik želi, da čim več dela opravi koda, AI pa samo presodi in združi. Čas ni pomemben (lokalno je lahko 30 minut), odločitve pa morajo biti kakovostne in razumljive.

## Odločitev
1. **Koda pripravi povzetke** (`stock_analyst/digest.py`, brez LLM): trg (donosi, SMA50/200, RSI14, ATR %, 52-tedenski razpon, volumen), temelji (metrike Finnhub, pasovi vrednotenja, kakovost, izvleček poročil EDGAR, če je na voljo) in novice (brez podvojenih, uradni viri prvi, govorice označene, Form 4 kot število). Vsak povzetek ima vir in `as_of` in obsega največ okoli 3000 znakov.
2. **Zaporedni analitiki** na vlogi `deep_quick_role`: tehnični, nato temeljni, nato novice. Vsak dobi svoj povzetek in zbrane sklepe prejšnjih. Vrne strukturiran zapis (stališče −2..+2, ključne točke, tveganja, kaj spremljati). Poročilo v časovnici izriše koda.
3. **Pregled po področjih:** bik in medved vidita samo zapise analitikov in tabelo ključnih številk.
4. **En končni odločevalec** na vlogi `deep_deep_role` vrne oceno, razloge, tveganja, pogoje za dvig in znižanje, prepričanje, spremembo glede na prejšnjo analizo in sodbo o hipotezi. Pri delnicah to nadomesti ločena klica za kartico in hipotezo.
5. **Neobvezen lokalni klic** sestavi kratek povzetek za uporabnika. Če pade, povzetek sestavi koda.
6. **Register dokazov:** koda iz povzetkov sestavi en omejen register. Vsak dokaz ima oznako (npr. `N1`), vrsto, vir, `as_of` in podatek, ali je potrjen (govorica ni). Vsi koraki vidijo isti register in se nanj sklicujejo z oznakami. Koda zavrže neznane oznake. Če nakup, povečanje ali potrjeno hipotezo podpirajo samo govorice, oceno zniža na Hold oziroma sodbo na `partly` (AGENTS.md, pravilo 4). Pri krajšanju odpadejo celi dokazi, nikoli pol stavka. Najprej ostanejo strukturirana dejstva o instrumentu (trg, temelji, insajderji, kontrola), nato poročila EDGAR, nato novice instrumenta. Splošne tržne novice (`macro`, oznaka `G`) so samo kontekst: največ 5, nikoli uradne, zato ne morejo potrditi govorice o podjetju. Vsak klic dobi tudi `instrument` (simbol, ime, borza, `as_of`). Prvi živi tek je pokazal, zakaj: 40 tujih sporočil za javnost je izrinilo vsa tržna dejstva, model pa ni vedel, katero podjetje analizira.
7. **Meja vhoda:** vsak klic gre skozi `budget.py`. Ocena je znaki / 2 in šteje sistemski poziv, vhod in shemo. Delovna meja je 12 tisoč, trda 16 tisoč, z rezervo za en popravni poskus odjemalca. Kar ne gre v mejo, se skrajša po prednosti. Če niti to ne zadošča, klic ne gre naprej. Ista meja velja za kartico in hipotezo pri ETF. Vsaka vloga ima zgornjo mejo izhoda (analitiki in pregled 6000, odločitev 10.000, povzetek 2000). Meja šteje tudi skrito razmišljanje MiniMax: pri meji 1500 je prvi živi tek porabil vse za razmišljanje in vrnil prazen odgovor. Popravni poskus pošlje nazaj samo vidno vsebino, zato rezerva zanj šteje največ 2000. MiniMax ne upošteva `response_format`, zato odjemalec shemo JSON pošlje tudi v sistemskem pozivu; brez tega je model ugibal polja in porabil večino izhoda za razmišljanje.
8. **Preverjanje številk po plasteh:** po vsakem koraku koda preveri številke v besedilu AI. Številko, ki je ni v registru, nadomesti z `[?]`, preden jo vidi naslednji korak ali časovnica, in jo zapiše v opozorilo `unverified_numbers` (AGENTS.md, pravilo 3).
9. Poraba po klicih in skupaj se shrani v `models.usage` analize.

## Posledice
- Pričakovano okoli 6 klicev s po 4–8 tisoč vhodnimi žetoni, skupaj okoli 40–50 tisoč namesto okoli 350 tisoč.
- Isti tok lahko teče na lokalnem modelu.
- Pri delnicah se graf TradingAgents ne uporablja več. Odstranitev knjižnice in njenih testov je ločena naloga.
- Analiza vidi manj surovih podatkov, kot jih je imel graf z orodji. To je namerno: številke izračuna koda, AI jih samo razlaga.

## Zavrnjene možnosti
- **Krajši pozivi v grafu TradingAgents:** krogi orodij in pošiljanje celotnih poročil naprej ostanejo, zato se poraba ne zmanjša dovolj in vhodi ne pridejo pod 16k.
- **En sam velik klic:** ne gre v mejo lokalnega modela, odločitev pa je težje sledljiva po področjih.
