# BL-224: pomoč in hierarhija podatkov

## Izvedeno

Na vseh 15 vrstah strani je ena ikona pomoči ob naslovu: Pregled, Radar, Vstopi, Signali, Predlogi, seznam/podrobnosti analiz, Portfelj, Instrument, seznam/podrobnosti Tez, Uspešnost, Nastavitve, Opcije in razvojni UX. Predogled instrumenta/signala ima kontekstno pomoč tudi na telefonu. Skupni Radix dialog ima tipiziran uredniški ključ, SL/EN, 48-px tarče, fokus in uporabo obstoječe zgodovine Nazaj. Odpiranje ne opravi omrežnega zahtevka ali produktnega dejanja.

Današnji lokalni datum je v nogi menija, na telefonu v Več. SSR ne ugiba časovnega pasu; osveži se ob koledarski polnoči in ponovnem prikazu zavihka. Datum podatka ostane pri podatku ali v njegovih podrobnostih. Produktne SCR oznake in podvojeni uvodi so odstranjeni; oznaka odloženih Opcij ostane.

Pregled nima več štirih praznih visokih makro kartic. Povsem prazen nabor, delni nabor, nalaganje in izpad imajo različna stanja; ob napaki osvežitve ostanejo prejšnji kazalniki vidni z napako. Ikona informacij razkrije vse štiri kazalnike, vir in lokalni čas. Treemap/pulz/lijak ohranijo pomen in kratko legendo, polna razlaga se razširi ob grafu. Demo oznaka, govorica in napake ostanejo vidne. Globalni izidi in testiranje mnenj imajo ločeno poimenovanje in vidno opozorilo o različnih metodah, brez spremembe matematike ali podatkov.

## Dovoljena uporaba OpenCode

Po dodatnem izrecnem dovoljenju uporabnika je zasebna standalone OpenCode seja pripravila samo osnutke navodil v SL/EN, brez orodij ali produktne implementacije. Klic je izbral opencode-go/deepseek-v4.1-flash#max; izhod ima start/text/finish in uspešen stop, dejanska ponudniška stopnja napora ni razkrita. Prvi predhodni odjemalec ni vrnil dogodkov in je bil preklican; to ni dokaz, da ni bilo prenosa. Posredovani so bili izbrani izseki kode in SPEC/plan, brez skrivnosti ali uporabnikovih izpisov. Root je popravil izmišljene tokove Radarja/Predlogov in netočne opise Portfelja/Nastavitev ter sam izvedel vso kodo in preverjanje.

## Preverjanje

- Novi komponentni testi najprej RED zaradi manjkajočih modulov, nato GREEN; dodatni RED/GREEN za jasno metodo globalnih izidov ter ohranitev predpomnjenih kazalnikov ob napaki.
- Končni celotni web **193 passed / 47 datotek**, gnezdena pomoč ciljno 3/3. Prisotno je obstoječe opozorilo o manjkajočem testnem timeZone v PositionsPanel fixture, ne produkcijska napaka. TypeScript, celotni ESLint in i18n 1382 čisti.
- Brskalnik preverja 15 strani × SL/EN × desktop/phone, Escape/Nazaj/fokus/filtre, predogled, ohranjen neoddan predlog in noben zapis ob pomoči. Desktop ima 200-% ekvivalent preureditve s polovično CSS širino, telefon dodatno 320 px. To ni trditev o dejanski povečavi brskalnika na telefonu.
- Diagnostika: prvi CSS-zoom preizkus ni ustrezal browser reflow; drugi Escape je bil poslan pred fokusom odprte pomoči. Popravljeno čakanje v testu, brez produktnega Escape obvoda. Obstoječi test dveh zavihkov je potreboval odzivno pregrado, da oba Check zahtevka prispejo pred potrditvijo; vse kontrole identitete/števila/zamrznjene vsebine/novih polj ostanejo. Šest ciljnih ponovitev (3 na napravo) 6/6; končna celota 90 passed in 10 namernih device-specific skipov (100 primerov).
- Neodvisni povezani pregled T1 PASS, nato PASS ozke testne sinhronizacije. Pregledovalčev pnpm poskus ni izvedel testov in ni spreminjal odvisnosti; testi so rootov dokaz, ne njegovi izmišljeni rezultati.

## Okolje in meje

Linux web build uspešen, samo demo web :3100 osvežen. Demo API ostane c2a6a0055ca57e674c98fbd6b270c0d1562525ffb7212d0c01d85ce1895530d7, brez migracije ali reseeda. Demo web ced94e6af79eef5a8cb8aa56f2bd28d2b7ef618e98e828d2ebff19e095628d0a.

:3000 je pred in po preverjanju nespremenjen: web 4eaf458ee0525197f3800d28ed6d758aaffa70ec23d6bfcf7ddaaff67e06f7c9, API 973f535ba8840631e0442f59c346c6b3469a17646f5b338703b50fdc9349e194. Brez push/merge, živih migracij, pošiljanja e-pošte ali aplikacijskih modelnih klicev. API/agents koda pri BL-224 ni spremenjena in njuni prejšnji rezultati niso nov dokaz.

BL-225–228 ostajajo naslednji rezi plana; pomoč ne pomeni izvedenih lastnih idej, osebne zbirke ali novih meril Tez. Ločeni backup/Flex/SMTP/lastniški pogoji ostanejo odprti.
