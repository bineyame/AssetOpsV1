"""S4-08 Site assumption and consequence history (`I-assumption-consequence-history-read`, `D-2026-10-16-s408`).

`tasks/S4-08-assumption-consequence-history.md` items 1-4. At one recorded UTC cutoff, every stored consequence
revision of one tenant's Site recorded at or before it (`financial_consequence_revision.recorded_at <= cutoff`),
from ONE repeatable-read snapshot, ordered `(recorded_at DESC, id DESC)`. Earlier versions, unpriced versions and
versions whose price was later superseded all stay listed; each row names its exact Finding, FindingRevision,
consequence revision and the price revision its stored link used (never today's price).

Currentness at the cutoff (`D-2026-10-16-s408` Q2): a row is `CURRENT_AT_CUTOFF` only when it is the latest
consequence `(recorded_at, id)` at or before the cutoff within the latest qualifying FindingRevision of its
Finding (by `revision_no`). A FindingRevision qualifies when its application-clock `created_at` is at or before
the cutoff, or when it has a consequence recorded (database clock) at or before the cutoff. Every other row is
`HISTORICAL_AT_CUTOFF`. This is an audit classification, not a physical assertion.

Money (`D-2026-10-16-s408` Q3): no current amount is ever claimed here, at any cutoff, including the server
default (`current_amount_shown: false`). A row may carry its stored, outward-rounded PRICED amount only as
recorded, assumption-conditioned audit history, and only when the Site source gate is open and that exact
version's S4-05b source block is a positive stored class; otherwise the amount is null with a typed reason.
Nothing is summed. Per-Finding `derive()` is never called.

Fence (S6-03 pattern, `actions/site_index.py`): count and maximum `(recorded_at, id)` over every in-scope row at
or before the cutoff, off-page rows included, recomputed in each page's own snapshot. The opaque cursor binds
tenant, Site, cutoff, limit, the fence token and the last sort pair; a changed scope or fence refuses with 409
`CONSEQUENCE_HISTORY_BASIS_CHANGED` (reload page one); an undecodable cursor refuses with 400 and no rows.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.evidence.provenance_read import consequence_provenance, source_gate
from assetops_backend.financials.consequence_read import display

SCHEMA_VERSION = "site-consequence-history-1"
PAGE_DEFAULT = 25
PAGE_MAX = 100
CURRENT_AT_CUTOFF = "CURRENT_AT_CUTOFF"
HISTORICAL_AT_CUTOFF = "HISTORICAL_AT_CUTOFF"
RECORDED_LABEL = "Recorded amount — historical, assumption-conditioned audit history"
ORDER = "recorded_at descending, then consequence revision ID descending"
CLASSIFICATION = (
    "CURRENT_AT_CUTOFF: the latest consequence revision recorded by the cutoff within the latest FindingRevision "
    "of its Finding recorded by the cutoff (application-clock created_at at or before the cutoff, or a consequence "
    "recorded by then; latest by revision_no). Every other row is HISTORICAL_AT_CUTOFF. An audit classification, "
    "not a physical assertion.")
ZERO_STATEMENT = ("No fuel cost version had been recorded for this Site at this moment. This says nothing about "
                  "Findings without a fuel cost or about anything recorded later.")
EXCLUSIONS = ("No Site or estate total is computed from these rows.",
              "No row is a current amount; today's amount is only on the Finding's own Financials read.")


class HistoryRefusal(Exception):
    """A typed refusal carrying no rows."""

    status = 422

    def __init__(self, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.detail = {"code": code, "message": message, "rows": None, **extra}


class InvalidHistoryRequest(HistoryRefusal):
    status = 422


class InvalidHistoryCursor(HistoryRefusal):
    status = 400


class HistoryBasisChanged(HistoryRefusal):
    status = 409


class HistoryRows(Protocol):
    def site_history(self, tenant_id: UUID, site_id: UUID, cutoff: datetime | None,
                     after: tuple[datetime, UUID] | None, limit: int) -> dict[str, Any]: ...


@dataclass(frozen=True)
class HistoryRequest:
    cutoff: datetime | None
    limit: int
    cursor: dict[str, Any] | None


def instant(value: datetime) -> str:
    """The exact cutoff string: microseconds kept, `+00:00` offset, the form the price read echoes for the same
    parsed instant (review L-R1: clients pass it through unchanged)."""
    return value.astimezone(timezone.utc).isoformat()


def _iso(value: datetime | None) -> str | None:
    return None if value is None else instant(value)


def parse_instant(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace(" ", "+").replace("Z", "+00:00"))
    except ValueError:
        raise InvalidHistoryRequest("INVALID_CUTOFF", f"`{field}` is not an ISO-8601 instant.", field=field) from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidHistoryRequest("INSTANT_NOT_ZONED", f"`{field}` must carry a timezone offset.", field=field)
    return parsed.astimezone(timezone.utc)


def encode_cursor(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8"))
        ok = (isinstance(payload, dict) and payload.get("v") == 1
              and all(isinstance(payload.get(k), str) for k in ("tenant_id", "site_id", "recorded_at", "fence"))
              and isinstance(payload.get("limit"), int)
              and isinstance(payload.get("after"), list) and len(payload["after"]) == 2)
        if ok:
            parse_instant(payload["recorded_at"], "cursor")
            parse_instant(payload["after"][0], "cursor")
            UUID(payload["after"][1])
    except (binascii.Error, ValueError, UnicodeDecodeError, TypeError, AttributeError, HistoryRefusal):
        ok = False
    if not ok:
        raise InvalidHistoryCursor("INVALID_CURSOR", "The cursor is not a cursor this list issued.", field="after")
    return payload


def parse_request(recorded_at: str | None, after: str | None, limit: str | None) -> HistoryRequest:
    """Validate before any read. Every failure is typed and carries no rows."""
    cutoff = None if recorded_at in (None, "") else parse_instant(recorded_at, "recorded_at")
    if limit in (None, ""):
        size = PAGE_DEFAULT
    else:
        try:
            size = int(limit)
        except ValueError:
            size = 0
        if not 1 <= size <= PAGE_MAX:
            raise InvalidHistoryRequest("INVALID_LIMIT", f"`limit` must be an integer from 1 to {PAGE_MAX}.",
                                        field="limit")
    if after not in (None, "") and cutoff is None:
        raise InvalidHistoryRequest("CUTOFF_REQUIRED_WITH_CURSOR", "A next page needs the same `recorded_at` its "
                                    "cursor was issued for.", field="recorded_at")
    cursor = None if after in (None, "") else decode_cursor(after)
    return HistoryRequest(cutoff, size, cursor)


def classify(revisions: list[dict[str, Any]], cutoff: datetime) -> dict[str, str | None]:
    """Finding ID -> the consequence revision ID current at the cutoff (None: no row of it is current)."""
    out: dict[str, str | None] = {}
    by_finding: dict[str, list[dict[str, Any]]] = {}
    for fr in revisions:
        by_finding.setdefault(str(fr["finding_id"]), []).append(fr)
    for finding, frs in by_finding.items():
        qualifying = [fr for fr in frs if fr["created_at"] <= cutoff or fr["latest_consequence_id"] is not None]
        latest = max(qualifying, key=lambda fr: fr["revision_no"], default=None)
        out[finding] = None if latest is None or latest["latest_consequence_id"] is None \
            else str(latest["latest_consequence_id"])
    return out


def _interval(lo: datetime | None, hi: datetime | None) -> dict[str, Any]:
    return {"from": _iso(lo), "to": _iso(hi), "bounds": "[from, to)"}


class ConsequenceHistoryService:
    def __init__(self, rows: HistoryRows, *, provenance: Any = None) -> None:
        self.rows = rows
        #: S4-05b exact-revision resolver; None reads every row as UNKNOWN (no recorded amount).
        self.provenance = provenance

    def read(self, tenant_id: UUID, site_id: UUID, site_code: str, request: HistoryRequest, *,
             source_open: bool, source_reason: str | None, access_basis: str) -> dict[str, Any]:
        cur = request.cursor
        after = None if cur is None else (parse_instant(cur["after"][0], "cursor"), UUID(cur["after"][1]))
        snap = self.rows.site_history(tenant_id, site_id, request.cutoff, after, request.limit)
        cutoff: datetime = snap["cutoff"]
        scope = {"tenant_id": str(tenant_id), "site_id": str(site_id), "recorded_at": instant(cutoff),
                 "limit": request.limit}
        f = snap["fence"]
        fence = {"count": f["count"], "max": None if f["max_recorded_at"] is None
                 else [instant(f["max_recorded_at"]), f["max_id"]]}
        token = "sch1-" + hashlib.sha256(json.dumps({**scope, **fence}, sort_keys=True).encode()).hexdigest()
        if cur is not None:
            changed = sorted(k for k, v in scope.items()
                             if (instant(parse_instant(cur[k], "cursor")) if k == "recorded_at" else cur.get(k)) != v)
            reason = "SCOPE_CHANGED" if changed else "FENCE_CHANGED" if cur["fence"] != token else None
            if reason is not None:
                raise HistoryBasisChanged(
                    "CONSEQUENCE_HISTORY_BASIS_CHANGED", "The recorded fuel cost versions at this moment changed "
                    "since this page was issued; request page one again without a cursor.", reason=reason,
                    changed_fields=changed, instruction="REQUEST_FIRST_PAGE_WITHOUT_CURSOR", next_cursor=None)
        rows = snap["page"]
        page, more = rows[:request.limit], len(rows) > request.limit
        current = classify(snap["finding_revisions"], cutoff)
        frs = {str(fr["id"]): fr for fr in snap["finding_revisions"]}
        next_cursor = None
        if more:
            last = page[-1]
            next_cursor = encode_cursor({**scope, "v": 1, "fence": token,
                                         "after": [instant(last["recorded_at"]), str(last["id"])]})
        return {
            "schema_version": SCHEMA_VERSION, "site_code": site_code, "site_id": str(site_id),
            "access_basis": access_basis,
            "cutoff": {"recorded_at": instant(cutoff),
                       "selected_by": "SERVER_DEFAULT" if request.cutoff is None else "RECORDED_CUTOFF",
                       "clock": "DATABASE",
                       "membership": "consequence recorded_at <= cutoff (database clock)"},
            "current_amount_shown": False,
            "source_gate": {"open": source_open, "reason": None if source_open else source_reason},
            "classification": CLASSIFICATION, "order": ORDER, "fence": {"token": token},
            "rows": [self._row(tenant_id, site_id, site_code, r, current, frs, snap, cutoff, source_open)
                     for r in page],
            "next_cursor": next_cursor,
            "page": {"limit": request.limit, "shown": len(page), "is_first": cur is None},
            "zero_statement": ZERO_STATEMENT if not page and cur is None else None,
            "exclusions": list(EXCLUSIONS),
        }

    def _row(self, tenant_id: UUID, site_id: UUID, code: str, r: dict[str, Any], current: dict[str, str | None],
             frs: dict[str, dict[str, Any]], snap: dict[str, Any], cutoff: datetime,
             source_open: bool) -> dict[str, Any]:
        cid, fid, frid = str(r["id"]), str(r["finding_id"]), str(r["finding_revision_id"])
        fr = frs.get(frid)
        links = snap["links"].get(r["id"], [])
        price_id = None if r["price_revision_id"] is None else str(r["price_revision_id"])
        broken = fr is None or any(
            x["a_revision_id"] is None or str(x["a_tenant_id"]) != str(tenant_id) or str(x["a_site_id"]) != str(site_id)
            or str(x["a_revision_id"]) != str(x["assumption_revision_id"]) for x in links)
        if r["state"] == "PRICED":
            used = [x for x in links if str(x["assumption_revision_id"]) == price_id]
            broken = broken or len(used) != 1
            price_state = "LINKED"
        else:
            price_state = "NOT_EVALUATED" if r["state"] == "QUANTITY_UNAVAILABLE" else "NO_PRICE_LINK"
        if broken:
            price_state = "LINEAGE_INCONSISTENT"
        assignments = [{
            "assumption_revision_id": str(x["assumption_revision_id"]), "assignment_id": str(x["assignment_id"]),
            "used": str(x["assumption_revision_id"]) == price_id,
            "valid": _interval(x["valid_from"], x["valid_to"]),
            # Recorded interval as known at the cutoff: a close recorded after the cutoff is not shown.
            "recorded": _interval(x["recorded_from"], x["recorded_to"] if x["recorded_to"] is not None
                                  and x["recorded_to"] <= cutoff else None)} for x in links]
        provenance = consequence_provenance(self.provenance, tenant_id, site_id, frid, cid)
        gate = source_gate(provenance)
        shown = display(r)
        if not source_open:
            disposition = "SOURCE_CLOSED"
        elif price_state == "LINEAGE_INCONSISTENT":
            disposition = "LINEAGE_INCONSISTENT"
        elif r["state"] != "PRICED":
            disposition = r["state"]
        elif shown is None or shown["state"] != "ROUNDED_OUTWARD":
            disposition = "MINOR_UNIT_UNKNOWN"
        elif not gate["permits_current_money"]:
            disposition = "MIXED_OR_UNKNOWN_SOURCE"
        else:
            disposition = "SHOWN"
        amount = None if disposition != "SHOWN" or shown is None else {
            "low": shown["amount_low"], "high": shown["amount_high"], "currency": shown["currency"]}
        prior = snap["priors"].get(r["prior_consequence_revision_id"])
        if r["prior_consequence_revision_id"] is None:
            change = "FIRST_VERSION"
        elif prior is None:
            change = "PRIOR_UNREADABLE"
        elif prior["technical_input_sha256"] == r["technical_input_sha256"]:
            change = "PRICE_ONLY" if prior["price_revision_id"] != r["price_revision_id"] else "SAME_INPUTS"
        else:
            change = "MEASURED_RESULT_CHANGED"
        q_high = r["quantity_high"]
        return {
            "finding_id": fid, "finding_revision_id": frid,
            "finding_revision_no": None if fr is None else fr["revision_no"],
            "finding_title": None if fr is None else fr["title"],
            "finding_window": None if fr is None else _interval(fr["episode_start"], fr["episode_end"]),
            "consequence_revision_id": cid, "revision_no": r["revision_no"],
            "prior_consequence_revision_id": None if r["prior_consequence_revision_id"] is None
            else str(r["prior_consequence_revision_id"]),
            "recorded_at": instant(r["recorded_at"]),
            "window": _interval(r["window_start"], r["window_end"]),
            "at_cutoff": CURRENT_AT_CUTOFF if current.get(fid) == cid else HISTORICAL_AT_CUTOFF,
            "state": r["state"],
            "quantity": {"state": r["quantity_state"], "reason": r["quantity_reason"], "unit": r["quantity_unit"],
                         "high": None if q_high is None else format(q_high, "f")},
            "price": {"state": price_state, "price_revision_id": price_id, "reason": r["price_reason"],
                      "value": None if r["price_value"] is None else format(r["price_value"], "f"),
                      "currency": r["price_currency"], "assignments": assignments},
            "change_from_prior": change,
            "recorded_amount": {"disposition": disposition, "label": RECORDED_LABEL if amount else None,
                                "amount": amount, "is_current_amount": False},
            "source_provenance": provenance,
            "source_gate": gate,
            "links": {
                "finding": f"/sites/{code}/findings/{fid}?revision_id={frid}",
                "finding_financials": f"/sites/{code}/financials?finding_id={fid}&revision_id={frid}"
                                      f"&consequence_revision_id={cid}",
                "price_revision": None if price_id is None
                else f"/sites/{code}/financials/assumptions?revision_id={price_id}",
                "api_consequence": f"/api/sites/{code}/findings/{fid}/financial-consequences?revision_id={frid}"
                                   f"&consequence_revision_id={cid}"},
        }

