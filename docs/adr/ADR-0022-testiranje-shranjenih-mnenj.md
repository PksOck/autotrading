# ADR-0022: Ponovljivo testiranje shranjenih signalov in končnih mnenj

**Status:** sprejeto v pregledni veji · **Datum:** 2026-10-29 · **Seja:** S-018

## Kontekst

Uporabnik je za prvi korak potrdil testiranje shranjenih signalov in mnenj brez novih plačljivih analiz. Shranjena mnenja niso navodila za dejansko izvrševanje poslov, trenutno stanje signala pa ni zgodovinska odločitev.

## Odločitev

- Ločena read-only študija dogodkov za signale in zaključena končna mnenja, z UTC datumskim filtrom razpoložljivosti, virom, močjo/stanjem signalov, stroški in horizontom 1/5/20/60 shranjenih sej.
- Razpoložljivost je `Signal.created_at` oziroma `AnalysisRun.finished_at`. Prvi vstopni zaključek je strogo po tem UTC dnevu; izstop je izbrano število shranjenih sej pozneje. Tekoči UTC dan je konservativno izključen.
- Buy/Overweight pomenita dolgo smer, Sell/Underweight kratko; Hold/neznano je preskok. Rezultati so deterministični Decimal; strošek na obeh straneh velja glede na dejansko vstopno/izstopno vrednost. API denarne vrednosti vrne kot decimalne nize.
- Opažanja se ne seštevajo v sestavljeni donos portfelja. UI kaže povprečje, delež pozitivnih izidov, vsako uporabljeno ceno/datum/vir/valuto in razloge preskokov. Nevtralne smeri, nepopolna zgodovina in neveljavne cene ostanejo vidne.
- Največ 1000 izbranih zapisov; celotno število zadetkov in omejitev sta vidna. Ena SQL poizvedba z lateralnimi indeksi pridobi največ horizont+1 sveč na zapis (največ 61.000), ne celotne zgodovine instrumentov.
- Ni pisanja poslov, sprememb signalov, novih ponudniških ali LLM klicev. Oblika cen, manjkajoče seje, korporativna dejanja, preživelost in izbor vzorca so izrecne omejitve; FX, likvidnost, davki, izposoja in portfeljska izvedba niso simulirani.

## Posledice

To je osnova primerjave zgodovinskih mnenj, ne popoln trgovalni backtester ali ponovitev celotnega zgodovinskega agentskega cevovoda. Ti razširitvi zahtevata ločene pogodbe o point-in-time podatkih, korporativnih dejanjih in stroških izvajanja.
