# Prevzem celotnega paketa za Claudov pregled

**Datum:** 2026-10-30 · **Seja:** S-020 · **Način:** pregled brez implementacije, merge ali deploy.

## 1. Kaj naj Claude odpre

- Delovni checkout: `C:/Users/Jan/.codex/worktrees/signal-expiry-fix/Claude-autotrading`.
- Veja s celotnim paketom: `feat/uxui-demo-upgrade`.
- Izhodišče novih sprememb: `1855eb8d37a6257d3b096ca055d0d9c665a4a20e`.
- Cilj pregleda: aktualni HEAD navedene veje, vključno s to datoteko in planom odprtega dela.

**Ne pregleduj samo `HEAD^..HEAD`:** zadnji commit je dokumentarni prevzem/plan. Produktna koda in testi so tudi v predhodnih commitih iste veje. Commita ne pomeni nujno prenosa v Claudovo vejo ali :3000.

Preverjeni vmesni produktni točki sta `cfcbb55` (prva integracija UX/podatki/avtomatika/dividende) in `bd33131` (uporabniške dopolnitve, SMTP, testiranje shranjenih zapisov). Pred njima so signalne regresije, specifikacije in podatkovna inventura. Podrobno časovnico hranijo S-015–S-020 v SESSIONS.md.

Uradni načrt iz izvorne Claudove veje je pri `28f2990`. Skupni prednik te veje in pregledne veje je zgornji `1855eb8`. Izvorni načrt je bil prevzet v pregledno vejo; izvorni checkout in njegove lokalne spremembe se ne prepisujejo. Trenutni `master` je lahko druga osnova in ne predstavlja samo razlike tega paketa.

## 2. Ukazi za pregled brez spremembe checkouta

Iz kateregakoli checkouta istega lokalnega repozitorija:

```powershell
git log --oneline 1855eb8..feat/uxui-demo-upgrade
git diff --stat 1855eb8..feat/uxui-demo-upgrade
git diff 1855eb8..feat/uxui-demo-upgrade -- services/api services/agents apps/web infra
git diff 1855eb8..feat/uxui-demo-upgrade -- docs BACKLOG.md PLAN.md DESIGN.md SESSIONS.md
```

Najprej preveri dejanske reference in stanje obeh vej. Ne izvajaj checkout/reset/cherry-pick/merge/rebase nad aktivnim ali umazanim Claudovim delovnim drevesom samo zaradi pregleda. Ob dodatnih novejših commitih zapiši dejansko pregledani končni hash.

## 3. Dokumenti in obseg

1. [SESSIONS](../../SESSIONS.md), [PLAN](../../PLAN.md), [BACKLOG](../../BACKLOG.md) in [DESIGN](../../DESIGN.md).
2. [Celoviti UX/UI SPEC](../superpowers/specs/2026-10-28-celovita-uxui-spec.md) in [izvorni načrt](../superpowers/plans/2026-10-28-celovita-uxui-nadgradnja.md).
3. [Prva integracija in njene meje](./2026-10-29-pregled-sprememb.md), [dopolnitve po uporabniškem pregledu](./2026-10-29-dopolnitve-po-pregledu.md).
4. [Enotni plan nedokončanega dela](../superpowers/plans/2026-10-30-zakljucevanje-odprtih-sklopov.md) — 49 odprtih/delnih/odloženih nalog s povezavo na pakete A–K.
5. [Priprava naslednjih SPEC](../superpowers/specs/2026-10-30-odprti-sklopi-priprava-spec.md) — to še niso končni izvedbeni SPEC posameznih sklopov.
6. [ADR indeks](../adr/README.md), posebej ADR-0017–0022; evidence virov/identitete/dividend v tej mapi.

## 4. Na kaj naj se pregled osredotoči

