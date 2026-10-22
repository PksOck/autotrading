# DESIGN.md: oblikovni sistem in zasloni

**Prototipi:** Artifact platno *Signalna platforma – UI* (povezava v [`design/README.md`](./design/README.md)). Platno je vizualni vir resnice za postavitev. Ta datoteka je vir resnice za tokene in pravila.

## 1. Načela

1. **Gostota z zrakom.** Veliko podatkov na zaslonu, a z jasno hierarhijo: ena glavna številka ali sporočilo na kartico.
2. **Številke so v monospace in poravnane desno** (tabular figures). Spremembe imajo predznak in puščico.
3. **Barva nosi pomen** (BRAND.md §5). Če element nima pomena, je nevtralen.
4. **Vir in svežina sta vedno na dosegu** (CMP-08 ProvenanceTag), pri zastarelih podatkih tudi vidno opozorilo.
5. **Govorica je vizualno ločena** od potrjenega dogodka (vijolična, črtkana obroba, oznaka "Nepotrjeno").
6. **Vsako dejanje je reverzibilno** ali zahteva potrditev (zavrnjen signal lahko obnoviš, naročilo zahteva dvojno potrditev).
7. **Mobilno:** vsi zasloni delujejo na telefonu (Telegram povezave se odpirajo na telefonu). Glavna dejanja so dosegljiva s palcem.

## 2. Teme: svetla in temna

- Atribut `data-theme="light|dark"` na `<html>`. Privzeto sledi sistemu (`prefers-color-scheme`), izbira se shrani (piškotek `theme` + nastavitve).
- Preklop je v glavi (ikona sonce/luna) in v Nastavitvah (Sistem / Svetla / Temna).
- Vsi barvni tokeni so CSS spremenljivke. Komponente ne uporabljajo surovih hex vrednosti.
- Grafi (lightweight-charts) berejo iste tokene ob preklopu teme.

### 2.1 Barvni tokeni

Kontrast je preverjen (WCAG 2.1): besedilni tokeni dosežejo vsaj 4,5:1 na `bg`, `surface` in `surface-2`.

| Token | Svetla | Temna | Uporaba |
|---|---|---|---|
| `--bg` | `#F5F6F8` | `#0D1015` | ozadje aplikacije |
| `--surface` | `#FFFFFF` | `#141920` | kartice, tabele, panele |
| `--surface-2` | `#EEF0F4` | `#1B212A` | vnosna polja, zavihki, vrstice ob hoverju |
| `--border` | `#DCE0E6` | `#29303B` | obrobe, ločila |
| `--text` | `#15181E` | `#E7EAEF` | glavno besedilo (16:1) |
| `--text-2` | `#454D59` | `#AFB7C3` | sekundarno besedilo (≥7,5:1) |
| `--text-3` | `#5B6472` | `#8C96A5` | oznake, meta (≥5,2:1) |
| `--accent` | `#3D4ED6` | `#8E9CFF` | interakcija, izbrano, znak |
| `--accent-soft` | `#E7EAFB` | `#222A4F` | ozadje izbranega |
| `--on-accent` | `#FFFFFF` | `#0D1015` | besedilo na `--accent` (≥6,4:1) |
| `--pos` | `#0B5E47` | `#4FE3B4` | rast, pozitivno (≥6,8:1) |
| `--pos-soft` | `#E2F3EC` | `#13302A` | ozadje pozitivne oznake |
| `--neg` | `#B9440F` | `#E8794A` | padec, negativno (≥4,7:1) |
| `--neg-soft` | `#FBEAE2` | `#3A1F16` | ozadje negativne oznake |
| `--warn` | `#8F5A00` | `#E9B949` | opozorilo, zastarelo, pregled |
| `--warn-soft` | `#FBF0DA` | `#33290F` | |
| `--rumor` | `#7139D6` | `#B99AF5` | govorica, nepotrjeno |
| `--rumor-soft` | `#EFE7FC` | `#2A2142` | |

`--pos` in `--neg` se ločita tudi po svetlosti (razmerje ≥1,5:1 v obeh temah), zato sta ločljiva tudi pri barvni slepoti. Poleg barve vedno uporabi predznak in ▲/▼.

### 2.2 Tipografija

