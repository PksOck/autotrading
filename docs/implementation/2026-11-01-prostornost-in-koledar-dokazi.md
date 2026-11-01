# Prostornost, dnevna ocena in koledar — dokazi S-027

## Obseg

Osnova 751fe9d, veja feat/uxui-demo-upgrade. Root je izvedel kodo; OpenCode ni bil uporabljen. Neodvisni agent je opravil samo bralni pregled. [SPEC](../superpowers/specs/2026-11-01-prostornost-in-dividendni-koledar-spec.md), [plan](../superpowers/plans/2026-11-01-prostornost-in-dividendni-koledar.md), [ADR-0026](../adr/ADR-0026-denarne-ocene-in-koledar.md).

## Izvedeno

- BL-229: široke tabelarične strani Analize/Portfelj/Uspešnost, različne privzete širine analiz brez ponastavitve shranjenih preferenc. Na velikem zaslonu ni več splošne omejitve 1440 px. Ožje strani ohranijo bralno širino, majhni zasloni varno drsenje tabel.
- BL-229: Predlogi imajo URL filtre Vsi/Še za izvedbo/Čakalna vrsta/Obdelava/Izvedeni/Pozornost/Neuspešni in iskanje po simbolu ali hipotezi. Filtriranje in validacija pred omejitvijo 200; neveljaven done ni uspeh. Filter opisuje fazo predloga, ne vsake povezane globoke analize. Brez ponovitve ali modela ob filtriranju.
- BL-229: zaloga idej privzeto zaprta, število ostane vidno; native tipkovnica/dotik. Vrstična opozorila so ohranjena ob odprtju, aktivna skupina ostane odprta.
- BL-229: datum in povezava portfelja v isti nogi; manj prazne višine. Dnevni premik je ocena uvoženih pozicij, ločeno po izvorni valuti, kadar cilja FX ni mogoče dokazati. Ne predstavlja spremembe celotnega računa. Neznane skupine ostanejo vidne.
- BL-229: vseh pet stanj aktivne teze z ničlami, razlaga njihovega pomena in jasnejše dejanje spremembe stanja. Pending sprejemi/osnutki/dokazi niso skriti ali avtomatsko potrjeni. To ni izvedba celotnega BL-226/227.
- BL-230: 12 mesecev, leto/valuta, prejeto bruto/neto in odprti obračuni; izbrani mesec odpre datume, instrumente, zneske, račun in vir. Letni zneski ostanejo po valuti. Nerazporejeni datumi in potrebne uskladitve so izrecni; annual/12 in ex-date kot datum plačila nista dovoljena. Obstoječa ocena trenutnih pozicij ostane ločena.

## Regresije in popravki pregleda

- Širina RED: 1920/2560 px sta prej dala main 1440 px; GREEN po odstranitvi omejitve samo na označenih straneh. Standardna tabela analiz brez vodoravnega drsenja pri obeh širinah. Uporabnikove namerno široke shranjene nastavitve se ne brišejo.
- API RED: starejši predlog za filtrom je bil skrit za 205 novejšimi; GREEN filter/validacija pred končnim LIMIT. Neveljavni done je v Pozornosti.
- Decimal domeni: nepopolne cene/FX, kratke pozicije, mešani datumi, NaN/Infinity, ničla in negativni izid; dividende po valuti/mesecu/letu, davčna vrzel, korekcije, neznan datum/znesek in deduplikacija akcije po conid oziroma simbolu. Dokaz gotovine izven izbranega razpona prepreči dvojni odprti prihodek, brez razširitve vsote prejete gotovine.
- Neodvisni pregled je odkril nepreverjen cilj FX: odpravljeno z izrecnim pogojem in izvorno-valutnim prikazom. DB integracija potrdi, da uvoženi fxRateToBase ne postane domnevni EUR izid in da neskladna valuta kotacije onemogoči celo skupino. Branje ne sproži ponudnika.
- Pregled je odkril skrite mesečne zneske za bralnik zaslona: dodan unikaten aria-describedby z oznakami bruto prejeto/odprto ter številom zapisov. RED/GREEN test dostopnega opisa.
- Vizualni pregled telefona je odkril podedovani coarse-pointer inline-flex na karticah Novo/Spremljam. Notranji blok ohrani vrstice in 48-px zunanjo tarčo. Browser RED vrednost y601 namesto vsaj625, nato GREEN na telefonu in namizju. Treemap ni spremenjen: ustaljena geometrija ostane v kartici; prehodni Motion posnetek ni bil dokaz trajnega preliva.
- Stari E2E selectorji stanja so omejeni na aktivno različico, da novi števci ne morejo zadostiti preverjanju dejanske trditve. Test opozorila zaloge jo najprej izrecno odpre. Potrditveni koraki in števci mutacij so ohranjeni. Neodvisni ponovni pregled PASS za oba podatkovna popravka in končno postavitev/teste.

