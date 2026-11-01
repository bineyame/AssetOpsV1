"""POLISH PA-2a: pure pins of the server copy, display codes and Finding labels (build sheet §3, §3.1, Addenda 4
and 6). Captures are deferred to PA-3 (Addendum 3); these exact-output tests are the screen proof until then."""
from __future__ import annotations

from types import SimpleNamespace

from assetops_backend.analytics import cold_site_reads as csr
from assetops_backend.analytics.finding_episode import (
    MERGED, NO_LONGER_SUPPORTED, SUPPORTED, TITLES, UNCONFIRMED)
from assetops_backend.estate import evidence_money, placement, portfolio
from assetops_backend.outcomes import warnings as w
from assetops_backend.outcomes.display_code import FINDING_LABEL, display_code, finding_label
from assetops_backend.site_outcomes import board, mini
from assetops_backend.work import domain_action_index as dai
from assetops_backend.work import site_index


# ---- display_code (§3 record codes) ---------------------------------------------------------------------------

def test_display_code_pads_to_three_digits() -> None:
    assert display_code("ACT-000001") == "ACT-001"
    assert display_code("WR-000006") == "WR-006"
    assert display_code("INC-000005") == "INC-005"
    assert display_code("PM-000013") == "PM-013"
    assert display_code("ACT-000048") == "ACT-048"
    assert display_code("ACT-001234") == "ACT-1234"
    assert display_code("ACT-1234567") == "ACT-1234567"
    assert display_code("ACT-000000") == "ACT-000"


def test_display_code_leaves_other_text_unchanged() -> None:
    assert display_code(None) is None
    assert display_code("") == ""
    assert display_code("generator-1") == "generator-1"
    assert display_code("Plan ready") == "Plan ready"
    assert display_code("act-000001") == "act-000001"
    assert display_code("ACT-00x1") == "ACT-00x1"
    assert display_code("ACT-") == "ACT-"
    assert display_code("-000001") == "-000001"
    assert display_code("ACT-000001-2") == "ACT-000001-2"


def test_finding_label_is_title_or_plain_finding() -> None:
    assert finding_label("Chamber temperature above policy") == "Chamber temperature above policy"
    assert finding_label(None) == FINDING_LABEL == "Finding"
    assert finding_label("") == "Finding"


# ---- codes inside server labels and sentences (Addendum 6 Q8, Q9) ----------------------------------------------

def test_board_item_text_and_action_name_use_display_codes() -> None:
    assert board._item_text("ACT-000003", "Inspect connector") == "ACT-003 · Inspect connector"
    assert board._item_text("ACT-000003", "") == "ACT-003"
    assert board._item_text(None, "Inspect connector") == "Inspect connector"
    assert board._action_name(SimpleNamespace(code="ACT-000001", title="")) == "ACT-001"
    assert board._action_name(SimpleNamespace(code=None, title="Trial")) == "Trial"


def test_warning_ref_labels_use_display_codes() -> None:
    plan = w.PlanCue(plan_id="p1", code="PM-000013", title="Generator service", due_at=None, due_on=None,
                     asset_id=None, href="/maintenance/preventive")
    assert w._plan_ref(plan) == {"kind": "PLAN", "id": "p1", "label": "PM-013", "href": "/maintenance/preventive"}


def test_mini_verified_results_text_uses_display_code() -> None:
    assert mini.VERIFICATION_TEXT["PENDING"].format(code=display_code("ACT-000001")) == "ACT-001 not yet verified"
    text = mini.VERIFIED_WITH_COST.replace("{amount}", "0.12").replace("{currency}", "USD")
    assert text.format(code=display_code("ACT-000001")) == (
        "ACT-001 verified on test data: estimated effect of the trial (not money saved): "
        "0.12 USD less supply cost per kWh")


