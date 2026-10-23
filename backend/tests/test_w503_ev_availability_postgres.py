"""W5-03a E1a: `ev-availability/1`, the selected observed connector-availability calculation.

The pure tests need no database; the persisted tests replay W2-05b's registered `Chain` through
`ev_depth_cases.py` on a private `*_test` database (window `[08:00, 09:00)`, decision clock 09:00 / 09:05).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from assetops_backend.analytics.ev_availability import (
    CALCULATION_VERSION,
    availability,
    ratio,
    selected_foundation,
    selected_rows,
)
from assetops_backend.ev_site_reads import connector_service_windows
from ev_depth_cases import HI, HISTORICAL_KNOWN_AT, LO, URL, chain, declared_empty, pending, settled, status_gap  # noqa: F401

needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

TOP_KEYS = ["calculation_version", "schedule_state", "scheduled_seconds", "known_available_seconds",
            "known_unavailable_seconds", "unknown_seconds", "known_time_ratio", "full_lower", "full_upper",
            "connectors"]
ROW_KEYS = ["asset_id", "label", "scheduled_seconds", "known_available_seconds", "known_unavailable_seconds",
            "unknown_seconds", "spans"]
SPAN_KEYS = ["from", "to", "state", "evidence_ids"]
A1, A2 = "00000000-0000-4000-8000-0000000000a1", "00000000-0000-4000-8000-0000000000a2"
ASSETS = {"c1": A1, "c2": A2}


def _at(minute: int) -> datetime:
    return LO + timedelta(minutes=minute)


def _connector(cid: str, *, cadence="1.0", unit="min", enabled="ENABLED", name: str | None = None) -> dict:
    props = [{"property_key": "ev-connector-enabled", "value": enabled, "unit": "state"}]
    if cadence is not None:
        props.append({"property_key": "ev-status-cadence", "value": cadence, "unit": unit})
    return {"component_id": cid, "component_type": "EV_CONNECTOR", "display_name": name or f"Connector {cid}",
            "properties": props}


def _weekly(start="08:00", end="16:00", day="TUESDAY") -> list:
    return [{"weekday": day, "local_start": start, "local_end": end, "utc_offset_minutes": 0}]


def _foundation(*, c1=None, c2=None, schedules=None, cadence1="1.0") -> dict:
    components = [{"component_id": "site-meter-1", "component_type": "METER"},
                  _connector("c1", cadence=cadence1), _connector("c2")]
    if schedules is None:
        schedules = [{"connector_asset_id": "c1", "weekly": _weekly() if c1 is None else c1},
                     {"connector_asset_id": "c2", "weekly": _weekly() if c2 is None else c2}]
    return {"id": "f-1", "content": {"components": components, "connector_enable_schedules": schedules},
            "valid_from": datetime(2026, 10, 1, tzinfo=timezone.utc), "valid_to": None}


def _row(n: int, minute: float, value: str, *, asset=A1, quality="GOOD", use=None, reason=None, connector=None,
         role="ev_connector_state") -> dict:
    at = LO + timedelta(minutes=minute)
    return {"evidence_id": f"00000000-0000-4000-8000-{n:012x}", "role": role, "value": value, "source_time": at,
            "sent_at": at, "received_at": at + timedelta(seconds=5), "quality": quality, "asset_id": asset,
            "connector_id": connector, "use": use, "reason": reason}


def _calc(rows, foundation=None, lo=LO, hi=HI) -> dict:
    return availability(_foundation() if foundation is None else foundation, ASSETS, rows, lo, hi)


def _conserved(body: dict) -> None:
    for row in body["connectors"]:
        assert (row["known_available_seconds"] + row["known_unavailable_seconds"] + row["unknown_seconds"]
                == row["scheduled_seconds"])
        assert sum((datetime.fromisoformat(s["to"].replace("Z", "+00:00"))
                    - datetime.fromisoformat(s["from"].replace("Z", "+00:00"))).total_seconds()
                   for s in row["spans"]) == row["scheduled_seconds"]
    for key in TOP_KEYS[2:6]:
        assert body[key] == sum(r[key] for r in body["connectors"])
    assert (body["known_available_seconds"] + body["known_unavailable_seconds"] + body["unknown_seconds"]
            == body["scheduled_seconds"])


# --- pure -------------------------------------------------------------------------------------------------


def test_exact_keys_cadence_bounds_and_conservation() -> None:
    rows = [_row(1, 0, "UNPLUGGED"), _row(2, 1, "UNPLUGGED"), _row(3, 10, "FAULTED"), _row(4, 30, "CHARGING")]
    body = _calc(rows)
    assert list(body) == TOP_KEYS and body["calculation_version"] == CALCULATION_VERSION == "ev-availability/1"
    assert body["schedule_state"] == "SCHEDULED"
    c1 = next(r for r in body["connectors"] if r["asset_id"] == A1)
    assert list(c1) == ROW_KEYS and all(list(s) == SPAN_KEYS for s in c1["spans"])
    # Each transition classifies only one cadence (one minute); CHARGING proves nothing; gaps are Unknown.
    assert c1["known_available_seconds"] == 120 and c1["known_unavailable_seconds"] == 60
    assert c1["unknown_seconds"] == 3600 - 180
    assert [(s["from"][11:16], s["to"][11:16], s["state"]) for s in c1["spans"]] == [
        ("08:00", "08:02", "AVAILABLE"), ("08:02", "08:10", "UNKNOWN"), ("08:10", "08:11", "UNAVAILABLE"),
        ("08:11", "09:00", "UNKNOWN")]
    assert c1["spans"][0]["evidence_ids"] == [rows[0]["evidence_id"], rows[1]["evidence_id"]]
    assert c1["spans"][1]["evidence_ids"] == []
    c2 = next(r for r in body["connectors"] if r["asset_id"] == A2)
    assert (c2["scheduled_seconds"], c2["unknown_seconds"]) == (3600, 3600)  # no status history: Unknown, not 100%
    _conserved(body)
    assert body["known_time_ratio"] == ratio(120, 180) == "0.666667"
    assert body["full_lower"] == "0.016667" and body["full_upper"] == ratio(120 + 3600 - 180 + 3600, 7200)


def test_state_never_carried_past_window_or_next_transition() -> None:
    rows = [_row(1, 59.5, "UNPLUGGED"), _row(2, 20, "AVAILABLE"), _row(3, 20.25, "FAULTED")]
    c1 = _calc(rows)["connectors"][0]
    assert c1["known_available_seconds"] == 15 + 30 and c1["known_unavailable_seconds"] == 60
    assert c1["spans"][-1] == {"from": "2026-10-06T08:59:30.000000Z", "to": "2026-10-06T09:00:00.000000Z",
                               "state": "AVAILABLE", "evidence_ids": [rows[0]["evidence_id"]]}


def test_same_time_conflict_and_duplicate() -> None:
    conflict = _calc([_row(1, 5, "UNPLUGGED"), _row(2, 5, "FAULTED"), _row(3, 5.5, "UNPLUGGED")])["connectors"][0]
    # The conflict's whole cadence interval up to the next transition is Unknown; the later row resumes.
    assert (conflict["known_available_seconds"], conflict["known_unavailable_seconds"]) == (60, 0)
    duplicate = _calc([_row(1, 5, "FAULTED"), _row(2, 5, "FAULTED")])["connectors"][0]
    assert duplicate["known_unavailable_seconds"] == 60
    assert next(s for s in duplicate["spans"] if s["state"] == "UNAVAILABLE")["evidence_ids"] == [
        "00000000-0000-4000-8000-000000000001", "00000000-0000-4000-8000-000000000002"]


def test_null_connector_id_binds_by_scoped_asset() -> None:
    # A row with no connector_id binds through its scoped asset to the enabled Foundation connector (and only that one).
    body = _calc([_row(1, 0, "UNPLUGGED", asset=A1, connector=None)])
    c1, c2 = body["connectors"]
    assert c1["known_available_seconds"] == 60 and c2["known_available_seconds"] == 0


def test_unusable_transition_ends_the_previous_observation() -> None:
    # The mismatched (unusable) row at 08:00:30 still ends the 08:00 observation's hold: only 30 s is known, the rest
    # is Unknown until the later valid transition at 08:05.
    rows = [_row(1, 0, "UNPLUGGED"), _row(2, 0.5, "UNPLUGGED", connector="c2"), _row(3, 5, "UNPLUGGED")]
    c1 = _calc(rows)["connectors"][0]
    assert c1["known_available_seconds"] == 30 + 60
    assert [(s["from"][11:19], s["to"][11:19], s["state"]) for s in c1["spans"]] == [
        ("08:00:00", "08:00:30", "AVAILABLE"), ("08:00:30", "08:05:00", "UNKNOWN"), ("08:05:00", "08:06:00", "AVAILABLE"),
        ("08:06:00", "09:00:00", "UNKNOWN")]
    _conserved(_calc(rows))


def test_untrustworthy_rows_never_classify() -> None:
    bad = [_row(1, 0, "UNPLUGGED", quality="SUSPECT"), _row(2, 2, "UNPLUGGED", use="EXCLUDED"),
           _row(3, 4, "UNPLUGGED", reason="CLOCK_UNATTESTED"), _row(4, 6, "UNPLUGGED", connector="c2"),
           _row(5, 8, "UNPLUGGED", asset=A2, role="ev_connector_power")]
    late = _row(6, 10, "UNPLUGGED")
    late["received_at"] = late["source_time"] - timedelta(seconds=1)
    naive = _row(7, 12, "UNPLUGGED")
    naive["sent_at"] = None
    body = _calc(bad + [late, naive, _row(8, 14, "UNPLUGGED", connector="c1")])
    c1, c2 = body["connectors"]
    assert c1["known_available_seconds"] == 60 and c2["known_available_seconds"] == 0
    # A missing or invalid cadence leaves scheduled time intact and every observed second Unknown.
    for cadence in (None, "0", "abc"):
        row = _calc([_row(1, 0, "UNPLUGGED")], _foundation(cadence1=cadence))["connectors"][0]
        assert (row["scheduled_seconds"], row["unknown_seconds"]) == (3600, 3600)


def test_selected_id_intersection_and_no_selection() -> None:
    rows = [_row(1, 0, "UNPLUGGED"), _row(2, 1, "UNPLUGGED")]
    snap = {"selected": {"evidence_ids": [rows[0]["evidence_id"].upper()], "foundation_ids": ["f-1"]}}
    kept = selected_rows(rows, snap)
    assert kept == [rows[0]]
    assert _calc(kept)["known_available_seconds"] == 60
    assert selected_rows(rows, {"selected": None}) is None
    empty = _calc(None)
    assert empty["schedule_state"] == "NOT_ESTABLISHED" and empty["connectors"] == []
    assert all(empty[k] is None for k in TOP_KEYS[2:9])


def test_selected_foundation_never_falls_back() -> None:
    f = _foundation()
    snap = {"selected": {"foundation_ids": ["F-1"], "evidence_ids": []}}
    assert selected_foundation(f, snap, LO, HI) is f
    assert selected_foundation(f, {"selected": None}, LO, HI) is None
    assert selected_foundation(f, {"selected": {"foundation_ids": ["f-1", "f-2"]}}, LO, HI) is None
    assert selected_foundation(f, {"selected": {"foundation_ids": ["f-2"]}}, LO, HI) is None
    assert selected_foundation({**f, "valid_to": HI - timedelta(seconds=1)}, snap, LO, HI) is None
    assert selected_foundation({**f, "valid_from": LO + timedelta(seconds=1)}, snap, LO, HI) is None
    assert selected_foundation(None, snap, LO, HI) is None


def test_per_connector_schedule_clipping_and_empty_weeks() -> None:
    f = _foundation(c1=_weekly("08:30", "10:00"), c2=_weekly("07:00", "08:15"))
    rows = connector_service_windows(f, ASSETS, LO, HI)
    assert [(r["component_id"], r["schedule"], [(a.isoformat()[11:16], b.isoformat()[11:16]) for a, b in r["windows"]])
            for r in rows] == [("c1", "WEEKLY", [("08:30", "09:00")]), ("c2", "WEEKLY", [("08:00", "08:15")])]
    body = _calc([_row(1, 10, "UNPLUGGED", asset=A2), _row(2, 40, "FAULTED")], f)
    c1, c2 = body["connectors"]
    assert (c1["scheduled_seconds"], c1["known_unavailable_seconds"]) == (1800, 60)
    assert (c2["scheduled_seconds"], c2["known_available_seconds"]) == (900, 60)
    _conserved(body)
    # A declared weekly list with no occurrence in the window is SCHEDULED with a zero denominator.
    other = _calc([], _foundation(c1=_weekly(day="MONDAY"), c2=_weekly(day="MONDAY")))
    assert (other["schedule_state"], other["scheduled_seconds"], other["full_lower"]) == ("SCHEDULED", 0, None)
    # Every enabled connector `weekly: []` declares zero service seconds, never 0% availability.
    empty = _calc([_row(1, 0, "UNPLUGGED")], _foundation(c1=[], c2=[]))
    assert empty["schedule_state"] == "DECLARED_EMPTY"
    assert [empty[k] for k in TOP_KEYS[2:9]] == [0, 0, 0, 0, None, None, None]
    assert [r["spans"] for r in empty["connectors"]] == [[], []]
    mixed = _calc([], _foundation(c1=[], c2=_weekly()))
    assert mixed["schedule_state"] == "SCHEDULED" and mixed["scheduled_seconds"] == 3600
    # A missing, duplicated or self-overlapping declaration is not established.
    for schedules in ([{"connector_asset_id": "c1", "weekly": _weekly()}],
                      [{"connector_asset_id": "c1", "weekly": _weekly()}, {"connector_asset_id": "c1", "weekly": []},
                       {"connector_asset_id": "c2", "weekly": _weekly()}],
                      [{"connector_asset_id": "c1", "weekly": _weekly() + _weekly("09:00", "10:00")},
                       {"connector_asset_id": "c2", "weekly": _weekly()}],
                      [{"connector_asset_id": "c1", "weekly": [{"weekday": "TUESDAY"}]},
                       {"connector_asset_id": "c2", "weekly": _weekly()}]):
        body = _calc([_row(1, 0, "UNPLUGGED")], _foundation(schedules=schedules))
        assert body["schedule_state"] == "NOT_ESTABLISHED" and all(body[k] is None for k in TOP_KEYS[2:9])


def test_ratios_are_six_place_half_even_strings() -> None:
    assert ratio(14, 15) == "0.933333" and ratio(1, 8) == "0.125000" and ratio(0, 0) is None
    assert ratio(Decimal("0.0000005"), 1) == "0.000000" and ratio(Decimal("0.0000015"), 1) == "0.000002"


# --- persisted -------------------------------------------------------------------------------------------


def _read(built, known_at=None) -> tuple[dict, dict, list]:
    from assetops_backend.analytics.composition import build_ev_read_service
    from assetops_backend.analytics.ev_availability import availability_on

    reads = build_ev_read_service(URL)
    try:
        def work(c):
            snap, _ = reads.open_on(c, built.tenant_id, built.site_id, built.site_code, LO, HI, known_at)
            return snap, availability_on(reads, c, snap), reads.accepted_on(c, snap)
        return reads.within(work)
    finally:
        reads.dispose()


def _state_ids(accepted: list, snap: dict) -> set:
    selected = set(snap["selected"]["evidence_ids"])
    return {r["evidence_id"] for r in accepted if r["role"] == "ev_connector_state" and r["evidence_id"] in selected}


def _classified(body: dict) -> set:
    return {i for row in body["connectors"] for s in row["spans"] for i in s["evidence_ids"]}


@needs_db
def test_observed_complete_and_historical(chain) -> None:  # noqa: F811
    built = settled(chain, "complete")
    snap, body, accepted = _read(built)
    assert snap["state"] == "CURRENT" and body["schedule_state"] == "SCHEDULED"
    assert body["scheduled_seconds"] == 7200 and body["known_available_seconds"] > 0
    assert _classified(body) and _classified(body) <= _state_ids(accepted, snap)
    assert all(s["evidence_ids"] == [] for r in body["connectors"] for s in r["spans"] if s["state"] == "UNKNOWN")
    _conserved(body)
    old_snap, old, _ = _read(built, datetime.fromisoformat(HISTORICAL_KNOWN_AT.replace("Z", "+00:00")))
    # The saved first watermark equals the current one here, so nothing newer exists: still CURRENT, same body.
    assert old_snap["state"] == "CURRENT" and old == body


@needs_db
def test_historical_cutoff_before_late_release(chain) -> None:  # noqa: F811
    built = pending(chain)
    snap, body, _ = _read(built)
    old_snap, old, accepted = _read(built, datetime.fromisoformat(HISTORICAL_KNOWN_AT.replace("Z", "+00:00")))
    assert snap["state"] == "PENDING_RECOMPUTE" and old_snap["state"] == "HISTORICAL"
    assert _classified(old) <= _state_ids(accepted, old_snap)
    _conserved(old)


@needs_db
def test_faulted_status_is_known_unavailable(chain) -> None:  # noqa: F811
    built = settled(chain, "interrupted")
    snap, body, accepted = _read(built)
    assert body["known_unavailable_seconds"] > 0 and _classified(body) <= _state_ids(accepted, snap)
    _conserved(body)


@needs_db
def test_pending_keeps_selected_head(chain) -> None:  # noqa: F811
    built = pending(chain)
    snap, body, accepted = _read(built)
    assert snap["state"] == "PENDING_RECOMPUTE"
    # No pending-only (09:05) row classifies a second.
    assert _classified(body) <= _state_ids(accepted, snap)
    assert {r["evidence_id"] for r in accepted} - set(snap["selected"]["evidence_ids"])
    _conserved(body)


@needs_db
def test_status_gap_and_empty_schedule(chain) -> None:  # noqa: F811
    built = status_gap(chain)
    snap, body, accepted = _read(built)
    assert list(body) == TOP_KEYS
    assert all(list(r) == ROW_KEYS and all(list(s) == SPAN_KEYS for s in r["spans"]) for r in body["connectors"])
    c1 = next(r for r in body["connectors"] if r["label"] == "Connector c1")
    gap = [s for s in c1["spans"] if s["state"] == "UNKNOWN"
           and s["from"] <= "2026-10-06T08:40:00.000000Z" and s["to"] >= "2026-10-06T08:45:00.000000Z"]
    assert gap, c1["spans"]
    # The omitted reports leave exactly that five-minute span Unknown, with an AVAILABLE span adjacent on each side.
    unknown = {"from": "2026-10-06T08:40:00.000000Z", "to": "2026-10-06T08:45:00.000000Z", "state": "UNKNOWN",
               "evidence_ids": []}
    assert unknown in c1["spans"], c1["spans"]
    at = c1["spans"].index(unknown)
    assert 0 < at < len(c1["spans"]) - 1, c1["spans"]
    before, after = c1["spans"][at - 1], c1["spans"][at + 1]
    assert before["state"] == "AVAILABLE" and before["to"] == unknown["from"], before
    assert after["state"] == "AVAILABLE" and after["from"] == unknown["to"], after
    c1_states = [r for r in accepted if r["role"] == "ev_connector_state" and r["asset_id"] == c1["asset_id"]]
    assert not [r for r in c1_states if LO + timedelta(minutes=40) <= r["source_time"] < LO + timedelta(minutes=45)]
    assert _classified(body) <= _state_ids(accepted, snap) and c1["known_available_seconds"] > 0
    _conserved(body)
    new_id = declared_empty(built)
    snap, body, _ = _read(built)
    assert snap["selected"]["foundation_ids"] == [new_id]
    assert body["schedule_state"] == "DECLARED_EMPTY"
    assert [body[k] for k in TOP_KEYS[2:9]] == [0, 0, 0, 0, None, None, None]
    assert all(r["spans"] == [] and r["scheduled_seconds"] == 0 for r in body["connectors"])
