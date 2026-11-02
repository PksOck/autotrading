# Portfelj in Watchlista: gostota in obdobja

Datum2026-11-01, dodatna uporabnikova zahteva med BL-232. BL-233. Izvedba po avtomatiki, v istem preglednem krogu.

- Pozicije/Watchlista imata vedno kompaktne vrstice in navpično sredinsko poravnano vsebino; številke ostanejo desno za pregledno primerjavo. Fiksna kompaktna gostota je omejena na te tabele, shranjeni izbor stolpcev/širin/profilov ostane. Ne režemo imen ali podatkovnih opozoril, zato ekstremne vsebine nimajo nasilno fiksne višine.
- Pri mini grafu sta število sej in dejanski datumski razpon takoj ob grafu oziroma pod njim. Info razkritje je ob črti,32px na namizju in48px na dotik; ne doda48px prazne vrstice med grafom in datumom. Vir in čas sta še vedno dosegljiva brez hover.
- Ob vrednosti portfelja izbirnik Dan / Od začetka leta ter podpisana znesek/odstotek. Iste definicije kot ADR-0026: to je cenovna ocena istih trenutnih količin, brez poslov, gotovine ali valutnega donosa, ne dejanski NAV donos računa. V EUR samo ob dokazani ciljni valuti FX, sicer izvorne valute ločeno z vidno omejitvijo.
- YTD uporablja zadnji shranjeni zaključek pred1. januarjem tekočega UTC leta (največ7 koledarskih dni od začetka leta) in zadnji svež zaključek. Če baza nima začetne cene, je jasna vrzel »Ni primerljive začetne cene za leto«. Brez delnih vsot ali uporabe prve poljubne cene v letu kot YTD. Datumi in vir so vidni v razlagi. Morebitni split/dividende niso NAV; brez usklajene osnove ne obljubljamo skupnega donosa.
- Strežniški izračuni Decimal in skupne, omejene poizvedbe po instrumentih. Prikaz/izbor obdobja ne kliče ponudnikov, LLM ali brokerja. Noben reseed samo za lepši YTD demo. API/TS se generirata; nova polja ne zahtevajo spremembe baze.

Dokaz: regresija gostote/centra in razmaka datuma v brskalniku, dosegljiv vir z Enter/dotikom, profile ohranimo. Sintetični YTD test z Dec31/Jan1 in manjkajočo/starodavno začetno ceno, mešanimi datumi/valutami ter determinističnim odstotkom. Celotni regresijski testi API in splet.

Dopolnitev po Astri2026-11-02: razkritje vira je v običajnem toku in samo odprta vrstica se poveča. Isti ponudnik ne potrdi split osnove; basis_verified privzeto false zahteva izrecen dokaz producenta, ki ga trenutni Bar nima. Zato produkcijski YTD ostane neznan, BL-234 je ločen naslednji podatkovni korak. Višina105px je interna kontrola običajnih demo vrstic, ne prepoved višjih dolgih imen/opozoril.