- **Finančna pravilnost:** več računov in datumov, prazen proti odsotnemu posnetku, frakcije, FX/valuta, cena posnetka proti tržni ceni, Decimal/numeric, zadnja uspešna analiza pred limitom.
- **Viri in neznanke:** forward P/E ni P/E TTM; donos ni DPS; valuta poročanja ni trgovalna valuta; makro kartica ali sintetična demonstracija ne dokazuje živega vira.
- **Avtomatika:** izklop pred naslednjim LLM klicem, ročni izvor/izjema okna, transakcijska kvota, DST, replay/recovery, aktivne rezervacije in otroški pregledi tez brez dvojnih plačljivih klicev.
- **SMTP:** TLS, več prejemnikov, revizije, deduplikacija, pavza med dostavami, negotov izid brez slepe ponovitve; nastavitve ne smejo same poslati sporočila.
- **Dividende:** stroga XML pogodba, identiteta/ponovitev/konflikt, podpisana gotovina in davki, odprti obračuni, pokritost ter ocena ostanejo ločeni; opozori na meje usklajevanja brez zadostnega dokaza.
- **Študija dogodkov:** čas razpoložljivosti, poznejši vstop, dokončane seje, stroški/smer, omejeno branje sveč, nepopolna zgodovina in pristranskosti; rezultat ni simulirani kumulativni portfelj.
- **UX:** standardni profili, opozorila tudi ob skritih stolpcih, predznaki/barve, trend z obdobjem, točen detail po ID, Back/Escape/fokus, ohranitev osnutka in mobilna dostopnost.
- **Plan/SPEC:** nobena odprta naloga brez paketa/merila; odloženi moduli niso prikriti pogoji prve izdaje; zastareli statusi niso napačno done; načrt ne obljublja nepreverjenih pravic ali podatkov. Predlagaj jasne dopolnitve naslednjih SPEC.

## 5. Prejšnje preverjanje in poštene omejitve

Predhodni rezultati so dokumentirani v S-018: 547 API, nato 32 ciljnih kontrol, 221 agentskih in 155 spletnih testov uspešnih; tipi/lint/i18n ter Docker build. Celotni brskalniški zagon je imel 59 uspešnih, 10 namerno preskočenih in numerično napako meritve 48px; po popravku testa je 16 ciljnih poti uspešnih. Dokumentarno je preverjena matrika 49 odprtih nalog in lokalne povezave. To niso sveže ponovno izvedeni testi tega dokumentarnega koraka.

Pri ponovnem preizkusu uporabi samo namenske testne baze, nikoli žive baze. API fixture lahko izvede downgrade/upgrade in truncate. Dve zbirki ne smeta sočasno uporabljati iste baze. Native Windows SWC ima znano omejitev predpomnilnika; produkcijska gradnja je bila preverjena v Linux Dockerju. Ne sproži resničnih sporočil/analiz samo zaradi preverjanja.

Še odprti ostajajo dejanski razširjeni Flex, robovi gotovine/valute, živa pokritost fundamentov, nerešene kotacije, makro viri, dejanska SMTP dostava, trajni ključ oddaje čez reload in širši UX/backtesting. Celotnega prvotnega načrta ne označi kot implementiranega.

## 6. Omejitev objave

Pregledna aplikacija je na **:3100** s sintetičnimi podatki. **:3000 ni posodobljen in ga ni dovoljeno posodobiti brez nove izrecne potrditve uporabnika.** Tudi nova stikala iz pregledne kode še ne upravljajo njegovih starih delavcev. Ne izvajaj prenosa ali združevanja zaradi tega navodila za pregled.

## 7. Poziv za Claude

```text
Review the complete local branch feat/uxui-demo-upgrade against baseline
1855eb8d37a6257d3b096ca055d0d9c665a4a20e, not only the last documentation commit.
Start with docs/implementation/2026-10-30-prevzem-za-claude-pregled.md and the
repository instructions. Review both the implemented code and the remaining-work
plan / specification preparation. Record the exact reviewed HEAD.

Perform a read-only review. Do not edit implementation, rewrite history, merge,
deploy to :3000, send notifications, or trigger provider/LLM calls. Preserve all
existing Claude worktree changes. Use isolated databases only if running tests.

Return findings in Slovenian, ordered by severity, with file/line, concrete
failure scenario, evidence and suggested correction. Distinguish confirmed bugs,
known documented limitations, missing verification and suggestions. Review the
plan for omissions, dependencies, acceptance criteria and false completion claims.
State what you actually verified and list the next SPEC documents to prepare.
Do not claim the entire application or live data connections are validated.
```
