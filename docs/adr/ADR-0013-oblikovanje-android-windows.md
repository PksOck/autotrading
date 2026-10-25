# ADR-0013: Oblikovanje za Android in Windows namesto vzorcev iOS
**Status:** sprejeto · **Datum:** 2026-10-25 · **Seja:** S-008

## Kontekst
Uporabnik aplikacijo uporablja na Androidu (telefon) in Windows (namizje, brskalnik Edge ali Chrome). Vmesnik je ponekod deloval kot aplikacija za Apple:
- bližnjica `⌘K` v iskalnem polju;
- segmentirane kontrole v slogu iOS (siva podlaga z belim drsnikom in senco);
- zamegljena glava in ozadje modalov (`backdrop-blur`);
- vzmeti z rahlim prenihajem;
- ciljna površina 44 px (Apple HIG);
- spodnja vrstica s 6 zavihki in tankim indikatorjem nad ikono;
- polji s sivim polnilom brez obrobe.

## Odločitev
Vmesnik ostane eden in platformno nevtralen. Kjer se platformi razlikujeta, sledi **Material 3** (Android, dotik) in **Fluent 2** (Windows, miška in tipkovnica). Lastna identiteta (barve, IBM Plex, gostota podatkov) ostane.

- **Bližnjice:** oznaka je odvisna od platforme. `Ctrl K` na Windows, Linux in Android s tipkovnico, `⌘K` samo na macOS. Na napravah brez natančnega kazalca (`pointer: coarse`) oznake bližnjic niso prikazane. Tipka `Ctrl` in `Meta` delujeta povsod.
- **Segmentirani gumbi:** skupina gumbov z obrobo (M3 segmented button). Izbrani segment ima polnilo `--accent-soft`, besedilo `--accent` in ikono kljukice, kadar je prostor. Brez belega drsnika in sence.
- **Polja:** obrobljena (M3 outlined, Fluent), ozadje `--surface`, obroba `--border`, fokus z obrobo `--accent` in obstoječim obročem.
- **Brez zameglitve:** glava ima polno ozadje `--surface`. Ozadje modalov in panelov je prosojna temna plast (scrim) `rgb(0 0 0 / .4)` brez `backdrop-filter`.
- **Gibanje:** vzmeti so kritično dušene (brez prenihaja). Trajanja in krivulje ostanejo (že ustrezajo M3 standard easing).
- **Ciljna površina:** 48 × 48 px pri `pointer: coarse` (M3). Pri miški ostane kompaktna gostota (vrstice in gumbi 32 do 36 px, Fluent).
- **Spodnja navigacija (pod `md`):** M3 navigacijska vrstica s 5 cilji: Pregled, Radar, Signali, Portfelj, Več. Vstopi in ostali moduli so pod Več. Aktivni cilj ima indikator v obliki pilule (64 × 32 px, `--accent-soft`) za ikono, oznaka je pod njo, višina vrstice 64 px + varni rob.
- **Polmeri:** `--r-sm` 4 px, `--r-md` 8 px, `--r-lg` 12 px (Fluent 2 in M3 srednja vrednost).
- **Drsniki:** tanki drsniki v barvah tokenov (`scrollbar-width: thin`, `scrollbar-color`), da Windows ne kaže debelih sivih drsnikov.
- **Namestitev:** spletni manifest z `display: standalone`, ikonami in barvo teme za obe temi (namestitev kot aplikacija na Androidu in v Edge na Windows).
- **Tipka nazaj na Androidu:** odprt modal ali panel se zapre s sistemsko tipko nazaj (vnos v zgodovino) in ne zapusti zaslona.

## Posledice
- Spremenijo se `tokens.css`, `globals.css`, `lib/motion.ts`, lupina (`Header`, `BottomNav`, `Sidebar`, `CommandPalette`) in komponente s segmentiranimi gumbi. DESIGN.md §2.3, §2.4, §3 in §8.1 se posodobijo.
- E2E testi, ki iščejo `⌘K` ali število zavihkov, se prilagodijo.
- Na macOS ostane `⌘K`, zato aplikacija tam ni slabša.

## Zavrnjene možnosti
- **Dve ločeni temi (Material na Androidu, Fluent na Windows):** dvojno vzdrževanje in testi, uporabnik bi med napravama videl različen vmesnik.
- **Knjižnica komponent Material (MUI) ali Fluent UI React:** zamenjava Radix in Tailwind, velik paket, izguba lastne identitete in gostote.
- **Ohraniti obstoječe:** iOS vzorci na Androidu in Windows delujejo tuje (uporabnikova pripomba).
