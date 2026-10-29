"""S4-04 phase 1: the Site Finding index read (`I-finding-index`).

Authority: `D-2026-10-15-a-finding-index` and `D-2026-10-15-s404-contract` (full rulings in
`.agent/architect-A-finding-index-answers.md` and `.agent/architect-S4-04-answers.md`).

One scoped read over committed S4-01 Finding/FindingRevision rows: the latest revision of each canonical
Finding of one domain whose selected episode intersects the half-open UTC window `[from, to)`, ordered by
`episode_start` descending then Finding UUID ascending. It is a new read; `findings_over` (inclusive end,
ascending order) is consumed elsewhere and is not used here.

Currentness. Discovery starts with every UTC-day analytic window intersecting `[from, to)` and repeatedly
adds the adjacent UTC day across an edge that a stored canonical episode reaches within the S4 20-minute
continuity tolerance (the matcher's own neighbour dependency, `finding_episode._Site.margin_ok`), to a fixed
point, capped at `INDEX_CONTINUITY_LIMIT` distinct days (409 `INDEX_CONTINUITY_LIMIT`; the cap does not
prove continuity ended). `CURRENT` needs every inspected day's S3 selection CURRENT, the S4 match pass
through that day's selection seq, and an unchanged writer fence before/after the read. Every other status
returns no rows and a null `total_count`: S4-04 builds no durable prior snapshot, so stale or failed reads
never reconstruct historical rows from newer heads.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.analytics import dispatch as dispatch_contract
from assetops_backend.analytics.dispatch_read import CURRENT, FAILED, PENDING, STALE, UNASSESSED, DispatchReadService
from assetops_backend.analytics.dispatch_v3 import CONTINUITY_TOLERANCE
from assetops_backend.analytics.finding_episode import DOMAIN as FINDING_DOMAIN
from assetops_backend.analytics.finding_episode import MATCHER_VERSION
from assetops_backend.analytics.finding_episode import MECHANISM as FINDING_MECHANISM
from assetops_backend.outcomes.catalogue import MINI
from assetops_backend.outcomes.outcome_map import categories_for, finding_signal_key

SCHEMA_VERSION = "site-finding-index-1"
# The new API domain token resolves to stored Finding domain/analytic, the S3 dispatch discovery basis and
# the S4 matcher on that basis. Any other token is a typed 422 (never an assessed zero).
DOMAINS: dict[str, tuple[str, str]] = {"mini-grid-dispatch": (FINDING_DOMAIN, dispatch_contract.ANALYTIC_ID)}
MAX_WINDOW = timedelta(days=31)
INDEX_CONTINUITY_LIMIT = 62
PAGE_DEFAULT, PAGE_MAX = 50, 100
DISPLAY_TIMEZONE = "UTC"
ORDER = "episode_start descending, then Finding UUID ascending"
INTERSECTION = "episode_start < to and episode_end > from (a boundary touch is excluded)"
KNOWLEDGE_AT = ("Latest S3 knowledge cutoff among the inspected days' selected runs: a selection cutoff, not a "
                "commit-ordered replay point. Exact revision IDs are the audit anchors.")
AMOUNT_UNAVAILABLE = {"state": "UNAVAILABLE",
                      "reason": "No current amount: exact-revision money provenance is not in this read yet."}
_RANK = (FAILED, STALE, PENDING, UNASSESSED)


class IndexRefusal(Exception):
    """A typed refusal carrying no rows, count or empty claim."""

    status = 422

    def __init__(self, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.detail = {"code": code, "message": message, **extra}


class InvalidIndexRequest(IndexRefusal):
    status = 422


class IndexConflict(IndexRefusal):
    status = 409


class FindingIndexStore(Protocol):
    def index_snapshot(self, tenant_id: UUID, site_id: UUID, domain: str, analytic_id: str) -> dict[str, Any]: ...

    def index_lineage(self, tenant_id: UUID, site_id: UUID, revision_ids: list[UUID]) -> dict[str, Any]: ...

    def fence(self, tenant_id: UUID, site_id: UUID, analytic_id: str) -> Any: ...


@dataclass(frozen=True)
class IndexRequest:
    domain: str
    finding_domain: str
    analytic_id: str
    start: datetime
    end: datetime
    limit: int
    cursor: dict[str, Any] | None


def _utc(value: str | None, field: str) -> datetime:
    if not value:
        raise InvalidIndexRequest("INVALID_WINDOW", f"`{field}` is required as a UTC instant.", field=field)
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise InvalidIndexRequest("INVALID_WINDOW", f"`{field}` is not an ISO-8601 instant.", field=field) from None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise InvalidIndexRequest("INVALID_WINDOW", f"`{field}` must be a UTC instant (Z or +00:00).", field=field)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def encode_cursor(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(value: str) -> dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        payload = json.loads(raw.decode("utf-8"))
        ok = (isinstance(payload, dict) and payload.get("v") == 1
              and all(isinstance(payload.get(k), str) for k in ("tenant_id", "site_id", "domain", "from", "to",
                                                                "selection_token"))
              and isinstance(payload.get("after"), list) and len(payload["after"]) == 2)
        if ok:
            datetime.fromisoformat(payload["after"][0].replace("Z", "+00:00"))
            UUID(payload["after"][1])
    except (binascii.Error, ValueError, UnicodeDecodeError, TypeError, AttributeError):
        ok = False
    if not ok:
        raise InvalidIndexRequest("INVALID_CURSOR", "The cursor is not a cursor this index issued.", field="cursor")
    return payload


def parse_request(domain: str | None, start: str | None, end: str | None, limit: str | None,
                  cursor: str | None) -> IndexRequest:
    """Validate the explicit scope before any discovery. Every failure is a typed 422 with no status."""
    if domain not in DOMAINS:
        raise InvalidIndexRequest("UNSUPPORTED_DOMAIN", f"Domain {domain!r} has no Site Finding index; supported: "
                                  + ", ".join(sorted(DOMAINS)) + ".", field="domain")
    lo, hi = _utc(start, "from"), _utc(end, "to")
    if not lo < hi:
        raise InvalidIndexRequest("INVALID_WINDOW", "`from` must be before `to`.", field="from")
    if hi - lo > MAX_WINDOW:
        raise InvalidIndexRequest("INVALID_WINDOW", "The window may span at most 31 UTC days.", field="to")
    if limit in (None, ""):
        size = PAGE_DEFAULT
    else:
        try:
            size = int(limit)
        except ValueError:
            size = 0
        if not 1 <= size <= PAGE_MAX:
            raise InvalidIndexRequest("INVALID_LIMIT", f"`limit` must be an integer from 1 to {PAGE_MAX}.",
                                      field="limit")
    finding_domain, analytic_id = DOMAINS[domain]
    return IndexRequest(domain, finding_domain, analytic_id, lo, hi, size,
                        None if cursor in (None, "") else decode_cursor(cursor))


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time(0), tzinfo=timezone.utc)


def requested_days(lo: datetime, hi: datetime) -> list[date]:
    days, day = [], lo.date()
    while _day_start(day) < hi:
        days.append(day)
        day += timedelta(days=1)
    return days


def reaches(head: dict[str, Any], edge: datetime) -> bool:
    """A stored episode reaches across a UTC-day edge when it lies within the continuity tolerance of it."""
    return head["episode_start"] <= edge + CONTINUITY_TOLERANCE and head["episode_end"] >= edge - CONTINUITY_TOLERANCE


def _instant(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def candidate_reach(read: dict[str, Any], day: date) -> tuple[bool, bool]:
    """Whether a selected S3 Candidate segment of this day lies within the continuity tolerance of its start or
    end edge (phase-1 review H1). The matcher may skip such a cluster while the neighbouring day is not CURRENT and
    still record a completed pass, so no stored episode reaches the edge; the neighbour must be inspected anyway,
    and its own status/match check then blocks CURRENT."""
    lo, hi = _day_start(day), _day_start(day + timedelta(days=1))
    down = up = False
    for rev in read.get("intervals") or []:
        for seg in (rev.get("result") or {}).get("segments") or []:
            if seg.get("classification") != dispatch_contract.CANDIDATE:
                continue
            start, end = _instant(seg.get("start")), _instant(seg.get("end"))
            down = down or (start is not None and start <= lo + CONTINUITY_TOLERANCE)
            up = up or (end is not None and end >= hi - CONTINUITY_TOLERANCE)
    return down, up


def discover(heads: list[dict[str, Any]], lo: datetime, hi: datetime, limit: int = INDEX_CONTINUITY_LIMIT,
             edge_reach: Callable[[date], tuple[bool, bool]] | None = None) -> list[date]:
    """Fixed-point continuity closure over contiguous UTC days; 409 past the cap. A day edge is crossed when a
    stored episode reaches it or (`edge_reach`) when the edge day's selected S3 Candidate segments reach it."""
    days = requested_days(lo, hi)
    first, last = days[0], days[-1]
    while True:
        grow_down = (any(reaches(h, _day_start(first)) for h in heads)
                     or (edge_reach is not None and edge_reach(first)[0]))
        grow_up = (any(reaches(h, _day_start(last + timedelta(days=1))) for h in heads)
                   or (edge_reach is not None and edge_reach(last)[1]))
        if not (grow_down or grow_up):
            return [first + timedelta(days=n) for n in range((last - first).days + 1)]
        nxt = (last - first).days + 1 + int(grow_down) + int(grow_up)
        if nxt > limit:
            raise IndexConflict(
                "INDEX_CONTINUITY_LIMIT",
                f"Episode continuity reaches beyond {limit} UTC days, the service limit for one index read. "
                "This does not mean continuity ends there; request a narrower window.",
                limit_days=limit, inspected_from=first.isoformat(), inspected_to=last.isoformat(),
                rows=None, total_count=None)
        first -= timedelta(days=int(grow_down))
        last += timedelta(days=int(grow_up))


