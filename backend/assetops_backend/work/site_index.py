"""W4-01 commit 4: the Site Incident and Maintenance lists (`site-work-index-1`).

`.agent/W4-01-build-spec.md` "API wire and refusals" (list body, cursor), Review closure B1/B2/B8/B9/B10/S15, closure 2
Q8/Q9/Q11, Run 5 rulings r1-r5, Run 6 rulings 1-2 and Run 7 rulings q7-1..q7-5 with the commit-4 dry-read.

One read-only REPEATABLE READ snapshot (`PostgresWorkRead.snapshot`) at one fixed cutoff K selects **every**
eligible case before paging: Incidents by root `occurred_at`, maintenance requests by root `created_at`, both in
`[from, to)` and created by K. Each case's latest revision at K, its events through K (reduced in `(recorded_at, id)`
order) and its latest maintenance record at K are selected; plans and OperationalRecords never join the list.

Per pinned link the list builds Q8's `{kind, root_id, selected_id, selection_token, state}` fence on the same
connection: a mini-grid Action pin carries the exact W1 `sai1-` Action window fence (q7-2/3); a valid cold/EV pin
carries the q6 `wce1-` token; a mini-grid Finding pin has no full `sfi1-` port here, so it is null/UNKNOWN (q6-2).
The commit-3 `work-link-selection/1` detail token is never a list fence. The `work-selection/1` token hashes the
whole eligible basis (rows, events, records, citations, fences) and is recomputed on every page; any change is
409 `WORK_BASIS_CHANGED`. Status, coverage, count and source provenance are over the full eligible set.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from uuid import UUID

from assetops_backend.actions.lifecycle import ACCEPTED, Selector
from assetops_backend.actions.service import selected_action_links
from assetops_backend.actions.site_index import ActionIndexService, index_token, window_scope
from assetops_backend.work import model as m
from assetops_backend.work.detail import parse_known_at
from assetops_backend.work.link_coverage import CURRENT, HISTORICAL, UNKNOWN, coverage_of, link_state, worst
from assetops_backend.work.model import WorkRefused
from assetops_backend.work.service import case_basis, missing_lineage, provenance_dto

KINDS = {"incidents": m.INCIDENT, "maintenance": m.REQUEST}
MAX_WINDOW = timedelta(days=31)
PAGE_DEFAULT, PAGE_MAX = 50, 100
SELECTION_VERSION = "work-selection/1"
COLD_EV_VERSION = "work-cold-ev-selection/1"
COLD_EV_DOMAINS = ("cold_chain", "ev_charging")
NEXT_EVIDENCE_COPY = "No next evidence recorded"
_CURSOR_TEXT = ("tenant_id", "site_id", "kind", "from", "to", "known_at", "selection_token")


@dataclass(frozen=True)
class ListRequest:
    start: datetime
    end: datetime
    limit: int
    known_at: datetime | None
    cursor: dict[str, Any] | None


def _window(message: str) -> WorkRefused:
    return WorkRefused("INVALID_WINDOW", message)


def _utc(value: str | None, field: str) -> datetime:
    """q7-5: the W1 UTC parsing semantics (`actions/site_index.py:_utc`) with the work list's refusal codes."""
    if not value:
        raise _window(f"`{field}` is required as a UTC instant; choose a bounded window of at most 31 days.")
    try:
        parsed = datetime.fromisoformat(value.strip().replace(" ", "+").replace("Z", "+00:00"))
    except ValueError:
        raise _window(f"`{field}` is not an ISO-8601 instant.") from None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise _window(f"`{field}` must be a UTC instant (Z or +00:00).")
    return parsed.astimezone(timezone.utc)


