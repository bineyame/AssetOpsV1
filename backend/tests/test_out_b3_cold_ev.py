"""OUT-B3: the cold and EV composers over fake ports (build spec §B.4 cold and EV tables; rulings B-Q7/Q17/Q18/Q21-Q26;
addenda 2-3: (a) cooling recovery, R551; (b) the route Site zone with the UTC fallback; (c) EV counts from
`denominator`; (d) EV closed Findings through the single `finding(...)` read; M1 the Finding source)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from assetops_backend.site_outcomes import cold, ev
from assetops_backend.site_outcomes.board import NOT_LOADED_LINK_SUFFIX, OUTSIDE_VIEW_SUFFIX, assemble
from assetops_backend.site_outcomes.mini import NOT_LOADED

GROW, COST, PROTECT, ASSURE = cold.GROW, cold.COST, cold.PROTECT, cold.ASSURE
LO = datetime(2026, 10, 20, tzinfo=timezone.utc)
HI = LO + timedelta(days=1)
ZONE = "Africa/Nairobi"  # UTC+3


def T(hour: int, minute: int = 0, day: int = 20) -> str:
    return datetime(2026, 10, day, hour, minute, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def contributor(row: dict, key: str) -> dict:
    return next(c for c in row["contributors"] if c["key"] == key)


def outcome(row: dict, key: str) -> str:
    return next(o["state"] for o in row["outcomes"] if o["key"] == key)


class Fake:
    """`refuse` names the ports that raise; `over` replaces a port's return value."""

    def __init__(self, refuse: tuple[str, ...] = (), **over: Any) -> None:
        self.refuse, self.over, self.calls = refuse, over, []

    def go(self, name: str, value: Any, *args: Any) -> Any:
        self.calls.append((name, args))
        if name in self.refuse:
            raise RuntimeError(f"{name} refused")
        return self.over.get(name, value)


# ================================================================ cold (GreenHarvest)

C = "COLD-LAB-001"
F118 = {"finding_id": "f118", "kind": "START_RESPONSE", "subject_asset_id": "gen", "revision_id": "f118r",
        "lifecycle": "SUPPORTED", "title": "Backup did not start", "claim": {"result": "OBSERVED_FAILURE"},
        "episode_bounds": {"start": {"earliest": T(6), "latest": T(6)}, "end": {"earliest": T(7), "latest": T(7)}},
        "links": {"finding": f"/sites/{C}/findings/f118"}}
F119 = {"finding_id": "f119", "kind": "EXCURSION", "subject_asset_id": "room", "revision_id": "f119r",
        "lifecycle": "UNCONFIRMED", "title": "Chamber above limit", "claim": {"peak_observed": "8.4"},
        "episode_bounds": {"start": {"earliest": T(6, 10), "latest": T(6, 20)},
                           "end": {"earliest": T(7, 0), "latest": T(7, 5)}},
        "links": {"finding": f"/sites/{C}/findings/f119"}}
COLD_OVERVIEW = {
    "currentness": {"state": "CURRENT"},
    "objective": {"policy_low_deg_c": "2", "policy_high_deg_c": "5", "room_asset_id": "room"},
    "needs_attention": [{"code": "COLD_START_FAILURE", "text": "x", "link": None}],
    "backup_summary": {"attempts": 1, "observed_success": 0, "observed_failure": 1, "unknown": 0},
    "cooling": {"state": "LIMITED", "text": "x", "limitation": "y"},
    "causal_strip": [{"step": "GRID", "state": "OBSERVED"}, {"step": "START_REQUEST", "state": "OBSERVED"},
                     {"step": "COMPRESSOR", "state": "MISSING"}],
}
DA1 = {"action_id": "da1", "action_code": "DA-1", "domain": "cold_chain", "title": "Witnessed automatic-start test",
       "origin": {"finding_id": "f118", "finding_revision_id": "f118r"}, "state": "OPEN",
       "links": {"action": f"/sites/{C}/actions/da1"}}
W1_ROW = {"action_id": "w1", "action_code": "ACT-001", "domain": "cold_chain", "title": None,
          "origin": {"finding_id": "f-w1", "finding_revision_id": "r"}, "state": "OPEN", "links": {}}
MR5 = {"case_id": "mr5", "code": "MR-5", "title": "Inspect generator", "state": "COMPLETED", "asset_id": "gen",
       "asset_label": "generator-1 · GENERATOR", "finding_links": [{"finding_id": "f118"}], "occurred_at": T(9)}
