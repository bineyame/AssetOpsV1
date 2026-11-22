"""6h2 (`specs/6h-named-option-levers/spec.md` §4, §10.1): a STATED_OPTIONS lever valued through the same evaluator.
Literals derived by hand in the spec (N1, T1, K2, S1)."""
from __future__ import annotations

from decimal import Decimal as D

import pytest

from assetops_backend.decisions.evaluate import evaluate_options
from assetops_backend.decisions.records import MemoryDecisionStore  # noqa: F401
from assetops_backend.decisions.run import option_inputs
from assetops_backend.structure.levers import LEVERS
from assetops_backend.structure.registry import REGISTRIES
from option_fixtures import (CC, EV, k2_base, n1_base, s1_base, named_decision, one_off_of, record_of, t1_base)


def run(lever_id, base, period, horizon, records=(), one_offs=None):
    lever = LEVERS[lever_id]
    decision, options = named_decision(lever_id, period, horizon)
    by_key = {o.option_key: o for o in options}
    recs = {(r.option_id, r.factor_id): r for r in records}
    offs = {by_key[k].id: one_off_of(by_key[k], a) for k, a in (one_offs or {}).items()}
    inputs = option_inputs(options, lever, None, {}, {}, offs, base=base, records=recs)
    outcome, rows = evaluate_options(REGISTRIES[lever.structure_key], base, decision, lever, inputs)
    return outcome, {o.option_key: r for o, r in zip(options, rows)}, by_key


def effects(row):
    return {e.factor_id: (e.change_per_month, e.currency) for e in row.effects}


def n1_records(by_key, **kw):
    o = by_key["storage-contract"]
    return [record_of(o, "contract_crate_days", 4500, "DAY", seq=1, **kw),
            record_of(o, "contract_rate", "0.18", "MONEY/DAY", "USD", seq=2, **kw),
            record_of(o, "handling", "100.00", "MONEY", "USD", seq=3, **kw)]


def n1(**kw):
    _, by_key = named_decision("storage_contract", "2026-10", 4)
    by_key = {o.option_key: o for o in by_key}
    return run("storage_contract", n1_base(), "2026-10", 4, n1_records(by_key, **kw), {"storage-contract": "270.00"})


def test_n1_mwea_contract():
    outcome, rows, _ = n1()
    r = rows["storage-contract"]
    assert outcome == "RECOMMENDED"
    assert (r.disposition, r.rank, r.source_class) == ("RECOMMENDED", 1, "RECORDED")
    assert (r.monthly_change, r.horizon_change, r.value, r.currency) == (D("485.00"), D("1940.00"), D("1670.00"), "USD")
    got = effects(r)
    assert list(got) == ["contract_crate_days", "contract_rate", "handling", "revenue", "kwh_model", "kwh", "energy",
                         "cost_to_serve", "contribution"]
    assert {k: v[0] for k, v in got.items()} == {
        "contract_crate_days": D(4500), "contract_rate": D("0.18"), "handling": D("100.00"), "revenue": D("810.00"),
        "kwh_model": D(1125), "kwh": D(1125), "energy": D("225.00"), "cost_to_serve": D("325.00"),
        "contribution": D("485.00")}
    assert {k: v[1] for k, v in got.items()} == {
        "contract_crate_days": None, "contract_rate": None, "handling": "USD", "revenue": "USD", "kwh_model": None,
        "kwh": None, "energy": "USD", "cost_to_serve": "USD", "contribution": "USD"}


def test_n1e_emulated_record_makes_the_row_emulated():
    _, rows, _ = n1(origin="source-emulated")
    assert rows["storage-contract"].source_class == "EMULATED"


def test_n1m_a_missing_record_names_itself():
    _, by_key = named_decision("storage_contract", "2026-10", 4)
    by_key = {o.option_key: o for o in by_key}
    recs = n1_records(by_key)[:2]
    outcome, rows, _ = run("storage_contract", n1_base(), "2026-10", 4, recs, {"storage-contract": "270.00"})
    r = rows["storage-contract"]
    assert r.value is None
    assert [(m.record_kind, m.source_family, m.factor_id) for m in r.missing] == [("OPTION_RECORD", "DECISION", "handling")]
    assert outcome == "RANKING_INCOMPLETE"


def test_n1k_a_record_in_another_currency_is_a_currency_mismatch():
    _, by_key = named_decision("storage_contract", "2026-10", 4)
    o = {x.option_key: x for x in by_key}["storage-contract"]
    recs = [record_of(o, "contract_crate_days", 4500, "DAY", seq=1),
            record_of(o, "contract_rate", "0.18", "MONEY/DAY", "KES", seq=2),
            record_of(o, "handling", "100.00", "MONEY", "USD", seq=3)]
    _, rows, _ = run("storage_contract", n1_base(), "2026-10", 4, recs, {"storage-contract": "270.00"})
    r = rows["storage-contract"]
    assert effects(r)["contribution"][0] is None
    assert [(m.record_kind, m.source_family, m.factor_id) for m in r.missing] == [("CURRENCY_MISMATCH", "STRUCTURE", None)]
    assert r.value is None


def t1(records=None, one_offs=None):
    _, opts = named_decision("backup_cover", "2026-10", 1)
    by_key = {o.option_key: o for o in opts}
    recs = [record_of(by_key["stopgap-and-claim"], "uncovered_nights", 0, "DAY", seq=1)] if records is None else records(by_key)
    return run("backup_cover", t1_base(), "2026-10", 1, recs, {"stopgap-and-claim": "100.00"} if one_offs is None else one_offs)


