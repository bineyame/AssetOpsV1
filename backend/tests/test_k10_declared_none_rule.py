"""K10 v2 (build sheet DIESEL-1 §9t, ruling DIESEL-1-R3t): the declared-absent day rule, pure (L0).

`productive_kwh` with no row on a day whose site setup declares no productive-use load (the port proves it) is left
out of that day's applicable measures: never graded, never COMPLETE, never a gap. Everything else keeps today's rule.
Kisiwa-, Kobo- and Cold-shaped rows; a fake port stands in for `PostgresChainRead.declared_none_days`."""
from __future__ import annotations

import json
from collections import namedtuple
from dataclasses import fields
from datetime import date, timedelta
from uuid import UUID

from assetops_backend.chain import read as cr
from assetops_backend.chain import reader as rd
from assetops_backend.chain.grading import COMPLETE, NO_DATA, PARTIAL, PENDING

Row = namedtuple("Row", "site_id local_day measure subject_ref grade value")
SITE = UUID("00000000-0000-0000-0000-00000000c1a1")
TENANT = UUID("00000000-0000-0000-0000-0000000000a1")
D1, D2, D3 = date(2026, 10, 26), date(2026, 10, 27), date(2026, 10, 28)
MG = tuple(m.key for m in cr.measures_for("MINIGRID"))   # productive_kwh, daylight_headroom_kw, ...
KWH = "productive_kwh"


def kisiwa_day(d, grade=COMPLETE, *, skip=()):
    """The three measures Kisiwa has; never a productive_kwh row."""
    rows = [Row(SITE, d, "daylight_headroom_kw", "SITE", grade, 1), Row(SITE, d, "critical_served", "SITE", grade, 1),
            Row(SITE, d, "avoidable_gen_min", "GEN-01", grade, 0)]
    return [r for r in rows if r.measure not in skip]


def kobo_day(d, grade=COMPLETE):
    return kisiwa_day(d, grade) + [Row(SITE, d, KWH, "MILL-01", grade, 12)]


ND = {D1: frozenset({KWH}), D2: frozenset({KWH}), D3: frozenset({KWH})}


# ---- the pure rule ------------------------------------------------------------------------------------------------

def test_applicable_measures_is_identity_without_declaration():
    per = cr._per_day(kisiwa_day(D1))[D1]
    assert rd.applicable_measures(per, MG) == MG
    assert rd.applicable_measures(per, MG, ()) == MG


def test_1_kisiwa_day_declared_absent_settles_with_readiness_over_three_measures():
    rows = kisiwa_day(D3)
    assert rd.applicable_measures(cr._per_day(rows)[D3], MG, ND[D3]) == tuple(m for m in MG if m != KWH)
    assert cr.day_settled(rows, D3, MG, none_declared=ND) is True
    assert cr.readiness_of(rows, [D3], MG, none_declared=ND) == cr.FULL
    assert cr.day_gaps(rows, [D3], MG, none_declared=ND) == ()
    # readiness is over the three: one PARTIAL applicable measure makes it LIMITED, never FULL
    part = kisiwa_day(D3)[:2] + [Row(SITE, D3, "avoidable_gen_min", "GEN-01", PARTIAL, 0)]
    assert cr.readiness_of(part, [D3], MG, none_declared=ND) == cr.LIMITED


def test_2_same_day_without_declaration_is_unsettled_and_a_gap():
    rows = kisiwa_day(D3)
    assert cr.day_settled(rows, D3, MG) is False
    assert cr.day_gaps(rows, [D3], MG) == (D3,)
    assert cr.readiness_of(rows, [D3], MG) == cr.LIMITED   # the missing productive_kwh is NO_DATA
    # a declaration for another day does not leak
    assert cr.day_settled(rows, D3, MG, none_declared={D1: frozenset({KWH})}) is False


def test_3_day_with_no_rows_stays_unsettled_even_when_declared_absent():
    rows = kisiwa_day(D1)
    assert cr.day_settled(rows, D2, MG, none_declared=ND) is False
    assert cr.day_gaps(rows, [D1, D2], MG, none_declared=ND) == (D2,)
    assert rd.applicable_measures({}, MG, ND[D2]) == MG
    gc = rd.counts(rows, D1, D2, MG, ND)
    assert (gc.complete, gc.no_data, gc.enough_data_days) == (1, 1, 1)


def test_4_a_productive_kwh_row_always_wins():
    rows = kisiwa_day(D3) + [Row(SITE, D3, KWH, "MILL-01", PENDING, None)]
    assert rd.applicable_measures(cr._per_day(rows)[D3], MG, ND[D3]) == MG
    assert cr.day_settled(rows, D3, MG, none_declared=ND) is False
    assert cr.day_gaps(rows, [D3], MG, none_declared=ND) == (D3,)
    assert cr.readiness_of(rows, [D3], MG, none_declared=ND) == cr.UNKNOWN


