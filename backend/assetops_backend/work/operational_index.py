"""W6-01e E1: the global Operational records selection behind `GET /api/work/operational-records`.

`.agent/W6-01-build-spec.md` section 1 (operational row) and the "E1-E2 pre-flight rulings" P-E1-1..8. Inside the one
read-only snapshot `gx` of `GlobalWorkIndexService.read`, every authorized Site's operational-record roots whose root
`occurred_at` is in `[from, to)` and that are recorded by K are selected at their last `(recorded_at, id)` head at K.
The root keeps its REC code and window membership; the head supplies kind, body, case, reading fields, actor, state
and the displayed occurrence. The `record_kind` filter applies to the selected head before the count, token, sort
and page slice. A non-SUBMITTED head or an unresolvable named case is a consistency failure (503), never a skipped row.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import quote
from uuid import UUID

from assetops_backend.estate.scope import token_time, wire_time
from assetops_backend.work import model as m
from assetops_backend.work.global_detail import _day_window
from assetops_backend.work.global_index import GlobalWorkRefusal, _micros, _site_href, site_link
from assetops_backend.work.service import provenance_dto

ALL = "all"
RECORD_KINDS = (ALL, "OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT")
CASE_KINDS = (m.INCIDENT, m.REQUEST)


def _q(value: str) -> str:
    return quote(value, safe="")


def _case_link(site_code: str, case_id: str, case: dict[str, Any], cutoff: datetime | None) -> dict[str, Any]:
    """P-E1-6: INCIDENT opens the Site incidents day window of the incident root occurrence; MAINTENANCE_REQUEST opens
    the exact request. Only an explicit inbound cutoff is carried, at its exact instant; the read watermark never is."""
    tail = "" if cutoff is None else f"&known_at={_q(m.iso(cutoff))}"
    if case["kind"] == m.INCIDENT:
        href = f"{_site_href(site_code)}/work/incidents?{_day_window(case['occurred_at'])}{tail}"
    else:
        href = f"/maintenance/requests/{_q(case_id)}?site_id={_q(site_code)}{tail}"
    return {"label": case["public_code"], "href": href}


def select_operational(gx: Any, tenant_id: UUID, sites: list[dict[str, Any]], lo: datetime, hi: datetime,
                       known_at: datetime, record_kind: str, *, cutoff: datetime | None = None
                       ) -> list[dict[str, Any]]:
    """Every selected operational head of every authorized Site at K whose kind matches `record_kind` (`all` admits
    every kind): `{wire, key, marker, basis, id}` sorted by the selected head `(recorded_at desc, site_code_key,
    site_id, canonical_record_id)`. `cutoff` is K when the page request named an explicit `known_at`, else None."""
    out = []
    for site in sites:
        site_id, code, name = site["site_id"], site["site_code"], site["site_name"]
        sid = str(site_id).lower()
        rx = gx.site(tenant_id, site_id, code)
        for rec in gx.operational_records(tenant_id, site_id, lo, hi, known_at):
            if rec["state"] != "SUBMITTED":  # P-E1-4: the current writer stores SUBMITTED only
                raise GlobalWorkRefusal("WORK_STORE_UNAVAILABLE")
            root_id, head_id = str(rec["root_id"]).lower(), str(rec["head_id"]).lower()
            case_id = None if rec["case_id"] is None else str(rec["case_id"]).lower()
            case_kind = case_code = case_link = None
            if case_id is not None:  # P-E1-5: same-tenant, same-Site resolution at K, else 503
                case = rx.case(case_id, known_at)
                if case is None or case["kind"] not in CASE_KINDS:
                    raise GlobalWorkRefusal("WORK_STORE_UNAVAILABLE")
                case_kind, case_code = case["kind"], case["public_code"]
                case_link = _case_link(code, case_id, case, cutoff)
            if record_kind != ALL and rec["kind"] != record_kind:
                continue
            supersedes = None if rec["supersedes_record_id"] is None else str(rec["supersedes_record_id"]).lower()
            quantity = m.decimal_text(rec["quantity"])
            dto = provenance_dto(rx, tenant_id, site_id, [], [head_id])
            wire = {
                "site_code": code, "site_name": name, "site_id": sid, "site_code_key": site["site_code_key"],
                "site_domain": site["site_type"],
                "canonical_record_id": root_id, "root_id": root_id, "head_id": head_id, "code": rec["root_code"],
                "kind": rec["kind"], "body": rec["body"], "root_occurred_at": wire_time(rec["root_occurred_at"]),
                "occurred_at": wire_time(rec["occurred_at"]), "recorded_at": wire_time(rec["recorded_at"]),
                "period_end": wire_time(rec["period_end"]), "actor_kind": rec["actor_kind"],
                "actor_id": rec["actor_id"], "quantity": quantity, "unit": rec["unit"],
                "source_document_sha256": rec["source_document_sha256"], "case_id": case_id,
                "case_kind": case_kind, "case_code": case_code, "state": rec["state"],
                "supersedes_record_id": supersedes, "correction_reason": rec["correction_reason"],
                "source_provenance": dto,
                "links": {"site": site_link(site), "case": case_link}}
            # P-E1-7 and the A1Q2 R3 standing rule: every stored value a row field reads is bound in the basis.
            basis = {"site_id": sid, "canonical_record_id": root_id, "root_id": root_id, "head_id": head_id,
                     "code": rec["root_code"], "root_occurred_at": token_time(rec["root_occurred_at"]),
                     "kind": rec["kind"], "body": rec["body"], "occurred_at": token_time(rec["occurred_at"]),
                     "recorded_at": token_time(rec["recorded_at"]), "period_end": token_time(rec["period_end"]),
                     "actor_kind": rec["actor_kind"], "actor_id": rec["actor_id"], "quantity": quantity,
                     "unit": rec["unit"], "source_document_sha256": rec["source_document_sha256"],
                     "case_id": case_id, "state": rec["state"], "supersedes_record_id": supersedes,
                     "correction_reason": rec["correction_reason"], "case_kind": case_kind, "case_code": case_code,
                     "selected_source_ids": [head_id]}
            key = (-_micros(rec["recorded_at"]), site["site_code_key"], sid, root_id)
            marker = [token_time(rec["recorded_at"]), site["site_code_key"], sid, root_id]
            out.append({"wire": wire, "key": key, "marker": marker, "basis": basis, "id": root_id})
    out.sort(key=lambda r: r["key"])
    return out
