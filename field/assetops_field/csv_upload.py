"""UP-1 (rev 7 section 7.5, D-17N.5): the reading-upload side of the illustrative CSV collector, as a process.

`field/` may be imported only by itself and `host/tests` (dependency-direction guard, TEL-01 ruling D4), so the
API reaches this module by running it, never by importing it:

    python -m assetops_field.csv_upload check --profile P --file F
    python -m assetops_field.csv_upload send --profile P --file F --gateway-address A --ipc-credential C \
        --snapshot-sha256 S --expect-identity E

`check` validates the whole file with `CsvCollector` (no IPC) and prints one JSON object: the dry-run preview, or
the refusal (one of the eight `CSV_CODES`, its field and detail). `send` runs the same validation, then one
`CsvCollector.collect` through the gateway channel (admit in file order, seal, release), and prints the admission
counts. Exit codes: 0 done, 2 the file is refused, 3 configuration refused, 4 gateway unavailable, 5 the gateway is
not the one configured (identity mismatch), 6 the gateway refused the request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from assetops_gateway.ipc import GatewayLink, GatewayRequestRefused, GatewayUnavailable

from assetops_field.export_csv import FORMAT, CsvCollector, CsvRefused
from assetops_field.profile import FieldProfile, ProfileRefused, load_profile
from assetops_field.publish import GatewayPublisher, IdentityMismatch

EXIT_OK, EXIT_REFUSED, EXIT_CONFIG, EXIT_UNAVAILABLE, EXIT_IDENTITY, EXIT_GATEWAY_REFUSED = 0, 2, 3, 4, 5, 6
#: The preview lists at most this many blank instants per column; `blanks` always carries the full count.
BLANK_TIMES_SHOWN = 24


class _NoGateway:
    """`check` builds the collector with no channel; any IPC from it is a defect."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"the dry run touched the gateway channel ({name})")


def preview(profile: FieldProfile, data: bytes) -> dict[str, Any]:
    """Validate `data` whole; return the dry-run preview. Raises `CsvRefused` (nothing is admitted either way)."""
    collector = CsvCollector(profile, _NoGateway())  # type: ignore[arg-type]
    reports = collector.reports_from_bytes(data)
    by_identity = {(row.device_id, row.signal_id): row for row in profile.rows}
    columns: dict[str, dict[str, Any]] = {}
    first_end: dict[str, str] = {}
    for report in reports:
        row = by_identity[(report.device_id, report.signal_id)]
        column = columns.setdefault(row.row_id, {
            "row_id": row.row_id, "column": row.csv.column if row.csv else None, "unit": report.unit,
            "profile_unit": row.source_unit, "unit_matches": report.unit == row.source_unit, "role": row.role,
            "device_id": row.device_id, "signal_id": row.signal_id, "readings": 0, "blanks": 0, "blank_times": []})
        if report.quality == "GOOD":
            column["readings"] += 1
        else:
            column["blanks"] += 1
            if len(column["blank_times"]) < BLANK_TIMES_SHOWN:
                column["blank_times"].append(report.source_time)
        # Rows are strictly increasing, so the first report of a role carries its earliest interval end.
        first_end.setdefault(row.role, report.source_time)
    ordered = [columns[row.row_id] for row in profile.rows if row.row_id in columns]
    rows = len(reports) // len(ordered)
    return {
        "format": FORMAT, "profile_id": profile.profile_id, "profile_sha256": profile.sha256,
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "period_start": min(r.interval_start for r in reports if r.interval_start is not None),
        "period_end": max(r.source_time for r in reports),
        "span_seconds": collector.span_seconds, "rows": rows, "cells": len(reports),
        "readings": sum(c["readings"] for c in ordered), "blanks": sum(c["blanks"] for c in ordered),
        "columns": ordered, "first_interval_end_by_role": dict(sorted(first_end.items())),
    }


def refusal(refused: CsvRefused) -> dict[str, Any]:
    return {"code": refused.code, "field": refused.field, "detail": refused.detail,
            "profile_sha256": refused.profile_sha256}


