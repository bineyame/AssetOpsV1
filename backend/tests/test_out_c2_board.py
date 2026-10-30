"""OUT-C U2: visits read, warnings on the board and the estate summary (build sheet OUT-C §2 U2)."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from test_out_b1_board import F104, cold as cold_facts, kobo, request, rows_by_cat
from test_out_b3_cold_ev import Fake, cold_ports
from test_out_c1_never_money import money_hits

from assetops_backend.outcomes.catalogue import CATEGORIES, COLD, MINI
from assetops_backend.outcomes.outcome_map import outcome_roles
from assetops_backend.outcomes.warnings import PlanCue, Visit, WarningFacts, evaluate
from assetops_backend.site_outcomes import cold, visits
from assetops_backend.site_outcomes.board import PlanFact, assemble
from assetops_backend.site_outcomes.mini import Reads

GROW, COST, PROTECT, ASSURE = CATEGORIES
TO = datetime(2026, 10, 21, tzinfo=timezone.utc)


# --------------------------------------------------------------- the three-window visits read

class WorkPort:
    def __init__(self, rows_by_window=None, refuse_at: int | None = None) -> None:
        self.calls: list[tuple] = []
        self.rows_by_window = rows_by_window or {}
        self.refuse_at = refuse_at

    def __call__(self, kind, lo, hi, cursor):
        self.calls.append((kind, lo, hi))
        if self.refuse_at is not None and len(self.calls) - 1 == self.refuse_at:
            raise PermissionError("refused")
        return {"rows": self.rows_by_window.get(len(self.calls) - 1, []), "next_cursor": None}


def mr(cid: str, at: datetime, state: str = "COMPLETED") -> dict:
    return {"case_id": cid, "code": cid.upper(), "title": "Visit", "state": state, "asset_id": "gen",
            "asset_label": "generator-1 · GENERATOR", "finding_links": [{"finding_id": "f118"}],
            "occurred_at": at.isoformat()}


def test_three_recorded_windows_dedupe_and_occurrence_filter() -> None:
    d = timedelta(days=1)
    port = WorkPort({0: [mr("old", TO - 60 * d), mr("older", TO - 60 * d - timedelta(seconds=1))],
                     1: [mr("a", TO - 5 * d), mr("old", TO - 60 * d)],
                     2: [mr("late", TO - 2 * d), mr("future", TO)]})
    reads = Reads()
    got = visits.maintenance_cases(reads, port, "C", TO)
    assert port.calls == [("maintenance", TO - 62 * d, TO - 31 * d), ("maintenance", TO - 31 * d, TO),
                          ("maintenance", TO, TO + 31 * d)]
    assert sorted(c.case_id for c in got) == ["a", "late", "old"]  # deduped; at to-60 d in, before it and at to out
    assert reads.failed == []


def test_any_refused_window_is_none_and_named_work_index() -> None:
    for i in range(3):
        reads = Reads()
        assert visits.maintenance_cases(reads, WorkPort(refuse_at=i), "C", TO) is None
        assert reads.failed == ["work_index"]


def test_refused_visit_read_is_partial_and_cc3_unknown() -> None:
    fake = Fake(refuse=())
    ports = cold_ports(fake)
    calls = {"n": 0}

    def work(kind, lo, hi, cur):
        if kind == "maintenance":
            calls["n"] += 1
            if calls["n"] == 3:
                raise PermissionError("refused")
        return ports.work(kind, lo, hi, cur)
    comp = cold.compose(replace(ports, work=work), site_code="C", lo=TO - timedelta(days=1), hi=TO,
                        site_timezone="Africa/Nairobi")
    rows = {r["category"]: r for r in assemble(comp.facts)}
    assert comp.read_state == "PARTIAL" and "work_index" in comp.failed
    assert rows[COST]["state"] == "UNKNOWN"
    assert [o["state"] for o in rows[COST]["outcomes"]] == ["UNKNOWN"]


def test_composer_settles_cc3_with_visits_and_findings() -> None:
    comp = cold.compose(cold_ports(Fake()), site_code="C", lo=TO - timedelta(days=1), hi=TO,
                        site_timezone="Africa/Nairobi")
    assert comp.facts.settled["CC-3"] is True
    comp = cold.compose(cold_ports(Fake(refuse=("cold_findings",))), site_code="C", lo=TO - timedelta(days=1),
                        hi=TO, site_timezone="Africa/Nairobi")
    assert comp.facts.settled["CC-3"] is False


# --------------------------------------------------------------- board with warnings (pure)

F118_KEYS = sum(outcome_roles("FINDING:COLD_START_FAILURE", COLD), ())


def repeat_warning(case_ids=("mr1", "mr2"), finding_href="/sites/COLD-LAB-001/findings/f118"):
    vs = tuple(Visit(cid, cid.upper(), "gen", "generator-1", "COMPLETED", TO - timedelta(days=9 - i),
                     (TO - timedelta(days=9 - i)).date(), ("f118",), f"/maintenance/requests/{cid}")
               for i, cid in enumerate(case_ids))
    return evaluate(WarningFacts(COLD, "COLD-LAB-001", TO, TO - timedelta(days=60), TO + timedelta(days=14),
                                 (date(2026, 10, 20),) * 2, visits=vs,
                                 open_findings={"f118": (F118_KEYS, finding_href)}))


def plan_warnings(due: datetime, pid: str = "p1"):
    cue = PlanCue(pid, "PM-1", "Witnessed backup start test", due, due.date(), "gen")
    return evaluate(WarningFacts(COLD, "COLD-LAB-001", TO, TO - timedelta(days=60), TO + timedelta(days=14),
                                 (date(2026, 10, 20),) * 2, plans=(cue,)))


def test_warning_sets_status_through_moves_only() -> None:
    (w,) = repeat_warning()
    rows = rows_by_cat(cold_facts(warnings=(w,)))
    assert rows[COST]["state"] == "NEEDS_ATTENTION"
    assert rows[COST]["lead_outcome"]["key"] == "CC-3"
    # the CHECKED role (Protect outcomes) sets nothing: Protect keeps its Finding-driven state and reasons
    base = rows_by_cat(cold_facts())
    assert [o["reason"] for o in rows[PROTECT]["outcomes"]] == [o["reason"] for o in base[PROTECT]["outcomes"]]


def test_needs_attention_beats_watch() -> None:
    (rw,) = repeat_warning()
    (pw,) = plan_warnings(TO - timedelta(days=4))
    rows = rows_by_cat(cold_facts(warnings=(rw, pw)))
    assert rows[COST]["state"] == "NEEDS_ATTENTION"
    plan_only = rows_by_cat(cold_facts(findings=(), cases=(), warnings=(pw,)))
    assert plan_only[PROTECT]["state"] == "WATCH"
    cc5 = next(o for o in plan_only[PROTECT]["outcomes"] if o["key"] == "CC-5")
    assert (cc5["state"], cc5["reason"]) == ("WATCH", "WARNING_WATCH")


def test_issue_order_findings_signals_checked_findings_then_warnings() -> None:
    (rw,) = repeat_warning()
    (pw,) = plan_warnings(TO - timedelta(days=4))
    rows = rows_by_cat(cold_facts(warnings=(rw, pw)))
    issues = [(i["kind"], i["role"], i["text"]) for i in rows[PROTECT]["issues"]]
    assert issues[-2:] == [("EARLY_WARNING", "MOVES", "Witnessed backup start test overdue"),
                           ("RISK", "CHECKED", "Repeated maintenance without a result")]
    assert all(k == "FINDING" for k, _, _ in issues[:-2])
    cost = rows[COST]["issues"]
    assert [(i["kind"], i["role"]) for i in cost] == [("FINDING", "CHECKED"), ("RISK", "MOVES")]
    assert cost[-1]["ref"] == rw.key and cost[-1]["href"] == "/maintenance/requests/mr2"
    for r in rows.values():
        assert r["counts"]["issues"] == len(r["issues"])


def test_repeat_visits_are_also_placed_in_cost() -> None:
    (w,) = repeat_warning()
    cases = (request("mr1", "COMPLETED", 11), request("mr2", "COMPLETED", 12))
    rows = rows_by_cat(cold_facts(cases=cases, warnings=(w,)))
    cost = [(e["text"].split(" · ")[0], e["result_label"]) for e in rows[COST]["earlier"]]
    assert cost == [("MR1", "Did not fix it"), ("MR2", "Not yet verified")]
    protect = [e["text"].split(" · ")[0] for e in rows[PROTECT]["earlier"]]
    assert protect == ["MR1", "MR2"]  # B's placement kept
    assert rows_by_cat(cold_facts(cases=cases))[COST]["earlier"] == []


def test_plan_state_labels_from_due_cue() -> None:
    plan = PlanFact("p1", "PM-1", "Witnessed backup start test", "CALENDAR", date(2026, 10, 17), None, "DRAFT",
                    "gen", "/maintenance/preventive", TO - timedelta(days=4))
    other = PlanFact("p2", "PM-2", "Coil", "CALENDAR", date(2026, 12, 1), None, "DRAFT", "cmp",
                     "/maintenance/preventive", datetime(2026, 12, 1, tzinfo=timezone.utc))
    (od,) = plan_warnings(TO - timedelta(days=4))
    (soon,) = plan_warnings(TO + timedelta(days=4))
    labels = lambda ws: [i["state_label"] for i in rows_by_cat(cold_facts(plans=(plan, other), warnings=ws))[
        PROTECT]["in_hand"] if i["text"].startswith("PM-")]
    assert labels((od,)) == ["Overdue", "Due 1 Dec"]
    assert labels((soon,)) == ["Due soon", "Due 1 Dec"]
    assert labels(()) == ["Due 17 Oct", "Due 1 Dec"]


def test_must_not_harm_for_repeat_warning() -> None:
    (w,) = repeat_warning()
    rows = rows_by_cat(cold_facts(warnings=(w,)))
    assert rows[COST]["must_not_harm"] == {
        "text": "Cooling continuity, stock kept saleable and compressor life: a repair counts only when the fault "
                "it answers stops", "href": "/sites/COLD-LAB-001/findings/f118"}
    assert rows[PROTECT]["must_not_harm"] is None  # the warning only checks Protect
    assert rows_by_cat(cold_facts())[COST]["must_not_harm"] is None


def test_mini_warning_rows() -> None:
    (w,) = evaluate(WarningFacts(MINI, "KOBO-001", TO, TO - timedelta(days=60), TO + timedelta(days=14),
                                 (date(2026, 10, 20),) * 2, reserve=(2, 3)))
    rows = rows_by_cat(kobo(warnings=(w,)))
    assert rows[PROTECT]["state"] == "WATCH"
    assert [(i["kind"], i["text"]) for i in rows[PROTECT]["issues"]][-1] == (
        "EARLY_WARNING", "Battery at or near its reserve")
    assert rows_by_cat(kobo())[PROTECT]["state"] == "NO_OBJECTIVE"
    assert F104.open


# --------------------------------------------------------------- wire and summary

def test_board_and_summary_wire(monkeypatch) -> None:
    from types import SimpleNamespace

    from test_out_b4_read import COLD as COLD_SITE, KOBO, ODD

    from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService

    (rw,) = repeat_warning()
    (pw,) = plan_warnings(TO - timedelta(days=4))
    (bw,) = evaluate(WarningFacts(MINI, "KOBO-001", TO, TO - timedelta(days=60), TO + timedelta(days=14),
                                  (date(2026, 10, 20),) * 2, reserve=(2, 3)))
    facts = {"COLD-LAB-001": cold_facts(warnings=(rw, pw)), "KOBO-001": kobo(warnings=(bw,))}

    def compose(self, site, **kw):
        if site.site_code not in facts:
            raise RuntimeError("no composer")
        comp = SimpleNamespace(facts=facts[site.site_code], read_state="AVAILABLE", short_values={})
        return comp, {"from": TO - timedelta(days=1), "to": TO, "known_at": None}

    monkeypatch.setattr(SiteOutcomeBoardService, "compose", compose)
    svc = SiteOutcomeBoardService(BoardServices())
    body = svc.board(COLD_SITE)
    assert body["policy_versions"]["warnings"] == "early-warnings/1"
    assert body["policy_versions"]["catalogue"] == "outcome-catalogue/2"
    assert [w["kind"] for w in body["warnings"]] == ["REPEATED_MAINTENANCE_NO_RESULT", "PLAN_OVERDUE"]
    w = body["warnings"][0]
    assert set(w) == {"key", "kind", "badge", "badge_label", "lens", "title", "seen", "persistence",
                      "persistence_label", "price_needs", "status_effect", "categories", "site_code", "site_name",
                      "href", "evidence_refs", "count", "subject_label", "fault_name"}
    assert (w["site_code"], w["site_name"]) == ("COLD-LAB-001", "GreenHarvest")
    assert money_hits(body["warnings"]) == []

    out = svc.summary([KOBO, COLD_SITE, ODD], TO - timedelta(days=1), TO)
    assert [x["key"] for x in out["warnings"]] == [bw.key, rw.key, pw.key]  # Site order, then evaluate order
    counts = {c["category"]: c["warning_count"] for c in out["categories"]}
    # battery: Protect; repeat: Cost moves + Protect checked; plan: Protect
    assert counts == {GROW: 0, COST: 1, PROTECT: 3, ASSURE: 0}
    assert out["sites"][2]["read_state"] == "UNAVAILABLE"


def test_visits_without_occurrence_are_dropped() -> None:
    """Ruling L3: the composer drops a visit with no `occurred_at` (read and fact derivation)."""
    row = dict(mr("none", TO - timedelta(days=3)), occurred_at=None)
    port = WorkPort({1: [row, mr("a", TO - timedelta(days=3))]})
    got = visits.maintenance_cases(Reads(), port, "C", TO)
    assert [c.case_id for c in got] == ["a"]
    case = replace(request("mr9", "COMPLETED", 5), occurred_at=None)
    wf = visits.warning_facts(cold_facts(cases=(case, request("mr1", "COMPLETED", 5))), to=TO, tz=None, suffix="",
                              lo=TO - timedelta(days=1))
    assert [v.case_id for v in wf.visits] == ["mr1"]
