# apps/web: frontend

Next.js 16 (App Router) · React 19 · Tailwind 4 · Motion · Radix · cmdk · sonner · TanStack Query · Zustand · d3 (izračun) · next-intl.

## Zagon

```bash
pnpm install            # v korenu repoja
pnpm dev                # http://localhost:3000 (API_URL privzeto http://localhost:8000)
pnpm --filter web test  # Vitest
pnpm --filter web lint && pnpm --filter web typecheck
pnpm --filter web build && pnpm --filter web start
CHROMIUM_PATH=/pot/do/chromium pnpm --filter web exec playwright test   # e2e na zagnani aplikaciji
pnpm --filter web gen:api      # TS tipi iz services/api/openapi.json
pnpm --filter web i18n:check   # sl.json in en.json imata iste ključe
```

## Kje kaj

```text
app/                    zasloni (DESIGN.md §4), template.tsx = prehod strani (MO-07)
  api/system/status/    proxy na FastAPI
  ux/                   živi oblikovni sistem (tokeni, MO-xx, LX-xx)
components/
  shell/                CMP-01 AppShell, Sidebar, BottomNav, Header, CMP-02 SystemStatus,
                        CMP-23 CommandPalette (⌘K), Shortcuts (LX-07), LocaleSwitch, ThemeToggle
  common/               CMP-19 EntityLink, CMP-20/21 InstrumentPreview + PeekPanel,
                        CMP-24 AnimatedNumber, ThesisBadge, Planned, PageHeader, Icon
  overview/             CMP-25 Treemap, CMP-26 PulseTimeline, CMP-27 Funnel,
                        CMP-28 RegimeStrip, CMP-29 Sparkline, SignalCards (CMP-03)
  proposals/            CMP-30 ProposalComposer, ProposalList (SCR-12)
lib/                    motion.ts (tokeni gibanja), format.ts (Intl), theme.ts, nav.ts,
                        entities.ts, use-peek.ts (LX-02/08), sample-data.ts (do M1), api/ (generirano)
stores/                 focus (LX-03), proposals (lokalno do BL-053)
messages/{sl,en}.json   vsa besedila (VOICE.md §6)
e2e/                    Playwright
```

**Pravila:** nobenega besedila v komponentah, barve samo prek tokenov, gibanje samo prek `lib/motion.ts`, vsaka številka prek `lib/format.ts`. Glej DESIGN.md §8–§11.
