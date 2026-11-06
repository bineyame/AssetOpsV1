"""OUT-B1: pure board assembly (build spec §B.1/§B.2; rulings B-Q14/Q18/Q19/Q20/Q28, addendum 1)."""
from __future__ import annotations

from assetops_backend.chain import refs as R
from link_parity import checked

import ast

import pytest
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from assetops_backend.outcomes.catalogue import CATEGORIES, COLD, EV, MINI, SITE_OUTCOMES
from assetops_backend.site_outcomes import board as board_module
from assetops_backend.site_outcomes.board import (
    EARLIER_EMPTY_NONE, EARLIER_EMPTY_OPEN, ActionFact, CaseFact, Contributor, FindingFact, Option, PlanFact,
    SignalFact, SiteFacts, assemble, join_names, readiness_confidence)

GROW, COST, PROTECT, ASSURE = CATEGORIES


def legacy(items):
    """The pre-Addendum-12 item fields: case/plan items also carry `kind`/`occurred_at` (pinned in test_out_b1_board)."""
    return [{k: v for k, v in i.items() if k not in ("kind", "occurred_at", "link_ref")} for i in items]


def t(day: int) -> datetime:
    return datetime(2026, 10, day, 12, tzinfo=timezone.utc)


def settled(domain: str, value: bool = True, **overrides: bool) -> dict[str, bool]:
    out = {o.key: value for o in SITE_OUTCOMES if o.domain == domain}
    out.update({k.replace("_", "-"): v for k, v in overrides.items()})
    return out


def rows_by_cat(facts: SiteFacts) -> dict[str, dict]:
    rows = checked(assemble(facts))  # CH-5a2a: link parity, then the legacy shape
    assert [r["category"] for r in rows] == list(CATEGORIES)
    return {r["category"]: r for r in rows}


F104 = FindingFact("f104", "f104r", "Generator support review", "GENERATOR_SUPPORT_CANDIDATE", "SUPPORTED",
                   R.finding_ref("KOBO-001", "f104"), confidence_label="Limited")
HEADROOM = SignalFact("SIGNAL:PRODUCTIVE_USE_HEADROOM", True, "Productive-use headroom",
                      R.evidence_ref("KOBO-001", "renewable"))
GAP = SignalFact("SIGNAL:EVIDENCE_GAP", True, "Battery output not reported limits this conclusion")


def act048(**kw) -> ActionFact:
    base = dict(action_id="a48", code="ACT-048", title="",  # no stored Action title (addendum 2 item 1)
                origin_finding_id="f104", origin_revision_id="f104r", applied=False, open=True,
                verification_state="PENDING", link_ref=R.action_ref("KOBO-001", "a48"),
                workflow_label="No action agreed yet",
                verification_ref=R.action_ref("KOBO-001", "a48", view="verification", event_id="e1"),
                source_class="REGISTERED_SIMULATION")  # CH-5a2b B7: the stored source of the demo outcome
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
    assert rows[PROTECT]["issues"][1]["ref"] == {"finding_id": "f104", "finding_revision_id": "f104r",
                                                "thread": None}  # CH-2 §5.3: additive, null unthreaded
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
    assert rows[COST]["in_hand"] == [{"text": "ACT-048",
                                      "href": "/sites/KOBO-001/actions/a48", "state_label": "Plan ready"}]
    assert rows[COST]["earlier"] == [] and rows[COST]["earlier_empty_text"] == EARLIER_EMPTY_OPEN
    assert rows[PROTECT]["earlier"] == [] and rows[PROTECT]["earlier_empty_text"] == EARLIER_EMPTY_NONE
    assert rows[PROTECT]["in_hand"] == []


def test_applied_action_moves_to_earlier_with_checked_entry() -> None:
    rows = rows_by_cat(kobo(actions=(act048(applied=True, workflow_label="Outcome pending"),)))
    assert rows[COST]["state"] == "WATCH"  # D4 (R542)
    assert rows[COST]["in_hand"] == []
    assert rows[COST]["earlier"] == [{"text": "ACT-048",
                                      "href": "/sites/KOBO-001/actions/a48", "result_label": "Pending",
                                      "detail": None}]
    assert rows[COST]["earlier_empty_text"] is None
    assert rows[PROTECT]["earlier"] == [{
        "text": "Reliable service and battery and generator life checked as safeguards in ACT-048",
        "href": "/sites/KOBO-001/actions/a48/verification?event_id=e1", "result_label": "Pending",
        "detail": None}]


def test_earlier_result_labels_for_mini_action() -> None:
    expected = {"VERIFIED": "Verified on example data", "INEFFECTIVE": "Did not fix it",
                "INCONCLUSIVE": "Not determined", "REASSESSMENT_PENDING": "Pending"}
    for state, label in expected.items():
        rows = rows_by_cat(kobo(actions=(act048(applied=True, open=False, verification_state=state),)))
        assert [e["result_label"] for e in rows[COST]["earlier"]] == [label], state


