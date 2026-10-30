"""OUT-B1: pure board assembly (build spec §B.1/§B.2; rulings B-Q14/Q18/Q19/Q20/Q28, addendum 1)."""
from __future__ import annotations

import ast
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from assetops_backend.outcomes.catalogue import CATEGORIES, COLD, EV, MINI, SITE_OUTCOMES
from assetops_backend.site_outcomes import board as board_module
from assetops_backend.site_outcomes.board import (
    EARLIER_EMPTY_NONE, EARLIER_EMPTY_OPEN, ActionFact, CaseFact, Contributor, FindingFact, Option, PlanFact,
    SignalFact, SiteFacts, assemble, join_names, readiness_confidence)

GROW, COST, PROTECT, ASSURE = CATEGORIES


def t(day: int) -> datetime:
    return datetime(2026, 10, day, 12, tzinfo=timezone.utc)


def settled(domain: str, value: bool = True, **overrides: bool) -> dict[str, bool]:
    out = {o.key: value for o in SITE_OUTCOMES if o.domain == domain}
    out.update({k.replace("_", "-"): v for k, v in overrides.items()})
    return out


def rows_by_cat(facts: SiteFacts) -> dict[str, dict]:
    rows = assemble(facts)
    assert [r["category"] for r in rows] == list(CATEGORIES)
    return {r["category"]: r for r in rows}


F104 = FindingFact("f104", "f104r", "Generator support review", "GENERATOR_SUPPORT_CANDIDATE", "SUPPORTED",
                   "/sites/KOBO-001/findings/f104", confidence_label="Limited")
HEADROOM = SignalFact("SIGNAL:PRODUCTIVE_USE_HEADROOM", "OPPORTUNITY", True, "Productive-use headroom",
                      "/sites/KOBO-001/performance/renewable")
GAP = SignalFact("SIGNAL:EVIDENCE_GAP", "EVIDENCE_GAP", True, "Battery output not reported limits this conclusion")


def act048(**kw) -> ActionFact:
    base = dict(action_id="a48", code="ACT-048", title="Trial a lower generator stop setting",
                origin_finding_id="f104", origin_revision_id="f104r", applied=False, open=True,
                verification_state="PENDING", href="/sites/KOBO-001/actions/a48",
                workflow_label="Recommendation not accepted",
                verification_href="/sites/KOBO-001/actions/a48/verification?event_id=e1")
    base.update(kw)
    return ActionFact(**base)


def kobo(**kw) -> SiteFacts:
    base = dict(domain=MINI, site_code="KOBO-001", findings=(F104,), actions=(act048(),),
                signals_extra=(GAP, HEADROOM), readiness="LIMITED", settled=settled(MINI))
    base.update(kw)
    return SiteFacts(**base)


# --------------------------------------------------------------- states, issues, order

def test_kobo_mock_grid_and_issue_order() -> None:
    rows = rows_by_cat(kobo())
    assert [rows[c]["state"] for c in CATEGORIES] == ["OPPORTUNITY", "NEEDS_ATTENTION", "NO_OBJECTIVE", "WATCH"]
    assert rows[COST]["lead_outcome"] == {"key": "MG-2", "label": "Supply cost per kWh"}
    assert [(i["kind"], i["role"], i["text"]) for i in rows[COST]["issues"]] == [
        ("FINDING", "MOVES", "Generator support review"),
        ("EVIDENCE_GAP", "CHECKED", "Battery output not reported limits this conclusion"),
        ("OPPORTUNITY", "CHECKED", "Productive-use headroom")]
    # signals never get the safeguard suffix; CHECKED Findings come last (B-Q20)
    assert [(i["kind"], i["role"], i["text"]) for i in rows[PROTECT]["issues"]] == [
        ("OPPORTUNITY", "CHECKED", "Productive-use headroom"),
        ("FINDING", "CHECKED", "Generator support review · checked here as a safeguard")]
    assert rows[PROTECT]["issues"][1]["ref"] == {"finding_id": "f104", "finding_revision_id": "f104r"}
    assert [i["kind"] for i in rows[ASSURE]["issues"]] == ["EVIDENCE_GAP"]
    assert [i["role"] for i in rows[GROW]["issues"]] == ["MOVES"]
    for r in rows.values():
        assert r["counts"] == {"issues": len(r["issues"]), "in_hand": len(r["in_hand"])}


