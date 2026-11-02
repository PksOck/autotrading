# Preverjena zgodovina YTD in predaja glavne veje

Datum2026-11-02, osnova1c4a735. Uporabnik je izrecno izbral podatkovno nadgradnjo YTD pred objavo na GitHub master. BL-234/235 in predaja BL-236. Root implementira, neodvisni pregled ostane bralen.3000 se ne namešča.

## Podatkovna odločitev

IBKR TRADES ima prilagoditev splitov brez dividend ([uradna pogodba](https://www.interactivebrokers.com/docs/tws-api/doc/md/historical-bars), WhatToShow/TRADES). ADJUSTED_LAST vključuje tudi dividende in ne ustreza našemu cenovnemu premiku. Yahoo ne pridobi jamstva samo z imenom ponudnika.

Nov nespremenljiv zajem zgodovine vsebuje instrument/identiteto/valuto, leto, čas pridobitve, vir/verzijo osnove in celoten omejen seznam dnevnih cen iz enega odgovora. Za YTD sta začetni zaključek pred1.januarjem in zadnji že zaključeni dan vedno iz istega zajema. Današnji potencialno nedokončani bar izključimo. Količine so trenutni uvoženi posnetek, ne rekonstrukcija poslov; donos računa/gotovina/dividende ostanejo zunaj obsega. Decimal na meji in pri izračunu, revizije ne prepišejo starega zajema.

Primerni ponudnik ima izrecno pogodbo koherentne split-prilagojene zgodovine; router za YTD ne pade na nepreverjen fallback. Uvoz shrani dokaz samo za razrešen stock/ETF in njegovo valuto/kotacijo. Zadnji primeren zajem se bere v skupni omejeni poizvedbi, brez provider/LLM klica ob prikazu. Zastarelost, manjkajoči začetek, vrzel v identiteti ali neusklajeni zaključni dnevi ne postanejo delna vsota. As_of, datuma in identiteta zajema so dosegljivi v UI. Obnovitev starega zajema ne sme oživiti zastarele osnove.

Osveževanje se vključi v refresh_bars, tudi ko so običajne svečke že sveže; največ en koherenten zajem na instrument/zaključeni dan. Obstoječi procesni gate/kvota in ročni zagon ostanejo. Napaka YTD ne pokvari obstoječih svečk in prejšnjega zajema. Brez dodatnih samodejnih modelnih klicev ali naročil. Nova migracija je aditivna.

## Demo in podatkovne meje

Za demonstracijo številčnega YTD se doda izrecno sintetični zajem samo v preverjeno demo bazo, brez reseeda ali spremembe starih zapisov. Vir je demo, ne IBKR. CLI zahteva demo opt-in ter preveri identiteto/izvor ciljnih instrumentov. Produkcijski zajemi nastanejo samo iz pravega primerno nastavljenega vira; kode/testa ne razglasimo za dokaz uspešnega živega IBKR dostopa.

## Kakovost podatkov

BL-235: opozorilo Zastarelo ostane vidno in ga je mogoče odpreti s tipkovnico/dotikom. Loči ceno od vsakega starega kazalnika, z izvorom in datumom. Delni podatki in nerazrešena identiteta ostanejo. Skriti stolpci ne skrijejo podatkovne vrzeli; razkritje je v običajnem toku.

## Predaja

Preveriti API/agents/web/migracije/generirane tipe ter E2E na ločenem demu. CI web E2E mora imeti dejansko sintetično API/demo bazo, ne le pnpm start brez backenda. Uporabnik je že odobril push na glavno vejo; brez novega dovoljenja ali force push. Pred push fetch, glavno vejo vključimo le varno, preverimo oddaljeni SHA in CI. Lokalni tuji checkout master ostane nedotaknjen. Nobene namestitve3000. Sestaviti konkretna navodila testiranja in jasno ločiti prihodnje BL-225/226/227/231 od te predaje.
