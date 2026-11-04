"""OUT-D U4: declared objectives on the board over fake ports (build sheet OUT-D §3 U4, §4).

Verdict -> status per rule with fake readings, the "Declared objective" contributor (order, text, chip), the mini
Assure count, CC-1 from the chamber range only, a failed objectives read, the board wire list, the summary count,
and no measure key, verdict code or policy string in any rendered text."""
from __future__ import annotations

from link_parity import checked

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import test_out_b2_mini as b2
import test_out_b3_cold_ev as b3
from assetops_backend.outcomes.objectives import MEASURES, POLICY
from assetops_backend.site_outcomes import cold, ev, mini, read
from assetops_backend.site_outcomes.board import assemble, objectives_wire
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef
from test_out_a1_outcome_map import _vocabulary_patterns

GROW, COST, PROTECT, ASSURE = mini.GROW, mini.COST, mini.PROTECT, mini.ASSURE
NOTE = "Declared for the demonstration; not a customer target"
MG2_ZERO = "Supply cost per kWh: no generator time longer than needed"


def objective(outcome: str, measure: str, target: str, currency: str | None = None, rid: str = "r1") -> dict:
    return {"id": uuid5(NAMESPACE_URL, f"{outcome}/{rid}"), "outcome_key": outcome, "measure_key": measure,
            "target": Decimal(target), "currency": currency, "source": "DECLARED", "source_note": NOTE}


KOBO_OBJECTIVES = [objective("MG-2", "avoidable_generator_minutes", "0"),
                   objective("MG-1", "productive_use_kwh", "300"),
                   objective("MG-5", "unserved_critical_kwh", "0")]


def dispatch(candidate: str, indeterminate: str) -> dict:
    return {"intervals": [{"result": {"portions_minutes": {"candidate": candidate, "necessary": "0",
                                                            "indeterminate": indeterminate}}}]}


def run_mini(fake: b2.Fake | None = None, rows: Any = KOBO_OBJECTIVES):
    ports = (fake or b2.Fake()).ports()
    ports = replace(ports, objectives=rows if callable(rows) else (lambda: rows))
    comp = mini.compose(ports, site_code=b2.C, day=b2.DAY, site_timezone=b2.ZONE)
    return comp, {r["category"]: r for r in checked(assemble(comp.facts))}


def declared(row: dict) -> list[dict]:
    return [c for c in row["contributors"] if c["label"] == "Declared objective"]


def state(row: dict, key: str) -> tuple[str, str]:
    return next((o["state"], o["reason"]) for o in row["outcomes"] if o["key"] == key)


def no_finding() -> b2.Fake:
    return b2.Fake(chain_findings=(),
                   estate={"site_cov": {"state": "CURRENT"}, "findings": [], "actions": []},
                   action_index={"rows": [], "next_cursor": None})


# ---------------------------------------------------------------- mini

def test_kobo_mg2_missed_keeps_the_finding_reason_first() -> None:
    comp, rows = run_mini(b2.Fake(dispatch=dispatch("12", "0")))
    assert comp.read_state == "AVAILABLE"
    assert rows[COST]["state"] == "NEEDS_ATTENTION"
    assert state(rows[COST], "MG-2") == ("NEEDS_ATTENTION", "PRIMARY_FINDING_OPEN")  # rule 4a before 4c
    [line] = declared(rows[COST])
    assert line == {"key": "declared_objective:MG-2", "label": "Declared objective",
                    "text": f"{MG2_ZERO} · 12 min longer than needed on this day",
                    "confidence": {"label": "Missed", "tone": "amber"}, "href": None}
    assert rows[COST]["contributors"][-1] == line  # after the domain contributors


def test_mg2_missed_without_a_finding_is_rule_4c() -> None:
    _, rows = run_mini(replace_fake(no_finding(), dispatch=dispatch("12", "5")))
    assert state(rows[COST], "MG-2") == ("NEEDS_ATTENTION", "OBJECTIVE_MISSED")  # a miss needs no complete window


def replace_fake(fake: b2.Fake, **over: Any) -> b2.Fake:
    fake.over.update(over)
    return fake


def test_mg2_zero_minutes_complete_is_on_track() -> None:
    _, rows = run_mini(replace_fake(no_finding(), dispatch=dispatch("0", "0")))
    assert state(rows[COST], "MG-2") == ("ON_TRACK", "OBJECTIVE_MET")
    [line] = declared(rows[COST])
    assert line["text"] == f"{MG2_ZERO} · 0 min longer than needed on this day"
    assert line["confidence"] == {"label": "Met", "tone": "green"}