def send(profile: FieldProfile, path: Path, publisher: GatewayPublisher) -> dict[str, Any]:
    """`CsvCollector.collect` (validate whole, admit in file order, seal and release); the summary the API keeps."""
    collector = CsvCollector(profile, publisher)
    result = collector.collect(path)
    # The admissions answer the reports one for one, in file order (`collect`), so each hold names its column.
    rows = {(row.device_id, row.signal_id): row.row_id for row in profile.rows}
    reports = collector.reports_from_bytes(path.read_bytes())
    outcomes = Counter(a["outcome"] for a in result["admissions"])
    held = Counter(f"{rows[(r.device_id, r.signal_id)]}:{a.get('kind')}:{a.get('field')}"
                   for r, a in zip(reports, result["admissions"]) if a["outcome"] == "HELD")
    return {"profile_sha256": result["profile_sha256"], "file_sha256": result["file_sha256"],
            "session_ref": result["session_ref"], "report_count": result["report_count"],
            "outcomes": dict(sorted(outcomes.items())), "held": dict(sorted(held.items())),
            "message_ids": [a.get("message_id") for a in result["admissions"]],
            "batch_ids": list(result["sealed"]["batch_ids"]), "seal_refused": result["sealed"]["seal_refused"]}


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m assetops_field.csv_upload")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--profile", required=True, type=Path)
    check.add_argument("--file", required=True, type=Path)
    send_p = sub.add_parser("send")
    send_p.add_argument("--profile", required=True, type=Path)
    send_p.add_argument("--file", required=True, type=Path)
    send_p.add_argument("--gateway-address", required=True)
    send_p.add_argument("--ipc-credential", required=True, type=Path)
    send_p.add_argument("--snapshot-sha256", required=True)
    send_p.add_argument("--expect-identity", required=True, type=Path)
    return parser.parse_args(argv)


def _emit(document: dict[str, Any]) -> None:
    print(json.dumps(document, sort_keys=True), flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = _arguments(argv)
    try:
        profile = load_profile(args.profile)
        if profile.interface != "EXPORT_CSV":
            raise ProfileRefused(f"profile interface {profile.interface} is not EXPORT_CSV")
        data = args.file.read_bytes()
    except (ProfileRefused, OSError) as refused:
        _emit({"ok": False, "error": "CONFIGURATION", "detail": str(refused)})
        return EXIT_CONFIG
    try:
        checked = preview(profile, data)
    except CsvRefused as refused:
        _emit({"ok": False, "refusal": refusal(refused)})
        return EXIT_REFUSED
    if args.command == "check":
        _emit({"ok": True, "preview": checked})
        return EXIT_OK
    try:
        if not re.fullmatch(r"[0-9a-f]{64}", args.snapshot_sha256):
            raise ProfileRefused("--snapshot-sha256 is 64 lowercase hex digits")
        from assetops_field.modbus_poller import new_session_ref

        expected = json.loads(args.expect_identity.read_text(encoding="utf-8"))
        publisher = GatewayPublisher(GatewayLink(args.gateway_address, args.ipc_credential), args.snapshot_sha256,
                                     new_session_ref(profile, datetime.now(timezone.utc)), expected)
        publisher.check_identity()
        sent = send(profile, args.file, publisher)
    except GatewayUnavailable as unavailable:
        _emit({"ok": False, "error": "GATEWAY_UNAVAILABLE", "detail": str(unavailable)})
        return EXIT_UNAVAILABLE
    except IdentityMismatch as mismatch:
        _emit({"ok": False, "error": "IDENTITY_MISMATCH", "detail": str(mismatch)})
        return EXIT_IDENTITY
    except GatewayRequestRefused as refused:
        _emit({"ok": False, "error": "GATEWAY_REFUSED", "detail": str(refused)})
        return EXIT_GATEWAY_REFUSED
    except (ProfileRefused, OSError, json.JSONDecodeError, KeyError) as refused:
        _emit({"ok": False, "error": "CONFIGURATION", "detail": str(refused)})
        return EXIT_CONFIG
    _emit({"ok": True, "preview": checked, "sent": sent})
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
