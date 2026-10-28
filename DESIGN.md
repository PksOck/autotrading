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
- Polmeri: `--r-sm` 4 px (oznake, polja), `--r-md` 8 px (kartice), `--r-lg` 12 px (paneli, modali), `--r-full` (pilule) ([ADR-0013](./docs/adr/ADR-0013-oblikovanje-android-windows.md)).
- Sence: samo za plavajoče elemente (meni, modal): `0 8px 24px rgb(0 0 0 / .12)` (svetla), `0 8px 24px rgb(0 0 0 / .5)` (temna). Kartice nimajo senc, samo obrobo.
- Zamik med karticami 16 px, notranji rob kartice 16 do 20 px.

### 2.4 Postavitev in prelomne točke

- Lupina: stranski meni 232 px (zložljiv na 64 px) + vsebina z `max-width: 1440px`.
- Prelomne točke: `sm` 640, `md` 960, `lg` 1280.
- Pod `md`: stranski meni postane navigacijska vrstica M3 s 5 cilji (Pregled, Radar, Signali, Portfelj, Več). Vstopi in ostali moduli so pod "Več". Aktivni cilj ima pilulo 64 × 32 px (`--accent-soft`) za ikono, višina 64 px + varni rob. Tabele se pretvorijo v kartice ali se drsijo vodoravno v okvirju.
- Najmanjša ciljna površina za dotik (`pointer: coarse`): 48 × 48 px (M3). Pri miški ostane kompaktna gostota (32 do 36 px, Fluent 2).

### 2.5 Platforme: Android in Windows

Ciljni napravi sta Android (dotik) in Windows (miška, tipkovnica). Vmesnik je eden; kjer se platformi razlikujeta, sledi Material 3 in Fluent 2 ([ADR-0013](./docs/adr/ADR-0013-oblikovanje-android-windows.md)).

- Bližnjice: `Ctrl K` povsod, `⌘K` samo na macOS. Na dotiku oznake bližnjic niso prikazane.
- Segmentirani gumbi: obrobljena skupina, izbrani segment `--accent-soft` z besedilom `--accent`. Brez belega drsnika in sence (vzorec iOS).
- Polja: obrobljena, ozadje `--surface`, fokus z obrobo `--accent`.
- Brez `backdrop-filter`: glava ima polno ozadje, modali in paneli temno prosojno plast `rgb(0 0 0 / .4)`.
- Tanki drsniki v barvah tokenov.
- Spletni manifest (`display: standalone`) za namestitev na Androidu in v Edge; barva teme za svetlo in temno temo.
- Sistemska tipka nazaj na Androidu zapre odprt modal ali panel, ne zaslona.

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
| CMP-11 | ThesisCheck | izvedeno BL-100: ikona in besedilo za odprto, drži, šibi, ovrženo in poteklo stanje; zgodovina dokazov z vidno oznako govorice | SCR-05, 09 |
| CMP-12 | AgentTimeline | koraki agentov v živo (SSE), razvrščeni v faze (Analitiki, Debata, Načrt, Tveganja, Odločitev), koraki analitikov zloženi po agentu (odprt samo zadnji med tekom), bik/medved v dveh stolpcih od `md`, zaprt korak pokaže 3 vrstice, odprt cel markdown, novi koraki pridejo z MO-03 | SCR-06 |
| CMP-13 | PriceChart | lightweight-charts + indikatorji (trading-signals) + oznake dogodkov in signalov | SCR-05 |
| CMP-14 | PayoffChart | profil dobička in izgube opcijske strukture, break-even, max izguba | SCR-07 |
| CMP-15 | LadderTable | lestvica postopnega nakupa (deleži, cene) | SCR-03, 04 |
| CMP-16 | ViewTabs | zavihki pogledov: Novi predlogi / Watchlista / Portfelj | SCR-02, 03, 04 |
| CMP-17 | EmptyState | razlog + dejanje | povsod |
| CMP-18 | ConfirmDialog | dvojna potrditev za nepovratna dejanja | SCR-07, (M7) |
| CMP-19 | EntityLink | klikljiva entiteta s predogledom in kukalom (LX-01, LX-02) | povsod |
| CMP-20 | HoverPreview | predogled entitete ob hoverju | povsod |
| CMP-21 | PeekPanel | desni panel z zgodovino, deljeni prehod na celoten zaslon | povsod |
| CMP-22 | Trail | veriga izvora: novica → dogodek → signal → analiza → odločitev | SCR-04, 05, 06 |
| CMP-23 | CommandPalette | ⌘K iskanje entitet in dejanj | glava |
| CMP-24 | AnimatedNumber | animirana številka z bliskom smeri (MO-04) | povsod |
| CMP-25 | Treemap | toplotni zemljevid portfelja (OV-01) | SCR-01, 08 |
| CMP-26 | PulseTimeline | utrip Radarja (OV-02) | SCR-01, 02 |
| CMP-27 | Funnel | lijak signalov (OV-03) | SCR-01, 10 |
| CMP-28 | RegimeStrip | trak tržnega režima (OV-04) | SCR-01 |
| CMP-29 | Sparkline | iskrica (OV-07) | povsod |
| CMP-30 | ProposalComposer | ročni predlog za analizo (§11) | glava, ⌘K, SCR-02, SCR-12 |
| CMP-31 | HorizonCard | obdobje (kratko, ~1 leto, 3+ let): sodba (podpira rast, mešano, proti rasti, premalo podatkov), trak za/nevtralno/proti s števili, 2 najmočnejša dokaza, manjkajoči podatki | SCR-06 |
| CMP-32 | EvidenceSplit | dokazi enega obdobja v dveh stolpcih: Za (pos) levo, Proti (neg) desno, nevtralni pod njima; vrstica = besedilo iz ključa, vrednost proti primerjavi, vir in čas | SCR-06 |