COLD_PLANS = [
    {"canonical_plan_id": "p1", "code": "PM-1", "title": "Generator service", "trigger_kind": "CALENDAR",
     "next_due_at": T(22, 0, 31), "next_due_hours": None, "state": "DRAFT", "asset_id": "gen",
     "asset_label": "generator-1 · GENERATOR"},
    {"canonical_plan_id": "p2", "code": "PM-2", "title": "Compressor check", "trigger_kind": "CALENDAR",
     "next_due_at": T(8, 0, 25), "next_due_hours": None, "state": "DRAFT", "asset_id": "cmp",
     "asset_label": "compressor-1 · COMPRESSOR"}]


def cold_ports(fake: Fake) -> cold.ColdPorts:
    return cold.ColdPorts(
        overview=lambda lo, hi: fake.go("cold_overview", COLD_OVERVIEW, lo, hi),
        findings=lambda lo, hi, cur: fake.go("cold_findings", {"items": [F118, F119], "next_cursor": None}, lo, hi),
        domain_actions=lambda lo, hi, cur: fake.go("domain_actions", {"rows": [DA1, W1_ROW], "next_cursor": None},
                                                   lo, hi),
        work=lambda kind, lo, hi, cur: fake.go("work", {"rows": [MR5] if kind == "maintenance" else [],
                                                        "next_cursor": None}, kind, lo, hi),
        plans=lambda lo, hi: fake.go("plans", COLD_PLANS, lo, hi),
        readiness=lambda lo, hi: fake.go("readiness", "LIMITED", lo, hi))


def run_cold(fake: Fake | None = None, tz: str | None = ZONE):
    comp = cold.compose(cold_ports(fake or Fake()), site_code=C, lo=LO, hi=HI, site_timezone=tz)
    return comp, {r["category"]: r for r in assemble(comp.facts)}


def test_greenharvest_board_from_ports() -> None:
    comp, rows = run_cold()
    assert comp.read_state == "AVAILABLE" and comp.failed == () and comp.timezone == ZONE
    assert rows[PROTECT]["state"] == "NEEDS_ATTENTION"
    assert outcome(rows[PROTECT], "CC-6") == "NEEDS_ATTENTION"
    assert contributor(rows[PROTECT], "chamber_temperature")["text"] == "Peak 8.4°C against a 5°C limit"
    assert contributor(rows[PROTECT], "backup_start")["text"] == "Automatic start failed; started by hand"
    recovery = contributor(rows[PROTECT], "cooling_recovery")
    assert recovery["text"] == cold.COOLING_TEXT["LIMITED"] and recovery["confidence"] is None  # addendum 3 (a)
    assert contributor(rows[PROTECT], "backup_generator")["text"] == "Generator service due 1 Nov"  # local zone
    assert contributor(rows[PROTECT], "compressor")["text"] == "Compressor check due 25 Oct"
    assert rows[PROTECT]["headline"] == "Chamber above 5°C for 40–55 min"
    assert rows[PROTECT]["subline"] == cold.PROTECT_SUBLINE_START
    assert [(o["text"], o["href"]) for o in rows[PROTECT]["options"]] == [
        ("Witnessed automatic-start test", f"/sites/{C}/actions/da1"),
        ("Stock value what-if", f"/sites/{C}/financials/scenarios")]
    assert contributor(rows[ASSURE], "verified_results")["text"] == "MR-5 completed; not yet verified"
    assert contributor(rows[ASSURE], "event_chain")["text"] == "1 step not recorded"  # singular (L7)
    assert rows[ASSURE]["headline"] == "Event partly reconstructed · no verified result yet"
    assert rows[ASSURE]["subline"] == cold.ASSURE_SUBLINE
    assert [o["text"] for o in rows[ASSURE]["options"]] == ["Record stock and door log"]


def test_w1_rows_ignored_and_domain_action_in_hand_only() -> None:
    comp, rows = run_cold()
    assert [a.action_id for a in comp.facts.actions] == ["da1"]  # B-Q21: the title-less W1 row is ignored
    assert any(i["text"] == "DA-1 · Witnessed automatic-start test" for i in rows[PROTECT]["in_hand"])
    assert not any("DA-1" in e["text"] for r in rows.values() for e in r["earlier"])


