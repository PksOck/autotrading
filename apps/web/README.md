# apps/web: frontend

Next.js 15 (App Router) · React 19 · Tailwind 4 · shadcn/ui · TanStack Query · lightweight-charts · trading-signals · next-intl.

- **Zasloni:** `SCR-01`–`SCR-11` (DESIGN.md §4), poti so navedene tam.
- **Komponente:** `CMP-01`–`CMP-18` (DESIGN.md §3) v `components/<področje>/`.
- **Tokeni in teme:** `app/tokens.css` (DESIGN.md §2), `data-theme` na `<html>`.
- **Besedila:** samo v `messages/sl.json` in `messages/en.json` (VOICE.md §6, ADR-0005).
- **API tipi:** `lib/api/` je generiran iz OpenAPI (ne urejaj ročno).

Predvidena struktura (nastane v M0, BL-007 do BL-009):

```text
app/                 # poti po DESIGN §4
components/
  shell/             # CMP-01, CMP-02
  signals/           # CMP-03, 05, 06, 15
  radar/             # CMP-04, 16
  entries/           # CMP-07, 10
  instrument/        # CMP-13
  analysis/          # CMP-12
  options/           # CMP-14
  common/            # CMP-08, 09, 17, 18
lib/{api,format,indicators,options}/
messages/{sl,en}.json
```