Osnova je **shadcn/ui** (Radix): Button, Tabs, Dialog, DropdownMenu, Tooltip, Table, Badge, Toggle, Command (iskanje ⌘K). Komponente CMP-xx so kompozicije nad njimi.

## 4. Zasloni (`SCR-xx`)

| ID | Zaslon | Pot | Ključna vsebina | Mejnik |
|---|---|---|---|---|
| SCR-01 | Pregled | `/` | novo danes (signali), stanje portfelja, opozorila, poraba LLM, uspešnost na kratko | M1→M3 |
| SCR-02 | Radar | `/radar?view=discover\|watchlist\|portfolio` | tok dogodkov, filtri (tip, govorica, ocena), trije pogledi | M2 |
| SCR-03 | Vstopi | `/entries?view=all\|portfolio\|watchlist&symbol=…` | zemljevid vstopov (OV-05), kandidati s filtri (kandidati, v coni, blizu, vse), cona in stop (CMP-07), vzrok padca (CMP-10), sprožena pravila, pasovi vrednotenja, lestvica z zneskom (CMP-15) | M3 |
| SCR-04 | Signali | `/signals` | nabiralnik, statusi, filtri, množična dejanja | M2 |
| SCR-05 | Instrument | `/i/[symbol]` | graf, ključni podatki ali ETF profil, signali, analize, teze | M1→M4 |
| SCR-06 | Analiza | `/analysis`, `/analysis/[runId]` | seznam zagonov kot tabela (instrument, datum, ocena agentov v navadnem jeziku, sodbe treh obdobij, za/proti, prepričanje, pozicija); detajl: zgoraj odločitvena glava (cena z virom, pozicija, ocena agentov z razlago, prepričanje, velikost, CMP-31 ×3, kaj bi spremenilo oceno), spodaj zaprte podrobnosti (CMP-32 dokazi za in proti, utemeljitev agentov, kontrolna ocena, CMP-12 po analitikih) (ADR-0014) | M4 |
| SCR-07 | Opcije | `/options/[symbol]` | predlagane strukture, payoff, veriga, tveganja | M6 |
| SCR-08 | Portfelj | `/portfolio` | pozicije, teže, izpostavljenost (skozi ETF), stanje tez; sinhronizacija IBKR in ročni uvoz Flex XML | M1 |
| SCR-09 | Teze | `/theses` | izvedeno BL-100: seznam, filter, strani in `/theses/[thesisId]`; ročno ustvarjanje iz analize, urejanje in potrditev osnutka, stanja trditev z dokazi in zgodovino, viri in lokalni čas; BL-101: tedenski predlogi pregleda ločeno od dejanskega stanja (značka »Predlog pregleda«, sprejem z izrecno potrditvijo, zavrnitev z razlogom, pokritost in napake pregleda) | M5 |
| SCR-10 | Uspešnost | `/track-record` | izvedeno BL-102: izbira horizonta (1/5/20/60 d, segmentirani gumbi), štiri ploščice (zadetki, povprečni donos v smeri signala, alfa proti indeksu iz izidov, izmerjeno/čaka), »Tvoji predlogi« proti »Sistemski signali«, tabela vrsta × vir, kalibracija moči kot 5 vrstic z merilnikom deleža zadetkov; razdelek »Predlog uteži« (BL-103): gumb za izračun pri izbranem horizontu, tabela skupin z intervalom in utežjo trenutno → predlagano, dvostopenjska potrditev in »Zavrzi predlog«; značka »Malo podatkov« pod 10 izidi in opozorilni pas, ko je malo izidov skupno; vir in čas izračuna ob horizontu | M5 |
| SCR-11 | Nastavitve | `/settings` | jezik, tema, univerzum, pragovi, LLM vloge in proračun, Telegram, povezave | M0→ |
| SCR-12 | Predlogi | `/proposals` | tvoji ročni predlogi, stanje analize, izid (§11) | M2→M4 |

