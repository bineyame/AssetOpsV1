"""DD3d-a (D-DD.154 as amended by D-DD.168): load a world's fuel deliveries and tank dips, each at its record time.

    python -m assetops_backend.load_fuel_records --dir DIR --tenant SLUG

Reads `DIR/<slug>/fuel-records.json` (`assetops.world-fuel-records/1`, written by `world_history.py exports
--telemetry`). Each record goes through the product's operational entry (`validate_entry`, `compose_entry`,
`post_operational_record`) as the entry service, with the work store's clock at the record's own `recorded_at`: the
operator recorded it then, not when the world was loaded. The clock is a prepare clock, so
`require_prepare_database(DATABASE_URL)` is checked before anything else.

A record's identity is its `source_record_id`: the idempotency key is derived from it alone, so a re-run answers 200
and writes nothing. One JSON line on stdout: `{"tenant", "recorded", "already", "by_kind"}`. Exit 0 done; 2 a refusal
(`<CODE> <record id or -> [detail]` on stderr); records before a refused one stay. Developer diagnostics only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from assetops_backend import config
from assetops_backend.prepare_clock import PrepareClockRefused, require_prepare_database
from assetops_backend.work.model import WorkRefused
from assetops_backend.work.operational_entry import (ENTRY_PRINCIPAL, compose_entry, entry_site_context,
                                                     validate_entry)

SCHEMA = "assetops.world-fuel-records/1"
FILE_NAME = "fuel-records.json"


class FuelRecordsRefused(Exception):
    def __init__(self, code: str, record: str = "-", detail: str = "") -> None:
        super().__init__(code)
        self.code, self.record, self.detail = code, record, detail


class RecordClock:
    """The work store's clock during the load: the current record's `recorded_at`."""

    def __init__(self) -> None:
        self.now: datetime | None = None

    def __call__(self) -> datetime:
        if self.now is None:
            raise RuntimeError("no record is being loaded")
        return self.now


def read_file(directory: Path, tenant: str) -> dict[str, Any]:
    path = Path(directory) / tenant / FILE_NAME
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise FuelRecordsRefused("FUEL_RECORDS_FILE", detail=type(error).__name__) from None
    if document.get("schema") != SCHEMA:
        raise FuelRecordsRefused("FUEL_RECORDS_FILE", detail=f"schema {document.get('schema')}")
    if document.get("tenant") != tenant:
        raise FuelRecordsRefused("FUEL_RECORDS_FILE", detail=f"tenant {document.get('tenant')}")
    return document


def entry_body(record: dict[str, Any]) -> dict[str, Any]:
    key = hashlib.sha256(record["source_record_id"].encode("utf-8")).hexdigest()[:32]
    return {"entry": record["kind"], "value": record["litres"], "taken_at_local": record["taken_at_local"],
            "ticket_reference": record["ticket_reference"], "idempotency_key": f"oprec-entry-{key}"}


def _load(document: dict[str, Any], scopes: dict[str, tuple[UUID, UUID]], service: Any, clock: RecordClock,
          site_context: Callable[[UUID, UUID], tuple[str, str | None]]) -> tuple[dict[int, int], dict[str, int]]:
    statuses, kinds = {200: 0, 201: 0}, {}
    for site in document["sites"]:
        tenant_id, site_id = scopes[site["site_code"]]
        for record in site["records"]:
            clock.now = datetime.fromisoformat(record["recorded_at"]).astimezone(timezone.utc)
            body = entry_body(record)
            try:
                validate_entry(body)
                zone, tank_id = site_context(tenant_id, site_id)
                command = compose_entry(body, zone, tank_id, with_actor=True)
                status, _ = service.post_operational_record(tenant_id, site_id, command, ENTRY_PRINCIPAL)
            except WorkRefused as refused:
                raise FuelRecordsRefused(refused.code, record["source_record_id"]) from refused
            statuses[status] += 1
            kinds[record["kind"]] = kinds.get(record["kind"], 0) + 1
    return statuses, dict(sorted(kinds.items()))


def load_fuel_records(directory: Path, tenant: str) -> dict[str, Any]:
    """Load the tenant's file into `DATABASE_URL`; raises `PrepareClockRefused` or `FuelRecordsRefused`."""
    url = config.database_url()
    require_prepare_database(url)
    document = read_file(directory, tenant)
    from assetops_backend.evidence.composition import build_evidence_ledger
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.work.composition import build_work_store
    from assetops_backend.work.service import WorkService

    ledger, fuel, store = build_evidence_ledger(url), build_fuel_balance_store(url), build_work_store(url)
    clock = RecordClock()
    store.test_db_clock_override = clock  # this one store only; production composition never sets it
    try:
        scopes = {}
        for site in document["sites"]:
            scope = ledger.site_scope(tenant, site["site_code"])
            if scope is None:
                raise FuelRecordsRefused("FUEL_RECORDS_SITE", detail=site["site_code"])
            scopes[site["site_code"]] = scope
        statuses, kinds = _load(document, scopes, WorkService(store), clock, entry_site_context(fuel.night_context))
    finally:
        fuel.dispose()
        store.dispose()
    return {"tenant": tenant, "recorded": statuses[201], "already": statuses[200], "by_kind": kinds}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.load_fuel_records",
                                     description="Load a world's fuel deliveries and tank dips.")
    parser.add_argument("--dir", required=True, type=Path, help="the directory `exports --telemetry` wrote")
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args(argv)
    try:
        result = load_fuel_records(args.dir, args.tenant)
    except PrepareClockRefused as refused:
        print(refused, file=sys.stderr)
        return 2
    except FuelRecordsRefused as refused:
        print(refused.code, refused.record, *([refused.detail] if refused.detail else []), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