def test_verified_label_follows_the_stored_source_class() -> None:
    """CH-5a2b B7 (DS-R1): "on example data" only for an example-data source class; a null class is plain."""
    for source, label in (("AUTHORED_DEMONSTRATION", "Verified on example data"), ("MEASURED_FIELD", "Verified"),
                          (None, "Verified")):
        a = act048(applied=True, open=False, verification_state="VERIFIED", source_class=source)
        assert [e["result_label"] for e in rows_by_cat(kobo(actions=(a,)))[COST]["earlier"]] == [label], source


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
        "text": "Reliable service and battery and generator life are checked as safeguards when ACT-048 is "
                "verified; a gain that harms them does not count",
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

F118 = FindingFact("f118", "f118r", "Backup did not start", "COLD_START_FAILURE", "SUPPORTED", R.finding_ref("C", "f118"),
                   asset_id="gen")
F119 = FindingFact("f119", "f119r", "Chamber above limit", "COLD_EXCURSION", "UNCONFIRMED", R.finding_ref("C", "f119"))
COLD_ACTION = ActionFact("da1", "DA-001", "Witnessed automatic-start test", "f118", "f118r", False, True, None,
                         R.action_ref("C", "da1"), is_domain=True)


def request(cid: str, state: str, day: int, *, asset: str | None = "gen", findings=("f118",)) -> CaseFact:
    return CaseFact(cid, cid.upper(), "MAINTENANCE_REQUEST", f"Inspect {cid}", state, asset, "GEN-1 · generator",
                    tuple(findings), t(day), R.case_ref("C", cid))


def cold(**kw) -> SiteFacts:
    base = dict(domain=COLD, site_code="COLD-LAB-001", findings=(F118, F119), actions=(COLD_ACTION,),
                cases=(request("mr1", "COMPLETED", 5),), readiness="LIMITED", settled=settled(COLD))
    base.update(kw)
    return SiteFacts(**base)


def test_cold_grid_and_not_measured_rows() -> None:
    rows = rows_by_cat(cold())
    # C: CC-3 is measured (R541 resolved); with no warning the Cost row has no objective declared
    assert [rows[c]["state"] for c in CATEGORIES] == ["NOT_MEASURED", "NO_OBJECTIVE", "NEEDS_ATTENTION", "WATCH"]
    grow = rows[GROW]
    assert grow["not_measured_text"] == "Needs occupancy, storage contract, income and sales records"
    assert grow["evidence_link"] is None and grow["headline"] is None
    assert grow["earlier"] == [] and grow["earlier_empty_text"] is None and grow["must_not_harm"] is None
    for key in ("contributors", "issues", "options", "in_hand"):
        assert grow[key] == []
    for key in ("contributors", "options", "in_hand"):
        assert rows[COST][key] == []
    # C: the measured Cost row now lists F-118, which checks CC-3, as a safeguard
    assert [(i["role"], i["text"]) for i in rows[COST]["issues"]] == [
        ("CHECKED", "Backup did not start · checked here as a safeguard")]
    assert rows[COST]["evidence_link"] == {"label": "Financial bridge", "href": "/sites/COLD-LAB-001/financials"}
    assert rows[COST]["not_measured_text"] is None and rows[COST]["headline"] is None


def test_cold_protect_lists_domain_action_in_hand_and_completed_request_not_yet_verified() -> None:
    p = rows_by_cat(cold())[PROTECT]
    assert p["must_not_harm"] is None  # domain Actions carry no verification
    assert [i["text"] for i in p["issues"]] == ["Backup did not start", "Chamber above limit"]
    assert legacy(p["in_hand"]) == [{"text": "DA-001 · Witnessed automatic-start test", "href": "/sites/C/actions/da1",
                             "state_label": "Open"}]
    assert legacy(p["earlier"]) == [{"text": "MR1 · Inspect mr1", "href": "/maintenance/requests/mr1",
                             "result_label": "Not yet verified", "detail": None}]


def test_later_request_on_same_asset_marks_earlier_did_not_fix_it() -> None:
    later = request("mr2", "OPEN", 9, findings=())
    p = rows_by_cat(cold(cases=(request("mr1", "COMPLETED", 5), later)))[PROTECT]
    assert [e["result_label"] for e in p["earlier"]] == ["Did not fix it"]
    assert {"text": "MR2 · Inspect mr2", "href": "/maintenance/requests/mr2",
            "state_label": "Open · not linked to a finding"} in legacy(p["in_hand"])
    # an earlier request on the same asset does not change the result
    p2 = rows_by_cat(cold(cases=(request("mr1", "COMPLETED", 5), request("mr0", "COMPLETED", 2))))[PROTECT]
    assert [(e["text"], e["result_label"]) for e in p2["earlier"]] == [
        ("MR0 · Inspect mr0", "Did not fix it"), ("MR1 · Inspect mr1", "Not yet verified")]
    # sharing a Finding id counts even on another asset
    p3 = rows_by_cat(cold(cases=(request("mr1", "COMPLETED", 5), request("mr3", "OPEN", 8, asset="x"))))[PROTECT]
    assert p3["earlier"][0]["result_label"] == "Did not fix it"