def test_cooling_states_and_full_chain() -> None:
    contradictory = dict(COLD_OVERVIEW, cooling={"state": "CONTRADICTORY"},
                         causal_strip=[{"step": "GRID", "state": "OBSERVED"}])
    _, rows = run_cold(Fake(cold_overview=contradictory))
    rec = contributor(rows[PROTECT], "cooling_recovery")
    assert rec["text"] == "Cooling records disagree, so recovery cannot be judged"
    assert rec["confidence"] == {"label": "Unknown", "tone": "gray"}
    assert contributor(rows[ASSURE], "event_chain")["text"] == "Every step recorded"
    assert rows[ASSURE]["headline"] == "Event fully reconstructed · no verified result yet"
    _, rows = run_cold(Fake(cold_overview=dict(COLD_OVERVIEW, cooling={"state": "UNAVAILABLE"})))
    assert contributor(rows[PROTECT], "cooling_recovery")["text"] == cold.COOLING_TEXT["UNAVAILABLE"]
    assert "Restarted with power" not in str(rows)  # R551


def test_no_start_failure_and_no_plans() -> None:
    calm = dict(COLD_OVERVIEW, needs_attention=[], backup_summary={"observed_success": 1})
    items = {"items": [F119], "next_cursor": None}
    _, rows = run_cold(Fake(cold_overview=calm, cold_findings=items, plans=[]))
    assert contributor(rows[PROTECT], "backup_start")["text"] == "Automatic start recorded"
    assert contributor(rows[PROTECT], "backup_generator")["text"] == "No preventive plan recorded"
    assert rows[PROTECT]["subline"] == "Compressor and backup condition are not assessed"
    assert [o["text"] for o in rows[PROTECT]["options"]] == ["Stock value what-if"]


def test_cold_utc_fallback_when_route_zone_missing() -> None:
    comp, rows = run_cold(tz=None)
    assert comp.timezone is None
    assert contributor(rows[PROTECT], "backup_generator")["text"] == (
        "Generator service due 31 Oct · UTC (Site time zone unavailable)")
    _, rows = run_cold(tz="Not/AZone")
    assert contributor(rows[PROTECT], "backup_generator")["text"].endswith("UTC (Site time zone unavailable)")


def test_refused_cold_findings_unsettle_cc6_cc1() -> None:
    comp, rows = run_cold(Fake(refuse=("cold_findings",)))
    assert comp.read_state == "PARTIAL" and "cold_findings" in comp.failed
    assert outcome(rows[PROTECT], "CC-6") == "UNKNOWN" and outcome(rows[PROTECT], "CC-1") == "UNKNOWN"
    labels = [i["state_label"] for i in rows[PROTECT]["in_hand"] if i["text"].startswith("DA-1")]
    assert labels == ["Open" + NOT_LOADED_LINK_SUFFIX]
    assert "outside this view" not in str(rows)


def test_cold_degrade_only_ports_never_set_unknown() -> None:
    for port in ("work", "plans", "domain_actions"):
        comp, rows = run_cold(Fake(refuse=(port,)))
        assert comp.read_state == "PARTIAL", port
        assert outcome(rows[PROTECT], "CC-6") == "NEEDS_ATTENTION", port
    _, rows = run_cold(Fake(refuse=("plans",)))
    assert contributor(rows[PROTECT], "compressor")["text"] == NOT_LOADED


def test_cold_overview_refusal_or_pending_unsettles() -> None:
    comp, rows = run_cold(Fake(refuse=("cold_overview",)))
    assert comp.read_state == "PARTIAL" and outcome(rows[PROTECT], "CC-6") == "UNKNOWN"
    assert contributor(rows[PROTECT], "cooling_recovery")["text"] == NOT_LOADED
    _, rows = run_cold(Fake(cold_overview=dict(COLD_OVERVIEW, currentness={"state": "PENDING_RECOMPUTE"})))
    assert outcome(rows[PROTECT], "CC-1") == "UNKNOWN"


# ================================================================ EV (Depot)

E = "EV-LAB-001"
F130 = {"finding_id": "f130", "revision_id": "f130r", "title": "Charging interrupted", "lifecycle": "SUPPORTED",
        "links": {"self": f"/sites/{E}/ev/findings/f130"}}
F120 = {"finding_id": "f120", "revision_id": "f120r", "title": "Charging interrupted (earlier)",
        "lifecycle": "RETIRED", "links": {"self": f"/sites/{E}/ev/findings/f120"}}