def test_mg2_unclear_minutes_are_not_checked_yet() -> None:
    _, rows = run_mini(replace_fake(no_finding(), dispatch=dispatch("0", "7")))
    assert state(rows[COST], "MG-2") == ("UNKNOWN", "OBJECTIVE_NOT_JUDGED")
    [line] = declared(rows[COST])
    assert line["text"] == f"{MG2_ZERO} · 7 min not yet clear on this day"
    assert line["confidence"] == {"label": "Not checked yet", "tone": "gray"}


def test_mg1_with_headroom_is_unknown_with_the_opportunity_as_potential() -> None:
    _, rows = run_mini()
    # WALK1-3b §A2.1: the declared MG-1 objective (no readings: not judged) sets the state; spare solar is potential
    assert rows[GROW]["state"] == "UNKNOWN" and state(rows[GROW], "MG-1")[0] == "UNKNOWN"
    assert rows[GROW]["potential"] == {"label": "Opportunity", "text": "Productive-use headroom"}
    [line] = declared(rows[GROW])
    assert line["text"] == ("Productive electricity sales: at least 300 kWh sold for productive use a month · "
                            "sales not recorded")
    assert line["confidence"]["label"] == "Not checked yet"


def test_mg5_unmeasured_and_measured() -> None:
    _, rows = run_mini()
    [line] = [c for r in rows.values() for c in declared(r) if c["key"] == "declared_objective:MG-5"]
    assert line["text"] == "Reliable service: all critical demand served · critical demand not measured"
    cards = {**b2.DEPTH, "service": {**b2.DEPTH["service"], "unserved_kwh": "3.0"}}
    _, rows = run_mini(b2.Fake(cards=cards))
    [line] = [c for r in rows.values() for c in declared(r) if c["key"] == "declared_objective:MG-5"]
    assert line["text"] == "Reliable service: all critical demand served · 3 kWh not served"
    assert line["confidence"]["label"] == "Missed"


def test_mini_assure_counts_declared_objectives() -> None:
    _, rows = run_mini(replace_fake(no_finding(), dispatch=dispatch("0", "0")))
    plan = next(c for c in rows[ASSURE]["contributors"] if c["key"] == "actual_against_plan")
    assert plan == {"key": "actual_against_plan", "label": "Actual against plan",
                    "text": "1 of 3 declared objectives met · 2 not checked yet", "confidence": None, "href": None}
    _, rows = run_mini(rows=[])
    plan = next(c for c in rows[ASSURE]["contributors"] if c["key"] == "actual_against_plan")
    assert plan["text"] == mini.FIXED["plan_target"]  # no objective: unchanged
    assert declared(rows[COST]) == [] and state(rows[COST], "MG-2")[0] != "ON_TRACK"


def test_failed_objectives_read_is_partial_and_never_no_objective() -> None:
    def boom() -> list:
        raise RuntimeError("objective store down")

    comp, rows = run_mini(rows=boom)
    assert comp.read_state == "PARTIAL" and "objectives" in comp.failed
    assert all(declared(r) == [] for r in rows.values())
    states = [o for r in rows.values() for o in r["outcomes"]]
    assert all(o["state"] != "NO_OBJECTIVE" for o in states)
    assert ("UNKNOWN", "OBJECTIVES_NOT_READ") in {(o["state"], o["reason"]) for o in states}
    _, base = run_mini(rows=[])
    assert any(o["state"] == "NO_OBJECTIVE" for r in base.values() for o in r["outcomes"])  # non-vacuous


def test_failed_objectives_read_never_says_no_target_declared() -> None:
    """Review M1: the Assure line makes no claim about targets when the store was never read."""
    def boom() -> list:
        raise RuntimeError("objective store down")

    comp, rows = run_mini(rows=boom)
    plan = next(c for c in rows[ASSURE]["contributors"] if c["key"] == "actual_against_plan")
    assert plan == {"key": "actual_against_plan", "label": "Actual against plan",
                    "text": "Not available yet · declared objectives could not be loaded", "confidence": None,
                    "href": None}
    assert plan["text"] == mini.PLAN_NOT_READ and mini.PLAN_NOT_READ in mini.COPY
    texts = _texts(rows)
    assert not [t for t in texts if "no target declared" in t]
    assert any("no target declared" in t for t in _texts(run_mini(rows=[])[1]))  # non-vacuous


def test_unsettled_outcome_has_no_verdict() -> None:
    comp, rows = run_mini(b2.Fake(refuse=("dispatch",)))
    assert state(rows[COST], "MG-2")[0] == "UNKNOWN"
    wire = {o["outcome_key"]: o for o in objectives_wire(comp.facts)}
    assert wire["MG-2"]["verdict"] is None
    [line] = declared(rows[COST])
    assert line["text"] == MG2_ZERO and line["confidence"]["label"] == "Not checked yet"


