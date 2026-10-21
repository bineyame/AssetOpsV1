"""W3-01 estate request grammar, refusals, access basis, selection token and cursor (pure; no storage).

Spec: `.agent/W3-01-build-spec.md` "Refusal table and cursor", Review closure B6/S12/S15, the `estate-selection/2`
amendment and Run 5 ruling 4 (strict shared parser). Every estate root takes whole UTC midnight days `[from, to)`
of at most 31 days and an optional UTC `known_at`; the later-than-read-time check happens inside the snapshot.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from uuid import UUID

MAX_DAYS = 31
DEFAULT_LIMIT, MAX_LIMIT = 50, 100
LENSES = ("all", "cost", "risks", "opportunities")
STATE_FILTERS = {"all": None, "supported": "SUPPORTED", "unconfirmed": "UNCONFIRMED",
                 "no_longer_supported": "NO_LONGER_SUPPORTED", "merged": "MERGED"}
ACCESS_VERSION, SELECTION_VERSION = "estate-access/1", "estate-selection/2"

MESSAGES = {
    "UNAUTHENTICATED": "Sign in to read estate records.",
    "ESTATE_BASIS_CHANGED": "The estate selection or Site access changed; request page one without a cursor.",
    "ESTATE_SELECTION_INCONSISTENT": "The selected Site revisions cannot be read consistently.",
    "INVALID_WINDOW": "from and to must be UTC instants in order, at most 31 days apart.",
    "INVALID_KNOWN_AT": "known_at must be UTC and no later than the read time.",
    "INVALID_LENS": "Use all, cost, risks or opportunities.",
    "INVALID_LIMIT": "limit must be an integer from 1 to 100.",
    "INVALID_CURSOR": "The cursor is not an estate cursor.",
    "ESTATE_STORE_UNAVAILABLE": "Estate records could not be read.",
}
STATUS = {"UNAUTHENTICATED": 401, "ESTATE_BASIS_CHANGED": 409, "ESTATE_SELECTION_INCONSISTENT": 409,
          "ESTATE_STORE_UNAVAILABLE": 503}

# The exact key sets of the estate roots (Run 5 ruling 4; W3-02 closure 4 B1 adds evidence and financials): any
# other key, or a repeated one, is INVALID_CURSOR; an unsupported root kind is INVALID_CURSOR too, never a 500.
KEYS = {"scope": ("from", "to", "known_at"),
        "findings": ("from", "to", "known_at", "lens", "state", "limit", "cursor"),
        "actions": ("from", "to", "known_at", "limit", "cursor"),
        "evidence": ("from", "to", "known_at", "limit", "cursor"),
        "financials": ("from", "to", "known_at", "limit", "cursor")}
_FINDING_CURSOR_KEYS = {"v", "tenant_id", "authorized_site_ids", "access_basis", "from", "to", "known_at", "lens",
                        "state_filter", "selection_token", "after", "page_one_mode"}
_ACTION_CURSOR_KEYS = (_FINDING_CURSOR_KEYS - {"lens", "state_filter"}) | {"kind"}
# W3-02 closure 4 B1: the Evidence and Financials cursors carry the Action key set (with `kind` equal to the root)
# and a kind-specific ordered marker: Evidence [site_code_key, site_id, capability_key]; Financials
# [window_start_or_null, site_code_key, site_id, category, line_key]. Finding/Action markers stay two-part.
_MARKER_KINDS = {"evidence": 3, "financials": 5}


class EstateRefusal(Exception):
    """A typed estate refusal; the router maps it to the exact refusal-table body."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code, self.status = code, STATUS.get(code, 422)
        self.detail = {"code": code, "message": MESSAGES[code], "rows": None, "total_count": None}


class EstateStoreUnavailable(Exception):
    """The estate snapshot could not be read (connection or driver failure): 503."""


class EstateSelectionInconsistent(Exception):
    """One transaction observed an impossible selected revision or lineage (refused exact pin): 409."""


@dataclass(frozen=True)
class EstateRequest:
    kind: str
    from_: datetime
    to: datetime
    known_at: datetime | None
    lens: str | None = None
    state_filter: str | None = None
    limit: int = DEFAULT_LIMIT
    cursor: str | None = None


def _instant(value: str, code: str) -> datetime:
    text_value = value.strip()
    if not text_value or not (text_value.endswith("Z") or text_value.endswith("+00:00")):
        raise EstateRefusal(code)
    try:
        parsed = datetime.fromisoformat(text_value[:-1] + "+00:00" if text_value.endswith("Z") else text_value)
    except ValueError as error:
        raise EstateRefusal(code) from error
    if parsed.utcoffset() != timedelta(0):
        raise EstateRefusal(code)
    return parsed.astimezone(timezone.utc)


