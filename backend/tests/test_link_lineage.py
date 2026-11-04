"""CH-5a1 §A4/§A5: the board's Finding->Action link is the thread join (CH-2/CH-3). The refresh-chain lineage
(LINK-LINEAGE, D-2026-10-31-board-action-refresh-lineage) is deleted with `refresh_chain`; these cases replace its
tests (E-change: deleted lineage). An Action belongs to a Finding through the same thread id and segment; without a
thread the exact origin revision is kept. No database."""
from __future__ import annotations

from assetops_backend.chain import refs as R

from dataclasses import replace

from assetops_backend.outcomes.catalogue import CATEGORIES, MINI, SITE_OUTCOMES
from assetops_backend.site_outcomes import board as board_module
from assetops_backend.site_outcomes.board import ActionFact, FindingFact, SignalFact, SiteFacts, assemble

GROW, COST, PROTECT, ASSURE = CATEGORIES


def _settled() -> dict[str, bool]:
    return {o.key: True for o in SITE_OUTCOMES if o.domain == MINI}


THREAD = {"id": "t1", "occurrence_no": 1, "occurrences": 1, "segment_no": 1, "state": "APPLIED",
          "applied": True, "verified": False}
F = FindingFact("f", "r2", "Generator support review", "GENERATOR_SUPPORT_CANDIDATE", "SUPPORTED",
                R.finding_ref("KOBO-001", "f"), thread=THREAD)
#: Raised on an earlier revision r1 of the shown Finding revision r2: linked only through the thread.
ACT = ActionFact(action_id="a1", code="ACT-000001", title="", origin_finding_id="f", origin_revision_id="r1",
                 applied=True, open=True, verification_state="PENDING", link_ref=R.action_ref("KOBO-001", "a1"),
                 workflow_label="Applied", verification_ref=R.action_ref("KOBO-001", "a1", view="verification", event_id="e1"),
                 thread_id="t1", segment_no=1)
SAFEGUARDS = ("Reliable service and battery and generator life are checked as safeguards when ACT-001 is "
              "verified; a gain that harms them does not count")


def board(finding: FindingFact = F, action: ActionFact = ACT) -> dict[str, dict]:
    facts = SiteFacts(domain=MINI, site_code="KOBO-001", findings=(finding,), actions=(action,),
                      signals_extra=(SignalFact("SIGNAL:EVIDENCE_GAP", True, "Gap"),), readiness="LIMITED",
                      settled=_settled())
    return {r["category"]: r for r in assemble(facts)}


def _finding_reasons(row: dict) -> set[str]:
    return {o["reason"] for o in row["outcomes"]} & {"PRIMARY_FINDING_APPLIED", "PRIMARY_FINDING_OPEN"}


def test_lineage_symbols_are_deleted() -> None:
    for name in ("refresh_chain", "BASIS_REFRESHED"):
        assert not hasattr(board_module, name), name
    assert "refreshed_from" not in FindingFact.__dataclass_fields__


def test_t1_same_thread_and_segment_links_across_revisions() -> None:
    cost = board()[COST]
    assert cost["must_not_harm"] == {"text": SAFEGUARDS, "href": R.href_for(ACT.verification_ref), "link_ref": ACT.verification_ref}
    assert _finding_reasons(cost) == {"PRIMARY_FINDING_APPLIED"}


def test_t2_other_segment_never_links() -> None:
    cost = board(action=replace(ACT, segment_no=2))[COST]
    assert cost["must_not_harm"] is None


def test_t3_other_thread_never_links_even_on_the_exact_revision() -> None:
    cost = board(action=replace(ACT, thread_id="t2", origin_revision_id="r2"))[COST]
    assert cost["must_not_harm"] is None


def test_t4_unthreaded_action_never_links_to_a_threaded_finding() -> None:
    cost = board(action=replace(ACT, thread_id=None, segment_no=None, origin_revision_id="r2"))[COST]
    assert cost["must_not_harm"] is None


def test_t5_no_thread_keeps_the_exact_revision_rule() -> None:
    unthreaded = replace(F, thread=None)
    exact = board(unthreaded, replace(ACT, thread_id=None, segment_no=None, origin_revision_id="r2"))[COST]
    assert exact["must_not_harm"] == {"text": SAFEGUARDS, "href": R.href_for(ACT.verification_ref), "link_ref": ACT.verification_ref}
    assert _finding_reasons(exact) == {"PRIMARY_FINDING_APPLIED"}
    earlier = board(unthreaded, replace(ACT, thread_id=None, segment_no=None))[COST]  # r1 != r2: no link
    assert earlier["must_not_harm"] is None
    assert _finding_reasons(earlier) == {"PRIMARY_FINDING_OPEN"}


def test_n6_domain_action_never_links() -> None:
    cost = board(action=replace(ACT, is_domain=True))[COST]
    assert cost["must_not_harm"] is None


def test_b3_earlier_lists_unchanged_by_the_link() -> None:
    linked, unlinked = board(), board(action=replace(ACT, segment_no=2))
    keys = ("earlier", "earlier_empty_text")
    assert [{k: linked[c].get(k) for k in keys} for c in CATEGORIES] == \
        [{k: unlinked[c].get(k) for k in keys} for c in CATEGORIES]
