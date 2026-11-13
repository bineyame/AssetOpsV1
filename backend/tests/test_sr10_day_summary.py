"""SR-10a (rev 10b.1/10b.3 tests, D-SR.31-33): the pure day reducers over stored `mini_depth.{fuel,backup}_day` hours.

Bound sums, missing and pending hours, the union of limitations, de-duplication by chain_id (latest hour wins), the
null rule for start successes, no `outage` key, the day state order, absent rows (STILL_PROCESSING), and the range
composer's totals over counted days only."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from assetops_backend.mini_depth import day_summary as ds
from assetops_backend.mini_depth import period_rows as pr
from assetops_backend.mini_depth.read import _Head, _Hour
from assetops_backend.mini_depth.rules import Window

DAY = date(2026, 11, 3)
T0 = datetime(2026, 11, 2, 21, 0, tzinfo=timezone.utc)  # Nairobi local midnight of DAY


def _w(i: int) -> Window:
    return Window(T0 + timedelta(hours=i), T0 + timedelta(hours=i + 1))


def _hour(i: int, result: dict | None, *, state: str = "CURRENT", job_state: str = "SETTLED") -> _Hour:
    head = None if result is None else _Head(i + 1, uuid4(), T0, "sha", result, ())
    if head is None and state == "CURRENT":
        state, job_state = "UNKNOWN", ("NONE" if job_state == "SETTLED" else job_state)
    return _Hour(DAY, _w(i), head, job_state, state, None, ())


def _fuel(status: str = "SUPPORTED", use: tuple | None = (1.5, 2.25), codes: tuple[str, ...] = ()) -> dict:
    return {"status": status, "limitations": [{"code": c, "evidence_ids": []} for c in codes],
            "cards": {"opening_l": {"low": 100, "high": 100}, "deliveries_l": None, "closing_l": None,
                      "residual_l": {"low": 9, "high": 9},
                      "expected_use_l": None if use is None else {"low": use[0], "high": use[1]}}}


def _backup(rows: list[dict], successes: int | None = None, status: str = "SUPPORTED") -> dict:
    return {"status": status, "limitations": [],
            "cards": {"outage_count": None, "start_success_count": successes, "critical_recovery": None},
            "rows": rows}


def _chain(cid: str, result: str, seconds: int | None = None, start: str = "2026-11-03T01:00:00Z") -> dict:
    return {"chain_id": cid, "outage_start": start, "result": result, "service_outcome": "RESTORED",
            "critical_recovery": None if seconds is None else {"seconds": seconds, "target_seconds": 120},
            "steps": [], "evidence_ids": []}


def test_fuel_sums_expected_use_bounds_only_over_hours_that_have_one() -> None:
    hours = [_hour(0, _fuel(use=(0.1, 0.2))), _hour(1, _fuel(use=(0.2, 0.3))), _hour(2, _fuel(use=None)),
             _hour(3, _fuel("LIMITED", use=(1, 2), codes=("B", "A"))), _hour(4, None)]
    s = ds.fuel_day_summary(DAY, hours)
    assert s["expected_use_l"] == {"low": 1.3, "high": 2.5}  # decimal sums, no float drift
    assert s["hours_with_use"] == 3
    assert (s["hours_expected"], s["hours_assessed"], s["hours_pending"], s["hours_missing"]) == (5, 4, 0, 1)
    assert s["status_counts"] == {"SUPPORTED": 3, "LIMITED": 1, "UNKNOWN": 0}
    assert s["limitations"] == ["A", "B"]
    assert not {"residual_l", "opening_l", "closing_l", "deliveries_l"} & set(s)  # never summed


def test_fuel_no_use_is_null_and_union_of_limitations() -> None:
    s = ds.fuel_day_summary(DAY, [_hour(0, _fuel(use=None, codes=("X",))), _hour(1, _fuel(use=None, codes=("X", "Y")))])
    assert s["expected_use_l"] is None and s["hours_with_use"] == 0
    assert s["limitations"] == ["X", "Y"]


def test_pending_hours_are_neither_assessed_nor_missing() -> None:
    hours = [_hour(0, _fuel(), state="PENDING_RECOMPUTE", job_state="PENDING"), _hour(1, None, job_state="LEASED"),
             _hour(2, _fuel()), _hour(3, None)]
    s = ds.fuel_day_summary(DAY, hours)
    assert (s["hours_assessed"], s["hours_pending"], s["hours_missing"]) == (1, 2, 1)
    assert s["expected_use_l"] == {"low": 1.5, "high": 2.25}  # the pending hour's stored head is not counted
    assert ds.day_state("fuel", s, "COMPLETE") == ("STILL_PROCESSING", True)


def test_backup_dedupes_chains_latest_hour_wins_and_has_no_outage_key() -> None:
    hours = [_hour(1, _backup([_chain("c1", "INCOMPLETE")], successes=None)),
             _hour(2, _backup([_chain("c1", "PASS", 60), _chain("c2", "FAIL", 300, "2026-11-03T02:00:00Z")],
                              successes=1)),
             _hour(3, _backup([], successes=2))]
    s = ds.backup_day_summary(DAY, hours)
    assert [(q["chain_id"], q["result"]) for q in s["sequences"]] == [("c1", "PASS"), ("c2", "FAIL")]
    assert s["sequence_counts"] == {"PASS": 1, "FAIL": 1, "INCOMPLETE": 0}
    assert s["start_success_count"] == 3
    assert s["slowest_recovery"] == {"seconds": 300, "target_seconds": 120}
    assert set(s["sequences"][0]) == {"chain_id", "outage_start", "result", "service_outcome", "critical_recovery"}
    assert "outage" not in repr(sorted(k for k in s if k != "sequences")).replace("outage_start", "")


def test_backup_start_successes_null_when_every_hour_is_null() -> None:
    s = ds.backup_day_summary(DAY, [_hour(0, _backup([])), _hour(1, _backup([]))])
    assert s["start_success_count"] is None and s["slowest_recovery"] is None
    assert ds.day_state("backup", s, "COMPLETE") == ("NO_SEQUENCE", False)


def test_day_state_order() -> None:
    fuel = ds.fuel_day_summary(DAY, [_hour(0, _fuel()), _hour(1, None)])
    assert ds.day_state("fuel", fuel, "NOT_EXPECTED") == ("NOT_EXPECTED", True)
    assert ds.day_state("fuel", None, "COMPLETE") == ("STILL_PROCESSING", False)  # absent row, never "nothing known"
    assert ds.day_state("fuel", fuel, "PARTIAL") == ("ASSESSED", True)
    none = ds.fuel_day_summary(DAY, [_hour(0, None)])
    assert ds.day_state("fuel", none, "NO_DATA") == ("NO_ASSESSMENT", True)
    limited = ds.fuel_day_summary(DAY, [_hour(0, _fuel("LIMITED"))])
    assert ds.day_state("fuel", limited, "COMPLETE") == ("ASSESSED", True)

    def b(*results: str) -> dict:
        return ds.backup_day_summary(DAY, [_hour(i, _backup([_chain(f"c{i}", r)])) for i, r in enumerate(results)])

    assert ds.day_state("backup", b("PASS", "INCOMPLETE", "FAIL"), "COMPLETE")[0] == "SEQUENCE_FAILED"
    assert ds.day_state("backup", b("PASS", "INCOMPLETE"), "COMPLETE")[0] == "SEQUENCE_INCOMPLETE"
    assert ds.day_state("backup", b("PASS"), "COMPLETE")[0] == "SEQUENCES_PASSED"


def _row(site: UUID, day: date, kind: str, hours: list[_Hour]) -> SimpleNamespace:
    body = {"hours": [pr.hour_json(h) for h in hours]}
    return SimpleNamespace(row=SimpleNamespace(site_id=site, local_day=day, kind=kind, body=body), pending=())


def test_compose_counts_assessed_days_only_and_reads_absent_as_still_processing() -> None:
    site = uuid4()
    days = [DAY, DAY + timedelta(days=1), DAY + timedelta(days=2), DAY + timedelta(days=3)]
    rows = [_row(site, days[0], "mini_depth.fuel_day", [_hour(0, _fuel(use=(1, 2))), _hour(1, _fuel(use=(3, 4)))]),
            _row(site, days[1], "mini_depth.fuel_day", [_hour(0, _fuel(use=(5, 6))), _hour(1, None)]),
            _row(site, days[3], "mini_depth.fuel_day", [_hour(0, _fuel(use=(7, 8)))])]
    result = SimpleNamespace(rows=rows, is_pending=lambda s, d, k: False)
    grades = {days[0]: "COMPLETE", days[1]: "PARTIAL", days[2]: "COMPLETE", days[3]: "NOT_EXPECTED"}
    body = ds.compose("fuel", {"id": site, "site_code": "KOBO-001", "site_name": "Kobo", "timezone": "Africa/Nairobi"},
                      {"from": "a", "to": "b", "known_at": None}, days, result, grades, historical=False)
    assert body["schema_version"] == "site-fuel-range-1" and "id" not in body["site"]
    assert [(d["state"], d["partial"]) for d in body["days"]] == [
        ("ASSESSED", False), ("ASSESSED", True), ("STILL_PROCESSING", False), ("NOT_EXPECTED", False)]
    assert body["days"][0]["hour_link"] == ("/sites/KOBO-001/performance/fuel"
                                            "?from=2026-11-03T09%3A00%3A00Z&to=2026-11-03T10%3A00%3A00Z")
    assert body["totals"] == {"days_counted": 2, "days_requested": 4, "partial": True,
                              "expected_use_l": {"low": 9, "high": 12}}


def test_compose_pending_row_reads_still_processing() -> None:
    site = uuid4()
    rows = [_row(site, DAY, "mini_depth.backup_day", [_hour(0, _backup([_chain("c", "PASS")]))])]
    result = SimpleNamespace(rows=rows, is_pending=lambda s, d, k: True)
    body = ds.compose("backup", {"id": site, "site_code": "K", "site_name": None, "timezone": "Africa/Nairobi"},
                      {}, [DAY], result, {DAY: "COMPLETE"}, historical=False)
    assert body["days"][0]["state"] == "STILL_PROCESSING" and body["days"][0]["hours_pending"] == 1
    assert body["totals"] == {"days_counted": 0, "days_requested": 1, "partial": True,
                              "sequence_counts": {"PASS": 0, "FAIL": 0, "INCOMPLETE": 0}, "start_success_count": None}


def test_day_kinds_are_registered_with_whole_day_builders() -> None:
    builders = pr.kind_builders(object())
    assert pr.DAY_KINDS == {"mini_depth.fuel_day": "fuel", "mini_depth.backup_day": "backup"}
    assert set(pr.DAY_KINDS) <= set(pr.KINDS) and set(pr.DAY_KINDS) <= set(builders)
    assert all(builders[k].whole_day and builders[k].kind == k and builders[k].domain == d
               for k, d in pr.DAY_KINDS.items())
    assert not builders["mini_depth.fuel"].whole_day
    from assetops_backend.chain.composition import period_kind_versions

    assert {period_kind_versions()[k] for k in pr.DAY_KINDS} == {pr.BUILDER_VERSION}  # no version bump


def test_absent_day_is_unknown_not_zero() -> None:
    """D-SR.51 (3)."""
    site = uuid4()
    result = SimpleNamespace(rows=[], is_pending=lambda s, d, k: False)
    for domain in ("fuel", "backup"):
        body = ds.compose(domain, {"id": site, "site_code": "K", "site_name": None, "timezone": "Africa/Nairobi"},
                          {}, [DAY], result, {DAY: "COMPLETE"}, historical=False)
        day = body["days"][0]
        assert day["stored"] is False and day["state"] == "STILL_PROCESSING" and day["partial"] is False
        assert all(v is None for k, v in day.items()
                   if k not in ("local_day", "stored", "state", "partial", "hour_link"))
    assert ds.fuel_day_summary(DAY, [_hour(0, _fuel())])["stored"] is True


def test_slowest_recovery_skips_null_takes_same_sequence_target_and_ties_to_earliest_start() -> None:
    """D-SR.51 (2)."""
    def seq(cid, start, seconds, target):
        return {"chain_id": cid, "outage_start": start, "critical_recovery":
                None if seconds is None else {"seconds": seconds, "target_seconds": target}}
    assert ds.slowest_recovery([seq("a", "2026-11-03T01:00:00Z", None, 1)]) is None
    got = ds.slowest_recovery([seq("late", "2026-11-03T05:00:00Z", 300, 111), seq("n", "2026-11-03T02:00:00Z", None, 9),
                               seq("early", "2026-11-03T01:00:00Z", 300, 222), seq("fast", "2026-11-03T00:00:00Z", 10, 5)])
    assert got == {"seconds": 300, "target_seconds": 222}


def test_totals_count_a_sequence_crossing_midnight_once_by_chain_id() -> None:
    """D-SR.51 (4): the same chain_id on two days' rows counts once (the latest day wins)."""
    site, d2 = uuid4(), DAY + timedelta(days=1)
    rows = [_row(site, DAY, "mini_depth.backup_day", [_hour(23, _backup([_chain("x", "INCOMPLETE")], successes=1))]),
            _row(site, d2, "mini_depth.backup_day", [_hour(0, _backup([_chain("x", "PASS", 60), _chain("y", "FAIL", 90)],
                                                                      successes=2))])]
    result = SimpleNamespace(rows=rows, is_pending=lambda s, d, k: False)
    body = ds.compose("backup", {"id": site, "site_code": "K", "site_name": None, "timezone": "Africa/Nairobi"},
                      {}, [DAY, d2], result, {DAY: "COMPLETE", d2: "COMPLETE"}, historical=False)
    assert body["totals"]["sequence_counts"] == {"PASS": 1, "FAIL": 1, "INCOMPLETE": 0}
    assert body["totals"]["start_success_count"] == 3


