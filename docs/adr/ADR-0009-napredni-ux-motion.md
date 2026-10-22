# ADR-0009: Napreden UX: gibanje, povezani pogledi, pregledi
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-002

## Kontekst
Uporabnik želi napreden, živ vmesnik: dinamične animacije, povezane poglede in preglede, ne statičnih tabel.

## Odločitev
- **React** (Next.js 15 App Router, React 19) ostane osnova (ADR-0002).
- **Motion** (`motion/react`) za gibanje: deljeni prehodi (`layoutId`), `AnimatePresence`, vzmeti, animirane številke. Tokeni v `apps/web/lib/motion.ts`.
- **View Transitions** za prehode med stranmi, kjer jih brskalnik podpira, sicer Motion.
- **Radix / shadcn/ui** za dostopne primitive (Dialog, Popover, HoverCard, Tabs), **cmdk** za ukazno paleto, **sonner** za obvestila z *Razveljavi*.
- **Vizualizacije pregledov:** lastne SVG komponente z `d3-scale`, `d3-hierarchy`, `d3-shape` (izračun) + React/Motion (izris in prehodi). Cenovni grafi: lightweight-charts.
- **Stanje povezovanja** (fokus entitete, kukalo, filtri): URL (deep link) + majhna globalna shramba (Zustand) za hover/fokus.
- Pravila gibanja in povezovanja so v DESIGN.md §8–§10.

## Posledice
- Vsaka nova komponenta mora podpirati `prefers-reduced-motion` (test v Vitest z mockom media query).
- Velikost paketa: Motion (~30 kB gz) in d3 moduli (uvoz po modulih). Merimo v CI (`next build` izpis), meja 250 kB gz za prvo stran.

## Zavrnjene možnosti
- **GSAP:** zmogljiv, a imperativen in manj usklajen z React stanjem.
- **Recharts / Nivo za preglede:** hitrejši začetek, a omejen nadzor nad animacijami in povezovanjem (LX-03).
- **Čisti CSS prehodi:** ne zmorejo deljenih prehodov in preurejanja seznamov.