## Preverjanje

- API: **618 passed, 1 skipped**, 19 obstoječih opozoril (Starlette/httpx in SQLAlchemy array comparator); Redis integracija pogojno preskočena. Sintetična namenska DB preza-ux-nov01-test, identiteta 2bb9973…; po testih odstranjena. Noben test ne uporablja žive ali demo baze za ponastavitev.
- Ruff: lint in format vseh 229 datotek čista. Mypy strict: 137 datotek brez napak.
- Splet: **199 passed / 49 datotek**; TypeScript/ESLint/i18n 1436 ključev čisti. Generirani OpenAPI in openapi-typescript pri ponovni generaciji identična; schema.d.ts ni ročno urejen ali preoblikovan.
- Ciljni brskalnik po zadnjih popravkih: **20/20** (SL/EN, namizje/telefon, filtri, zaloga, koledar, stanja, explicit acceptance in responsive geometrija).
- Celotni končni brskalnik: **100 passed / 12 namernih device-specific skipov**, 112 primerov; SL/EN, namizje/telefon, brez napak. Prva regresija je razkrila štiri zastarele selectorje za stanja/zalogo; zgoraj opisani popravki so ohranili dejanska varovala in zadnji celotni zagon je zelen.
- Linux Docker build API in splet uspešen. Vizualni posnetki obeh jezikov/naprav v lokalni mapi s027-refinement; pregledani namizni koledar ter namizni/telefonski Pregled. Fotografije so vzorčni podatki, ne dokaz resničnega prihodnjega dohodka.

## Demo in omejitve

Posodobljena samo preza-demo-api/web na :3100. Shema ostane0020, brez nove migracije ali reseeda. Spletna slika 4b1ce641597371c594868f42869f5d1414b780ddbf72a3bd0a3e15f8b25cc305; API ace679551f6bac96b7c48970aac28ead38dbf3ef689a4dbab5547a0e53fd75e7. Obstoječi celotni E2E vsebujejo sintetični CRUD predlogov/watchliste v demo okolju; to ni obljuba byte-identične demo baze. Kontrola pred zagonom: 18 predlogov/5 analiz/3 teze, po obeh celotnih zagonih: 20/5/3. Shema je pred in po0020; uporabniški zapisi niso reseedani ali množično izbrisani.

:3000 preverjeno ohranjen: web 4eaf458ee0525197f3800d28ed6d758aaffa70ec23d6bfcf7ddaaff67e06f7c9, API 973f535ba8840631e0442f59c346c6b3469a17646f5b338703b50fdc9349e194. Brez push/merge, živega uvoza, pošiljanja e-pošte, aplikacijskih modelnih klicev ali broker naročil.

Za popoln prihodnji koledar potrebujemo vir objavljenih datumov in razširjeni Flex dokaz (BL-202). Za skupni dnevni premik tujih pozicij v EUR je treba ohraniti in preveriti ciljno valuto FX; prejšnja vrednost portfelja ima še obstoječo predpostavko FX. Študija ni NAV performance.

[Laboratorij SPEC](../superpowers/specs/2026-11-01-laboratorij-financnih-kazalnikov-spec.md) je **predlog**: najprej zgodovina kazalnikov, nato pravila nakupa/prodaje. Nima še poti /lab, migracije ali izvajalnika. BL-231 ostaja next; BL-225/226/227, backup in pogoji Flex/SMTP niso s tem zaključeni. Dodatni predlogi za Predloge so zapisani v istem dokumentu, brez trditve, da so že izvedeni.