def test_board_wire_objectives_and_policy() -> None:
    comp, _ = run_mini(b2.Fake(dispatch=dispatch("12", "0")))
    assert read.POLICY_VERSIONS["objectives"] == POLICY == "outcome-objectives/2"
    assert [(o["outcome_key"], o["outcome_label"], o["source"], o["verdict"]) for o in objectives_wire(comp.facts)] == [
        ("MG-1", "Productive electricity sales", "DECLARED", "NOT_JUDGED"),
        ("MG-2", "Supply cost per kWh", "DECLARED", "MISSED"),
        ("MG-5", "Reliable service", "DECLARED", "NOT_JUDGED")]
    assert all(o["revision_id"] for o in objectives_wire(comp.facts))
    assert {o["source_note"] for o in objectives_wire(comp.facts)} == {NOTE}  # review L1: wire data only
    assert not [t for t in _texts(run_mini(b2.Fake(dispatch=dispatch("12", "0")))[1]) if NOTE in t]


# ---------------------------------------------------------------- cold

def run_cold(rows: list, overview: dict | None = None):
    fake = b3.Fake(**({"cold_overview": overview} if overview is not None else {}))
    ports = replace(b3.cold_ports(fake), objectives=lambda: rows)
    comp = cold.compose(ports, site_code=b3.C, lo=b3.LO, hi=b3.HI, site_timezone=b3.ZONE)
    return comp, {r["category"]: r for r in checked(assemble(comp.facts))}


def test_cc1_reads_the_chamber_range_only() -> None:
    comp, rows = run_cold([])
    [cc1] = comp.facts.objectives
    assert (cc1.outcome_key, cc1.revision_id, cc1.source) == ("CC-1", None, "DECLARED")
    lines = declared(rows[PROTECT])
    assert [c["key"] for c in lines] == ["declared_objective:CC-1"]
    assert lines[0]["text"] == "Stock kept saleable: chamber held between 2 and 5°C · above 5°C in this window"
    assert lines[0]["confidence"]["label"] == "Missed"
    no_policy = dict(b3.COLD_OVERVIEW, objective={"policy_low_deg_c": None, "policy_high_deg_c": "5"})
    comp, rows = run_cold([], no_policy)
    assert comp.facts.objectives == () and declared(rows[PROTECT]) == []
    assert objectives_wire(run_cold([])[0].facts)[0]["source_note"] is None


def test_cc1_on_track_with_no_excursion_and_a_complete_window() -> None:
    """Review extra: a cold board with no excursion and a complete window reaches On track through CC-1."""
    held = dict(b3.COLD_OVERVIEW, needs_attention=[],
                backup_summary={"attempts": 1, "observed_success": 1, "observed_failure": 0, "unknown": 0})
    fake = b3.Fake(cold_overview=held, cold_findings={"items": [], "next_cursor": None})
    ports = replace(b3.cold_ports(fake), objectives=lambda: [])
    comp = cold.compose(ports, site_code=b3.C, lo=b3.LO, hi=b3.HI, site_timezone=b3.ZONE)
    rows = {r["category"]: r for r in checked(assemble(comp.facts))}
    assert {o["outcome_key"]: o["verdict"] for o in objectives_wire(comp.facts)} == {"CC-1": "MET"}
    [line] = declared(rows[PROTECT])
    assert line["text"] == "Stock kept saleable: chamber held between 2 and 5°C · " + cold.CC1_HELD
    assert line["confidence"]["label"] == "Met"
    assert state(rows[PROTECT], "CC-1")[0] == "ON_TRACK"


def test_cc6_declared_and_contributor_order() -> None:
    comp, rows = run_cold([objective("CC-6", "backup_start_failures", "0")])
    assert [o.outcome_key for o in comp.facts.objectives] == ["CC-1", "CC-6"]  # catalogue order
    lines = declared(rows[PROTECT])
    assert [c["text"] for c in lines] == [
        "Stock kept saleable: chamber held between 2 and 5°C · above 5°C in this window",
        "Cooling continuity: every backup start succeeds by itself · automatic start failed"]
    assert [c["confidence"]["label"] for c in lines] == ["Missed", "Missed"]
    assert rows[PROTECT]["contributors"][-2:] == lines
    held = dict(b3.COLD_OVERVIEW, needs_attention=[], backup_summary={"observed_success": 1})
    _, rows = run_cold([objective("CC-6", "backup_start_failures", "0")], held)
    assert declared(rows[PROTECT])[1]["text"].endswith(" · started by itself")


# ---------------------------------------------------------------- EV