Na platnu so narisani: SCR-01, 02, 03, 05, 06, 07, 11 in tabla tokenov. Od M0 naprej je **vir resnice React aplikacija** (`apps/web`, živi primeri na `/ux`); nove zaslone gradimo neposredno v kodi. CMP-22 Trail in OV-06 nastaneta skupaj s svojima zaslonoma. OV-05 je izveden v `components/entries/EntryMap.tsx`: x je razdalja do cone v ATR (os se prilagodi podatkom), y je delež ugodnih pasov vrednotenja, črtkan krog pomeni, da vrednotenja ni (npr. ETF); prekrivajoče točke se razmaknejo navpično.

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

## 8. Gibanje (motion sistem)

Gibanje ni okras. **Vsaka animacija pojasni vzrok in posledico:** kaj se je spremenilo, od kod je prišlo, kam je šlo. Knjižnica: **Motion** (`motion/react`, naslednik Framer Motion) ([ADR-0009](./docs/adr/ADR-0009-napredni-ux-motion.md)).

### 8.1 Tokeni gibanja

| Token | Vrednost | Uporaba |
|---|---|---|
| `--dur-fast` | 120 ms | hover, fokus, preklop stikala |
| `--dur-base` | 200 ms | pojav ali skritje elementa, zavihek |
| `--dur-slow` | 320 ms | odpiranje panela, prehod strani |
| `--ease-standard` | `cubic-bezier(.2, 0, 0, 1)` | večina prehodov |
| `--ease-exit` | `cubic-bezier(.4, 0, 1, 1)` | izhod (hitrejši od vhoda) |
| `spring.snappy` | kritično dušena, `{ stiffness: 520, damping: 46 }` | indikator zavihka, izbira, preurejanje seznama |
| `spring.soft` | kritično dušena, `{ stiffness: 260, damping: 33 }` | panel, kartica, ki se razširi |

Vzmeti nimajo prenihaja (ADR-0013); odbijanje deluje kot iOS.

Tokeni živijo v `apps/web/lib/motion.ts` (JS) in `tokens.css` (CSS). Komponente ne uporabljajo lastnih trajanj.

### 8.2 Vzorci gibanja (obvezni)

