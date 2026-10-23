"""W6-01a/b: the global work list roots (`global-work-index-1`): A1 `GET /api/work/incidents`; B1
`GET /api/work/maintenance` and `GET /api/work/preventive`; E1 `GET /api/work/operational-records` (selection in
`work/operational_index.py`, kind filter bound in the cursor and token `filter`).

`.agent/W6-01-build-spec.md` section 1 (wire, parser, refusals, envelope, incident row) and section 3.1 (A1Q G2 and
the Q3-Q9 rulings). One read-only REPEATABLE READ snapshot (`PostgresGlobalWorkRead.snapshot`) at one fixed cutoff
K selects every authorized imported Site of the server's tenant (a denied candidate never enters a row, count,
digest or cursor) and every eligible case of every such Site before paging, through the per-Site W4 reads on the
same connection. Incident rows sort by `(root occurred_at desc, site_code_key asc, site_id asc, case_id asc)`,
request rows by root `created_at` in the same tuple, and draft plan rows by the selected head
`(recorded_at desc, site_code_key asc, site_id asc, canonical_plan_id asc)` (B1 pre-flight rulings P-B1-10..13).

The cursor is the W3-03 Portfolio HMAC pattern with the dedicated `ASSETOPS_WORK_CURSOR_KEY_HEX` key (bad key 503,
bad MAC or shape 422, changed scope or selection 409); W4's unsigned Site cursor is not reused. Page one's status
mode is bound in the cursor (Q4), and the page-two cutoff follows the estate wire-second rule.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable
from urllib.parse import quote
from uuid import UUID

from assetops_backend.estate.scope import MESSAGES as ESTATE_MESSAGES
from assetops_backend.estate.scope import access_basis, encode_cursor, token_time, wire_time
from assetops_backend.work import model as m
from assetops_backend.work.service import (action_event_ids, all_action_links, case_basis, missing_lineage,
                                           provenance_dto)
from assetops_backend.work.site_index import _action_link, _finding_link, action_selection_key

SCHEMA = "global-work-index-1"
SELECTION_VERSION = "global-work-selection/1"
PLAN = "PLAN"
OPERATIONAL = "operational-records"
KINDS = {"incidents": m.INCIDENT, "maintenance": m.REQUEST, "preventive": PLAN, OPERATIONAL: "OPERATIONAL_RECORD"}
_LIST_KEYS = ("from", "to", "known_at", "limit", "cursor")
KEYS = {"incidents": _LIST_KEYS, "maintenance": _LIST_KEYS, "preventive": _LIST_KEYS,
        OPERATIONAL: (*_LIST_KEYS, "kind")}  # P-E1-2: only operational records admit `kind`
# W6-01e P-E1-2: the normalized operational `kind` filter (absent and `all` are both `all`).
RECORD_KINDS = ("all", "OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT")
# A2Q1 / X1 / P-B1-11: the full-selection state counts; preventive and operational records carry null.
STATE_COUNTS = {"incidents": ("OPEN", "IN_PROGRESS", "CLOSED"),
                "maintenance": ("OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"), "preventive": None,
                OPERATIONAL: None}
MAX_DAYS = 31
DEFAULT_LIMIT, MAX_LIMIT = 50, 100
CURRENT, HISTORICAL, EMPTY_SCOPE = "CURRENT", "HISTORICAL", "EMPTY_SCOPE"
CURSOR_KEY_ENV = "ASSETOPS_WORK_CURSOR_KEY_HEX"
_HEX = frozenset("0123456789abcdefABCDEF")
_MAC_HEX = frozenset("0123456789abcdef")
_CURSOR_KEYS = {"v", "route", "filter", "tenant_id", "authorized_site_ids", "access_basis", "from", "to",
                "known_at", "page_one_mode", "selection_token", "after"}
_MODES = {"current": CURRENT, "historical": HISTORICAL}

# Section 1 refusal table: W3 parser literals for the list grammar, merged W4 literals for basis and store.
MESSAGES = {
    "UNAUTHENTICATED": ESTATE_MESSAGES["UNAUTHENTICATED"],
    "INVALID_WINDOW": ESTATE_MESSAGES["INVALID_WINDOW"],
    "INVALID_KNOWN_AT": ESTATE_MESSAGES["INVALID_KNOWN_AT"],
    "INVALID_LIMIT": ESTATE_MESSAGES["INVALID_LIMIT"],
    "INVALID_CURSOR": ESTATE_MESSAGES["INVALID_CURSOR"],
    "WORK_BASIS_CHANGED": m.MESSAGES["WORK_BASIS_CHANGED"],
    "WORK_STORE_UNAVAILABLE": m.MESSAGES["WORK_STORE_UNAVAILABLE"],
}
STATUS = {"UNAUTHENTICATED": 401, "WORK_BASIS_CHANGED": 409, "WORK_STORE_UNAVAILABLE": 503}


class GlobalWorkRefusal(Exception):
    """A typed global list refusal; the router maps it to `{"detail": {code, message, rows: null, total_count: null}}`."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code, self.status = code, STATUS.get(code, 422)
        self.detail = {"code": code, "message": MESSAGES[code], "rows": None, "total_count": None}