| Token | Velikost / višina vrstice | Teža | Uporaba |
|---|---|---|---|
| `display` | 28 / 34 | 600 | naslov zaslona |
| `title` | 20 / 28 | 600 | naslov sekcije |
| `heading` | 16 / 24 | 600 | naslov kartice |
| `body` | 14 / 22 | 400 | besedilo |
| `small` | 13 / 20 | 400 | sekundarno |
| `label` | 12 / 16 | 500, razmik 0,02em | oznake, glave tabel |
| `num-lg` | 24 / 30 Mono | 500 | glavne številke |
| `num` | 14 / 20 Mono | 400 | številke v tabelah |

- Pisavi: **IBM Plex Sans** (400, 500, 600) in **IBM Plex Mono** (400, 500) prek `next/font/google`, podmnožica `latin-ext` (č, š, ž).
- Številke: `font-variant-numeric: tabular-nums`.

### 2.3 Razmiki, polmeri, sence

- Osnovna enota je **4 px**. Lestvica: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64.
- Polmeri: `--r-sm` 6 px (oznake, polja), `--r-md` 10 px (kartice), `--r-lg` 14 px (paneli, modali), `--r-full` (pilule).
- Sence: samo za plavajoče elemente (meni, modal): `0 8px 24px rgb(0 0 0 / .12)` (svetla), `0 8px 24px rgb(0 0 0 / .5)` (temna). Kartice nimajo senc, samo obrobo.
- Zamik med karticami 16 px, notranji rob kartice 16 do 20 px.

### 2.4 Postavitev in prelomne točke

- Lupina: stranski meni 232 px (zložljiv na 64 px) + vsebina z `max-width: 1440px`.
- Prelomne točke: `sm` 640, `md` 960, `lg` 1280.
- Pod `md`: stranski meni postane spodnja vrstica z 5 glavnimi moduli (Pregled, Radar, Vstopi, Signali, Portfelj), ostalo pod "Več". Tabele se pretvorijo v kartice ali se drsijo vodoravno v okvirju.
- Najmanjša ciljna površina za dotik: 44 × 44 px.

## 3. Komponente (`CMP-xx`)

| ID | Ime | Opis | Zasloni |
|---|---|---|---|
| CMP-01 | AppShell | stranski meni, glava (iskanje, SL/EN, tema, stanje sistema) | vsi |
| CMP-02 | SystemStatus | pike stanja: IB Gateway, Flex, Ollama, LiteLLM, poraba LLM | glava, SCR-11 |
| CMP-03 | SignalCard | smer, vrsta, simbol, moč, razlaga, vstop/stop/cilj, dejanja | SCR-01, 04 |
| CMP-04 | EventRow | dogodek Radarja: tip, simboli, ocena, odziv cene, govorica/potrjeno, viri | SCR-02 |
| CMP-05 | ScoreMeter | ocena 0–1 kot vodoravna lestvica s številko | SCR-02, 03, 04 |
| CMP-06 | RatingPill | Kupi / Povečaj / Drži / Zmanjšaj / Prodaj / Potreben pregled | SCR-04, 05, 06 |
| CMP-07 | EntryZoneBar | trenutna cena glede na vstopno cono, stop, cilj (linearna lestvica) | SCR-03, 05 |
| CMP-08 | ProvenanceTag | vir · pred X min, opozorilo pri zastarelem | povsod |
| CMP-09 | ChangeValue | ▲ +2,1 % / ▼ −3,4 % z barvo in predznakom | povsod |
| CMP-10 | CauseBadge | vzrok padca: trg / sektor / začasno / temeljno / neznano | SCR-03 |
| CMP-11 | ThesisCheck | trditev teze s stanjem ✓ drži / ! šibi / ✕ ovržena | SCR-05, 09 |
| CMP-12 | AgentTimeline | koraki agentov v živo (SSE), razširljivi izhodi, stroški | SCR-06 |
| CMP-13 | PriceChart | lightweight-charts + indikatorji (trading-signals) + oznake dogodkov in signalov | SCR-05 |
| CMP-14 | PayoffChart | profil dobička in izgube opcijske strukture, break-even, max izguba | SCR-07 |
| CMP-15 | LadderTable | lestvica postopnega nakupa (deleži, cene) | SCR-03, 04 |
| CMP-16 | ViewTabs | zavihki pogledov: Novi predlogi / Watchlista / Portfelj | SCR-02, 03, 04 |
| CMP-17 | EmptyState | razlog + dejanje | povsod |
| CMP-18 | ConfirmDialog | dvojna potrditev za nepovratna dejanja | SCR-07, (M7) |