def parse_request(kind: str, items: Iterable[tuple[str, str]]) -> EstateRequest:
    """The strict shared parser. Window keys missing or repeated: INVALID_WINDOW; any other repeated or unknown
    key: INVALID_CURSOR. Validation order: window, known_at, lens/state, limit, cursor shape."""
    if kind not in KEYS:
        raise EstateRefusal("INVALID_CURSOR")
    seen: dict[str, list[str]] = {}
    for key, value in items:
        seen.setdefault(key, []).append(value)
    if any(len(seen.get(k, ())) != 1 for k in ("from", "to")):
        raise EstateRefusal("INVALID_WINDOW")
    if any(k not in KEYS[kind] or len(v) != 1 for k, v in seen.items()):
        raise EstateRefusal("INVALID_CURSOR")
    one = {k: v[0] for k, v in seen.items()}
    from_, to = _instant(one["from"], "INVALID_WINDOW"), _instant(one["to"], "INVALID_WINDOW")
    midnight = all(x.hour == x.minute == x.second == x.microsecond == 0 for x in (from_, to))
    if not midnight or from_ >= to or to - from_ > timedelta(days=MAX_DAYS):
        raise EstateRefusal("INVALID_WINDOW")
    known_at = None if "known_at" not in one else _instant(one["known_at"], "INVALID_KNOWN_AT")
    lens = state_filter = None
    if kind == "findings":
        lens = one.get("lens", "all")
        state_filter = one.get("state", "all")
        # Reading (pending confirmation): the refusal table names no state code; an unsupported state value is
        # refused with the lens code, since both choose the Findings basis view.
        if lens not in LENSES or state_filter not in STATE_FILTERS:
            raise EstateRefusal("INVALID_LENS")
    limit = DEFAULT_LIMIT
    if "limit" in one:
        raw = one["limit"].strip()
        if not raw.isdigit() or not 1 <= int(raw) <= MAX_LIMIT:
            raise EstateRefusal("INVALID_LIMIT")
        limit = int(raw)
    cursor = one.get("cursor")
    if cursor is not None:
        decode_cursor(kind, cursor)  # shape only; the fence is compared inside the snapshot
    return EstateRequest(kind, from_, to, known_at, lens, state_filter, limit, cursor)


# --- canonical formatting -------------------------------------------------------------------------------------

def wire_time(at: datetime | None) -> str | None:
    """Wire UTC: whole seconds with `Z` (Run 6 reading 7)."""
    return None if at is None else at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def token_time(at: datetime | None) -> str | None:
    """Canonical token/cursor UTC: six fractional digits with `Z` (S12/S15)."""
    return None if at is None else at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _ids(values: Iterable[Any]) -> list[str]:
    return sorted({str(v).lower() for v in values if v is not None})


