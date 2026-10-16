"""S6-02a phase 2 pure verdict rules: VERIFIED / INEFFECTIVE / INCONCLUSIVE, the per-window source pair, the plan's
battery/bound-asset filter (phase-1 review F6) and `+00:00` timestamps (F7). No database.

`D-2026-10-16-s6-verification`: a complete, comparable, source-coherent pair whose target and every guardrail pass is
VERIFIED; a fully assessable target miss and/or measured guardrail failure is INEFFECTIVE (`GUARDRAIL_FAIL` only for
the latter); any unknown required fact is INCONCLUSIVE even beside a known failure, which stays in the reasons.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from test_s6_verification_rules import RESERVE, T0, evidence, full_window, point

from assetops_backend.actions import verification_rules as vr

AUTHORED = {"state": "AUTHORED_DEMONSTRATION", "fixtures": [{"fixture_id": "D-verification-window",
                                                            "fixture_version": 1}], "runs": []}


def registered(digest: str) -> dict:
    return {"state": "REGISTERED_SIMULATION", "fixtures": [], "runs": [{"run_id": digest, "run_identity_sha256": digest}]}


LATER = T0 + timedelta(days=7)


def pair(*, base_soc="50", later_soc="50", later_kw="10", later=None, base=None):
    b = base or evidence(full_window())
    lt = later or evidence(full_window(LATER, soc=later_soc, load_kw=later_kw), start=LATER,
                           reserves=[vr.ReserveValue(RESERVE[0].value, T0, None, "rev-2")])
    return b, lt


def verdict(b, lt, *, baseline_seconds=1200, later_seconds=600, source=None, blockers=()):
    target = {"state": "KNOWN", "candidate_seconds": later_seconds, "reasons": []} if later_seconds is not None \
        else {"state": "INCONCLUSIVE", "candidate_seconds": None, "reasons": ["OPEN_BOUND"]}
    return vr.decide(baseline=b, later=lt, comparable=vr.comparability(b, lt), baseline_seconds=baseline_seconds,
                     later_target=target, source=source or vr.source_pair(AUTHORED, AUTHORED), blockers=blockers)


def test_complete_pass_is_verified_with_every_metric_recorded() -> None:
    b, lt = pair()
    out = verdict(b, lt)
    assert out["outcome"] == "VERIFIED" and out["reasons"] == ["TARGET_AND_GUARDRAILS_PASS"]
    keys = {(m["metric_key"], m["window_name"]) for m in out["metrics"]}
    assert {("target_reduction", "COMPARISON"), ("unserved_critical_energy", "COMPARISON"),
            ("below_reserve_seconds", "COMPARISON"), ("terminal_soc", "COMPARISON"),
            ("source_provenance", "COMPARISON"), ("window_coverage", "BASELINE"), ("window_coverage", "LATER"),
            ("feeder_demand_energy_band", "COMPARISON"), ("initial_soc_band", "COMPARISON")} <= keys
    assert all(m["state"] == "PASS" for m in out["metrics"])


def test_target_edge_is_inclusive_and_a_miss_is_ineffective_without_guardrail_reason() -> None:
    b, lt = pair()
    assert verdict(b, lt, baseline_seconds=1200, later_seconds=900)["outcome"] == "VERIFIED"  # 4*900 == 3*1200
    miss = verdict(b, lt, baseline_seconds=1200, later_seconds=901)
    assert miss["outcome"] == "INEFFECTIVE" and miss["reasons"] == ["TARGET_MISS"]
    assert "GUARDRAIL_FAIL" not in miss["reasons"]


def test_measured_guardrail_failure_is_ineffective_with_guardrail_fail() -> None:
    # Later SOC 29 is below the 30 reserve at every slot: sampled breach seconds > 0. Initial SOC must stay within the
    # two-point band, so the baseline also starts at 30 (not below reserve) and ends higher than the later window.
    b, lt = pair(later=evidence(full_window(LATER, soc="29"), start=LATER), base=evidence(full_window(soc="30")))
    out = verdict(b, lt)
    assert out["outcome"] == "INEFFECTIVE" and out["reasons"][0] == "GUARDRAIL_FAIL"
    assert "GUARDRAIL:below_reserve_seconds" in out["reasons"] and "GUARDRAIL:terminal_soc" in out["reasons"]
    both = verdict(b, lt, later_seconds=1000)
    assert both["outcome"] == "INEFFECTIVE" and both["reasons"][-1] == "TARGET_MISS"


def test_unknown_overrides_a_known_failure_which_stays_visible() -> None:
    b = evidence(full_window(soc="30"))
    lt = evidence(full_window(LATER, soc="29", terminal=False), start=LATER)  # terminal SOC missing
    out = verdict(b, lt)
    assert out["outcome"] == "INCONCLUSIVE"
    assert "INCOMPLETE_LATER_WINDOW" in out["reasons"] and "GUARDRAIL_UNKNOWN:terminal_soc" in out["reasons"]
    assert "KNOWN_FAILURE:below_reserve_seconds" in out["reasons"] and "GUARDRAIL_FAIL" not in out["reasons"]


@pytest.mark.parametrize("kw, outcome", [("11", "VERIFIED"), ("11.0001", "INCONCLUSIVE")])
def test_comparability_band_edge(kw: str, outcome: str) -> None:
    b, lt = pair(later_kw=kw)  # +10 % feeder energy is inside the inclusive band; anything more is not comparable
    got = verdict(b, lt)
    assert got["outcome"] == outcome
    if outcome == "INCONCLUSIVE":
        assert "NOT_COMPARABLE" in got["reasons"]


def test_missing_critical_role_and_unknown_target_and_blockers_are_inconclusive() -> None:
    b, _ = pair()
    no_critical = [r for r in full_window(LATER) if r.role != "critical_load_delivered_power"]
    lt = evidence(no_critical, start=LATER)
    out = verdict(b, lt)
    assert out["outcome"] == "INCONCLUSIVE" and "GUARDRAIL_UNKNOWN:unserved_critical_energy" in out["reasons"]
    b, lt = pair()
    assert "TARGET_UNKNOWN" in verdict(b, lt, later_seconds=None)["reasons"]
    blocked = verdict(b, lt, blockers=["FOUNDATION_CHANGED"])
    assert blocked["outcome"] == "INCONCLUSIVE" and "BLOCKED:FOUNDATION_CHANGED" in blocked["reasons"]


def test_source_pair_is_per_window_and_fails_closed() -> None:
    assert vr.source_pair(AUTHORED, AUTHORED)["state"] == "PASS"
    assert vr.source_pair(registered("a" * 64), registered("b" * 64))["state"] == "PASS"
    shared = vr.source_pair(registered("a" * 64), registered("a" * 64))
    assert shared["state"] == "UNKNOWN" and "one registered run" in shared["problems"][0]
    crossed = vr.source_pair(AUTHORED, registered("a" * 64))
    assert crossed["state"] == "UNKNOWN" and "crossed" in crossed["problems"][0]
    other = {**AUTHORED, "fixtures": [{"fixture_id": "D-other", "fixture_version": 1}]}
    assert vr.source_pair(AUTHORED, other)["state"] == "UNKNOWN"
    # A MIXED or UNKNOWN set never passes, even shaped like two distinct single runs.
    for state in ("MIXED", "UNKNOWN"):
        assert vr.source_pair({**registered("a" * 64), "state": state},
                              {**registered("b" * 64), "state": state})["state"] == "UNKNOWN"
    for bad in ({"state": "MIXED", "reasons": ["CROSSED"]}, {"state": "UNKNOWN"}, None):
        assert vr.source_pair(AUTHORED, bad)["state"] == "UNKNOWN"
    b, lt = pair()
    out = verdict(b, lt, source=vr.source_pair(AUTHORED, {"state": "MIXED"}))
    assert out["outcome"] == "INCONCLUSIVE" and "SOURCE_NOT_COHERENT" in out["reasons"]


def test_f6_soc_of_another_battery_and_unbound_assets_are_ignored() -> None:
    readings = full_window()
    other = [point("battery_soc", "other-bat", T0 + vr.SLOT * i, "5") for i in range(13)]
    mixed = vr.window_evidence(T0, readings + other, load_asset_ids=["load-a", "load-b"],
                               critical_load_asset_id="crit", reserves=RESERVE)
    assert mixed["complete"] is False  # without the filter two SOC assets are ambiguous
    kept = vr.window_evidence(T0, readings + other, load_asset_ids=["load-a", "load-b"],
                              critical_load_asset_id="crit", reserves=RESERVE, battery_asset_id="bat",
                              role_assets={"generator_power": ["gen"]})
    assert kept["complete"] is True and kept["below_reserve_seconds"] == 0
    unbound = vr.window_evidence(T0, readings, load_asset_ids=["load-a", "load-b"], critical_load_asset_id="crit",
                                 reserves=RESERVE, battery_asset_id="bat", role_assets={"generator_power": ["gen-2"]})
    assert unbound["complete"] is False  # the bound generator reported nothing


def test_f7_rule_timestamps_use_plus_zero() -> None:
    w = evidence(full_window())
    assert w["window_start"].endswith("+00:00") and w["slots"][0]["slot_start"].endswith("+00:00")
    assert not any(str(s["slot_end"]).endswith("Z") for s in w["slots"])
