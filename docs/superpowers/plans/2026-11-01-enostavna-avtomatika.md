# Enostavna avtomatika — izvedbeni plan

> Execute inline using superpowers:executing-plans; root implements, one final independent read-only review.

**Goal:** Vedno vidna pavza vse avtomatike in hitra stikala modulov brez izgube urnikov.
**Architecture:** obstoječi revisioned control/policy API, ločen pregled in posnetek urejevalnika v React; brez backend sprememb.
**Tech Stack:** React/Next/next-intl, TanStack Query, Vitest/Playwright.
**Spec:** ../specs/2026-11-01-enostavna-avtomatika-spec.md

## Global Constraints

Samo3100, brez reseeda ali spremembe3000. UI SL/EN,48px dotik. Pavza ohrani modul/urnik. Brez /run ob preklopu, brez novega API/migracije.

## Review Focus

1. Hiter vklop ne prepiše starih terminov ali oživi izklopljenih modulov.
2. Napaka/409/pending ne ustvari navideznega uspeha ali ponovitve.
3. Globalni preklop/refetch ne izbriše neshranjenega urejevalnika.
4. Manual/process off/paused niso running; drugo control polje ostane.
5. Phone/SL/EN dostopnost, brez izgube ročnega zagona, kvot ali sledi.

## T1 — BL-232: RED in pregled avtomatike

- [x] Testi glavnega stikala, celotnih modulov, napak/pending/CAS in nespremenjenega urnika.
- [x] AutomationSettings + hitra stikala, skupine, shranjen urnik/stanje, modelno stikalo in pomoč; obstoječi hooki/API.

## T2 — BL-232: urejevalnik in vključitev

- [x] Test umazanega osnutka, ohranitve pri refetchu, shranjevanja skritih polj in izrecnega discard/reload.
- [x] Izločiti ProcessPolicyEditor iz SettingsView, dodatne omejitve in ročni zagon razkrita ločeno; pregled na vrh nastavitev, batch/sledi ohranjeni.

## T3 — dokaz in predaja

- [x] Web suite, TS/ESLint/Prettier/i18n, Linux build, samo demo web3100.
- [x] SL/EN/phone E2E s prestreženimi zapisi, vizualni pregled in obstoječe regresije nastavitev/pomoči.
- [x] Neodvisni pregled/popravki, SESSIONS/DESIGN/BACKLOG/PLAN in lokalni commit brez pusha.

## Dodano med izvedbo — BL-233

**Spec:** ../specs/2026-11-01-portfelj-gostota-in-obdobja-spec.md. Uporabnik je dodal gostoto obeh tabel in dnevni/YTD prikaz. Root nadaljuje po T2, pred končnim T3.

- [x] RED browser za vrstice/datum in komponentni test fiksne gostote; compactRows samo Pozicije/Watchlista, sredinska navpična poravnava in kompaktno razkritje ob grafu.
- [x] RED Decimal/DB za YTD baseline ter komponentni izbor Dan/YTD, vrzeli in valute.
- [x] Strežniški baseline read/DTO, generirana pogodba in PortfolioChangeSummary ob vrednosti; brez provider refresh in namišljenega EUR/YTD.
- [x] API/splet regresije in finalni T3 za skupni obseg BL-232/233; :3000 ostane.

## Zaključek S-028

[Dokazi](../../implementation/2026-11-02-zakljucek-avtomatika-portfelj.md): API620+1skip, web213/51, browser106+12namernihskipov. Astra re-review brez novih pomembnih ugotovitev. Produkcijski številčni YTD ostaja podatkovna zmožnost BL-234; izvedeni so izbirnik, pravilen izračun na preverjenem sintetičnem primeru in varovalo nepreverjene osnove. Samo3100, brez reseeda/pusha;3000 ohranjen.
