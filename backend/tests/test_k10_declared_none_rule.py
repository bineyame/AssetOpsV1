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
    assert declared_none_of(tz, [(t0, None, none), (t0, None, none)], days) == {D1, D2, D3}  # R3t3: overlap allowed
    assert declared_none_of(tz, [(t0, None, none), (t0, None, load)], days) == frozenset()   # any overlapping mill
    assert declared_none_of(tz, [(t0, mid, none), (mid, None, load)], days) == frozenset()   # R3t4: ever a mill
    assert declared_none_of(tz, [(t0, mid, load), (mid, None, none)], days) == frozenset()   # R3t4: ever a mill
    assert declared_none_of(tz, [(t0, mid, none), (mid, None, none)], days) == {D1, D2, D3}
    # the local end bound: a revision ending at local midnight D3 leaves D3 uncovered
    end_d2 = datetime(2026, 10, 27, 21, tzinfo=timezone.utc)
    assert declared_none_of(tz, [(t0, end_d2, none)], days) == {D1, D2}


def _h(n):
    from datetime import datetime, timezone
    return datetime(2026, 10, 27, tzinfo=timezone.utc) + timedelta(hours=n)


LO, HI = _h(0), _h(24)


def test_r3t3_declared_none_day_eleven_cases():
    f = rd.declared_none_day
    assert f([(_h(-5), _h(30), False)], LO, HI) is True                                  # 1 one covers the day
    assert f([(_h(-5), None, False)], LO, HI) is True                                    # 2 open-ended
    assert f([(_h(-5), _h(12), False), (_h(12), _h(30), False)], LO, HI) is True         # 3 contiguous at 12:00
    assert f([(_h(-9), LO, False), (LO, _h(30), False)], LO, HI) is True                 # 4 one ends exactly at lo
    assert f([(_h(-5), HI, False)], LO, HI) is True                                      # 5 valid_to == hi (half-open)
    assert f([(_h(-5), _h(8), False), (_h(8), _h(14), True), (_h(14), None, False)], LO, HI) is False   # 6 mid-day mill
    assert f([(_h(-5), _h(8), False), (_h(14), None, False)], LO, HI) is False           # 7 mid-day gap
    assert f([(_h(0.5), None, False)], LO, HI) is False                                  # 8 gap at the start
    assert f([(_h(-5), _h(23), False)], LO, HI) is False                                 # 9 gap at the end
    assert f([], LO, HI) is False                                                        # 10 no revisions
    assert f([(_h(-5), None, False), (_h(8), _h(14), True)], LO, HI) is False            # 11 overlap, one with a mill
    # only revisions overlapping the day count: one ending at lo, or starting at hi, is ignored
    assert f([(_h(-9), LO, True), (LO, HI, False), (HI, None, True)], LO, HI) is True
    assert f([(_h(-9), LO, False)], LO, HI) is False


# ---- R3t4: a Site that ever declared productive equipment declares nothing absent ----------------------------------

def _rev(content_kind):
    house = {"component_id": "HH", "component_type": "LOAD",
             "properties": [{"property_key": "supply-use", "unit": "state", "value": "ESSENTIAL"}]}
    mill = {"component_id": "MILL", "component_type": "LOAD",
            "properties": [{"property_key": "supply-use", "unit": "state", "value": "PRODUCTIVE"}]}
    return {"components": [house, mill] if content_kind == "mill" else [house]}


def _window(end, n=31):
    return [end - timedelta(days=i) for i in range(n - 1, -1, -1)]


def test_r3t4_site_never_declared_pure_gate():
    from datetime import datetime, timezone
    t = datetime(2026, 9, 1, tzinfo=timezone.utc)
    assert rd.site_never_declared([]) is True
    assert rd.site_never_declared([(t, None, False), (t, t, False)]) is True
    assert rd.site_never_declared([(t, None, False), (t, None, True)]) is False


