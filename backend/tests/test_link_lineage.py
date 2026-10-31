"""LINK-LINEAGE U1: the pure refresh-chain rule and the board's Finding->Action link
(D-2026-10-31-board-action-refresh-lineage). No database."""
from __future__ import annotations

from dataclasses import replace

from assetops_backend.outcomes.catalogue import CATEGORIES, MINI, SITE_OUTCOMES
from assetops_backend.site_outcomes.board import (
    ActionFact, FindingFact, SignalFact, SiteFacts, assemble, refresh_chain)

GROW, COST, PROTECT, ASSURE = CATEGORIES
START, END = "2026-10-06T14:20:00Z", "2026-10-06T15:20:00Z"


def rev(no: int, transition: str = "BASIS_REFRESHED", lifecycle: str = "SUPPORTED", start: str = START,
        end: str = END) -> dict:
    return {"id": f"r{no}", "revision_no": no, "transition": transition, "lifecycle": lifecycle,
            "episode": {"start": start, "end": end}}


ORIGIN = rev(1, "CREATED")


# --------------------------------------------------------------- positives
def test_p1_one_basis_refresh_links() -> None:
    assert refresh_chain([ORIGIN, rev(2)], "r1", "r2") is True


def test_p2_two_basis_refreshes_link() -> None:
    assert refresh_chain([ORIGIN, rev(2), rev(3)], "r1", "r3") is True


def test_p3_later_support_change_after_the_shown_pin_is_not_read() -> None:
    assert refresh_chain([ORIGIN, rev(2), rev(3, "SUPPORT_CHANGED")], "r1", "r2") is True


# --------------------------------------------------------------- negatives
def test_n1_support_changed_breaks() -> None:
    assert refresh_chain([ORIGIN, rev(2, "SUPPORT_CHANGED")], "r1", "r2") is False


def test_n2_changed_lifecycle_breaks() -> None:
    assert refresh_chain([ORIGIN, rev(2, lifecycle="UNCONFIRMED")], "r1", "r2") is False


def test_n3_changed_episode_end_breaks() -> None:
    assert refresh_chain([ORIGIN, rev(2, end="2026-10-06T15:25:00Z")], "r1", "r2") is False


def test_n4_changed_episode_start_breaks() -> None:
    assert refresh_chain([ORIGIN, rev(2, start="2026-10-06T14:15:00Z")], "r1", "r2") is False


def test_n5_no_longer_supported_after_a_refresh_breaks() -> None:
    assert refresh_chain([ORIGIN, rev(2), rev(3, "NO_LONGER_SUPPORTED")], "r1", "r3") is False


def test_n5b_every_other_transition_breaks() -> None:
    for tr in ("REOPENED", "SPLIT", "MERGED_INTO", "MODEL_REEVALUATED", "SOMETHING_NEW"):
        assert refresh_chain([ORIGIN, rev(2, tr)], "r1", "r2") is False, tr


def test_n7_origin_absent_breaks() -> None:
    assert refresh_chain([rev(2), rev(3)], "r1", "r3") is False
    assert refresh_chain([ORIGIN, rev(2)], "r1", "r9") is False


def test_n8_origin_equal_to_shown_is_the_exact_rule_not_a_chain() -> None:
    assert refresh_chain([ORIGIN, rev(2)], "r2", "r2") is False


def test_n9_origin_after_shown_never_links() -> None:
    assert refresh_chain([ORIGIN, rev(2), rev(3)], "r3", "r2") is False


def test_n10_revision_gap_breaks() -> None:
    assert refresh_chain([ORIGIN, rev(3)], "r1", "r3") is False


def test_n11_no_history_breaks() -> None:
    assert refresh_chain(None, "r1", "r2") is False
    assert refresh_chain([], "r1", "r2") is False


# --------------------------------------------------------------- the board join
def _settled() -> dict[str, bool]:
    return {o.key: True for o in SITE_OUTCOMES if o.domain == MINI}


F = FindingFact("f", "r2", "Generator support review", "GENERATOR_SUPPORT_CANDIDATE", "SUPPORTED",
                "/sites/KOBO-001/findings/f", refreshed_from=("r1",))
ACT = ActionFact(action_id="a1", code="ACT-000001", title="", origin_finding_id="f", origin_revision_id="r1",
                 applied=True, open=True, verification_state="PENDING", href="/sites/KOBO-001/actions/a1",
                 workflow_label="Applied", verification_href="/sites/KOBO-001/actions/a1/verification?event_id=e1")
SAFEGUARDS = ("Reliable service and battery and generator life are checked as safeguards when ACT-000001 is "
              "verified; a gain that harms them does not count")


def board(finding: FindingFact = F, action: ActionFact = ACT) -> dict[str, dict]:
    facts = SiteFacts(domain=MINI, site_code="KOBO-001", findings=(finding,), actions=(action,),
                      signals_extra=(SignalFact("SIGNAL:EVIDENCE_GAP", True, "Gap"),), readiness="LIMITED",
                      settled=_settled())
    return {r["category"]: r for r in assemble(facts)}


def _finding_reasons(row: dict) -> set[str]:
    return {o["reason"] for o in row["outcomes"]} & {"PRIMARY_FINDING_APPLIED", "PRIMARY_FINDING_OPEN"}


def test_b1_refreshed_chain_links_applied_and_must_not_harm() -> None:
    cost = board()[COST]
    assert cost["must_not_harm"] == {"text": SAFEGUARDS, "href": ACT.verification_href}
    assert _finding_reasons(cost) == {"PRIMARY_FINDING_APPLIED"}


def test_b2_without_a_proved_chain_today_s_exact_rule_holds() -> None:
    cost = board(replace(F, refreshed_from=()))[COST]
    assert cost["must_not_harm"] is None
    assert _finding_reasons(cost) == {"PRIMARY_FINDING_OPEN"}


def test_n6_domain_action_never_links() -> None:
    cost = board(action=replace(ACT, is_domain=True))[COST]
    assert cost["must_not_harm"] is None
    assert _finding_reasons(cost) == {"PRIMARY_FINDING_OPEN"}


def test_b3_earlier_lists_unchanged_by_the_link() -> None:
    linked, exact = board(), board(replace(F, refreshed_from=()))
    keys = ("earlier", "earlier_empty_text")
    assert [{k: linked[c].get(k) for k in keys} for c in CATEGORIES] == \
        [{k: exact[c].get(k) for k in keys} for c in CATEGORIES]
