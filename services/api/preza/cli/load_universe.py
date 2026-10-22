"""Run: python -m preza.cli.load_universe"""

import asyncio

from preza.db import get_sessionmaker
from preza.universe.loader import load_ucits


async def main() -> None:
    async with get_sessionmaker()() as session:
        count = await load_ucits(session)
        await session.commit()
    print(f"loaded {count} UCITS ETFs")


if __name__ == "__main__":
    asyncio.run(main())
