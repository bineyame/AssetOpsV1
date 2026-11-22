import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "simulator"))
sys.path.insert(0, str(REPOSITORY / "contracts"))  # DS1b P1: the canonical format from this tree

# DS1 world history CLI (`specs/DS1-history-generator/spec.md` §4.1).
#
# The only reader of a YAML manifest for the world generator. `--manifest` takes a
# `.yaml`/`.yml` manifest, or a `.json` view (the view is idempotent).
#
#   view     --manifest M --out F       write the view's file bytes
#   generate --manifest M --out H       write the history file
#   check    --manifest M --history H   exit 0 on identical bytes; otherwise print
#                                       `DS1_CHECK_DIFF <scope_key>` (or `meta`) and exit 1
#   records  --manifest M --out DIR     DS1b: write the canonical v1 batches and `unwritten.json` into a new
#                                       or empty DIR outside the repository; exit 3 with `DS1B_*` on stderr
#   exports  --manifest M --out DIR     3A3: write the emulated native CSV exports (October, mini-grid) and
#                                       `unwritten.json` into a new or empty DIR outside the repository; exit 3 with
#                                       `EMU_*` or `DS1B_*` on stderr

import argparse  # noqa: E402
import json  # noqa: E402

from assetops_contracts.canonical import to_canonical_json  # noqa: E402

from assetops_simulator.world.canonical import file_bytes, write_canonical_file  # noqa: E402
from assetops_simulator.world import telemetry as telemetry_writer  # noqa: E402
from assetops_simulator.world.exports import build_exports, file_name  # noqa: E402
from assetops_simulator.world.history import generate_history  # noqa: E402
from assetops_simulator.world.records import batch_file_name, build_records  # noqa: E402
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


def _out_dir(out: Path) -> Path:
    """DS1b P6: the records directory must resolve outside the repository and hold nothing yet."""
    resolved = out.resolve()
    if resolved == REPOSITORY or resolved.is_relative_to(REPOSITORY):
        raise ValueError("DS1B_OUT inside-repository")
    if resolved.exists() and (not resolved.is_dir() or any(resolved.iterdir())):
        raise ValueError("DS1B_OUT not-empty")
    return resolved


def _records(manifest: Path, out: Path) -> int:
    try:
        target = _out_dir(out)
        view = load_view(manifest)
        result = build_records(view, generate_history(view))
    except ValueError as error:
        if not str(error).startswith("DS1B_"):
            raise
        print(error, file=sys.stderr)
        return 3
    target.mkdir(parents=True, exist_ok=True)
    for batch in result.batches:
        (target / batch_file_name(batch)).write_bytes(to_canonical_json(batch))
    (target / "unwritten.json").write_bytes(file_bytes([list(row) for row in result.unwritten]))
    return 0


def _exports(manifest: Path, out: Path, extras: Path | None = None) -> int:
    try:
        target = _out_dir(out)
        extra = _out_dir(extras) if extras is not None else None
        view = load_view(manifest)
        result = build_exports(view, generate_history(view))
    except ValueError as error:
        if not str(error).startswith(("EMU_", "DS1B_")):
            raise
        print(error, file=sys.stderr)
        return 3
    target.mkdir(parents=True, exist_ok=True)
    for export in result.files:
        (target / file_name(export)).write_bytes(export.data)
    if extra is not None:  # D-DD.54 staged DS1b JSON and DD spec §5.4 statements: not in the CSV directory
        extra.mkdir(parents=True, exist_ok=True)
        for name, data in (*result.staged, *result.statements):
            (extra / name).write_bytes(data)
    (target / "unwritten.json").write_bytes(file_bytes([list(row) for row in result.unwritten]))
    return 0