EV_OVERVIEW = {
    "currentness": {"state": "CURRENT"},
    "denominator": {"started": 6, "completed": 4, "observed_abort": 1, "incomplete": 1, "contradictory": 0,
                    "orphan": 0, "confirmed_delivery": 4, "fault_aborted": 1},
    "energy": {"complete_kwh": "182.50"},
    "site_power": {"observed_peak_kw": "76", "configured_limit_kw": "120"},
    "consequence_summary": {"state": "PRICED", "amount": "12.40", "currency": "USD"},
}
HEALTH = {"health": {"rows": [{"kind": "CONNECTOR", "label": "C2", "asset_code": "c2",
                               "condition_state": "NEEDS_INVESTIGATION"},
                              {"kind": "CONNECTOR", "label": "C1", "asset_code": "c1", "condition_state": "UNKNOWN"}]}}
AVAIL = {"availability": {"connectors": [
    {"label": "C1", "known_unavailable_seconds": 0, "unknown_seconds": 0, "spans": []},
    {"label": "C2", "known_unavailable_seconds": 5400, "unknown_seconds": 1800,
     "spans": [{"from": T(10), "to": T(10, 30), "state": "UNKNOWN"}]}]}}
EA1 = {"action_id": "ea1", "action_code": "DA-7", "domain": "ev_charging", "title": "Inspect connector C2",
       "origin": {"finding_id": "f130", "finding_revision_id": "f130r"}, "state": "OPEN",
       "links": {"action": f"/sites/{E}/actions/ea1"}}
MR9 = {"case_id": "mr9", "code": "MR-9", "title": "Replace connector latch", "state": "COMPLETED", "asset_id": "c2",
       "asset_label": "c2 · EV_CONNECTOR", "finding_links": [{"finding_id": "f120"}], "occurred_at": T(3, 0, 12)}


def ev_ports(fake: Fake, single: Any = None) -> ev.EvPorts:
    def finding(fid, lo, hi):
        value = fake.go("ev_finding", None, fid, lo, hi)
        return value if "ev_finding" in fake.over else ({"f120": F120}.get(fid) if single is None else single)

    return ev.EvPorts(
        overview=lambda lo, hi: fake.go("ev_overview", EV_OVERVIEW, lo, hi),
        findings=lambda lo, hi, cur: fake.go("ev_findings", {"items": [F130], "next_cursor": None}, lo, hi),
        finding=finding,
        health=lambda lo, hi: fake.go("ev_depth", HEALTH, lo, hi),
        availability=lambda lo, hi: fake.go("ev_availability", AVAIL, lo, hi),
        domain_actions=lambda lo, hi, cur: fake.go("domain_actions", {"rows": [EA1], "next_cursor": None}, lo, hi),
        work=lambda kind, lo, hi, cur: fake.go("work", {"rows": [MR9] if kind == "maintenance" else [],
                                                        "next_cursor": None}, kind, lo, hi),
        plans=lambda lo, hi: fake.go("plans", [], lo, hi),
        readiness=lambda lo, hi: fake.go("readiness", "LIMITED", lo, hi))


def run_ev(fake: Fake | None = None, tz: str | None = ZONE):
    comp = ev.compose(ev_ports(fake or Fake()), site_code=E, lo=LO, hi=HI, site_timezone=tz)
    return comp, {r["category"]: r for r in assemble(comp.facts)}


def test_depot_board_from_ports() -> None:
    comp, rows = run_ev()
    assert comp.read_state == "AVAILABLE" and comp.failed == ()
    assert outcome(rows[PROTECT], "EV-1") == "NEEDS_ATTENTION"
    assert contributor(rows[GROW], "charging_delivered")["text"] == "182.5 kWh with a complete meter record · 4 of 6 sessions completed"
    assert rows[GROW]["headline"] == "gross tariff estimate"
    assert rows[GROW]["headline_money"] == {"amount_low": "12.40", "amount_high": "12.40", "currency": "USD"}
    assert rows[GROW]["subline"] == "182.5 kWh with a complete meter record"
    assert contributor(rows[PROTECT], "session_service")["text"] == "1 fault-aborted session, 1 outcome unknown"
    assert contributor(rows[PROTECT], "connector_availability")["text"] == "Connector C2: 1 h 30 min out, 30 min unknown"
    assert contributor(rows[PROTECT], "charger_condition")["text"] == "Fault recorded on C2"
    assert contributor(rows[PROTECT], "site_power")["text"] == "Peak 76 kW of the 120 kW import limit"
    assert rows[PROTECT]["headline"] == "1 interrupted · 1 unknown of 6 sessions"  # addendum 3 (c)
    assert rows[PROTECT]["subline"] == ("Connector C2 was out of service for 1 h 30 min; which departures were "
                                        "affected is not known yet. Charger condition is not assessed")
    assert [(o["text"], o["href"]) for o in rows[PROTECT]["options"]] == [
        ("Investigate connector C2", f"/sites/{E}/actions/ea1")]
    assert contributor(rows[ASSURE], "session_records")["text"] == "1 session has no accepted end"
    assert contributor(rows[ASSURE], "connector_status")["text"] == "Missing 20 Oct 13:00–20 Oct 13:30"  # UTC+3
    assert rows[ASSURE]["headline"] == "Evidence limited · no verified result yet"
    assert rows[ASSURE]["subline"] == "1 session end and 30 min of connector status are missing"
    assert contributor(rows[ASSURE], "energy_billed")["href"] == f"/sites/{E}/ev/financials"