def _digest(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def access_basis(tenant_id: Any, authorized_site_ids: Iterable[Any]) -> str:
    """B6: a digest/fence of the authorized Site set, not a signature or policy claim."""
    return _digest({"version": ACCESS_VERSION, "tenant_id": None if tenant_id is None else str(tenant_id).lower(),
                    "authorized_site_ids": _ids(authorized_site_ids)})


SITE_TOKEN_ARRAYS = ("selected_finding_revision_ids", "selected_action_event_ids", "selected_assessment_revision_ids",
                     "selected_consequence_revision_ids", "selected_assumption_revision_ids",
                     "cited_accepted_evidence_ids")


def selection_token(tenant_id: Any, authorized_site_ids: Iterable[Any], from_: datetime, to: datetime,
                    known_at: datetime, lens: str | None, state_filter: str | None,
                    sites: Iterable[dict[str, Any]]) -> str:
    """The canonical `estate-selection/2` digest over the full selected set (never a page)."""
    items = []
    for s in sites:
        item = {"site_id": str(s["site_id"]).lower(), "domain": s["domain"],
                "selection_id": None if s.get("selection_id") is None else str(s["selection_id"]).lower(),
                "watermark": token_time(s.get("watermark")), "match_state": s["match_state"],
                "job_state": s["job_state"], "source_freshness": s["source_freshness"]}
        for key in SITE_TOKEN_ARRAYS:
            item[key] = _ids(s.get(key) or ())
        items.append(item)
    items.sort(key=lambda x: (x["site_id"], x["domain"]))
    return _digest({"version": SELECTION_VERSION, "tenant_id": None if tenant_id is None else str(tenant_id).lower(),
                    "authorized_site_ids": _ids(authorized_site_ids), "from": token_time(from_),
                    "to": token_time(to), "known_at": token_time(known_at), "lens": lens,
                    "state_filter": state_filter, "sites": items})


# --- cursor --------------------------------------------------------------------------------------------------

def encode_cursor(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _canonical_instant(value: Any) -> bool:
    """A canonical six-digit UTC token instant (the `token_time` form) and nothing else."""
    if not isinstance(value, str):
        return False
    try:
        return token_time(_instant(value, "INVALID_CURSOR")) == value
    except EstateRefusal:
        return False


def _uuid(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        UUID(value)
    except ValueError:
        return False
    return True


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _marker_ok(kind: str, after: Any) -> bool:
    if not isinstance(after, list):
        return False
    if kind in _MARKER_KINDS:
        if len(after) != _MARKER_KINDS[kind]:
            return False
        if kind == "evidence":
            return all(_nonempty(x) for x in after) and _uuid(after[1])
        return ((after[0] is None or _canonical_instant(after[0])) and all(_nonempty(x) for x in after[1:])
                and _uuid(after[2]))
    if len(after) != 2 or not all(isinstance(x, str) for x in after):
        return False
    try:
        _instant(after[0], "INVALID_CURSOR")
    except EstateRefusal:
        return False
    return True


def decode_cursor(kind: str, value: str) -> dict[str, Any]:
    """A structurally valid estate cursor of this root, else 422 INVALID_CURSOR (unsigned; no tamper claim)."""
    if kind not in KEYS or kind == "scope" or not isinstance(value, str):
        raise EstateRefusal("INVALID_CURSOR")
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        payload = json.loads(raw.decode("utf-8"))
    except (binascii.Error, ValueError, UnicodeDecodeError) as error:
        raise EstateRefusal("INVALID_CURSOR") from error
    keys = _FINDING_CURSOR_KEYS if kind == "findings" else _ACTION_CURSOR_KEYS
    ok = (isinstance(payload, dict) and set(payload) == keys and payload.get("v") == 1
          and (kind == "findings" or payload.get("kind") == kind)
          and payload.get("page_one_mode") in ("live", "historical")
          and all(isinstance(payload.get(k), str) for k in ("access_basis", "from", "to", "known_at",
                                                             "selection_token"))
          and (payload.get("tenant_id") is None or isinstance(payload["tenant_id"], str))
          and isinstance(payload.get("authorized_site_ids"), list)
          and all(isinstance(x, str) for x in payload["authorized_site_ids"])
          and _marker_ok(kind, payload.get("after")))
    if ok:
        try:
            _instant(payload["known_at"], "INVALID_CURSOR")
        except EstateRefusal:
            ok = False
    if ok and kind in _MARKER_KINDS:
        ok = all(_canonical_instant(payload[k]) for k in ("from", "to", "known_at"))
    if not ok:
        raise EstateRefusal("INVALID_CURSOR")
    return payload


def cursor_after(payload: dict[str, Any]) -> tuple:
    """The ordered resume marker: `(at, row_id)` for Findings/Actions (unchanged); the stored string tuple for
    Evidence; `(window_start_or_None, site_code_key, site_id, category, line_key)` for Financials."""
    kind = payload.get("kind")
    after = payload["after"]
    if kind == "evidence":
        return tuple(after)
    if kind == "financials":
        return (None if after[0] is None else _instant(after[0], "INVALID_CURSOR"), *after[1:])
    return _instant(after[0], "INVALID_CURSOR"), after[1]


def cursor_marker(kind: str, after: tuple) -> list[Any]:
    """The wire form of a resume marker (inverse of `cursor_after`)."""
    if kind == "evidence":
        return [str(x) for x in after]
    if kind == "financials":
        return [token_time(after[0]), *(str(x) for x in after[1:])]
    return [token_time(after[0]), after[1]]


def resume_after(markers: Iterable[tuple], after: tuple) -> int:
    """Closure 4 B1: only after the fence passes, the marker must exist in the full ordered row set; returns the
    index of the first row after it. An absent marker is 422 INVALID_CURSOR."""
    for i, marker in enumerate(markers):
        if tuple(marker) == tuple(after):
            return i + 1
    raise EstateRefusal("INVALID_CURSOR")


def cursor_known_at(payload: dict[str, Any]) -> datetime:
    return _instant(payload["known_at"], "INVALID_CURSOR")
