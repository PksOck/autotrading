# S-B · Flex, dividende in valutna osnova

**Status: NEXT-SPEC / CONDITIONAL PROPOSAL.** Datum 2026-10-30. BL-214; izvedbeni nalogi BL-202/205. Manjkajoči dejanski očiščeni XML in razlaga njegovih korekcij preprečujeta odvisno izvedbo in zaključek B. Dokument ne potrjuje živih finančnih podatkov.

Podlage: [neposredni dodatni krog §8](./2026-10-30-dodatni-krog-claude-spec.md), [priprava SPEC](./2026-10-30-odprti-sklopi-priprava-spec.md), [glavni načrt B](../plans/2026-10-30-zakljucevanje-odprtih-sklopov.md). Statični ogled kode na delovni osnovi `d0ceebf4cb28cb8919d23e00f2c419fa9c41d802`; sočasne spremembe pred izvedbo ponovno primerjaj. Testi v tem dokumentarnem koraku niso zagnani.

## 1. Rezultat in meje

Po uvozu uporabnik loči knjiženi prejemek, odprto upravičenje, spremembo upravičenja in oceno. Odsotna sekcija ne izbriše zadnjega veljavnega posnetka; neznana valuta ne postane USD; tečaj računa z bazo USD ne vrednoti portfelja v EUR. Številke računa deterministična koda z Decimal; JSON denar/tečaj sta decimalna niza, datumi poročila niso trenutek prenosa.

Zavezujoče so omejitve iz AGENTS/ADR in neposrednega SPEC: brez ugibanja pomena `Re`, brez tihega netiranja, brez privzete ciljne valute ali zgodovinskega FX backfilla. Spodnje dopolnitve sheme so predlog za pregled, ne že izvedena migracija. Noben modelni klic ali ponudnik ni potreben za lokalne teste.

## 2. Dejanska izhodišča

- `broker/flex.py:parse_statement` sklepa `cash_complete` iz prisotnosti CashReport in preskoči BASE_SUMMARY. Zato prisotna sekcija brez izvirnovalutnih vrstic še ni dokaz prazne gotovine (B5).
- `domain/portfolio.py:PositionIn`/`models.py:Position` hranita `fx_rate_to_base`, brez eksplicitne ciljne valute; `services/portfolio.py:_value_in_base` uporabi stopnjo tudi za drugo zahtevano bazo (F1).
- `domain/dividends.py:CashEvent` že ima `base_currency`/`fx_basis`; teh polj ne uvajaj znova. `Accrual`, `ImportCoverage`, `DividendAccrualSnapshot` in `DividendCashEvent` ostanejo ločeni modeli. Trenutni simbol sam ni dokaz poslovne identitete.
- D1 coverage popravlja neposredni krog; S-B zahteva njegov novi dokaz in regresijo, brez ponovnega izvajanja iste spremembe. D2 ostane verjetna ugotovitev do reprodukcije; D3 zahteva pregled dejanskega besedila.

## 3. Zahteve in vhodna pogodba

| ID | Pogodba / izvor resnice | Prevzem |
|---|---|---|
| SB-01 / BL-202 | Minimalni dejanski očiščeni Flex XML: CashTransactions, OpenDividendAccruals, ChangeInDividendAccruals s primerom `Re`, OpenPositions, CashReport, AccountInformation in FinancialInstrumentInformation v dejansko uporabljeni obliki. Manifest vsebuje SHA256 očiščenega XML, različico query/izvoza, sekcije, obdobje, datum generiranja/pridobitve in opis anonimizacije. | F-B01 |
| SB-02 / BL-205, B5 | Za vsak račun/sekcijo loči odsotno, prisotno nepopolno, prisotno popolno in izrecno prazno popolno sekcijo. BASE_SUMMARY-only je nepodprt/nepopoln izvirnovalutni snapshot. Lot-only, manjkajoča valuta/količina ali konflikt računa ne postanejo popoln snapshot. | F-B02/03 |
| SB-03 / BL-202, D2 | Vzorec z `Re` dobi dokumentirano izvorno razlago: kateremu dogodku pripada, ali spreminja upravičenje, ga prekliče ali poravna ter katera cash knjižba dokazuje plačilo. Prevod kode `Re` v učinek je dovoljen šele po tem dokazu. | F-B04 |
| SB-04 / BL-202 | Idempotenca cash uporablja `(broker, account_id, transaction_id)`; accrual snapshot `(account_id, natural_key, as_of)` in deterministično različico vsebine. Isti ključ/druga poslovna vsebina vrne konflikt ter rollback celotnega importa. Ponovni izvoz iste knjižbe z novim časom prenosa ni konflikt. | F-B05 |
| SB-05 / BL-202 | Povezava davka/prejemka/upravičenja potrebuje račun, potrjeno identiteto kotacije in izrecni corporate-action/reference ID. Enak simbol/datum nista zadostna. Več davkov ali delno plačilo ostanejo sledljivi; odsotnost davka ni dokaz davka 0. | F-B06 |
| SB-06 / BL-205, F1 | Vsaka uporabljena FX stopnja ima izvorno valuto, ciljno valuto, račun, datum/osnovo, source/as_of. Uporabi jo samo za isti par in veljavno osnovo; različne baze računov se ne seštejejo v en prikrit total. | F-B07/08 |
| SB-07 / BL-202, D3 | `complete` lahko potrdi pokritost zgolj navedenega obdobja/sekcije; `partial` prikaže vrzeli in obdobje; `missing` ne pomeni ničelnih prejemkov. Besedilo »izpis do« samo po sebi ni dokaz, da UI napačno zatrjuje popolnost. | F-B09 |
| SB-08 / BL-202 | Projekcija vsebuje potrjeno DPS osnovo/valuto/obdobje/source/as_of, količino in datum pozicije; brez osnove ostane null z razlogom. Osebnih prejemkov ne deli s trenutno količino; stari knjižbeni FX ni današnja projekcijska stopnja. | F-B10 |
| SB-09 / BL-202 | FinancialInstrumentInformation poveži s potrjenimi identifikatorji po [S-C](./2026-10-30-identiteta-kotacij-spec.md); konflikt identitete zavrne import. Ne popravljaj zgodovinskih denarnih vrednosti zaradi novega imena/valute kotacije. | F-B03/11 |

