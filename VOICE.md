# VOICE.md: ton, jezik, besedila

## 1. Ton

| Je | Ni |
|---|---|
| jasen, kratek, stvaren | hiperboličen ("ogromna priložnost!", "raketa") |
| previden pri gotovosti ("verjetno", "kaže na") | samozavesten brez podlage ("bo zrasla") |
| konkreten (številka, datum, vir) | splošen ("trg je nervozen") |
| miren tudi pri slabih novicah | alarmanten, kričeč |
| spoštljiv do uporabnikove odločitve | ukazovalen ("kupi zdaj") |

**Preizkus:** bi to napisal izkušen analitik v interni zapisek kolegu? Če ne, prepiši.

## 2. Slovenska pravila

- **Naslavljanje:** v UI nevtralno, z nedoločnikom ali samostalnikom pri dejanjih (*Zaženi analizo*, *Zavrzi*, *Shrani*). V daljših razlagah **tikanje** (osebno orodje): *"Teza drži, padec je posledica sektorja."*, *"Tvoja pozicija je 6,2 % portfelja."*
- **Gumbi:** glagol v velevalniku, 1 do 3 besede: *Analiziraj*, *Sprejmi*, *Spremljaj*, *Zavrzi*, *Odpri v IBKR*.
- **Naslovi:** samo prva beseda z veliko začetnico (*Vstopne točke danes*, ne *Vstopne Točke Danes*).
- **Brez** klicajev, emojijev in pomišljajev kot ločil v stavku (uporabi vejico, dvopičje ali nov stavek).
- **Anglizmi,** ki jih sprejmemo, ker so v slovenskem vlagateljskem žargonu bolj razumljivi: *watchlista*, *ETF*, *call*, *put*, *strike*, *spread*, *stop*, *filing*, *P/E*. Drugo prevajamo (glosar §4).
- **Tikerji** ostanejo nespremenjeni in v monospace: `AMZN`, `VWCE`.

## 3. Formati (vedno prek `Intl`, nikoli ročno)

| Podatek | `sl` | `en` | Opomba |
|---|---|---|---|
| število | 1.234,56 | 1,234.56 | `Intl.NumberFormat(locale)` |
| odstotek | +4,2 % | +4.2% | vedno predznak pri spremembah |
| cena USD | 184,20 $ | $184.20 | valuta instrumenta, ne preračunavamo samodejno |
| velike vrednosti | 1,2 mrd $ | $1.2B | kompaktni zapis |
| datum | 22. 10. 2026 | Oct 22, 2026 | |
| datum + čas | 22. 10. 2026, 15:30 | Oct 22, 2026, 3:30 PM | lokalni čas uporabnika |
| relativni čas | pred 12 min | 12 min ago | `Intl.RelativeTimeFormat` |
| razpon | 178–182 $ | $178–182 | stični pomišljaj samo v razponih |

**Spremembe** imajo vedno predznak in puščico (▲ +2,1 %, ▼ −3,4 %), barva je samo dodatek.

## 4. Glosar SL ↔ EN (ključni izrazi)

| SL | EN | Ključ v `messages` |
|---|---|---|
| signal | signal | `signal.*` |
| predlog (ročni) | proposal | `proposal.*` |
| hipoteza | hypothesis | `proposal.hypothesis` |
| globina analize: hitro / standardno / globoko | depth: quick / standard / deep | `proposal.depth.*` |
| vstopna točka / vstopna cona | entry point / entry zone | `entry.*` |
| katalizator | catalyst | `signal.kind.catalyst` |
| opozorilo za izstop | exit warning | `signal.kind.exit_warning` |
| teza / zlom teze | thesis / thesis break | `thesis.*` |
| govorica, nepotrjeno | rumor, unconfirmed | `radar.rumor` |
| potrjeno | confirmed | `radar.confirmed` |
| dogodek | event | `radar.event` |
| ocena priložnosti | opportunity score | `radar.score` |
| pomembnost | materiality | `radar.materiality` |
| novost | novelty | `radar.novelty` |
| odziv cene | price reaction | `radar.reaction` |
| vzrok padca | drawdown cause | `entry.cause.*` |
| trg / sektor / začasno / temeljno | market / sector / transient / fundamental | `entry.cause.*` |
| postopni nakup (lestvica) | scaled entry (ladder) | `entry.ladder` |
| zaupanje | confidence | `signal.confidence` |
| moč | strength | `signal.strength` |
| horizont | horizon | `signal.horizon` |
| dnevi / tedni / meseci / leta | days / weeks / months / years | `signal.horizon.*` |
| izpostavljenost | exposure | `portfolio.exposure` |
| prekrivanje (ETF) | overlap | `etf.overlap` |
| analiza (agentski zagon) | analysis (agent run) | `analysis.*` |
| razdeljeno mnenje | split opinion | `analysis.split` |
| potreben pregled | needs review | `rating.review` |
| vir / osveženo | source / updated | `provenance.*` |
| zastarelo | stale | `state.stale` |