def test_t1_thika_stopgap_shows_value_and_purpose_but_no_recommendation():
    outcome, rows, _ = t1()
    r = rows["stopgap-and-claim"]
    assert outcome == "BOUNDS_NOT_CHECKED"
    assert (r.disposition, r.reason_code, r.rank) == ("CONDITIONAL", "BOUNDS_NOT_CHECKED", None)
    assert (r.monthly_change, r.value, r.currency, r.evidence_class, r.source_class) == (
        D(0), D("-100.00"), "USD", "DECLARED", "RECORDED")
    got = effects(r)
    assert {k: v[0] for k, v in got.items()} == {"uncovered_nights": D(-26), "nights_without_backup_cover": D(-26),
                                                  "contribution": D(0)}
    assert got["contribution"][1] == "USD"
    s = rows["self-repair"]
    assert (s.disposition, s.reason_code, s.value, s.evidence_class) == ("DEFERRED", "VALUE_NOT_AVAILABLE", None, "DECLARED")
    assert [(m.record_kind, m.source_family, m.factor_id) for m in s.missing] == [
        ("OPTION_RECORD", "DECISION", "uncovered_nights"), ("ONE_OFF", "DECISION", None)]


def test_t1o_an_unrecorded_own_leaf_makes_the_value_null_even_with_a_one_off():
    _, rows, _ = t1(one_offs={"stopgap-and-claim": "100.00", "self-repair": "50.00"})
    s = rows["self-repair"]
    assert s.value is None
    assert [(m.record_kind, m.source_family, m.factor_id) for m in s.missing] == [
        ("OPTION_RECORD", "DECISION", "uncovered_nights")]


def test_t1e_emulated_stopgap_is_emulated_and_declared():
    _, rows, _ = t1(records=lambda k: [record_of(k["stopgap-and-claim"], "uncovered_nights", 0, "DAY",
                                                 origin="source-emulated", seq=1)])
    r = rows["stopgap-and-claim"]
    assert (r.source_class, r.evidence_class) == ("EMULATED", "DECLARED")


def test_t1b_records_are_read_per_option_and_factor():
    _, rows, _ = t1(records=lambda k: [record_of(k["stopgap-and-claim"], "uncovered_nights", 0, "DAY", seq=1),
                                       record_of(k["self-repair"], "uncovered_nights", 10, "DAY", seq=2)])
    s = rows["self-repair"]
    assert {k: v[0] for k, v in effects(s).items()} == {"uncovered_nights": D(-16),
                                                         "nights_without_backup_cover": D(-16), "contribution": D(0)}
    assert [(m.record_kind, m.source_family, m.factor_id) for m in s.missing] == [("ONE_OFF", "DECISION", None)]
    assert s.value is None
    st = rows["stopgap-and-claim"]
    assert (effects(st)["uncovered_nights"][0], st.value) == (D(-26), D("-100.00"))


def test_k2_kasarani_stopgap():
    _, opts = named_decision("charger_restore", "2026-11", 1)
    by_key = {o.option_key: o for o in opts}
    rec = [record_of(by_key["stopgap-and-claim"], "covered_bus_nights", 6, "DAY", seq=1)]
    outcome, rows, _ = run("charger_restore", k2_base(), "2026-11", 1, rec, {"stopgap-and-claim": "90.00"})
    r = rows["stopgap-and-claim"]
    got = {k: v[0] for k, v in effects(r).items()}
    assert got == {"covered_bus_nights": D(6), "departures_missed": D(-6), "penalties": D("-720.00"),
                   "cost_to_serve": D("-720.00"), "contribution": D("720.00")}
    assert (r.value, r.disposition, r.reason_code, r.rank) == (D("630.00"), "CONDITIONAL", "BOUNDS_NOT_CHECKED", None)
    assert outcome == "BOUNDS_NOT_CHECKED"


def test_s1_embakasi_names_each_simulation_then_the_one_off():
    outcome, rows, _ = run("charging_schedule", s1_base(), "2026-11", 1)
    want = [("OPTION_STUDY", "SIMULATION", f) for f in
            ("peak_kwh", "kwh_2200_2400", "kwh_0000_0500", "max_kw", "extra_missed_departures")]
    want.append(("ONE_OFF", "DECISION", None))
    for key in ("deadline-aware", "cheapest-window"):
        assert [(m.record_kind, m.source_family, m.factor_id) for m in rows[key].missing] == want
    assert outcome == "RANKING_INCOMPLETE"



def test_a_held_record_over_a_missing_base_level_is_missing_never_zero():
    from option_fixtures import leaves_for
    base = leaves_for(CC, {})  # the month's uncovered nights were not received
    _, opts = named_decision("backup_cover", "2026-10", 1)
    by_key = {o.option_key: o for o in opts}
    rec = [record_of(by_key["stopgap-and-claim"], "uncovered_nights", 0, "DAY", seq=1)]
    _, rows, _ = run("backup_cover", base, "2026-10", 1, rec, {"stopgap-and-claim": "100.00"})
    r = rows["stopgap-and-claim"]
    miss = base["uncovered_nights"].missing
    assert r.value is None
    assert (miss.record_kind, miss.source_family, "uncovered_nights") in [
        (m.record_kind, m.source_family, m.factor_id) for m in r.missing]
    assert effects(r)["uncovered_nights"][0] is None