@dataclass(frozen=True)
class GlobalWorkRequest:
    kind: str
    from_: datetime
    to: datetime
    known_at: datetime | None
    limit: int = DEFAULT_LIMIT
    cursor: str | None = None
    record_kind: str = "all"


def _instant(value: str, code: str) -> datetime:
    """The W3 strict UTC instant (`estate/scope.py:_instant`) with this root's refusal codes."""
    raw = value.strip()
    if not raw or not (raw.endswith("Z") or raw.endswith("+00:00")):
        raise GlobalWorkRefusal(code)
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError as error:
        raise GlobalWorkRefusal(code) from error
    if parsed.utcoffset() != timedelta(0):
        raise GlobalWorkRefusal(code)
    return parsed.astimezone(timezone.utc)


def parse_global_request(kind: str, items: Iterable[tuple[str, str]]) -> GlobalWorkRequest:
    """The W3 strict parser discipline: window keys missing or repeated INVALID_WINDOW; any other repeated or unknown
    key INVALID_CURSOR. Order: window, known_at, limit, cursor envelope (the MAC verifies inside the snapshot)."""
    if kind not in KEYS:
        raise GlobalWorkRefusal("INVALID_CURSOR")
    seen: dict[str, list[str]] = {}
    for key, value in items:
        seen.setdefault(key, []).append(value)
    if any(len(seen.get(k, ())) != 1 for k in ("from", "to")):
        raise GlobalWorkRefusal("INVALID_WINDOW")
    if any(k not in KEYS[kind] or len(v) != 1 for k, v in seen.items()):
        raise GlobalWorkRefusal("INVALID_CURSOR")
    one = {k: v[0] for k, v in seen.items()}
    from_, to = _instant(one["from"], "INVALID_WINDOW"), _instant(one["to"], "INVALID_WINDOW")
    midnight = all(x.hour == x.minute == x.second == x.microsecond == 0 for x in (from_, to))
    if not midnight or from_ >= to or to - from_ > timedelta(days=MAX_DAYS):
        raise GlobalWorkRefusal("INVALID_WINDOW")
    known_at = None if "known_at" not in one else _instant(one["known_at"], "INVALID_KNOWN_AT")
    limit = DEFAULT_LIMIT
    if "limit" in one:
        raw = one["limit"].strip()
        if not raw.isdigit() or not 1 <= int(raw) <= MAX_LIMIT:
            raise GlobalWorkRefusal("INVALID_LIMIT")
        limit = int(raw)
    cursor = one.get("cursor")
    if cursor is not None:
        _envelope(cursor)
    record_kind = one.get("kind", "all")  # P-E1-2: KEYS admits `kind` on operational records only
    if record_kind not in RECORD_KINDS:  # empty, unsupported (a repeated key already failed above)
        raise GlobalWorkRefusal("INVALID_CURSOR")
    return GlobalWorkRequest(kind, from_, to, known_at, limit, cursor, record_kind)


# --- authenticated cursor (the W3-03 Portfolio pattern, `estate/scope.py:299-341`) ----------------------------

