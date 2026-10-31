"""OUT-E E2: the pure trial cost comparison (`financials/trial_fuel_comparison.py`), no database.

`.agent/build-sheet-OUT-E.md` E2: the worked example (generator 40/28 kWh, feeder 120/126 kWh, SFC 0.3 L/kWh,
1.25 USD/L, intervention cost 0), one isolating test per reason, the precedence order, change 0, and the reason
list equal to 0037's table CHECK.
"""

from __future__ import annotations

import importlib.util
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import UUID

import pytest

from assetops_backend.financials import trial_fuel_comparison as tfc
from assetops_backend.financials.fuel_cost import PriceSelection
from assetops_backend.mini_depth.rules import SfcValue

UTC = timezone.utc
B0 = datetime(2026, 10, 6, 8, 0, tzinfo=UTC)
L0 = datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
H = timedelta(hours=1)
REV = UUID(int=7)
SFC = (SfcValue(REV, Decimal("0.3"), datetime(2026, 1, 1, tzinfo=UTC), None),)
V1 = PriceSelection("PRICED", None, "price-v1", Decimal("1.25"), "USD")
COST = tfc.InterventionCost(Fraction(0), None, "Generator stop setting changed; no direct cost declared")


def window(start, gen, feeder, ids=("e1", "e2"), complete=True) -> tfc.WindowFacts:
    return tfc.WindowFacts(tuple(ids), complete, None if gen is None else Fraction(gen),
                           None if feeder is None else Fraction(feeder), start, start + H)


BASE = window(B0, 40, 120, ("b1", "b2"))
LATER = window(L0, 28, 126, ("l1", "l2"))
OUT = tfc.OutcomeFacts("outcome-1", "plan-1", "rev-1", "VERIFIED", {"baseline": ("b2", "b1"), "later": ("l1", "l2")},
                       "PASS", "PASS")


def run(baseline=BASE, later=LATER, outcome=OUT, sfc=SFC, prices=(V1, V1), cost=COST):
    return tfc.compare(baseline, later, outcome, sfc, prices, cost)


def test_worked_example():
    out = run()
    assert out["state"] == "MODELLED_IMPROVEMENT" and out["reason"] is None
    assert out["change_per_demand_kwh"] == {"nominal": "1/24", "upper": "11/240"}
    assert out["windows"]["baseline"]["cost_per_demand_kwh"]["nominal"] == "0.125"
    assert out["windows"]["later"]["cost_per_demand_kwh"]["nominal"] == "1/12"
    assert out["windows"]["baseline"] == {"generator_kwh": "40", "feeder_demand_kwh": "120",
                                          "fuel_l": {"nominal": "12", "upper": "13.2"},
                                          "cost": {"nominal": "15", "upper": "16.5"},
                                          "cost_per_demand_kwh": {"nominal": "0.125", "upper": "0.1375"}}
    assert out["windows"]["later"]["fuel_l"] == {"nominal": "8.4", "upper": "9.24"}
    assert out["price"] == {"revision_id": "price-v1", "value": "1.25", "currency": "USD"}
    assert out["sfc"] == {"value_l_per_kwh": "0.3"}
    assert out["intervention_cost"] == {"amount": "0", "currency": "USD",
                                        "source": "Generator stop setting changed; no direct cost declared"}
    assert out["evidence_ids"] == {"baseline": ["b1", "b2"], "later": ["l1", "l2"]}
    assert (out["formula"], out["claim_level"], out["beneficiary"]) == (
        "trial-fuel-comparison/1", "POST_INTERVENTION_MODELLED", "MINI_OPERATOR")
    assert set(out) == {"formula", "claim_level", "beneficiary", "state", "reason", "outcome_id", "plan_id",
                        "origin_finding_revision_id", "windows", "change_per_demand_kwh", "intervention_cost",
                        "price", "sfc", "evidence_ids", "basis_sha256", "label"}
    assert len(out["basis_sha256"]) == 64 and run()["basis_sha256"] == out["basis_sha256"]


def test_intervention_cost_is_never_subtracted_and_never_changes_the_state():
    costly = run(cost=tfc.InterventionCost(Fraction(500), "USD", "declared"))
    assert costly["change_per_demand_kwh"] == run()["change_per_demand_kwh"]
    assert costly["state"] == "MODELLED_IMPROVEMENT" and costly["basis_sha256"] != run()["basis_sha256"]
    with pytest.raises(ValueError):
        run(cost=tfc.InterventionCost(Fraction(5), "EUR", "declared"))


def test_change_zero_and_negative_are_no_improvement():
    same = run(later=window(L0, 40, 120, ("l1", "l2")))
    assert same["state"] == "MODELLED_NO_IMPROVEMENT" and same["change_per_demand_kwh"]["nominal"] == "0"
    worse = run(later=window(L0, 50, 120, ("l1", "l2")))
    assert worse["state"] == "MODELLED_NO_IMPROVEMENT" and worse["change_per_demand_kwh"]["nominal"].startswith("-")


