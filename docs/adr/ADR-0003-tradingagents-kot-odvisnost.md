# ADR-0003: TradingAgents kot odvisnost, ne fork
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-001

## Kontekst
TradingAgents (Apache-2.0) ponuja zrel agentski graf za analizo delnic, s strukturiranim izhodom in pretakanjem korakov. Projekt se hitro razvija (izdaja vsake 2 do 3 tedne).

## Odločitev
Uporabimo ga kot **pip odvisnost z zaklenjeno verzijo** za globoko analizo **delnic**. Prilagoditve delamo prek njihovih razširitvenih točk: lasten podatkovni vendor (`vendor_local`), konfiguracija modelov (backend URL na LiteLLM) in portfelj kot kontekst. ETF-je, vzrok padca, opcije in teze pokrivajo **naši** cevovodi.

## Posledice
- Posodobitve so ročne, po regresijskem testu na fiksnih posnetkih (BL-086).
- Če bomo potrebovali globlje spremembe grafa, nov ADR odloči o forku.

## Zavrnjene možnosti
- **Fork:** prevzamemo vzdrževanje 28k vrstic.
- **Lasten graf od začetka:** podvajanje dela, ki je že dobro narejeno.
- **Vibe-Trading kot jedro:** prevelik, nestabilen, izvaja LLM-generirano kodo.
