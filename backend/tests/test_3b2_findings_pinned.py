"""3B2: Findings pinned to their factors (spec §6, T1-T5; rulings D-3B2.1 to D-3B2.15).

T1's pin table, T3's expected differences and T4's wire snapshot are literals written here (W2, D-3B2.6): none is
imported from `pins.py` or built from `outcome_map.ENTRIES`. No database: run with `DATABASE_URL` and
`ASSETOPS_TEST_DATABASE_URL` unset.
"""

from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path
from types import MappingProxyType

import pytest
import yaml

from assetops_backend.config import ConfigurationError
from assetops_backend.outcomes import outcome_map
from assetops_backend.structure import check as check_module
from assetops_backend.structure import pins
from assetops_backend.structure import registry as registry_module
from assetops_backend.structure.check import CODES, PIN_CODES, StructureError, check_all, check_pins
from assetops_backend.structure.registry import REGISTRIES, Home, Registry

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
MANIFEST = yaml.load(MANIFEST_PATH.read_text(encoding="utf-8"), Loader=_LOADER)

# ---- the test's own literals (W2) ------------------------------------------------------------------------------

#: Design §4 (spec §2): mechanism -> (structure key, factor).
DESIGN_PINS = {
    "GENERATOR_SUPPORT_CANDIDATE": ("MINI_GRID", "candidate_l"),
    "UNEXPLAINED_FUEL": ("MINI_GRID", "unexplained_l"),
    # 3B6 (D-3B6.5): the three cold and EV mechanisms, pinned to leaves under Protect.
    "COLD_START_FAILURE": ("COLD_CHAIN", "uncovered_nights"),
    "COLD_EXCURSION": ("COLD_CHAIN", "excursion_crates"),
    "EV_INTERRUPTION": ("EV_DEPOT_CAPTIVE", "chargers_in_service"),
}
DESIGN_PENDING: dict[str, str] = {}  # 3B6 moved the three into PINS
#: D-3B2.7: the catalogue's domain values, lower case.
OWN_DOMAIN_OF_STRUCTURE = {"MINI_GRID": "mini_grid", "COLD_CHAIN": "cold_chain", "EV_DEPOT_CAPTIVE": "ev_charging"}
#: The manifest's heading words (T1).
OWN_HEADING = {"grow": "GROW_REVENUE", "optimize": "OPTIMIZE_COST", "protect": "PROTECT_ASSET",
               "assure": "ASSURE_PERFORMANCE"}
#: D-3B2.9: the manifest's site names (3B6: the cold rooms and depots too).
OWN_SITE_STRUCTURE = {"Kobo": "MINI_GRID", "Kisiwa": "MINI_GRID", "Mto": "MINI_GRID",
                      "Room A · Mwea": "COLD_CHAIN", "Room B · Thika": "COLD_CHAIN", "Room C · Kirinyaga": "COLD_CHAIN",
                      "Embakasi": "EV_DEPOT_CAPTIVE", "Kasarani": "EV_DEPOT_CAPTIVE", "Ruiru": "EV_DEPOT_CAPTIVE"}
#: 3B6 (D-3B6.5): a pinned mechanism no screen Finding shows yet, with its reason.
NO_MANIFEST_ROW = {"COLD_EXCURSION": "no pack Site has an excursion Finding in October (home_categories.findings)"}

#: Spec §4 / D-3B2.4: the ruled differences between the literal and the registry. A new or vanished one fails T3.
EXPECTED_DIVERGENCES = {
    ("UNEXPLAINED_FUEL", "PROTECT_ASSET", "OPTIMIZE_COST", "RISK", "COST"),
}

DOMAINS = ("mini_grid", "cold_chain", "ev_charging")

