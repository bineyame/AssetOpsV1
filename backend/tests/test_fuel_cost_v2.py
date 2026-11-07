"""FUEL-1 A1 (`.agent/build-sheet-FUEL-1.md` §4.1): the pure `fuel-cost-2` model, its selection, and the declared
no-load vocabulary in the Site parser.

Expected values are computed here from the inputs (hours x rate, P x hours x SFC, x 1.10), never typed from a run.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from assetops_backend.financials import fuel_cost as fc
from assetops_backend.financials import fuel_cost_v2 as fc2
from assetops_backend.sites.models import COMPONENT_PROPERTY_DEFINITIONS
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.sites.site_parsing import parse_site_document

DAY = datetime(2026, 9, 14, tzinfo=timezone.utc)
GEN = "GEN-1"
SFC = ("0.3", "L/kWh")
RATE = ("3.3", "L/h")
PRICE = fc.PriceSelection("PRICED", None, "P", Decimal("1.25"), "USD")


def at(minutes: int) -> datetime:
    return DAY + timedelta(hours=6, minutes=minutes)


def foundation(rid: str, no_load=(RATE,), basis=("GENERIC_DEFAULT",), sfc=(SFC,)) -> fc2.FoundationRevision:
    return fc2.FoundationRevision(rid, DAY, None, tuple(sfc), tuple(no_load), tuple(basis))


def finding(readings: list[tuple[int, int, str, str]], foundations) -> fc.FindingInput:
    """One observed Candidate span covering the readings `(start_min, end_min, kW, foundation_id)` exactly."""
    lo, hi = min(r[0] for r in readings), max(r[1] for r in readings)
    seg = fc.Segment(at(lo), at(hi), True, fc.CANDIDATE)
    power = tuple(fc.PowerReading(f"r{i}", GEN, at(s), at(e), kw, "kW", "GOOD", f"sha-r{i}", fid, "B1")
                  for i, (s, e, kw, fid) in enumerate(readings, 1))
    assessment = fc.AssessmentInput("A1", "RUN1", "INTERVAL", True, GEN, (seg,), frozenset(r.evidence_id for r in power),
                                    frozenset(f.revision_id for f in foundations))
    return fc.FindingInput("T", "S", "FIND", "FREV", GEN, at(lo), at(hi), "SUPPORTED",
                           (fc.CandidateSpan(at(lo), at(hi), "A1"),), (assessment,), power, tuple(foundations),
                           (fc.BindingRevision("B1", DAY, None),))


# ---- the reviewed parameter version ----------------------------------------------------------------------------

def test_parameter_version_is_new_and_fuel_cost_1_is_untouched() -> None:
    assert fc2.MODEL_ID == "fuel-cost-2" and fc2.MULTIPLIER == Decimal("1.10")
    assert fc2.PARAMETER_VERSION["parameter_version"] == "fuel-cost-2/sfc-upper-multiplier-and-no-load/v1"
    assert fc2.FORMULA_VERSION == "fuel-cost-2+fuel-cost-2/sfc-upper-multiplier-and-no-load/v1"
    assert fc2.PARAMETER_VERSION["author"] == "Claude Architect (FUEL-1)"
    assert fc2.PARAMETER_SHA256 != fc.PARAMETER_SHA256
    assert fc.MODEL_ID == "fuel-cost-1" and fc.FORMULA_VERSION == "fuel-cost-1+fuel-cost-1/sfc-upper-multiplier/v1"
    assert fc2.REVIEWED_PARAMETER_SHA256 == {"fuel-cost-1": fc.PARAMETER_SHA256, "fuel-cost-2": fc2.PARAMETER_SHA256}


def test_limitations_v2() -> None:
    assert len(fc2.LIMITATIONS) == 5
    assert fc2.LIMITATIONS[:2] == fc.LIMITATIONS[:2] and fc2.LIMITATIONS[3] == fc.LIMITATIONS[3]
    assert fc2.LIMITATIONS[2].endswith("specific fuel consumption, and the declared no-load fuel rate for running at "
                                       "0 kW (fuel-cost-2 reviewed modelling allowance).")
    assert fc2.LIMITATIONS[4] == ("Running at 0 kW inside Candidate time is counted at the declared no-load fuel "
                                  "rate; a generic rate is not this generator's own figure.")


# ---- selection ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("v1_foundation", [True, False])
def test_no_rate_selects_fuel_cost_1_byte_equal(v1_foundation: bool) -> None:
    fr = (fc.FoundationRevision("F1", DAY, None, (SFC,)) if v1_foundation
          else foundation("F1", no_load=(), basis=()))
    f = finding([(0, 60, "20", "F1"), (60, 90, "0", "F1")], [fr])
    q = fc2.quantify(f)
    assert not fc2.is_v2(q) and q == fc.quantify(f)
    c1, c2 = fc.consequence(f, fc.quantify(f), PRICE), fc2.consequence(f, q, PRICE)
    assert type(c2) is fc.Consequence
    assert (c2.basis_sha256, c2.technical_input_sha256, c2.amount_high, c2.limitations) == (
        c1.basis_sha256, c1.technical_input_sha256, c1.amount_high, c1.limitations)
    cols = fc2.model_columns(c2)
    assert cols["model_id"] == "fuel-cost-1" and cols["parameter_sha256"] == fc.PARAMETER_SHA256
    assert (cols["no_load_fuel_rate_l_per_h"], cols["no_load_fuel_rate_basis"], cols["idle_seconds"]) == (
        None, None, None)


def test_fuel_cost_1_unavailable_stays_fuel_cost_1() -> None:
    f = finding([(0, 60, "-1", "F1")], [foundation("F1")])
    q = fc2.quantify(f)
    assert not fc2.is_v2(q) and q.reason == "POWER_NEGATIVE"


# ---- quantity -----------------------------------------------------------------------------------------------

def test_idle_only_200_minutes_at_3_3() -> None:
    f = finding([(0, 100, "0", "F1"), (100, 200, "0.0", "F1")], [foundation("F1")])
    q = fc2.quantify(f)
    assert fc2.is_v2(q) and q.state == "AVAILABLE" and q.low == Decimal(0)
    assert q.high_exact == Fraction(11, 10) * Fraction(200, 60) * Fraction(33, 10)
    assert q.high_exact == Fraction(121, 10) and q.high == Decimal("12.1")
    assert q.idle_seconds == 200 * 60 and q.no_load_l_per_h == Decimal("3.3") and q.no_load_basis == "GENERIC_DEFAULT"
    assert all(c.idle and c.no_load_l_per_h == Decimal("3.3") for c in q.intervals)
    assert fc.quantify(f).high_exact == 0  # fuel-cost-1 prices the same idle time at nothing


def test_loaded_only_with_rate_declared_equals_fuel_cost_1() -> None:
    f = finding([(0, 60, "20", "F1"), (60, 75, "12.5", "F1")], [foundation("F1")])
    q1, q2 = fc.quantify(f), fc2.quantify(f)
    assert fc2.is_v2(q2) and q2.idle_seconds == 0
    assert [c.litres for c in q2.intervals] == [c.litres for c in q1.intervals]
    assert q2.high_exact == q1.high_exact and q2.high == q1.high
    assert q2.high_exact == Fraction(11, 10) * (20 * 1 * Fraction(3, 10) + Fraction(25, 2) * Fraction(1, 4)
                                                * Fraction(3, 10))


def test_mixed_loaded_and_idle() -> None:
    f = finding([(0, 60, "20", "F1"), (60, 90, "0", "F1")], [foundation("F1")])
    q = fc2.quantify(f)
    loaded = 20 * Fraction(1) * Fraction(3, 10)
    idle = Fraction(30, 60) * Fraction(33, 10)
    assert q.high_exact == Fraction(11, 10) * (loaded + idle)
    assert [c.idle for c in q.intervals] == [False, True] and q.idle_seconds == 1800
    c = fc2.consequence(f, q, PRICE)
    assert isinstance(c, fc2.Consequence) and c.state == "PRICED" and c.limitations == fc2.LIMITATIONS
    assert c.amount_high == q.high * Decimal("1.25") and c.amount_low == Decimal(0)
    assert c.basis_sha256 != fc.consequence(f, fc.quantify(f), PRICE).basis_sha256
    cols = fc2.model_columns(c)
    assert cols == {"model_id": "fuel-cost-2", "formula_version": fc2.FORMULA_VERSION,
                    "parameter_version": "fuel-cost-2/sfc-upper-multiplier-and-no-load/v1",
                    "parameter_sha256": fc2.PARAMETER_SHA256, "sfc_upper_multiplier": Decimal("1.10"),
                    "no_load_fuel_rate_l_per_h": Decimal("3.3"), "no_load_fuel_rate_basis": "GENERIC_DEFAULT",
                    "idle_seconds": 1800}


def test_technical_digest_names_rate_basis_and_idle_flags() -> None:
    base = finding([(0, 60, "20", "F1"), (60, 90, "0", "F1")], [foundation("F1")])
    other_basis = finding([(0, 60, "20", "F1"), (60, 90, "0", "F1")], [foundation("F1", basis=("SITE_TEST",))])
    q_a, q_b = fc2.quantify(base), fc2.quantify(other_basis)
    assert q_a.high_exact == q_b.high_exact
    assert fc2.technical_input_sha256(base, q_a) != fc2.technical_input_sha256(other_basis, q_b)


# ---- the four new refusals -----------------------------------------------------------------------------------

@pytest.mark.parametrize(("readings", "foundations", "reason"), [
    # an idle reading whose revision declares no rate (another counted reading's revision selects fuel-cost-2)
    ([(0, 60, "20", "F2"), (60, 90, "0", "F1")], ["F1:none", "F2"], "NO_LOAD_RATE_MISSING"),
    # two distinct rates across the counted readings
    ([(0, 60, "0", "F1"), (60, 90, "0", "F2")], ["F1", "F2:3.5"], "NO_LOAD_RATE_CONFLICT"),
    # a rate <= 0, and a unit other than L/h
    ([(0, 60, "0", "F1")], ["F1:0"], "NO_LOAD_RATE_INVALID"),
    ([(0, 60, "0", "F1")], ["F1:L/kWh"], "NO_LOAD_RATE_INVALID"),
    # no basis property
    ([(0, 60, "0", "F1")], ["F1:nobasis"], "NO_LOAD_RATE_BASIS_MISSING"),
])
def test_new_refusals(readings, foundations, reason) -> None:
    built = []
    for spec in foundations:
        rid, _, mod = spec.partition(":")
        if mod == "none":
            built.append(foundation(rid, no_load=(), basis=()))
        elif mod == "3.5":
            built.append(foundation(rid, no_load=(("3.5", "L/h"),)))
        elif mod == "0":
            built.append(foundation(rid, no_load=(("0", "L/h"),)))
        elif mod == "L/kWh":
            built.append(foundation(rid, no_load=(("3.3", "L/kWh"),)))
        elif mod == "nobasis":
            built.append(foundation(rid, basis=()))
        else:
            built.append(foundation(rid))
    f = finding(readings, built)
    q = fc2.quantify(f)
    assert fc2.is_v2(q) and q.state == "QUANTITY_UNAVAILABLE" and q.reason == reason, q.detail
    assert q.high is None and q.low is None and q.high_exact is None and q.intervals == ()
    assert (q.no_load_l_per_h, q.no_load_basis, q.idle_seconds) == (None, None, None)
    c = fc2.consequence(f, q, PRICE)
    assert c.state == "QUANTITY_UNAVAILABLE" and c.price.state == "NOT_EVALUATED" and c.amount_high is None
    assert fc2.model_columns(c)["model_id"] == "fuel-cost-2"


def test_conflicting_basis_is_a_conflict() -> None:
    f = finding([(0, 60, "0", "F1"), (60, 90, "0", "F2")],
                [foundation("F1"), foundation("F2", basis=("MANUFACTURER_DATASHEET",))])
    assert fc2.quantify(f).reason == "NO_LOAD_RATE_CONFLICT"


def test_basis_outside_the_three_reads_basis_missing() -> None:
    """A1 review L2 (closed in A2): a stored basis value outside the three states is no basis."""
    f = finding([(0, 60, "0", "F1")], [foundation("F1", basis=("GUESSED",))])
    q = fc2.quantify(f)
    assert fc2.is_v2(q) and q.reason == "NO_LOAD_RATE_BASIS_MISSING"


def test_loaded_reading_on_a_non_declaring_revision_stays_available() -> None:
    """A1 review L2 (closed in A2): MISSING applies to idle readings only, so a Finding whose loaded reading spans a
    Foundation revision without the rate, next to a declaring one, stays AVAILABLE and prices the idle reading."""
    f = finding([(0, 60, "20", "F2"), (60, 90, "0", "F1")], [foundation("F1"), foundation("F2", no_load=(), basis=())])
    q = fc2.quantify(f)
    assert fc2.is_v2(q) and q.state == "AVAILABLE", (q.reason, q.detail)
    assert q.high_exact == Fraction(11, 10) * (20 * Fraction(3, 10) + Fraction(30, 60) * Fraction(33, 10))


# ---- the Site parser ------------------------------------------------------------------------------------------

KOBO = yaml.safe_load((Path(__file__).resolve().parent / "fixtures" / "s1" / "kobo-001.yaml").read_text(
    encoding="utf-8"))


def _with(component_id: str, key: str, value, unit: str | None = None) -> dict:
    doc = copy.deepcopy(KOBO)
    for component in doc["foundation"]["components"]:
        if component["component_id"] == component_id:
            component["properties"] = list(component.get("properties") or []) + [{
                "property_key": key, "value": value, "unit": unit or COMPONENT_PROPERTY_DEFINITIONS[key].unit,
                "source": "SITE", "source_version": 1}]
    return doc


def _props(doc: dict) -> dict:
    site = parse_site_document(doc, source="test document")
    return {(c.component_id, p.property_key): (p.value, p.unit) for c in site.foundation.components
            for p in (c.properties or ())}


class TestNoLoadVocabulary:
    def test_rate_in_l_per_h_is_accepted_on_the_generator(self) -> None:
        assert _props(_with("generator", "generator-no-load-fuel-rate", 3.3))[
            ("generator", "generator-no-load-fuel-rate")] == (3.3, "L/h")

    def test_rate_in_another_unit_is_refused(self) -> None:
        with pytest.raises(SiteConfigurationInvalid):
            _props(_with("generator", "generator-no-load-fuel-rate", 3.3, unit="L/kWh"))

    def test_sfc_in_l_per_h_is_still_refused(self) -> None:
        doc = copy.deepcopy(KOBO)
        for component in doc["foundation"]["components"]:
            for prop in component.get("properties") or ():
                if prop["property_key"] == "specific-fuel-consumption":
                    prop["unit"] = "L/h"
        with pytest.raises(SiteConfigurationInvalid):
            _props(doc)

    @pytest.mark.parametrize("value", ["GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST"])
    def test_each_basis_state_is_accepted(self, value) -> None:
        assert _props(_with("generator", "generator-no-load-fuel-rate-basis", value))[
            ("generator", "generator-no-load-fuel-rate-basis")] == (value, "state")

    @pytest.mark.parametrize("value", ["generic_default", "GUESS", "", 3.3])
    def test_basis_outside_the_state_set_is_refused(self, value) -> None:
        with pytest.raises(SiteConfigurationInvalid):
            _props(_with("generator", "generator-no-load-fuel-rate-basis", value))

    @pytest.mark.parametrize(("key", "value"), [("generator-no-load-fuel-rate", 3.3),
                                                ("generator-no-load-fuel-rate-basis", "GENERIC_DEFAULT")])
    def test_carrier_is_the_generator(self, key, value) -> None:
        with pytest.raises(SiteConfigurationInvalid, match=f"{key} belongs on a GENERATOR"):
            _props(_with("battery", key, value))