**SB-01 blokada:** fizična imena atributov v AccountInformation in pomen različic `Re` še niso potrjeni z dejanskim vzorcem. Imen logičnih polj v tem dokumentu ni dovoljeno razglasiti za preverjene XML poti. Pred implementacijo napiši preslikovalno tabelo `XML pot/atribut → logično polje → tip/enota → dokaz/fixture`; priloži uradno razlago uporabljenega formata brez širjenja dostopa do zasebnih podatkov.

## 4. Shema in migracija F1

Predlagana najmanjša dopolnitev (SB-10):

| Mesto | Dodatek / invariant |
|---|---|
| AccountSnapshotIn / AccountSnapshot | `account_base_currency: str | None`; zgodovinska osnova računa za ta report_date, ne trenutna globalna nastavitev. Provenienca: source, as_of, uvozni fingerprint; po potrebi ločena metapodatkovna tabela, če obstoječa shema ne nosi celotne sledi. |
| PositionIn / Position | `fx_base_currency: str | None`, obstoječa `currency` je izvorna; `fx_as_of`, `fx_basis`, `fx_source` so eksplicitna provenienca oziroma nedvoumna vez na isti posnetek. `fx_rate_to_base` ostane Numeric/Decimal. Stopnja mora biti pozitivna in končna. |
| CashEvent in dividendni payload | Že obstoječa `base_currency` ostane cilj knjižbenega FX. Pri manjkajočem/konfliktnem cilju je FX neuporaben; ne dopolni ga iz settings. Različne cilje prikaži ločeno. |
| API read modeli | Za zahtevano bazo vrni `total_value=null`/`missing_fx`, če za katerikoli sestavni del manjka veljaven par; ohrani izvorne zneske in per-account/per-currency metapodatke. Delni seštevek se ne imenuje celotni portfelj. |

Migracija dobi naslednji prosti ID **po dejanskem head**, po trenutno pripravljenih 0016–0020; tukaj ne rezerviramo 0021. Dodaj nullable polja brez privzetih valut. Najprej suhi audit/backfill na kopiji: samo dokazljiv isti račun/report/payload lahko napolni cilj; vsak zapis dobi dokaz ali razlog `unknown_base_currency`. Ohrani število starih neznanih vrstic, pred/po hash in število spremenjenih vrstic; nedokazane ostanejo null. Brez ponovnega omrežnega pridobivanja ali množičnega uvoza zaradi backfilla.

Upgrade/downgrade na testni kopiji preverita vrednosti in število vrstic, ne le Alembic head. Downgrade ne obnovi izgubljene sledi sam od sebe; dump/restore iz [S-F5](./2026-10-30-varnostne-kopije-restore-spec.md) je obvezen pred prvo živo migracijo, tudi 0016–0020. Posodobljena OpenAPI/TS sta generirana, ne ročno urejena.

## 5. Prehodi, atomarnost in omejeno delo

Uvoz: `received → parsed → validated → committed`; napaka `→ rejected` z varno kodo in nič trajnih sprememb katerekoli sekcije istega importa. Celoten XML preveri pred zapisom; shranjevanje pozicij/gotovine/dividend/coverage je ena transakcija. Istočasna importa enakih ključev se serializirata ali zaključita s konfliktom; ni delnega uspeha zaradi vrstnega reda.

