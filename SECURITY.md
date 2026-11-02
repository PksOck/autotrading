# Varnost

Preža je zasebno raziskovalno orodje. Aktivni razvoj je v0.2.x; razvojna predizdaja ni zagotovilo produkcijske odpornosti ali zaključene neodvisne penetracijske revizije.

## Poročanje

Težavo najprej sporoči lastniku namestitve po znanem zasebnem kanalu. Za repozitorij uporabi zasebno prijavo prek zavihka GitHub Security, če je omogočena. Javna issue naj ne vsebuje poverilnic, sejnih piškotkov, Flex izpisov, osebnih računov ali podrobnosti uporabnega obvoda. Kontaktnega naslova, ki še ni potrjen, ne objavljamo.

## Namestitev

- Produkcija mora uporabljati HTTPS in lastniško prijavo. API, baza, Redis, LiteLLM in Gateway nimajo javno odprtih portov. Docker web ostane vezan na loopback; Tailscale Serve doda HTTPS.
- Tailscale ne pomeni samodejne omejitve na en telefon. Dejanski omrežni dostop določajo pravila tailneta; lastniška prijava je ločen sloj.
- Skrivnosti samo v ignorirani lokalni konfiguraciji. `.env.example` vsebuje prazne ali vzorčne vrednosti. Bcrypt gesla nad72 UTF8 bajti niso tiho skrajšana.
- Pred nadgradnjo dejanske baze preveri backup/restore. Oznaka izdaje omogoča izbiro kode, ne samodejne povrnitve podatkovne sheme.
- Naročila vedno zahtevajo človekovo odločitev in broker varovala. Read-only Gateway ostane zahteva pred odobritvijo M7.

Postopek: [zasebna namestitev](docs/implementation/2026-11-02-zasebni-dostop-navodila.md), [ADR-0028](docs/adr/ADR-0028-lastniska-prijava.md), [pravila projekta](AGENTS.md).