def test_r3t4_kobo_history_declares_nothing_absent_on_any_window():
    from datetime import datetime, timezone
    from assetops_backend.chain.adapters.postgres_chain_read import declared_none_of
    tz = "Africa/Dar_es_Salaam"
    revs = [(datetime(2026, 9, 29, 11, 57, tzinfo=timezone.utc), datetime(2026, 10, 8, 11, 25, tzinfo=timezone.utc), _rev("none")),
            (datetime(2026, 10, 8, 11, 25, tzinfo=timezone.utc), None, _rev("mill"))]
    for end in (date(2026, 11, 6), date(2026, 11, 1), date(2026, 10, 28), date(2026, 10, 5)):   # S, S-5d, d1, 10-05
        assert declared_none_of(tz, revs, _window(end)) == frozenset(), end


def test_r3t4_kisiwa_shaped_history_keeps_the_r3t3_results():
    from datetime import datetime, timezone
    from assetops_backend.chain.adapters.postgres_chain_read import declared_none_of
    tz = "Africa/Dar_es_Salaam"
    t0 = datetime(2026, 10, 26, 10, tzinfo=timezone.utc)   # 13:00 local on D1: D1 is not covered
    revs = [(t0, datetime(2026, 11, 2, tzinfo=timezone.utc), _rev("none")), (datetime(2026, 11, 2, tzinfo=timezone.utc), None, _rev("none"))]
    assert declared_none_of(tz, revs, (D1, D2, D3)) == {D2, D3}
    assert declared_none_of(tz, [(datetime(2026, 9, 1, tzinfo=timezone.utc), None, _rev("none"))], (D1, D2, D3)) == {D1, D2, D3}


def test_r3t4_a_mill_valid_only_after_the_window_still_blocks():
    from datetime import datetime, timezone
    from assetops_backend.chain.adapters.postgres_chain_read import declared_none_of
    tz = "Africa/Dar_es_Salaam"
    t0 = datetime(2026, 9, 1, tzinfo=timezone.utc)
    revs = [(t0, datetime(2026, 12, 1, tzinfo=timezone.utc), _rev("none")), (datetime(2026, 12, 1, tzinfo=timezone.utc), None, _rev("mill"))]
    assert declared_none_of(tz, revs, (D1, D2, D3)) == frozenset()


def test_r3t4_the_eleven_r3t3_cases_hold_on_a_never_declared_site():
    # the 11 cases carry has_productive=True revisions; a Site with any such revision now declares nothing, so the
    # cases that hold with only no-load revisions are 1-5 and 7-10; 6 and 11 are blocked by the gate (False either way)
    f = rd.declared_none_day
    for revs, want in (([(_h(-5), _h(30), False)], True), ([(_h(-5), None, False)], True),
                       ([(_h(-5), _h(12), False), (_h(12), _h(30), False)], True), ([(_h(-5), HI, False)], True),
                       ([(_h(-5), _h(8), False), (_h(14), None, False)], False), ([(_h(0.5), None, False)], False),
                       ([(_h(-5), _h(23), False)], False), ([], False)):
        assert rd.site_never_declared(revs) is True and f(revs, LO, HI) is want
    mill_cases = ([(_h(-5), _h(8), False), (_h(8), _h(14), True), (_h(14), None, False)],
                  [(_h(-5), None, False), (_h(8), _h(14), True)])
    for revs in mill_cases:
        assert rd.site_never_declared(revs) is False


# ---- R3v: the chain body's per-day grades are over the same applicable measures as the counts ---------------------------

from assetops_backend.chain import measures as _ms
from assetops_backend.chain import site_chain as sc

K0 = date(2026, 10, 9)
GRADE_FIELDS = ("complete", "partial", "low", "no_data", "not_expected", "pending")


def _tally(days):
    return {f: sum(1 for e in days if e["grade"] == f.upper()) for f in GRADE_FIELDS}


def _old_days_of(facts, measures):
    """days_of exactly as before R3v."""
    out = []
    for d in facts.days:
        per = {m: list((facts.grades.get(d) or {}).get(m, {}).values()) for m in measures}
        per = {m: g for m, g in per.items() if g}
        out.append({"day": d.isoformat(), "grade": cr.day_grade(per, measures),
                    "measures": {m: cr.day_grade(per, [m]) for m in measures}})
    return out


