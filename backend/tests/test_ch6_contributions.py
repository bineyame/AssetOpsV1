"""CH-6a1 L0 (build sheet CH-6 R2, R4, R12, §A2.2, §A2.3; SCOPE-1; CH6a1-R): the node records and the strategy
registry. Pure: no database, no app."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from assetops_backend.chain.graph import KNOWN_GAPS, NOT_CHAIN_SOURCED
from assetops_backend.chain.measures import MEASURES as CHAIN_MEASURES
from assetops_backend.chain.ports import SnapshotRow
from assetops_backend.chain.read import MoneyHead
from assetops_backend.chain.strategies import REGISTRY
from assetops_backend.chain.strategies.base import (
    CURRENCY_MIXED, MODELLED, NO_RECORDS, NOT_PRESENT, NOT_PRICED, NOT_SUPPORTED, ContributionContext,
    UnknownStrategy)
from assetops_backend.outcomes import outcome_map
from assetops_backend.outcomes.catalogue import OUTCOME_BY_KEY
from assetops_backend.outcomes.objectives import CHAMBER_RANGE_MEASURE, MEASURES as OBJECTIVE_MEASURES
from assetops_backend.outcomes.outcome_map import (
    CONTRIBUTIONS, ENTRIES, OutcomeContribution, kpi_record, records_for)
from assetops_backend.outcomes.status import Signal

#: Today's `ENTRIES`, verbatim (SCOPE-1: the literal stays; the derived form is BL-03).
ENTRIES_TODAY = {
    "FINDING:GENERATOR_SUPPORT_CANDIDATE": (("MG-2",), ("MG-5", "MG-4")),
    "FINDING:COLD_START_FAILURE": (("CC-6", "CC-1"), ("CC-5", "CC-3")),
    "FINDING:COLD_EXCURSION": (("CC-1",), ()),
    "FINDING:EV_INTERRUPTION": (("EV-1", "EV-3"), ("EV-4",)),
    "SIGNAL:PRODUCTIVE_USE_HEADROOM": (("MG-1",), ("MG-2", "MG-5")),
    "SIGNAL:EVIDENCE_GAP": (("MG-7",), ("MG-2",)),
    "SIGNAL:EVIDENCE_READINESS": (("@EVIDENCE",), ()),
    "WARNING:REPEATED_MAINTENANCE_NO_RESULT": (("@COST",), ("@LINKED",)),
    "WARNING:PLAN_OVERDUE": (("@ASSET_LIFE",), ()),
    "WARNING:PLAN_DUE_SOON": (("@ASSET_LIFE",), ()),
    "WARNING:BATTERY_NEAR_RESERVE": (("MG-4",), ()),
    "WARNING:CHARGER_FAULT_OVERDUE_INSPECTION": (("EV-4",), ()),
    "WARNING:CONNECTOR_OUT_OF_SERVICE": (("EV-1",), ()),
    "WARNING:PEAK_NEAR_IMPORT_LIMIT": (("EV-5",), ("EV-1",)),
    "WARNING:CHARGERS_MOSTLY_IDLE": (("EV-3",), ("EV-1",)),
}

#: §A2.2, row by row: (source, outcome, node, strategy, driver, money).
A22 = [
    ("MEASURE:productive_kwh", "MG-1", "kpi", "graded_verdict@1", "productive_use_kwh", None),
    ("MEASURE:productive_kwh", "MG-1", "earnings", "priced_energy@1", "productive_use_sales",
     {"measure": "productive_kwh", "price": "declared.productive_price", "label": "estimated_income"}),
    ("SIGNAL:PRODUCTIVE_USE_HEADROOM", "MG-1", "potential", "priced_energy@1", "daytime_solar_headroom",
     {"measure": "headroom_kw", "price": "declared.productive_price", "label": "potential",
      "basis": "per_hour_of_use"}),
    ("MEASURE:avoidable_gen_min", "MG-2", "kpi", "graded_verdict@1", "avoidable_generator_minutes", None),
    ("FINDING:GENERATOR_SUPPORT_CANDIDATE", "MG-2", "earnings", "avoided_cost@1", "possible_extra_fuel_cost",
     {"measure": "consequence", "price": "model.fuel-cost-1", "label": "possible_extra_fuel_cost"}),
    ("MEASURE:chamber_temp_c", "CC-1", "kpi", "graded_verdict@1", "excursions", None),
    ("MEASURE:backup_start_chain", "CC-6", "kpi", "graded_verdict@1", "backup_start_failures", None),
    ("MEASURE:charging_kwh", "EV-1", "kpi", "graded_verdict@1", "interrupted_sessions", None),
    ("MEASURE:charging_kwh", "EV-3", "earnings", "priced_energy@1", "charging_income",
     {"measure": "charging_kwh", "price": "declared.ev_tariff", "label": "estimated_charging_income"}),
    ("WARNING:CHARGERS_MOSTLY_IDLE", "EV-3", "potential", "direction_only@1", "idle_charger_capacity", None),
]

STRATEGY_KEYS = {"finding_presence@1", "direction_only@1", "graded_verdict@1", "priced_energy@1",
                 "avoided_cost@1", "recorded_amount@1"}


# ---- records --------------------------------------------------------------------------------------------------

def test_entries_literal_unchanged():
    assert ENTRIES == ENTRIES_TODAY
    assert list(ENTRIES) == list(ENTRIES_TODAY)


def test_record_fields_are_s1_in_order_and_frozen():
    assert [f.name for f in fields(OutcomeContribution)] == [
        "source", "outcome", "role", "rank", "driver", "direction", "node", "strategy", "money"]
    with pytest.raises(FrozenInstanceError):
        CONTRIBUTIONS[0].rank = 1  # type: ignore[misc]


def test_records_are_exactly_a22():
    got = [(r.source, r.outcome, r.node, r.strategy, r.driver, None if r.money is None else dict(r.money))
           for r in CONTRIBUTIONS]
    assert got == A22


def test_record_role_rank_direction():
    for r in CONTRIBUTIONS:
        assert (r.role, r.rank) == ("MOVES", 0)
        want = "CHECK" if r.node == "kpi" else ("ADVERSE" if (r.outcome, r.node) == ("MG-2", "earnings")
                                                else "FAVOURABLE")
        assert r.direction == want, r
    assert not any(r.outcome == "MG-5" for r in CONTRIBUTIONS)  # R9


def test_no_duplicate_record():
    keys = [(r.source, r.outcome, r.node, r.role) for r in CONTRIBUTIONS]
    assert len(keys) == len(set(keys))


def test_every_outcome_and_source_resolves():
    for r in CONTRIBUTIONS:
        assert r.outcome in OUTCOME_BY_KEY, r
        kind, _, rest = r.source.partition(":")
        if kind == "MEASURE":
            assert rest in CHAIN_MEASURES, r  # a `MEASURE:` source names a declared chain measure
        else:
            assert r.source in ENTRIES, r


def test_every_kpi_driver_is_an_objective_measure():
    kpis = [r for r in CONTRIBUTIONS if r.node == "kpi"]
    assert kpis
    for r in kpis:
        # CH6a1-R Q2: an objective `MEASURES` key, or CC-1's chamber-range measure.
        assert r.driver in OBJECTIVE_MEASURES or r.driver == CHAMBER_RANGE_MEASURE, r
        if r.driver in OBJECTIVE_MEASURES:
            assert OBJECTIVE_MEASURES[r.driver].outcome == r.outcome, r


def test_money_measure_rule():
    for r in CONTRIBUTIONS:
        if r.money is None:
            continue
        assert set(r.money) <= {"measure", "price", "label", "basis"} and {"measure", "price", "label"} <= set(r.money)
        if r.node == "earnings":
            assert r.money["measure"] in CHAIN_MEASURES or r.money["measure"] == "consequence", r
        else:  # CH6a1-R Q3: the potential reads `headroom_kw` from the opportunity thread items (R13)
            assert r.money["measure"] == "headroom_kw", r


def test_records_for_and_kpi_record():
    assert [r.node for r in records_for("MEASURE:productive_kwh")] == ["kpi", "earnings"]
    assert [r.outcome for r in records_for("MEASURE:charging_kwh", "earnings")] == ["EV-3"]
    assert records_for("SIGNAL:EVIDENCE_GAP") == ()
    assert kpi_record("MG-2").driver == "avoidable_generator_minutes"
    assert kpi_record("CC-1").source == "MEASURE:chamber_temp_c"
    assert kpi_record("MG-5") is None and kpi_record("EV-3") is None


def test_records_are_data_only():
    for r in CONTRIBUTIONS:
        for v in (r.source, r.outcome, r.role, r.driver, r.direction, r.node, r.strategy):
            assert isinstance(v, str)
        assert r.money is None or all(isinstance(v, str) for v in r.money.values())


def test_chargers_mostly_idle_kept_as_known_gap_owned_by_bl06():
    # SCOPE-1 / CH6a1-R Q4: the key and the R12 record stay; no producer (BL-06).
    assert "WARNING:CHARGERS_MOSTLY_IDLE" in ENTRIES
    assert records_for("WARNING:CHARGERS_MOSTLY_IDLE", "potential")
    assert NOT_CHAIN_SOURCED["WARNING:CHARGERS_MOSTLY_IDLE"] == (None, "BL-06")
    assert KNOWN_GAPS == {"WARNING:CHARGERS_MOSTLY_IDLE"}


# ---- strategies -----------------------------------------------------------------------------------------------

def test_registry_has_the_six_keys_and_every_record_resolves():
    assert set(REGISTRY.keys()) == STRATEGY_KEYS
    for r in CONTRIBUTIONS:
        s = REGISTRY.resolve(r.strategy)
        assert f"{s.key}@{s.version}" == r.strategy
    with pytest.raises(UnknownStrategy):
        REGISTRY.resolve("priced_energy@2")


T, S = UUID(int=1), UUID(int=2)


def _row(day: int, grade: str, amount: str | None, currency: str = "USD", measure: str = "productive_kwh",
         subject: str = "asset:a") -> SnapshotRow:
    money = None if amount is None else {"amount": amount, "currency": currency}
    return SnapshotRow(T, S, date(2026, 10, day), "ASSET", subject, measure, "MEASURED", 1, True, 100, 100, "100",
                       grade, {"kwh": "1"}, money, "p", "c", 1, "fp")


def _rec(source: str, node: str) -> OutcomeContribution:
    return records_for(source, node)[0]


EARN = ("MEASURE:productive_kwh", "earnings")


def _effect(rec: OutcomeContribution, **kw):
    return REGISTRY.resolve(rec.strategy).effect(ContributionContext(rec, **kw))


def test_priced_energy_sums_complete_and_partial_unscaled():
    rows = (_row(1, "COMPLETE", "2.50"), _row(2, "PARTIAL", "0.75"), _row(3, "LOW", "9.00"),
            _row(4, "NO_DATA", None))
    e = _effect(_rec(*EARN), day_rows=rows)
    assert e.money == {"amount": Decimal("3.25"), "currency": "USD"}  # PARTIAL as stored; LOW not totalled
    assert e.days["COMPLETE"] == 1 and e.days["PARTIAL"] == 1 and e.days["LOW"] == 1 and e.days["NO_DATA"] == 1
    assert e.basis == "MEASURED" and len(e.explanation_ids) == 2


def test_priced_energy_zero_kwh_is_zero_money():
    e = _effect(_rec(*EARN), day_rows=(_row(1, "COMPLETE", "0.00"),))
    assert e.money == {"amount": Decimal("0.00"), "currency": "USD"}


def test_priced_energy_refuses_mixed_currency():
    e = _effect(_rec(*EARN), day_rows=(_row(1, "COMPLETE", "1.00"), _row(2, "COMPLETE", "1.00", "KES")))
    assert e.money is None and e.reason == CURRENCY_MIXED


def test_priced_energy_without_counted_or_priced_days():
    assert _effect(_rec(*EARN), day_rows=(_row(1, "LOW", "1.00"),)).reason == NO_RECORDS
    assert _effect(_rec(*EARN), day_rows=(_row(1, "COMPLETE", None),)).reason == NOT_PRICED


def test_priced_energy_potential_only_when_supported():
    rec = _rec("SIGNAL:PRODUCTIVE_USE_HEADROOM", "potential")
    hk = (Decimal("4"), Decimal("6"))
    e = _effect(rec, headroom_kw=hk, evidence_status="SUPPORTED", price=Decimal("0.25"), currency="USD")
    assert e.money == {"low": Decimal("1.00"), "high": Decimal("1.50"), "currency": "USD"}
    assert _effect(rec, headroom_kw=hk, evidence_status="LIMITED", price=Decimal("0.25"),
                   currency="USD").reason == NOT_SUPPORTED
    assert _effect(rec, evidence_status="SUPPORTED").reason == NOT_SUPPORTED
    assert _effect(rec, headroom_kw=hk, evidence_status="SUPPORTED").reason == NOT_PRICED


def test_avoided_cost_reads_the_stored_range():
    rec = _rec("FINDING:GENERATOR_SUPPORT_CANDIDATE", "earnings")
    head = MoneyHead(True, Decimal("3"), Decimal("5"), "USD", None)
    e = _effect(rec, money_head=head)
    assert e.money == {"low": Decimal("3"), "high": Decimal("5"), "currency": "USD"} and e.basis == MODELLED
    assert _effect(rec).reason == NOT_PRICED
    assert _effect(rec, money_head=MoneyHead(False, None, None, None, None)).reason == NOT_PRICED


def test_direction_only_never_a_number():
    rec = _rec("WARNING:CHARGERS_MOSTLY_IDLE", "potential")
    e = _effect(rec)
    assert e.money is None and e.magnitude == (None, None) and e.reason == NOT_PRESENT
    e = _effect(rec, title="Chargers used under a fifth of capacity")
    assert e.title and e.reason is None and e.money is None


def test_graded_verdict_counts_weakest_grade_per_day():
    rec = kpi_record("MG-1")
    rows = (_row(1, "COMPLETE", None), _row(1, "PARTIAL", None, subject="asset:b"), _row(2, "COMPLETE", None))
    e = _effect(rec, day_rows=rows)
    assert e.days["COMPLETE"] == 1 and e.days["PARTIAL"] == 1 and e.money is None
    assert e.inputs == {"measure": "productive_use_kwh"}


def test_finding_presence_and_recorded_amount():
    rec = OutcomeContribution("FINDING:COLD_EXCURSION", "CC-1", "MOVES", 0, "excursions", "ADVERSE", "status",
                              "finding_presence@1", None)
    e = _effect(rec, signals=(Signal("FINDING", "CC-1", True, True, False),))
    assert e.inputs["open"] and e.inputs["primary"] and not e.inputs["applied"] and e.money is None
    rec2 = OutcomeContribution("MEASURE:charging_kwh", "EV-3", "MOVES", 0, "x", "FAVOURABLE", "earnings",
                               "recorded_amount@1", None)
    assert _effect(rec2).money is None and _effect(rec2).reason == NO_RECORDS


def test_outcome_map_module_still_pure():
    # No importer change (SCOPE-1): the module's public surface keeps its earlier names.
    for name in ("ENTRIES", "DOMAIN_ALIAS", "outcome_roles", "categories_for", "lens_flags", "thread_signal_key",
                 "finding_signal_key", "COLD_KIND_MECHANISM", "POLICY_VERSION"):
        assert hasattr(outcome_map, name)
