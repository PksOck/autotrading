# Različice, GitHub predstavitev in lokalna prijava

> Execute inline; user authorized GitHub publication/version tracking and relocation of their owner configuration. Astra reviews authentication read-only.

**Goal:** Uporabnikov obstoječi bcrypt hash deluje, zasebni HTTPS dostop ima lastniški login, GitHub pa pregledno izdajo in sledljive različice.
**Architecture:** bcrypt kompatibilnost ob privzetem scrypt, obstoječi API-wide guard; VERSION=0.2.0 z enakimi paketnimi številkami/health/UI in CI preverjanjem; annotated tag in GitHub prerelease za uporabniško testiranje.

- [x] BL-240: RED/GREEN bcrypt2a/2b/2y, cost10–16, brez krajšanja nad72 UTF8 bajtov, malformed fail-closed; oba lockfile. Resnični hash samo lokalno, .env.example očiščen po izrecni potrditvi. Astra PASS.
- [x] BL-241 koda: VERSION, CHANGELOG, trenutni README in varnostna/razvojna navodila, preverjanje usklajenosti paketov/lockov in oznake, vidna verzija UI/API.
- [x] Testi, build, neposredni zaklep zasebnega3300; Serve8443 brez spremembe443 ali3000. Uporabnik ohrani sedanja Tailscale pravila: druge naprave omrežja imajo omrežni dostop, prijava je obvezna.
- [x] Commit/push master, CI, annotated v0.2.0 in GitHub predizdaja s konkretnimi mejami; brez skrivnosti ali zasebnih naslovov v objavi.

**Odločitev:** 0.2.0 je prva sledena razvojna izdaja za testiranje. GitHub jo označi kot prerelease; ne trdimo, da je zaključena implementacija vseh BL ali produkcijsko naročanje. Popravki nato0.2.1, nov obseg0.3.0. Označenih izdaj ne premikamo in ne uporabljamo force.

Dokazi: API649+1skip, web219, ciljnih6 browser (bcrypt+verzija SL/EN desktop/phone), Alembiccheck, ruff/mypy/TS/ESLint/i18n1509, checker pozitivni in napačni tag, produkcijski Docker build ter dejanski HTTPS200/307/401. GitHub opis/teme urejeni. Označitev/publikacija sledi zelenemu CI commita.

Objavljeno: annotated tagv0.2.0 →0ca8615e37638c49628bfa89a917db375c2a6abf, GitHub predizdaja https://github.com/PksOck/autotrading/releases/tag/v0.2.0. CI41486663845 in tag-check41487841802 success. Obstoječe oznake niso premaknjene.
