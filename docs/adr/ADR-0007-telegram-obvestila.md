# ADR-0007: Obvestila prek Telegrama
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-001

## Kontekst
Uporabnik želi obvestila na telefon. Strežnik je doma za Tailscale, brez javnih portov.

## Odločitev
**Telegram bot** (Bot API, `aiogram` ali `python-telegram-bot`) v načinu **long polling**, zato ne potrebuje javnega webhooka. Bot odgovarja **samo** na nastavljen `chat_id`. Sporočila sledijo VOICE.md §5 in imajo gumbe *Odpri*, *Spremljaj*, *Zavrzi*. Povezava *Odpri* vodi na Tailscale naslov aplikacije.

Pravila pošiljanja:
- tihi časi (privzeto 22:00–7:00);
- največ N obvestil na dan (privzeto 5), ostalo v dnevnem povzetku ob 7:30;
- takoj se pošljejo samo `thesis_break` na pozicijah in signali z oceno nad pragom.

## Posledice
- Vsebina obvestil gre prek Telegramovih strežnikov. Zneskov pozicij v obvestila ne pišemo, samo odstotke.

## Zavrnjene možnosti
- **ntfy:** dober, a zahteva lasten strežnik ali javni ntfy.sh in nima gumbov z odgovorom v istem obsegu.
- **E-pošta:** prepočasna za obvestila.