def test_action_links_read_display_code_or_plain_action() -> None:
    assert site_index.action_label("ACT-000003") == "ACT-003"
    assert site_index.action_label(None) == site_index.ACTION_LABEL == "Action"
    link = site_index._action_link("COLD-LAB-001", {"kind": "DOMAIN_ACTION", "action_id": "0" * 8 + "-1",
                                                    "action_event_id": None, "finding_revision_id": "r"}, None)
    assert link["label"] == "Action"
    w1 = site_index._action_link("MG-001", {"action_id": "abcdef12-0000", "action_event_id": "e"}, None)
    assert w1["label"] == "Action"


def test_finding_links_read_the_revision_title() -> None:
    link = {"finding_id": "d374e29a-1111", "finding_revision_id": "R1"}
    assert site_index._finding_link("S", link, True, {"r1": "Chamber temperature above policy"})["label"] == (
        "Chamber temperature above policy")
    assert site_index._finding_link("S", link, True)["label"] == "Finding"
    assert dai._title_label({"title": "Connector out of service"}) == "Connector out of service"
    assert dai._title_label(None) == "Finding"
    assert dai._title_label({"id": "x"}) == "Finding"


# ---- Finding titles (§3 / Addendum 4) ---------------------------------------------------------------------------

def test_finding_titles_are_the_ruled_plain_titles() -> None:
    assert TITLES[SUPPORTED] == "Generator may have been on longer than needed"
    assert TITLES[UNCONFIRMED] == "Extra generator time not confirmed by the latest check"
    assert TITLES[NO_LONGER_SUPPORTED] == "Extra generator time no longer supported by the latest check"
    assert TITLES[MERGED] == "Generator support episode merged into an earlier episode"


# ---- §3.1 BE strings --------------------------------------------------------------------------------------------

def test_placement_reason_texts() -> None:
    assert placement.REASON_TEXT["EPISODE_OPEN"] == "No end time yet"
    row = {"_recurs_after": "d374e29a-0000", "_recurs_after_title": "Chamber temperature above policy"}
    assert placement._reason("RECURRED", row).text == (
        "Happened again after an earlier occurrence (Chamber temperature above policy)")
    assert placement._reason("RECURRED", {"_recurs_after": "d374e29a-0000"}).text == (
        "Happened again after an earlier occurrence")
    assert placement._reason("RECURRED", {"_recurs_after": "x", "_recurs_after_title": None}).text == (
        "Happened again after an earlier occurrence")


def test_no_action_agreed_yet_keeps_its_reason_and_in_hand_label() -> None:
    assert portfolio.workflow_label(None) == "No action agreed yet"
    assert placement._ACTION_REASON["No action agreed yet"] == "NO_ACTION_RECORDED"
    assert board.WORKFLOW_IN_HAND["No action agreed yet"] == "Plan ready"
    assert "Recommendation not accepted" not in placement._ACTION_REASON
    assert "Recommendation not accepted" not in board.WORKFLOW_IN_HAND


def test_portfolio_and_estate_labels() -> None:
    assert portfolio.DISPLAYED_VALUE["WITHHELD"] == "Can't be compared across these sites yet"
    assert evidence_money.CURRENT_VIEW == "Current view"


def test_cold_read_copy_and_transfer_observation() -> None:
    assert csr.ATTENTION["COLD_START_FAILURE"] == "Backup generator did not start on its own"
    assert csr.plain_limitation("Not observed: TRANSFER.") == "No record of switching to backup power."
    assert evidence_money.plain_limitation is csr.plain_limitation
    assert evidence_money.COLD_OBSERVATION_WORDS["TRANSFER"] == "No record of switching to backup power."
    sel = SimpleNamespace(result={"limitations": ["Not observed: TRANSFER."]})
    snap = {"selected": {csr.START: sel}}
    assert csr.ColdSiteReadService._limits(snap, csr.START) == "No record of switching to backup power."


def test_trial_cost_and_before_after_lines() -> None:
    assert board.COST_NO_CHANGE == "Estimated effect of the trial (not money saved): no lower supply cost per kWh."
    assert board.COST_CHANGE.format(amount="0.12", currency="USD") == (
        "Estimated effect of the trial (not money saved): 0.12 USD less supply cost per kWh.")
    assert board.TRIAL_ATTRIBUTED.format(label="ignored", before="missed", after="met") == (
        "Goal before the trial: missed; after: met.")