def _kisiwa_month():
    """31 days: 3 PARTIAL (the 10-28/10-29/11-07 shapes), 8 with avoidable_gen_min missing (the 10-30 shape), 20 empty."""
    rows, shape = [], {}
    for i in range(31):
        d = K0 + timedelta(days=i)
        if i in (19, 20, 29):
            rows += kisiwa_day(d, PARTIAL); shape[d] = "partial"
        elif 21 <= i <= 28:
            rows += kisiwa_day(d, COMPLETE, skip=("avoidable_gen_min",)); shape[d] = "gap"
        else:
            shape[d] = "empty"
    declared = {d for d, s in shape.items() if s != "empty"}
    return _day(DeclaringPort(rows, declared=declared), days=[K0 + timedelta(days=i) for i in range(31)]), shape


def test_r3v_days_of_tally_equals_grade_counts_of_on_kisiwa_month():
    f, _ = _kisiwa_month()
    gc = rd.grade_counts_of(f, MG)
    tally = _tally(sc.days_of(f, MG))
    assert tally == {x: getattr(gc, x) for x in GRADE_FIELDS}
    assert tally["partial"] == 3 and tally["no_data"] == 28
    # the old call form disagrees (the COH-18 defect)
    assert _tally(_old_days_of(f, MG))["partial"] == 0


def _plain_facts(site_type, with_gaps):
    specs = [m.key for m in _ms.measures_for(site_type)]
    rows = []
    for i in range(6):
        d = K0 + timedelta(days=i)
        for j, m in enumerate(specs):
            if with_gaps and i == 4 and j == 0:
                continue
            rows.append(Row(SITE, d, m, "SITE", PARTIAL if (i == 2 and j == 1) else COMPLETE, 1))
    return _day(Port(rows), site_type=site_type, days=[K0 + timedelta(days=i) for i in range(7)]), tuple(specs)


def test_r3v_other_site_types_identity_and_bytes_unchanged():
    types = sorted({m.site_type for m in _ms.MEASURES.values()})
    assert len(types) >= 2
    for st in types:
        for gaps in (False, True):
            f, ms = _plain_facts(st, gaps)
            assert dict(f.none_declared) == {}
            new = sc.days_of(f, ms)
            gc = rd.grade_counts_of(f, ms)
            assert _tally(new) == {x: getattr(gc, x) for x in GRADE_FIELDS}
            assert new == _old_days_of(f, ms)
            assert json.dumps(new, sort_keys=True) == json.dumps(_old_days_of(f, ms), sort_keys=True)
            assert all("none_declared" not in e for e in new)


def test_r3v_day_entry_shape():
    f, shape = _kisiwa_month()
    by = {e["day"]: e for e in sc.days_of(f, MG)}
    p = by[(K0 + timedelta(days=19)).isoformat()]      # a 10-28 shape
    assert p["grade"] == PARTIAL and p["measures"][KWH] == NO_DATA and p["none_declared"] == [KWH]
    g = by[(K0 + timedelta(days=22)).isoformat()]      # a 10-30 shape: another measure is NO_DATA
    assert g["grade"] == NO_DATA and g["none_declared"] == [KWH]
    e = by[K0.isoformat()]                              # no rows at all
    assert e["grade"] == NO_DATA and "none_declared" not in e
    # a productive_kwh row always wins: no key
    f2 = _day(DeclaringPort(kobo_day(D1), declared={D1}), days=[D1])
    d2 = sc.days_of(f2, MG)[0]
    assert d2["grade"] == COMPLETE and "none_declared" not in d2


def test_counts_rule_with_declaration_over_a_window():
    rows = [r for i in range(5) for r in kisiwa_day(D1 + timedelta(days=i))]
    nd = {D1 + timedelta(days=i): frozenset({KWH}) for i in range(5)}
    gc = rd.counts(rows, D1, D1 + timedelta(days=4), MG, nd)
    assert (gc.requested, gc.complete, gc.enough_data_days, gc.no_data) == (5, 5, 5, 0)
    assert rd.counts(rows, D1, D1 + timedelta(days=4), MG).no_data == 5
