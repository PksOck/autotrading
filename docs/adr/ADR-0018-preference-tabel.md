# ADR-0018: Lokalne preference tabel in deljivo stanje v URL

**Status:** sprejeto za pregledno vejo · **Datum:** 2026-10-29 · **Seja:** S-017

## Kontekst

Pozicije, watchlista in analize potrebujejo izbirne stolpce ter različno gostoto. Deljena povezava mora ohraniti filtre in izbrani predmet brez odvisnosti od lokalnega brskalnika.

## Odločitev

- `preza.view.<module>.v1` v lokalni shrambi hrani dovoljene stolpce, vrstni red, širine, pripenjanje in gostoto. Pokvarjeni zapisi se varno normalizirajo; obveznih stolpcev ni mogoče odstraniti.
- Preference se berejo z `useSyncExternalStore`, zato strežniški izris in prvi odjemalčev izris ostaneta usklajena. Sinhronizacija med napravami ni vključena.
- Filtri, izbor, sortiranje in stran ostanejo v URL. API razvršča celotni vrnjeni nabor, null na konec obeh smeri; denarni zneski se razvrščajo po valutnih skupinah. Tabela lokalno razdeli urejen rezultat na strani po 25.
- Identiteta, dejanja in opozorila ostanejo vidni. Preurejanje ima gumbe za tipkovnico; obstoječa pravila dotikalnih ciljev ostanejo veljavna.

## Posledice

Profili Vrednotenje/Dividende so uporabni tudi z razloženimi vrzelmi. Poimenovane uporabniške predloge, primerjanje izbranih vrstic in enoten iskalnik vseh tabel ostajajo nadaljnje nadgradnje.