# T4 snapshot (D-3B2.6): `categories_for` and `lens_flags` written once from `main` at 39e1682de, never rebuilt.
_V = "outcome-map/1"
_NOT = ({"policy_version": _V, "state": "NOT_MAPPED", "items": []}, [])
_OPT = {"category": "OPTIMIZE_COST", "label": "Optimize cost and efficiency"}
_PRO = {"category": "PROTECT_ASSET", "label": "Protect asset and capital"}
_GRO = {"category": "GROW_REVENUE", "label": "Grow revenue"}
WIRE_SNAPSHOT = {
    ("FINDING:GENERATOR_SUPPORT_CANDIDATE", "mini_grid"): (
        {"policy_version": _V, "state": "MAPPED", "items": [
            {**_OPT, "role": "MOVES", "outcomes": [{"key": "MG-2", "label": "Supply cost per kWh"}]},
            {**_PRO, "role": "CHECKED", "outcomes": [{"key": "MG-5", "label": "Reliable service"},
                                                     {"key": "MG-4", "label": "Battery and generator life"}]}]},
        ["COST"]),
    ("FINDING:GENERATOR_SUPPORT_CANDIDATE", "cold_chain"): _NOT,
    ("FINDING:GENERATOR_SUPPORT_CANDIDATE", "ev_charging"): _NOT,
    ("FINDING:COLD_START_FAILURE", "mini_grid"): _NOT,
    ("FINDING:COLD_START_FAILURE", "cold_chain"): (
        {"policy_version": _V, "state": "MAPPED", "items": [
            {**_PRO, "role": "MOVES", "outcomes": [{"key": "CC-6", "label": "Cooling continuity"},
                                                   {"key": "CC-1", "label": "Stock kept saleable"}]},
            {**_PRO, "role": "CHECKED", "outcomes": [{"key": "CC-5", "label": "Compressor life"}]},
            {**_OPT, "role": "CHECKED", "outcomes": [{"key": "CC-3", "label": "Cost per cooling unit"}]}]},
        ["RISK"]),
    ("FINDING:COLD_START_FAILURE", "ev_charging"): _NOT,
    ("FINDING:COLD_EXCURSION", "mini_grid"): _NOT,
    ("FINDING:COLD_EXCURSION", "cold_chain"): (
        {"policy_version": _V, "state": "MAPPED", "items": [
            {**_PRO, "role": "MOVES", "outcomes": [{"key": "CC-1", "label": "Stock kept saleable"}]}]},
        ["RISK"]),
    ("FINDING:COLD_EXCURSION", "ev_charging"): _NOT,
    ("FINDING:EV_INTERRUPTION", "mini_grid"): _NOT,
    ("FINDING:EV_INTERRUPTION", "cold_chain"): _NOT,
    ("FINDING:EV_INTERRUPTION", "ev_charging"): (
        {"policy_version": _V, "state": "MAPPED", "items": [
            {**_PRO, "role": "MOVES", "outcomes": [{"key": "EV-1", "label": "Buses ready for service"}]},
            {**_GRO, "role": "MOVES", "outcomes": [{"key": "EV-3", "label": "Charger use"}]},
            {**_PRO, "role": "CHECKED", "outcomes": [{"key": "EV-4", "label": "Charger life"}]}]},
        ["RISK"]),
    ("FINDING:UNEXPLAINED_FUEL", "mini_grid"): (
        {"policy_version": _V, "state": "MAPPED", "items": [
            {**_PRO, "role": "MOVES", "outcomes": [{"key": "MG-8", "label": "Fuel accounted for"}]}]},
        ["RISK"]),
    ("FINDING:UNEXPLAINED_FUEL", "cold_chain"): _NOT,
    ("FINDING:UNEXPLAINED_FUEL", "ev_charging"): _NOT,
    ("FINDING:UNMAPPED", "mini_grid"): _NOT,
    ("FINDING:UNMAPPED", "cold_chain"): _NOT,
    ("FINDING:UNMAPPED", "ev_charging"): _NOT,
}
WIRE_KEYS = ("FINDING:GENERATOR_SUPPORT_CANDIDATE", "FINDING:COLD_START_FAILURE", "FINDING:COLD_EXCURSION",
             "FINDING:EV_INTERRUPTION", "FINDING:UNEXPLAINED_FUEL", "FINDING:UNMAPPED")

MG = REGISTRIES["MINI_GRID"]


def _pins(**overrides: tuple[str, str]) -> dict[str, pins.Pin]:
    """The real pins with `mechanism=(structure_key, factor_id)` overrides; a `None` value drops the mechanism."""
    out = dict(pins.PINS)
    for mechanism, target in overrides.items():
        if target is None:
            out.pop(mechanism, None)
        else:
            out[mechanism] = pins.Pin(mechanism, *target)
    return out


# ---------------------------------------------------------------- T1 pins against the design and the manifest


