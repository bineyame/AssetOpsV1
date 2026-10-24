"""W5-02a K1b / W5-04a V1b: the domain Action detail (cold, EV) and the Site Action union index (reads only).

`.agent/W5-02-build-spec.md` "Command/read wire", "Site Action index", "Backend wire ... (K1a-K1c)" lines K1b,
and the Architect pre-flight ruling B1-B3:

- `GET /api/sites/{site_code}/domain-work/actions/{action_id}?known_at=` -> `domain-action-intent-read-1`.
- `GET /api/sites/{site_code}/domain-work/action-index?from=&to=&known_at=&limit=&cursor=` ->
  `site-domain-action-index-1`, a union of W1 battery Actions (through `PostgresActionStore.site_window_on` and the
  W1 row projection `ActionIndexService._row`; the W1 API and its `sai1-` token are untouched) and `domain_action`
  roots, on one repeatable-read snapshot.

The index has its own parser (never W4 `parse_list_request`): window, limit, `known_at` (shape, then not after the
DB read time), cursor, each with the exact W4 literal; a valid cursor over a changed full-set fence is 409
`WORK_BASIS_CHANGED`. Default page 5 (W4 stays 50). Selection tokens are `sha256:` + 64 lowercase hex; the detail
token is the K1a intent write token recomputed by `domain_action.selection_token`. An intent declares success
conditions only: the initial unevaluated results are fixed and cite no evidence; nothing here infers `VERIFIED`.
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

from assetops_backend.actions.lifecycle import ACCEPTED
from assetops_backend.actions.site_index import ActionIndexService
from assetops_backend.work import domain_action as d
from assetops_backend.work import model as m
from assetops_backend.work.detail import parse_known_at
from assetops_backend.work.link_coverage import CURRENT, HISTORICAL, UNKNOWN, coverage_of, link_state, worst
from assetops_backend.work.model import WorkRefused, WorkStoreUnavailable
from assetops_backend.work.service import missing_lineage, provenance_dto

SCHEMA_DETAIL = "domain-action-intent-read-1"
SCHEMA_INDEX = "site-domain-action-index-1"
MAX_WINDOW = timedelta(days=31)
PAGE_DEFAULT, PAGE_MAX = 5, 100
CURSOR_KIND = "site-domain-action-index"
CURSOR_VERSION = 1
FENCE_VERSION = "site-domain-action-index/1"
W1_DOMAIN = "MINIGRID"
STATE_OPEN = "OPEN"
KIND_W1, KIND_DOMAIN = "ACTION", "DOMAIN_ACTION"
_CURSOR_TEXT = ("kind", "tenant_id", "site_id", "from", "to", "known_at", "selection_token")

#: Initial supported replay results, in criteria display order (spec "Criteria keys").
INITIAL_RESULTS = d.DOMAINS[d.DOMAIN].initial_results
#: `criterion_summary` from the selected intent's exact criterion keys (never a fixture constant); one entry per
#: closed domain contract (W5-04a pre-flight 9).
CRITERION_SUMMARY = {tuple(k for k, _, _ in spec.criteria): spec.summary for spec in d.DOMAINS.values()}


@dataclass(frozen=True)
class IndexRequest:
    start: datetime
    end: datetime
    limit: int
    known_at: datetime | None
    cursor: str | None


def _utc(value: str | None) -> datetime:
    if not value:
        raise WorkRefused("INVALID_WINDOW")
    try:
        parsed = datetime.fromisoformat(value.strip().replace(" ", "+").replace("Z", "+00:00"))
    except ValueError:
        raise WorkRefused("INVALID_WINDOW") from None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise WorkRefused("INVALID_WINDOW")
    return parsed.astimezone(timezone.utc)


def _instant(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(value)
    return parsed.astimezone(timezone.utc)


def parse_index_request(start: str | None, end: str | None, limit: str | None, known_values: Sequence[str],
                        cursor: str | None) -> IndexRequest:
    """Ruling B3, before data selection: window, limit, `known_at` shape. The future `known_at` check and the
    cursor decode follow in that order on the snapshot (`DomainActionReadService.index`)."""
    lo, hi = _utc(start), _utc(end)
    if not lo < hi or hi - lo > MAX_WINDOW:
        raise WorkRefused("INVALID_WINDOW")
    if limit in (None, ""):
        size = PAGE_DEFAULT
    else:
        try:
            size = int(limit)
        except ValueError:
            size = 0
        if not 1 <= size <= PAGE_MAX:
            raise WorkRefused("INVALID_LIMIT")
    return IndexRequest(lo, hi, size, parse_known_at(known_values), None if cursor in (None, "") else cursor)


def encode_cursor(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(value: str) -> dict[str, Any]:
    """The W4 Site cursor shape (`v`, `after`, scope, cutoff, full-set token) under this index's own kind."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8"))
        ok = (isinstance(payload, dict) and payload.get("v") == CURSOR_VERSION
              and all(isinstance(payload.get(k), str) for k in _CURSOR_TEXT) and payload["kind"] == CURSOR_KIND
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


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(m.canonical_json(value).encode("utf-8")).hexdigest()


def _iso(value: datetime | None) -> str | None:
    return None if value is None else m.iso(value)


def _after(row_key: tuple[datetime, str], key: tuple[datetime, str]) -> bool:
    """True when a row sorts after `key` in `membership DESC, action_id ASC` order."""
    return row_key[0] < key[0] or (row_key[0] == key[0] and row_key[1] > key[1])


def _head(intents: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The selected intent at the cutoff: the newest recorded version (each supersedes the then-current head)."""
    return intents[-1] if intents else None


def _summary(intent: Mapping[str, Any] | None, spec: d.DomainSpec | None = None) -> str | None:
    """The domain's summary only for its exact ordered criterion keys (W5-04 build spec "EV closure contract")."""
    if intent is None:
        return None
    keys = tuple(c.get("key") for c in intent["criteria"] or ())
    if spec is None:
        return CRITERION_SUMMARY.get(keys)
    return spec.summary if keys == tuple(k for k, _, _ in spec.criteria) else None


def _finding_domain(action: Mapping[str, Any]) -> str | None:
    """The analytics Finding domain of the Action row's stored domain (readiness 12); None outside `DOMAINS`."""
    spec = d.spec_of(action["domain"])
    return None if spec is None else spec.finding_domain


def _finding_href(site_code: str, finding_id: str, revision_id: str, selected: bool) -> str | None:
    return f"/sites/{site_code}/findings/{finding_id}?revision_id={revision_id}" if selected else None


class _Lineage:
    """Per-snapshot cache of the selected Finding pin of each pinned revision (ruling B1/B2), by the Action row's
    domain (W5-04a V1b)."""

    def __init__(self, rx: Any, known_at: datetime) -> None:
        self._rx, self._k, self._pins = rx, known_at, {}

    def resolve(self, actions: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
        revisions = self._rx.finding_revisions(
            sorted({a["origin_finding_revision_id"] for a in actions}), self._k) if actions else {}
        out = {}
        for a in actions:
            rid = a["origin_finding_revision_id"]
            if rid not in self._pins:
                rev = revisions.get(rid)
                ok = (rev is not None and rev["finding_id"] == a["origin_finding_id"]
                      and rev["domain"] == _finding_domain(a))
                self._pins[rid] = {"revision": rev if ok else None,
                                   "pin": self._rx.pin(rev, self._k) if ok else None}
            out[a["id"]] = self._pins[rid]
        return out


def _source_state(pin: Mapping[str, Any] | None, finding_domain: str | None = d.FINDING_DOMAIN) -> str:
    """The pinned Finding's source state without HISTORICAL (the cutoff is applied once, envelope-wide)."""
    return link_state({"domain": finding_domain, "pin": pin}, False)


class DomainActionReadService:
    def __init__(self, reads: Any) -> None:
        self._reads = reads

    # ---- detail -------------------------------------------------------------------------------------------

    def detail(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: str,
               known_values: Sequence[str]) -> dict[str, Any]:
        requested = parse_known_at(known_values)
        aid = d.path_action_id(action_id)

        def work(rx: Any) -> dict[str, Any]:
            if requested is not None and requested > rx.read_at:
                raise WorkRefused("INVALID_KNOWN_AT")
            known_at = rx.read_at if requested is None else requested
            historical = requested is not None and known_at < rx.read_at
            action = None if aid is None else rx.action(aid, known_at)
            if action is None:
                raise d.refuse("ACTION_NOT_FOUND")
            if action["domain"] == d.EV_DOMAIN:
                return self._ev_detail(rx, tenant_id, site_id, site_code, action, known_at, historical)
            lineage = _Lineage(rx, known_at).resolve([action])[action["id"]]
            pin = lineage["pin"]
            if pin is not None:
                # Ruling B1: the selected cold envelope on this connection must carry the pinned assessment
                # revision; its currentness is the cold source state.
                envelope = rx.envelope(pin, known_at)
                currentness = envelope.get("currentness") or {}
                chosen = (currentness.get("watermark") or {}).get("assessment_revision_ids") or []
                pin = ({**pin, "state": currentness.get("state", UNKNOWN)}
                       if str(pin["assessment_revision_id"]) in [str(x) for x in chosen] else None)
            selected = pin is not None
            intent = _head(rx.intents([action["id"]], known_at))
            states = [_source_state(pin)]
            token_case, record_id, cited, finding_revision = None, None, [], action["origin_finding_revision_id"]
            if intent is not None:
                basis = intent["basis"]
                finding_revision = basis["finding_revision_id"]
                cited = sorted(basis["accepted_evidence_ids"])
                record_id = basis["work_record_id"]
                if basis["work_case_id"] is not None:
                    token_case = rx.selected_case_link(action["id"], basis["work_case_id"], intent["recorded_at"])
                    states.append(CURRENT if token_case is not None else UNKNOWN)
            status = worst(states)
            if status == CURRENT and historical:
                status = HISTORICAL
            token = d.selection_token(tenant_id, site_id, action, finding_revision,
                                      None if intent is None else intent["id"], token_case, record_id, cited)
            ids = [action["id"], finding_revision]
            if intent is not None:
                ids.append(intent["id"])
            if token_case is not None:
                ids += [token_case["case_revision_id"], token_case["case_event_id"]]
            if record_id is not None:
                ids.append(record_id)
            provenance = provenance_dto(rx, tenant_id, site_id, cited, sorted(set(ids)))
            if not selected:
                provenance = missing_lineage(provenance)
            fid = action["origin_finding_id"]
            return {
                "schema_version": SCHEMA_DETAIL, "site_code": site_code,
                "action": {"id": action["id"], "action_code": action["action_code"], "domain": action["domain"],
                           "title": action["title"], "owner_label": action["owner_label"],
                           "due_at": _iso(action["due_at"]), "raised_at": m.iso(action["raised_at"]),
                           "recorded_at": m.iso(action["recorded_at"]), "state": STATE_OPEN},
                "known_at": m.iso(known_at), "status": status,
                "intent": None if intent is None else {
                    "id": intent["id"], "recorded_at": m.iso(intent["recorded_at"]), "criteria": intent["criteria"],
                    "basis": intent["basis"]},
                "results": None if intent is None else [
                    {"key": c["key"], "result": r, "evidence_ids": []}
                    for c, r in zip(intent["criteria"], INITIAL_RESULTS)],
                "links": {"finding": {"label": f"Finding {fid[:8]}",
                                      "href": _finding_href(site_code, fid, action["origin_finding_revision_id"],
                                                            selected)},
                          "work": self._work(rx, action["id"], known_at)},
                "source_provenance": provenance, "selection_token": token,
            }

        return self._reads.snapshot(tenant_id, site_id, site_code, work)

    @staticmethod
    def _ev_selection(rx: Any, action: Mapping[str, Any], cutoff: datetime) -> dict[str, Any] | None:
        """Readiness 27: the Action's exact EV Finding revision re-selected at `cutoff` (its run window, the pin's
        evidence cutoff and seqs) with its selected basis; None when that exact revision is not selected."""
        rid = action["origin_finding_revision_id"]
        rev = rx.finding_revisions([rid], cutoff).get(rid)
        if rev is None or rev["finding_id"] != action["origin_finding_id"] or rev["domain"] != d.EV_FINDING_DOMAIN:
            return None
        pin = rx.pin(rev, cutoff)
        if pin is None:
            return None
        ev = rx.ev_basis(pin, cutoff, rid)
        return ev if d.ev_selects_finding(ev, rid) else None

    def _ev_detail(self, rx: Any, tenant_id: UUID, site_id: UUID, site_code: str, action: Mapping[str, Any],
                   known_at: datetime, historical: bool) -> dict[str, Any]:
        """W5-04a V1b: the EV Action detail (no cold envelope). The selection cutoff is the selected intent's
        `recorded_at` bounded by the read `known_at` (readiness 27), else `known_at`; with an intent, the exact
        Finding revision, every declared session root with its selected revision and every declared citation are
        rechecked there, and any miss is 409 `DOMAIN_INTENT_BASIS_CHANGED` - no later head is substituted. Status is
        the selected EV read's own state; results are the three fixed PENDING rows citing nothing."""
        spec = d.DOMAINS[d.EV_DOMAIN]
        intent = _head(rx.intents([action["id"]], known_at))
        cutoff = known_at if intent is None else min(intent["recorded_at"], known_at)
        ev = self._ev_selection(rx, action, cutoff)
        rid = action["origin_finding_revision_id"]
        if intent is not None and (ev is None or intent["basis"]["finding_revision_id"] != rid
                                   or not d.ev_members_selected(ev, intent["basis"])):
            raise spec.refuse("DOMAIN_INTENT_BASIS_CHANGED")
        selected = ev is not None
        states = [_source_state(None if ev is None else {"state": ev["state"]}, spec.finding_domain)]
        token_case, record_id, cited, session_revisions = None, None, [], []
        if intent is not None:
            basis = intent["basis"]
            cited = sorted(basis["accepted_evidence_ids"])
            record_id = basis["work_record_id"]
            roots = {str(k).lower(): v for k, v in ev["sessions"].items()}
            session_revisions = [roots[str(s).lower()] for s in basis["session_ids"]]
            if basis["work_case_id"] is not None:
                token_case = rx.selected_case_link(action["id"], basis["work_case_id"], intent["recorded_at"])
                states.append(CURRENT if token_case is not None else UNKNOWN)
        status = worst(states)
        if status == CURRENT and historical:
            status = HISTORICAL
        token = d.selection_token(tenant_id, site_id, action, rid, None if intent is None else intent["id"],
                                  token_case, record_id, cited)
        ids = [action["id"], rid, *session_revisions]
        if intent is not None:
            ids.append(intent["id"])
        if token_case is not None:
            ids += [token_case["case_revision_id"], token_case["case_event_id"]]
        if record_id is not None:
            ids.append(record_id)
        provenance = provenance_dto(rx, tenant_id, site_id, cited, sorted(set(ids)))
        if not selected:
            provenance = missing_lineage(provenance)
        fid = action["origin_finding_id"]
        return {
            "schema_version": SCHEMA_DETAIL, "site_code": site_code,
            "action": {"id": action["id"], "action_code": action["action_code"], "domain": action["domain"],
                       "title": action["title"], "owner_label": action["owner_label"],
                       "due_at": _iso(action["due_at"]), "raised_at": m.iso(action["raised_at"]),
                       "recorded_at": m.iso(action["recorded_at"]), "state": STATE_OPEN},
            "known_at": m.iso(known_at), "status": status,
            "intent": None if intent is None else {
                "id": intent["id"], "recorded_at": m.iso(intent["recorded_at"]), "criteria": intent["criteria"],
                "basis": intent["basis"]},
            "results": None if intent is None else [
                {"key": c["key"], "result": r, "evidence_ids": []}
                for c, r in zip(intent["criteria"], spec.initial_results)],
            "links": {"finding": {"label": f"Finding {fid[:8]}",
                                  "href": _finding_href(site_code, fid, rid, selected)},
                      "work": self._work(rx, action["id"], known_at)},
            "source_provenance": provenance, "selection_token": token,
        }

    @staticmethod
    def _work(rx: Any, action_id: str, known_at: datetime) -> dict[str, Any]:
        """Ruling B3: the latest explicit linked MAINTENANCE_REQUEST by `(case_link.recorded_at DESC, case_id ASC)`
        at the cutoff; title/state from its selected revision/events, record from its selected performed record.
        `href` stays null until the W6 C2 request Overview mounts."""
        empty = {"case_id": None, "case_code": None, "case_title": None, "request_state": None, "record_id": None,
                 "label": None, "href": None}
        links = sorted((x for x in rx.case_links(action_id, known_at) if x["kind"] == m.REQUEST),
                       key=lambda x: x["case_id"])
        links.sort(key=lambda x: x["recorded_at"], reverse=True)
        if not links:
            return empty
        chosen = links[0]
        view = rx.request_view(chosen["case_id"], known_at)
        if view is None:
            return empty
        return {"case_id": chosen["case_id"], "case_code": chosen["public_code"],
                "case_title": view["revision"]["title"], "request_state": m.reduce_state(m.REQUEST, view["events"]),
                "record_id": view["record_id"], "label": f"Maintenance request {chosen['public_code']}", "href": None}

    # ---- union index --------------------------------------------------------------------------------------

    def index(self, tenant_id: UUID, site_id: UUID, site_code: str, request: IndexRequest) -> dict[str, Any]:
        scope = {"kind": CURSOR_KIND, "tenant_id": str(tenant_id), "site_id": str(site_id),
                 "from": m.iso(request.start), "to": m.iso(request.end)}

        def work(rx: Any) -> dict[str, Any]:
            if request.known_at is not None and request.known_at > rx.read_at:
                raise WorkRefused("INVALID_KNOWN_AT")
            cursor = None if request.cursor is None else decode_cursor(request.cursor)
            if cursor is not None:
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
            chosen = self._select(rx, tenant_id, site_id, site_code, request.start, request.end, known_at)
            if cursor is not None and cursor["selection_token"] != chosen["selection_token"]:
                raise WorkRefused("WORK_BASIS_CHANGED")
            after = None if cursor is None else (_instant(cursor["after"][0]), cursor["after"][1])
            remaining = [r for r in chosen["rows"] if after is None or _after(r["after"], after)]
            page = remaining[:request.limit]
            next_cursor = None
            if len(remaining) > request.limit:
                last_time, last_id = page[-1]["after"]
                next_cursor = encode_cursor({**scope, "v": CURSOR_VERSION, "known_at": m.iso(known_at),
                                             "selection_token": chosen["selection_token"],
                                             "after": [m.iso(last_time), last_id]})
            states = chosen["states"]
            status = worst(states) if states else CURRENT
            if status == CURRENT and historical:
                status = HISTORICAL
            coverage_state, reason = coverage_of(states)
            rows = chosen["rows"]
            return {
                "schema_version": SCHEMA_INDEX, "site_code": site_code,
                "window": {"from": scope["from"], "to": scope["to"], "bounds": "[from, to)"},
                "known_at": m.iso(known_at), "status": status,
                "coverage": {"state": coverage_state, "reason": reason}, "total_count": len(rows),
                "all_due_dates_unset": bool(rows) and all(r["wire"]["due_at"] is None for r in rows),
                "rows": [r["wire"] for r in page], "next_cursor": next_cursor,
                "selection_token": chosen["selection_token"],
            }

        return self._reads.snapshot(tenant_id, site_id, site_code, work)

    @staticmethod
    def _select(rx: Any, tenant_id: UUID, site_id: UUID, site_code: str, lo: datetime, hi: datetime,
                known_at: datetime) -> dict[str, Any]:
        """The full selected set before paging: W1 and domain rows, their source states and the full-set fence."""
        rows, fence, states = [], [], []
        window = rx.w1_window(lo, hi, known_at)
        by_action: dict[str, list[dict[str, Any]]] = {str(a["id"]): [] for a in window["actions"]}
        for event in window["events"]:
            if str(event["action_id"]) not in by_action:
                raise WorkStoreUnavailable("The W1 Action window was not consistent.")
            by_action[str(event["action_id"])].append(event)
        if any(not any(e["kind"] == ACCEPTED for e in evs) for evs in by_action.values()):
            raise WorkStoreUnavailable("The W1 Action window was not consistent.")
        for a in window["actions"]:
            w1 = ActionIndexService._row(tenant_id, site_id, site_code, a, by_action[str(a["id"])])
            created = a["created_at"].astimezone(timezone.utc)
            origin = w1["origin"]
            rows.append({"after": (created, w1["action_id"]), "wire": {
                "action_id": w1["action_id"], "action_code": w1["action_code"], "domain": W1_DOMAIN, "title": None,
                "owner_label": None, "due_at": None, "raised_at": m.iso(created), "recorded_at": m.iso(created),
                "origin": {"finding_id": origin["finding_id"], "finding_revision_id": origin["finding_revision_id"],
                           "label": f"Finding {origin['finding_id'][:8]}", "href": w1["links"]["origin_finding"]},
                "state": w1["state"], "criterion_summary": None,
                "links": {"action": w1["links"]["canonical"], "history": w1["links"]["history_at_event"]}}})
            fence.append((KIND_W1, w1["action_id"], m.iso(created), None, origin["finding_revision_id"]))
            states.append(CURRENT)  # ruling B2: W1 contributes CURRENT/COMPLETE
        actions = rx.actions_in_window(lo, hi, known_at)
        lineage = _Lineage(rx, known_at).resolve(actions)
        intents: dict[str, list[dict[str, Any]]] = {}
        for i in rx.intents([a["id"] for a in actions], known_at) if actions else []:
            intents.setdefault(i["action_id"], []).append(i)
        for a in actions:
            pin = lineage[a["id"]]["pin"]
            intent = _head(intents.get(a["id"], []))
            selected = pin is not None
            raised = a["raised_at"].astimezone(timezone.utc)
            fid, frev = a["origin_finding_id"], a["origin_finding_revision_id"]
            rows.append({"after": (raised, a["id"]), "wire": {
                "action_id": a["id"], "action_code": a["action_code"], "domain": a["domain"], "title": a["title"],
                "owner_label": a["owner_label"], "due_at": _iso(a["due_at"]), "raised_at": m.iso(raised),
                "recorded_at": m.iso(a["recorded_at"]),
                "origin": {"finding_id": fid, "finding_revision_id": frev, "label": f"Finding {fid[:8]}",
                           "href": _finding_href(site_code, fid, frev, selected)},
                "state": STATE_OPEN, "criterion_summary": _summary(intent, d.spec_of(a["domain"])),
                "links": {"action": f"/sites/{site_code}/actions/{a['id']}/verification", "history": None}}})
            fence.append((KIND_DOMAIN, a["id"], m.iso(raised), None if intent is None else intent["id"],
                          frev if selected else None))
            states.append(_source_state(pin, _finding_domain(a)))
        rows.sort(key=lambda r: r["after"][1])
        rows.sort(key=lambda r: r["after"][0], reverse=True)
        fence.sort(key=lambda f: f[1])
        fence.sort(key=lambda f: f[2], reverse=True)
        token = _sha({"version": FENCE_VERSION, "tenant_id": str(tenant_id), "site_id": str(site_id),
                      "from": m.iso(lo), "to": m.iso(hi), "known_at": m.iso(known_at),
                      "rows": [list(f) for f in fence]})
        return {"rows": rows, "states": states, "selection_token": token}
