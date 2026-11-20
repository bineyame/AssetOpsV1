"""3A2 (spec §3.4; D-3A2.5, R12, P3): create a tenant's pseudonym key. ON1 (spec §3.5; D-ON1.7, D-ON1.14): erase it.

`python -m assetops_backend.commercial.pseudonym_key create --dir <dir> --tenant-id <uuid>` writes 32 random bytes to
`<dir>/<tenant_id>.key` with mode 0600 (through the composition's `create_key_file`). An existing key is never
replaced, a missing directory is never created, and an erased key is never made again (exit 2 each).

`python -m assetops_backend.commercial.pseudonym_key erase --dir <dir> --tenant-id <uuid>` writes the tenant's
tombstone and removes its key (through the composition's `erase_key_file`): `Erased.` or `Already erased.`, exit 0.
Erasure is final. Messages go to standard error, results to standard output; the key is never printed.
"""
from __future__ import annotations

import argparse
import sys
from uuid import UUID

from assetops_backend.commercial.composition import (KeyDirectoryMissing, KeyErased, KeyExists, create_key_file,
                                                     erase_key_file)

_ERASED = ("This tenant's key was erased. A new key would not match the records already held; onboard the operator "
           "as a new tenant.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pseudonym_key")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("create", "erase"):
        command = commands.add_parser(name)
        command.add_argument("--dir", required=True)
        command.add_argument("--tenant-id", required=True, type=UUID)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "erase":
            done = erase_key_file(args.dir, args.tenant_id)
            sys.stdout.write("Erased.\n" if done == "ERASED" else "Already erased.\n")
            return 0
        create_key_file(args.dir, args.tenant_id)
    except KeyDirectoryMissing:
        sys.stderr.write("The key directory does not exist.\n")
        return 2
    except KeyExists:
        sys.stderr.write("A key already exists for this tenant; it is never replaced.\n")
        return 2
    except KeyErased:
        sys.stderr.write(_ERASED + "\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