def run_ev(rows: list):
    ports = replace(b3.ev_ports(b3.Fake()), objectives=lambda: rows)
    comp = ev.compose(ports, site_code=b3.E, lo=b3.LO, hi=b3.HI, site_timezone=b3.ZONE)
    return comp, {r["category"]: r for r in checked(assemble(comp.facts))}


def test_ev1_missed_and_ev2_has_no_line() -> None:
    comp, rows = run_ev([objective("EV-1", "interrupted_sessions", "0"),
                         objective("EV-2", "energy_cost_per_km", "0.20", "USD")])
    lines = [c for r in rows.values() for c in declared(r)]
    assert [c["text"] for c in lines] == [
        "Buses ready for service: no interrupted charging sessions · 1 interrupted · 1 outcome unknown"]
    assert lines[0]["confidence"]["label"] == "Missed"
    assert {o["outcome_key"] for o in objectives_wire(comp.facts)} == {"EV-1", "EV-2"}
    ev2 = next(o for r in rows.values() for o in r["outcomes"] if o["key"] == "EV-2")
    assert ev2["state"] == "NOT_MEASURED"  # R583


# ---------------------------------------------------------------- rendered text

def _texts(rows: dict) -> list[str]:
    out: list[str] = []
    for r in rows.values():
        for c in r["contributors"]:
            out += [c["label"], c["text"]] + ([c["confidence"]["label"]] if c["confidence"] else [])
        out += [r["state_label"], r.get("headline") or "", r.get("subline") or ""]
    return out


def test_no_code_on_screen_and_vocabulary() -> None:
    texts = (_texts(run_mini(b2.Fake(dispatch=dispatch("12", "0")))[1])
             + _texts(run_cold([objective("CC-6", "backup_start_failures", "0")])[1])
             + _texts(run_ev([objective("EV-1", "interrupted_sessions", "2")])[1]))
    codes = [*MEASURES, "MET", "MISSED", "NOT_JUDGED", POLICY, "excursions", "{"]
    assert [t for t in texts for code in codes if code in t] == []
    patterns = _vocabulary_patterns()
    lines = [t for t in texts if "objective" in t.lower() or " · " in t]
    assert [(t, n) for t in lines for n, p in patterns if p.search(t)] == []


# ---------------------------------------------------------------- summary

SITES = [SiteRef(UUID(int=i), UUID(int=10 + i), code, code, "MINIGRID", "UTC")
         for i, code in enumerate(("KOBO-001", "KOBO-002", "KOBO-003"))]


class Boards(SiteOutcomeBoardService):
    def __init__(self, objectives: dict[str, list | None]) -> None:
        super().__init__(BoardServices())
        self.objectives = objectives

    def board(self, site, **_: Any) -> dict:
        found = self.objectives[site.site_code]
        if found is None:
            raise RuntimeError("board failed")
        if found == "unread":  # the board loaded but the objectives read failed (review M2)
            return {"rows": [], "_short_values": {}, "read_state": "PARTIAL", "warnings": [],
                    "window": {"from": None, "to": None, "known_at": None}, "objectives": [],
                    "objectives_read": False}
        return {"rows": [], "_short_values": {}, "read_state": "AVAILABLE", "warnings": [],
                "window": {"from": None, "to": None, "known_at": None}, "objectives": found,
                "objectives_read": True}


def test_summary_objective_site_count() -> None:
    lo, hi = datetime(2026, 10, 20, tzinfo=timezone.utc), datetime(2026, 10, 21, tzinfo=timezone.utc)
    def count(o: dict) -> tuple[int | None, int]:
        body = Boards(o).summary(SITES, lo, hi)
        return body["objective_site_count"], body["objective_sites_unread"]

    mg2, mg1 = [{"outcome_key": "MG-2"}], [{"outcome_key": "MG-1"}]
    assert count({"KOBO-001": mg2, "KOBO-002": [], "KOBO-003": mg1}) == (2, 0)
    assert count({"KOBO-001": mg2, "KOBO-002": None, "KOBO-003": None}) == (1, 2)  # failed boards are unread
    assert count({"KOBO-001": [], "KOBO-002": [], "KOBO-003": []}) == (0, 0)
    assert count({"KOBO-001": None, "KOBO-002": None, "KOBO-003": None}) == (None, 3)
    # review M2: a failed objectives read is unread, never "none declared"
    assert count({"KOBO-001": "unread", "KOBO-002": "unread", "KOBO-003": "unread"}) == (None, 3)
    assert count({"KOBO-001": mg2, "KOBO-002": "unread", "KOBO-003": []}) == (1, 1)
    assert count({"KOBO-001": [], "KOBO-002": "unread", "KOBO-003": None}) == (0, 2)
