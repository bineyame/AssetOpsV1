"""0K4e (`specs/0K4e-candidate-energy/spec.md` §3, E1-E8b): `dispatch-3.3`'s energy-to-cover test on the
battery-support Candidate branch. Pure: the `AnalyticInputSet` is built here as `test_s3_dispatch_v3_analytic.py`
builds it. Every expected figure is a hand literal (W2), never a call to `energy_to_cover`:

- need = the load PV does not cover, at 5/60 h a slot, from the point until PV alone covers the load with 10 %
  headroom (that slot excluded); held = (SOC - reserve) / 100 x capacity x efficiency / 100;
- Candidate iff held >= 1.1 x need.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.analytics import dispatch_v3 as d3
from assetops_backend.analytics.assessment_inputs import (
    CONTROL_BATTERY_CAPACITY,
    CONTROL_BATTERY_RESERVE,
    CONTROL_PCS_EFFICIENCY,
    AcceptedReading,
    ControlValue,
    EvidenceQuery,
    EvidenceQueryResult,
    RoleBinding,
    Window,
    build_input_set,
)
from assetops_backend.analytics.cohort import select_cohort
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_1, ROLE_SET_MINIGRID_2, roles_for

T0 = datetime(2026, 10, 2, 0, 0, tzinfo=timezone.utc)
WINDOW = Window(T0, T0 + timedelta(days=1))          # read range: 2026-10-01T18:00 .. 2026-10-03T06:00
GW = UUID(int=1)
SRC = {"gen": UUID(int=11), "bat": UUID(int=12), "pv": UUID(int=13), "meter": UUID(int=14)}
ASSET = {"gen": UUID(int=21), "bat": UUID(int=22), "pv": UUID(int=23), "pcs": UUID(int=24), "f1": UUID(int=31)}
FOUNDATION = UUID(int=41)
BSET = UUID(int=42)
ROLES_BY_SET = {s: tuple(roles_for(s)) for s in (ROLE_SET_MINIGRID_1, ROLE_SET_MINIGRID_2)}
ROLE_SRC = {"generator_state": "gen", "generator_power": "gen", "feeder_demand": "meter", "pv_available_power": "pv",
            "pcs_discharge_capability": "bat", "battery_soc": "bat"}
ROLE_ASSET = {"generator_state": "gen", "generator_power": "gen", "feeder_demand": "f1", "pv_available_power": "pv",
              "pcs_discharge_capability": "pcs", "battery_soc": "bat"}
BATTERY_SUPPORT = "PV available plus PCS discharge capability covers load with 10 % headroom"


def at(h: int, m: int = 0) -> datetime:
    """`at(30)` is 06:00 on the next day."""
    return T0 + timedelta(hours=h, minutes=m)


def stamp(h: int, m: int = 0) -> str:
    return at(h, m).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def slots(lo: datetime, hi: datetime, step: int = 5):
    t = lo
    while t <= hi:
        yield t
        t += timedelta(minutes=step)


class Night:
    """Accepted readings; sequences are assigned per source in source-time order when the set is built."""

    def __init__(self) -> None:
        self.specs: list[tuple[datetime, str, str, int | None]] = []

    def mean(self, role: str, end: datetime, value: str, minutes: int = 5) -> "Night":
        self.specs.append((end, role, value, minutes))
        return self

    def instant(self, role: str, when: datetime, value: str) -> "Night":
        self.specs.append((when, role, value, None))
        return self

    def series(self, role: str, lo: datetime, hi: datetime, value, *, skip=()) -> "Night":
        for t in slots(lo, hi):
            if t not in skip:
                self.mean(role, t, value(t) if callable(value) else value)
        return self

    def generator(self, lo: datetime, hi: datetime, *, soc: str, dis: str = "30") -> "Night":
        """STOPPED 5 min before `lo`, RUNNING every 5 min over [lo, hi], STOPPED 5 min after; SOC and discharge at
        every RUNNING report."""
        self.instant("generator_state", lo - timedelta(minutes=5), "STOPPED")
        for t in slots(lo, hi):
            self.instant("generator_state", t, "RUNNING")
            self.instant("battery_soc", t, soc)
            self.mean("pcs_discharge_capability", t, dis)
        self.instant("generator_state", hi + timedelta(minutes=5), "STOPPED")
        return self

    def readings(self) -> tuple[AcceptedReading, ...]:
        seq: Counter = Counter()
        out = []
        for when, role, value, minutes in sorted(self.specs, key=lambda s: (s[0], s[1])):
            src = ROLE_SRC[role]
            seq[src] += 1
            out.append(AcceptedReading(
                evidence_id=uuid4(), envelope_sha256=f"sha-{len(out)}", batch_id=UUID(int=99), gateway_id=GW,
                source_id=SRC[src], sequence_epoch="e1", sequence=seq[src], role=role,
                asset_id=ASSET[ROLE_ASSET[role]], source_time=when,
                interval_start=None if minutes is None else when - timedelta(minutes=minutes),
                interval_end=None if minutes is None else when, published_at=when, received_at=when,
                accepted_at=when, quality="GOOD", value=value, unit="kW", foundation_revision_id=FOUNDATION,
                binding_set_revision_id=BSET, binding_revision_id=UUID(int=43), source_mode="SIMULATED"))
        return tuple(out)


def bindings() -> tuple[RoleBinding, ...]:
    return tuple(RoleBinding(role, ASSET[a], T0 - timedelta(days=5), None, BSET, UUID(int=43), ROLE_SET_MINIGRID_2)
                 for role, a in ROLE_ASSET.items())


def controls(*, reserve: str = "30", capacity: str | None = "200", efficiency: str | None = "95"):
    since = T0 - timedelta(days=5)
    out = [ControlValue(CONTROL_BATTERY_RESERVE, reserve, "%", since, None, FOUNDATION, "IMPORT")]
    if capacity is not None:
        out.append(ControlValue(CONTROL_BATTERY_CAPACITY, capacity, "kWh", since, None, FOUNDATION, "IMPORT"))
    if efficiency is not None:
        out.append(ControlValue(CONTROL_PCS_EFFICIENCY, efficiency, "%", since, None, FOUNDATION, "IMPORT"))
    return tuple(out)


def run(night: Night, *, window: Window = WINDOW, ctrl=None):
    query = EvidenceQuery(UUID(int=7), UUID(int=8), "dispatch", window, at(23), cohort=None)
    result = EvidenceQueryResult(query, night.readings(), bindings(), ctrl or controls(), (ROLE_SET_MINIGRID_2,))
    selection = select_cohort(result.readings, window, None)
    inputs = build_input_set(result, selection, analytic_id=d3.ANALYTIC_ID, model_version=d3.MODEL_VERSION,
                             roles_by_set=ROLES_BY_SET)
    return d3.assess(inputs)


def one_point_night(*, soc: str = "80", load="10", pv_cover_at: datetime = at(30), pv_to: datetime | None = None,
                    pv_skip=()) -> Night:
    """E1's night: one RUNNING report at 18:00 (one point); load and PV as 5-minute means from 18:00; PV 0 until
    `pv_cover_at`, 12 kW from it (to `pv_to`, default `pv_cover_at`)."""
    night = Night().generator(at(18), at(18), soc=soc)
    night.series("feeder_demand", at(18), pv_to or pv_cover_at, load)
    night.series("pv_available_power", at(18), pv_to or pv_cover_at,
                 lambda t: "12" if t >= pv_cover_at else "0", skip=pv_skip)
    return night


def only_segment(result) -> dict:
    [interval] = result.intervals
    [segment] = interval.result["segments"]
    return segment


def entry(state: str, **fields) -> dict:
    base = {"at": stamp(18), "state": state, "held_kwh": None, "need_kwh": None, "input": None, "problem": None,
            "gap_at": None, "range_end": None, "controls": []}
    base.update(fields)
    return base


def test_e1_a_night_the_battery_cannot_carry_is_indeterminate_with_the_shortfall_stored():
    # need: 144 slots (18:00 .. 05:55) of 10 kW x 5/60 h = 120 kWh; held: 0.5 x 200 x 0.95 = 95 kWh < 132.
    seg = only_segment(run(one_point_night(soc="80")))
    assert seg["classification"] == d3.INDETERMINATE
    assert seg["missing"] == []                                   # nothing added to 3.2's missing for this point
    assert BATTERY_SUPPORT not in seg["reasons"]
    assert seg["energy_cover"] == [entry("SHORT", held_kwh="95", need_kwh="120")]


def test_e2_enough_stored_energy_keeps_the_candidate_with_3_2_s_reason():
    # held: 0.7 x 200 x 0.95 = 133 kWh >= 1.1 x 120 = 132 kWh.
    seg = only_segment(run(one_point_night(soc="100")))
    assert seg["classification"] == d3.CANDIDATE
    assert BATTERY_SUPPORT in seg["reasons"]
    assert seg["missing"] == []
    assert seg["energy_cover"] == [entry("COVERED", held_kwh="133", need_kwh="120")]
    assert seg["margin_kw"] == "20"                               # 3.2's margin: PV 0 + discharge 30 - load 10


def test_e3_the_headroom_edge():
    # Load 9.5 kW: need 144 x 9.5 x 5/60 = 114 kWh; 1.1 x 114 = 125.4 kWh.
    # SOC 96: held 0.66 x 200 x 0.95 = 125.4 kWh, exactly 1.1 x need: Candidate.
    edge = only_segment(run(one_point_night(soc="96", load="9.5")))
    assert edge["classification"] == d3.CANDIDATE
    assert edge["energy_cover"] == [entry("COVERED", held_kwh="125.4", need_kwh="114")]
    # SOC 95: held 0.65 x 200 x 0.95 = 123.5 kWh, below 125.4 (held >= need, and 130 kWh without efficiency).
    below = only_segment(run(one_point_night(soc="95", load="9.5")))
    assert below["classification"] == d3.INDETERMINATE
    assert below["energy_cover"] == [entry("SHORT", held_kwh="123.5", need_kwh="114")]


def test_e4_a_missing_reading_before_cover_is_a_gap_never_zero_load():
    seg = only_segment(run(one_point_night(soc="100", pv_skip=(at(23),))))
    assert seg["classification"] == d3.INDETERMINATE
    assert seg["energy_cover"] == [entry("GAP", held_kwh="133", input="pv_available_power", problem="MISSING",
                                         gap_at=stamp(23))]
    load_gap = Night().generator(at(18), at(18), soc="100")
    load_gap.series("feeder_demand", at(18), at(30), "10", skip=(at(20, 30),))
    load_gap.series("pv_available_power", at(18), at(30), lambda t: "12" if t >= at(30) else "0")
    seg = only_segment(run(load_gap))
    assert seg["energy_cover"] == [entry("GAP", held_kwh="133", input="feeder_demand", problem="MISSING",
                                         gap_at=stamp(20, 30))]


def test_e5_fifteen_minute_means_hold_over_their_own_interval():
    # Load 10 and PV 0 as 15-minute means (17:45, 18:00] .. (05:30, 05:45]; the last quarter hour as 5-minute means
    # (PV 0 ending 05:50 and 05:55, PV 12 ending 06:00), so the cover is at 06:00 as in E1: need 120 kWh exactly.
    night = Night().generator(at(18), at(18), soc="80")
    for t in slots(at(18), at(29, 45), 15):
        night.mean("feeder_demand", t, "10", 15).mean("pv_available_power", t, "0", 15)
    for t in slots(at(29, 50), at(30)):
        night.mean("feeder_demand", t, "10").mean("pv_available_power", t, "12" if t == at(30) else "0")
    seg = only_segment(run(night))
    assert seg["energy_cover"] == [entry("SHORT", held_kwh="95", need_kwh="120")]


def test_e5b_the_fallback_starts_strictly_after_a_mean_s_interval_start():
    # Load 10 kW as 5-minute means ending 18:00, 18:05, 18:10; none ending 18:15; one 15-minute mean (18:15, 18:30]
    # of 20 kW, then 20 kW ending 18:35 and 18:40. PV 0 to 18:30, 30 kW from 18:35. At 18:15 no reading ends and
    # 18:15 is not inside (18:15, 18:30]: a gap. (Read the other way it is 20 kW, cover at 18:35, need 55/6 kWh.)
    night = Night().generator(at(18), at(18), soc="100")
    for t in (at(18), at(18, 5), at(18, 10)):
        night.mean("feeder_demand", t, "10")
    night.mean("feeder_demand", at(18, 30), "20", 15)
    night.mean("feeder_demand", at(18, 35), "20").mean("feeder_demand", at(18, 40), "20")
    night.series("pv_available_power", at(18), at(18, 40), lambda t: "30" if t >= at(18, 35) else "0")
    seg = only_segment(run(night))
    assert seg["classification"] == d3.INDETERMINATE
    assert seg["energy_cover"] == [entry("GAP", held_kwh="133", input="feeder_demand", problem="MISSING",
                                         gap_at=stamp(18, 15))]


def test_e6_a_cover_after_the_read_range_is_not_reached_and_inside_it_is_counted():
    # Read range ends 06:00 next day; PV covers only at 07:00.
    late = one_point_night(soc="100", pv_cover_at=at(31))
    seg = only_segment(run(late))
    assert seg["classification"] == d3.INDETERMINATE
    assert seg["energy_cover"] == [entry("NOT_REACHED", held_kwh="133", range_end=stamp(30))]
    # Window 04:00 .. 04:00 next day: the read range ends at 10:00, past the window's end; the cover at 06:00 counts.
    seg = only_segment(run(one_point_night(soc="100"), window=Window(at(4), at(28))))
    assert seg["classification"] == d3.CANDIDATE
    assert seg["energy_cover"] == [entry("COVERED", held_kwh="133", need_kwh="120")]


def test_e7_no_capacity_is_not_configured_and_the_pv_alone_branch_needs_none():
    seg = only_segment(run(one_point_night(soc="100"), ctrl=controls(capacity=None)))
    assert seg["classification"] == d3.INDETERMINATE
    assert seg["missing"] == []
    assert seg["energy_cover"] == [entry("NOT_CONFIGURED", controls=["battery_energy_capacity"])]
    both = only_segment(run(one_point_night(soc="100"), ctrl=controls(capacity=None, efficiency=None)))
    assert both["energy_cover"] == [entry("NOT_CONFIGURED", controls=["battery_energy_capacity",
                                                                      "pcs_conversion_efficiency"])]
    # PV 20 kW alone covers 10 kW load with headroom: Candidate, no capacity needed, no entry.
    pv_alone = Night().generator(at(18), at(18), soc="100")
    pv_alone.series("feeder_demand", at(18), at(18), "10").series("pv_available_power", at(18), at(18), "20")
    seg = only_segment(run(pv_alone, ctrl=controls(capacity=None, efficiency=None)))
    assert seg["classification"] == d3.CANDIDATE
    assert "PV available alone covers load with 10 % headroom; PCS availability evidenced" in seg["reasons"]
    assert "energy_cover" not in seg


def test_e8b_the_walk_reads_each_slot_once_per_assessment(monkeypatch):
    """37 RUNNING reports 18:00 .. 21:00 (36 segments, each end a battery-support point), one walk memo."""
    inside = {"depth": 0}
    calls: Counter = Counter()
    lookup, walk = d3._Index.lookup_asset, d3._Index.energy_to_cover

    def counted_lookup(self, role, asset, when):
        if inside["depth"]:
            calls[(role, asset, when)] += 1
        return lookup(self, role, asset, when)

    def counted_walk(self, t):
        inside["depth"] += 1
        try:
            return walk(self, t)
        finally:
            inside["depth"] -= 1

    monkeypatch.setattr(d3._Index, "lookup_asset", counted_lookup)
    monkeypatch.setattr(d3._Index, "energy_to_cover", counted_walk)
    night = Night().generator(at(18), at(21), soc="80")
    night.series("feeder_demand", at(18), at(30), "10")
    night.series("pv_available_power", at(18), at(30), lambda t: "12" if t >= at(30) else "0")
    [interval] = run(night).intervals
    segments = interval.result["segments"]
    assert len(segments) == 36
    assert calls and max(calls.values()) == 1, calls.most_common(3)
    # 145 slots read (18:00 .. 06:00), load and PV each.
    assert len(calls) == 2 * 145
    first, last = segments[0]["energy_cover"][0], segments[-1]["energy_cover"][-1]
    assert first == entry("SHORT", held_kwh="95", need_kwh="120")
    # 21:00 .. 05:55: 108 slots of 10 kW x 5/60 h = 90 kWh.
    assert last == entry("SHORT", at=stamp(21), held_kwh="95", need_kwh="90")
    assert all(s["classification"] == d3.INDETERMINATE for s in segments)


def test_the_branch_is_dispatch_3_3():
    assert d3.MODEL_VERSION == "dispatch-3.3"
    assert d3.COVER_WALK_STEP == timedelta(minutes=5)


@pytest.mark.parametrize("key", [CONTROL_BATTERY_CAPACITY, CONTROL_PCS_EFFICIENCY])
def test_a_change_of_either_new_control_cuts_a_segment(key):
    change = at(18, 2, )
    since = T0 - timedelta(days=5)
    ctrl = list(controls())
    value = ctrl.pop(next(i for i, c in enumerate(ctrl) if c.key == key)).value
    ctrl += [ControlValue(key, value, "x", since, change, FOUNDATION, "IMPORT"),
             ControlValue(key, value, "x", change, None, UUID(int=44), "IMPORT")]
    night = Night().generator(at(18), at(18, 5), soc="100")
    night.series("feeder_demand", at(18), at(30), "10")
    night.series("pv_available_power", at(18), at(30), lambda t: "12" if t >= at(30) else "0")
    [interval] = run(night, ctrl=tuple(ctrl)).intervals
    assert [s["start"] for s in interval.result["segments"]] == [stamp(18), stamp(18, 2)]


def test_e8_a_segment_that_never_reaches_the_branch_carries_no_entry():
    """3.2's own fixtures: PV alone, near reserve, capability shortfall, 10-point SOC headroom, a contradiction."""
    import test_s3_dispatch_v3_analytic as s3

    feeds = [s3.run_interval(s3.Feed(), 5, 6, pv=s3.PV_ALONE), s3.run_interval(s3.Feed(), 5, 6, pv="5", soc="35"),
             s3.run_interval(s3.Feed(), 5, 6, pv="5", dis="5", soc="90"),
             s3.run_interval(s3.Feed(), 5, 6, soc="38"), s3.run_interval(s3.Feed(), 5, 6, pv="20", dis="10")]
    seen = set()
    for feed in feeds:
        _, result = s3.run(feed)
        for interval in result.intervals:
            for seg in interval.result["segments"]:
                seen.add(seg["classification"])
                assert "energy_cover" not in seg, seg
    assert seen == {d3.CANDIDATE, d3.NECESSARY, d3.INDETERMINATE}