def test_moves_findings_ordered_by_title() -> None:
    other = replace(F104, finding_id="f2", revision_id="f2r", title="Another generator review")
    issues = rows_by_cat(kobo(findings=(F104, other), actions=()))[COST]["issues"]
    assert [i["text"] for i in issues if i["kind"] == "FINDING"] == ["Another generator review",
                                                                      "Generator support review"]


def test_closed_signal_and_closed_finding_are_not_issues() -> None:
    closed = replace(F104, lifecycle="RETIRED")
    rows = rows_by_cat(kobo(findings=(closed,), actions=(), signals_extra=(replace(GAP, open=False),)))
    assert rows[COST]["issues"] == [] and rows[COST]["state"] == "NO_OBJECTIVE"
    assert rows[ASSURE]["issues"] == []
    assert rows[COST]["earlier_empty_text"] == EARLIER_EMPTY_NONE


def test_unsettled_outcome_is_unknown_and_signals_still_listed() -> None:
    rows = rows_by_cat(kobo(settled=settled(MINI, MG_2=False)))
    assert rows[COST]["state"] == "UNKNOWN" and rows[COST]["outcomes"][0]["reason"] == "PRODUCER_NOT_SETTLED"
    assert rows[GROW]["state"] == "OPPORTUNITY"


def test_absent_settled_key_reads_unknown() -> None:
    assert rows_by_cat(kobo(settled={}))[COST]["state"] == "UNKNOWN"


# --------------------------------------------------------------- in hand / earlier (B-Q18)

def test_pre_applied_action_is_in_hand_only_with_plan_ready() -> None:
    rows = rows_by_cat(kobo())
    assert rows[COST]["in_hand"] == [{"text": "ACT-048 · Trial a lower generator stop setting",
                                      "href": "/sites/KOBO-001/actions/a48", "state_label": "Plan ready"}]
    assert rows[COST]["earlier"] == [] and rows[COST]["earlier_empty_text"] == EARLIER_EMPTY_OPEN
    assert rows[PROTECT]["earlier"] == [] and rows[PROTECT]["earlier_empty_text"] == EARLIER_EMPTY_NONE
    assert rows[PROTECT]["in_hand"] == []


def test_applied_action_moves_to_earlier_with_checked_entry() -> None:
    rows = rows_by_cat(kobo(actions=(act048(applied=True, workflow_label="Outcome pending"),)))
    assert rows[COST]["state"] == "WATCH"  # D4 (R542)
    assert rows[COST]["in_hand"] == []
    assert rows[COST]["earlier"] == [{"text": "ACT-048 · Trial a lower generator stop setting",
                                      "href": "/sites/KOBO-001/actions/a48", "result_label": "Pending"}]
    assert rows[COST]["earlier_empty_text"] is None
    assert rows[PROTECT]["earlier"] == [{
        "text": "Reliable service and battery and generator life checked as safeguards in "
                "Trial a lower generator stop setting",
        "href": "/sites/KOBO-001/actions/a48/verification?event_id=e1", "result_label": "Pending"}]


def test_earlier_result_labels_for_mini_action() -> None:
    expected = {"VERIFIED": "Verified on test data", "INEFFECTIVE": "Did not fix it",
                "INCONCLUSIVE": "Not determined", "REASSESSMENT_PENDING": "Pending"}
    for state, label in expected.items():
        rows = rows_by_cat(kobo(actions=(act048(applied=True, open=False, verification_state=state),)))
        assert [e["result_label"] for e in rows[COST]["earlier"]] == [label], state


