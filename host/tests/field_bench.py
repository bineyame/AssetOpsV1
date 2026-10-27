"""Field bench helpers (build spec 0.6 "Expect-identity file", Q-T31, Q-T50).

Stdlib only. `expect_identity_from_snapshot` writes what the poller compares
against the gateway's `identity` answer; `cohort_members` names the cohort an
`assess --cohort` call reads. The TEL-08 subcommands (`setup`, `activate`,
`read`) are added by TEL-08.
"""

from __future__ import annotations

import json
from typing import Any, Mapping


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
