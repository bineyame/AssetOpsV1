"""S6-03 Site Action index: request validation, cursor, ordering, fence and consistency (no database).

The PostgreSQL read, refusals and same-fence parity with Action detail are in
`test_s6_site_action_index_postgres.py`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.actions.site_index import (
    ActionIndexConflict,
    ActionIndexService,
    InvalidActionIndexRequest,
    decode_cursor,
    encode_cursor,
    parse_request,
)

UTC = timezone.utc
T0 = datetime(2026, 11, 1, tzinfo=UTC)
TENANT, SITE = uuid4(), uuid4()


def event(action_id, kind, recorded, occurred=None, **extra):
    return {"id": uuid4(), "action_id": action_id, "kind": kind, "recorded_at": recorded,
            "occurred_at": occurred or recorded, "failure_code": None, "payload": None,
            "verification_outcome_id": None, "verification_plan_id": None, **extra}


def action(created, action_id=None):
    return {"id": action_id or uuid4(), "action_code": "ACT-X", "created_at": created, "origin_finding_id": uuid4(),
            "origin_finding_revision_id": uuid4(), "origin_revision_no": 1}


class Store:
    def __init__(self, actions, events):
        self.actions, self.events = actions, events

    def site_window(self, tenant_id, site_id, start, end):
        return {"actions": [a for a in self.actions if start <= a["created_at"] < end], "events": list(self.events)}


def read(store, **q):
    request = parse_request(q.get("from", "2026-11-01T00:00:00Z"), q.get("to", "2026-11-02T00:00:00Z"),
                            q.get("limit"), q.get("cursor"))
    return ActionIndexService(store, clock=lambda: T0 + timedelta(days=2)).read(TENANT, SITE, "KOBO-001", request,
                                                                                access_basis="test")


@pytest.mark.parametrize("start,end,limit,code", [
    (None, "2026-11-02T00:00:00Z", None, "WINDOW_REQUIRED"),
    ("2026-11-01T00:00:00Z", None, None, "WINDOW_REQUIRED"),
    ("2026-11-01T00:00:00", "2026-11-02T00:00:00Z", None, "INVALID_WINDOW"),
    ("2026-11-01T00:00:00+01:00", "2026-11-02T00:00:00Z", None, "INVALID_WINDOW"),
    ("2026-11-02T00:00:00Z", "2026-11-01T00:00:00Z", None, "INVALID_WINDOW"),
    ("2026-10-01T00:00:00Z", "2026-11-01T00:00:01Z", None, "INVALID_WINDOW"),
    ("2026-11-01T00:00:00Z", "2026-11-02T00:00:00Z", "0", "INVALID_LIMIT"),
    ("2026-11-01T00:00:00Z", "2026-11-02T00:00:00Z", "101", "INVALID_LIMIT"),
    ("2026-11-01T00:00:00Z", "2026-11-02T00:00:00Z", "x", "INVALID_LIMIT"),
])
def test_invalid_requests_are_typed_422(start, end, limit, code) -> None:
    with pytest.raises(InvalidActionIndexRequest) as caught:
        parse_request(start, end, limit, None)
    assert caught.value.status == 422 and caught.value.detail["code"] == code
    assert caught.value.detail["rows"] is None and caught.value.detail["total_count"] is None


def test_thirty_one_days_is_allowed_and_cursor_garbage_is_refused() -> None:
    assert parse_request("2026-10-01T00:00:00Z", "2026-11-01T00:00:00Z", None, None).limit == 25
    for bad in ("not-a-cursor", encode_cursor({"v": 2}), encode_cursor({"v": 1, "after": []})):
        with pytest.raises(InvalidActionIndexRequest) as caught:
            parse_request("2026-11-01T00:00:00Z", "2026-11-02T00:00:00Z", None, bad)
        assert caught.value.detail["code"] == "INVALID_CURSOR"


def test_order_selection_paging_and_fence() -> None:
    tie = T0 + timedelta(hours=2)
    a1, a2, a3 = action(T0 + timedelta(hours=1)), action(tie, UUID(int=2)), action(tie, UUID(int=1))
    outside = action(T0 + timedelta(days=1))  # `to` is exclusive
    events = [event(a["id"], "ACCEPTED", a["created_at"]) for a in (a1, a2, a3)]
    # A later-recorded observation that occurred before the ACCEPTED event: it is still the selected event.
    late = event(a1["id"], "OBSERVED", T0 + timedelta(hours=5), occurred=T0)
    store = Store([a1, a2, a3, outside], events + [late])
    body = read(store)
    assert [r["action_id"] for r in body["rows"]] == [str(a3["id"]), str(a2["id"]), str(a1["id"])]
    assert body["total_count"] == 3 and body["next_cursor"] is None and body["status"] == "CURRENT"
    first = body["rows"][2]
    assert first["selected_event"]["id"] == str(late["id"]) and first["selected_event"]["occurred_before_recorded"]
    assert first["links"]["selected_event"] == f"/sites/KOBO-001/actions/{a1['id']}?event_id={late['id']}"
    assert body["fence"]["action_count"] == 3 and body["fence"]["event_count"] == 4
    assert body["fence"]["max_event_recorded_at"] == "2026-11-01T05:00:00Z"

    page1 = read(store, limit="2")
    assert [r["action_id"] for r in page1["rows"]] == [str(a3["id"]), str(a2["id"])] and page1["next_cursor"]
    page2 = read(store, limit="2", cursor=page1["next_cursor"])
    assert [r["action_id"] for r in page2["rows"]] == [str(a1["id"])] and page2["next_cursor"] is None
    assert page2["fence"]["token"] == page1["fence"]["token"] and page2["page"]["is_first"] is False

    # An event committed later but stamped BEFORE the fence's max recorded time still changes the fence (count).
    store.events.append(event(a2["id"], "OBSERVED", T0 + timedelta(hours=3)))
    with pytest.raises(ActionIndexConflict) as caught:
        read(store, limit="2", cursor=page1["next_cursor"])
    assert caught.value.detail["code"] == "ACTION_INDEX_BASIS_CHANGED"
    assert caught.value.detail["reason"] == "FENCE_CHANGED" and caught.value.detail["rows"] is None

    # A cursor from another window is a scope change, not a page.
    with pytest.raises(ActionIndexConflict) as caught:
        read(store, limit="2", to="2026-11-01T12:00:00Z", cursor=read(store, limit="2")["next_cursor"])
    assert caught.value.detail["reason"] == "SCOPE_CHANGED" and caught.value.detail["changed_fields"] == ["to"]


def test_zero_window_is_an_explicit_zero_fence() -> None:
    body = read(Store([], []))
    assert body["status"] == "CURRENT" and body["total_count"] == 0 and body["rows"] == []
    assert body["fence"]["zero_rows"] is True and body["fence"]["action_count"] == 0
    assert body["fence"]["max_created_at"] is None and body["zero_statement"].startswith("No persisted Action")


def test_inconsistent_snapshot_is_refused_not_listed() -> None:
    a = action(T0)
    for events, reason in (([], "ACTION_WITHOUT_ACCEPTED"),
                           ([event(a["id"], "OBSERVED", T0)], "ACTION_WITHOUT_ACCEPTED"),
                           ([event(a["id"], "ACCEPTED", T0), event(uuid4(), "ACCEPTED", T0)], "EVENT_WITHOUT_ACTION")):
        with pytest.raises(ActionIndexConflict) as caught:
            read(Store([a], events))
        assert caught.value.detail["code"] == "ACTION_INDEX_INCONSISTENT"
        assert caught.value.detail["reason"] == reason and caught.value.detail["total_count"] is None


def test_an_event_recorded_before_acceptance_is_listed_not_refused() -> None:
    """Served-clock case (walkthrough): an apply attempt recorded on a clock behind the fixture's acceptance time
    sorts before ACCEPTED. The Action is still consistent; the row shows the latest event in recorded order."""
    a = action(T0)
    accepted = event(a["id"], "ACCEPTED", T0)
    early = event(a["id"], "FAILED", T0 - timedelta(days=15))
    body = read(Store([a], [early, accepted]))
    [row] = body["rows"]
    assert row["selected_event"]["id"] == str(accepted["id"]) and row["event_count"] == 2


def test_cursor_round_trip() -> None:
    payload = {"v": 1, "tenant_id": "t", "site_id": "s", "from": "a", "to": "b", "fence": "f",
               "after": ["2026-11-01T00:00:00Z", str(uuid4())]}
    assert decode_cursor(encode_cursor(payload)) == payload
