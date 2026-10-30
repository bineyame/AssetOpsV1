"""OUT-C U3: the GreenHarvest Cost row from fake ports (build sheet OUT-C §2 U3); the Postgres check is
`test_out_c3_repeat_visits_postgres.py`."""
from __future__ import annotations

from dataclasses import replace

from test_out_b3_cold_ev import C, HI, LO, MR5, T, Fake, cold_ports, contributor

from assetops_backend.site_outcomes import cold
from assetops_backend.site_outcomes.board import assemble

COST, PROTECT = cold.COST, cold.PROTECT
E1 = dict(MR5, case_id="e1", code="MR-1", occurred_at=T(9, 0, 2))
E2 = dict(MR5, case_id="e2", code="MR-2", occurred_at=T(9, 0, 12))


def run(rows, fake: Fake | None = None, tz: str | None = "Africa/Nairobi", plans=None):
    ports = cold_ports(fake or Fake())
    work = lambda kind, lo, hi, cur: {"rows": list(rows) if kind == "maintenance" else [], "next_cursor": None}
    ports = replace(ports, work=work, **({"plans": lambda lo, hi: plans} if plans is not None else {}))
    comp = cold.compose(ports, site_code=C, lo=LO, hi=HI, site_timezone=tz)
    return comp, {r["category"]: r for r in assemble(comp.facts)}


def test_repeat_visits_fill_the_cost_row() -> None:
    comp, rows = run([E1, E2, MR5])
    cost = rows[COST]
    assert cost["state"] == "NEEDS_ATTENTION" and cost["lead_outcome"]["key"] == "CC-3"
    assert cost["headline"] == "3 repair visits in 60 days without a result"
    assert cost["subline"] == ("None of the visits has fixed the automatic start failure yet; repair cost is not "
                               "recorded")
    eff = contributor(cost, "maintenance_effectiveness")
    assert eff["text"] == "3 visits (2 Oct, 12 Oct, 20 Oct); the automatic start failure is still open"
    # H1-4a: the repeat warning reuses Protect's start-test option (same href)
    assert [(o["text"], o["href"]) for o in cost["options"]] == [
        ("Witnessed automatic-start test", f"/sites/{C}/actions/da1")]
    (w,) = [w for w in comp.facts.warnings if w.kind == "REPEATED_MAINTENANCE_NO_RESULT"]
    assert w.fault_name == "automatic start failure" and w.badge == "RISK"
    assert w.seen.endswith("; the automatic start failure is still open")
    assert eff["confidence"] == {"label": "Limited", "tone": "amber"} and eff["href"] == "/maintenance/requests/mr5"
    rep = contributor(cost, "repair_cost")
    assert (rep["text"], rep["confidence"], rep["href"]) == (
        "No cost on work record MR-5", {"label": "Unknown", "tone": "gray"}, f"/sites/{C}/financials")
    cool = contributor(cost, "cooling_energy")
    assert (cool["text"], cool["confidence"], cool["href"]) == (cold.NO_COOLING_METER, None, None)
    assert [e["result_label"] for e in cost["earlier"]] == ["Did not fix it", "Did not fix it", "Not yet verified"]
    assert cost["must_not_harm"]["href"] == f"/sites/{C}/findings/f118"


def test_no_repeat_and_failed_visits() -> None:
    _, rows = run([MR5])
    cost = rows[COST]
    assert cost["headline"] is None and cost["subline"] is None
    assert cost["options"] == []  # no repeat warning: nothing proposed under Cost
    assert contributor(cost, "maintenance_effectiveness")["text"] == cold.NO_REPEAT
    _, rows = run([])
    assert contributor(rows[COST], "repair_cost")["text"] == cold.NO_REPAIR_COST

    ports = cold_ports(Fake())

    def work(kind, lo, hi, cur):
        if kind == "maintenance":
            raise PermissionError("refused")
        return {"rows": [], "next_cursor": None}
    comp = cold.compose(replace(ports, work=work), site_code=C, lo=LO, hi=HI, site_timezone="Africa/Nairobi")
    rows = {r["category"]: r for r in assemble(comp.facts)}
    eff = contributor(rows[COST], "maintenance_effectiveness")
    assert (eff["text"], eff["confidence"]) == (cold.NOT_LOADED, None)
    assert rows[COST]["state"] == "UNKNOWN"


def test_utc_suffix_on_visit_dates() -> None:
    _, rows = run([E1, E2, MR5], tz=None)
    assert contributor(rows[COST], "maintenance_effectiveness")["text"] == (
        "3 visits (2 Oct, 12 Oct, 20 Oct · UTC (Site time zone unavailable)); the automatic start failure is still open")


def test_cost_subline_falls_back_without_a_fault_name() -> None:
    class W:
        fault_name = "linked finding"
    assert cold._cost_subline(W()) == cold.COST_SUBLINE
    W.fault_name = None
    assert cold._cost_subline(W()) == cold.COST_SUBLINE
    assert cold._cost_subline(None) is None


def test_overdue_plan_contributor_text() -> None:
    plans = [{"canonical_plan_id": "p1", "code": "PM-1", "title": "Witnessed backup start test",
              "trigger_kind": "CALENDAR", "next_due_at": T(0, 0, 16), "next_due_hours": None, "state": "DRAFT",
              "asset_id": "gen", "asset_label": "generator-1 · GENERATOR"}]
    _, rows = run([MR5], plans=plans)
    assert contributor(rows[PROTECT], "backup_generator")["text"] == "Witnessed backup start test overdue since 16 Oct"
    assert "Witnessed backup start test overdue" in [i["text"] for i in rows[PROTECT]["issues"]]
    assert [i["state_label"] for i in rows[PROTECT]["in_hand"] if i["text"].startswith("PM-1")] == ["Overdue"]


def test_c_copy_passes_the_vocabulary_scan() -> None:
    """Every C string a viewer reads: cold Cost copy, filled boards, and every warning's wire texts."""
    from test_out_b2_vocabulary import _patterns, _texts
    from test_out_c1_never_money import every_rule

    from assetops_backend.outcomes.warnings import BADGE_LABEL, PERSISTENCE_LABEL, PRICE_NEEDS
    patterns = _patterns()
    texts = list(cold.COPY) + list(PRICE_NEEDS.values()) + list(BADGE_LABEL.values()) + list(
        PERSISTENCE_LABEL.values())
    for rows in (run([E1, E2, MR5])[1], run([E1, E2, MR5], tz=None)[1]):
        texts += _texts(list(rows.values()), [])
    for w in every_rule():
        texts += [w.title, w.seen] + ([w.subject_label] if w.subject_label else [])
    hits = [(t, name) for t in texts for name, pat in patterns if pat.search(t)]
    assert hits == []
    assert any(pat.search("dispatch interval") for _, pat in patterns)  # non-vacuous