def test_null_denominator_reads_not_available() -> None:
    nulls = dict(EV_OVERVIEW, denominator={k: None for k in EV_OVERVIEW["denominator"]})
    _, rows = run_ev(Fake(ev_overview=nulls))
    for cat, key in ((PROTECT, "session_service"), (ASSURE, "session_records")):
        c = contributor(rows[cat], key)
        assert c["text"] == ev.NO_SESSION_ASSESSMENT and c["confidence"] is None, key
    # addendum 9 M1: the energy still stands when the session counts are null
    assert contributor(rows[GROW], "charging_delivered")["text"] == "182.5 kWh with a complete meter record"
    assert rows[PROTECT]["headline"] == "Charging interrupted"  # null headline: the board's lead-Finding fallback


def test_closed_linked_finding_resolved_through_single_read() -> None:
    fake = Fake()
    comp, rows = run_ev(fake)
    assert [args[0] for name, args in fake.calls if name == "ev_finding"] == ["f120"]  # only the missing link
    assert {f.finding_id for f in comp.facts.findings} == {"f130", "f120"} and comp.diagnostics == ()
    assert {"text": "MR-9 · Replace connector latch", "href": "/maintenance/requests/mr9",
            "result_label": "Not yet verified"} in rows[PROTECT]["earlier"]
    assert "outside this view" not in str(rows)


def test_single_read_none_is_outside_this_view() -> None:
    comp, rows = run_ev(Fake(ev_finding=None))
    assert comp.diagnostics == (("mr9", "f120"),) and comp.read_state == "AVAILABLE"
    assert any(e["result_label"].endswith(OUTSIDE_VIEW_SUFFIX) for e in rows[PROTECT]["earlier"])


def test_refused_ev_finding_source_unsettles_ev1_ev3() -> None:
    for refuse in ("ev_findings", "ev_finding"):
        comp, rows = run_ev(Fake(refuse=(refuse,)))
        assert comp.read_state == "PARTIAL" and "ev_findings" in comp.failed, refuse
        assert outcome(rows[PROTECT], "EV-1") == "UNKNOWN" and outcome(rows[GROW], "EV-3") == "UNKNOWN", refuse
        assert not comp.facts.findings_settled
        assert "outside this view" not in str(rows), refuse
    _, rows = run_ev(Fake(refuse=("ev_finding",)))
    assert any(e["result_label"].endswith(NOT_LOADED_LINK_SUFFIX) for e in rows[PROTECT]["earlier"])


def test_ev_depth_refusals_degrade_contributors() -> None:
    comp, rows = run_ev(Fake(refuse=("ev_depth", "ev_availability")))
    assert comp.read_state == "PARTIAL"
    assert contributor(rows[PROTECT], "charger_condition")["text"] == NOT_LOADED
    assert contributor(rows[ASSURE], "connector_status")["text"] == NOT_LOADED
    quiet = {"availability": {"connectors": [{"label": "C1", "known_unavailable_seconds": 0, "unknown_seconds": 0,
                                              "spans": []}]}}
    _, rows = run_ev(Fake(ev_availability=quiet, ev_depth={"health": {"rows": []}}))
    assert contributor(rows[PROTECT], "connector_availability")["text"] == "All connectors available"
    assert contributor(rows[PROTECT], "charger_condition")["text"] == "No charger fault recorded"
    assert contributor(rows[ASSURE], "connector_status")["text"] == "No status gap"
    assert rows[PROTECT]["subline"] == "Charger condition is not assessed"


