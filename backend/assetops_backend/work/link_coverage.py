"""W4-01 commit 3: computable link coverage (closure 2 Q9, B9; Run 3 rulings 6-7).

`linked_coverage` is the pure reduction of adapter-supplied pinned-link selection rows into
`{state, reason, links}`. It owns no SQL and opens nothing: its `snapshot` port
(`work/adapters/postgres_work_read.py`) reads every pinned Finding/Action link and its exact selected domain read on
the caller's one read-only REPEATABLE READ connection. Cold/EV rows carry the state of the shared
`ColdReadService._snapshot` / `EvReadService._snapshot` pinned read; mini-grid rows carry the at-cutoff S3 dispatch
days and the S4 matcher pass. A missing or inconsistent pin is `UNKNOWN`/`LINK_SELECTION_MISSING`; a later head
never replaces a pinned revision or event.

Link state precedence (B9): `UNKNOWN` > `PENDING_RECOMPUTE` > `STALE_SOURCE` > `HISTORICAL` > `CURRENT`.
Coverage: `UNKNOWN` when any link is UNKNOWN, `PARTIAL` when any is pending or stale, `COMPLETE` otherwise;
reason `LINK_SELECTION_MISSING` > `LINK_WORK_PENDING` > `LINK_SOURCE_STALE`, else null.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Mapping, Protocol, Sequence
from uuid import UUID

UNKNOWN, PENDING, STALE, HISTORICAL, CURRENT = (
    "UNKNOWN", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "CURRENT")
_PRECEDENCE = (UNKNOWN, PENDING, STALE, HISTORICAL, CURRENT)
# W5-02a ruling C1: an explicit cold domain Action case link; its selected ID is the pinned Finding revision and
# its token is the same `sha256:` link-selection token as every other kind (W1 `sai1-` stays on W1 links only).
DOMAIN_ACTION = "DOMAIN_ACTION"
_REASON = {UNKNOWN: "LINK_SELECTION_MISSING", PENDING: "LINK_WORK_PENDING", STALE: "LINK_SOURCE_STALE"}

# S3 dispatch day statuses (`analytics/dispatch_read.py`) as link states.
_DISPATCH_PENDING = ("PENDING", "FAILED", "STALE_PROJECTION")
_DISPATCH_UNKNOWN = ("UNASSESSED",)


class LinkSnapshot(Protocol):
    """The adapter port: reads on the caller's open read transaction only."""

    read_at: datetime

    def link_selections(self, revision_id: str, from_: datetime | None, to: datetime | None,
                        known_at: datetime) -> list[dict[str, Any]]: ...


def worst(states: Sequence[str]) -> str:
    return next((s for s in _PRECEDENCE if s in states), CURRENT)


def _minigrid_state(pin: Mapping[str, Any]) -> str:
    """The `finding_index._day` rule per day of the pinned window, at the cutoff: an unreconstructable or
    unassessed day is UNKNOWN; a pending/failed/stale-projection day, or a CURRENT day whose selection the
    matcher pass has not covered (or deferred), is PENDING_RECOMPUTE."""
    days = pin.get("days") or []
    if not days:
        return UNKNOWN
    through = pin.get("matched_through_selection_seq")
    out = []
    for day in days:
        if not day["available"] or day["status"] in _DISPATCH_UNKNOWN or day["status"] is None:
            out.append(UNKNOWN)
        elif day["status"] in _DISPATCH_PENDING:
            out.append(PENDING)
        else:
            matched = (day["seq"] is not None and through is not None and through >= day["seq"]
                       and not day["deferred"])
            out.append(CURRENT if matched else PENDING)
    return worst(out)


def link_state(row: Mapping[str, Any], historical: bool) -> str:
    pin = row.get("pin")
    if pin is None:
        return UNKNOWN
    raw = _minigrid_state(pin) if row["domain"] == "mini_grid" else pin.get("state", UNKNOWN)
    if raw not in _PRECEDENCE:
        raw = UNKNOWN
    if raw in (UNKNOWN, PENDING, STALE):
        return raw
    return HISTORICAL if historical else CURRENT


def _plain(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _token(row: Mapping[str, Any], state: str) -> str | None:
    if row.get("pin") is None:
        return None
    basis = {"version": "work-link-selection/1", "kind": row["kind"], "id": row["id"],
             "selected_id": row["selected_id"], "domain": row["domain"], "pin": _plain(row["pin"]), "state": state}
    digest = hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def linked_coverage(snapshot: LinkSnapshot, tenant_id: UUID, site_id: UUID, revision_id: str,
                    from_: datetime | None, to: datetime | None, known_at: datetime) -> dict[str, Any]:
    """Q9: `{state, reason, links:[{kind,id,selected_id,selection_token,state}]}` for the selected case revision's
    pinned links. `from_`/`to` is the list window; detail passes none (each pinned Finding's own window).
    HISTORICAL marks an explicit cutoff earlier than the snapshot's read time, below any failure."""
    historical = known_at < snapshot.read_at
    links = []
    for row in snapshot.link_selections(revision_id, from_, to, known_at):
        state = link_state(row, historical)
        links.append({"kind": row["kind"], "id": row["id"], "selected_id": row["selected_id"],
                      "selection_token": _token(row, state), "state": state})
    links.sort(key=lambda x: (x["kind"], x["id"], x["selected_id"]))
    state, reason = coverage_of([x["state"] for x in links])
    return {"state": state, "reason": reason, "links": links}


def coverage_of(states: Sequence[str]) -> tuple[str, str | None]:
    """B9 coverage over link states (shared by detail and the commit-4 list)."""
    if UNKNOWN in states:
        return "UNKNOWN", _REASON[UNKNOWN]
    if PENDING in states:
        return "PARTIAL", _REASON[PENDING]
    if STALE in states:
        return "PARTIAL", _REASON[STALE]
    return "COMPLETE", None