def test_t1_pins_equal_the_design_table():
    assert {m: (p.structure_key, p.factor_id) for m, p in pins.PINS.items()} == DESIGN_PINS
    assert all(p.mechanism == m for m, p in pins.PINS.items())
    assert dict(pins.PENDING_PINS) == DESIGN_PENDING
    assert isinstance(pins.PINS, MappingProxyType) and isinstance(pins.PENDING_PINS, MappingProxyType)
    assert dict(pins.DOMAIN_OF_STRUCTURE) == OWN_DOMAIN_OF_STRUCTURE


def test_t1_pin_is_a_frozen_record():
    pin = pins.Pin("X", "MINI_GRID", "candidate_l")
    with pytest.raises(dataclasses.FrozenInstanceError):
        pin.factor_id = "diesel_l"  # type: ignore[misc]


@pytest.mark.parametrize("mechanism", sorted(DESIGN_PINS))
def test_t1_each_pin_sits_on_a_manifest_findings_row(mechanism):
    structure_key, factor_id = DESIGN_PINS[mechanism]
    category = REGISTRIES[structure_key].row(factor_id).home.category
    structure = MANIFEST["structures"][structure_key]
    # 3B6 (D-3B6.5): a row on a node that is exactly the pinned leaf (a bare rename) counts as the leaf's row.
    rows = [r for r in MANIFEST["home_categories"]["findings"]
            if (r["factor"] == factor_id or structure.get(r["factor"]) == factor_id)
            and OWN_HEADING[r["heading"]] == category
            and OWN_SITE_STRUCTURE.get(r["site"]) == structure_key]
    if mechanism in NO_MANIFEST_ROW:
        assert not rows, f"{mechanism} now has a findings row; drop it from NO_MANIFEST_ROW"
        return
    assert rows, f"no home_categories.findings row for {structure_key}/{factor_id} under {category}"


# ---------------------------------------------------------------- T2 start-up check


def _plants() -> dict[str, tuple[dict, str]]:
    """One planted `check_pins` argument set per §3 code, with the full text it must raise."""
    entries = dict(outcome_map.ENTRIES)
    return {
        "STRUCTURE_PIN": ({"pins": _pins(UNEXPLAINED_FUEL=("MINI_GRID", "no_such_factor"))},
                          "STRUCTURE_PIN MINI_GRID/no_such_factor"),
        "STRUCTURE_PIN_TOTAL": ({"pins": _pins(UNEXPLAINED_FUEL=("MINI_GRID", "diesel_l"))},
                                "STRUCTURE_PIN_TOTAL MINI_GRID/diesel_l"),
        "STRUCTURE_PIN_DUPLICATE": ({"pending": {**pins.PENDING_PINS, "UNEXPLAINED_FUEL": "MINI_GRID"}},
                                    "STRUCTURE_PIN_DUPLICATE MINI_GRID/UNEXPLAINED_FUEL"),
        "STRUCTURE_PIN_UNKNOWN": ({"pending": {**pins.PENDING_PINS, "NOT_A_MECHANISM": "COLD_CHAIN"}},
                                  "STRUCTURE_PIN_UNKNOWN COLD_CHAIN/NOT_A_MECHANISM"),
        "STRUCTURE_PIN_MISSING": ({"entries": {**entries, "FINDING:NEW_MECHANISM": (("MG-2",), ())}},
                                  "STRUCTURE_PIN_MISSING -/NEW_MECHANISM"),
    }


def test_t2_pin_codes_are_separate_and_in_order():
    assert PIN_CODES == ("STRUCTURE_PIN", "STRUCTURE_PIN_TOTAL", "STRUCTURE_PIN_DUPLICATE",
                         "STRUCTURE_PIN_UNKNOWN", "STRUCTURE_PIN_MISSING")
    assert not set(PIN_CODES) & set(CODES)  # D-3B2.13
    assert "check_pins" in check_module.__all__ and "PIN_CODES" in check_module.__all__


@pytest.mark.parametrize("code", PIN_CODES)
def test_t2_each_code_is_raised_with_its_full_text(code):
    kwargs, text = _plants()[code]
    with pytest.raises(StructureError) as caught:
        check_pins(**kwargs)
    assert str(caught.value) == text
    assert caught.value.code == code


def test_t2_plants_cover_every_code():
    assert set(_plants()) == set(PIN_CODES)


def test_t2_a_pin_on_a_structure_with_no_registry_is_refused():
    with pytest.raises(StructureError, match=r"^STRUCTURE_PIN COLD_CHAIN/candidate_l$"):
        check_pins(pins=_pins(UNEXPLAINED_FUEL=("COLD_CHAIN", "candidate_l")))


