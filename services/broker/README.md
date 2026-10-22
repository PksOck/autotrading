# services/broker: Interactive Brokers

Do ločitve servisa je koda v `services/api/preza/broker/` (Flex) in `services/api/preza/data/providers/ibkr.py` (sveče prek IB Gateway).

- `flex/`: Flex Web Service (pozicije, posli, gotovina, dividende), samo branje, brez gatewaya (BL-022).
- `ib_client.py`: ib_async → IB Gateway (Docker, **Read-Only API**): EOD svečke, contract details, opcijske verige, zakasnjeni podatki (BL-024, BL-120). Delno prirejeno po Vibe-Trading `agent/src/trading/connectors/ibkr/local.py` (MIT).
- `guards.py`: varovala za naročila (M7, ADR-0006).

**Pravilo:** v tej mapi je edina koda, ki bo kdaj lahko oddala naročilo. Do M7 je ni.
