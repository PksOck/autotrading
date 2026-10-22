# ADR-0001: Gostovanje: Docker lokalno, Tailscale
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-001

## Kontekst
Sistem potrebuje stalne procese: IB Gateway (Java, 2FA), Python workerje, Postgres, Redis, LiteLLM in dostop do Ollame na GPU napravi v LAN. Na voljo sta lokalni Docker in cPanel pri Neoservu.

## Odločitev
Vse teče v **Docker Compose na lokalnem strežniku**. Ollama teče na ločeni GPU napravi v istem omrežju. Dostop od zunaj je samo prek **Tailscale** (HTTPS s Tailscale certifikatom), brez odprtih portov na usmerjevalniku.

## Posledice
- Podatki portfelja in poverilnice ostanejo doma.
- Strežnik mora biti stalno prižgan. Potrebne so varnostne kopije baze (BL-017).
- IB Gateway zahteva občasno potrditev 2FA v IBKR Mobile.

## Zavrnjene možnosti
- **cPanel (deljeno gostovanje):** ne podpira stalnih procesov, Dockerja, Redisa ali Postgresa in pomeni javno izpostavljenost.
- **VPS:** možen kasneje, a podatki o portfelju bi bili pri tretji osebi, Ollama pa ni dosegljiva brez tunela.
