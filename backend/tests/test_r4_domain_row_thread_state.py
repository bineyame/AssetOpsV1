"""R4.1: a Cold/EV Portfolio row with no joined Action reads its thread state (pure `portfolio_row`, no DB)."""

from __future__ import annotations

from datetime import datetime, timezone

from assetops_backend.estate import portfolio
from assetops_backend.estate.portfolio import THREAD_LABEL, portfolio_row

T0 = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)


def row(domain: str, mechanism: str, thread_state: str | None) -> dict:
    code = {"MINIGRID": "KOBO-001", "COLDCHAIN": "COLD-001", "EV_CHARGING": "EV-001"}[domain]
    return {
        "_site": {"site_code": code, "site_code_key": code.lower()}, "site_id": "S1", "site_code": code,
        "site_name": "Site", "_domain": domain, "finding_id": "f-1", "finding_revision_id": "r-1",
        "finding_label": "x", "title": "x", "_mechanism": mechanism, "episode_start": None, "_episode_end": None,
        "lifecycle": "SUPPORTED", "lens_flags": [], "priority": None, "consequence": None,
        "source_provenance": {"state": "REGISTERED_SIMULATION"}, "_at": T0,
        "link_refs": {"site": {"kind": "SITE", "site": code},
                      "finding": {"kind": "FINDING", "site": code, "id": "f-1", "revision_id": "r-1"}},
        "_thread": None if thread_state is None else {"state": thread_state}}


def build(domain: str, mechanism: str, thread_state: str | None) -> dict:
    return portfolio_row(row(domain, mechanism, thread_state), [])


def test_a_cold_start_failure_with_an_action_in_hand_reads_pending() -> None:
    out = build("COLDCHAIN", "COLD_START_FAILURE", "ACTION_IN_HAND")
    assert out["workflow_label"] == "Pending" and out["action_id"] is None
    assert out["placement"]["group"] == "ACT_NOW"
    assert [r["code"] for r in out["placement"]["reasons"]] == ["EPISODE_OPEN", "ACTION_PENDING"]


def test_b_a_cold_row_with_an_open_thread_keeps_no_action_agreed() -> None:
    assert build("COLDCHAIN", "COLD_EXCURSION", "OPEN")["workflow_label"] == "No action agreed yet"


def test_c_an_ev_row_with_a_change_applied_reads_applied() -> None:
    assert build("EV_CHARGING", "EV_INTERRUPTION", "CHANGE_APPLIED")["workflow_label"] == "Applied"


def test_d_a_cold_row_with_no_thread_keeps_no_action_agreed() -> None:
    assert build("COLDCHAIN", "COLD_START_FAILURE", None)["workflow_label"] == "No action agreed yet"


def test_e_a_mini_grid_row_with_no_action_ignores_its_thread() -> None:
    """Must fail if the rule is widened beyond Cold/EV: a mini-grid join is authoritative."""
    out = build("MINIGRID", "GENERATOR_SUPPORT_CANDIDATE", "ACTION_IN_HAND")
    assert out["workflow_label"] == "No action agreed yet"


def test_f_the_fuel_row_is_unchanged() -> None:
    assert build("MINIGRID", "UNEXPLAINED_FUEL", "RESOLVED_MONITORING")["workflow_label"] == "Verified"
    assert build("MINIGRID", "UNEXPLAINED_FUEL", "OPEN")["workflow_label"] == "No action agreed yet"
    assert not hasattr(portfolio, "FUEL_THREAD_LABEL") and THREAD_LABEL["ACTION_IN_HAND"] == "Pending"
