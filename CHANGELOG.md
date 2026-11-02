# Dnevnik sprememb

Različice sledijo obliki `MAJOR.MINOR.PATCH`. `VERSION` je izhodišče; CI preveri enakost različic v paketih, Python lockfile in API runtime. Oznake `vX.Y.Z` so nespremenljive in kažejo na konkretni commit. Predizdaje so na GitHubu izrecno označene.

## Neizdano

Naslednje spremembe se dodajajo sem, nato se ob novi izdaji razvrstijo v Dodano/Popravljeno/Spremenjeno.

## [0.2.0] — 2026-11-02

Razvojna predizdaja za uporabniško testiranje; prva GitHub izdaja tega razvojnega kroga. Prejšnja številka paketov0.1.0 ni imela ločene GitHub izdaje.

### Dodano

- Lastniška prijava brez registracije, zaščita neposrednega API-ja, odjava med zavihki in potek seje. Lokalna konfiguracija sprejme scrypt ter bcrypt2a/2b/2y; gesla se ne shranjujejo v repozitorij.
- Zasebna Docker namestitev na ločenem loopback portu, HTTPS prek Tailscale Serve in javne informativne strani O aplikaciji/Zasebnost/Pogoji/Varnost.
- Številčni YTD iz koherentnih nespremenljivih zajemov IBKR TRADES; ločeno označen sintetični demo, čas/vir/ID zajema in previdna obravnava podatkovnih vrzeli.
- Globalni in modulski vklop avtomatike, urniki, izrecen nadzor avtomatskih modelnih analiz ter zaščita neshranjenih nastavitev.
- Nastavljivi stolpci in profili portfelja/watchliste, podpisane spremembe, datumski mini grafi, zložljiva zaloga idej, filtri analiz in predlogov.
- Dividendni koledar, read-only študija shranjenih signalov/mnenj ter jasnejši prikaz tez in pomoči.
- Vidna različica v nogi aplikacije, health različica in avtomatsko preverjanje skladnosti različic.

### Popravljeno

- Neveljavni izhodi predlogov imajo razumljivo stanje; poslovne napake se ne prikazujejo kot uspešna analiza.
- Kompaktne vrstice, širine tabel na velikih zaslonih, dostopna dokazila in razčlenitev zastarelosti cene/kazalnikov.
- CSRF preverjanje izvora, omejitve prijav in teles, varne seje/SSE, skrit prikaz z ohranjenimi osnutki ter čiščenje občutljivih dnevnikov/build kontekstov.

### Podatki in nadgradnja

- API samodejno izvede aditivni migraciji0021 (zgodovina YTD) in0022 (lastniške seje). Pred uporabo dejanske baze naredi preverjeno varnostno kopijo.
- Produkcija brez ustreznih lastniških poverilnic in HTTPS izvora ostane zaklenjena. Dejanske vrednosti sodijo v ignorirano `.env` oziroma `infra/secrets/`, ne v `.env.example`.
- Demo3100 je ločen; `seed_demo` je destruktiven in ni produkcijski postopek. `seed_ytd_demo` je aditiven, opt-in in zavrne zasebni portfelj.

### Odprto in omejitve

- YTD je cenovni premik trenutnih količin, ne NAV donos računa; tuje valute niso seštete brez preverjenega FX dokaza. Živi zgodovinski vir zahteva pravice IBKR in kvalificiran instrument.
- Polno osebno spremljanje idej, razširjene teze/merila in laboratorij zgodovinskih kazalnikov ostajajo v BACKLOG.
- Razširjeni dejanski Flex, produktno varnostno kopiranje/obnova in dejanska dostava SMTP potrebujejo ločena dokazila.
- Ni samodejnih naročil. GitHub izdaja ne spremeni že zagnane namestitve; ozka pravila Tailscale so ločena uporabnikova odločitev.

[0.2.0]: https://github.com/PksOck/autotrading/releases/tag/v0.2.0