def test_ev_unpriced_and_declared_limit() -> None:
    body = dict(EV_OVERVIEW, consequence_summary={"state": None, "amount": None, "currency": None},
                site_power={"observed_peak_kw": None, "configured_limit_kw": "120"})
    _, rows = run_ev(Fake(ev_overview=body), tz=None)
    assert rows[GROW]["headline"] == "Gross tariff estimate not available yet" and rows[GROW]["headline_money"] is None
    power = contributor(rows[PROTECT], "site_power")
    assert power["confidence"] == {"label": "Declared", "tone": "neutral"}
    assert contributor(rows[ASSURE], "connector_status")["text"] == (
        "Missing 20 Oct 10:00–20 Oct 10:30 · UTC (Site time zone unavailable)")


def test_ev_grow_pairs_meter_record_with_completed_honestly() -> None:  # addendum 9 M1
    den = dict(EV_OVERVIEW["denominator"], started=1, completed=0)
    body = dict(EV_OVERVIEW, denominator=den, energy={"complete_kwh": "15"})
    _, rows = run_ev(Fake(ev_overview=body))
    assert contributor(rows[GROW], "charging_delivered")["text"] == (
        "15 kWh with a complete meter record · 0 of 1 session completed")
    den = dict(den, completed=None)
    _, rows = run_ev(Fake(ev_overview=dict(body, denominator=den)))
    assert contributor(rows[GROW], "charging_delivered")["text"] == "15 kWh with a complete meter record"
    _, rows = run_ev(Fake(ev_overview=dict(body, energy={"complete_kwh": None})))
    assert rows[GROW]["subline"] is None
    assert "Not available yet" in contributor(rows[GROW], "charging_delivered")["text"]


def test_ev_assure_subline_never_prints_unknown_count() -> None:  # addendum 9 L2
    def sub(incomplete, avail=AVAIL):
        den = dict(EV_OVERVIEW["denominator"], incomplete=incomplete)
        _, rows = run_ev(Fake(ev_overview=dict(EV_OVERVIEW, denominator=den), ev_availability=avail))
        return rows[ASSURE]["subline"]

    quiet = {"availability": {"connectors": [{"label": "C1", "known_unavailable_seconds": 0, "unknown_seconds": 0,
                                              "spans": []}]}}
    assert sub(None) == "30 min of connector status is missing"
    assert sub(0) == "30 min of connector status is missing"
    assert sub(2, quiet) == "2 session ends are missing"
    assert sub(1, quiet) == "1 session end is missing"
    assert sub(None, quiet) is None
    assert sub(2) == "2 session ends and 30 min of connector status are missing"


def test_ev_status_gap_guards_null_span_bounds() -> None:  # addendum 9 L3
    avail = {"availability": {"connectors": [
        {"label": "C2", "known_unavailable_seconds": 0, "unknown_seconds": 1800,
         "spans": [{"from": None, "to": None, "state": "UNKNOWN"}]}]}}
    _, rows = run_ev(Fake(ev_availability=avail))
    text = contributor(rows[ASSURE], "connector_status")["text"]
    assert text == "Connector status missing for part of this window" and "None" not in text
    _, rows = run_ev(Fake(ev_availability=avail), tz=None)
    text = contributor(rows[ASSURE], "connector_status")["text"]
    assert text.startswith("Connector status missing for part of this window · UTC") and "None" not in text


def test_cold_chain_counts_contradictory_steps() -> None:  # addendum 9 L1
    def chain(strip):
        _, rows = run_cold(Fake(cold_overview=dict(COLD_OVERVIEW, causal_strip=strip)))
        return contributor(rows[ASSURE], "event_chain")["text"], rows[ASSURE]["headline"]

    ok, miss, con = ({"step": "A", "state": s} for s in ("OBSERVED", "MISSING", "CONTRADICTORY"))
    assert chain([ok]) == ("Every step recorded", cold.ASSURE_FULL)
    assert chain([ok, miss]) == ("1 step not recorded", cold.ASSURE_PART)
    assert chain([ok, con]) == ("1 step has conflicting records", cold.ASSURE_PART)
    assert chain([con, con, miss, miss]) == (
        "2 steps not recorded · 2 steps have conflicting records", cold.ASSURE_PART)


def test_cold_and_ev_composers_import_no_adapter_or_composition() -> None:
    import ast
    from pathlib import Path
    for module in (cold, ev):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        names = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
        assert not [n for n in names if ".adapters" in n or n.endswith(".composition")], module.__name__


def vocabulary_compositions():
    return [run_cold()[0], run_cold(Fake(refuse=("cold_findings", "plans")), tz=None)[0],
            run_ev()[0], run_ev(Fake(refuse=("ev_finding",)), tz=None)[0]]
