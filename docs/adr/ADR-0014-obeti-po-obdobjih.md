# ADR-0014: Obeti po obdobjih in dokazi za in proti na zaslonu analize
**Status:** sprejeto · **Datum:** 2026-10-25 · **Seja:** S-009

## Kontekst
Uporabnik je pri SCR-06 (ASML) rekel, da je analiza zanj preveč zapletena:
- na enem kupu je veliko podatkov;
- oznaka `Underweight` mu ne pove, kaj naj naredi;
- ni videti, kateri podatki podpirajo rast in kateri ji nasprotujejo;
- nima ločenega pogleda za kratki rok, približno eno leto in tri leta ali več;
- v glavi manjkata trenutna cena in število delnic v portfelju;
- 87 korakov analitikov je razpostavljenih po celem zaslonu;
- seznam `/analysis` kaže samo status in oceno.

Želi, da obete po obdobjih pripravi **prikaz in ne agenti**. Pravilo 3 iz AGENTS.md že zahteva, da številke računa deterministična koda.

## Odločitev
1. **Obeti se računajo v API, deterministično, iz posnetka zagona** (`analysis_runs.snapshot`):
   - računa jih čista funkcija `preza/domain/outlook.py`;
   - vhodi so cene (800 dni), temeljni podatki in zgodovina vrednotenja s časom `as_of` analize;
   - rezultat je zato ponovljiv in ostane enak, tudi če se podatki v bazi kasneje spremenijo;
   - LLM ne sodeluje.
2. **Dokaz** je en kazalnik z `key`, obdobjem, smerjo (`pro`, `contra`, `neutral`), vrednostjo, primerjalno vrednostjo, `source` in `as_of`. Besedilo dokaza sestavi spletna aplikacija iz ključa (i18n), ne model.
3. **Obdobja in pravila** (pragovi so konstante v kodi):

   | Obdobje | Dokaz | Za | Proti |
   |---|---|---|---|
   | Kratko (do 3 mesecev) | cena proti SMA50 | nad | pod |
   | | RSI14 | < 30 (preprodano) | > 70 (prekupljeno) |
   | | donos 1 mesec (21 dni) | > +3 % | < −3 % |
   | | nihajnost ATR14/cena | < 1,5 % | > 3,5 % |
   | Srednje (~1 leto) | cena proti SMA200 | nad | pod |
   | | SMA50 proti SMA200 | nad | pod |
   | | zagon 12-1 (252 do 21 dni nazaj) | > +5 % | < −5 % |
   | | vrednotenje proti lastni 5-letni zgodovini | ocena ≥ 0,3 (poceni) | ≤ −0,3 (drago) |
   | Dolgo (3+ let) | ROE, neto marža, rast prihodkov, dolg/kapital (iz `quality_parts`) | delna ocena ≥ 0,5 | delna ocena < 0 |
   | | vrednotenje proti lastni 5-letni zgodovini | ≥ 0,3 | ≤ −0,3 |
   | | letni donos 3 leta (CAGR, 756 dni) | > 7 % | < 0 % |

   Vmesne vrednosti so `neutral`.
4. **Sodba obdobja:**
   - `balance = (za − proti) / vsi dokazi`;
   - `supports` (podpira rast), če je ≥ 0,34;
   - `against` (proti rasti), če je ≤ −0,34;
   - sicer `mixed`;
   - `insufficient`, če ima obdobje manj kot 2 dokaza.

   Manjkajoči dokazi (na primer brez temeljnih podatkov) so našteti v `missing`, da je vrzel vidna.
5. **Ocena agentov v navadnem jeziku:** `Underweight` postane "Zmanjšaj delež" z enovrstično razlago, kaj to pomeni za obstoječo pozicijo in za novo. Angleška oznaka ostane samo v podrobnostih.
6. **Zgornji del zaslona** vsebuje vse za odločitev:
   - instrument;
   - trenutna cena z virom in datumom (zadnji dnevni bar);
   - pozicija v portfelju (količina, vrednost, nerealiziran donos), če obstaja;
   - ocena agentov, prepričanje in okvirna velikost;
   - tri kartice obdobij;
   - kaj bi spremenilo oceno.

   Podrobnosti so spodaj in privzeto zaprte: dokazi za in proti po obdobjih, utemeljitev agentov, kontrolna ocena, koraki analitikov (razvrščeni po analitiku).
7. **Seznam `/analysis`** dobi stolpce:
   - instrument;
   - datum;
   - ocena agentov;
   - tri sodbe obdobij;
   - število dokazov za in proti;
   - prepričanje;
   - pozicija v portfelju.

   Povzetek obetov se računa ob branju iz posnetka. Pri omejitvi 100 zagonov je to nekaj milisekund na zagon.

## Posledice
- `AnalysisOut.outlook` in `AnalysisSummary.outlook_brief` sta nova, oba nullable. Starejši zagoni brez posnetka ju nimajo.
- Brez migracije: obeti se računajo ob branju. Če bo seznam počasen, se povzetek shrani ob koncu zagona (nova naloga).
- Pragovi so poenostavitev, ne napoved. Zaslon to pove v opombi. Vsak dokaz ima vir in čas.

## Zavrnjene možnosti
- **Obete napišejo agenti:** uporabnik je to izrecno zavrnil, poleg tega bi bile številke nepreverljive (pravilo 3).
- **Računanje v brskalniku iz cen:** podvojeni kazalniki v TS in Pythonu (paritetni test že obstaja samo za vstope), temeljni podatki in zgodovina vrednotenja v brskalniku niso na voljo.
- **Ena skupna ocena brez obdobij:** skrije, da je ASML kratkoročno šibek, dolgoročno pa morda zdrav; prav to razliko uporabnik želi videti.
