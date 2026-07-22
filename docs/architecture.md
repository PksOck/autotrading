# Architecture

The Next.js App Router renders fixture-backed research pages primarily on the server. UI routes depend on the `MarketDataProvider` interface and domain objects, not raw JSON. `FixtureMarketDataProvider` validates bundled input with Zod, normalizes symbols, and exposes explicit not-found errors.

Client components are limited to search filtering and theme interaction. A future licensed provider can replace the fixture implementation without changing stock presentation components.
