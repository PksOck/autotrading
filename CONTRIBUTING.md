# Razvoj in izdaje

Najprej preberi AGENTS.md, zadnjo sejo SESSIONS.md, PLAN in relevantni BACKLOG. Dokumentacija je slovenska, koda/commiti angleški. Ena BL naloga naj ima čim bolj samostojen pregled. Brez skrivnosti, samodejnih naročil ali modelnih števil kot dejstev.

## Preverjanje

- API: `uv sync --frozen`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest -q`. Integracije samo na lastni testni bazi s TEST_DATABASE_URL; testi jo resetirajo.
- Agents: enaki Python koraki v `services/agents`; omrežni modeli so v testih zamenjani s sintetičnimi posnetki.
- Web: `pnpm install --frozen-lockfile`, nato v apps/web `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, `pnpm i18n:check`.
- Browser: zagnan ločeni demo3100, BASE_URL=http://127.0.0.1:3100. Lastniška prijava ima ločeni disposable auth-test3200. Ne usmerjaj testov na zasebno namestitev.
- Koren: `python scripts/check_version.py`. OpenAPI in TS se generirata; ne urejata se ročno.

## Nova različica

1. Izberi PATCH za popravek ali MINOR za nov obseg. Dokler je MAJOR0, je aplikacija še v razvoju.
2. Posodobi VERSION, root/web package.json, API/agents pyproject.toml in API __version__; osveži oba uv.lock. Checker potrdi vse številke.
3. Dopolni CHANGELOG, namestitvena navodila in odprte naloge. Ne trdi, da je deploy izveden samo zato, ker je koda objavljena.
4. Opravi relevantne teste in CI na konkretnem commitu. Tag `vX.Y.Z` ustvari šele na preverjenem commitu, brez force; obstoječe oznake se ne premikajo.
5. GitHub izdaja ima povzetek, meje podatkov, migracije, testna dokazila in znane odprte naloge. Za testno izdajo uporabi prerelease. Naslednji popravek dobi novo verzijo.
6. Namestitev nadgradi iz izbrane oznake, z lokalnimi poverilnicami in preverjeno varnostno kopijo. Posodobitev :3000 ali zasebnih podatkov zahteva ločeno pooblastilo lastnika.
