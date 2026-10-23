"""W4-01 commit 3: the work-case detail read (B3 `work-case-detail-1`; Run 3 ruling 8).

One read-only REPEATABLE READ snapshot (`WorkReads.snapshot`, `work/adapters/postgres_work_read.py`) supplies the
DB read time once; an omitted `known_at` is that instant, a later one is 422 `INVALID_KNOWN_AT`. The case is
selected for the scoped tenant/Site with `created_at <= known_at` (else 404 `WORK_CASE_NOT_FOUND`, never
disclosing whether it exists elsewhere); its latest revision, event prefix and records with
`recorded_at <= known_at`, ordered and tied by `(recorded_at, id)`. Provenance is Q11 through the shared
`PublicProvenance`; coverage is Q9 `linked_coverage` on the same connection.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Protocol, Sequence
from uuid import UUID

from assetops_backend.work import model as m
from assetops_backend.work.link_coverage import linked_coverage
from assetops_backend.work.model import WorkRefused
from assetops_backend.work.service import case_provenance


class WorkReads(Protocol):
    def snapshot(self, tenant_id: UUID, site_id: UUID, site_code: str, work: Callable[[Any], Any]) -> Any: ...


def parse_known_at(values: Sequence[str]) -> datetime | None:
    """The optional single `known_at` query value as a UTC instant; repeated or invalid is INVALID_KNOWN_AT."""
    if not values:
        return None
    if len(values) != 1:
        raise WorkRefused("INVALID_KNOWN_AT")
    try:
        return m.utc_instant(values[0])
    except WorkRefused:
        raise WorkRefused("INVALID_KNOWN_AT") from None


def _uuid(value: Any) -> str | None:
    return None if value is None else str(value)


def select_case_detail(rx: Any, tenant_id: UUID, site_id: UUID, site_code: str, case_id: str,
                       known_at: datetime) -> dict[str, Any]:
    """W6-01c C1: the `work-case-detail-1` body of one scoped case at `known_at`, on the caller's snapshot `rx`.
    Shared by the W4 Site route and the W6 global request route, each inside its own snapshot."""
    cid = case_id
    case = rx.case(cid, known_at)
    if case is None:
        raise WorkRefused("WORK_CASE_NOT_FOUND")
    revisions = rx.revisions(cid, known_at)
    if not revisions:
        raise WorkRefused("WORK_CASE_NOT_FOUND")
    revision = revisions[-1]
    events = rx.events(cid, known_at)
    records = rx.records(cid, known_at)
    links = rx.revision_links(str(revision["id"]))
    provenance = case_provenance(rx, tenant_id, site_id, links, str(revision["id"]),
                                 [str(e["id"]) for e in events],
                                 str(records[-1]["id"]) if records else None)
    coverage = linked_coverage(rx, tenant_id, site_id, str(revision["id"]), None, None, known_at)
    return {
        "schema_version": m.SCHEMA_DETAIL, "site_code": site_code,
        "case": {"id": str(case["id"]), "code": case["public_code"], "kind": case["kind"],
                 "asset_id": _uuid(case["asset_id"]), "occurred_at": m.iso(case["occurred_at"]),
                 "created_at": m.iso(case["created_at"]), "state": m.reduce_state(case["kind"], events),
                 "incident_id": _uuid(case["incident_id"])},
        "selected_revision": {
            "id": str(revision["id"]), "revision_no": revision["revision_no"],
            "supersedes_revision_id": _uuid(revision["supersedes_revision_id"]), "title": revision["title"],
            "narrative": revision["narrative"], "reason": revision["reason"],
            "recorded_at": m.iso(revision["recorded_at"]), "actor_kind": revision["actor_kind"],
            "actor_id": revision["actor_id"], "occurred_at": m.iso(revision["occurred_at"])},
        "finding_links": sorted(links["finding_links"], key=lambda x: (x["finding_id"], x["finding_revision_id"])),
        "action_links": sorted(links["action_links"], key=lambda x: (x["action_id"], x["action_event_id"])),
        "cited_accepted_evidence_ids": sorted(links["evidence_ids"]),
        "events": [{"id": str(e["id"]), "kind": e["kind"], "payload": e["payload"],
                    "occurred_at": m.iso(e["occurred_at"]), "recorded_at": m.iso(e["recorded_at"]),
                    "actor_kind": e["actor_kind"], "actor_id": e["actor_id"]} for e in events],
        "records": [{"id": str(r["id"]), "activity": r["activity"], "outcome_note": r["outcome_note"],
                     "occurred_at": m.iso(r["occurred_at"]), "recorded_at": m.iso(r["recorded_at"]),
                     "supersedes_record_id": _uuid(r["supersedes_record_id"])} for r in records],
        "source_provenance": provenance,
        "coverage": {"state": coverage["state"], "reason": coverage["reason"]},
    }


class WorkDetailService:
    def __init__(self, reads: WorkReads) -> None:
        self._reads = reads

    def detail(self, tenant_id: UUID, site_id: UUID, site_code: str, case_id: str,
               known_values: Sequence[str]) -> dict[str, Any]:
        requested = parse_known_at(known_values)
        try:
            cid = m.uuid_text(case_id)
        except WorkRefused:
            raise WorkRefused("WORK_CASE_NOT_FOUND") from None

        def work(rx: Any) -> dict[str, Any]:
            if requested is not None and requested > rx.read_at:
                raise WorkRefused("INVALID_KNOWN_AT")
            known_at = rx.read_at if requested is None else requested
            return select_case_detail(rx, tenant_id, site_id, site_code, cid, known_at)

        return self._reads.snapshot(tenant_id, site_id, site_code, work)