def cursor_key() -> bytes:
    """Exactly 64 ASCII hex characters (32 bytes) from the host environment, no default; missing or malformed is
    503 WORK_STORE_UNAVAILABLE. The key is never echoed, carried in a cursor or response, or logged."""
    raw = os.environ.get(CURSOR_KEY_ENV)
    if not isinstance(raw, str) or len(raw) != 64 or not set(raw) <= _HEX:
        raise GlobalWorkRefusal("WORK_STORE_UNAVAILABLE")
    return bytes.fromhex(raw)


def _mac(payload: dict[str, Any], key: bytes) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hmac.new(key, body, hashlib.sha256).hexdigest()


def encode_global_cursor(payload: dict[str, Any], key: bytes) -> str:
    return encode_cursor({**payload, "mac": _mac(payload, key)})


def _envelope(value: Any) -> dict[str, Any]:
    """Base64/JSON object with exactly the cursor key set plus a lowercase 64-hex `mac`; nothing else is trusted
    before the MAC verifies."""
    if not isinstance(value, str):
        raise GlobalWorkRefusal("INVALID_CURSOR")
    try:
        payload = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8"))
    except (binascii.Error, ValueError, UnicodeDecodeError) as error:
        raise GlobalWorkRefusal("INVALID_CURSOR") from error
    if (not isinstance(payload, dict) or set(payload) != _CURSOR_KEYS | {"mac"}
            or not isinstance(payload["mac"], str) or len(payload["mac"]) != 64
            or not set(payload["mac"]) <= _MAC_HEX):
        raise GlobalWorkRefusal("INVALID_CURSOR")
    return payload


