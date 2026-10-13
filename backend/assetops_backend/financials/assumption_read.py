"""Site financial assumption reads (S4-02a phase 2, packet item 3).

Exact and at-recorded-cutoff selection over the stored assumption history. Both time axes are half-open:
a price whose valid range ends at `t` does not cover `t`, one that begins at `t` does; a cutoff `c` selects
the assignments with `recorded_from <= c < recorded_to` (current: `recorded_to IS NULL`). A cutoff selects
stored assumption knowledge only: it is never an arbitrary S3 `knowledge_at` replay.

No default price, tenant fallback or inferred amount exists here: an uncovered instant is `NO_PRICE`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.financials.assumptions import ASSUMPTION_KEYS, UNIT

PAGE_LIMIT = 200
CUTOFF_BASIS = ("A recorded cutoff selects the Site assumption history as it was stored at that instant; it does "
                "not replay any other knowledge (no S3 knowledge_at replay).")


class AssumptionRows(Protocol):
    def snapshot(self, tenant_id: UUID, site_id: UUID, key: str, recorded_at: datetime | None,
                 after_revision_no: int, limit: int) -> dict[str, Any]: ...

    def revision_detail(self, tenant_id: UUID, site_id: UUID, revision_id: UUID) -> dict[str, Any] | None: ...


def _range(lo: datetime, hi: datetime | None) -> dict[str, Any]:
    return {"from": lo, "to": hi, "bounds": "[)"}


def revision_view(r: dict[str, Any]) -> dict[str, Any]:
    """One stored price revision. `value` is the authored decimal as a string, never a float."""
    return {
        "revision_id": r["id"], "revision_no": r["revision_no"], "prior_revision_id": r["prior_revision_id"],
        "assumption_key": r["assumption_key"], "value": str(r["value"]), "currency": r["currency"],
        "unit": r["unit"], "basis": r["basis"], "source_reference": r["source_reference"],
        "authored_valid": _range(r["valid_from"], r["valid_to"]), "recorded_at": r["recorded_at"],
        "change_kind": r["change_kind"], "correction_reason": r["correction_reason"],
        "actor": {"kind": r["actor_kind"], "id": r["actor_id"], "author_id": r["author_id"]},
        "channel": r["channel"], "authorization_basis": r["authorization_basis"], "provenance": r["provenance"],
        "idempotency_key": r["idempotency_key"], "request_sha256": r["request_sha256"],
    }


def assignment_view(a: dict[str, Any]) -> dict[str, Any]:
    return {"assignment_id": a["id"], "revision_id": a["revision_id"],
            "publication_revision_id": a["publication_revision_id"],
            "valid": _range(a["valid_from"], a["valid_to"]), "recorded": _range(a["recorded_from"], a["recorded_to"])}


def covers(a: dict[str, Any], at: datetime) -> bool:
    return a["valid_from"] <= at and (a["valid_to"] is None or at < a["valid_to"])


class AssumptionReadService:
    def __init__(self, rows: AssumptionRows) -> None:
        self.rows = rows

    def series(self, tenant_id: UUID, site_id: UUID, key: str, *, valid_at: datetime | None,
               recorded_at: datetime | None, after_revision_no: int = 0, limit: int = PAGE_LIMIT
               ) -> dict[str, Any]:
        limit = max(1, min(limit, PAGE_LIMIT))
        snap = self.rows.snapshot(tenant_id, site_id, key, recorded_at, after_revision_no, limit)
        cited = snap["cited"]
        timeline = [{**assignment_view(a), "price": revision_view(cited[a["revision_id"]])}
                    for a in snap["timeline"]]
        selection = None
        if valid_at is not None:
            hits = [a for a in snap["timeline"] if covers(a, valid_at)]
            if len(hits) > 1:  # the exclusion constraint forbids this; never pick one silently
                selection = {"state": "CONFLICT", "valid_at": valid_at, "revision_id": None, "assignment_id": None,
                             "conflicting_assignment_ids": [a["id"] for a in hits]}
            elif hits:
                a = hits[0]
                selection = {"state": "PRICED", "valid_at": valid_at, "revision_id": a["revision_id"],
                             "assignment_id": a["id"], **assignment_view(a),
                             "price": revision_view(cited[a["revision_id"]])}
            else:
                selection = {"state": "NO_PRICE", "valid_at": valid_at, "revision_id": None, "assignment_id": None,
                             "note": "No stored price covers this instant at the selected cutoff; no default or "
                                     "tenant price is substituted."}
        page = [revision_view(r) for r in snap["revisions"]]
        return {
            "assumption_key": key, "unit": UNIT,
            "state": "PUBLISHED" if snap["total"] else "NO_PRICE",
            "cutoff": {"recorded_at": recorded_at, "selected_by": "CURRENT" if recorded_at is None
                       else "RECORDED_CUTOFF", "basis": CUTOFF_BASIS},
            "selection": selection,
            "timeline": timeline,
            "revisions": page,
            "revision_page": {"after_revision_no": after_revision_no, "limit": limit, "total": snap["total"],
                              "next_after_revision_no": page[-1]["revision_no"]
                              if page and page[-1]["revision_no"] < max_no(snap) else None},
        }

    def revision(self, tenant_id: UUID, site_id: UUID, revision_id: UUID) -> dict[str, Any] | None:
        detail = self.rows.revision_detail(tenant_id, site_id, revision_id)
        if detail is None:
            return None
        rows = detail["assignments"]
        return {
            "selection": {"revision_id": revision_id, "selected_by": "EXACT_REVISION_ID"},
            "revision": revision_view(detail["revision"]),
            # Every assignment row that ever named this price, including closed ones: an exact ID stays stable.
            "assignments": [assignment_view(a) for a in rows if a["revision_id"] == revision_id],
            "recorded_by_this_publication": [assignment_view(a) for a in rows
                                             if a["publication_revision_id"] == revision_id],
        }


def max_no(snap: dict[str, Any]) -> int:
    """The highest revision number visible at the cutoff (revision numbers are dense from 1)."""
    return snap["total"]


def known_key(key: str) -> bool:
    return key in ASSUMPTION_KEYS
