# services/claude_runner: Claude Agent SDK

Majhen servis, ki izvaja naloge vloge `cloud-deep` prek **Claude Agent SDK** z naročniško prijavo (Claude Pro, ločen mesečni Agent SDK kredit).

- Vhod: opravilo iz Redis vrste (poziv, shema izhoda, kontekst).
- Izhod: validiran JSON + poraba (tokeni, ocenjen strošek).
- Števec kredita: ko je mesečni kredit porabljen, servis zavrne opravilo in LiteLLM fallback preusmeri na OpenAI.

Ref: PLAN.md §4, ADR-0004, BL-013, BL-084.
