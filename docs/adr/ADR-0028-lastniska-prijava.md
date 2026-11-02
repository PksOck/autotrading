# ADR-0028: Lastniška prijava in zasebni dostop

**Status:** sprejeto · **Datum:** 2026-11-02 · **Seja:** S-029

Prijavni zaslon sam ne varuje API-ja. FastAPI je zato avtoriteta sej za vse zasebne REST/SSE/docs poti. Produkcija zahteva prijavo tudi ob AUTH_ENABLED=false; nepopolna konfiguracija in manjkajoč HTTPS zavrneta dostop. Razvojni demo je izrecna izjema, ne vzorec za javno gostovanje.

En lastnik, brez registracije ali obnove po e-pošti. scrypt-v1 uporablja naključno128-bitno sol, N=16384,r=8,p=5. V DB se hrani samo SHA256 naključnega256-bitnega sejnega žetona. Seja poteče v8h ali po30min uporabniške nedejavnosti; menjava gesla/uporabnika jo prekliče. Izhodni piškotek je HttpOnly/SameSiteStrict/Secure; produkcija uporablja __Host prefiks. DB globalno omejuje pet poskusov v15min s transakcijsko ključavnico, ne zaupa forwarded IP. To zavestno daje prednost zaščiti pred ugibanjem; ob napadu lahko lastnik15min ne more ponovno vstopiti.

Vsi nevarni zahtevki preverijo točen nastavljeni Origin, tudi login/logout/activity. Background GET/poll/SSE ne podaljšuje mirovanja. Odprt SSE ponovno preveri sejo pred branjem in pošiljanjem koraka. Splet preverja sejo ob odpiranju, v30s intervalih ter ob vrnitvi; odjava obvesti druge zavihke in počisti query cache. Skriti prikaz ohrani osnutke, preklic pa zasebno drevo odstrani. Zasebni odgovori imajo no-store. Že videne informacije in lokalni osnutki niso kriptografsko izbrisani z odjavo.

Proxy omejuje telo pred dekodiranjem, potrdi pot, ne sledi redirectom in ne posreduje poljubnih internih glav. CSP prepove okvirjanje/objekte in tuje obrazce, a ni polna nonce CSP za vse Next skripte. Secret build konteksti so izključeni, občutljivi HTTP dnevniki očiščeni, Flex traceback nima verige z žetonom.

Končni namen uporabnika je Docker + Tailscale Serve HTTPS samo s telefona S26 FE; Funnel in javni WAN port nista dovoljena postavitev. Privzeti all→all je treba nadomestiti z izjemo za TCP8443 tudi za IPv6. Druge storitve/SSH ostanejo. Dejansko varnost pravil potrdita Tailscale validator in preizkus naprave. Produkcijsko geslo nastavi uporabnik lokalno; samo testne sintetične poverilnice so v testih.

## Dopolnitev S-030

Za obstoječo uporabnikovo lokalno nastavitev sprejmemo tudi bcrypt2a/2b/2y, cost10–16. Knjižnica bcrypt5 preveri hash; več kot72 UTF8 bajtov se zavrne, ne krajša. Privzeto generiranje ostane scrypt. Uporabnik za zdaj ohrani trenutna Tailscale pravila; omejitev samo S26 se ne uveljavi. S tem dostop ni omejen na en telefon, lastniški API guard pa ostane obvezen.