def test_applied_action_without_plan_is_not_earlier_and_stays_in_hand_if_open() -> None:
    rows = rows_by_cat(kobo(actions=(act048(applied=True, verification_state="NO_PLAN", workflow_label="Applied"),)))
    assert rows[COST]["earlier"] == [] and rows[PROTECT]["earlier"] == []
    assert [i["state_label"] for i in rows[COST]["in_hand"]] == ["Applied"]
    closed = rows_by_cat(kobo(actions=(act048(applied=True, open=False, verification_state="NO_PLAN"),)))
    assert closed[COST]["in_hand"] == [] and closed[COST]["earlier"] == []


def test_awaiting_verification_label_rename() -> None:
    rows = rows_by_cat(kobo(actions=(act048(verification_state=None, workflow_label="Outcome pending"),)))
    assert rows[COST]["in_hand"][0]["state_label"] == "Awaiting verification"


# --------------------------------------------------------------- must not harm (B-Q19, addendum 1)

def test_must_not_harm_present_with_verification_and_absent_without() -> None:
    rows = rows_by_cat(kobo())
    assert rows[COST]["must_not_harm"] == {
        "text": "Reliable service and battery and generator life are checked as safeguards in "
                "Trial a lower generator stop setting; a gain that harms them does not count",
        "href": "/sites/KOBO-001/actions/a48/verification?event_id=e1"}
    assert rows[PROTECT]["must_not_harm"] is None
    assert rows_by_cat(kobo(actions=(act048(verification_state="NO_PLAN"),)))[COST]["must_not_harm"] is None
    assert rows_by_cat(kobo(actions=()))[COST]["must_not_harm"] is None
    wrong_rev = act048(origin_revision_id="older")
    assert rows_by_cat(kobo(actions=(wrong_rev,)))[COST]["must_not_harm"] is None


def test_join_names() -> None:
    assert join_names(["Reliable service"]) == "Reliable service"
    assert join_names(["reliable service", "Battery life"]) == "Reliable service and battery life"
    assert join_names(["A", "B", "C"]) == "A, b and c"


# --------------------------------------------------------------- cold: cases, plans, not measured

F118 = FindingFact("f118", "f118r", "Backup did not start", "COLD_START_FAILURE", "SUPPORTED", "/sites/C/f118",
                   asset_id="gen")
F119 = FindingFact("f119", "f119r", "Chamber above limit", "COLD_EXCURSION", "UNCONFIRMED", "/sites/C/f119")
COLD_ACTION = ActionFact("da1", "DA-1", "Witnessed automatic-start test", "f118", "f118r", False, True, None,
                         "/sites/C/actions/da1", is_domain=True)


def request(cid: str, state: str, day: int, *, asset: str | None = "gen", findings=("f118",)) -> CaseFact:
    return CaseFact(cid, cid.upper(), "MAINTENANCE_REQUEST", f"Inspect {cid}", state, asset, "GEN-1 · generator",
                    tuple(findings), t(day), f"/maintenance/requests/{cid}")


def cold(**kw) -> SiteFacts:
    base = dict(domain=COLD, site_code="COLD-LAB-001", findings=(F118, F119), actions=(COLD_ACTION,),
                cases=(request("mr1", "COMPLETED", 5),), readiness="LIMITED", settled=settled(COLD))
    base.update(kw)
    return SiteFacts(**base)


def test_cold_grid_and_not_measured_rows() -> None:
    rows = rows_by_cat(cold())
    assert [rows[c]["state"] for c in CATEGORIES] == ["NOT_MEASURED", "NOT_MEASURED", "NEEDS_ATTENTION", "WATCH"]
    grow = rows[GROW]
    assert grow["not_measured_text"] == "Needs occupancy, storage contract, income and sales records"
    assert grow["evidence_link"] is None and grow["headline"] is None
    assert grow["earlier"] == [] and grow["earlier_empty_text"] is None and grow["must_not_harm"] is None
    for key in ("contributors", "issues", "options", "in_hand"):
        assert grow[key] == [] and rows[COST][key] == []
    assert rows[COST]["evidence_link"] == {"label": "Financial bridge", "href": "/sites/COLD-LAB-001/financials"}
    assert rows[COST]["not_measured_text"] == "Cost per cooling unit needs cooling energy and repair cost records"


