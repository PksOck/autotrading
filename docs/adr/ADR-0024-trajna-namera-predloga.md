# ADR-0024: Trajna namera oddaje predloga

**Status:** sprejeto za pregledno vejo · **Datum:** 2026-10-30 · **Seja:** S-024 · **Naloga:** BL-204

## Kontekst

Strežnik že sprejema request_id pod transakcijskim zaklepom in zavrne isti ID z drugo vsebino. Brskalnik je shranil samo urejana polja, ID namere pa v pomnilnik. Po izgubljenem odgovoru in reload je isti predlog lahko dobil nov ID. Dva zavihka istega osnutka zahtevata tudi zaščito pred zastarelim prepisom novih urejenih polj.

## Odločitev

- Verzija v2 lokalnega zapisa vsebuje identiteto osnutka, urejana polja in ločeno zamrznjeno operacijo z request_id, celotnim kanoničnim telesom, stanjem in potrjenim proposal_id. Operacija in preverjen zapis sta pred POST.
- Vsi brskalniški pisci uporabljajo isti koordinacijski mehanizem IndexedDB readwrite transakcije. Zapis ostane v localStorage, kjer ga lahko spremljajo drugi zavihki. Znotraj transakcije so read/modify/write/readback sinhroni. Če IndexedDB ni na voljo, se uporabi razpoložljivi Web Locks; brez varne koordinacije/shrambe se oddaja ustavi.
- UUID je kriptografski tudi na navadnem HTTP: če randomUUID ni na voljo, getRandomValues izdela UUIDv4. Ni odvisnosti od zunanjega izvajalca, knjižnice ali naključja Math.random.
- Izrecno preverjanje najprej prebere `/proposals/{request_id}`. Samo 404 dovoljuje ponovitev istega telesa/ID; drugi izidi ostanejo sledljivi. Ujemati se morajo ID in vsa poslovna polja. Ponovnega plačljivega dela ali samodejnega background replay ni.
- Urejan osnutek ostane ločen. Potrditev stare operacije sme počistiti samo še enaka aktualno shranjena polja znotraj iste koordinirane transakcije; novejša polja drugega zavihka se ohranijo. Programski restore/reopen ne sme sprožiti zastarelega autosave.
- Poškodovana v2 operacija se ne nadomesti tiho z novo. Iz v1 se obnovijo uporabna polja brez izmišljanja izgubljenega starega operation ID. Napaka po transportu ne zatrjuje, da ni bilo nič poslano; stanje se preveri z istim ID.

## Posledice

Trajnost velja znotraj brskalniškega izvora in njegove ohranjene shrambe. Ni večnapravna sinhronizacija ali varnostna kopija. Ročni izbris shrambe ne more obnoviti neznanega starega request_id. Strežniška idempotenca in kvote ostanejo avtoritativne; brskalniška koordinacija jih dopolni, ne nadomesti. Nobena sprememba ne odda naročila ali vklopi zunanjega modela.