def _site_inputs(onboarding: Path, bindings: Path, out: Path) -> int:
    documents = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(onboarding.glob("*.onboarding.json"))]
    joined = {"schema": telemetry_writer.SITE_INPUTS_SCHEMA, "generator": telemetry_writer.GENERATOR, "sites": []}
    by_code = {}
    for path in sorted(bindings.glob("*-bindings.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        by_code[document["site_code"]] = document
    try:
        for document in documents:
            joined["sites"] += telemetry_writer.site_inputs(document, by_code)["sites"]
    except telemetry_writer.TelemetryRefused as error:
        print(error, file=sys.stderr)
        return 3
    joined["sites"].sort(key=lambda s: (s["tenant"], s["code"]))
    write_canonical_file(joined, out)
    return 0


def _telemetry(manifest: Path, sites: Path, books: Path, out: Path, start: str, end: str,
               only: tuple[str, ...] | None) -> int:
    try:
        target = _out_dir(out)
        view = load_view(manifest)
        history = generate_history(view)
        expenses = {p.name.removesuffix(".expenses.csv"): p.read_text(encoding="utf-8")
                    for p in books.glob("*.expenses.csv")}
        result = telemetry_writer.build_telemetry(
            view, json.loads(sites.read_text(encoding="utf-8")), telemetry_writer.books_for(view, history, expenses),
            start=start, end=end, only=only)
    except telemetry_writer.TelemetryRefused as error:
        print(error, file=sys.stderr)
        return 3
    for name, data in result.files:
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        (target / name).write_bytes(data)
    for name, document in result.manifests:
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        write_canonical_file(document, target / name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """ON1 (spec §4): public, so the runbook test parses its command line."""
    parser = argparse.ArgumentParser(prog="world_history.py", description="DS1 world history generator")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("view", "generate"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", required=True, type=Path)
        command.add_argument("--out", required=True, type=Path)
    records = commands.add_parser("records", help="write the canonical v1 money records (DS1b)")
    records.add_argument("--manifest", required=True, type=Path)
    records.add_argument("--out", required=True, type=Path, help="a new or empty directory outside the repository")
    exports = commands.add_parser("exports", help="write the emulated native CSV exports (3A3)")
    exports.add_argument("--manifest", required=True, type=Path)
    exports.add_argument("--out", required=True, type=Path, help="a new or empty directory outside the repository")
    exports.add_argument("--extras", type=Path, default=None,
                         help="a new or empty directory outside the repository for the staged DS1b JSON and statements")
    inputs = commands.add_parser("site-inputs", help="join each /2 Site with its binding conversion (DD3.1, D-DD.28)")
    inputs.add_argument("--onboarding", required=True, type=Path, help="a directory of *.onboarding.json")
    inputs.add_argument("--bindings", required=True, type=Path, help="a directory of *-bindings.json")
    inputs.add_argument("--out", required=True, type=Path)
    telemetry = commands.add_parser("telemetry", help="write the Sites' readings (DD3.1)")
    telemetry.add_argument("--manifest", required=True, type=Path)
    telemetry.add_argument("--sites", required=True, type=Path)
    telemetry.add_argument("--books", required=True, type=Path, help="the directory `exports` wrote")
    telemetry.add_argument("--out", required=True, type=Path, help="a new or empty directory outside the repository")
    telemetry.add_argument("--start", default="2026-07-01", help="first local day of the span")
    telemetry.add_argument("--end", default="2026-10-31", help="last local day of the span")
    telemetry.add_argument("--site", action="append", default=None, help="a Site code; repeat for several")
    check = commands.add_parser("check")
    check.add_argument("--manifest", required=True, type=Path)
    check.add_argument("--history", required=True, type=Path)
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "records":
        return _records(args.manifest, args.out)
    if args.command == "exports":
        return _exports(args.manifest, args.out, args.extras)
    if args.command == "site-inputs":
        return _site_inputs(args.onboarding, args.bindings, args.out)
    if args.command == "telemetry":
        return _telemetry(args.manifest, args.sites, args.books, args.out, args.start, args.end,
                          tuple(args.site) if args.site else None)

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
