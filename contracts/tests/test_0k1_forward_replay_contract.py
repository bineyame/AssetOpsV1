"""0K1: the forward replay contract's construction rules (spec §2.1, D-0K1.9, D-0K1.18)."""

from __future__ import annotations

import ast
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from assetops_contracts import forward_replay as contract
from assetops_contracts.forward_replay import (
    ForwardReplayProjection,
    ForwardReplayRefused,
    ForwardReplayRequest,
    LoadSeries,
    ReplaySettings,
    ReplayStartState,
)

F = Fraction
INEXACT = (0.5, 1, Decimal("0.5"))


def _request(**overrides) -> ForwardReplayRequest:
    fields = dict(case_id="baseline", pv_available_kw=(F(1), F(2)), loads=(LoadSeries("load-mill", (F(3), F(4))),),
                  start=ReplayStartState(F(40), F(300), "STOPPED"), settings=ReplaySettings())
    fields.update(overrides)
    return ForwardReplayRequest(**fields)


def test_a_well_formed_request_constructs_and_none_is_allowed_inside_a_series() -> None:
    request = _request(pv_available_kw=(F(1), None), loads=(LoadSeries("load-mill", (None, F(4))),))
    assert request.settings == ReplaySettings()


@pytest.mark.parametrize("bad", INEXACT, ids=["float", "int", "Decimal"])
@pytest.mark.parametrize("field", ["pv", "load", "soc", "fuel", "stop", "reserve"])
def test_every_numeric_request_field_refuses_a_non_fraction(field: str, bad) -> None:
    with pytest.raises(TypeError):
        if field == "pv":
            _request(pv_available_kw=(F(1), bad))
        elif field == "load":
            LoadSeries("load-mill", (bad, F(1)))
        elif field == "soc":
            ReplayStartState(bad, F(300), "STOPPED")
        elif field == "fuel":
            ReplayStartState(F(40), bad, "STOPPED")
        elif field == "stop":
            ReplaySettings(stop_soc_pct=bad)
        else:
            ReplaySettings(reserve_soc_pct=bad)


@pytest.mark.parametrize("case_id", ["Bad Id", "", "a" * 41])
def test_a_case_id_outside_the_pattern_is_refused(case_id: str) -> None:
    with pytest.raises(ValueError):
        _request(case_id=case_id)


def test_a_forty_character_case_id_is_accepted() -> None:
    assert _request(case_id="a" * 40).case_id == "a" * 40


def test_the_generator_state_is_not_judged_at_construction() -> None:
    # The refusal is the adapter's (T6), so its reason reaches the caller as a code (D-0K1.18).
    assert ReplayStartState(F(40), F(300), "RUNNING").generator_state == "RUNNING"


def _projection(**overrides) -> ForwardReplayProjection:
    fields = dict(base_run_id="run-x", case_id="baseline", status="COMPLETED", model_profile_id="mini-grid",
                  model_profile_version=7, interval_start="2026-09-22T03:00:00Z", timestep_minutes=5,
                  stop_soc_pct=F(90), stop_source="BASELINE", reserve_soc_pct=F(30), reserve_source="BASELINE",
                  steps=(), soc_end_pct=F(50), fuel_end_l=F(290), min_soc_pct=F(30), generator_kwh=F(0),
                  unserved_kwh=F(0), starts=0, running_steps=0, fuel_burned_l=F(10), clipped_offsets=(),
                  replay_identity="id")
    fields.update(overrides)
    return ForwardReplayProjection(**fields)


def test_failure_kind_is_set_if_and_only_if_failed() -> None:
    assert _projection().evidence_class == "MODELLED"
    assert _projection(status="FAILED", failure_kind="PHYSICAL_RESOLUTION_FAILURE").status == "FAILED"
    with pytest.raises(ValueError):
        _projection(status="FAILED")
    with pytest.raises(ValueError):
        _projection(failure_kind="PHYSICAL_RESOLUTION_FAILURE")
    with pytest.raises(ValueError):
        _projection(status="PARTIAL")


def test_a_refusal_speaks_only_its_own_vocabulary() -> None:
    with pytest.raises(ValueError):
        ForwardReplayRefused("NOPE", "", "")
    refused = ForwardReplayRefused("INPUT_GAP", "pv@50", "a gap")
    assert (refused.code, refused.subject, refused.detail) == ("INPUT_GAP", "pv@50", "a gap")


def test_the_module_imports_only_the_standard_library() -> None:
    tree = ast.parse(Path(contract.__file__).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            roots.add(node.module.split(".")[0])
    assert roots, "vacuous: no import found"
    assert roots <= set(sys.stdlib_module_names) | {"__future__"}, roots