def test_5_missing_site_measure_on_declared_absent_day_is_still_a_gap():
    rows = kisiwa_day(D3, skip=("critical_served",))
    assert cr.day_settled(rows, D3, MG, none_declared=ND) is False
    assert cr.day_gaps(rows, [D3], MG, none_declared=ND) == (D3,)
    assert rd.counts(rows, D3, D3, MG, ND).no_data == 1


def test_only_productive_kwh_can_be_declared_absent():
    rows = kisiwa_day(D3, skip=("critical_served",)) + [Row(SITE, D3, KWH, "MILL-01", COMPLETE, 1)]
    other = {D3: frozenset({"critical_served"})}
    assert rd.applicable_measures(cr._per_day(rows)[D3], MG, other[D3]) == MG
    assert cr.day_settled(rows, D3, MG, none_declared=other) is False
    assert rd.DECLARED_SUBJECT_MEASURES == frozenset({KWH})


def test_excluded_measure_is_never_complete_nor_lifts_enough_days():
    rows = kisiwa_day(D3, PARTIAL)
    gc = rd.counts(rows, D3, D3, MG, ND)
    assert (gc.complete, gc.partial, gc.enough_data_days) == (0, 1, 0)
    assert cr.readiness_of(rows, [D3], MG, none_declared=ND) == cr.LIMITED
    # the per-measure count of productive_kwh alone never reads COMPLETE on a declared-absent day
    assert rd.counts(rows, D3, D3, [KWH], ND).complete == 0


# ---- ChainRequest.day with fake ports ------------------------------------------------------------------------------

class Port:
    def __init__(self, rows, declared=frozenset()):
        self.rows, self.declared, self.calls = list(rows), frozenset(declared), []

    def snapshots(self, tenant_id, site_id, lo, hi, measures, known_at):
        return tuple(r for r in self.rows if lo <= r.local_day <= hi and r.measure in measures)


class DeclaringPort(Port):
    def declared_none_days(self, tenant_id, site_id, measure, days, known_at):
        self.calls.append((measure, tuple(days)))
        return frozenset(d for d in days if d in self.declared)


def _day(port, site_type="MINIGRID", days=(D1, D2, D3)):
    return cr.ChainReader(port).request(TENANT, None).day(SITE, site_type, list(days))


def test_chain_day_carries_declared_absent_days_and_settles():
    port = DeclaringPort(kisiwa_day(D1, PENDING) + kisiwa_day(D3), declared={D1, D2, D3})
    f = _day(port)
    assert port.calls == [(KWH, (D1, D3))]          # D2 holds no row at all: never asked
    assert dict(f.none_declared) == {D1: frozenset({KWH}), D3: frozenset({KWH})}
    assert f.settled is True and f.readiness == cr.UNKNOWN and f.gaps == (D1, D2)
    assert rd.grade_counts_of(f, MG) == rd.counts(list(f.rows), D1, D3, MG, f.none_declared)


def test_chain_day_setup_not_declaring_none_keeps_todays_rule():
    port = DeclaringPort(kisiwa_day(D3), declared=set())   # the port found a load, or the setup missing/ambiguous
    f = _day(port, days=(D3,))
    assert dict(f.none_declared) == {} and f.settled is False and f.gaps == (D3,)


def test_6_kobo_shaped_rows_give_equal_day_facts_and_counts():
    rows = kobo_day(D1) + kobo_day(D2, PARTIAL) + kobo_day(D3)
    plain, declaring = Port(rows), DeclaringPort(rows, declared={D1, D2, D3})
    a, b = _day(plain), _day(declaring)
    assert all(getattr(a, x.name) == getattr(b, x.name) for x in fields(cr.DayFacts))
    assert a == b and dict(b.none_declared) == {}
    before = rd._counts(list(a.rows), D1, D3, MG)
    assert rd.grade_counts_of(a, MG) == rd.grade_counts_of(b, MG) == before
    assert rd.counts(list(a.rows), D1, D3, MG, {}) == rd.counts(list(a.rows), D1, D3, MG) == before
    # the keyword-only defaults are byte-identical to the old calls
    assert cr.day_settled(rows, D3, MG) == cr.day_settled(rows, D3, MG, none_declared={})
    assert cr.readiness_of(rows, [D1, D2, D3], MG) == cr.readiness_of(rows, [D1, D2, D3], MG, none_declared=None)
    assert cr.day_gaps(rows, [D1, D2, D3], MG) == cr.day_gaps(rows, [D1, D2, D3], MG, none_declared={})


