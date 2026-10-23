"""W6-01c C1: the exact global work request detail (`global-work-detail-1`; `.agent/W6-01-build-spec.md` section 1
Detail DTO and the "C1-C3 pre-flight rulings", paragraph "C1 outer wire and selection").

`GlobalWorkDetailService.detail` runs after the route has authenticated, validated one `site_id`, authorized and
scoped that Site. It parses the case UUID (malformed is 404 `WORK_CASE_NOT_FOUND`) and the optional single
`known_at` (W4 `INVALID_KNOWN_AT`) before any store read, then reads everything in one read-only snapshot of the
global reader:

- `effective_known_at` is chosen once: the requested instant at full microsecond precision, or the snapshot read
  time; every nested and outer selection uses it and `selected.known_at` serializes it with six digits and `Z`.
- `work_detail` is the W4 `work-case-detail-1` body from the shared `select_case_detail` (Site parity). Only a
  MAINTENANCE_REQUEST is served; an INCIDENT, absent or out-of-scope case is 404. A case with no CREATED event is a
  503 consistency failure decided here, never in the shared selector (the Site route stays unchanged).
- `history.revisions` are the case revisions at the cutoff; `history.operational_records` are the operational
  record roots whose immutable root `case_id` is this request, with each root's latest head at the cutoff.
- outer `links`: the Site (stored name read in the same snapshot), the canonical Overview / Maintenance record /
  History values, the source incident (root occurrence day window), and lineage-true exact Finding/Action links
  (`link_selections(revision, None, None, K)`, no analytic window). Generated URLs carry `known_at` only when the
  request supplied one, as that exact instant.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from urllib.parse import quote
from uuid import UUID

from assetops_backend.work import model as m
from assetops_backend.work.detail import parse_known_at, select_case_detail
from assetops_backend.work.model import WorkRefused, WorkStoreUnavailable
from assetops_backend.work.site_index import _action_link, _finding_link

SCHEMA_GLOBAL_DETAIL = "global-work-detail-1"


def _q(value: str) -> str:
    return quote(value, safe="")


def _day_window(at: datetime) -> str:
    """`from` and `to` of the UTC day holding `at`, whole seconds with `Z`, URL encoded."""
    lo = at.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return "&".join(f"{k}={_q(v.strftime('%Y-%m-%dT%H:%M:%SZ'))}" for k, v in (("from", lo),
                                                                               ("to", lo + timedelta(days=1))))


def _has_created(events: Sequence[dict[str, Any]]) -> bool:
    return any(e["kind"] == "CREATED" for e in events)


class GlobalWorkDetailService:
    def __init__(self, reads: Any) -> None:
        self._reads = reads

    def detail(self, tenant_id: UUID, site_id: UUID, site_code: str, case_id: str,
               known_values: Sequence[str]) -> dict[str, Any]:
        try:
            cid = m.uuid_text(case_id)
        except WorkRefused:
            raise WorkRefused("WORK_CASE_NOT_FOUND") from None
        requested = parse_known_at(known_values)

        def work(gx: Any) -> dict[str, Any]:
            if requested is not None and requested > gx.read_at:
                raise WorkRefused("INVALID_KNOWN_AT")
            known_at = gx.read_at if requested is None else requested
            rx = gx.site(tenant_id, site_id, site_code)
            try:
                work_detail = select_case_detail(rx, tenant_id, site_id, site_code, cid, known_at)
            except ValueError as error:
                # The shared W4 state reduction refuses a case with no CREATED event; here that is a 503.
                if not _has_created(rx.events(cid, known_at)):
                    raise WorkStoreUnavailable("A work request has no CREATED event.") from error
                raise
            case = work_detail["case"]
            if case["kind"] != m.REQUEST:
                raise WorkRefused("WORK_CASE_NOT_FOUND")
            if not _has_created(work_detail["events"]):
                raise WorkStoreUnavailable("A work request has no CREATED event.")
            return _body(gx, rx, tenant_id, site_id, site_code, cid, known_at, requested is not None, work_detail)

        return self._reads.snapshot(work)


def _body(gx: Any, rx: Any, tenant_id: UUID, site_id: UUID, site_code: str, cid: str, known_at: datetime,
          explicit: bool, work_detail: dict[str, Any]) -> dict[str, Any]:
    case = work_detail["case"]
    revision_id = work_detail["selected_revision"]["id"]
    cutoff = f"&known_at={_q(m.iso(known_at))}" if explicit else ""
    site_href = f"/sites/{_q(site_code)}"

    selections = rx.link_selections(revision_id, None, None, known_at)
    by_key = {(s["kind"], s["id"], s["selected_id"]): s for s in selections}
    findings = [_finding_link(site_code, x, by_key.get(("FINDING", x["finding_id"], x["finding_revision_id"]),
                                                       {"lineage": False})["lineage"])
                for x in work_detail["finding_links"]]
    actions = [_action_link(site_code, x, by_key.get(("ACTION", x["action_id"], x["action_event_id"])))
               for x in work_detail["action_links"]]

    source_incident = None
    if case["incident_id"] is not None:
        incident = rx.case(case["incident_id"], known_at)
        if incident is not None and incident["kind"] == m.INCIDENT and rx.revisions(case["incident_id"], known_at):
            source_incident = {"label": f"Incident {incident['public_code']}",
                               "href": f"{site_href}/work/incidents?{_day_window(incident['occurred_at'])}{cutoff}"}

    operational = sorted(({
        "canonical_record_id": r["canonical_record_id"], "head_id": r["head_id"], "code": r["code"],
        "kind": r["kind"], "body": r["body"], "root_occurred_at": m.iso(r["root_occurred_at"]),
        "occurred_at": m.iso(r["occurred_at"]), "recorded_at": m.iso(r["recorded_at"])}
        for r in gx.case_operational_records(tenant_id, site_id, cid, known_at)),
        key=lambda x: (x["root_occurred_at"], x["canonical_record_id"]))
    revisions = [{"id": str(v["id"]), "revision_no": v["revision_no"],
                  "supersedes_revision_id": None if v["supersedes_revision_id"] is None
                  else str(v["supersedes_revision_id"]),
                  "title": v["title"], "reason": v["reason"], "occurred_at": m.iso(v["occurred_at"]),
                  "recorded_at": m.iso(v["recorded_at"]), "actor_kind": v["actor_kind"], "actor_id": v["actor_id"]}
                 for v in rx.revisions(cid, known_at)]

    request = f"/maintenance/requests/{_q(cid)}"
    query = f"?site_id={_q(site_code)}{cutoff}"
    return {
        "schema_version": SCHEMA_GLOBAL_DETAIL,
        "selected": {"site_code": site_code, "site_id": str(site_id), "case_id": cid, "case_code": case["code"],
                     "case_kind": case["kind"], "known_at": m.iso(known_at)},
        "work_detail": work_detail,
        "work_asset": None if case["asset_id"] is None else gx.asset(tenant_id, site_id, case["asset_id"]),
        "history": {"revisions": revisions, "operational_records": operational},
        "links": {
            "site": {"label": rx.site_name(), "href": site_href},
            "overview": {"label": "Overview", "href": f"{request}{query}"},
            "record": {"label": "Maintenance record", "href": f"{request}/record{query}"},
            "history": {"label": "History", "href": f"{request}/history{query}"},
            "source_incident": source_incident,
            "findings": [{"label": x["label"], "href": x["href"]} for x in findings],
            "actions": [{"label": x["label"], "href": x["href"]} for x in actions],
        },
    }