ISOLATED = {
    "OUTCOME_INCONCLUSIVE": dict(outcome=replace(OUT, outcome="INCONCLUSIVE")),
    "WINDOW_INCOMPLETE": dict(later=replace(LATER, complete=False)),
    "NOT_COMPARABLE": dict(outcome=replace(OUT, comparability_state="FAIL")),
    "SOURCE_NOT_COHERENT": dict(outcome=replace(OUT, source_state="UNKNOWN")),
    "EVIDENCE_REPLAY_MISMATCH": dict(later=replace(LATER, evidence_ids=("l1", "l2", "l3"))),
    "GENERATOR_KWH_UNKNOWN": dict(baseline=replace(BASE, generator_kwh=None)),
    "ZERO_DEMAND": dict(later=replace(LATER, feeder_demand_kwh=Fraction(0))),
    "SFC_MISSING": dict(sfc=()),
    "SFC_DIFFERS": dict(sfc=(SfcValue(REV, Decimal("0.3"), B0, B0 + H), SfcValue(REV, Decimal("0.31"), L0, None))),
    "PRICE_MISSING": dict(prices=(V1, PriceSelection("UNPRICED", "NO_PRICE"))),
    "PRICE_BASIS_DIFFERS": dict(prices=(replace(V1, revision_id="price-v4", value=Decimal("1.28")), V1)),
}


@pytest.mark.parametrize("reason", tfc.REASSESSMENT_REASONS)
def test_each_reason_in_isolation(reason):
    out = run(**ISOLATED[reason])
    assert (out["state"], out["reason"], out["change_per_demand_kwh"]) == ("UNAVAILABLE", reason, None)


def test_reason_precedence_first_that_applies_wins():
    reasons = list(tfc.REASSESSMENT_REASONS)
    for i, reason in enumerate(reasons):
        kwargs: dict = {}
        for later_reason in reasons[i:]:  # this reason plus every reason after it, merged
            for key, value in ISOLATED[later_reason].items():
                if key == "outcome" and "outcome" in kwargs:
                    a, b = kwargs["outcome"], value
                    value = replace(a, **{f: getattr(b, f) for f in ("outcome", "comparability_state", "source_state")
                                          if getattr(b, f) != getattr(OUT, f)})
                if key in ("baseline", "later") and key in kwargs:
                    a, b, ref = kwargs[key], value, BASE if key == "baseline" else LATER
                    value = replace(a, **{f: getattr(b, f) for f in ("complete", "generator_kwh", "feeder_demand_kwh",
                                                                    "evidence_ids") if getattr(b, f) != getattr(ref, f)})
                kwargs.setdefault(key, value) if key in ("sfc", "prices") else kwargs.__setitem__(key, value)
        assert run(**kwargs)["reason"] == reason, (reason, kwargs)


def test_uncomputable_fields_are_null_and_hashed():
    out = run(baseline=replace(BASE, generator_kwh=None))
    assert out["windows"]["baseline"] == {"generator_kwh": None, "feeder_demand_kwh": "120", "fuel_l": None,
                                          "cost": None, "cost_per_demand_kwh": None}
    assert out["windows"]["later"]["cost_per_demand_kwh"]["nominal"] == "1/12"
    unpriced = run(prices=(PriceSelection("UNPRICED", "NO_PRICE"),) * 2)
    assert unpriced["price"] is None and unpriced["intervention_cost"]["currency"] is None
    assert len({out["basis_sha256"], unpriced["basis_sha256"], run()["basis_sha256"]}) == 3


def test_reasons_equal_the_0037_table_check():
    path = Path(__file__).resolve().parents[1] / "migrations" / "versions" / "0037_cc_trial_cost_comparison.py"
    spec = importlib.util.spec_from_file_location("m0037", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.REASONS == tfc.REASSESSMENT_REASONS
    assert module.STATES == tfc.REASSESSMENT_STATES
    assert module.FORMULA == tfc.FORMULA


def test_sfc_for_refuses_several_zero_and_ending_inside_the_window():
    """Review L3: no single positive fuel rate in force over the whole window -> SFC_MISSING."""
    jan = datetime(2026, 1, 1, tzinfo=UTC)
    two = (SfcValue(REV, Decimal("0.3"), jan, None), SfcValue(UUID(int=8), Decimal("0.3"), jan, None))
    zero = (SfcValue(REV, Decimal("0"), jan, None),)
    ends = (SfcValue(REV, Decimal("0.3"), jan, B0 + timedelta(minutes=30)), SfcValue(REV, Decimal("0.3"), L0, None))
    for sfc in (two, zero, ends):
        assert run(sfc=sfc)["reason"] == "SFC_MISSING", sfc
    assert tfc.sfc_for(BASE, ends) is None and tfc.sfc_for(LATER, ends) is not None
    assert tfc.sfc_for(BASE, SFC).value_l_per_kwh == Decimal("0.3")


def test_malformed_fuel_rate_is_not_a_value():
    """Review L2: `sfc_history` skips a malformed or non-finite authored value, so the check reads SFC_MISSING."""
    from assetops_backend.actions.adapters.postgres_action_store import finite_decimal

    assert finite_decimal("0.3") == Decimal("0.3") and finite_decimal(0.3) == Decimal("0.3")
    for bad in ("abc", "NaN", "Infinity", None, True, ""):
        assert finite_decimal(bad) is None, bad