def _instant(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(value)
    return parsed.astimezone(timezone.utc)


def encode_cursor(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8"))
        ok = (isinstance(payload, dict) and payload.get("v") == 1
              and all(isinstance(payload.get(k), str) for k in _CURSOR_TEXT)
              and isinstance(payload.get("after"), list) and len(payload["after"]) == 2
              and all(isinstance(x, str) for x in payload["after"]))
        if ok:
            for key in ("from", "to", "known_at"):
                _instant(payload[key])
            _instant(payload["after"][0])
            UUID(payload["after"][1])
    except (binascii.Error, ValueError, UnicodeDecodeError, TypeError, AttributeError):
        ok = False
    if not ok:
        raise WorkRefused("INVALID_CURSOR")
    return payload


def parse_list_request(start: str | None, end: str | None, limit: str | None, known_values: Sequence[str],
                       cursor: str | None) -> ListRequest:
    """Validated after access and Site scope (q7-5): window, then limit, then `known_at`, then cursor."""
    lo, hi = _utc(start, "from"), _utc(end, "to")
    if not lo < hi:
        raise _window("`from` must be before `to`.")
    if hi - lo > MAX_WINDOW:
        raise _window("The window may span at most 31 days.")
    if limit in (None, ""):
        size = PAGE_DEFAULT
    else:
        try:
            size = int(limit)
        except ValueError:
            size = 0
        if not 1 <= size <= PAGE_MAX:
            raise WorkRefused("INVALID_LIMIT")
    known_at = parse_known_at(known_values)
    return ListRequest(lo, hi, size, known_at, None if cursor in (None, "") else decode_cursor(cursor))


def _sha(value: Any) -> str:
    return hashlib.sha256(m.canonical_json(value).encode("utf-8")).hexdigest()


def _action_fence(rx: Any, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                  known_at: datetime) -> str | None:
    """q7-2: the exact W1 `sai1-` token of the case-list window at K on the snapshot connection, by the W1 rules
    (`ActionIndexService.fence`, `index_token`); None when unwired or the W1 read would refuse as inconsistent."""
    window = rx.action_window(lo, hi, known_at)
    if window is None:
        return None
    actions, events = window["actions"], window["events"]
    by_action: dict[str, list[dict[str, Any]]] = {str(a["id"]): [] for a in actions}
    for event in events:
        if str(event["action_id"]) not in by_action:
            return None
        by_action[str(event["action_id"])].append(event)
    if any(not any(e["kind"] == ACCEPTED for e in evs) for evs in by_action.values()):
        return None
    return index_token(window_scope(tenant_id, site_id, lo, hi), ActionIndexService.fence(actions, events))


def _cold_ev_token(tenant_id: UUID, site_id: UUID, row: Mapping[str, Any], sai1: str | None) -> str | None:
    """Run 6 ruling 1: the `wce1-` token of a valid exact cold/EV pin (an Action adds its origin and `sai1-`)."""
    pin = row["pin"]
    basis: dict[str, Any] = {
        "version": COLD_EV_VERSION, "tenant_id": str(tenant_id), "site_id": str(site_id), "kind": row["kind"],
        "root_id": row["id"], "selected_id": row["selected_id"],
        "selection_key": {"domain": row["domain"], "analytic_id": pin["analytic_id"],
                          "window_start": m.iso(pin["window_start"]), "window_end": m.iso(pin["window_end"]),
                          "selection_seq": int(pin["seq"])},
        "selection_seqs": {k: int(v) for k, v in sorted(pin["selection_seqs"].items())},
        "assessment_revision_id": str(pin["assessment_revision_id"]),
        "evidence_cutoff": m.iso(pin["evidence_cutoff"]), "state": pin["state"]}
    if row["kind"] == "ACTION":
        if sai1 is None or not row.get("origin_finding_id") or not row.get("origin_finding_revision_id"):
            return None
        basis.update({"origin_finding_id": row["origin_finding_id"],
                      "origin_finding_revision_id": row["origin_finding_revision_id"], "action_index_token": sai1})
    return "wce1-" + _sha(basis)


def link_fence(tenant_id: UUID, site_id: UUID, row: Mapping[str, Any], sai1: str | None) -> dict[str, Any]:
    """Q8's list fence for one pinned link. The state excludes HISTORICAL (the fixed K is already in the list
    token), so an omitted page-two cutoff bound by the cursor reproduces page one's basis exactly."""
    state = link_state(row, False) if row["lineage"] else UNKNOWN
    token = None
    if row["lineage"] and row["pin"] is not None and state != UNKNOWN:
        if row["domain"] == "mini_grid":
            token = sai1 if row["kind"] == "ACTION" else None  # q7-3; q6-2: no full `sfi1-` port
        elif row["domain"] in COLD_EV_DOMAINS:
            token = _cold_ev_token(tenant_id, site_id, row, sai1)
    return {"kind": row["kind"], "root_id": row["id"], "selected_id": row["selected_id"],
            "selection_token": token, "state": state if token is not None else UNKNOWN}


def _finding_link(site_code: str, link: Mapping[str, Any], lineage: bool) -> dict[str, Any]:
    fid, frev = link["finding_id"], link["finding_revision_id"]
    return {"finding_id": fid, "finding_revision_id": frev, "label": f"Finding {fid[:8]}",
            "href": f"/sites/{site_code}/findings/{fid}?revision_id={frev}" if lineage else None}


def _action_link(site_code: str, link: Mapping[str, Any], selection: Mapping[str, Any] | None) -> dict[str, Any]:
    aid, event = link["action_id"], link["action_event_id"]
    href = None
    if selection is not None and selection["lineage"]:
        action = {"id": aid, "origin_finding_id": selection["origin_finding_id"],
                  "origin_finding_revision_id": selection["origin_finding_revision_id"]}
        href = selected_action_links(site_code, action, Selector("EVENT_ID", event_id=event))["selected"]
    return {"action_id": aid, "action_event_id": event, "label": f"Action {aid[:8]}", "href": href}


def _sort_time(case: Mapping[str, Any]) -> datetime:
    return case["occurred_at"] if case["kind"] == m.INCIDENT else case["created_at"]


def select(rx: Any, tenant_id: UUID, site_id: UUID, site_code: str, kind: str, lo: datetime, hi: datetime,
           known_at: datetime, access_basis: str) -> dict[str, Any]:
    """Every eligible case at K, before paging, on the snapshot connection: sorted wire rows, the full-set fences,
    provenance and the B8 `work-selection/1` token."""
    case_kind = KINDS[kind]
    sai1 = _action_fence(rx, tenant_id, site_id, lo, hi, known_at)
    cases = sorted(sorted(rx.eligible_cases(case_kind, lo, hi, known_at), key=lambda c: str(c["id"])),
                   key=_sort_time, reverse=True)
    rows, token_rows, fences = [], [], {}
    all_selected: set[str] = set()
    all_cited: set[str] = set()
    any_missing = False
    for case in cases:
        cid = str(case["id"])
        revision = rx.revisions(cid, known_at)[-1]
        rid = str(revision["id"])
        events = rx.events(cid, known_at)
        records = rx.records(cid, known_at)
        record = records[-1] if records else None
        links = rx.revision_links(rid)
        selections = rx.link_selections(rid, lo, hi, known_at)
        by_key = {(s["kind"], s["id"], s["selected_id"]): s for s in selections}
        for s in selections:
            fence = link_fence(tenant_id, site_id, s, sai1)
            fences[m.canonical_json(fence)] = fence
        missing = not all(s["lineage"] for s in selections)
        any_missing = any_missing or missing
        event_ids = sorted(str(e["id"]) for e in events)
        record_id = None if record is None else str(record["id"])
        selected, cited = case_basis(rx, links, rid, event_ids, record_id)
        all_selected.update(selected)
        all_cited.update(cited)
        dto = provenance_dto(rx, tenant_id, site_id, cited, selected)
        if missing:
            dto = missing_lineage(dto)
        finding_links = sorted(links["finding_links"], key=lambda x: (x["finding_id"], x["finding_revision_id"]))
        action_links = sorted(links["action_links"], key=lambda x: (x["action_id"], x["action_event_id"]))
        state = m.reduce_state(case["kind"], events)
        asset_label = None if case["asset_code"] is None else f"{case['asset_code']} · {case['asset_type']}"
        row = {
            "case_id": cid, "revision_id": rid, "code": case["public_code"], "title": revision["title"],
            "narrative": revision["narrative"], "occurred_at": m.iso(case["occurred_at"]),
            "recorded_at": m.iso(revision["recorded_at"]), "state": state, "asset_id": case["asset_id"],
            "asset_label": asset_label,
            "finding_links": [_finding_link(site_code, x, by_key.get(
                ("FINDING", x["finding_id"], x["finding_revision_id"]), {"lineage": False})["lineage"])
                for x in finding_links],
            "action_links": [_action_link(site_code, x, by_key.get(("ACTION", x["action_id"], x["action_event_id"])))
                             for x in action_links],
            "url": None, "source_provenance": dto}
        if case["kind"] == m.REQUEST:
            row.update({"request_state": state, "incident_id": case["incident_id"], "record_id": record_id,
                        "activity": None if record is None else record["activity"],
                        "outcome_note": None if record is None else record["outcome_note"],
                        "outcome_state": "UNVERIFIED", "next_evidence": None,
                        "next_evidence_copy": NEXT_EVIDENCE_COPY})
        rows.append({"wire": row, "after": (_sort_time(case), cid)})
        token_rows.append({"case_id": cid, "revision_id": rid, "selected_event_ids": event_ids,
                           "selected_record_id": record_id,
                           "finding_revision_ids": sorted(x["finding_revision_id"] for x in finding_links),
                           "action_event_ids": sorted(x["action_event_id"] for x in action_links),
                           "cited_accepted_evidence_ids": cited})
    linked = sorted(fences.values(), key=lambda f: (f["kind"], f["root_id"], f["selected_id"],
                                                     m.canonical_json(f)))
    token = "sha256:" + _sha({
        "version": SELECTION_VERSION, "tenant_id": str(tenant_id), "site_id": str(site_id), "kind": kind,
        "from": m.iso(lo), "to": m.iso(hi), "known_at": m.iso(known_at), "access_basis": access_basis,
        "rows": sorted(token_rows, key=lambda r: r["case_id"]), "linked_selection_fences": linked})
    provenance = provenance_dto(rx, tenant_id, site_id, sorted(all_cited), sorted(all_selected))
    if any_missing:
        provenance = missing_lineage(provenance)
    return {"rows": rows, "linked_selection_fences": linked, "selection_token": token,
            "source_provenance": provenance, "action_index_token": sai1}


def _after(row_key: tuple[datetime, str], key: tuple[datetime, str]) -> bool:
    """True when a row sorts after `key` in `time DESC, case UUID ASC` order (r4 keyset)."""
    return row_key[0] < key[0] or (row_key[0] == key[0] and row_key[1] > key[1])


class WorkIndexService:
    def __init__(self, reads: Any) -> None:
        self._reads = reads

    def read(self, tenant_id: UUID, site_id: UUID, site_code: str, kind: str, request: ListRequest, *,
             access_basis: str) -> dict[str, Any]:
        scope = {"tenant_id": str(tenant_id), "site_id": str(site_id), "kind": kind, "from": m.iso(request.start),
                 "to": m.iso(request.end)}

        def work(rx: Any) -> dict[str, Any]:
            if request.known_at is not None and request.known_at > rx.read_at:
                raise WorkRefused("INVALID_KNOWN_AT")
            cursor = request.cursor
            if cursor is not None:
                # r4: page two uses page one's fixed K (explicit, or bound in the cursor when omitted).
                if any(cursor[k] != v for k, v in scope.items()):
                    raise WorkRefused("WORK_BASIS_CHANGED")
                if request.known_at is not None and m.iso(request.known_at) != cursor["known_at"]:
                    raise WorkRefused("WORK_BASIS_CHANGED")
                known_at = _instant(cursor["known_at"])
                if known_at > rx.read_at:
                    raise WorkRefused("WORK_BASIS_CHANGED")
            else:
                known_at = rx.read_at if request.known_at is None else request.known_at
            historical = request.known_at is not None and known_at < rx.read_at
            chosen = select(rx, tenant_id, site_id, site_code, kind, request.start, request.end, known_at,
                            access_basis)
            if cursor is not None and cursor["selection_token"] != chosen["selection_token"]:
                raise WorkRefused("WORK_BASIS_CHANGED")
            after = None if cursor is None else (_instant(cursor["after"][0]), cursor["after"][1])
            remaining = [r for r in chosen["rows"] if after is None or _after(r["after"], after)]
            page = remaining[:request.limit]
            next_cursor = None
            if len(remaining) > request.limit:
                last_time, last_id = page[-1]["after"]
                next_cursor = encode_cursor({**scope, "v": 1, "known_at": m.iso(known_at),
                                             "selection_token": chosen["selection_token"],
                                             "after": [m.iso(last_time), last_id]})
            states = [f["state"] for f in chosen["linked_selection_fences"]]
            status = worst(states) if states else CURRENT
            if status == CURRENT and historical:
                status = HISTORICAL
            coverage_state, reason = coverage_of(states)
            return {
                "schema_version": m.SCHEMA_INDEX, "site_code": site_code, "site_name": rx.site_name(),
                "window": {"from": scope["from"], "to": scope["to"], "bounds": "[from, to)"},
                "known_at": m.iso(known_at), "status": status,
                "coverage": {"state": coverage_state, "reason": reason},
                "source_provenance": chosen["source_provenance"], "total_count": len(chosen["rows"]),
                "rows": [r["wire"] for r in page], "next_cursor": next_cursor,
                "selection_token": chosen["selection_token"],
            }

        return self._reads.snapshot(tenant_id, site_id, site_code, work)