**Ocene** (5-stopenjska lestvica iz TradingAgents):

| Interno | SL | EN |
|---|---|---|
| `Buy` | Kupi | Buy |
| `Overweight` | Povečaj | Overweight |
| `Hold` | Drži | Hold |
| `Underweight` | Zmanjšaj | Underweight |
| `Sell` | Prodaj | Sell |
| `REVIEW` | Potreben pregled | Needs review |

## 5. Vzorci besedil

**Razlaga signala (`rationale`):** 1 do 3 stavki, najprej *kaj*, nato *zakaj*, nato *kaj bi to ovrglo*.

> AMZN je 4 % nad SMA200 po 14 % padcu od vrha. Padec sledi sektorju (XLY −11 %), teza o rasti AWS ostaja nespremenjena. Ovrglo bi jo poročilo z rastjo AWS pod 15 %.

**Govorica:**

> **Nepotrjeno.** Na Redditu in X narašča omemba prevzema podjetja XYZ (8× nad povprečjem). Uradnega vira ni. Signal se nadgradi, ko se pojavi 8-K ali sporočilo za javnost.

**Telegram obvestilo** (največ 4 vrstice, simbol najprej):

```text
▲ Vstop · MSFT · v coni 402–410 $
Padec −9 % sledi sektorju, teza drži. Moč 0,72
Lestvica: 40 % @ 408 · 30 % @ 401 · 30 % @ 394
Odpri: https://preza.<tailnet>/s/8f3a
```

**Prazna stanja:** povej, zakaj je prazno in kaj lahko narediš.

> Danes ni novih vstopnih točk. Pragovi so strogi, kar je dobro. Nastavitve pragov: Nastavitve › Vstopi.

**Napake:** kaj se je zgodilo, posledica, kaj narediti. Brez opravičevanja in brez tehničnega žargona v prvem stavku.

> IB Gateway ni povezan. Cene so stare 2 h. Odpri IBKR Mobile in potrdi prijavo.

## 6. i18n: kako je zasnovano

- **Knjižnica:** `next-intl` (App Router, strežniške komponente).
- **Datoteke:** `apps/web/messages/sl.json` (privzeto, vir resnice) in `apps/web/messages/en.json`. Ključi so hierarhični po modulih (`nav.radar`, `entry.cause.sector`).
- **Privzeti jezik:** `sl`. Izbira se shrani v piškotek `locale` in v uporabnikove nastavitve (baza). Preklop je v glavi (SL | EN) in v Nastavitvah.
- **Pravilo:** v komponentah ni nobenega besedila. Manjkajoč ključ v `en.json` pade nazaj na `sl.json`, CI pa opozori (`BL-008`).
- **Množina:** ICU sintaksa (`{count, plural, one {# signal} two {# signala} few {# signali} other {# signalov}}`). Slovenščina ima 4 oblike, zato jih vedno navedi vse.
- **Številke, datumi, valute:** samo prek `useFormatter()` iz next-intl, ki uporablja `Intl`.
- **Podatki iz baze** (imena podjetij, naslovi novic) se ne prevajajo. Prevajajo se samo **povzetki agentov** (§7).

## 7. Jezik agentov

- **Sistemski pozivi in notranje razmišljanje agentov:** angleščina.
- **Polja za uporabnika** (`rationale`, `executive_summary`, teze): generirajo se v jeziku uporabnika (`output_language` v kontekstu). Če se jezik zamenja, se star povzetek prevede z `local-fast` in označi "prevedeno".
- **Agenti pišejo po §1 in §5:** brez hiperbol, z navedbo virov `[1]`, `[2]`, ki se v UI pretvorijo v povezave.
- **Prepovedane besede v izhodih agentov** (preverja post-procesor): *zagotovo, garantirano, ne more pasti, raketa, to the moon, all-in*.
