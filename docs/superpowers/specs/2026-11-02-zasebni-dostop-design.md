# Zasebni dostop, spremljevalne strani in varnost

Uporabnik je odobril izvedbo ter Astra pregled. Zadnja usmeritev: Docker, HTTPS prek Tailscale in dostop samo z njegovega telefona. Javne internetne objave ne aktiviramo. Konkreten telefon/domena še nista določena; konfiguracija Tailscale ostane ločen operativni korak.

## Odločitev
FastAPI je edina avtoriteta sej: en lastniški račun iz lokalne konfiguracije, brez registracije/obnove po pošti. Geslo scrypt; naključna seja, v bazi samo hash, absolutni rok8h in nedejavnost30min, odjava in menjava poverilnice prekličeta seje. Produkcija obvezno zahteva prijavo in veljavno HTTPS izhodišče; nepopolna konfiguracija zavrne zasebne zahtevke. Demo razvoj lahko ostane brez prijave, poseben izoliran test omogoči prijavo.

Next preusmeri obiskovalca na prijavo in preveri sejo pred proxy dostopom; API preveri vsak zasebni zahtevek tudi neposredno. Cookie HttpOnly/SameSite=Strict/Secure v produkciji. Vsi nevarni zahtevki zahtevajo točen konfigurirani Origin. Globalna DB omejitev poskusov s ključavnico prepreči obhod prek ponovnega zagona/ponarejenega IP. Nezaupanja vredne X-Forwarded glave niso dokaz identitete.

Proxy sprejme samo dovoljene poti, zavrne dot/slash obhode, omeji tok telesa pred dekodiranjem (10MiB Flex,1MiB ostalo), ne sledi preusmeritvam. Nobena glava odjemalca ne more izklopiti zaščite. Zasebni odgovori niso predpomnjeni. Varnostne glave: frame-ancestors/objekti onemogočeni, nosniff, referrer, permissions. CSP združljiv z Next se dokumentira brez lažnega jamstva proti XSS.

Povezave: O aplikaciji, Zasebnost in piškotki, Pogoji uporabe, Varnost. Besedila SL/EN opisujejo dejansko zasebno orodje, nujne piškotke, vire/LLM ponudnike glede na lokalno nastavitev, omejitve podatkov in človeško odločitev. Brez izmišljene pravne osebe, kontaktnega naslova ali jamstva skladnosti.

## Možnosti in meje
Prijava samo v Next bi pustila nezaščiten API; samo Tailscale bi dovolil vsem napravam glede na trenutna ACL pravila. Izbrana sta oba sloja. Lastnik geslo nastavi lokalno; v pogovoru ali repozitoriju se nikoli ne zbira. Tailscale Serve ni Funnel. Odpiranje interneta zahteva ponovno preverjanje TLS/proxy/MFA in gostovanja. Nobena rešitev ni »hackproof«.

## Sprejem
Neposredni API in splet brez seje ne razkrijeta zasebnih podatkov. Neveljavna/potekla/preklicana seja odpove. Čezizvorni zapis/prijava/odjava odpovejo. Omejitev poskusov deluje ob sočasnih klicih. Prijava/odjava delujeta na telefonu, javne informativne strani so dostopne brez seje. Migracije in YTD regresije ostanejo zelene. :3000 in zasebni podatki ostanejo nespremenjeni.
