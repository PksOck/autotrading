# Avtomatika in portfelj — zaključni dokazi S-028

Osnova4842514, veja feat/uxui-demo-upgrade, delo2026-11-01–02. Root je izvedel vse spremembe. Read-only SOL in nato na izrecno uporabnikovo zahtevo Astra sta pregledala kodo. OpenCode ni bil uporabljen.

## Izvedeno

- BL-232: Procesi in urniki so takoj za videzom. Vidno stikalo Vsa avtomatika ohrani urnike in izbiro modulov; ločeno stikalo ureja samodejne modelne analize. Skupine Podatki/Analize in spremljanje/Obvestila pokažejo vse module s hitrimi revizioniranimi stikali. Razdelek pojasni, da izklop modula prepreči tudi njegov ročni zagon; za ohranitev ročnih zagonov obstaja urnik Samo ročno.
- Urejevalnik razkrije potrebna polja, napredne omejitve in ročni zagon ločeno. Osnutka ni mogoče izgubiti zaradi hitrega preklopa, konflikta, refetcha ali poznega odgovora prej zaprte instance. Izrecni instance token varuje tudi A→B→A.409 zahteva uspešen izrecni reload, neuspešno branje ne razglasi cache za svežo revizijo. Stikala ne sprožijo /run ali samodejnega paketnega sprejema.
- BL-233: Pozicije/Watchlista imajo fiksno kompaktne vrstice, navpično sredinsko vsebino in ohranjene stolpce/širine/profile. Številke ostanejo desno. Gumbi Watchliste32px na namizju/48px na dotik. Črta, dejanski razpon in število sej so skupaj. Izrecno odprt vir/čas poveča samo svojo vrstico, zato zadnja vrstica ne potrebuje notranjega navpičnega drsenja.
- Ob vrednosti portfelja je Dan/YTD, znesek in odstotek. Dnevni podatki uporabljajo ADR-0026 in izvorne valute, kadar cilj FX ni preverjen. YTD je strogo cenovna ocena trenutnih količin, brez gotovine/poslov/dividend, ne dejanski NAV donos računa.

## Omejitve, ki ostajajo izrecne

Številčni produkcijski YTD **še ni omogočen**: Bar ne hrani dokazila, da sta začetna in zadnja cena primerljivo prilagojeni ob splitih. Isti ponudnik tega ne dokazuje. Novi basis_verified je privzeto false; manjkajoč datum ali dokaz ne postaneta0 ali delni donos. Sintetična preverjena osnova potrdi matematiko, ne žive pokritosti. BL-234 določa naslednjo podatkovno nadgradnjo. Tudi skupni EUR dnevni premik tujih pozicij še potrebuje dokaz ciljne valute FX; prejšnji skupni vrednosti ne pripišemo novega jamstva.

## Pregled in regresije

SOL je odkril asinkrono izgubo osnutka,409 brez blokade, napačno obravnavo neuspešnega refetcha in dnevno besedilo v pomoči YTD. Popravljeno z RED/GREEN testi, vključno z zakasnjenim PATCH/GET in A→B→A. Astra je dodatno našla možno odrezovanje vira pri zadnji vrstici ter nepreverjeno split osnovo. Obe ugotovitvi sta odpravljeni; ponovni pregled brez novih pomembnih produktnih P1/P2.

Browser RED je dejansko ponovil zadnjo odprto vrstico v tabeli; GREEN preveri spodnji rob vsebine glede na vidni scroller. Časovno občutljivi YTD browser test zdaj uporablja izrecen sintetičen GET odgovor; domena/DB ločeno preverita manjkajoči datum, stare/pomešane vire, nepreverjeno osnovo in Decimal izračun preverjenega primera. Dostopni imeni izbirnikov sta izrecni, datumski selector razlikuje razpon od datuma vira. Interna višinska meja105px velja za običajne testne vrstice, ne za rezanje dolgih imen ali opozoril.

## Preverjanje

- API **620 passed /1 pogojni Redis skip**,19 obstoječih opozoril Starlette/SQLAlchemy. Ruff229 in mypy137 čista. Lastna tmpfs sintetična DB3898d35… je po identitetni kontroli odstranjena. Noben reset žive/demo baze.
- Web **213 passed /51 datotek**; TypeScript/ESLint/Prettier in i18n1474 čisti. Ponovna generacija OpenAPI/TS identična, generirani tipi niso ročno urejeni.
- Ciljni brskalnik **10/10**: avtomatikaSL/EN na telefonu/namizju, nižje vrstice, datum ob grafu, vir zadnje vrstice brez clippinga, izbor YTD in eksplicitna podatkovna vrzel. Nastavitveni PATCH so prestreženi s sintetičnim API, brez dejanskega spreminjanja demo avtomatike.
- Celotni končni brskalnik **106 passed /12 namernih device-specific skipov**,118 primerov, SL/EN/desktop/phone. Zagon je trajal2,2min, brez napak.
- Linux build API/web uspešen. Vizualno pregledana namizni Portfelj, Watchlista in Procesi; posnetki v lokalni mapi s028-settings-portfolio. Tabela dopušča večjo odprto vrstico za dokazila, brez absolutno skritega vira.

## Demo in predaja

Samo3100: web f16217d3f85359949a28804174e01b9c5433902176e42740f86931555320a9d8; API1ddf667a95b74c2fcfc0d20b039ee43902cde5e75f7f4b3fd6c2148842a2a0d9. Shema ostane0020, brez migracije/reseeda. Celotna obstoječa E2E zbirka ima sintetični CRUD v demu.3000 preverjeno ohrani web4eaf458ee… in API973f535ba…. Brez push/merge, pravih modelnih klicev, pošiljanja e-pošte ali broker naročil.

## Dodatno opažanje za naslednji UX rez

DataQualityBadges združi zastarelo ceno in katerikoli zastareli finančni kazalnik v en napis Zastarelo. To ni nov napačen izračun, vendar pri skritih stolpcih ni jasno, kateri podatek je star. Predlog BL-235: dostopna razčlenitev cene/kazalnikov z njihovim virom/časom, ne odstranjevanje opozorila. Ni vključeno kot prikrito dodatno že izvedeno delo.