@pytest.mark.parametrize("factor_id", ["diesel_l", "cost_to_serve", "metered_kwh", "billed_kwh"])
def test_t2_a_pin_on_a_sum_is_refused(factor_id):  # D-3B2.12 live totals
    with pytest.raises(StructureError, match=rf"^STRUCTURE_PIN_TOTAL MINI_GRID/{factor_id}$"):
        check_pins(pins=_pins(UNEXPLAINED_FUEL=("MINI_GRID", factor_id)))


def test_t2_a_pin_on_a_product_is_accepted():
    check_pins(pins=_pins(UNEXPLAINED_FUEL=("MINI_GRID", "fuel_cost")))


@pytest.mark.parametrize("expression, total", [
    ("candidate_l", True),  # a bare Ref (an alias) counts as a total
    ("candidate_l - unexplained_l", True),
    ("-candidate_l + 2", True),
    ("candidate_l * 2", False),
    ("candidate_l / 2", False),
    ("max(candidate_l, unexplained_l)", False),
    ("candidate_l + unexplained_l * 2", False),  # any `*` anywhere makes it pinnable
])
def test_t2_which_planted_nodes_are_totals(expression, total):
    row = dataclasses.replace(MG.row("diesel_l"), factor_id="planted_node", expression=expression)
    # 3B6: the real cold and EV registries stay beside the planted one, as the real pins name them.
    planted = {**REGISTRIES, "MINI_GRID": Registry("MINI_GRID", MG.version, MG.rows + (row,))}
    planted_pins = _pins(UNEXPLAINED_FUEL=("MINI_GRID", "planted_node"))
    if total:
        with pytest.raises(StructureError, match=r"^STRUCTURE_PIN_TOTAL MINI_GRID/planted_node$"):
            check_pins(pins=planted_pins, registries=planted)
    else:
        check_pins(pins=planted_pins, registries=planted)


def test_t2_the_real_data_passes():
    check_pins()
    check_all()


def test_t2_check_all_with_planted_registries_runs_no_pin_check(monkeypatch):
    # P5 (D-3B2.10): a set with no MINI_GRID would fail STRUCTURE_PIN against the real pins; it is not checked.
    # 3B6 (D-3B6.4, D-3B6.21): the planted key differs from its registry's key, so L2 refuses it first
    # (`STRUCTURE_CATALOGUE X/-`, the same registry code).
    check_all(registries={})
    with pytest.raises(StructureError) as caught:
        check_all(registries={"X": Registry("NOT_MINI_GRID_KEY", MG.version, MG.rows)})
    assert caught.value.code in CODES  # a registry code (STRUCTURE_CATALOGUE), never a pin code
    monkeypatch.setattr(pins, "PINS", MappingProxyType(_pins(UNEXPLAINED_FUEL=("MINI_GRID", "diesel_l"))))
    check_all(registries={"MINI_GRID": MG})  # a bad pin is not read when registries are given


def test_t2_check_all_without_argument_runs_the_pin_check(monkeypatch):
    monkeypatch.setattr(pins, "PINS", MappingProxyType(_pins(UNEXPLAINED_FUEL=("MINI_GRID", "diesel_l"))))
    with pytest.raises(StructureError, match=r"^STRUCTURE_PIN_TOTAL MINI_GRID/diesel_l$"):
        check_all()


def test_t2_create_app_refuses_a_bad_pin(monkeypatch):
    from assetops_backend.main import create_app

    monkeypatch.setattr(pins, "PINS", MappingProxyType(_pins(UNEXPLAINED_FUEL=("MINI_GRID", "no_such_factor"))))
    with pytest.raises(ConfigurationError, match=r"^STRUCTURE_PIN MINI_GRID/no_such_factor$") as caught:
        create_app()
    assert isinstance(caught.value.__cause__, StructureError)


def test_t2_create_app_refuses_an_unpinned_mechanism(monkeypatch):  # P2
    from assetops_backend.main import create_app

    pinned = {k: v for k, v in pins.PINS.items() if k != "EV_INTERRUPTION"}  # 3B6: it is pinned, not pending
    monkeypatch.setattr(pins, "PINS", MappingProxyType(pinned))
    with pytest.raises(ConfigurationError, match=r"^STRUCTURE_PIN_MISSING -/EV_INTERRUPTION$"):
        create_app()


# ---------------------------------------------------------------- T3 parity