| ID | Vzorec | Kje | Kako |
|---|---|---|---|
| MO-01 | **Deljeni prehod** (shared layout) | kartica signala → panel podrobnosti, vrstica → instrument | `layoutId` na simbolu, ceni in oceni. Element "odpotuje" na novo mesto, ne izgine in se ponovno pojavi |
| MO-02 | **Drsni indikator** | zavihki, stranski meni, navigacijska vrstica (segmentirani gumbi samo prelijejo barvo) | en `motion.span` z `layoutId`, ki zdrsne pod aktivno izbiro |
| MO-03 | **Živi seznam** | Radar, Signali, časovnica agentov | `AnimatePresence` + `layout`: novi elementi zdrsnejo od zgoraj (y −8 → 0, prozornost 0 → 1), ostali se gladko premaknejo navzdol, odstranjeni se skrčijo |
| MO-04 | **Animirana številka** | cene, vrednost portfelja, ocene, števci | štetje do nove vrednosti (`useSpring`) + kratek blisk ozadja `--pos-soft` / `--neg-soft` (600 ms) glede na smer spremembe |
| MO-05 | **Postopno razkrivanje** | debata agentov, povzetki | besedilo prihaja v delih (SSE), kazalnik pisanja, nov korak se razširi z `spring.soft` |
| MO-06 | **Okostje → vsebina** | vse kartice | prelivanje (crossfade) iz okostja v vsebino iste oblike, brez skoka postavitve |
| MO-07 | **Prehod strani** | med zasloni | View Transitions API (podpora v Next.js) ali Motion: vsebina se zamenja s prelivom in premikom 8 px, glava in meni ostaneta pri miru |
| MO-08 | **Prehod grafa** | sprememba obdobja, filtra | črta se morfira med stanji (interpolacija poti), osi se animirajo, ne izrišejo na novo |
| MO-09 | **Pulz dogodka** | nov dogodek nad pragom, oznaka na grafu | en val (obroč, ki se razširi in zbledi, 1,2 s). Nikoli neskončna animacija |
| MO-10 | **Razveljavi** | Zavrzi, Spremljaj, Sprejmi | optimistična posodobitev + toast z gumbom *Razveljavi* (5 s) |

**Pravila:**
- Animiramo samo `transform` in `opacity` (in barvo ozadja za MO-04). Nikoli `width`/`height`/`top` neposredno (uporabi `layout`).
- Hkrati se animira največ en "glavni" element. Ostalo je statično ali se samo prelije.
- `prefers-reduced-motion`: vsi vzorci se zamenjajo s takojšnjo spremembo ali prelivom ≤ 120 ms. MO-09 se ne izvaja.
- Gibanje nikoli ne zakasni podatka: vsebina je v DOM takoj, animacija je samo prikaz.

## 9. Povezovanje: vse je povezano z vsem

Cilj: uporabnik nikoli ne izgubi konteksta in vedno vidi, **od kod je kaj prišlo** in **kaj je s čim povezano**.

| ID | Vzorec | Opis |
|---|---|---|
| LX-01 | **Entiteta povsod klikljiva** | vsak simbol, dogodek, signal, analiza, teza in pozicija je `EntityLink` (CMP-19). Hover po 300 ms odpre predogled (CMP-20 HoverPreview): mini graf, cena, zadnji signal, stanje teze |
| LX-02 | **Kukalo (peek panel)** | klik na entiteto odpre desni panel (CMP-21 PeekPanel) brez zapustitve trenutnega zaslona. `Shift`+klik ali gumb "Odpri" vodi na celoten zaslon (z MO-01). Panel ima lastno zgodovino (nazaj/naprej) |
| LX-03 | **Navzkrižno poudarjanje** | hover na dogodek v seznamu poudari njegovo oznako na grafu in obratno. Hover na pozicijo v portfelju poudari vse njene signale in dogodke na vseh vidnih panelih (skupno stanje `focusEntity`) |
| LX-04 | **Sled (lineage)** | CMP-22 Trail: veriga *Novica → Dogodek → Signal → Analiza → Odločitev → (Naročilo)*. Na vsakem objektu vidiš celotno verigo in skočiš na kateri koli člen |
| LX-05 | **Globalni kontekst simbola** | izbira simbola (⌘K ali klik "Fokus") filtrira vse zaslone na ta simbol, dokler fokusa ne odstraniš (značka v glavi) |
| LX-06 | **Ukazna paleta** | CMP-23 ⌘K: iskanje entitet in dejanj (*Analiziraj MSFT*, *Dodaj na watchlisto*, *Preklopi temo*, *Pojdi na Radar*). Nedavne entitete na vrhu |
| LX-07 | **Tipkovnica** | `j`/`k` premik po seznamu, `Enter` odpri kukalo, `a` analiziraj, `w` spremljaj, `x` zavrzi, `g r` Radar, `g e` Vstopi, `?` pomoč |
| LX-08 | **Deep link** | vsak pogled, filter, fokus in odprt panel je v URL (`?peek=signal:8f3a&focus=MSFT`). Telegram povezave odprejo točno to stanje |

## 10. Pregledi (overview vizualizacije)

