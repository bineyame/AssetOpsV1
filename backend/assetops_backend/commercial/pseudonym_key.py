"""3A2 (spec §3.4; D-3A2.5, R12, P3): create a tenant's pseudonym key.

`python -m assetops_backend.commercial.pseudonym_key create --dir <dir> --tenant-id <uuid>` writes 32 random bytes to
`<dir>/<tenant_id>.key` with mode 0600 (through the composition's `create_key_file`). An existing key is never
replaced and a missing directory is never created (exit 2 each). Messages go to standard error; the key is never
printed. No other subcommand.
"""
from __future__ import annotations

import argparse
import sys
from uuid import UUID

from assetops_backend.commercial.composition import KeyDirectoryMissing, KeyExists, create_key_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pseudonym_key")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--dir", required=True)
    create.add_argument("--tenant-id", required=True, type=UUID)
    args = parser.parse_args(argv)
    try:
        create_key_file(args.dir, args.tenant_id)
    except KeyDirectoryMissing:
        sys.stderr.write("The key directory does not exist.\n")
        return 2
    except KeyExists:
        sys.stderr.write("A key already exists for this tenant; it is never replaced.\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
