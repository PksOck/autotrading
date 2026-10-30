# Arhitekturne odločitve (ADR)

Vsaka odločitev, pri kateri bo kdo kasneje vprašal "zakaj tako?", dobi svoj zapis.
Format: `ADR-xxxx-kratek-naslov.md`, statusi: `predlagano` · `sprejeto` · `zamenjano z ADR-yyyy`.

| ID | Naslov | Status |
|---|---|---|
| [ADR-0001](./ADR-0001-docker-lokalno.md) | Gostovanje: Docker lokalno, Tailscale | sprejeto |
| [ADR-0002](./ADR-0002-python-backend-nextjs-frontend.md) | Python backend, Next.js frontend | sprejeto |
| [ADR-0003](./ADR-0003-tradingagents-kot-odvisnost.md) | TradingAgents kot odvisnost, ne fork | sprejeto |
| [ADR-0004](./ADR-0004-llm-vloge-litellm.md) | LLM vloge prek LiteLLM | sprejeto |
| [ADR-0005](./ADR-0005-i18n-sl-privzeto.md) | i18n: slovenščina privzeto, next-intl | sprejeto |
| [ADR-0006](./ADR-0006-clovek-vedno-odloci.md) | Človek vedno odloči, brez samodejnih naročil | sprejeto |
| [ADR-0007](./ADR-0007-telegram-obvestila.md) | Obvestila prek Telegrama | sprejeto |
| [ADR-0008](./ADR-0008-instrumenti-ucits.md) | Instrumenti: ameriške delnice + UCITS ETF-ji | sprejeto |
| [ADR-0009](./ADR-0009-napredni-ux-motion.md) | Napreden UX: gibanje, povezani pogledi, pregledi | sprejeto |
| [ADR-0010](./ADR-0010-vstopi-pravila-ta-lib.md) | Vstopi: pravila s TA-Lib, signal samo z nedotaknjeno tezo | sprejeto |
| [ADR-0011](./ADR-0011-storitev-agentov.md) | Globoka analiza v ločeni storitvi `agents`, TradingAgents bere posnetek naše baze | sprejeto |
| [ADR-0012](./ADR-0012-tedenski-pregled-tez.md) | Tedenski pregled tez | sprejeto |
| [ADR-0013](./ADR-0013-oblikovanje-android-windows.md) | Oblikovanje Android/Windows | sprejeto |
| [ADR-0014](./ADR-0014-obeti-po-obdobjih.md) | Obeti po obdobjih | sprejeto |
| [ADR-0015](./ADR-0015-kalibracija-utezi.md) | Kalibracija uteži s potrditvijo | sprejeto |
| [ADR-0016](./ADR-0016-vitka-zaporedna-analiza.md) | Vitka zaporedna analiza | sprejeto |
| [ADR-0017](./ADR-0017-metapodatki-in-read-modeli.md) | Metapodatki metrik in skupni bralni modeli | sprejeto v pregledni veji |
| [ADR-0018](./ADR-0018-preference-tabel.md) | Preference tabel in stanje v URL | sprejeto v pregledni veji |
| [ADR-0019](./ADR-0019-politike-procesov.md) | Politike procesov in paketnih analiz | sprejeto v pregledni veji |
| [ADR-0020](./ADR-0020-dividende-evidence-in-pokritost.md) | Dividendne evidence in pokritost | sprejeto; živi XML še nepreverjen |
| [ADR-0021](./ADR-0021-nadzor-modelov-in-email.md) | Nadzor samodejnih modelov in SMTP | sprejeto v pregledni veji |
| [ADR-0022](./ADR-0022-testiranje-shranjenih-mnenj.md) | Testiranje shranjenih signalov in mnenj | sprejeto v pregledni veji |

## Predloga

```markdown
# ADR-xxxx: <naslov>
**Status:** predlagano · **Datum:** LLLL-MM-DD · **Seja:** S-xxx
## Kontekst
## Odločitev
## Posledice
## Zavrnjene možnosti
```
