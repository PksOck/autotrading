"""Run interactively on your machine; prints only a salted hash for local secret config."""

from argparse import ArgumentParser
from getpass import getpass
from pathlib import Path

from preza.services.owner_access import hash_password


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, help="Create a local env file; refuses to overwrite")
    args = parser.parse_args()
    password = getpass("New owner password (14-256 characters): ")
    if password != getpass("Repeat password: "):
        raise SystemExit("Passwords differ")
    encoded = hash_password(password)
    if args.output is None:
        print(encoded)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as target:
            target.write(f"OWNER_PASSWORD_HASH='{encoded}'\n")
        print("Owner hash saved locally. Protect this file; do not commit it.")


if __name__ == "__main__":
    main()
