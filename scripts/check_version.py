"""Check release/package versions without installing project dependencies."""

import json
import os
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    expected = (ROOT / "VERSION").read_text().strip()
    number = r"(?:0|[1-9]\d*)"
    if not re.fullmatch(rf"{number}\.{number}\.{number}", expected):
        raise SystemExit("VERSION must be a release number x.y.z")
    values = {}
    for relative in ["package.json", "apps/web/package.json"]:
        values[relative] = json.loads((ROOT / relative).read_text())["version"]
    for folder in ["services/api", "services/agents"]:
        meta = tomllib.loads((ROOT / folder / "pyproject.toml").read_text())
        values[f"{folder}/pyproject.toml"] = meta["project"]["version"]
        lock = tomllib.loads((ROOT / folder / "uv.lock").read_text())
        own = next(p for p in lock["package"] if p["name"] == meta["project"]["name"])
        values[f"{folder}/uv.lock"] = own["version"]
    source = (ROOT / "services/api/preza/__init__.py").read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', source)
    values["API runtime"] = match.group(1) if match else None
    for name, actual in values.items():
        if actual != expected:
            raise SystemExit(f"Version mismatch: {name}: {actual} != {expected}")
    ref = os.environ.get("GITHUB_REF", "")
    if ref.startswith("refs/tags/") and ref != f"refs/tags/v{expected}":
        raise SystemExit("Release tag does not match VERSION")
    print(f"Version {expected}: all package/runtime/lock versions match")


if __name__ == "__main__":
    main()
