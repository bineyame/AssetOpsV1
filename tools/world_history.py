import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "simulator"))

# DS1 world history CLI (`specs/DS1-history-generator/spec.md` §4.1).
#
# The only reader of a YAML manifest for the world generator. `--manifest` takes a
# `.yaml`/`.yml` manifest, or a `.json` view (the view is idempotent).
#
#   view     --manifest M --out F       write the view's file bytes
#   generate --manifest M --out H       write the history file
#   check    --manifest M --history H   exit 0 on identical bytes; otherwise print
#                                       `DS1_CHECK_DIFF <scope_key>` (or `meta`) and exit 1

import argparse  # noqa: E402
import json  # noqa: E402

from assetops_simulator.world.canonical import file_bytes, write_canonical_file  # noqa: E402
from assetops_simulator.world.history import generate_history  # noqa: E402
from assetops_simulator.world.view import ManifestView  # noqa: E402


def load_view(path: Path) -> ManifestView:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        document = json.loads(text)
    else:
        import yaml  # the only YAML read in the generator path

        document = yaml.safe_load(text)
    return ManifestView.from_document(document)


def _first_difference(expected: dict, found_bytes: bytes) -> str:
    try:
        found = json.loads(found_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return "meta"
    if not isinstance(found, dict) or found.get("meta") != expected["meta"]:
        return "meta"
    found_tenants = found.get("tenants")
    if not isinstance(found_tenants, dict):
        return "meta"
    seen = set()
    for tenant, sites in expected["tenants"].items():
        for site, months in sites.items():
            for month, block in months.items():
                key = f"{tenant}/{site}/{month}"
                seen.add(key)
                if found_tenants.get(tenant, {}).get(site, {}).get(month) != block:
                    return key
    for tenant, sites in found_tenants.items():
        for site, months in (sites or {}).items():
            for month in months or {}:
                key = f"{tenant}/{site}/{month}"
                if key not in seen:
                    return key
    return "meta"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="world_history.py", description="DS1 world history generator")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("view", "generate"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", required=True, type=Path)
        command.add_argument("--out", required=True, type=Path)
    check = commands.add_parser("check")
    check.add_argument("--manifest", required=True, type=Path)
    check.add_argument("--history", required=True, type=Path)
    args = parser.parse_args(argv)

    view = load_view(args.manifest)
    if args.command == "view":
        write_canonical_file(view, args.out)
        return 0
    history = generate_history(view)
    if args.command == "generate":
        write_canonical_file(history, args.out)
        return 0
    found = args.history.read_bytes()
    sys.stdout.reconfigure(encoding="utf-8")
    if found == file_bytes(history):
        return 0
    print(f"DS1_CHECK_DIFF {_first_difference(history, found)}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
