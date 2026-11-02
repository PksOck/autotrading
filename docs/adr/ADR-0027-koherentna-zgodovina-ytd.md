# ADR-0027: YTD iz enega nespremenljivega zajema cen

**Status:** sprejeto · **Datum:** 2026-11-02 · **Seja:** S-029

Inkrementalna tabela Bar ni dokaz prilagoditve stare cene po splitu. Zato oba konca letne primerjave izhajata iz istega zaključenega odgovora zgodovine. IBKR TRADES je po [uradni pogodbi](https://www.interactivebrokers.com/docs/tws-api/doc/md/historical-bars) prilagojen splitom, ne dividendam. Zahtevamo znani pozitivni con_id, kvalifikacijo pogodbe, skladno valuto in identiteto stock/ETF. Yahoo/Stooq brez te izrecne zmožnosti nista nadomestni dokaz.

Tabela price_history_capture hrani kanonične Decimal zaključke, identiteto, vir/osnovo, oba datuma, leto, čas pridobitve in prstni odtis. Zajem ne vključuje današnje nedokončane sveče. Celota se zapiše v transakciji; UPDATE prepreči DB sprožilec. Per-instrument transakcijska ključavnica in primerjava samo z zadnjim zajemom odpravita ponovitve ter ohranita zaporedje A→B→A. BigInt identity določi vrstni red ob enakem času.

GET portfelja bere zadnji ustrezni zajem brez ponudniških klicev. Neznana identiteta, mešana valuta, bodoči čas, nepreverjena osnova in manjkajoča zgodovina ostanejo jasno nedostopni. Ob napaki osveževanja ostane prejšnji dokaz; zgodovina ima svojo osvežitev tudi, če je kratki Bar cache svež. Uporablja obstoječi proces cen in njegove omejitve/kvote.

Izračun je cenovni premik trenutnih uvoženih količin od zaključka pred novim letom, ne zgodovinski NAV donos računa. Gotovina, spremembe količin, dividende in gibanje FX niso vključeni. Tuje valute ostajajo ločene do dokaza ciljne valute FX. Sintetični demo ima svojo osnovo in je dovoljen samo izrecno za demo pozicije; opt-in CLI ne prepiše obstoječega portfelja.