| ID | Pregled | Zaslon | Opis |
|---|---|---|---|
| OV-01 | **Toplotni zemljevid portfelja** (treemap) | SCR-01, SCR-08 | ploščina = teža, barva = dnevna sprememba (diverging pos/neg), obroba = stanje teze. Klik = kukalo |
| OV-02 | **Utrip Radarja** | SCR-01, SCR-02 | časovnica zadnjih 7 dni: vrstica na simbol, pike = dogodki (velikost = ocena, barva = tip, črtkano = govorica). Čopič (brush) za izbiro obdobja filtrira seznam |
| OV-03 | **Lijak signalov** | SCR-01, SCR-10 | novice → dogodki → nad pragom → signali → sprejeti → izidi. Pokaže, koliko šuma sistem filtrira |
| OV-04 | **Trak tržnega režima** | glava SCR-01 | SPY proti SMA200, VIX, 10-l. obrestna mera, dolar: 4 mini indikatorji z barvo režima |
| OV-05 | **Zemljevid vstopov** | SCR-03 | razsevni diagram: x = razdalja do cone, y = kakovost/vrednotenje, velikost = moč, barva = vzrok padca. Kandidati v "ciljnem kvadrantu" so poudarjeni |
| OV-06 | **Mreža izpostavljenosti** | SCR-08 | sektor × regija skozi ETF holdinge, prekrivanja med ETF-ji |
| OV-07 | **Iskrice (sparklines)** | povsod | 30-dnevni trend ob vsakem simbolu v tabelah |

Vizualizacije pregledov so lastne SVG komponente (`d3-scale`, `d3-hierarchy`, `d3-shape` za izračun, React za izris, Motion za prehode). Cenovni grafi ostanejo lightweight-charts.

## 11. Ročni predlogi (uporabnik predlaga, sistem analizira)

Ideja ne pride samo iz Radarja. Uporabnik lahko **sam predlaga instrument ali tezo** in jo pošlje v analizo.

**Vstopne točke:**
- gumb **+ Predlog** v glavi (vedno viden) → CMP-30 ProposalComposer kot plavajoči panel;
- ⌘K: *Predlagaj …* ali neposredno vnos simbola + `Enter` → *Predlagaj v analizo*;
- Telegram: `/predlog MSFT padec po poročilu, zanima me vstop pod 400` ali posredovano sporočilo/povezava botu;
- na vsakem dogodku in instrumentu: *Dodaj svojo hipotezo*.

**Polja predloga** (samo simbol je obvezen):

| Polje | Opis |
|---|---|
| simbol(i) | eden ali več; iz prilepljenega besedila jih predlaga lokalni model (`local-fast`), uporabnik potrdi |
| hipoteza | prosto besedilo: zakaj te zanima (postane kontekst za agente, ne dejstvo) |
| vir | povezava, prilepljena novica ali besedilo (shrani se kot `news_item` z virom `manual`) |
| smer in horizont | gor/dol/ne vem · dnevi/tedni/meseci/leta |
| globina | **Hitro** (lokalno, ~1 min, 0 $), **Standardno** (cloud-quick), **Globoko** (celoten TradingAgents/ETF graf, porabi kredit) |
| kam shrani | watchlista (aktivna/zaloga) ali samo enkratna analiza |

**Tok:** predlog → takojšnja potrditev (MO-10 toast z *Razveljavi*) → vrsta analiz (vidna v glavi kot števec) → rezultat kot signal `source=manual` z uporabnikovo hipotezo, ki jo agenti **izrecno potrdijo ali ovržejo** ("Tvoja hipoteza: … Ocena: delno drži, ker …") → obvestilo v Telegram.

**Pravila:**
- ročni predlogi gredo mimo praga Radarja, vendar spoštujejo dnevni proračun za globoke analize (prikaz preostanka ob izbiri globine);
- hipoteza uporabnika se v pozivih označi kot *user hypothesis*, agenti jo morajo preveriti z dokazi, ne jo privzeti;
- uspešnost ročnih predlogov se meri ločeno (SCR-10: "tvoji predlogi" proti "sistemski signali").

**Zaslon:** SCR-12 *Predlogi* (`/proposals`): seznam tvojih predlogov s stanjem (v vrsti, v analizi, končano) in izidom.