def test_7_grade_counts_of_equals_counts_with_the_same_declaration():
    port = DeclaringPort(kisiwa_day(D1) + kisiwa_day(D2, PARTIAL) + kisiwa_day(D3, skip=("critical_served",)),
                         declared={D1, D2, D3})
    f = _day(port)
    nd = f.none_declared
    assert rd.grade_counts_of(f, MG) == rd.counts(list(f.rows), D1, D3, MG, nd)
    gc = rd.grade_counts_of(f, MG)
    assert (gc.complete, gc.partial, gc.no_data, gc.enough_data_days) == (1, 1, 1, 1)


def test_8_lazy_trigger_no_port_call_on_kobo_rows_or_cold_site():
    kobo = DeclaringPort(kobo_day(D1) + kobo_day(D2) + kobo_day(D3), declared={D1, D2, D3})
    _day(kobo)
    assert kobo.calls == []
    cold_rows = [Row(SITE, d, "chamber_temp_c", "CH-01", COMPLETE, 4) for d in (D1, D2, D3)]
    cold = DeclaringPort(cold_rows, declared={D1, D2, D3})
    f = _day(cold, "COLDCHAIN")
    assert cold.calls == [] and dict(f.none_declared) == {}
    empty = DeclaringPort([], declared={D1})
    assert dict(_day(empty).none_declared) == {} and empty.calls == []


def test_port_without_method_declares_nothing():
    rows = kisiwa_day(D3)
    f = _day(Port(rows), days=(D3,))
    assert dict(f.none_declared) == {} and f.settled is False


def test_port_error_propagates():
    class Broken(Port):
        def declared_none_days(self, *a):
            raise RuntimeError("setup read failed")
    try:
        _day(Broken(kisiwa_day(D3)), days=(D3,))
    except RuntimeError as e:
        assert "setup read failed" in str(e)
    else:
        raise AssertionError("a failed setup read must never become a claim")


# ---- safeguard 1, pure: the adapter's coverage rule and the shared filter ------------------------------------------

def test_declared_none_of_needs_exactly_one_revision_at_both_bounds():
    from datetime import datetime, timezone
    from assetops_backend.chain.adapters.postgres_chain_read import declared_none_of
    from assetops_backend.mini_depth.read import productive_loads
    house = {"component_id": "HH", "component_type": "LOAD",
             "properties": [{"property_key": "supply-use", "unit": "state", "value": "ESSENTIAL"}]}
    mill = {"component_id": "MILL", "component_type": "LOAD",
            "properties": [{"property_key": "supply-use", "unit": "state", "value": "PRODUCTIVE"}]}
    none, load = {"components": [house]}, {"components": [house, mill]}
    assert productive_loads(none) == [] and productive_loads(load) == [mill]
    t0 = datetime(2026, 9, 1, tzinfo=timezone.utc)
    mid = datetime(2026, 10, 27, 9, tzinfo=timezone.utc)   # midday local D2 at UTC+3
    tz, days = "Africa/Dar_es_Salaam", (D1, D2, D3)
    assert declared_none_of(tz, [(t0, None, none)], days) == {D1, D2, D3}
    assert declared_none_of(tz, [(t0, None, json.dumps(none))], days) == {D1, D2, D3}   # text content
    assert declared_none_of(tz, [(t0, None, load)], days) == frozenset()
    assert declared_none_of(tz, [], days) == frozenset()
    assert declared_none_of(tz, [(None, None, None)], days) == frozenset()              # LEFT JOIN, no revision
    assert declared_none_of(None, [(t0, None, none)], days) == frozenset()              # no timezone
    assert declared_none_of(tz, [(t0, None, none), (t0, None, none)], days) == frozenset()   # ambiguous
    assert declared_none_of(tz, [(t0, mid, none), (mid, None, load)], days) == {D1}      # load at D2's end
    assert declared_none_of(tz, [(t0, mid, load), (mid, None, none)], days) == {D3}      # load at D2's start
    assert declared_none_of(tz, [(t0, mid, none), (mid, None, none)], days) == {D1, D2, D3}
    # the local end bound: a revision ending at local midnight D3 leaves D3 uncovered
    end_d2 = datetime(2026, 10, 27, 21, tzinfo=timezone.utc)
    assert declared_none_of(tz, [(t0, end_d2, none)], days) == {D1, D2}


def test_counts_rule_with_declaration_over_a_window():
    rows = [r for i in range(5) for r in kisiwa_day(D1 + timedelta(days=i))]
    nd = {D1 + timedelta(days=i): frozenset({KWH}) for i in range(5)}
    gc = rd.counts(rows, D1, D1 + timedelta(days=4), MG, nd)
    assert (gc.requested, gc.complete, gc.enough_data_days, gc.no_data) == (5, 5, 5, 0)
    assert rd.counts(rows, D1, D1 + timedelta(days=4), MG).no_data == 5