def test_cold_protect_lists_domain_action_in_hand_and_completed_request_not_yet_verified() -> None:
    p = rows_by_cat(cold())[PROTECT]
    assert p["must_not_harm"] is None  # domain Actions carry no verification
    assert [i["text"] for i in p["issues"]] == ["Backup did not start", "Chamber above limit"]
    assert p["in_hand"] == [{"text": "DA-1 · Witnessed automatic-start test", "href": "/sites/C/actions/da1",
                             "state_label": "Open"}]
    assert p["earlier"] == [{"text": "MR1 · Inspect mr1", "href": "/maintenance/requests/mr1",
                             "result_label": "Not yet verified"}]


def test_later_request_on_same_asset_marks_earlier_did_not_fix_it() -> None:
    later = request("mr2", "OPEN", 9, findings=())
    p = rows_by_cat(cold(cases=(request("mr1", "COMPLETED", 5), later)))[PROTECT]
    assert [e["result_label"] for e in p["earlier"]] == ["Did not fix it"]
    assert {"text": "MR2 · Inspect mr2", "href": "/maintenance/requests/mr2",
            "state_label": "Open · not linked to a finding"} in p["in_hand"]
    # an earlier request on the same asset does not change the result
    p2 = rows_by_cat(cold(cases=(request("mr1", "COMPLETED", 5), request("mr0", "COMPLETED", 2))))[PROTECT]
    assert [(e["text"], e["result_label"]) for e in p2["earlier"]] == [
        ("MR0 · Inspect mr0", "Did not fix it"), ("MR1 · Inspect mr1", "Not yet verified")]
    # sharing a Finding id counts even on another asset
    p3 = rows_by_cat(cold(cases=(request("mr1", "COMPLETED", 5), request("mr3", "OPEN", 8, asset="x"))))[PROTECT]
    assert p3["earlier"][0]["result_label"] == "Did not fix it"


def test_incidents_and_closed_cases() -> None:
    inc = CaseFact("i1", "INC-1", "INCIDENT", "Power cut", "CLOSED", None, None, (), t(3), "/sites/C/work/incidents")
    inc_open = replace(inc, case_id="i2", code="INC-2", state="IN_PROGRESS")
    p = rows_by_cat(cold(cases=(inc, inc_open)))[PROTECT]
    assert p["earlier"] == [] and p["earlier_empty_text"] == EARLIER_EMPTY_OPEN
    assert p["in_hand"][-1] == {"text": "INC-2 · Power cut", "href": "/sites/C/work/incidents",
                                "state_label": "In progress · not linked to a finding"}


def test_plans_in_hand_on_protect_only() -> None:
    plans = (PlanFact("p1", "PM-1", "Generator service", "RUN_HOURS", None, 500, "DRAFT", "gen", "/maintenance/preventive"),
             PlanFact("p2", "PM-2", "Compressor check", "CALENDAR", date(2026, 11, 3), None, "ACTIVE", None, None),
             PlanFact("p3", "PM-3", "Retired", "CALENDAR", date(2026, 11, 3), None, "RETIRED", None, None))
    rows = rows_by_cat(cold(plans=plans, actions=(), cases=()))
    assert [(i["text"], i["state_label"]) for i in rows[PROTECT]["in_hand"]] == [
        ("PM-1 · Generator service", "Due at 500 operating hours"), ("PM-2 · Compressor check", "Due 3 Nov")]
    assert rows[ASSURE]["in_hand"] == []


# --------------------------------------------------------------- EV: headline, money, contributors, links