def _canonical(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return token_time(_instant(value, "INVALID_CURSOR")) == value
    except GlobalWorkRefusal:
        return False


def _uuid(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


def decode_global_cursor(value: str, key: bytes) -> dict[str, Any]:
    """Verify the MAC with `hmac.compare_digest` before any field is used, then the shape. Else 422."""
    payload = _envelope(value)
    body = {k: v for k, v in payload.items() if k != "mac"}
    if not hmac.compare_digest(payload["mac"], _mac(body, key)):
        raise GlobalWorkRefusal("INVALID_CURSOR")
    after = body["after"]
    # P-E1-2: `filter` is null on the three case/plan routes and an allowed kind string on operational records.
    ok = (body["v"] == 1 and body["route"] in KINDS
          and (body["filter"] in RECORD_KINDS if body["route"] == OPERATIONAL else body["filter"] is None)
          and body["page_one_mode"] in _MODES
          and (body["tenant_id"] is None or _uuid(body["tenant_id"]))
          and isinstance(body["authorized_site_ids"], list) and all(_uuid(x) for x in body["authorized_site_ids"])
          and all(isinstance(body[k], str) for k in ("access_basis", "selection_token"))
          and all(_canonical(body[k]) for k in ("from", "to", "known_at"))
          and isinstance(after, list) and len(after) == 4 and _canonical(after[0])
          and isinstance(after[1], str) and _uuid(after[2]) and _uuid(after[3]))
    if not ok:
        raise GlobalWorkRefusal("INVALID_CURSOR")
    return body


# --- selection --------------------------------------------------------------------------------------------------

def _digest(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _micros(at: datetime) -> int:
    delta = at.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds


def _site_href(site_code: str) -> str:
    return f"/sites/{quote(site_code, safe='')}"


def _window_query(lo: datetime, hi: datetime, known_at: datetime) -> str:
    """A1Q Q8: the global page's `[from, to)` and the response `known_at`, URL-encoded on every page."""
    return "&".join(f"{k}={quote(wire_time(v), safe='')}" for k, v in (("from", lo), ("to", hi), ("known_at", known_at)))


def _owner(events: list[dict[str, Any]]) -> str | None:
    """Latest selected ASSIGN payload assignee (events are in `(recorded_at, id)` order), never the event actor."""
    assignee = None
    for event in events:
        if event["kind"] == "ASSIGN":
            assignee = (event["payload"] or {}).get("assignee")
    return assignee


def select_incidents(gx: Any, tenant_id: UUID, sites: list[dict[str, Any]], lo: datetime, hi: datetime,
                     known_at: datetime, cutoff: datetime | None = None) -> list[dict[str, Any]]:
    """Every eligible Incident of every authorized Site at K, before paging: `{wire, key, basis}` sorted by the
    section 1 tuple. Provenance and links follow the Site row exactly (A1Q Q3, Q7)."""
    return _select_cases(gx, tenant_id, sites, lo, hi, known_at, m.INCIDENT)


def select_maintenance(gx: Any, tenant_id: UUID, sites: list[dict[str, Any]], lo: datetime, hi: datetime,
                       known_at: datetime, cutoff: datetime | None = None) -> list[dict[str, Any]]:
    """B1: every eligible maintenance request at K (membership by root `created_at`, P-B1-1), before paging. The
    record fields are the W4 Site row's: the last selected record by `(recorded_at, id)` (P-B1-12). W6-01c C2:
    `cutoff` is K when the list request named an explicit `known_at`, else None; it decides `links.detail`'s cutoff."""
    return _select_cases(gx, tenant_id, sites, lo, hi, known_at, m.REQUEST, cutoff)


def _select_cases(gx: Any, tenant_id: UUID, sites: list[dict[str, Any]], lo: datetime, hi: datetime,
                  known_at: datetime, case_kind: str, cutoff: datetime | None = None) -> list[dict[str, Any]]:
    out = []
    query = _window_query(lo, hi, known_at)
    states = STATE_COUNTS["incidents" if case_kind == m.INCIDENT else "maintenance"]
    member = "occurred_at" if case_kind == m.INCIDENT else "created_at"
    for site in sites:
        site_id, code, name = site["site_id"], site["site_code"], site["site_name"]
        sid = str(site_id).lower()
        rx = gx.site(tenant_id, site_id, code)
        for case in rx.eligible_cases(case_kind, lo, hi, known_at):
            cid = str(case["id"]).lower()
            revision = rx.revisions(cid, known_at)[-1]
            rid = str(revision["id"])
            events = rx.events(cid, known_at)
            records = rx.records(cid, known_at)
            record = records[-1] if records else None
            record_id = None if record is None else str(record["id"])
            links = rx.revision_links(rid, known_at)
            selections = rx.link_selections(rid, lo, hi, known_at)
            by_key = {(s["kind"], s["id"], s["selected_id"]): s for s in selections}
            event_ids = sorted(str(e["id"]) for e in events)
            selected, cited = case_basis(rx, links, rid, event_ids, record_id)
            dto = provenance_dto(rx, tenant_id, site_id, cited, selected)
            if not all(s["lineage"] for s in selections):
                dto = missing_lineage(dto)
            finding_links = sorted(links["finding_links"], key=lambda x: (x["finding_id"], x["finding_revision_id"]))
            action_links = all_action_links(links)
            findings = [_finding_link(code, x, by_key.get(("FINDING", x["finding_id"], x["finding_revision_id"]),
                                                          {"lineage": False})["lineage"]) for x in finding_links]
            actions = [_action_link(code, x, by_key.get(action_selection_key(x))) for x in action_links]
            try:
                state = m.reduce_state(case_kind, events)
            except (ValueError, m.WorkRefused) as error:  # no CREATED event, or an event chain W4 cannot reduce
                raise GlobalWorkRefusal("WORK_STORE_UNAVAILABLE") from error
            if state not in states:  # P-B1-11: e.g. VERIFICATION_WINDOW is a consistency failure, never uncounted
                raise GlobalWorkRefusal("WORK_STORE_UNAVAILABLE")
            asset_label = None if case["asset_code"] is None else f"{case['asset_code']} · {case['asset_type']}"
            wire = {
                "site_code": code, "site_name": name, "site_id": sid, "site_code_key": site["site_code_key"],
                "case_id": cid, "code": case["public_code"], "kind": case_kind, "revision_id": rid,
                "title": revision["title"], "narrative": revision["narrative"],
                "occurred_at": wire_time(case["occurred_at"]), "created_at": wire_time(case["created_at"]),
                "recorded_at": wire_time(revision["recorded_at"]), "state": state,
                "owner": _owner(events), "asset_id": case["asset_id"], "asset_label": asset_label,
                "incident_id": case["incident_id"]}
            basis = {"site_id": sid, "case_id": cid, "revision_id": rid, "selected_event_ids": event_ids,
                     "selected_record_id": record_id,
                     "finding_revision_ids": sorted(x["finding_revision_id"] for x in finding_links),
                     "action_event_ids": action_event_ids(action_links),
                     "link_lineage": sorted([s["kind"], s["id"], s["selected_id"], bool(s["lineage"])]
                                            for s in selections),
                     "cited_accepted_evidence_ids": cited}
            if links.get("domain_action_links"):  # W5-02a ruling C1; W1-only and unlinked rows keep their basis
                basis["domain_action_links"] = sorted(
                    [x["action_id"], x["finding_revision_id"]] for x in links["domain_action_links"])
            site_link = {"label": name, "href": _site_href(code)}
            if case_kind == m.INCIDENT:
                requests = gx.linked_request_codes(tenant_id, site_id, cid, known_at)
                wire["linked_request_codes"] = requests
                basis["linked_request_codes"] = requests
            else:  # P-B1-12: W4 Site row parity for the latest selected record
                wire.update({"record_id": record_id, "activity": None if record is None else record["activity"],
                             "outcome_note": None if record is None else record["outcome_note"]})
            wire["finding_links"] = [{"label": x["label"], "href": x["href"]} for x in findings]
            wire["action_links"] = [{"label": x["label"], "href": x["href"]} for x in actions]
            wire["source_provenance"] = dto
            if case_kind == m.INCIDENT:
                wire["links"] = {"site": site_link,
                                 "site_incidents": {"label": "Site incidents",
                                                    "href": f"{_site_href(code)}/work/incidents?{query}"}}
            else:  # P-B1-13 label and Site fallback; W6-01c C2 (P-C2-12): the exact request Overview
                detail = f"/maintenance/requests/{quote(cid, safe='')}?site_id={quote(code, safe='')}"
                if cutoff is not None:  # P-C1-5: only an explicit cutoff is carried, at its exact instant
                    detail += f"&known_at={quote(m.iso(cutoff), safe='')}"
                wire["links"] = {"site": site_link,
                                 "site_maintenance": {"label": "Site maintenance",
                                                      "href": f"{_site_href(code)}/work/maintenance?{query}"},
                                 "detail": {"label": wire["code"], "href": detail}}
            key = (-_micros(case[member]), site["site_code_key"], sid, cid)
            marker = [token_time(case[member]), site["site_code_key"], sid, cid]
            out.append({"wire": wire, "key": key, "marker": marker, "basis": basis, "id": cid})
    out.sort(key=lambda r: r["key"])
    return out


def select_preventive(gx: Any, tenant_id: UUID, sites: list[dict[str, Any]], lo: datetime, hi: datetime,
                      known_at: datetime, cutoff: datetime | None = None) -> list[dict[str, Any]]:
    """B1 (P-B1-10): DRAFT plan roots whose root `occurred_at` is in `[from, to)` and recorded by K, each at its
    last head recorded by K (`(recorded_at, id)`); sorted by the selected head `(recorded_at desc, site_code_key,
    site_id, canonical_plan_id)`. Provenance is `provenance_dto` over `[head_id]` with no cited IDs."""
    out = []
    for site in sites:
        site_id, code, name = site["site_id"], site["site_code"], site["site_name"]
        sid = str(site_id).lower()
        rx = gx.site(tenant_id, site_id, code)
        for plan in gx.plans(tenant_id, site_id, lo, hi, known_at):
            root_id, head_id = str(plan["root_id"]).lower(), str(plan["head_id"]).lower()
            if plan["state"] != "DRAFT":  # the wire admits only DRAFT; another stored state is a consistency failure
                raise GlobalWorkRefusal("WORK_STORE_UNAVAILABLE")
            asset_id = None if plan["asset_id"] is None else str(plan["asset_id"]).lower()
            asset_label = None if plan["asset_code"] is None else f"{plan['asset_code']} · {plan['asset_type']}"
            supersedes = None if plan["supersedes_plan_id"] is None else str(plan["supersedes_plan_id"]).lower()
            dto = provenance_dto(rx, tenant_id, site_id, [], [head_id])
            wire = {
                "site_code": code, "site_name": name, "site_id": sid, "site_code_key": site["site_code_key"],
                "canonical_plan_id": root_id, "root_id": root_id, "head_id": head_id, "code": plan["root_code"],
                "title": plan["title"], "trigger_kind": plan["trigger_kind"],
                "next_due_at": None if plan["next_due_at"] is None else wire_time(plan["next_due_at"]),
                "next_due_hours": m.decimal_text(plan["next_due_hours"]), "state": plan["state"],
                "asset_id": asset_id, "asset_label": asset_label,
                "root_occurred_at": wire_time(plan["root_occurred_at"]), "occurred_at": wire_time(plan["occurred_at"]),
                "recorded_at": wire_time(plan["recorded_at"]), "supersedes_plan_id": supersedes,
                "correction_reason": plan["correction_reason"], "source_provenance": dto,
                "links": {"site": {"label": name, "href": _site_href(code)}}}
            # A1Q2 R3 standing rule: every stored value a row field reads is bound in the basis.
            basis = {"site_id": sid, "canonical_plan_id": root_id, "head_id": head_id, "asset_id": asset_id,
                     "root_code": plan["root_code"], "root_occurred_at": token_time(plan["root_occurred_at"]),
                     "root_recorded_at": token_time(plan["root_recorded_at"]), "title": plan["title"],
                     "trigger_kind": plan["trigger_kind"], "next_due_at": wire["next_due_at"],
                     "next_due_hours": wire["next_due_hours"], "state": plan["state"],
                     "occurred_at": token_time(plan["occurred_at"]), "recorded_at": token_time(plan["recorded_at"]),
                     "supersedes_plan_id": supersedes, "correction_reason": plan["correction_reason"],
                     "asset_label": asset_label, "selected_source_ids": [head_id]}
            key = (-_micros(plan["recorded_at"]), site["site_code_key"], sid, root_id)
            marker = [token_time(plan["recorded_at"]), site["site_code_key"], sid, root_id]
            out.append({"wire": wire, "key": key, "marker": marker, "basis": basis, "id": root_id})
    out.sort(key=lambda r: r["key"])
    return out


SELECT = {"incidents": select_incidents, "maintenance": select_maintenance, "preventive": select_preventive}


def _marker_key(after: list[Any]) -> tuple:
    return (-_micros(_instant(after[0], "INVALID_CURSOR")), after[1], after[2], after[3])


class GlobalWorkIndexService:
    def __init__(self, reads: Any) -> None:
        self._reads = reads

    def read(self, tenant_id: UUID | None, kind: str, request: GlobalWorkRequest,
             admit: Callable[[str], bool]) -> dict[str, Any]:
        if kind not in KINDS:
            raise GlobalWorkRefusal("INVALID_CURSOR")
        tenant = None if tenant_id is None else str(tenant_id).lower()
        record_filter = request.record_kind if kind == OPERATIONAL else None

        def work(gx: Any) -> dict[str, Any]:
            key = cursor_key()  # checked on every request, page one and an empty scope too, before any selection
            cursor = None if request.cursor is None else decode_global_cursor(request.cursor, key)
            if cursor is not None and cursor["route"] != kind:
                raise GlobalWorkRefusal("WORK_BASIS_CHANGED")
            if cursor is not None and cursor["filter"] != record_filter:  # P-E1-2: before any selection
                raise GlobalWorkRefusal("WORK_BASIS_CHANGED")
            read_at: datetime = gx.read_at
            known = request.known_at
            if known is not None and known > read_at:
                raise GlobalWorkRefusal("INVALID_KNOWN_AT")
            k = read_at if known is None else known
            if cursor is not None:
                # A1Q Q4: the cursor's six-digit cutoff is the effective K; an explicit page-two cutoff must equal
                # it exactly or be its whole-second copy; a cursor cutoff later than the read time is 409.
                cursor_k = _instant(cursor["known_at"], "INVALID_CURSOR")
                if known is not None and known != cursor_k and not (
                        known.microsecond == 0 and known == cursor_k.replace(microsecond=0)):
                    raise GlobalWorkRefusal("WORK_BASIS_CHANGED")
                if cursor_k > read_at:
                    raise GlobalWorkRefusal("WORK_BASIS_CHANGED")
                k = cursor_k
            candidates = [] if tenant_id is None else gx.imported_sites(tenant_id, request.to)
            sites = [s for s in candidates if admit(s["site_code"])]
            ids = sorted(str(s["site_id"]).lower() for s in sites)
            basis = access_basis(tenant_id, ids)
            if not sites:
                status = EMPTY_SCOPE
            elif cursor is not None:
                status = _MODES[cursor["page_one_mode"]]
            else:
                status = HISTORICAL if known is not None and known < read_at else CURRENT
            cutoff = k if request.known_at is not None else None  # W6-01c C2: the explicit cutoff only
            if not sites:
                rows = []
            elif kind == OPERATIONAL:  # W6-01e P-E1-1: the one operational dispatch; the old roots are unchanged
                from assetops_backend.work.operational_index import select_operational  # import cycle: lazy
                rows = select_operational(gx, tenant_id, sites, request.from_, request.to, k, request.record_kind,
                                          cutoff=cutoff)
            else:
                rows = SELECT[kind](gx, tenant_id, sites, request.from_, request.to, k, cutoff)
            token = _digest({"version": SELECTION_VERSION, "route": kind, "filter": record_filter, "tenant_id": tenant,
                             "authorized_site_ids": ids, "access_basis": basis, "from": token_time(request.from_),
                             "to": token_time(request.to), "known_at": token_time(k),
                             "rows": [r["basis"] for r in sorted(rows, key=lambda r: (r["basis"]["site_id"], r["id"]))]})
            after = None
            if cursor is not None:
                expected = {"tenant_id": tenant, "authorized_site_ids": ids, "access_basis": basis,
                            "from": token_time(request.from_), "to": token_time(request.to), "selection_token": token}
                if any(cursor[name] != value for name, value in expected.items()):
                    raise GlobalWorkRefusal("WORK_BASIS_CHANGED")
                after = _marker_key(cursor["after"])
            remaining = rows if after is None else [r for r in rows if r["key"] > after]
            page = remaining[:request.limit]
            next_cursor = None
            if len(remaining) > request.limit:
                mode = cursor["page_one_mode"] if cursor is not None else (
                    "historical" if status == HISTORICAL else "current")
                next_cursor = encode_global_cursor({
                    "v": 1, "route": kind, "filter": record_filter, "tenant_id": tenant, "authorized_site_ids": ids,
                    "access_basis": basis, "from": token_time(request.from_), "to": token_time(request.to),
                    "known_at": token_time(k), "page_one_mode": mode, "selection_token": token,
                    "after": page[-1]["marker"]}, key)
            empty = not sites
            names = STATE_COUNTS[kind]  # A2Q1: full selection, before paging; null on preventive
            state_counts = None if names is None else {name: sum(1 for r in rows if r["wire"]["state"] == name)
                                                       for name in names}
            if state_counts is not None and sum(state_counts.values()) != len(rows):
                raise GlobalWorkRefusal("WORK_STORE_UNAVAILABLE")  # P-B1-11
            return {
                "schema_version": SCHEMA,
                "scope": {"tenant_id": None if tenant_id is None else str(tenant_id),
                          "authorized_site_count": len(sites), "covered_site_count": len(sites),
                          "access_basis": basis},
                "window": {"from": wire_time(request.from_), "to": wire_time(request.to), "bounds": "[from, to)"},
                "known_at": wire_time(k), "status": status,
                "coverage": {"state": EMPTY_SCOPE if empty else "COMPLETE",
                             "reason": "NO_ACCESSIBLE_SITES" if empty else None,
                             "sites": [{"site_code": s["site_code"], "site_id": str(s["site_id"]), "state": "COVERED"}
                                       for s in sites]},
                "total_count": len(rows), "state_counts": state_counts, "rows": [r["wire"] for r in page], "next_cursor": next_cursor,
                "selection_token": token,
            }

        return self._reads.snapshot(work)