Osnova je **shadcn/ui** (Radix): Button, Tabs, Dialog, DropdownMenu, Tooltip, Table, Badge, Toggle, Command (iskanje ⌘K). Komponente CMP-xx so kompozicije nad njimi.

## 4. Zasloni (`SCR-xx`)

| ID | Zaslon | Pot | Ključna vsebina | Mejnik |
|---|---|---|---|---|
| SCR-01 | Pregled | `/` | novo danes (signali), stanje portfelja, opozorila, poraba LLM, uspešnost na kratko | M1→M3 |
| SCR-02 | Radar | `/radar?view=discover\|watchlist\|portfolio` | tok dogodkov, filtri (tip, govorica, ocena), trije pogledi | M2 |
| SCR-03 | Vstopi | `/entries?view=…` | kandidati, razdalja do cone, vzrok padca, teza, lestvica | M3 |
| SCR-04 | Signali | `/signals` | nabiralnik, statusi, filtri, množična dejanja | M2 |
| SCR-05 | Instrument | `/i/[symbol]` | graf, ključni podatki ali ETF profil, signali, analize, teze | M1→M4 |
| SCR-06 | Analiza | `/analysis/[runId]` | debata agentov v živo, končna odločitev, stroški | M4 |
| SCR-07 | Opcije | `/options/[symbol]` | predlagane strukture, payoff, veriga, tveganja | M6 |
| SCR-08 | Portfelj | `/portfolio` | pozicije, teže, izpostavljenost (skozi ETF), stanje tez | M1 |
| SCR-09 | Teze | `/theses` | trditve in tedenski pregledi | M5 |
| SCR-10 | Uspešnost | `/track-record` | hit rate, alfa, kalibracija po virih | M5 |
| SCR-11 | Nastavitve | `/settings` | jezik, tema, univerzum, pragovi, LLM vloge in proračun, Telegram, povezave | M0→ |

Na platnu so narisani: SCR-01, 02, 03, 05, 06, 07, 11 in tabla tokenov. SCR-04, 08, 09, 10 sledijo istim vzorcem (BL-005).

## 5. Stanja (obvezna za vsak zaslon)

| Stanje | Prikaz |
|---|---|
| nalaganje | skeleton v obliki končne vsebine (ne vrtavka čez cel zaslon) |
| prazno | CMP-17: razlog + dejanje (VOICE.md §5) |
| zastarelo | jantarna oznaka na CMP-08 + pasica, če je ključni vir (Gateway, Flex) nedosegljiv |
| napaka | sporočilo v kartici, ostala stran deluje (izolacija napak po karticah) |
| delno | prikaži, kar je, manjkajoče označi "ni podatka", nikoli 0 |
| v teku | agentski zagon: CMP-12 z živim napredkom; drugje drobna oznaka "posodabljam" |

## 6. Grafi in vizualizacija podatkov

- Cenovni graf: sveče ali črta (preklop), volumen spodaj, SMA50 in SMA200 privzeto, ostali indikatorji na zahtevo.
- **Oznake na časovnici:** dogodki Radarja (krog, barva po tipu), signali (puščica), lastni posli iz IBKR (trikotnik). Hover prikaže povzetek.
- **Vstopna cona:** poltransparenten pas `--accent-soft` čez graf, stop črtkana `--neg`, cilj črtkana `--pos`.
- Barve serij v grafih: `--accent`, `--text-2`, `--warn`, `--rumor`. Nikoli pos/neg za kategorije.
- Pred implementacijo grafov preberi pravila v `dataviz` skill (če je na voljo).

## 7. Dostopnost

- Vsi interaktivni elementi so pravi `<button>` ali `<a>`, dosegljivi s tipkovnico, z vidnim fokusom (`outline: 2px solid var(--accent)`, odmik 2 px).
- Ikonski gumbi imajo `aria-label` (preveden).
- Grafi imajo besedilni povzetek za bralnike zaslona (kot v legacy `price-chart`).
- `prefers-reduced-motion`: brez animacij razen nujnih kazalnikov napredka.
- Jezik strani (`<html lang>`) sledi izbranemu jeziku.

## 8. Gibanje

- Trajanje 120 do 200 ms, `ease-out`. Animiramo samo prozornost in premik do 4 px.
- Nov dogodek v Radarju: kratek poudarek ozadja (`--accent-soft`, 1,2 s), brez skakanja vsebine.