F130 = FindingFact("f130", "f130r", "Charging interrupted", "EV_INTERRUPTION", "SUPPORTED", "/sites/EV/f130")


def test_ev_grid_headline_fallback_money_passthrough_and_contributors() -> None:
    money = {"amount_low": "12.40", "amount_high": "12.40", "currency": "USD"}
    contributor = Contributor("charging", "Charging delivered", "40 kWh in 3 complete sessions",
                              readiness_confidence("FULL"), "/sites/EV-LAB-001/ev/sessions")
    facts = SiteFacts(EV, "EV-LAB-001", findings=(F130,), readiness="NONE", settled=settled(EV),
                      contributors={GROW: (contributor,)}, options={GROW: (Option("Charging what-ifs", "/x"),)},
                      headline={GROW: "gross tariff estimate"}, headline_money={GROW: money},
                      subline={PROTECT: "Charger condition is not assessed"})
    rows = rows_by_cat(facts)
    assert [rows[c]["state"] for c in CATEGORIES] == ["WATCH", "NOT_MEASURED", "NEEDS_ATTENTION", "WATCH"]
    assert rows[GROW]["headline"] == "gross tariff estimate" and rows[GROW]["headline_money"] == money
    assert rows[PROTECT]["headline"] == "Charging interrupted"  # lead Finding fallback
    assert rows[PROTECT]["headline_money"] is None and rows[PROTECT]["subline"] == "Charger condition is not assessed"
    assert rows[ASSURE]["headline"] is None  # readiness-driven, not Finding-driven
    assert rows[GROW]["contributors"] == [{"key": "charging", "label": "Charging delivered",
                                           "text": "40 kWh in 3 complete sessions",
                                           "confidence": {"label": "High", "tone": "green"},
                                           "href": "/sites/EV-LAB-001/ev/sessions"}]
    assert rows[GROW]["options"] == [{"text": "Charging what-ifs", "href": "/x"}]
    assert rows[GROW]["evidence_link"]["href"] == "/sites/EV-LAB-001/ev/financials"
    assert rows[COST]["evidence_link"] is None
    assert rows[COST]["not_measured_text"].startswith("Energy cost per km needs odometer readings")


def test_secondary_headline_fallback_uses_finding_moving_lead() -> None:
    rows = rows_by_cat(SiteFacts(EV, "EV-LAB-001", findings=(F130,), settled=settled(EV)))
    assert rows[GROW]["headline"] == "Charging interrupted"
    assert rows[GROW]["outcomes"][0]["reason"] == "SECONDARY_FINDING_OPEN"


def test_mini_evidence_links() -> None:
    rows = rows_by_cat(kobo())
    assert {c: r["evidence_link"]["href"] for c, r in rows.items()} == {
        GROW: "/sites/KOBO-001/performance/renewable", COST: "/sites/KOBO-001/performance/dispatch",
        PROTECT: "/sites/KOBO-001/health", ASSURE: "/sites/KOBO-001/evidence"}


def test_readiness_confidence_chips() -> None:
    assert readiness_confidence("FULL") == {"label": "High", "tone": "green"}
    assert readiness_confidence("LIMITED") == {"label": "Limited", "tone": "amber"}
    assert readiness_confidence("NONE") == {"label": "Low", "tone": "amber"}
    assert readiness_confidence(None) == {"label": "Unknown", "tone": "gray"}


def test_mini_protect_unmeasured_outcome_never_sets_state() -> None:
    rows = rows_by_cat(kobo())
    assert [o["state"] for o in rows[PROTECT]["outcomes"]] == ["NO_OBJECTIVE", "NOT_MEASURED"]


# --------------------------------------------------------------- purity

def test_board_imports_only_outcomes_and_stdlib() -> None:
    allowed = {"__future__", "dataclasses", "typing", "collections.abc"}
    tree = ast.parse(Path(board_module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module in allowed or node.module.startswith("assetops_backend.outcomes"), node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name in allowed, alias.name
