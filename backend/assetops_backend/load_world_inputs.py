"""DS3 (spec `specs/DS3-bulk-loader/spec.md` §2.5; D-DS3.2, D-DS3.12, D-DS3.13): load a generated world's inputs.

    python -m assetops_backend.load_world_inputs --world DIR --submit-as EMAIL --accept-as EMAIL [--tenant SLUG]

`DIR` holds one directory per tenant slug, each with at most `commercial/` (the tenant's DS1b canonical files, loaded
through 3A2's intake by `load_emulated_exports`, the one commercial path) and `telemetry/` (Batch V2 files
`*.batch.json`, loaded in sorted name order by the bulk evidence load, and readings files `*.readings.json`). Before
any connection: `DATABASE_URL` must
be set and name a permitted database (a `<prefix>_audit*` database or a harness clone on the test container, never an
operator's), and every selected tenant directory must hold nothing else.

Readings (DD5a; spec §4.6 as amended by D-DD.139, D-DD.140): each Site's readings files are sealed by
`evidence/world_seal.seal_readings` against the Site's pinned binding snapshot (the Site resolved by
`PostgresEvidenceLedger.site_scope`, its `foundation_digest` from `site-inputs.json` beside the tenant folders) and
written once to `<slug>/sealed/`; a re-run re-seals and refuses `WORLD_SEALED_BYTES_DIFFER` if the bytes differ. The
sealed batches load after the `/1` batch files. A tenant folder may also hold `staged/`, `sealed/` and `disorder/`.

One JSON line per tenant on stdout: `{"tenant", "commercial_exit", "batches", "already_loaded", "envelopes",
"readings_files", "sealed_batches"}`.
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
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Sequence

from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.evidence.world_seal import SealContext, WorldSealRefused, context_from_snapshot, seal_readings

COMMERCIAL = "commercial"
TELEMETRY = "telemetry"
SEALED = "sealed"
#: D-DD.140: `staged/` (canonical JSON loaded by its own step) and `disorder/` (planted files) are accepted here.
_LAYOUT = frozenset({COMMERCIAL, TELEMETRY, SEALED, "staged", "disorder"})
SITE_INPUTS = "site-inputs.json"
#: `(slug, site code, first reading start, last reading end, foundation_digest)` -> the Site's seal context.
SealResolver = Callable[[str, str, datetime, datetime, str], SealContext]


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


def _digests(world: Path) -> dict[tuple[str, str], str]:
    path = world / SITE_INPUTS
    if not path.is_file():
        return {}
    return {(s["tenant"], s["code"]): s["foundation_digest"] for s in json.loads(path.read_bytes())["sites"]}


def _seal_tenant(tenant: Path, digests: dict, resolve: SealResolver) -> tuple[int, list[bytes]]:
    """The tenant's readings files sealed (D-DD.139), written to `sealed/` once (D-DD.140); returns the number of
    readings files and the sealed batch bytes in sealing order."""
    files = sorted((tenant / TELEMETRY).glob("*.readings.json"), key=lambda p: p.name)
    by_site: dict[str, list[tuple[date, list, str]]] = {}
    for path in files:
        document = json.loads(path.read_bytes())
        by_site.setdefault(document["site_code"], []).append(
            (date.fromisoformat(document["day"]), document["readings"], path.name))
    sealed: list[tuple[str, bytes]] = []
    for code in sorted(by_site):
        days = sorted(by_site[code], key=lambda d: d[0])
        first = days[0][2]
        digest = digests.get((tenant.name, code))
        if digest is None:
            raise _Refused("WORLD_TELEMETRY_UNRESOLVED", first, f"foundation_digest {code} not in {SITE_INPUTS}")
        rows = [r for _, day_rows, _ in days for r in day_rows]
        if not rows:
            continue
        try:
            context = resolve(tenant.name, code, min(datetime.fromisoformat(r["start"]) for r in rows),
                              max(datetime.fromisoformat(r["end"]) for r in rows), digest)
            batches = seal_readings(context, [(d, day_rows) for d, day_rows, _ in days])
        except WorldSealRefused as refused:
            raise _Refused(refused.code, first, refused.detail) from None
        sealed += [(b.name, b.text.encode("utf-8")) for b in batches]
    folder = tenant / SEALED
    present = {p.name for p in folder.glob("*.batch.json")} if folder.is_dir() else set()
    names = {name for name, _ in sealed}
    for name, body in sealed:
        if name in present and (folder / name).read_bytes() != body:
            raise _Refused("WORLD_SEALED_BYTES_DIFFER", name, "the sealed file is not the re-seal of the inputs")
    for name in sorted(present - names):
        raise _Refused("WORLD_SEALED_BYTES_DIFFER", name, "the sealed file is no batch of the inputs")
    for name, body in sealed:
        if name not in present:
            folder.mkdir(exist_ok=True)
            (folder / name).write_bytes(body)
    return len(files), [body for _, body in sealed]


def _database_resolver(url: str, ledger: Any) -> SealResolver:
    """The Site's scope by `site_scope(slug, code)` and its binding snapshot over the readings span, as the gateway
    downloads it (`sites.registered_basis.select_registered_basis`, which calls `acquisition_snapshot`)."""
    from assetops_backend.sites.composition import build_foundation_store
    from assetops_backend.sites.foundation_service import FoundationService, utc_now
    from assetops_backend.sites.registered_basis import BasisRefused, select_registered_basis

    store = build_foundation_store(url)

    def resolve(slug: str, code: str, start: datetime, end: datetime, digest: str) -> SealContext:
        scope = ledger.site_scope(slug, code)
        if scope is None:
            raise WorldSealRefused("WORLD_TELEMETRY_UNRESOLVED", f"site {code}")
        service = FoundationService(store, slug, utc_now)
        tenant = service.tenant()
        site = service.site(tenant, code)
        if site is None or site.id != scope[1]:
            raise WorldSealRefused("WORLD_TELEMETRY_UNRESOLVED", f"site {code}")
        try:
            basis = select_registered_basis(service, tenant, site, start=start, end=end, knowledge_at=None)
        except BasisRefused as refused:
            raise WorldSealRefused("WORLD_TELEMETRY_UNRESOLVED", f"bindings {code} {refused.code}") from None
        return context_from_snapshot(code, str(scope[1]), basis.snapshot.document, basis.snapshot.sha256, digest)

    return resolve


def _run(args: argparse.Namespace, ledger: Any, load_exports: Callable[..., int] | None,
         seal_context: SealResolver | None = None) -> int:
    from assetops_backend.evidence.bulk_load import BulkEvidenceLoad, BulkLoadRefused, permitted_database

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise _Refused("NO_DATABASE", None, "set DATABASE_URL to a permitted test or audit database")
    if not permitted_database(url):
        raise _Refused("BULK_DATABASE_NOT_PERMITTED", None,
                       "only a <prefix>_audit* database or a harness clone on the test container is loaded")
    tenants = _tenants(args.world, args.tenant)
    if load_exports is None:
        from assetops_backend import load_emulated_exports

        load_exports = load_emulated_exports.main
    if ledger is None:
        from assetops_backend.evidence.composition import build_evidence_ledger

        ledger = build_evidence_ledger(url)
    digests = _digests(args.world)
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
        readings_files, sealed = 0, []
        if (tenant / TELEMETRY).is_dir():
            files = sorted((tenant / TELEMETRY).glob("*.batch.json"), key=lambda p: p.name)
            if any((tenant / TELEMETRY).glob("*.readings.json")):
                if seal_context is None:
                    seal_context = _database_resolver(url, ledger)
                readings_files, sealed = _seal_tenant(tenant, digests, seal_context)
            try:
                loaded = BulkEvidenceLoad(ledger).load([f.read_bytes() for f in files] + sealed)
            except BulkLoadRefused as error:
                raise _Refused(error.code, error.external_batch_id, error.detail) from None
        sys.stdout.write(json.dumps({
            "tenant": slug, "commercial_exit": commercial_exit,
            "batches": 0 if loaded is None else loaded.batches,
            "already_loaded": 0 if loaded is None else loaded.already_loaded,
            "envelopes": 0 if loaded is None else loaded.envelopes,
            "readings_files": readings_files, "sealed_batches": len(sealed),
        }, sort_keys=True) + "\n")
    return 0


def main(argv: Sequence[str] | None = None, *, ledger: Any = None,
         load_exports: Callable[..., int] | None = None, seal_context: SealResolver | None = None) -> int:
    """`ledger`, `load_exports` and `seal_context` are injected by tests; the checks before any connection always
    run."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return _run(args, ledger, load_exports, seal_context)
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
