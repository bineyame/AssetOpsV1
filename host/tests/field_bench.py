"""Field bench helpers (build spec 0.6 "Expect-identity file", Q-T31, Q-T50).

Stdlib only. `expect_identity_from_snapshot` writes what the poller compares
against the gateway's `identity` answer; `cohort_members` names the cohort an
`assess --cohort` call reads. The TEL-08 subcommands (`setup`, `activate`,
`read`) are added by TEL-08; MB-1 built `activate` and `read --what evidence|runs` (the board-only `setup`
and the provenance/assess/findings/consequences reads stay with TEL-08).

    python host/tests/field_bench.py activate --address <ipc> --credential <file> --activation <activation.json>
    python host/tests/field_bench.py read --database-url <url> --site KOBO-001 --what evidence|runs --start <Z> --end <Z>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


def expect_identity_from_snapshot(snapshot_text: str, profile_document: Mapping[str, Any],
                                  sequence_epoch: str) -> dict[str, Any]:
    """The expected identity for a profile served by the gateway a registered snapshot provisions.

    `row_sources` maps `"<device_id>/<signal_id>"` to the snapshot binding's
    source UUID for exactly the profile's rows; a row without a binding raises.
    """
    snapshot = json.loads(snapshot_text)
    bound: dict[tuple[str, str], set[str]] = {}
    for binding in snapshot["bindings"]:
        bound.setdefault((binding["device_id"], binding["signal_id"]), set()).add(binding["source_id"])
    row_sources: dict[str, str] = {}
    for row in profile_document["rows"]:
        signal = (row["device_id"], row["signal_id"])
        sources = bound.get(signal)
        if not sources:
            raise ValueError(f"profile row {row['row_id']} ({signal[0]}/{signal[1]}) has no snapshot binding")
        if len(sources) != 1:
            raise ValueError(f"profile row {row['row_id']} is bound to {len(sources)} sources")
        row_sources[f"{signal[0]}/{signal[1]}"] = next(iter(sources))
    return {
        "tenant_id": snapshot["tenant_id"],
        "site_id": snapshot["site"]["site_id"],
        "gateway_id": snapshot["gateway"]["gateway_id"],
        "source_mode": snapshot["gateway"]["mode"],
        "sequence_epoch": sequence_epoch,
        "row_sources": dict(sorted(row_sources.items())),
    }


def cohort_members(expect: Mapping[str, Any]) -> list[str]:
    """`gateway:source:epoch` for each profile source, sorted (the `assess --cohort` members)."""
    return sorted({f"{expect['gateway_id']}:{source_id}:{expect['sequence_epoch']}"
                   for source_id in expect["row_sources"].values()})


def activate(address: str, credential: Path, activation: Path) -> dict[str, Any]:
    """One `activate` over the gateway's IPC link (stdlib plus `assetops_gateway.ipc`, so it runs on a board)."""
    from assetops_gateway.ipc import GatewayLink

    document = json.loads(activation.read_text(encoding="utf-8"))
    return GatewayLink(address, credential).call("activate", {"snapshot_text": document["snapshot_text"],
                                                             "claimed": document["claimed"]})


_READS = {
    "evidence": ("SELECT e.role, e.device_id, e.signal_id, e.sequence_epoch, count(*) AS readings, "
                 "min(e.source_time) AS first, max(e.source_time) AS last FROM accepted_evidence e "
                 "JOIN site s ON s.tenant_id = e.tenant_id AND s.id = e.site_id WHERE s.site_code = :site "
                 "AND e.source_time > :start AND e.source_time <= :end "
                 "GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4"),
    "runs": ("SELECT r.analytic_id, r.selection, r.job_id IS NOT NULL AS by_job, r.window_start, r.window_end, "
             "r.knowledge_cutoff FROM analytic_run r JOIN site s ON s.tenant_id = r.tenant_id AND s.id = r.site_id "
             "WHERE s.site_code = :site AND r.window_end > :start AND r.window_start < :end ORDER BY r.window_start, 1"),
}


def read(database_url: str, site: str, what: str, start: str, end: str) -> list[dict[str, Any]]:
    """In-process reads printing one JSON document (backend imports inside): the accepted evidence per signal and
    epoch, or the analytic runs, over `(start, end]`."""
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url)
    try:
        with engine.connect() as c:
            rows = c.execute(text(_READS[what]), {"site": site, "start": start, "end": end}).mappings().all()
    finally:
        engine.dispose()
    return [dict(r) for r in rows]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="field_bench")
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("activate")
    a.add_argument("--address", required=True)
    a.add_argument("--credential", required=True, type=Path)
    a.add_argument("--activation", required=True, type=Path)
    r = sub.add_parser("read")
    r.add_argument("--database-url", required=True)
    r.add_argument("--site", default="KOBO-001")
    r.add_argument("--what", required=True, choices=sorted(_READS))
    r.add_argument("--start", required=True)
    r.add_argument("--end", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "activate":
        out: Any = activate(args.address, args.credential, args.activation)
    else:
        out = read(args.database_url, args.site, args.what, args.start, args.end)
    print(json.dumps(out, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