def sort_key(row: dict[str, Any]) -> tuple[float, str]:
    """Shared with S5-01 `choose`: greatest episode_start first, then the smallest Finding UUID string."""
    return (-row["episode_start"].timestamp(), str(row["finding_id"]))


def _token(payload: dict[str, Any]) -> str:
    return "sfi1-" + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


class FindingIndexService:
    def __init__(self, store: FindingIndexStore, dispatch: DispatchReadService, *,
                 continuity_limit: int = INDEX_CONTINUITY_LIMIT) -> None:
        self.store, self.dispatch, self.continuity_limit = store, dispatch, continuity_limit

    def _day(self, read: dict[str, Any], day: date, seq: int | None,
             match_pass: dict[str, Any] | None, deferred: frozenset[datetime] = frozenset()) -> dict[str, Any]:
        selection = read.get("selection") or {}
        window_rev = read.get("window_assessment") or {}
        matched = seq is not None and match_pass is not None and match_pass["matched_through_selection_seq"] >= seq
        if _day_start(day) in deferred:  # the pass deferred this window: not matched, whatever its sequence
            matched = False
        status, reasons = read["status"], list(read["status_reasons"])
        if status == CURRENT and not matched:
            status = PENDING
            reasons.append("MATCH_PENDING: no completed S4 Finding match covers this day's current S3 selection")
        return {"day": day.isoformat(), "status": status, "reasons": reasons,
                "s3": {"status": read["status"], "selection_seq": seq, "run_id": selection.get("run_id"),
                       "window_assessment_revision_id": window_rev.get("id"),
                       "model_version": selection.get("model_version"),
                       "input_sha256": selection.get("input_sha256"),
                       "configuration_sha256": selection.get("configuration_sha256"),
                       "knowledge_cutoff": selection.get("knowledge_cutoff"),
                       "selected_at": selection.get("selected_at"), "watermarks": read.get("watermarks")},
                "s4": {"matched": matched, "matcher_version": MATCHER_VERSION},
                "coverage": read.get("coverage"), "limitations": list(read.get("limitations") or []),
                "_read_at": (read.get("current_basis") or {}).get("read_at")}

    def read(self, tenant_id: UUID, site_id: UUID, site_code: str, request: IndexRequest, *,
             access_basis: str) -> dict[str, Any]:
        t, s, analytic = tenant_id, site_id, request.analytic_id
        snap = self.store.index_snapshot(t, s, request.finding_domain, analytic)
        canonical = [h for h in snap["heads"] if h["merged_into_finding_id"] is None]
        reads: dict[date, dict[str, Any]] = {}

        def window(day: date) -> dict[str, Any]:
            if day not in reads:
                reads[day] = self.dispatch.window(t, s, day)
            return reads[day]

        days = discover(canonical, request.start, request.end, self.continuity_limit,
                        edge_reach=lambda day: candidate_reach(window(day), day))
        match_pass = snap["match_pass"]
        inspected = [self._day(window(d), d, snap["selection_seqs"].get(_day_start(d)), match_pass,
                              frozenset(snap.get("deferred_windows") or ())) for d in days]
        moved = self.store.fence(t, s, analytic) != snap["fence"]
        reasons = [f"{d['day']}: {r}" for d in inspected for r in d["reasons"]]
        statuses = {d["status"] for d in inspected}
        if moved:
            reasons.append("SELECTION_MOVED_DURING_READ: an S3 selection, recompute job or Finding revision changed "
                           "during this read")
        status = next((x for x in _RANK if x in statuses), STALE if moved else CURRENT)
        rows = sorted((h for h in canonical if h["episode_start"] < request.end and h["episode_end"] > request.start),
                      key=sort_key)
        basis = {"tenant_id": str(t), "site_id": str(s), "domain": request.domain, "analytic_id": analytic,
                 "matcher_version": MATCHER_VERSION, "match_pass": match_pass,
                 "days": [{"day": d["day"], "status": d["status"], "s3_selection_seq": d["s3"]["selection_seq"],
                           "run_id": d["s3"]["run_id"], "input_sha256": d["s3"]["input_sha256"],
                           "configuration_sha256": d["s3"]["configuration_sha256"],
                           "model_version": d["s3"]["model_version"], "s4_matched": d["s4"]["matched"]}
                          for d in inspected],
                 "rows": [[str(r["finding_id"]), str(r["finding_revision_id"])] for r in rows]}
        token = _token(basis)
        scope = {"tenant_id": str(t), "site_id": str(s), "domain": request.domain,
                 "from": _iso(request.start), "to": _iso(request.end)}
        after = None
        if request.cursor is not None:
            cur = request.cursor
            changed = [k for k, v in scope.items() if cur.get(k) != v]
            reason = ("SCOPE_CHANGED" if changed else "BASIS_NOT_CURRENT" if status != CURRENT
                      else "SELECTION_CHANGED" if cur["selection_token"] != token else None)
            if reason is not None:
                raise IndexConflict("INDEX_BASIS_CHANGED",
                                    "The index basis this cursor was issued on has changed; request page one "
                                    "again without a cursor.", reason=reason, changed_fields=changed,
                                    instruction="REQUEST_FIRST_PAGE_WITHOUT_CURSOR", rows=None, total_count=None,
                                    next_cursor=None)
            after = (datetime.fromisoformat(cur["after"][0].replace("Z", "+00:00")), cur["after"][1])
        page, next_cursor, total = [], None, None
        if status == CURRENT:
            total = len(rows)
            remaining = rows if after is None else [
                r for r in rows if sort_key(r) > (-after[0].timestamp(), after[1])]
            page = remaining[:request.limit]
            if len(remaining) > request.limit:
                last = page[-1]
                next_cursor = encode_cursor({**scope, "v": 1, "selection_token": token,
                                             "after": [_iso(last["episode_start"]), str(last["finding_id"])]})
        built = [d["_read_at"] for d in inspected if d["_read_at"] is not None]
        cutoffs = [d["s3"]["knowledge_cutoff"] for d in inspected if d["s3"]["knowledge_cutoff"] is not None]
        return {
            "schema_version": SCHEMA_VERSION, "site_code": site_code, "site_id": str(s), "access_basis": access_basis,
            "domain": {"requested": request.domain, "finding_domain": request.finding_domain,
                       "analytic_id": analytic, "matcher_version": MATCHER_VERSION},
            "window": {"from": _iso(request.start), "to": _iso(request.end), "bounds": "[from, to)",
                       "intersection": INTERSECTION},
            "display_timezone": DISPLAY_TIMEZONE,
            "status": status, "status_reasons": reasons, "is_current": status == CURRENT,
            "selection_token": token,
            "knowledge_at": max(cutoffs) if cutoffs else None, "knowledge_at_label": KNOWLEDGE_AT,
            "built_at": max(built) if built else None,
            "discovery": {"days": [d["day"] for d in inspected],
                          "requested_days": [d.isoformat() for d in requested_days(request.start, request.end)],
                          "continuity_tolerance_minutes": int(CONTINUITY_TOLERANCE.total_seconds() // 60),
                          "limit_days": self.continuity_limit},
            "watermarks": {"matcher": match_pass,
                           "days": [{k: v for k, v in d.items() if k not in ("_read_at", "coverage", "limitations")}
                                    for d in inspected]},
            "coverage": [{"day": d["day"], "coverage": d["coverage"], "limitations": d["limitations"]}
                         for d in inspected],
            "order": ORDER,
            "rows": self._rows(t, s, site_code, page, snap) if page else [],
            "total_count": total, "next_cursor": next_cursor,
            "rows_statement": None if status == CURRENT else (
                "No rows and no count: this index is not current, and no durable prior snapshot exists to show "
                "historical rows. This is not a no-Findings verdict."),
        }

    def _rows(self, t: UUID, s: UUID, code: str, page: list[dict[str, Any]], snap: dict[str, Any]
              ) -> list[dict[str, Any]]:
        lineage = self.store.index_lineage(t, s, [r["finding_revision_id"] for r in page])
        runs = {str(r["id"]): r for r in lineage["runs"]}
        heads = snap["heads"]
        out = []
        for r in page:
            fid, rid = str(r["finding_id"]), str(r["finding_revision_id"])
            cites = [a for a in lineage["assessments"] if str(a["finding_revision_id"]) == rid]
            run_ids = list(dict.fromkeys(str(a["analytic_run_id"]) for a in cites))
            base = f"/sites/{code}/findings/{fid}"
            out.append({
                "key": {"tenant_id": str(t), "site_id": str(s), "finding_id": fid},
                "finding_id": fid, "canonical_finding_id": fid, "finding_revision_id": rid,
                "revision_no": r["revision_no"], "title": r["title"],
                "domain": r["domain"], "analytic_id": r["analytic_id"],
                "episode": {"start": _iso(r["episode_start"]), "end": _iso(r["episode_end"])},
                "lifecycle": r["lifecycle"], "transition": r["transition"], "claim_level": r["claim_level"],
                "assessment": {
                    "assessment_revision_id": str(r["assessment_revision_id"]),
                    "analytic_run_id": str(r["analytic_run_id"]),
                    "window_assessment_revision_ids": [str(a["assessment_revision_id"]) for a in cites
                                                       if a["scope"] == "WINDOW"],
                    "interval_assessment_revision_ids": [str(a["assessment_revision_id"]) for a in cites
                                                         if a["scope"] == "INTERVAL"],
                    "analytic_run_ids": run_ids, "model_version": r["model_version"],
                    "matcher_version": r["matcher_version"], "cohort_sha256": r["cohort_sha256"]},
                "cited": {
                    "accepted_evidence_ids": [str(e["evidence_id"]) for e in lineage["evidence"]
                                              if str(e["finding_revision_id"]) == rid],
                    "configuration": [{"run_id": x, **{k: runs[x][k] for k in (
                        "configuration_sha256", "foundation_revision_ids", "binding_set_revision_ids")}}
                        for x in run_ids if x in runs]},
                "limitations": r["limitations"],
                "relations": {
                    "merged_from": [str(m["superseded_finding_id"]) for m in snap["merges"]
                                    if str(m["canonical_finding_id"]) == fid],
                    "recurs_after": None if r["recurs_after_finding_id"] is None else str(r["recurs_after_finding_id"]),
                    "recurred_by": [str(h["finding_id"]) for h in heads if str(h["recurs_after_finding_id"]) == fid],
                    "split_from": None if r["split_from_finding_id"] is None else str(r["split_from_finding_id"]),
                    "split_parts": [str(h["finding_id"]) for h in heads if str(h["split_from_finding_id"]) == fid]},
                "links": {"selected_revision": f"{base}?revision_id={rid}", "canonical": base,
                          "api_history": f"/api{base}/history?revision_id={rid}",
                          "api_selected_revision": f"/api{base}?revision_id={rid}"},
                "amount": dict(AMOUNT_UNAVAILABLE),
                # OUT-A2 (ruling A-Q13): the one domain's Findings all carry the S4 matcher mechanism.
                "categories": categories_for(finding_signal_key(FINDING_MECHANISM), MINI),
            })
        return out
