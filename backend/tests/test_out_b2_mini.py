"""OUT-B2: the mini composer over fake ports (build spec §B.4 mini table; rulings B-Q6/Q10-Q14/Q17/Q18/Q22/Q23,
addendum 2). Includes M1b: every Finding a case or Action links is supplied, closed heads included."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from typing import Any

from assetops_backend.site_outcomes import mini
from assetops_backend.site_outcomes.board import assemble
from assetops_backend.site_outcomes.mini import MiniPorts, compose, limitation_text

GROW, COST, PROTECT, ASSURE = mini.GROW, mini.COST, mini.PROTECT, mini.ASSURE
DAY = date(2026, 10, 20)
ZONE = "Africa/Nairobi"  # UTC+3, no DST
C = "KOBO-001"


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


T = lambda day, hour=0: datetime(2026, 10, day, hour, tzinfo=timezone.utc)  # noqa: E731

OVERVIEW = {
    "freshness": {"state": "CURRENT"},
    "assessment": {"state": "LIMITED", "limitations": ["EVIDENCE_GAP: interval from x is Indeterminate over a..b: "
                                                        "PCS_CAPABILITY_UNAVAILABLE"]},
    "money": {"state": "PRICED", "eligibility": {"state": "ELIGIBLE"}, "amount_low": "3.31", "amount_high": "3.97",
              "currency": "USD", "source_provenance": {"state": "REGISTERED_SIMULATION"}},
}
DEPTH = {
    "renewable": {"headroom_kw": {"low": "18", "high": "24.25"}, "eligible_days": 1, "assessed_days": 1},
    "fuel": {"opening_l": None},
    "service": {"delivered_load_kw": "11.2"},
    "backup": {"outage_count": 0, "start_success_count": None},
}
F104 = {"finding_id": "f104", "finding_revision_id": "f104r", "title": "Generator support review",
        "lifecycle": "SUPPORTED", "episode": {"start": iso(T(20, 6)), "end": iso(T(20, 9))},
        "links": {"selected_revision": f"/sites/{C}/findings/f104?revision_id=f104r"}}
F090 = {"finding_id": "f090", "finding_revision_id": "f090r", "title": "Generator support review (earlier)",
        "lifecycle": "RETIRED", "episode": {"start": iso(T(2, 6)), "end": iso(T(2, 9))},
        "links": {"selected_revision": f"/sites/{C}/findings/f090?revision_id=f090r"}}
ESTATE_F104 = {"finding_id": "f104", "finding_revision_id": "f104r", "lifecycle": "SUPPORTED",
               "source_provenance": {"state": "REGISTERED_SIMULATION"}, "consequence": {"state": "PRICED"},
               "_episode_end": T(20, 9), "_mechanism": "GENERATOR_SUPPORT_CANDIDATE"}
ESTATE_A48 = {"action_id": "a48", "source_finding_id": "f104", "source_finding_revision_id": "f104r",
              "application_state": "PENDING", "resolution_state": None, "verification_outcome": None,
              "_raw": {"_selected_recorded_at": T(19), "_verification_window": False}}
A48 = {"action_id": "a48", "action_code": "ACT-048", "origin": {"finding_id": "f104", "finding_revision_id": "f104r"},
       "selected_event": {"id": "e1"}, "state": {"application": "PENDING"},
       "links": {"selected_event": f"/sites/{C}/actions/a48?event_id=e1"}}
MR1 = {"case_id": "mr1", "code": "MR-1", "title": "Check generator stop", "state": "COMPLETED", "asset_id": "gen",
       "asset_label": "GEN-1 · generator", "finding_links": [{"finding_id": "f090"}], "occurred_at": iso(T(3))}
IN1 = {"case_id": "in1", "code": "IN-1", "title": "Feeder trip", "state": "OPEN", "asset_id": None,
       "asset_label": None, "finding_links": [{"finding_id": "f-old"}], "occurred_at": iso(T(1))}
PLANS = [{"canonical_plan_id": "p1", "code": "PM-1", "title": "Generator service", "trigger_kind": "RUN_HOURS",
          "next_due_at": None, "next_due_hours": "500.0", "state": "DRAFT", "asset_id": "gen"},
         {"canonical_plan_id": "p2", "code": "PM-2", "title": "Battery check", "trigger_kind": "CALENDAR",
          "next_due_at": iso(T(31, 22)), "next_due_hours": None, "state": "DRAFT", "asset_id": "bat"}]


class Fake:
    """Fake ports; `refuse` names the ports that raise, `calls` records every call."""

    def __init__(self, refuse: tuple[str, ...] = (), **over: Any) -> None:
        self.refuse, self.over, self.calls = refuse, over, []

    def _go(self, name: str, value: Any, *args: Any) -> Any:
        self.calls.append((name, args))
        if name in self.refuse:
            raise RuntimeError(f"{name} refused")
        return self.over.get(name, value)

    def ports(self) -> MiniPorts:
        def depth(domain, lo, hi):
            self.calls.append(("depth", (domain, lo, hi)))
            if "depth" in self.refuse or f"depth:{domain}" in self.refuse:
                raise RuntimeError("refused")
            return {"site": {"timezone": ZONE}, "cards": self.over.get("cards", DEPTH)[domain]}

        def finding_index(lo, hi, cursor):  # two pages (paging combined, M1b closed head on page two)
            page = self._go("finding_index", None, lo, hi, cursor)
            if page is not None:
                return page
            return ({"rows": [F104], "next_cursor": "c2"} if cursor is None else {"rows": [F090], "next_cursor": None})

        return MiniPorts(
            overview=lambda d: self._go("overview", OVERVIEW, d),
            depth=depth,
            dispatch=lambda d: self._go("dispatch", {"intervals": [
                {"result": {"portions_minutes": {"candidate": "30.0", "necessary": "10", "indeterminate": "12"}}},
                {"result": {"portions_minutes": {"candidate": "15", "necessary": "0", "indeterminate": "0"}}}]}, d),
            assumption=lambda at: self._go("assumptions", {"selection": {"state": "PRICED", "price": {
                "value": "1.45", "currency": "USD"}}}, at),
            finding_index=finding_index,
            estate=lambda lo, hi: self._go("estate", {"site_cov": {"state": "CURRENT"}, "findings": [ESTATE_F104],
                                                      "actions": [ESTATE_A48]}, lo, hi),
            action_index=lambda lo, hi, cur: self._go("action_index", {"rows": [A48], "next_cursor": None}, lo, hi),
            verification=lambda aid: self._go("verification", {"state": "PENDING"}, aid),
            action=lambda aid, ev: self._go("action", {"change": {"id": "ch1"}}, aid, ev),
            work=lambda kind, lo, hi, cur: self._go(
                "work", {"rows": [MR1] if kind == "maintenance" else [IN1], "next_cursor": None}, kind, lo, hi),
            plans=lambda lo, hi: self._go("plans", PLANS, lo, hi),
            readiness=lambda lo, hi: self._go("readiness", "LIMITED", lo, hi),
        )


def run(fake: Fake | None = None, tz: str | None = ZONE):
    comp = compose((fake or Fake()).ports(), site_code=C, day=DAY, site_timezone=tz)
    return comp, {r["category"]: r for r in assemble(comp.facts)}


def contributor(row: dict, key: str) -> dict:
    return next(c for c in row["contributors"] if c["key"] == key)


def outcome(row: dict, key: str) -> str:
    return next(o["state"] for o in row["outcomes"] if o["key"] == key)


def vocabulary_compositions():
    return [run()[0], run(Fake(refuse=("depth", "estate", "dispatch", "overview")))[0], run(tz=None)[0]]


# --------------------------------------------------------------- happy path

def test_kobo_board_from_ports() -> None:
    comp, rows = run()
    assert comp.read_state == "AVAILABLE" and comp.failed == () and comp.timezone == ZONE
    assert [rows[c]["state"] for c in (GROW, COST, PROTECT, ASSURE)] == [
        "OPPORTUNITY", "NEEDS_ATTENTION", "NO_OBJECTIVE", "WATCH"]
    assert rows[GROW]["headline"] == "18–24.3 kW of daytime solar unused"
    assert contributor(rows[GROW], "productive_use")["text"] == "Spare solar on 1 of 1 well-observed day"
    assert rows[COST]["headline"] == "exposure in this hour"
    assert rows[COST]["headline_money"] == {"amount_low": "3.31", "amount_high": "3.97", "currency": "USD"}
    assert rows[COST]["subline"] == "Generator stayed on 45 minutes longer than needed"
    gen = contributor(rows[COST], "generator_use")
    assert gen["text"] == "45 min avoidable, 12 min unclear"
    assert gen["confidence"] == {"label": "High", "tone": "green"}  # place() over the estate row (addendum 2 #3)
    assert contributor(rows[COST], "fuel")["text"] == "No complete fuel balance yet"
    assert contributor(rows[COST], "fuel_price")["text"] == "Declared at 1.45 USD per litre"
    assert [o["text"] for o in rows[COST]["options"]] == ["Trial a lower generator stop setting",
                                                          "Proposed setting change"]
    assert rows[COST]["options"][0]["href"] == f"/sites/{C}/findings/f104/recommendation"
    assert rows[COST]["in_hand"] == [{"text": "ACT-048", "href": f"/sites/{C}/actions/a48?event_id=e1",
                                      "state_label": "Pending"}]  # workflow_label: application PENDING
    assert rows[COST]["must_not_harm"]["text"] == (
        "Reliable service and battery and generator life are checked as safeguards when ACT-048 is verified; "
        "a gain that harms them does not count")
    assert rows[COST]["must_not_harm"]["href"] == f"/sites/{C}/actions/a48/verification?event_id=e1"
    assert contributor(rows[PROTECT], "generator")["text"] == (
        "Service due at 500 operating hours · hours since service not recorded")
    assert contributor(rows[PROTECT], "service_delivery")["text"] == "Delivered power measured; demand not measured"
    assert contributor(rows[PROTECT], "backup_readiness")["text"] == "No backup event in this window"
    assert contributor(rows[ASSURE], "verified_results")["text"] == "ACT-048 not yet verified"
    assert contributor(rows[ASSURE], "readings")["text"] == "Generated test data source · readiness Limited"
    assert contributor(rows[ASSURE], "battery_reporting")["text"] == "Battery output not reported"
    assert [i["text"] for i in rows[ASSURE]["issues"]] == ["Battery output not reported limits this conclusion"]
    assert [o["text"] for o in rows[ASSURE]["options"]] == ["Restore battery reporting"]
    assert rows[ASSURE]["subline"] == "Battery output not reported"


def test_depth_windows_follow_the_site_local_day() -> None:
    fake = Fake()
    run(fake)
    windows = {args[0]: args[1:] for name, args in fake.calls if name == "depth"}
    assert windows["renewable"] == (T(19, 21), T(20, 21))  # local midnight 20 Oct .. 21 Oct (UTC+3)
    assert windows["service"] == windows["fuel"] == windows["backup"] == (T(20, 9), T(20, 10))  # local noon hour


def test_work_window_is_31_days_ending_with_the_day() -> None:
    fake = Fake()
    run(fake)
    for name in ("finding_index", "action_index", "estate", "plans"):
        args = next(a for n, a in fake.calls if n == name)
        assert args[:2] == (T(21) - timedelta(days=31), T(21)), name


# --------------------------------------------------------------- M1b and unresolved links (addendum 2 #4)

def test_every_linked_finding_is_supplied_closed_included() -> None:
    comp, rows = run()
    ids = {f.finding_id: f for f in comp.facts.findings}
    assert set(ids) == {"f104", "f090"}  # both index pages, closed head included
    assert ids["f104"].in_window and not ids["f090"].in_window
    linked = {a.origin_finding_id for a in comp.facts.actions} | {
        fid for case in comp.facts.cases if case.case_id == "mr1" for fid in case.finding_ids}
    assert linked <= set(ids)
    assert rows[COST]["earlier"] == [{"text": "MR-1 · Check generator stop", "href": "/maintenance/requests/mr1",
                                      "result_label": "Not yet verified"}]
    assert not [i for i in rows[COST]["issues"] if i["ref"] and i["ref"]["finding_id"] == "f090"]


def test_unresolved_link_is_kept_and_recorded_not_on_the_wire() -> None:
    comp, rows = run()
    assert comp.diagnostics == (("in1", "f-old"),)
    assert {"text": "IN-1 · Feeder trip", "href": f"/sites/{C}/work/incidents",
            "state_label": "Open · linked finding outside this view"} in rows[PROTECT]["in_hand"]
    assert "diagnostics" not in str(rows) and "f-old" not in str(rows)


def test_out_of_window_finding_drives_no_issue() -> None:
    later = dict(F104, episode={"start": iso(T(10, 6)), "end": iso(T(10, 9))})
    fake = Fake(finding_index={"rows": [later, F090], "next_cursor": None})
    comp, rows = run(fake)
    assert not any(i["kind"] == "FINDING" for r in rows.values() for i in r["issues"])
    assert [i["text"] for i in rows[COST]["in_hand"]] == ["ACT-048"]
    assert rows[COST]["options"][0]["text"] == "Proposed setting change"


# --------------------------------------------------------------- refusals (B-Q6, B-Q17, addendum 2 #2/#5/#6)

def test_depth_refusal_sets_mg1_mg5_unknown_and_utc_dates() -> None:
    comp, rows = run(Fake(refuse=("depth",)))
    assert comp.read_state == "PARTIAL" and "mini_depth" in comp.failed and comp.timezone is None
    assert outcome(rows[GROW], "MG-1") == "UNKNOWN" and outcome(rows[PROTECT], "MG-5") == "UNKNOWN"
    assert outcome(rows[COST], "MG-2") == "NEEDS_ATTENTION"
    assert contributor(rows[GROW], "productive_use")["text"] == mini.NOT_LOADED
    plan = next(i for i in rows[PROTECT]["in_hand"] if i["text"] == "PM-2 · Battery check")
    assert plan["state_label"] == "Due 31 Oct · UTC (Site time zone unavailable)"
    _, ok = run()
    assert next(i for i in ok[PROTECT]["in_hand"] if i["text"] == "PM-2 · Battery check")["state_label"] == "Due 1 Nov"


def test_one_depth_domain_refused_is_partial_and_unsettles() -> None:
    comp, rows = run(Fake(refuse=("depth:backup",)))
    assert comp.read_state == "PARTIAL" and outcome(rows[GROW], "MG-1") == "UNKNOWN"
    assert contributor(rows[PROTECT], "backup_readiness")["text"] == mini.NOT_LOADED


def test_missing_site_zone_skips_depth() -> None:
    fake = Fake()
    comp, rows = run(fake, tz=None)
    assert not [c for c in fake.calls if c[0] == "depth"] and "mini_depth" in comp.failed
    assert outcome(rows[GROW], "MG-1") == "UNKNOWN"


def test_dispatch_refusal_unsettles_mg2_only() -> None:
    comp, rows = run(Fake(refuse=("dispatch",)))
    assert comp.read_state == "PARTIAL"
    assert outcome(rows[COST], "MG-2") == "UNKNOWN" and outcome(rows[GROW], "MG-1") == "OPPORTUNITY"
    assert contributor(rows[COST], "generator_use")["text"] == mini.NOT_LOADED
    assert rows[COST]["subline"] is None


def test_estate_refusal_labels_not_loaded_and_nulls_confidence() -> None:
    comp, rows = run(Fake(refuse=("estate",)))
    assert comp.read_state == "PARTIAL" and comp.failed == ("estate",)
    assert rows[COST]["in_hand"][0]["state_label"] == mini.NOT_LOADED
    assert contributor(rows[COST], "generator_use")["confidence"] is None
    assert rows[COST]["state"] == "NEEDS_ATTENTION"  # degrade-only: no UNKNOWN


def test_degrade_only_ports_never_set_unknown() -> None:
    for port in ("work", "plans", "assumptions", "verification", "action", "action_index"):
        comp, rows = run(Fake(refuse=(port,)))
        assert comp.read_state == "PARTIAL", port
        assert [rows[c]["state"] for c in (GROW, COST, PROTECT)] == [
            "OPPORTUNITY", "NEEDS_ATTENTION", "NO_OBJECTIVE"], port
    _, rows = run(Fake(refuse=("assumptions",)))
    assert contributor(rows[COST], "fuel_price")["text"] == mini.NOT_LOADED
    _, rows = run(Fake(refuse=("plans",)))
    assert contributor(rows[PROTECT], "generator")["text"] == mini.NOT_LOADED


def _assert_finding_source_unsettled(comp, rows) -> None:
    """Addendum 3 M1: MG-2 UNKNOWN, PARTIAL, the could-not-be-loaded suffix, and no outside-view suffix."""
    assert comp.read_state == "PARTIAL" and "finding_index" in comp.failed
    assert outcome(rows[COST], "MG-2") == "UNKNOWN"
    assert outcome(rows[GROW], "MG-1") == "OPPORTUNITY"  # only the outcomes a mini Finding mechanism moves
    assert not comp.facts.findings_settled
    loaded = " · Not available yet · linked finding could not be loaded"
    assert {"text": "ACT-048", "href": f"/sites/{C}/actions/a48?event_id=e1",
            "state_label": "Pending" + loaded} in rows[PROTECT]["in_hand"]
    assert {"text": "IN-1 · Feeder trip", "href": f"/sites/{C}/work/incidents",
            "state_label": "Open" + loaded} in rows[PROTECT]["in_hand"]
    assert {"text": "MR-1 · Check generator stop", "href": "/maintenance/requests/mr1",
            "result_label": "Not yet verified" + loaded} in rows[PROTECT]["earlier"]
    assert "outside this view" not in str(rows)
    assert ("a48", "f104") in comp.diagnostics and ("in1", "f-old") in comp.diagnostics


def test_refused_finding_index_unsettles_finding_outcomes() -> None:
    """Negative control of test_degrade_only_ports_never_set_unknown: the Finding source is a status producer."""
    _assert_finding_source_unsettled(*run(Fake(refuse=("finding_index",))))


def test_pending_finding_index_unsettles_finding_outcomes() -> None:
    for status in ("PENDING", "STALE", "FAILED"):
        body = {"status": status, "rows": [], "next_cursor": None}
        _assert_finding_source_unsettled(*run(Fake(finding_index=body)))
    comp, rows = run(Fake(finding_index={"status": "UNASSESSED", "rows": [F104, F090], "next_cursor": None}))
    assert comp.facts.findings_settled and outcome(rows[COST], "MG-2") == "NEEDS_ATTENTION"


def test_missing_estate_row_is_partial_and_recorded() -> None:
    """Addendum 3 L3: the estate read succeeds but lacks the Action, so the text and the notice agree."""
    estate = {"site_cov": {"state": "CURRENT"}, "findings": [ESTATE_F104], "actions": []}
    comp, rows = run(Fake(estate=estate))
    assert comp.read_state == "PARTIAL" and comp.failed == ("estate",)
    assert ("a48", mini.ESTATE_ROW_MISSING) in comp.diagnostics
    assert rows[COST]["in_hand"][0]["state_label"] == mini.NOT_LOADED
    assert mini.ESTATE_ROW_MISSING not in str(rows)


def test_overview_refusal_or_stale_unsettles_everything_measured() -> None:
    comp, rows = run(Fake(refuse=("overview",)))
    assert comp.read_state == "PARTIAL"
    for key, cat in (("MG-1", GROW), ("MG-2", COST), ("MG-5", PROTECT), ("MG-7", ASSURE)):
        assert outcome(rows[cat], key) == "UNKNOWN", key
    stale = dict(OVERVIEW, freshness={"state": "STALE"})
    _, rows = run(Fake(overview=stale))
    assert outcome(rows[COST], "MG-2") == "UNKNOWN"
    closed = dict(OVERVIEW, assessment={"state": "CLOSED", "limitations": []})
    _, rows = run(Fake(overview=closed))
    assert outcome(rows[COST], "MG-2") == "UNKNOWN"


def test_unknown_readiness_unsettles_mg7() -> None:
    _, rows = run(Fake(readiness="UNKNOWN"))
    assert outcome(rows[ASSURE], "MG-7") == "UNKNOWN"


# --------------------------------------------------------------- copy rules

def test_limitation_text_never_renders_raw_codes() -> None:
    assert limitation_text("PCS_CAPABILITY_UNAVAILABLE: x") == "Battery output not reported"
    assert limitation_text("EVIDENCE_GAP: over a..b: PCS_CAPABILITY_UNAVAILABLE") == "Battery output not reported"
    assert limitation_text("NO_COHORT: none usable") == "An evidence gap limits this conclusion"
    _, rows = run(Fake(overview=dict(OVERVIEW, assessment={"state": "LIMITED", "limitations": ["NO_COHORT: x"]})))
    assert [i["text"] for i in rows[ASSURE]["issues"]] == ["An evidence gap limits this conclusion"]


def test_unpriced_money_and_verified_headline() -> None:
    unpriced = dict(OVERVIEW, money={**OVERVIEW["money"], "state": "NOT_PRICED"})
    _, rows = run(Fake(overview=unpriced, verification={"state": "VERIFIED"}))
    assert rows[COST]["headline"] == "No priced exposure in this hour" and rows[COST]["headline_money"] is None
    assert rows[ASSURE]["headline"] == "1 verified result"  # addendum 3 L7
    assert contributor(rows[ASSURE], "verified_results") == {
        "key": "verified_results", "label": "Verified results", "text": "ACT-048 verified on test data",
        "confidence": None, "href": f"/sites/{C}/actions/a48/verification?event_id=e1"}


def test_declared_price_is_formatted_for_display() -> None:
    price = {"selection": {"state": "PRICED", "price": {"value": "1.4500", "currency": "USD"}}}
    _, rows = run(Fake(assumptions=price))
    assert contributor(rows[COST], "fuel_price")["text"] == "Declared at 1.45 USD per litre"  # B2 review L6
    assert mini.price_text("2") == "2.00" and mini.price_text("0.1234") == "0.1234"


def test_singular_for_one_in_count_templates() -> None:
    """Addendum 3 L7: n = 1 reads singular in every "{n} ..." template."""
    cards = {**DEPTH, "backup": {"outage_count": 1, "start_success_count": 1},
             "renewable": {**DEPTH["renewable"], "eligible_days": 2, "assessed_days": 3}}
    one_minute = {"intervals": [{"result": {"portions_minutes": {"candidate": "1", "indeterminate": "0"}}}]}
    plans = [dict(PLANS[0], next_due_hours="1")]
    _, rows = run(Fake(cards=cards, dispatch=one_minute, plans=plans))
    assert contributor(rows[PROTECT], "backup_readiness")["text"] == "1 backup start recorded"
    assert contributor(rows[GROW], "productive_use")["text"] == "Spare solar on 2 of 3 well-observed days"
    assert rows[COST]["subline"] == "Generator stayed on 1 minute longer than needed"
    assert contributor(rows[PROTECT], "generator")["text"].startswith("Service due at 1 operating hour ·")
    assert any(i["state_label"] == "Due at 1 operating hour" for i in rows[PROTECT]["in_hand"])


def test_source_words_match_the_portfolio() -> None:
    from assetops_backend.estate import placement
    assert mini.SOURCE_TEXT == placement._SOURCE_TEXT  # noqa: SLF001 - equality pin for the local copy (L1)
    assert mini.SOURCE_UNRESOLVED == placement._SOURCE_UNRESOLVED_TEXT  # noqa: SLF001


def test_backup_starts_and_fuel_opening() -> None:
    cards = {**DEPTH, "backup": {"outage_count": 2, "start_success_count": 2}, "fuel": {"opening_l": "120.0"}}
    _, rows = run(Fake(cards=cards))
    assert contributor(rows[PROTECT], "backup_readiness")["text"] == "2 backup starts recorded"
    assert contributor(rows[COST], "fuel")["text"] == "120 L at the start of the window"


def test_mini_composer_imports_no_adapter_or_composition() -> None:
    import ast
    from pathlib import Path
    tree = ast.parse(Path(mini.__file__).read_text(encoding="utf-8"))
    names = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
    assert not [n for n in names if ".adapters" in n or n.endswith(".composition")]
