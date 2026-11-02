# Enostavni Procesi in urniki

Datum: 2026-11-01. Osnova4842514. BL-232. Uporabnik želi preglednost in hiter vklop/izklop avtomatike oziroma posameznega modula. Izvedbene podrobnosti je v tem pogovoru prepustil rootu.

## Odločitev

Uporabimo obstoječi API, revizije in delavčeva varovala. Razdelek postavimo takoj za Videz in jezik. Na vrhu je vedno vidno stikalo vseh samodejnih začetkov, ločeno stikalo samodejnih modelnih analiz ter kratko jasno stanje. Pavza ohrani urnike/modulske izbire, tekočega dela ne prekine, izrecni ročni zagoni ostanejo mogoči. Vklop samo odstrani pavzo, ne omogoči prej izklopljenih procesov in ne odda opravila.

Namesto dropdown izbire pokažemo vse module, razvrščene v Podatke / Analize in spremljanje / Obvestila. Vrstica vsebuje ime, shranjeni urnik, stanje dovoljenja in takojšnje stikalo Omogoči modul. To uporablja obstoječi enabled: izklop prepreči tudi ročni zagon tega procesa. Samo ročno je ločena izbira urnika. Stanje ni dokaz, da delavec ravno teče ali da so povezave pripravljene.

Gumb ob vrstici odpre en urejevalnik. Osnovno pokaže omogočenost in tip urnika s potrebnim časom/intervalom; časovni pas, dnevi in okno so pod Dodatne omejitve. Ročni zagon je ločeno razkritje. Skriti podatki ostanejo ohranjeni in se pri preklopu ne ponastavijo. Naslednji termini so informativni po shranjenem urniku, ne obljuba izvedbe med globalno pavzo.

## Obravnavani pristopi

Samo premik starega gumba je najmanjši poseg, vendar ne pokaže modulov. Masovni prepis vseh enabled bi omogočil en klik, vendar bi uničil uporabnikov prejšnji izbor in povečal možnost delnega shranjevanja. Izbran je obstoječi globalni paused + posamezne revizionirane politike in postopno razkritje. Gre za rootovo izvedbeno odločitev, ne nov uporabnikov izbor.

## Pogodba sprememb

- Hiter preklop pošlje nespremenjeni policyBody s trenutno revizijo in samo obrnjenim enabled. Ni optimistične trditve o uspehu; potrjeno stanje pride iz odgovora oziroma osveženega API.
- Med zapisom blokiramo ponovni klik. Napaka ostane pri modulu. Konflikt zahteva osvežitev in nov uporabnikov klik; brez samodejne ponovitve stare spremembe.
- Urejevalnik hrani svoj posnetek. Refetch po globalnem preklopu ali drugem modulu ne izbriše osnutka. Ko je osnutek umazan, sta preklop istega modula in menjava urejevalnika onemogočena z razlago; Shrani/Zavrzi sta dosegljiva.
- Pavza/LLM stikalo ohranita drugo polje in revizijo. Pomanjkljiv/nedosegljiv control ne pomeni vklopa. Vidne napake/ponovno nalaganje, slovenski in angleški teksti, tipkovnica in48px dotik.
- Brez novega API, migracije, izvajanja procesov, pravih modelnih klicev ali pošiljanja sporočil ob prikazu/preklopu nastavitev. Samo demo3100;3000 ostane nespremenjen.

## Dokaz

Komponentni testi za glavno pavzo/LLM neodvisnost, ohranitev urnika/revizije, napake in konflikt, dvojni klik, umazan osnutek in refetch. Brskalnik SL/EN in telefon: hitro stikalo je brez odpiranja podrobnosti, urejanje urnika ohrani skrita polja, shranjevanje ne kliče /run. Dejanske spremembe kontrol v testih se prestrežejo s sintetičnim API; demo podatkov ne preklapljamo samodejno.