Coverage ni ena globalna lestvica: stanje velja za račun/sekcijo/obdobje/različico. Manjkajoča sekcija ne degradira prej dokazane. Novejša izrecno prazna popolna sekcija sme veljavno izprazniti odprte obračune. D1 določa monotono varovanje statusa/različice in ohranitev obstoječih konfliktov cash/accrual identitet. **SB-12 je dodatni prihodnji predlog:** za coverage z isto časovno oznako/različico in različno prisotno vsebino zahtevaj stabilen fingerprint ter izrecen konflikt, ne »zadnji writer zmaga«. To ni trditev o sedanjem vedenju D1; pred izvedbo SB-12 je potreben pregled coverage identitete/migracijskega vpliva in fixture za tak konflikt.

Upravičenje/preklic/poravnava/cash so ločena dejstva, ne splošni avtomat `Re → paid`. Do potrditve SB-03 nepodprti popravek zadrži odvisno uskladitev kot unknown z razlogom; iz njega ne ustvari ne pričakovanega bruto ne prejemka. Odsotna nova knjižba ni preklic.

Predlagani tehnični limit SB-11: največ 20 MiB XML in 100.000 poslovnih vrstic na import; presežek zavrni pred pisanjem, brez tihega rezanja. Izvajalec potrdi limit na anonimiziranem vzorcu in določi 60-s lokalni rok validacije; večji resnični izvoz zahteva pregled limita, ne izgubo vrstic. GET prikazuje bazo, ne pridobiva Flex.

## 6. Fixture in vrata

| Fixture | Given / When / Then |
|---|---|
| F-B01 dejanski anonimizirani export + manifest | Znana query različica → parser → evidentirane vse podprte/odsotne sekcije in preslikave; sintetični fixture ni dokaz žive semantike. |
| F-B02 BASE_SUMMARY-only, missing, explicit-empty | Prej veljavna gotovina → vsak izvoz → prvi dve obliki je ne izpraznita; samo dokazano popoln prazni snapshot jo sme. |
| F-B03 lot-only, missing-currency, bad-account/ID | Uvoz delno uporabnih vrstic → zavrnitev → stare pozicije/gotovina/dividende nespremenjene, brez privzete USD. |
| F-B04 dejanski `Re` + povezani izvorni dogodek | Reprodukcija D2 pred popravkom; po potrjeni razlagi pravilen pričakovani znesek/preklic, brez izmišljenega cash. Trenutno BLOKIRANO. |
| F-B05 ponovitev, conflict, sočasnost | Isti import dvakrat → iste vsote/število; isti ID/druga vsebina → konflikt in celoten rollback. |
| F-B06 delno plačilo, dva davka, nepovezan odtegljaj, prodana pozicija | Samo izrecno povezane knjižbe vplivajo na uskladitev; neznani neto ostane null. |
| F-B07 račun A baza USD, B baza EUR | Zahteva EUR → USD-account FX se ne uporabi kot EUR; unknown total/missing_fx ter vidna izvorna zneska. |
| F-B08 stari zapisi brez cilja + dokazljiv podnabor | Backfill → spremeni samo dokazljive, drugje null; isti backfill dvakrat nima novih sprememb. |
| F-B09 complete/partial/missing, vrzeli | SL/EN/telefon → le complete potrdi obdobje, partial pokaže vrzeli, missing ne pokaže 0. |
| F-B10 brez DPS, spremenjena pozicija, star FX | Projekcija → datum/osnova/vrzel so vidni, ni izmišljene mesečne ocene. |
| F-B11 dvojni simbol/ISIN na dveh kotacijah | Import → ne zamenja instrument_id ali zgodovine. |
| F-B12 predlog SB-12, ista coverage različica/druga prisotna vsebina | Po odobritvi dopolnitve coverage pogodbe → konflikt z nespremenjenim prejšnjim dokazom; ta novi fixture ne dokazuje vedenja neposrednega D1. |

Vrata: ciljni pytest za `test_flex*`, `test_dividend*`, `test_portfolio*` in dodane regresije na izoliranem Postgres; ruff/format/mypy, OpenAPI/TS diff, Vitest za dividendni pogled, nato relevantni Playwright samo `BASE_URL=http://localhost:3100`. Imena novih testnih datotek določi izvedbeni plan; tabela določa obvezne trditve. Zabeleži ukaze, SHA, DB alias, izide in nepričakovane skipe. Noben živi uvoz v tej pripravi.

**Vrata pripravljenosti:** SB-01/03 (dejanski vir in semantika), potrjena preslikava FX, pregled migracije/backfilla in obnovljivost. Dokler katero manjka, BL-202/205 in paket B ostanejo odprti; neodvisne sintetične regresije se lahko pripravijo brez trditve o živem zaključku.
