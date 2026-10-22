"""Write the OpenAPI schema used to generate apps/web/lib/api/schema.d.ts.

Run: python -m preza.cli.export_openapi <path>
"""

import json
import sys
from pathlib import Path

from preza.main import create_app


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
    schema = create_app().openapi()
    target.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
