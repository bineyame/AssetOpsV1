"""DS3 (spec `specs/DS3-bulk-loader/spec.md` §2.5; D-DS3.2, D-DS3.12, D-DS3.13): load a generated world's inputs.

    python -m assetops_backend.load_world_inputs --world DIR --submit-as EMAIL --accept-as EMAIL [--tenant SLUG]

`DIR` holds one directory per tenant slug, each with at most `commercial/` (the tenant's DS1b canonical files, loaded
through 3A2's intake by `load_emulated_exports`, the one commercial path) and `telemetry/` (Batch V2 files
`*.batch.json`, loaded in sorted name order by the bulk evidence load). Before any connection: `DATABASE_URL` must
be set and name a permitted database (a `*_test` or `<prefix>_audit*` database on the test container, never an
operator's), and every selected tenant directory must hold nothing else.

One JSON line per tenant on stdout: `{"tenant", "commercial_exit", "batches", "already_loaded", "envelopes"}`.
Exit 0 done; 2 this command refused (`<CODE> <batch or -> <detail>` on stderr); 3 a database error
(`DATABASE_ERROR <class>`, never the URL); 4 the commercial step failed (`COMMERCIAL_EXIT <tenant> <exit>` after the
loader's own lines; that tenant's telemetry and later tenants are not loaded). Developer diagnostics only; nothing
here is served (D-DS3.7).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from assetops_backend.evidence.ledger import LedgerUnavailable

COMMERCIAL = "commercial"
TELEMETRY = "telemetry"
_LAYOUT = frozenset({COMMERCIAL, TELEMETRY})


class _Refused(Exception):
    def __init__(self, code: str, batch: str | None, detail: str) -> None:
        super().__init__(code)
        self.code, self.batch, self.detail = code, batch, detail


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.load_world_inputs",
                                     description="Load a generated world's commercial files and telemetry.")
    parser.add_argument("--world", required=True, type=Path, help="the world directory, one folder per tenant slug")
    parser.add_argument("--submit-as", required=True, help="email of the person who submits commercial files")
    parser.add_argument("--accept-as", required=True, help="email of another person who accepts them")
    parser.add_argument("--tenant", default=None, help="load this tenant only")
    return parser


def _tenants(world: Path, only: str | None) -> list[Path]:
    if not world.is_dir():
        raise _Refused("WORLD_LAYOUT_UNKNOWN", None, "the world is not a directory")
    tenants = sorted((p for p in world.iterdir() if p.is_dir()), key=lambda p: p.name)
    if only is not None:
        tenants = [p for p in tenants if p.name == only]
        if not tenants:
            raise _Refused("WORLD_LAYOUT_UNKNOWN", None, f"no tenant directory {only}")
    for tenant in tenants:
        for entry in sorted(tenant.iterdir(), key=lambda p: p.name):
            if entry.name not in _LAYOUT or not entry.is_dir():
                raise _Refused("WORLD_LAYOUT_UNKNOWN", None, f"{tenant.name}/{entry.name} is not commercial/ or telemetry/")
    return tenants


def _run(args: argparse.Namespace, ledger: Any, load_exports: Callable[..., int] | None) -> int:
    from assetops_backend.evidence.bulk_load import BulkEvidenceLoad, BulkLoadRefused, permitted_database

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise _Refused("NO_DATABASE", None, "set DATABASE_URL to a permitted test or audit database")
    if not permitted_database(url):
        raise _Refused("BULK_DATABASE_NOT_PERMITTED", None,
                       "only a *_test or <prefix>_audit* database on the test container is loaded")
    tenants = _tenants(args.world, args.tenant)
    if load_exports is None:
        from assetops_backend import load_emulated_exports

        load_exports = load_emulated_exports.main
    if ledger is None:
        from assetops_backend.evidence.composition import build_evidence_ledger

        ledger = build_evidence_ledger(url)
    for tenant in tenants:
        slug = tenant.name
        commercial_exit = None
        if (tenant / COMMERCIAL).is_dir():
            commercial_exit = load_exports(["--dir", str(tenant / COMMERCIAL), "--tenant", slug,
                                            "--submit-as", args.submit_as, "--accept-as", args.accept_as])
            if commercial_exit != 0:
                sys.stderr.write(f"COMMERCIAL_EXIT {slug} {commercial_exit}\n")
                return 4
        loaded = None
        if (tenant / TELEMETRY).is_dir():
            files = sorted((tenant / TELEMETRY).glob("*.batch.json"), key=lambda p: p.name)
            try:
                loaded = BulkEvidenceLoad(ledger).load([f.read_bytes() for f in files])
            except BulkLoadRefused as error:
                raise _Refused(error.code, error.external_batch_id, error.detail) from None
        sys.stdout.write(json.dumps({
            "tenant": slug, "commercial_exit": commercial_exit,
            "batches": 0 if loaded is None else loaded.batches,
            "already_loaded": 0 if loaded is None else loaded.already_loaded,
            "envelopes": 0 if loaded is None else loaded.envelopes,
        }, sort_keys=True) + "\n")
    return 0


def main(argv: Sequence[str] | None = None, *, ledger: Any = None,
         load_exports: Callable[..., int] | None = None) -> int:
    """`ledger` and `load_exports` are injected by tests; the checks before any connection always run."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return _run(args, ledger, load_exports)
    except _Refused as refused:
        sys.stderr.write(f"{refused.code} {refused.batch or '-'} {refused.detail}\n")
        return 2
    except Exception as error:  # noqa: BLE001 - a database error is exit 3; anything else is a defect and raises
        if not (isinstance(error, LedgerUnavailable) or _is_database_error(error)):
            raise
        sys.stderr.write(f"DATABASE_ERROR {type(error).__name__}\n")
        return 3


def _is_database_error(error: BaseException) -> bool:
    """SQLAlchemy's and the driver's errors, by their package (this module imports no database driver)."""
    return any(c.__module__.split(".")[0] in {"sqlalchemy", "psycopg"} for c in type(error).__mro__)


if __name__ == "__main__":
    sys.exit(main())
