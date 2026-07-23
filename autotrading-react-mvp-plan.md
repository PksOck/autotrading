# Autotrading — React Stock Research MVP

**Datum:** 2026-07-22  
**Repozitorij:** `PksOck/autotrading`  
**Predlagana veja:** `feat/stock-research-mvp`

## 1. Namen dokumenta

Ta dokument povzema potrjeno zasnovo in izvedbeni načrt za prvo različico projekta. Namenjen je prenosu na drug računalnik in nadaljevanju implementacije brez izgube konteksta.

Prvi izdelek bo spletna aplikacija za raziskovanje delnic, podobna ValueSnapshotu. Quant raziskave, napovedovanje, backtesting in avtomatsko trgovanje bodo ločene poznejše faze.

## 2. Ključne odločitve

- Prvi MVP je **stock-research portal**, ne trgovalni robot.
- Uporabniški vmesnik bo izdelan z Reactom in Next.js, ne s Streamlitom.
- Prva različica podpira ameriške delnice in fixture podatke.
- Vsak finančni podatek mora prikazati enoto, valuto, vir in čas osvežitve.
- Vrednotenje bo deterministično in razložljivo.
- TimesFM ni obvezna odvisnost.
- Napovedni modeli ne smejo neposredno oddajati naročil.
- Brokerji, paper trading in live trading niso del MVP-ja.

## 3. Obseg MVP-ja

### Vključeno

- domača stran;
- iskanje po simbolu in imenu podjetja;
- stran `/stocks/[symbol]`;
- cena, dnevna sprememba in osnovni tržni podatki;
- interaktivni cenovni graf;
- ključni fundamentalni kazalniki;
- letni in četrtletni finančni trendi;
- konservativni, osnovni in optimistični DCF scenarij;
- lokalna watchlista;
- metodologija in podatkovna pojasnila;
- responsive svetla in temna tema;
- loading, empty, stale-data in error stanja;
- avtomatizirani testi.

### Ni vključeno

- avtentikacija in naročnine;
- podatkovna baza uporabnikov;
- broker povezave;
- paper ali live naročila;
- backtesting;
- optimizacija strategij;
- TimesFM, Chronos, Qlib ali FinRL;
- AI priporočila za nakup ali prodajo;
- opcije, futures, forex in kripto.

## 4. Tehnološki sklad

- Node.js 22 LTS
- pnpm
- Next.js 15 z App Routerjem
- React 19
- TypeScript s `strict: true`
- Tailwind CSS 4
- shadcn/ui
- TradingView Lightweight Charts
- Zod
- Vitest
- React Testing Library
- Playwright
- ESLint in Prettier

## 5. Predlagana struktura

```text
autotrading/
├── docs/
│   ├── architecture.md
│   ├── methodology.md
│   └── roadmap.md
├── public/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── methodology/page.tsx
│   │   ├── watchlist/page.tsx
│   │   └── stocks/[symbol]/
│   │       ├── loading.tsx
│   │       ├── not-found.tsx
│   │       └── page.tsx
│   ├── components/
│   │   ├── charts/
│   │   │   └── price-chart.tsx
│   │   ├── layout/
│   │   │   ├── app-header.tsx
│   │   │   └── app-footer.tsx
│   │   ├── stock/
│   │   │   ├── stock-header.tsx
│   │   │   ├── metric-card.tsx
│   │   │   ├── financial-trends.tsx
│   │   │   └── data-provenance.tsx
│   │   ├── valuation/
│   │   │   ├── valuation-form.tsx
│   │   │   └── valuation-result.tsx
│   │   └── watchlist/
│   │       └── watchlist-button.tsx
│   ├── data/
│   │   ├── market-data-provider.ts
│   │   ├── fixture-provider.ts
│   │   └── fixtures/
│   │       ├── amzn.json
│   │       ├── aapl.json
│   │       └── msft.json
│   ├── domain/
│   │   ├── stock.ts
│   │   ├── financials.ts
│   │   ├── price-history.ts
│   │   └── valuation.ts
│   ├── lib/
│   │   ├── format.ts
│   │   └── watchlist-storage.ts
│   └── test/
│       └── setup.ts
├── e2e/
│   ├── stock-search.spec.ts
│   ├── stock-detail.spec.ts
│   └── watchlist.spec.ts
├── package.json
├── playwright.config.ts
├── tsconfig.json
└── vitest.config.ts
```

## 6. Podatkovna pogodba

```ts
export type PriceRange = "1M" | "6M" | "1Y" | "5Y" | "MAX";

export interface MarketDataProvider {
  searchStocks(query: string): Promise<StockSearchResult[]>;
  getStockSnapshot(symbol: string): Promise<StockSnapshot>;
  getPriceHistory(
    symbol: string,
    range: PriceRange,
  ): Promise<PricePoint[]>;
  getFinancials(symbol: string): Promise<FinancialSeries>;
}
```

Pravila podatkov:

- vsi timestampi so ISO-8601 UTC;
- valuta je obvezna;
- manjkajoča vrednost je `null`, nikoli `0`;
- vsak odgovor vsebuje `source` in `asOf`;
- provider podatke validira z Zod;
- cenovne točke morajo biti unikatne in časovno naraščajoče;
- UI ne sme prikriti zastarelih ali manjkajočih podatkov.

## 7. Stock stran

Pot: `/stocks/[symbol]`

Zaporedje vsebine:

1. podjetje, simbol, borza in valuta;
2. zadnja cena, dnevna sprememba in čas osvežitve;
3. gumb za watchlisto;
4. graf z obdobji `1M`, `6M`, `1Y`, `5Y`, `MAX`;
5. market cap, enterprise value, P/E, EV/EBITDA in FCF yield;
6. prihodki, operativni dobiček, FCF, marže in diluted shares;
7. trije scenariji vrednotenja;
8. tveganja, metodologija, vir in omejitve.

## 8. Vrednotenje

```ts
export interface ValuationAssumptions {
  normalizedFcf: number;
  growthRate: number;
  explicitYears: number;
  terminalGrowthRate: number;
  discountRate: number;
  netDebt: number;
  dilutedShares: number;
}
```

Obvezna pravila:

- terminalna rast mora biti manjša od diskontne stopnje;
- diskontna stopnja mora biti pozitivna;
- število delnic mora biti večje od nič;
- ekstremne predpostavke prikažejo opozorilo;
- rezultat je označen kot ocena, ne priporočilo ali ciljna cena;
- vse formule imajo enotne teste.

## 9. Izvedbeni mejniki

### Mejnik 1 — Vertikalni AMZN prototip

- inicializacija Next.js projekta;
- CI, lint, typecheck in test ukazi;
- osnovni layout in tema;
- domenski tipi in Zod sheme;
- `FixtureMarketDataProvider`;
- iskanje;
- popolna `/stocks/AMZN` stran;
- osnovni responsive testi.

### Mejnik 2 — Grafi in finančni trendi

- Lightweight Charts;
- izbira obdobja;
- volume;
- revenue, operating income in FCF grafi;
- stale in missing-data stanja;
- test urejanja in deduplikacije časovnih točk.

### Mejnik 3 — DCF in watchlista

- DCF računanje po TDD;
- trije scenariji;
- urejanje predpostavk;
- validacijska opozorila;
- `localStorage` watchlista;
- Playwright test persistence.

### Mejnik 4 — Pripravljenost na pravi API

- contract testi providerja;
- cache in retry politika;
- zaščita API ključev na strežniški strani;
- metodologija in data-provenance dokumentacija;
- izbira licenciranega podatkovnega ponudnika.

## 10. Preverjanje

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm build
```

MVP je zaključen, ko:

- uporabnik poišče AMZN in odpre stran;
- vsak podatek prikaže enoto in svežino;
- graf deluje v vseh obdobjih;
- DCF se pravilno preračuna in zavrne nevarne vnose;
- watchlista ostane po osvežitvi;
- desktop in mobile Playwright testi uspejo;
- aplikacija ne vsebuje trgovalnih ali napovednih trditev.

## 11. Prihodnja quant arhitektura

Napovedovanje je ločen podsistem:

```text
Point-in-time podatki
        ↓
Feature pipeline
        ↓
Naive benchmarki
        ↓
LightGBM cross-sectional ranking
        ↓
Walk-forward validacija in kalibracija
        ↓
TimesFM / Chronos kot neobvezna challenger modela
        ↓
Risk engine
        ↓
Paper trading
        ↓
Live execution
```

Model napreduje samo, če po stroških preseže:

- random walk;
- always-up oziroma base-rate napoved;
- preprost linearni model;
- LightGBM baseline.

Metrike morajo vključevati neto donos, Sharpe, max drawdown, turnover, kalibracijo, stabilnost po režimih in statistično značilnost. Sama directional accuracy ni dovolj.

## 12. Nadaljevanje na drugem računalniku

```bash
git clone https://github.com/PksOck/autotrading.git
cd autotrading
git switch -c feat/stock-research-mvp
```

Priporočen ukaz za Codex:

> Implementiraj prvi mejnik iz dokumenta `autotrading-react-mvp-plan.md`. Uporabi Next.js, React, TypeScript, fixture podatke in TDD. TimesFM, backtesting in broker integracije niso del MVP-ja. Najprej pripravi delujočo `/stocks/AMZN` vertikalo in poženi lint, typecheck, unit ter Playwright teste.

## 13. Varnost in odgovornost

- API ključi ne smejo biti poslani v odjemalca ali shranjeni v Git.
- Vsi analitični rezultati morajo imeti vir, čas in omejitve.
- Live trading zahteva kill switch, omejitve pozicij, idempotentnost naročil, reconciliation in audit log.
- Raziskovalni rezultat ni finančno priporočilo.
