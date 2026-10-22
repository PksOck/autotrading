# BRAND.md

## 1. Ime

**Preža** (potrjeno v S-002)

- *Biti na preži* pomeni mirno opazovati in čakati na pravi trenutek. To je bistvo dolgoročnega vlagatelja, ki ne lovi vsakega gibanja, ampak pravi vstop.
- Kratko, slovensko, brez kolizije z znanimi finančnimi produkti.
- V angleškem vmesniku ostane **Preža** (brez prevoda). Opis za angleški vmesnik: *"Preža: opportunity radar for long-term investors"*.

Ime se uporablja samo v `apps/web/messages/*.json` (`app.name`), naslovu strani in Telegram botu.

## 2. Pozicioniranje

> **Preža opazuje trg namesto tebe in te pokliče, ko se nekaj res zgodi ali ko je cena prava. Pove, zakaj, in pokaže dokaze. Odločiš ti.**

| Smo | Nismo |
|---|---|
| radar in raziskovalni asistent | trgovalni robot |
| za dolgoročne pozicije, občasno kratkoročne priložnosti in opcije | za dnevno trgovanje in skalpiranje |
| preverljivi: vsak signal ima vir, čas in razlago | črna škatla z "zaupaj mi" priporočili |
| mirni: malo, a pomembnih obvestil | igralnica z rdečimi utripajočimi številkami |
| osebno orodje enega vlagatelja | produkt za stranke |

## 3. Načela znamke (veljajo tudi za odločitve v izdelku)

1. **Mir pred hrupom.** Raje 3 dobri signali na teden kot 30 povprečnih. Privzeti pragovi so strogi.
2. **Dokaz pred mnenjem.** Vsaka trditev ima povezavo na vir (novica, filing, indikator, izračun).
3. **Razlika med govorico in dejstvom je vidna.** Govorice imajo svojo barvo in oznako in nikoli niso priporočilo za nakup.
4. **Odločitev je tvoja.** Sistem predlaga, ti potrdiš. Brez samodejnih naročil.
5. **Poštenost do sebe.** Sistem meri lastno uspešnost in jo kaže na vidnem mestu, tudi ko je slaba.

## 4. Imena modulov (uporabljaj dosledno)

| Modul | SL (UI) | EN (UI) | Kratek opis | Zaslon |
|---|---|---|---|---|
| Pregled | Pregled | Overview | dnevni povzetek: novo, portfelj, opozorila | SCR-01 |
| Radar | Radar | Radar | dogodki iz novic, filingov, špekulacij, v treh pogledih | SCR-02 |
| Vstopne točke | Vstopi | Entries | kakovostna naložba na dobri ceni + vzrok padca | SCR-03 |
| Signali | Signali | Signals | nabiralnik vseh signalov s statusi | SCR-04 |
| Instrument | (ime simbola) | (symbol) | delnica ali ETF: graf, podatki, analize | SCR-05 |
| Analiza | Analiza | Analysis | agentski zagon v živo (debata agentov) | SCR-06 |
| Opcije | Opcije | Options | opcijske ideje za signale | SCR-07 |
| Portfelj | Portfelj | Portfolio | IBKR pozicije, izpostavljenost, stanje tez | SCR-08 |
| Teze | Teze | Theses | trditve, ki morajo veljati, in njihovo stanje | SCR-09 |
| Uspešnost | Uspešnost | Track record | ali signali delujejo | SCR-10 |
| Nastavitve | Nastavitve | Settings | jezik, tema, viri, LLM, proračun, Telegram | SCR-11 |
| Predlogi | Predlogi | Proposals | tvoji ročni predlogi za analizo | SCR-12 |

**Trije pogledi Radarja** (zavihki na SCR-02):

| Pogled | SL | EN | Obseg |
|---|---|---|---|
| Novi predlogi | Novi predlogi | Discover | širši univerzum (S&P 500, Nasdaq 100, izbrani ETF-ji), kar še nimaš |
| Watchlista | Watchlista | Watchlist | instrumenti, ki jih spremljaš |
| Portfelj | Portfelj | Portfolio | instrumenti, ki jih imaš pri IBKR |

## 5. Vizualna identiteta (povzetek, podrobno v DESIGN.md)

- **Znak:** krožni lok radarja (¾ kroga) s piko v kotu. Pika pomeni zaznan dogodek. Enobarven, deluje v 16 px.
- **Značaj:** natančen, miren, gost s podatki, a zračen. Navdih so kakovostni terminali in znanstveni instrumenti, ne kazino.
- **Barve imajo pomen, ne okras:**
  - **Indigo** je poudarek, interakcija, "Preža".
  - **Zelenomodra** je rast in pozitivno, **opečnato oranžna** padec in negativno. Barvi se ločita tudi po svetlosti, vedno s predznakom in puščico.
  - **Vijolična** je govorica oziroma nepotrjeno.
  - **Jantarna** je opozorilo, zastarel podatek, potreben pregled.
- **Tipografija:** IBM Plex Sans (UI) in IBM Plex Mono (številke, simboli, tabele). Obe podpirata č, š, ž.
- **Brez:** gradientov, emojijev, kričečih rdeče-zelenih ploskev, stock fotografij, "AI iskric".

## 6. Telegram bot

- Ime: **Preža**, uporabniško ime predlog `@preza_<tvoje>_bot`.
- Ikona: znak na indigo ozadju.
- Sporočila sledijo VOICE.md §5 (kratko, simbol najprej, povezava v aplikacijo).
