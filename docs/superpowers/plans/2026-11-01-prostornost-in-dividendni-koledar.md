# Prostornost in dividendni koledar — izvedbeni plan

> For agentic workers: execute inline using superpowers:executing-plans; one final independent review.

**Goal:** Velik zaslon uporabiti za pregledne tabele, omogočiti filtre in uporaben koledar znanih dividend.
**Architecture:** obstoječi Next/Radix/next-intl, dodaten read-only DTO in Decimal funkcije v FastAPI. Brez nove sheme ali modelnih klicev.
**Tech Stack:** TypeScript, React, CSS/Tailwind, Vitest/Playwright; Python/Pydantic, pytest, Postgres.
**Spec:** ../specs/2026-11-01-prostornost-in-dividendni-koledar-spec.md

## Global Constraints
:3000/živi podatki ostanejo; samo :3100 po preverjanju, brez reseeda. Vse SL/EN. Ne skrij opozoril, ne ponastavi preferenc. Neznano ni0 in ocena ni potrjen prihodek.

## Review Focus
1. Uporabnikova širina ostane; 1920/2560px izraba in telefon brez page overflow.
2. Filter Predlogov pred LIMIT, napaka done ni uspeh, drug query/Peek ostane.
3. Ocena delta ne sešteva različnih datumov/valut/nerazrešene identitete.
4. Dividende: tax, korekcije, prejeto+open ista akcija, manjkajoč datum/znesek, brez implicitnega FX.
5. Pregled stanj Tez ne spremeni stanja in ne skrije urejanja osnutka ali pending odločitev.

## T1 [BL-229]: širina in zložljiva zaloga
- [x] RED browser1920/2560: prostor strani, tabela brez nepotrebnega drsenja; obstoječe preference/telefon ohranjeni.
- [x] PageHeader wide oznaka, AppShell selektor; AnalysisRunList različne širine brez spremembe shranjenih. WatchlistPanel reserve details privzeto zaprt, count in keyboard.

## T2 [BL-229]: Predlogi in Teze
- [x] RED API/UI: status/search pred LIMIT, invalid done v pozornosti, URL/default združljivost; brez pisanja ob filtru.
- [x] routes/proposals.py + hooks/ProposalList; vse vrste stanj, pregledno prazno stanje in število prikazanih zapisov.
- [x] ThesisDetail aktivna stanja z ničlami + read-only pregled; DraftEditor in pending sprejem ostaneta nespremenjena.

## T3 [BL-229]: kompaktna kartica in dnevna ocena
- [x] RED domain portfolio_daily: Decimal, missing/FX/mixed-date/short/zero/identity; API DTO in service brez N+1.
- [x] LiveOverview krajši footer + SignedChange za znesek/odstotek, podatkovna razlaga in izrecna vrzel.

## T4 [BL-230]: koledar dividend
- [x] RED domain dividend_calendar: meseci/leta po valutah, davčna vrzel, popravki, linked cash+open, brez pay_date/amount.
- [x] Add calendar DTO to DividendsOut/get_dividends; noben nov ingest/napoved termina.
- [x] DividendCalendar komponenta: 12 dostopnih mesecev, leto/valuta, datumi/instrumenti, letni povzetek, nerazporejeno + uskladitve.

## T5 [BL-231]: laboratorij in zaključek
- [x] Napiši ločen predlog SPEC zgodovinskih kazalnikov in poznejših pravil; primerjaj primarne vire LEAN/VectorBT/Backtrader, brez novega izvajalnika zdaj.
- [x] API/web regresije, generirani OpenAPI/TS, lint/typecheck/i18n, Linux build; E2E SL/EN desktop/phone in širok zaslon.
- [x] Neodvisni pregled, odprava ugotovitev, DESIGN/SESSIONS/BACKLOG, commit in samo demo :3100.

## Zaključek S-027

Izvedeno BL-229/230, [dokazi](../../implementation/2026-11-01-prostornost-in-koledar-dokazi.md). API618+1 pogojni skip, web199/49, celotni E2E100+12 namernih skipov. Neodvisni ponovni pregled PASS. Dopolnitev po pregledu: FX target zahteva dokaz; native skupine ohranijo vrzeli. Laboratorij ima predlog SPEC, BL-231 implementacija ostane next. Samo demo3100, brez reseeda/push/merge;3000 ohranjen.
