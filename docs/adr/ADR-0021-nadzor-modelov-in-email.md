# ADR-0021: Nadzor samodejnih modelov in SMTP obvestila

**Status:** sprejeto v pregledni veji · **Datum:** 2026-10-29 · **Seja:** S-018

## Kontekst

Uporabnik želi ustaviti avtomatsko uporabo lokalnih modelov brez izklopa prenosa cen, novic in portfelja ter nastaviti e-pošto za več prejemnikov. Enkraten pregled stikala na začetku večstopenjske analize ne ustavi njenih naslednjih klicev.

## Odločitev

- Trajno glavno stikalo samodejnih analiz je ločeno od globalne pavze. Preveri se pri sprejemu/prevzemu in pred vsakim novim avtomatskim LLM klicem. Tekoči HTTP klic se dokonča. Ročne analize ohranijo svojo izrecno pot, politiko in kvoto.
- Izvor je vezan na trajno izvedbo; ročni vhodni posli uporabljajo strežniške oznake, vezane na ime funkcije. Neznan job ID ne pomeni ročnega dovoljenja. Otroški pregledi tez preverijo ID, revizijo, teden in pripadnost trajni izvedbi ter podedujejo ročni izvor/izjemo okna.
- Ročni otroški pregled dobi ID svoje izvedbe, da blokiran avtomatski posel ne zatre ročnega zagona. Rezervacija in atomarni dispatch ostaneta avtoritativna; drug posel ne označi še aktivnega pregleda kot prekinjenega in ne ponovi plačljivega klica.
- SMTP host, port, uporabnik, geslo, pošiljatelj in TLS način so samo strežniška konfiguracija. UI hrani največ 20 validiranih prejemnikov, vrste obvestil, omogočenost in revizijo. Brez povezave ali prejemnikov pošiljanje ni mogoče.
- Novi signali, končane analize in dnevni povzetek dobijo trajno dostavo za vsakega prejemnika. Enolični ključ prepreči normalno ponovno pošiljanje. Pred vsako dostavo se preverijo aktualne preference in globalna pavza.
- Pred SMTP se trajno zapiše namera pošiljanja. Nejasen odgovor ali prekinitev ostane `unknown`/`sending` z vidnim opozorilom in brez samodejnega ponavljanja. To daje prednost preprečevanju dvojnikov pred zagotovljeno dostavo; exactly-once SMTP ni obljubljen.

## Posledice

SMTP podpira samo STARTTLS ali TLS z validacijo certifikata. Shranjevanje nastavitev ne pošlje testnega sporočila. V razvoju so testi ponaredili transport; dejanska povezava/dostava ostaja za uporabniško konfiguracijo in ločeno izrecno preverjanje. Na :3000 te nove kontrole še niso nameščene.
