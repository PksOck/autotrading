# ADR-0005: i18n: slovenščina privzeto, next-intl
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-001

## Kontekst
Uporabnik želi slovenski vmesnik z možnostjo preklopa na angleščino.

## Odločitev
- `next-intl`, datoteke `apps/web/messages/sl.json` (vir resnice) in `en.json`.
- Privzeti jezik je `sl`, izbira v piškotku in nastavitvah. URL-ji brez jezikovne predpone (interna aplikacija).
- Formatiranje števil, datumov in valut samo prek `Intl` (VOICE.md §3).
- Povzetki agentov se generirajo v izbranem jeziku. Pozivi agentom so v angleščini (VOICE.md §7).

## Posledice
- V komponentah ni nobenega trdo kodiranega besedila (preverja CI, BL-008).
- Slovenska množina ima 4 oblike (ICU `one/two/few/other`).

## Zavrnjene možnosti
- `react-i18next`: manj naravna integracija s strežniškimi komponentami App Routerja.
- Jezikovna predpona v URL (`/sl/...`): nepotrebno za interno aplikacijo.