def test_t3_parity_equals_the_ruled_differences():
    got = {(d.mechanism, d.literal_category, d.registry_category, d.literal_lens, d.registry_lens)
           for d in pins.parity()}
    assert got == EXPECTED_DIVERGENCES
    assert len(pins.parity()) == len(EXPECTED_DIVERGENCES)


def test_t3_a_new_difference_is_reported(monkeypatch):  # P3
    rows = tuple(dataclasses.replace(r, home=Home("PROTECT_ASSET", "P1")) if r.factor_id == "candidate_l" else r
                 for r in MG.rows)
    monkeypatch.setattr(registry_module, "REGISTRIES", MappingProxyType(  # 3B6: cold and EV kept for their pins
        {**REGISTRIES, "MINI_GRID": Registry("MINI_GRID", MG.version, rows)}))
    got = {(d.mechanism, d.registry_category) for d in pins.parity()}
    assert ("GENERATOR_SUPPORT_CANDIDATE", "PROTECT_ASSET") in got


def test_t3_parity_compares_only_the_pin_domain():  # P7 (D-3B2.7)
    for divergence in pins.parity():
        assert pins.PINS[divergence.mechanism].structure_key == "MINI_GRID"
    assert outcome_map.outcome_roles("FINDING:GENERATOR_SUPPORT_CANDIDATE", "cold_chain") == ((), ())
    assert "GENERATOR_SUPPORT_CANDIDATE" not in {d.mechanism for d in pins.parity()}


# ---------------------------------------------------------------- T4 no wire change


def test_t4_the_snapshot_covers_every_finding_key():
    finding_keys = {k for k in outcome_map.ENTRIES if k.startswith("FINDING:")} | {"FINDING:UNMAPPED"}
    assert set(WIRE_KEYS) == finding_keys
    assert set(WIRE_SNAPSHOT) == {(k, d) for k in WIRE_KEYS for d in DOMAINS}


@pytest.mark.parametrize("key", WIRE_KEYS)
@pytest.mark.parametrize("domain", DOMAINS)
def test_t4_wire_is_unchanged(key, domain):
    assert (outcome_map.categories_for(key, domain), outcome_map.lens_flags(key, domain)) == WIRE_SNAPSHOT[(key, domain)]


def test_t4_outcomes_folder_is_untouched():
    base = subprocess.run(["git", "merge-base", "main", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    if base.returncode != 0:
        pytest.skip("no git main ref in this checkout")
    diff = subprocess.run(["git", "diff", base.stdout.strip(), "--", "backend/assetops_backend/outcomes/"],
                          cwd=ROOT, capture_output=True, text=True, check=True)
    assert diff.stdout == ""


# ---------------------------------------------------------------- T5 pinned_category


@pytest.mark.parametrize("mechanism", ["GENERATOR_SUPPORT_CANDIDATE", "UNEXPLAINED_FUEL"])
def test_t5_mini_mechanisms_read_optimize(mechanism):
    assert pins.pinned_category(mechanism) == "OPTIMIZE_COST"
    assert pins.pin_of(mechanism) == pins.Pin(mechanism, *DESIGN_PINS[mechanism])


@pytest.mark.parametrize("mechanism", ["NOT_A_MECHANISM"])  # 3B6: the three pending mechanisms are pinned (§3)
def test_t5_pending_and_unknown_read_none(mechanism):
    assert pins.pinned_category(mechanism) is None
    assert pins.pin_of(mechanism) is None


def test_t5_a_placement_home_reads_none(monkeypatch):
    rows = tuple(dataclasses.replace(r, home=Home("ABOVE", None)) if r.factor_id == "candidate_l" else r
                 for r in MG.rows)
    monkeypatch.setattr(registry_module, "REGISTRIES", MappingProxyType(
        {"MINI_GRID": Registry("MINI_GRID", MG.version, rows)}))
    assert pins.pinned_category("GENERATOR_SUPPORT_CANDIDATE") is None


def test_t5_reads_the_registry_at_call_time(monkeypatch):  # P4
    rows = tuple(dataclasses.replace(r, home=Home("PROTECT_ASSET", "P1")) if r.factor_id == "unexplained_l" else r
                 for r in MG.rows)
    monkeypatch.setattr(registry_module, "REGISTRIES", MappingProxyType(
        {"MINI_GRID": Registry("MINI_GRID", MG.version, rows)}))
    assert pins.pinned_category("UNEXPLAINED_FUEL") == "PROTECT_ASSET"
