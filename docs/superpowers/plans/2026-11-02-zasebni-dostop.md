# Zasebni dostop Implementation Plan

> Execute inline using executing-plans; Astra provides read-only review. User authorized implementation.

**Goal:** Lastniška prijava, zaščiten API in pregledna navodila za zaseben HTTPS dostop s telefona.
**Architecture:** FastAPI opaque DB sessions + mandatory production guard; Next login/proxy gates; Tailscale Serve operational handoff.
**Spec:** ../specs/2026-11-02-zasebni-dostop-design.md

- [x] BL-237: RED testi scrypt, neposredni API, Origin, expiry/logout, global throttle; modeli/migracija0022, auth service/routes/middleware, konfiguracija in lokalni CLI.
- [x] BL-238: prijavna stran, gate aplikacije/API, varni proxy tok/URL, odjava, glave; SL/EN spremljevalne strani in footer, testi obhodov.
- [ ] BL-239: Docker/Tailscale navodila z ACL samo telefon, brez Funnel ali spremembe3000; neodvisni Astra pregled in popravek.
- [ ] Ponoviti končne suite/build/schema/migracijo in pregled3100, zaključiti YTD BL234/235 ter predajo BL236; posodobiti dokumentacijo, commit/push master brez force in preveriti remote/CI.

Preverjanje: API643+1skip; agents229; web219; E2E110+12device skip. Astra PASS. BL239 operativno odprt: uporabnik dobi konkretni zasebni JSON za Save, geslo nastavi lokalno, nato Serve/test naprave. GitHub predaja je odobrena, še potrditi remote/CI.

GitHub koda objavljena v d859fce, CI41477710171 success. Dokumentacija in lokalna priprava zasebnega sklada sta dokončani; dejanski BL239 še zahteva Save pravil, lokalno geslo in test naprave.
