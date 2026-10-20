"""S6-03 Site Work Action index (`I-site-action-index-read`, `D-2026-10-16-a-action-index`).

One authenticated tenant and Site, one half-open UTC creation window `[from, to)` of at most 31 days. Membership is
`created_at >= from AND created_at < to`, whatever happens to the Action later. Every Action in the window and every
event of those Actions is read from ONE repeatable-read snapshot (`PostgresActionStore.site_window`); each row's
latest event is chosen by `(recorded_at, id)`, never `occurred_at`, and its lifecycle is reduced by the same
`actions.lifecycle.reduce` that Action detail uses, so list and detail agree at the same fence. Persisted S6-02a
`RESOLVED` / `RESOLUTION_WITHDRAWN` events are shown as recorded events; this read derives no verdict of its own.

Fence (`D-2026-10-16-w1-remaining-questions` 1): max included creation time, max included event recorded time,
included Action count and included event count, over the whole Site/window selection including rows off the
page. The opaque cursor binds tenant, Site, window, that fence and the last sort key; any change refuses the
next page (409 `ACTION_INDEX_BASIS_CHANGED`) and the client reloads page one. Zero rows is an explicit zero fence:
no persisted Action was created in this Site/window, nothing more.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.actions.lifecycle import ACCEPTED, Selector, ordered, reduce
from assetops_backend.actions.service import _wire, selected_action_links, utc_now

SCHEMA_VERSION = "site-action-index-1"
MAX_WINDOW = timedelta(days=31)
PAGE_DEFAULT = 25
PAGE_MAX = 100
DISPLAY_TIMEZONE = "UTC"
ORDER = "created_at descending, then Action UUID ascending"
MEMBERSHIP = "created_at >= from and created_at < to (creation time only; later events do not move a row)"
SELECTION = "latest event by (recorded_at, id); never occurred_at"
ZERO_STATEMENT = ("No persisted Action was created for this Site in this window. This says nothing about Findings, "
                  "recommendations, incidents, maintenance or work that was never recorded.")
NOT_INCLUDED = ("Incidents, maintenance, owners, due dates, priority and verification verdicts are not part of this "
                "list.")


class ActionIndexRefusal(Exception):
    """A typed refusal carrying no rows, count or empty claim."""

    status = 422

    def __init__(self, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.detail = {"code": code, "message": message, "rows": None, "total_count": None, **extra}


class InvalidActionIndexRequest(ActionIndexRefusal):
    status = 422


class ActionIndexConflict(ActionIndexRefusal):
    status = 409


class ActionIndexStore(Protocol):
    def site_window(self, tenant_id: UUID, site_id: UUID, start: datetime, end: datetime) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ActionIndexRequest:
    start: datetime
    end: datetime
    limit: int
    cursor: dict[str, Any] | None


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc(value: str | None, field: str) -> datetime:
    if not value:
        raise InvalidActionIndexRequest("WINDOW_REQUIRED", f"`{field}` is required as a UTC instant; choose a "
                                        "bounded window of at most 31 days.", field=field)
    try:
        parsed = datetime.fromisoformat(value.strip().replace(" ", "+").replace("Z", "+00:00"))
    except ValueError:
        raise InvalidActionIndexRequest("INVALID_WINDOW", f"`{field}` is not an ISO-8601 instant.",
                                        field=field) from None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise InvalidActionIndexRequest("INVALID_WINDOW", f"`{field}` must be a UTC instant (Z or +00:00).",
                                        field=field)
    return parsed.astimezone(timezone.utc)


def encode_cursor(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8"))
        ok = (isinstance(payload, dict) and payload.get("v") == 1
              and all(isinstance(payload.get(k), str) for k in ("tenant_id", "site_id", "from", "to", "fence"))
              and isinstance(payload.get("after"), list) and len(payload["after"]) == 2)
        if ok:
            datetime.fromisoformat(payload["after"][0].replace("Z", "+00:00"))
            UUID(payload["after"][1])
    except (binascii.Error, ValueError, UnicodeDecodeError, TypeError, AttributeError):
        ok = False
    if not ok:
        raise InvalidActionIndexRequest("INVALID_CURSOR", "The cursor is not a cursor this list issued.",
                                        field="cursor")
    return payload


def parse_request(start: str | None, end: str | None, limit: str | None, cursor: str | None) -> ActionIndexRequest:
    """Validate the explicit scope before any read. Every failure is a typed 422 with no rows or count."""
    lo, hi = _utc(start, "from"), _utc(end, "to")
    if not lo < hi:
        raise InvalidActionIndexRequest("INVALID_WINDOW", "`from` must be before `to`.", field="from")
    if hi - lo > MAX_WINDOW:
        raise InvalidActionIndexRequest("INVALID_WINDOW", "The window may span at most 31 days.", field="to")
    if limit in (None, ""):
        size = PAGE_DEFAULT
    else:
        try:
            size = int(limit)
        except ValueError:
            size = 0
        if not 1 <= size <= PAGE_MAX:
            raise InvalidActionIndexRequest("INVALID_LIMIT", f"`limit` must be an integer from 1 to {PAGE_MAX}.",
                                            field="limit")
    return ActionIndexRequest(lo, hi, size, None if cursor in (None, "") else decode_cursor(cursor))


def window_scope(tenant_id: UUID, site_id: UUID, start: datetime, end: datetime) -> dict[str, str | None]:
    return {"tenant_id": str(tenant_id), "site_id": str(site_id), "from": _iso(start), "to": _iso(end)}


def index_token(scope: dict[str, Any], fence: dict[str, Any]) -> str:
    """The `sai1-` fence token (also reproduced by the W4-01 work list on its own snapshot connection)."""
    return "sai1-" + hashlib.sha256(json.dumps({**scope, **fence}, sort_keys=True).encode("utf-8")).hexdigest()


def _after(row: dict[str, Any], key: tuple[datetime, str]) -> bool:
    """True when `row` sorts after `key` in `created_at DESC, action_id ASC` order."""
    return row["created_at"] < key[0] or (row["created_at"] == key[0] and str(row["id"]) > key[1])


class ActionIndexService:
    def __init__(self, store: ActionIndexStore, clock: Callable[[], datetime] = utc_now) -> None:
        self.store, self.clock = store, clock

    @staticmethod
    def fence(actions: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
        return {"max_created_at": _iso(max((a["created_at"] for a in actions), default=None)),
                "max_event_recorded_at": _iso(max((e["recorded_at"] for e in events), default=None)),
                "action_count": len(actions), "event_count": len(events), "zero_rows": not actions}

    def read(self, tenant_id: UUID, site_id: UUID, site_code: str, request: ActionIndexRequest, *,
             access_basis: str) -> dict[str, Any]:
        scope = window_scope(tenant_id, site_id, request.start, request.end)
        snap = self.store.site_window(tenant_id, site_id, request.start, request.end)
        read_at = self.clock()
        actions, events = snap["actions"], snap["events"]
        by_action: dict[str, list[dict[str, Any]]] = {str(a["id"]): [] for a in actions}
        for event in events:
            if str(event["action_id"]) not in by_action:
                raise ActionIndexConflict("ACTION_INDEX_INCONSISTENT", "The Action read was not consistent; "
                                          "nothing is listed. Reload the list.", reason="EVENT_WITHOUT_ACTION")
            by_action[str(event["action_id"])].append(event)
        for key, evs in by_action.items():
            # Every Action is created with its ACCEPTED event in one transaction. It need not be FIRST in
            # (recorded_at, id) order: a later attempt recorded on a server clock behind the fixture's sorts earlier.
            if not any(e["kind"] == ACCEPTED for e in evs):
                raise ActionIndexConflict("ACTION_INDEX_INCONSISTENT", "The Action read was not consistent; "
                                          "nothing is listed. Reload the list.", reason="ACTION_WITHOUT_ACCEPTED",
                                          action_id=key)
        fence = self.fence(actions, events)
        token = index_token(scope, fence)
        after = None
        if request.cursor is not None:
            cur = request.cursor
            changed = sorted(k for k, v in scope.items() if cur.get(k) != v)
            reason = "SCOPE_CHANGED" if changed else "FENCE_CHANGED" if cur["fence"] != token else None
            if reason is not None:
                raise ActionIndexConflict("ACTION_INDEX_BASIS_CHANGED",
                                          "The Actions in this window changed since this page was issued; request "
                                          "page one again without a cursor.", reason=reason, changed_fields=changed,
                                          instruction="REQUEST_FIRST_PAGE_WITHOUT_CURSOR", next_cursor=None)
            after = (datetime.fromisoformat(cur["after"][0].replace("Z", "+00:00")), cur["after"][1])
        rows = sorted(sorted(actions, key=lambda a: str(a["id"])), key=lambda a: a["created_at"], reverse=True)
        remaining = rows if after is None else [r for r in rows if _after(r, after)]
        page = remaining[:request.limit]
        next_cursor = None
        if len(remaining) > request.limit:
            last = page[-1]
            next_cursor = encode_cursor({**scope, "v": 1, "fence": token,
                                         "after": [_iso(last["created_at"]), str(last["id"])]})
        return {
            "schema_version": SCHEMA_VERSION, "site_code": site_code, "site_id": str(site_id),
            "access_basis": access_basis, "kind": "ACTIONS",
            "window": {"from": scope["from"], "to": scope["to"], "bounds": "[from, to)", "membership": MEMBERSHIP},
            "display_timezone": DISPLAY_TIMEZONE, "status": "CURRENT", "is_current": True,
            "read_at": _iso(read_at), "fence": {**fence, "token": token}, "order": ORDER, "selection": SELECTION,
            "rows": [self._row(tenant_id, site_id, site_code, a, by_action[str(a["id"])]) for a in page],
            "total_count": len(rows), "next_cursor": next_cursor,
            "page": {"limit": request.limit, "shown": len(page), "is_first": after is None},
            "zero_statement": ZERO_STATEMENT if not rows else None, "not_included": NOT_INCLUDED,
        }

    @staticmethod
    def _row(tenant_id: UUID, site_id: UUID, site_code: str, action: dict[str, Any],
             events: list[dict[str, Any]]) -> dict[str, Any]:
        evs = ordered(events)
        latest = evs[-1]
        exact = selected_action_links(site_code, action, Selector("EVENT_ID", event_id=latest["id"]))
        canonical = selected_action_links(site_code, action, Selector("LATEST"))
        return {
            "key": {"tenant_id": str(tenant_id), "site_id": str(site_id), "action_id": str(action["id"])},
            "action_id": str(action["id"]), "action_code": action["action_code"],
            "created_at": _iso(action["created_at"]),
            "origin": {"finding_id": str(action["origin_finding_id"]),
                       "finding_revision_id": str(action["origin_finding_revision_id"]),
                       "revision_no": action["origin_revision_no"]},
            "selected_event": {"id": str(latest["id"]), "kind": latest["kind"],
                               "recorded_at": _iso(latest["recorded_at"]),
                               "occurred_at": _iso(latest["occurred_at"]),
                               "occurred_before_recorded": latest["occurred_at"] < latest["recorded_at"]},
            "event_count": len(evs),
            "state": _wire(reduce(evs)),
            "links": {"canonical": canonical["canonical"], "selected_event": exact["selected"],
                      "history_at_event": exact["history"], "api_action_at_event": exact["api_action"],
                      "api_events_at_event": exact["api_events"], "origin_finding": exact["origin_finding"]},
        }
