# Dokazi in sprejemni pregled S-029

## Izvedeno in preverjeno

BL-234/235/237/238, ADR-0027/0028. API643 passed +1 conditional Redis skip (19 predhodnih SQLAlchemy opozoril); agents229 passed; web219 passed v53 datotekah; browser110 passed +12 namernih device-specific skipov. Ruff247 API datotek/46 agents, mypy146 API/23 agents, TypeScript/ESLint/i18n1508 ter produkcijski Docker build. OpenAPI in TS se generirata iz dejanskega API-ja, ne urejata ročno.

Alembic migraciji0021 in0022 sta aditivni. Celotni testi uporabljajo samo lastno začasno Postgres bazo z resetom downbase/uphead. Alembic check brez razlik; model zdaj vsebuje že obstoječi parcialni active-weight index, primerjava izloči le Timescale lastni bar_day_idx. Obnova lastnih sintetičnih tabel instrument/price_history_capture v ločeno migrirano bazo potrdi2 zajema, enak agregat prstnih odtisov in zavrnitev UPDATE. To ni dokaz celotne obnove zasebne baze, ki ostaja drug backlog.

Demo3100 nadgrajen brez reseeda. Kontrolna točka pred browser testi:21 predlogov,5 analiz,3 tez ostanejo;12 sintetičnih YTD zajemov, schema0022. Browser testi lahko ustvarijo svoje zapise. Za prijavo uporablja ločeni disposable sklad3200 le testne poverilnice; ni namenjen telefonu ali produkciji.

## Astra pregled in odprava

1. A→B→A zajemi niso globalno deduplicirani; zaklenjeno zadnje opažanje + monotoniID ohranita novo opažanje. Znani con_id je obvezen na provider/service/store mejah.
2. Jan1 demo je veljaven no-op, zgodovinski DB testi imajo fiksen čas. Zastarelost loči obdobje podatka od časa pridobitve.
3. API ima neposredno avtentikacijo, ne samo UI preusmeritve. CSRF Origin, pretočna omejitev teles, varne poti/redirect, frame/nosniff/referrer/permissions glave.
4. .env/secrets/ključi so izločeni iz obeh Docker kontekstov. Flex napaka ne veriga URL izjeme, centralni HTTP dnevniki imajo idempotentno čiščenje.
5. SSE se prekine ob preklicu/poteku; query/cache se po odjavi skrije tudi drugemu zavihku. Polli ne osvežujejo idle roka. Skrito drevo ohrani neshranjene obrazce; regresija to preveri tudi pri poznem odgovoru preverjanja.

Končni bralni pregled: PASS, brez preostalih P1/P2. Noben živ vdor, resnična pošta, LLM klic ali naročilo ni del preverjanja.

## Sprejemni koraki uporabnika

- Na3100: Portfelj → YTD pokaže podpisane numerične skupine po valutah, razlaga pa demo vir/capture ID in čas. Podatek ni NAV/celotni donos; dividende in trgovanje niso vključeni. Neznan dokaz ostane opozorilo.
- V Pozicijah/Watchlisti odpri Zastarelo, preveri katera cena/kazalnik je star ter vir/obdobje/čas; zapri, preveri kompaktnost. Preveri skrite stolpce in zadnjo vrstico.
- Oglej si /login in štiri podporne strani brez zasebnih kontrol. Dejanski lastniški račun in telefon nastavi po [navodilih](./2026-11-02-zasebni-dostop-navodila.md). Gesla ne pošiljaj v pogovor.
- Po aktivaciji preveri neposredni /api/portfolio brez seje401, prijavo in odjavo v dveh zavihkih, Back ter ohranjen osnutek pri preklopu aplikacije. Odjava ne izbriše že prenesenih podatkov ali lokalnih osnutkov.

## Meje predaje

Živi IBKR zgodovinski zajem potrebuje dostopen read-only Gateway, kvalificiran con_id in dovoljenja. Trenutni sintetični testi niso živa potrditev ponudnika. Tuji zneski ostanejo ločeni do potrjene ciljne valute FX.

GitHub master push je uporabnik odobril. Končni remote SHA in CI se preverita ob objavi; to ne dovoljuje zamenjave obstoječega3000. Tailscale pravilo je pripravljeno, dejanski Save/validator in test S26 še nista avtomatsko potrjena. Serve443→8090 ostane. Šele po lokalnem geslu in pravilih se omogoči8443 na ločeni zasebni namestitvi.

Odprti ostajajo BL-225/226/227/231, pravi razširjeni Flex, podatkovni FX, dejanska SMTP dostava in produktni backup/restore. Ta predaja jih ne označuje kot dokončane in ne zagotavlja »hackproof« ali pravne skladnosti javne storitve.
