# ADR-0004: LLM vloge prek LiteLLM
**Status:** sprejeto · **Datum:** 2026-10-22 · **Seja:** S-001

## Kontekst
Na voljo so: lokalna Ollama (24 GB VRAM, Qwen ~27B Q4), Claude Pro (Agent SDK kredit), OpenAI naročnina (ChatGPT prijava), OpenCode naročnina (OpenAI-kompatibilen endpoint). Ponudniki in modeli se bodo menjali.

## Odločitev
**Dopolnitev S-003:** Claude ni v avtomatiziranem cevovodu (uporabnik ga ne bo uporabljal prek API). `cloud-deep` = MiniMax, rezerva OpenCode Go. Spodnja izjema za `claude_runner` je odložena.

Koda kliče **vloge**, ne modelov: `embed`, `local-fast`, `local-reason`, `cloud-quick`, `cloud-deep`. Preslikava, proračuni in fallbacki so v `infra/litellm/config.yaml`. Izjema je `services/claude_runner`, ki uporablja Claude Agent SDK neposredno (naročniški kredit ne gre prek API ključa), vendar je izpostavljen kot ponudnik vloge `cloud-deep`.

## Posledice
- Zamenjava modela je sprememba konfiguracije, ne kode.
- Vsak klic se beleži s tokeni in ceno (`agent_run`).
- Masovne naloge (triaža) so brezplačne na lokalnem modelu.

## Zavrnjene možnosti
- Neposredni SDK klici iz vsakega modula: razpršeni ključi in ni centralnega proračuna.
