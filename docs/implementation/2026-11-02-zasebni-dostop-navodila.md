# Zasebna namestitev in sprejemni pregled

Ta krog ne zamenja obstoječega :3000. :3100 ostaja ločen sintetičen demo; /login ter /about, /privacy, /terms, /security so tam za pregled. :3200 je začasen avtomatizirani test prijave, nikoli produkcijska namestitev ali cilj Tailscale Serve.

## Produkcijski koraki

1. V ločeno lokalno `.env.private` prenesi potrebne nastavitve iz `.env.example`, uporabi lastni skrivnosti za DB/LiteLLM ter APP_ENV=production. APP_BASE_URL mora biti točen HTTPS naslov Serve z :8443, brez poti. WEB_BIND naj ostane127.0.0.1. Datoteke ne commitaj.
2. V `services/api` lokalno zaženi `uv run python -m preza.cli.owner_password --output ../../infra/secrets/owner.env`. Sam vpiši in ponovi edinstveno geslo (14–256 znakov). Orodje ne izpiše gesla, ustvari datoteko s soljenim hashom in zavrne prepis obstoječe datoteke. Za zamenjavo najprej varno odstrani/premakni staro lokalno datoteko. Datoteka naj bo dostopna samo lastniku.
3. Iz korena repoja: `docker compose --env-file .env.private --env-file infra/secrets/owner.env -p preza-private -f infra/docker-compose.yml -f infra/docker-compose.private.yml up -d --build postgres redis api web`. To ustvari svojo prazno bazo/volumne in loopback3300. Ne uporablja produkcijskega/demonstracijskega volumna drugega projekta in ne poganja modelnih delavcev. Uvoz zasebnih podatkov je ločen korak.
4. V Tailscale potrdi ozko pravilo: izbran telefon → ta gostitelj TCP8443. Prejšnje all→all ne sme več pokrivati8443; izloči oba naslova gostitelja IPv4/IPv6. Lokalna prilagojena konfiguracija vsebuje pozitivne/negativne teste in ohranjeni SSH; zasebni IP niso v GitHubu. Potrditev pravil je pogoj za aktivacijo Serve, ne dokaz, da je naprava že preizkušena.
5. Obstoječega Serve443→8090 ne prepiši. Šele po korakih1–4 zaženi `tailscale serve --bg --https=8443 http://127.0.0.1:3300`. Nikoli `funnel`. Preveri `tailscale serve status` in da WAN/LAN porta3300/8443 nista odprta neposredno na Docker.
6. S S26 FE ob vključenem Tailscale odpri nastavljeni HTTPS naslov. Brez prijave mora slediti /login, brez seje /api/portfolio vrne401. Prijavi se, preveri portfelj in odjavo. Drugi telefon/NAS morata povezavo8443 zavrniti. Druga storitev443 mora delovati kot prej. Če pravilna naprava izgubi svojo identiteto/IP (ponovna registracija), popravi pravilo in ponovno opravi negativni test.

## Meje in obnova

Seja velja8h, mirovanje30min; statusna osveževanja mirovanja ne podaljšujejo. Aktivnost miške/tipkovnice obvesti strežnik največ1/min. Pet prijavnih poskusov v15min je skupnih za vse povezave, tudi neuspešni. Menjava hasha in ponovni zagon API prekličeta stare seje po naslednjem preverjanju.

Lastniška namestitev nima javne registracije ali poštne obnove gesla. Za obnovo je potreben lokalni dostop do konfiguracije. Izgubljen telefon odstrani iz Tailscale ter zamenjaj geslo. Tailscale pravila varujejo ta dostop; druga naprava z že dovoljenim SSH/upravnim dostopom do gostitelja ni izločena iz njegovega operacijskega sistema. Prijava ne odstrani datotek, ki jih je lastnik že prenesel.

Referenčna navodila: [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve), [grants](https://tailscale.com/docs/reference/syntax/grants), [IP sets](https://tailscale.com/docs/features/tailnet-policy-file/ip-sets), [OWASP seje](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).
