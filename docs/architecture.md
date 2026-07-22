# Architecture

The Next.js App Router renders fixture-backed research pages primarily on the server. UI routes depend on the capability-oriented `MarketDataProvider` interface and domain objects, not raw JSON. A provider supplies an instrument snapshot, available price history, and either financial series or an explicit unavailable capability. `FixtureMarketDataProvider` validates bundled input with Zod, normalizes symbols, and exposes explicit not-found errors.

`/instruments/[symbol]` is the canonical research route. The former `/stocks/[symbol]` path permanently redirects after symbol normalization, preserving existing links while keeping navigation instrument-neutral.

Client components are limited to search filtering, chart interaction, and theme interaction. Price charts provide native pressed range controls and a screen-readable observation summary; the visual chart canvas is decorative. Financial trend charts preserve missing observations as gaps. A future licensed provider can replace the fixture implementation without changing instrument presentation components.
