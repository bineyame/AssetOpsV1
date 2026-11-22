"""6h (`specs/6h-named-option-levers/spec.md` §3.2, §5.3, §10.2 test 1): the named-option lever checks.

Branches 15 to 22 of `check_levers` refuse one planted fault each as `STRUCTURE_LEVER <structure>/<lever>`; the grid
branches 6 to 13 run for `SETTING_GRID` only (D-P6.63)."""
from __future__ import annotations

import dataclasses
from types import MappingProxyType

import pytest

from assetops_backend.structure import pins as pins_module
from assetops_backend.structure.check import StructureError, check_levers
from assetops_backend.structure.levers import (LEVERS, RECORD, STUDY, ChangeSource, Lever, LeverOption, SettingAxis)
from assetops_backend.structure.registry import REGISTRIES

from decimal import Decimal

NAMED = Lever("t_named", "COLD_CHAIN", "excess_kwh", "STATED_OPTIONS", (), "", ("model_factor", "excess_kwh"),
              options=(LeverOption("repair", "REPAIR", ("excess_kwh",)),
                       LeverOption("replace", "CAPEX", ("model_factor", "excess_kwh"))),
              change_sources=MappingProxyType({"model_factor": RECORD, "excess_kwh": RECORD}))


def _registries(lever_id="t_named", factor_id="excess_kwh", key="COLD_CHAIN", **change):
    reg = REGISTRIES[key]
    rows = tuple(dataclasses.replace(r, levers=(*r.levers, lever_id), **change) if r.factor_id == factor_id else r
                 for r in reg.rows)
    return MappingProxyType({**REGISTRIES, key: dataclasses.replace(reg, rows=rows)})


def _named(**change) -> Lever:
    return dataclasses.replace(NAMED, **change)


def _opt(i=0, **change) -> tuple[LeverOption, ...]:
    opts = list(NAMED.options)
    opts[i] = dataclasses.replace(opts[i], **change)
    return tuple(opts)


def _check(lever: Lever, registries=None, pins=None) -> None:
    check_levers(MappingProxyType({**LEVERS, lever.lever_id: lever}), registries or _registries(lever.lever_id),
                 pins_module.PINS if pins is None else pins)


CASES = {
    "15-generator": dict(lever=_named(generator="CHOICE_LIST")),
    "16-sources-keys": dict(lever=_named(change_sources=MappingProxyType({"excess_kwh": RECORD}))),
    "16-source-kind": dict(lever=_named(change_sources=MappingProxyType({"model_factor": RECORD,
                                                                         "excess_kwh": ChangeSource("QUOTE")}))),
    "17-grid-with-options": dict(lever=dataclasses.replace(LEVERS["generator_stop_reserve"],
                                                           options=NAMED.options[:1])),
    "17-named-with-axes": dict(lever=_named(axes=(SettingAxis("stop_soc_pct", (Decimal(90),), "%"),))),
    "17-named-without-options": dict(lever=_named(options=())),
    "17-named-with-template": dict(lever=_named(key_template="repair-{x}")),
    "18-key-form": dict(lever=_named(options=_opt(0, key="Repair"))),
    "18-no-action": dict(lever=_named(options=_opt(0, key="no-action"))),
    "18-repeated": dict(lever=_named(options=_opt(1, key="repair"))),
    "19-kind": dict(lever=_named(options=_opt(0, kind="WISH"))),
    "20-empty": dict(lever=_named(options=_opt(0, changes=()))),
    "20-not-subset": dict(lever=_named(options=_opt(0, changes=("kwh_model",)))),
    "20-order": dict(lever=_named(options=_opt(1, changes=("excess_kwh", "model_factor")))),
    "21-no-action-words": dict(lever=_named(no_action_words="DO_NOTHING")),
    "22-bounds-on-optimize": dict(lever=_named(bounds_required=True)),
}


def test_1_a_planted_named_lever_passes() -> None:
    _check(NAMED)
    _check(_named(bounds_required=True, purpose_factor="nights_without_backup_cover", lever_id="t_cover",
                  changes=("uncovered_nights",), options=(LeverOption("stopgap", "SUPPLIER_REMEDY",
                                                                      ("uncovered_nights",)),),
                  change_sources=MappingProxyType({"uncovered_nights": RECORD}), no_action_words="WAIT_FOR_REMEDY"),
           registries=_registries("t_cover", "nights_without_backup_cover"))


@pytest.mark.parametrize("name", sorted(CASES))
def test_1_each_branch_15_to_22_refuses(name: str) -> None:
    lever = CASES[name]["lever"]
    with pytest.raises(StructureError) as caught:
        _check(lever, registries=_registries(lever.lever_id, lever.purpose_factor, lever.structure_key)
               if lever.lever_id != "generator_stop_reserve" else REGISTRIES)
    assert str(caught.value) == f"STRUCTURE_LEVER {lever.structure_key}/{lever.lever_id}"


def test_1_the_cases_cover_branches_15_to_22() -> None:
    assert sorted({int(n.split("-")[0]) for n in CASES}) == list(range(15, 23))


def test_1_grid_branches_run_for_setting_grid_only() -> None:
    # a named lever has no axes and an empty template: branches 6 to 13 would refuse it (10: template names)
    _check(NAMED)
    with pytest.raises(StructureError):
        _check(dataclasses.replace(LEVERS["generator_stop_reserve"], key_template="stop-{stop_soc_pct}"),
               registries=REGISTRIES)


def test_1_the_generator_lever_reads_its_study_sources_and_keep_settings() -> None:
    lever = LEVERS["generator_stop_reserve"]
    assert dict(lever.change_sources) == {"candidate_l": STUDY, "battery_throughput_kwh": STUDY}
    assert (lever.no_action_words, lever.bounds_required, lever.options) == ("KEEP_SETTINGS", False, ())
