# Preverjanje identitete in prikaz podatkov instrumenta

## Pogodba vira

- Uradna dokumentacija: [Finnhub Company Profile 2](https://finnhub.io/docs/api/company-profile2).
- Preverjena uradna shema ponudnikovega SDK: [CompanyProfile2](https://github.com/Finnhub-Stock-API/finnhub-go/blob/master/model_company_profile2.go), pregled 2026-10-29.
- `ticker` identificira simbol na navedeni borzi; `name` je ime družbe; `exchange` je oznaka borze. `currency` pomeni valuto poročil družbe, zato ni uporabljena za valuto trgovanja. Shema ne vsebuje vrste vrednostnega papirja. Klasifikacija `unknown` ostane ohranjena.
- Borze ne krajšamo in ne pretvarjamo na podlagi ugibanja. Oznaka, daljša od obstoječega polja (20 znakov), ostane vrzel `exchange_label_requires_mapping`.

## Izvedeno

- Izrecni `POST /instruments/{symbol}/identity/enrich` zahteva interni ID in pričakovani čas spremembe. Napačen simbol, več kotacij istega simbola, neujemanje borze ali sočasna sprememba blokirajo dopolnitev. Obstoječih vrednosti ne prepisuje.
- Samo dejanska dopolnitev spremeni izvor/čas identitete. Preverjanje brez spremembe vrne ločen čas preverjanja, ne ponaredi nove svežine shranjenih podatkov.
- `GET` podrobnosti bere shranjene metrike, metapodatke in identiteto brez novih ponudniških klicev. Novi panel prikaže vir, polje, osnovo, čas pridobitve ter manjkajoče/delne/zastarele podatke.
- Živih ponudniških klicev, množičnega osveževanja ali naročil med izvedbo ni bilo. Preverjanje povezave uporablja sintetične odgovore; veljaven API ključ in pravice dostopa se preverijo šele ob uporabnikovem dejanju.
- Ročno popravljanje vrste/valute ni vključeno; ohranitev `unknown` je namerna omejitev dokaza, ne avtomatska klasifikacija.

## Dokazi

- RED: novi API testi so pred izvedbo padli zaradi manjkajoče pogodbe/modula.
- API: namenski `codex_identity_test` v izoliranem testnem PostgreSQL; preverjeni pravilni simbol, neskladni simbol, dvoumne kotacije, optimistic conflict, ohranitev neznane valute/vrste, manjkajoča povezava, dolga borzna oznaka in varne ponudniške napake.
- UI: trije testi preverjajo dejanske metrike/vir/opozorila, izrecno dejanje z ID/verzijo in napako brez lažnega praznega stanja.
- Format/lint in mypy za spremenjene Python datoteke; ESLint za nove spletne datoteke ter TypeScript preverjanje celotnega spletnega projekta.
- Celotni regresijski testi in brskalniški prevzem so naloga integratorja.