def test_reading_at_site_local_0030_dirties_the_local_day_not_the_utc_day() -> None:
    """D-SR.53: the register keys the dirty day by the Site-local day (`span_local`), so a reading at Nairobi 00:30 on
    2026-11-03 (UTC 21:30 on 2026-11-02) dirties both day kinds of 2026-11-03 and not of 2026-11-02. The event is built by
    hand here (the ingest path has no Python event helper: its `reading.accepted` rows come from the 0044 SQL producer on
    `accepted_evidence`, pinned in the Postgres file by an outbox insert of the same shape)."""
    from assetops_backend.chain.adapters.file_chain_config import load_event_register
    from assetops_backend.chain.events import Event, resolve

    at = datetime(2026, 11, 2, 21, 30, tzinfo=timezone.utc)
    event = Event(uuid4(), "reading.accepted", 1, at, at, "accepted_evidence", uuid4(), uuid4(),
                  {"roles": ["fuel_level"], "asset_ids": [], "span": ["2026-11-02T21:30:00Z", "2026-11-02T21:30:00Z"]})
    marks = resolve(load_event_register(), event, site_type="MINIGRID", tz="Africa/Nairobi", today=date(2026, 11, 4))
    for kind in pr.DAY_KINDS:
        assert (date(2026, 11, 3), kind) in marks and (date(2026, 11, 2), kind) not in marks