def test_incidents_and_closed_cases() -> None:
    inc = CaseFact("i1", "INC-001", "INCIDENT", "Power cut", "CLOSED", None, None, (), t(3), R.site_ref("C", "work_incidents"))
    inc_open = replace(inc, case_id="i2", code="INC-002", state="IN_PROGRESS")
    p = rows_by_cat(cold(cases=(inc, inc_open)))[PROTECT]
    assert p["earlier"] == [] and p["earlier_empty_text"] == EARLIER_EMPTY_OPEN
    assert p["in_hand"][-1] == {"text": "INC-002 · Power cut", "href": "/sites/C/work/incidents",
                                "state_label": "In progress · not linked to a finding",
                                "kind": "INCIDENT", "occurred_at": "2026-10-03T12:00:00Z"}  # POLISH Addendum 12 Q1


def test_case_items_carry_their_stored_kind_and_occurred_at() -> None:
    """POLISH Addendum 12 Q1: in-hand and earlier case items carry the stored `kind` and ISO `occurred_at`; plan items
    carry kind PLAN; the existing fields are unchanged."""
    p = rows_by_cat(cold(cases=(request("mr1", "COMPLETED", 5), request("mr3", "OPEN", 8))))[PROTECT]
    earlier = next(i for i in p["earlier"] if i["href"] == "/maintenance/requests/mr1")
    assert (earlier["kind"], earlier["occurred_at"]) == ("MAINTENANCE_REQUEST", "2026-10-05T12:00:00Z")
    assert set(earlier) == {"text", "href", "result_label", "detail", "kind", "occurred_at"}
    open_item = next(i for i in p["in_hand"] if i["href"] == "/maintenance/requests/mr3")
    assert (open_item["kind"], open_item["occurred_at"]) == ("MAINTENANCE_REQUEST", "2026-10-08T12:00:00Z")
    plan = PlanFact("p1", "PM-001", "Generator service", "RUN_HOURS", None, 500, "DRAFT", "gen", R.estate_ref("maintenance_preventive"))
    item = rows_by_cat(cold(plans=(plan,), actions=(), cases=()))[PROTECT]["in_hand"][0]
    assert item["kind"] == "PLAN" and "occurred_at" not in item
    action = next(i for i in rows_by_cat(cold())[PROTECT]["in_hand"] if i["href"] == "/sites/C/actions/da1")
    assert "kind" not in action and "occurred_at" not in action  # Action items are unchanged


def test_plans_in_hand_on_protect_only() -> None:
    plans = (PlanFact("p1", "PM-001", "Generator service", "RUN_HOURS", None, 500, "DRAFT", "gen", R.estate_ref("maintenance_preventive")),
             PlanFact("p2", "PM-002", "Compressor check", "CALENDAR", date(2026, 11, 3), None, "ACTIVE", None, None),
             PlanFact("p3", "PM-003", "Retired", "CALENDAR", date(2026, 11, 3), None, "RETIRED", None, None))
    rows = rows_by_cat(cold(plans=plans, actions=(), cases=()))
    assert [(i["text"], i["state_label"]) for i in rows[PROTECT]["in_hand"]] == [
        ("PM-001 · Generator service", "Due at 500 operating hours"), ("PM-002 · Compressor check", "Due 3 Nov")]
    assert rows[ASSURE]["in_hand"] == []


# --------------------------------------------------------------- EV: headline, money, contributors, links

F130 = FindingFact("f130", "f130r", "Charging interrupted", "EV_INTERRUPTION", "SUPPORTED", R.finding_ref("EV", "f130"))


def test_ev_grid_headline_fallback_money_passthrough_and_contributors() -> None:
    money = {"amount_low": "12.40", "amount_high": "12.40", "currency": "USD"}
    contributor = Contributor("charging", "Charging delivered", "40 kWh in 3 complete sessions",
                              readiness_confidence("FULL"), R.evidence_ref("EV-LAB-001", "sessions"))
    facts = SiteFacts(EV, "EV-LAB-001", findings=(F130,), readiness="NONE", settled=settled(EV),
                      contributors={GROW: (contributor,)}, options={GROW: (Option("Charging what-ifs", R.site_ref("EV-LAB-001", "ev_scenarios")),)},
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
                                           "href": "/sites/EV-LAB-001/performance/sessions"}]
    assert rows[GROW]["options"] == [{"text": "Charging what-ifs", "href": "/sites/EV-LAB-001/ev/financials/scenarios"}]
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


