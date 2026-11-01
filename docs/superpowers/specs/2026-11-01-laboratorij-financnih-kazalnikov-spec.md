# Laboratorij: zgodovina kazalnikov in testiranje pravil

**Status:** predlog naslednjega modula, ne že izvedena funkcija. **Datum:** 2026-11-01. Uporabnik je potrdil: oboje, najprej zgodovinski kazalniki, nato pravila nakupa/prodaje. Predlagana pot /lab in ime Laboratorij sta izvedbena predloga, ne uporabnikova poimenovanja. Povezava z BL-216 (polni backtester) in BL-227 (dokazljiva merila), ne zamenjava /track-record.

## Kaj rešuje

/track-record odgovarja, kaj se je zgodilo po konkretnem shranjenem signalu ali mnenju. Laboratorij odgovarja, kako se je finančno stanje podjetja spreminjalo in kako bi se obnašala vnaprej določena strategija. Današnjega P/E ali poznejše popravljene bilance ne smemo vnesti v preteklost, ko še nista bila znana.

Prvi pogled: instrument, več izbirnih kazalnikov, obdobje ter TTM/četrtletje/leto. Cena in finančni kazalniki imajo ločene osi/panele z enotami. Pod grafom so vrednosti po obdobjih, datum objave, prva razpoložljivost, vir, različica in vrzeli. Uporabnik lahko shrani raziskovalni pogled, ne pa z njim odpreti borznega posla.

Drugi pogled: uporabnik sestavi pogoje, vstop/izstop, horizont, pogostost ponovnega izbora in stroške; pred izračunom vidi zamrznjen povzetek. Rezultat loči delež izpolnjenih meril od simulirane izvedbe. Prikaže posle, drawdown, donos, pokritost, preskoke ter občutljivost na stroške; kombinacij meril se ne razglasi za strategijo samo zaradi najboljšega preteklega izida. Test in validacijsko obdobje sta ločena, ponovni izbor parametrov ustvari novo verzijo. Brez modelnih klicev ob obisku.

## Podatkovna pogodba pred implementacijo

Sedanji Fundamentals ima en zapis na instrument, metrics/metrics_meta in history JSON za obstoječe potrebe. To ni samo po sebi arhiv vseh verzij in časov objav. Najprej popiši, katere zgodovinske serije vir dejansko zagotavlja, z dejanskimi fixtures; ne predpostavljaj, da je vsak metrics ključ razpoložljiv za vsako preteklo obdobje.

Predlagan immutable observation: instrument_id, metric_id, fiscal_period_start/end, period_type, unit, currency, basis, published_at, available_at, first_seen_at, source, source_record_id, version in supersedes_id. Popravki dodajo opažanje, ne prepišejo pretekle osnove. unknown available_at onemogoči point-in-time simulacijo, ne nujno opisnega grafa z vidno omejitvijo.

- Prihodki/EPS/FCF/marže so kandidati, ne obljuba pokritosti vsakega instrumenta. ETF in delnica nimata iste sheme. Vsak kandidat potrebuje vir, enoto in fixtures.
- Zgodovinski P/E TTM se računa iz takrat razpoložljivega EPS in primerljive, glede splitov usklajene cene. Forward P/E potrebuje arhiv takratnih napovedi; sedanja napoved ne postane zgodovinska.
- Simulacija potrebuje sestavo univerzuma takrat, umaknjene instrumente, corporate actions, čas izvedbe in dostopnost kotacij. FX/davki/slippage ter izposoja imajo izrecen podprt obseg; manjkajoče ni0.
- Decimal za denar, deterministični izračuni in verzioniran engine/method_id; LLM lahko razloži že izračunano, ne dopolni števil. Nobena simulacija ne piše dejanskega Signal/AnalysisRun ali broker naročila.

## Primerljive rešitve in izbira

- **QuantConnect/LEAN** je smiseln kandidat za poznejši celovit engine, ker uradna dokumentacija podpira zgodovino delnic in fundamentalnih objektov. Podatkovno pokritost/licenco za uporabnikove borze in UCITS moramo preveriti ločeno; engine ni dovoljenje za poljubne podatke. [Primarna dokumentacija](https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/asset-classes/us-equities).
- **VectorBT** je kandidat za hitro primerjavo več kombinacij pravil in portfolio simulacijo iz signalov. To ne reši pogodbe zgodovinskih fundamentalov; njegova numerična reprezentacija/stroški morajo prestati primerjavo z našimi Decimal fixtures. [Funkcije](https://vectorbt.dev/getting-started/features/).
- **Backtrader** ponuja jasen strategijski življenjski cikel in buy/sell/order callbacke; smiseln za eksplicitne dogodkovne simulacije. Za prvi read-only prikaz kazalnikov je uvajanje celotnega izvajalnika nepotrebno. [Strategy API](https://www.backtrader.com/docu/strategy/).

Predlagam obstoječi UI + lastno strogo podatkovno pogodbo za prvi zgodovinski pogled. Pred izbiro izvajalnika naredimo referenčno primerjavo ene iste strategije in cen v LEAN/VectorBT (vstop/izstop, stroški in corporate actions). Nove odvisnosti ali plačljivi podatki niso že vključeni s tem dokumentom.

## Zaporedje izvedbe in dokaz

1. Inventar history in izvornih objav za nekaj nedvoumnih instrumentov; podatkovne/licenčne vrzeli izrecno.
2. Ločen izvedbeni plan in migracija immutable observation; uvoz z restatement fixtures in source/as_of.
3. /lab Zgodovina: več serij, primerjava, tabelarična dokazila, shranjeni pogled. Test napačne osnove/valute, manjkajočega datuma objave, prepisanega EPS in splitov.
4. /lab Pravila: verzionirane simulacije, out-of-sample, bounded obseg in stroški. Test prepovedanega vpogleda v prihodnje podatke, nepodprtega instrumenta, umika kotacije ter izgubljenega odgovora istega zahtevka.
5. Povezave na Teze/osebno spremljanje ohranijo izvorno različico in čase; simulacija ne nadomesti dejanskega zgodovinskega mnenja.

## Dodatni predlogi za Predloge

Po novih filtrih so smiselni: vrstni red »potrebna odločitev«; kratko glavno dejanje glede na stanje (odpri sklep/analizo ali izrecno ponovi); uporabnikove oznake; zaznava podobnih hipotez iste delnice z možnostjo primerjave, brez brisanja starega predloga. Števec v vrsti in čas čakanja sta koristnejša od velikega stalnega uvoda. Skupinska ponovitev neuspelih se ne doda samodejno, ker lahko porabi kvoto. To so predlogi, ne dodatne že izvedene funkcije tega kroga.