def _facts(days: list[date], grades: dict, none_declared: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(days=days, grades=grades, none_declared=none_declared or {})


def test_no_reading_days_every_applicable_measure_no_data() -> None:
    from assetops_backend.chain.measures import measures_for

    keys = [m.key for m in measures_for("MINIGRID")]
    d0, d1, d2, d3 = (DAY + timedelta(days=i) for i in range(4))
    nd = {k: {"i": "NO_DATA"} for k in keys}
    mixed = {k: {"i": "NO_DATA"} for k in keys}
    mixed[keys[0]] = {"i": "PARTIAL"}                      # one weak measure is not "no readings"
    half = {k: {"i": "NO_DATA"} for k in keys[1:]}          # a missing snapshot is NO_DATA (Q9)
    facts = _facts([d0, d1, d2, d3], {d0: nd, d1: mixed, d2: half, d3: {}},
                   {d1: (keys[1],)})
    assert ds.no_reading_days(facts) == {d0, d2, d3}
    # none_declared (only productive_kwh, only when it has no row, R3t) is left out of "applicable". A measure with no
    # row already grades NOT_EXPECTED, so the declared exclusion and the NOT_EXPECTED exclusion agree: declared or not,
    # the day is NO_DATA while another measure reads NO_DATA, and neither leaves a measure to read when the rest are
    # NOT_EXPECTED.
    pk = keys[0]
    no_pk_row = {pk: {}, **{k: {"i": "NO_DATA"} for k in keys[1:]}}
    assert ds.no_reading_days(_facts([d1], {d1: no_pk_row}, {d1: (pk,)})) == {d1}
    assert ds.no_reading_days(_facts([d1], {d1: no_pk_row})) == {d1}
    only_pk = {pk: {}, **{k: {"i": "NOT_EXPECTED"} for k in keys[1:]}}
    assert ds.no_reading_days(_facts([d1], {d1: only_pk}, {d1: (pk,)})) == frozenset()
    assert ds.no_reading_days(_facts([d1], {d1: only_pk})) == frozenset()


def test_not_expected_measures_are_left_out_of_applicable() -> None:
    from assetops_backend.chain.measures import measures_for

    keys = [m.key for m in measures_for("MINIGRID")]
    d0 = DAY
    ne = {k: {"i": "NO_DATA"} for k in keys}
    ne[keys[0]] = {"i": "NOT_EXPECTED"}
    assert ds.no_reading_days(_facts([d0], {d0: ne})) == {d0}           # NOT_EXPECTED is not a reading, not applicable
    weak = dict(ne)
    weak[keys[1]] = {"i": "PARTIAL"}
    assert ds.no_reading_days(_facts([d0], {d0: weak})) == frozenset()  # a real weak measure still blocks NO_DATA
    only_ne = {k: {"i": "NOT_EXPECTED"} for k in keys}
    assert ds.no_reading_days(_facts([d0], {d0: only_ne})) == frozenset()  # none applicable left


def test_pending_without_stored_row_reads_still_processing_not_no_data() -> None:
    """D-SR.70 step 2: pending beats NO_DATA even when no row is stored."""
    site = uuid4()
    result = SimpleNamespace(rows=[], is_pending=lambda s, d, k: True)
    for domain in ("fuel", "backup"):
        body = ds.compose(domain, {"id": site, "site_code": "K", "site_name": None, "timezone": "Africa/Nairobi"},
                          {}, [DAY], result, {DAY: "NO_DATA"}, historical=False, no_readings=frozenset({DAY}))
        assert body["days"][0]["state"] == "STILL_PROCESSING"


def test_no_data_beats_absent_and_stored_rows_and_pending_beats_no_data() -> None:
    full = ds.fuel_day_summary(DAY, [_hour(h, _fuel()) for h in range(24)])
    empty = ds.fuel_day_summary(DAY, [_hour(0, None)])
    pend = ds.fuel_day_summary(DAY, [_hour(0, _fuel(), state="PENDING_RECOMPUTE", job_state="PENDING")])
    assert ds.day_state("fuel", None, "NO_DATA", no_readings=True, pending=False) == ("NO_DATA", False)
    assert ds.day_state("fuel", full, "NO_DATA", no_readings=True, pending=False)[0] == "NO_DATA"
    assert ds.day_state("fuel", empty, "NO_DATA", no_readings=True, pending=False)[0] == "NO_DATA"
    assert ds.day_state("backup", ds.backup_day_summary(DAY, [_hour(0, _backup([]))]), "NO_DATA",
                        no_readings=True, pending=False)[0] == "NO_DATA"
    assert ds.day_state("fuel", pend, "NO_DATA", no_readings=True, pending=False)[0] == "STILL_PROCESSING"
    assert ds.day_state("fuel", full, "NO_DATA", no_readings=True, pending=True)[0] == "STILL_PROCESSING"
    assert ds.day_state("fuel", full, "NOT_EXPECTED", no_readings=True, pending=True)[0] == "NOT_EXPECTED"
    assert ds.day_state("fuel", None, "COMPLETE", no_readings=False, pending=False)[0] == "STILL_PROCESSING"


def test_compose_no_data_day_is_not_counted_and_nulls_figures() -> None:
    site = uuid4()
    days = [DAY, DAY + timedelta(days=1), DAY + timedelta(days=2)]
    rows = [_row(site, days[0], "mini_depth.fuel_day", [_hour(0, _fuel(use=(1, 2)))]),
            _row(site, days[1], "mini_depth.fuel_day", [_hour(h, _fuel(use=(3, 4))) for h in range(24)])]
    result = SimpleNamespace(rows=rows, is_pending=lambda s, d, k: False)
    body = ds.compose("fuel", {"id": site, "site_code": "K", "site_name": None, "timezone": "Africa/Nairobi"},
                      {"from": "a", "to": "b", "known_at": None}, days, result, {}, historical=False,
                      no_readings=frozenset(days[1:]))
    states = [(d["state"], d["stored"]) for d in body["days"]]
    assert states == [("ASSESSED", True), ("NO_DATA", True), ("NO_DATA", False)]
    for d in body["days"][1:]:
        assert d["partial"] is False and d["expected_use_l"] is None and d["hours_assessed"] is None
        assert d["hour_link"]
    assert body["totals"]["days_counted"] == 1 and body["totals"]["partial"] is True