def test_mini_protect_battery_outcome_measured_without_warning() -> None:
    rows = rows_by_cat(kobo())  # C: MG-4 is measured (R541 resolved); no warning, so no objective declared
    assert [(o["key"], o["state"]) for o in rows[PROTECT]["outcomes"]] == [
        ("MG-5", "NO_OBJECTIVE"), ("MG-4", "NO_OBJECTIVE")]


# --------------------------------------------------------------- purity

def test_board_imports_only_outcomes_and_stdlib() -> None:
    allowed = {"__future__", "dataclasses", "typing", "collections.abc"}
    tree = ast.parse(Path(board_module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # CH-5a2a: the one link builder `chain.refs` (stdlib-only, pinned below); CH-5a2b B7: the one wording
            # helper `chain.vocabulary.provenance_suffix`. These are the only non-outcomes imports.
            assert (node.module in allowed or node.module.startswith("assetops_backend.outcomes")
                    or (node.module == "assetops_backend.chain" and [a.name for a in node.names] == ["refs"])
                    or (node.module == "assetops_backend.chain.vocabulary"
                        # CH-6a3: plus the two node wording helpers the Grow parts read
                        and sorted(a.name for a in node.names) == ["days_line", "node_text", "provenance_suffix"])), node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name in allowed, alias.name


# --------------------------------------------------------------- unresolved links (addendum 2 item 4, replaces M1)

def test_unresolved_linked_finding_is_kept_under_protect_with_suffix() -> None:
    orphan_case = request("mr9", "OPEN", 6, findings=("missing",))
    facts = cold(cases=(orphan_case,))
    rows = rows_by_cat(facts)
    assert {"text": "MR9 · Inspect mr9", "href": "/maintenance/requests/mr9",
            "state_label": "Open · linked finding outside this view"} in legacy(rows[PROTECT]["in_hand"])
    assert board_module.unresolved_links(facts) == (("mr9", "missing"),)
    done = request("mr8", "COMPLETED", 2, findings=("missing",))
    rows = rows_by_cat(cold(cases=(done,)))
    assert [e["result_label"] for e in rows[PROTECT]["earlier"]] == ["Not yet verified · linked finding outside this view"]

    orphan_action = replace(COLD_ACTION, origin_finding_id="missing")
    facts = cold(actions=(orphan_action,), cases=())
    rows = rows_by_cat(facts)
    assert [i["state_label"] for i in rows[PROTECT]["in_hand"]] == ["Open · linked finding outside this view"]
    assert board_module.unresolved_links(facts) == (("da1", "missing"),)
    mini = kobo(findings=(), actions=(act048(origin_finding_id="gone"),), signals_extra=())
    rows = rows_by_cat(mini)
    assert rows[PROTECT]["in_hand"] == [{"text": "ACT-048", "href": "/sites/KOBO-001/actions/a48",
                                         "state_label": "Plan ready · linked finding outside this view"}]
    assert rows[COST]["in_hand"] == [] and rows[COST]["must_not_harm"] is None


def test_out_of_window_finding_places_work_but_drives_no_signal_or_issue() -> None:
    outside = replace(F104, in_window=False)
    rows = rows_by_cat(kobo(findings=(outside,), signals_extra=()))
    assert rows[COST]["issues"] == [] and rows[PROTECT]["issues"] == []
    assert rows[COST]["state"] != "NEEDS_ATTENTION"
    assert [i["text"] for i in rows[COST]["in_hand"]] == ["ACT-048"]
    assert rows[COST]["earlier_empty_text"] == EARLIER_EMPTY_NONE
    assert board_module.unresolved_links(kobo(findings=(outside,))) == ()
    # Addendum 3 L5: the Must-not-harm line stays; the Action is in hand on this row and its check exists.
    assert rows[COST]["must_not_harm"] is not None and "ACT-048" in rows[COST]["must_not_harm"]["text"]


def test_closed_linked_finding_keeps_case_in_its_outcome() -> None:
    closed = replace(F104, lifecycle="RETIRED")
    case = CaseFact("w1", "MR-007", "MAINTENANCE_REQUEST", "Check generator", "COMPLETED", "gen", None, ("f104",),
                    t(1), R.case_ref("C", "w1"))
    rows = rows_by_cat(kobo(findings=(closed,), actions=(), cases=(case,)))
    assert [e["result_label"] for e in rows[COST]["earlier"]] == ["Not yet verified"]
    assert rows[PROTECT]["earlier"] == [] and not [i for i in rows[COST]["issues"] if i["kind"] == "FINDING"]


def test_signal_kind_derived_from_key() -> None:
    assert HEADROOM.kind == "OPPORTUNITY" and GAP.kind == "EVIDENCE_GAP"
