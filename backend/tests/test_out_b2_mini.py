"""OUT-B2: the mini composer over fake ports (build spec §B.4 mini table; rulings B-Q6/Q10-Q14/Q17/Q18/Q22/Q23,
addendum 2). Includes M1b: every Finding a case or Action links is supplied, closed heads included.
CH-5a1: the fakes are the ChainReader ports (`chain/read.py` `DayFacts`, `FindingHead`, `ActionFacts`,
`MoneyHead`); the overview, Finding index, estate readiness, verification/action and Finding-history ports are gone
(§A4). Old override -> new: `overview` -> `source` / `day` (settled) / dispatch `limitations` / `money_head`;
`finding_index` -> `chain_findings` / `findings_settled` / `day` gaps; `readiness` -> `day` readiness;
`verification` + `action` -> `action_facts`. Expected values changed only per §A6 E1-E5, named at each test."""
from __future__ import annotations

from link_parity import checked

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from assetops_backend.chain.read import ActionFacts, DayFacts, FindingHead, MoneyHead
from assetops_backend.site_outcomes import mini
from assetops_backend.site_outcomes.board import assemble, with_threads
from assetops_backend.site_outcomes.mini import MiniPorts, compose, limitation_text

GROW, COST, PROTECT, ASSURE = mini.GROW, mini.COST, mini.PROTECT, mini.ASSURE
DAY = date(2026, 10, 20)
ZONE = "Africa/Nairobi"  # UTC+3, no DST
C = "KOBO-001"


def legacy(items):
    """The pre-Addendum-12 item fields: case/plan items also carry `kind`/`occurred_at` (pinned in test_out_b1_board)."""
    return [{k: v for k, v in i.items() if k not in ("kind", "occurred_at", "link_ref")} for i in items]


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


T = lambda day, hour=0: datetime(2026, 10, day, hour, tzinfo=timezone.utc)  # noqa: E731
#: E4 (R6): the board day is the Site-local day [local 00:00 D, local 00:00 D+1) = [T(19, 21), T(20, 21)) at UTC+3.
LO, HI = T(19, 21), T(20, 21)

LIMITATIONS = ["EVIDENCE_GAP: interval from x is Indeterminate over a..b: PCS_CAPABILITY_UNAVAILABLE"]
INTERVALS = [{"result": {"portions_minutes": {"candidate": "30.0", "necessary": "10", "indeterminate": "12"}}},
             {"result": {"portions_minutes": {"candidate": "15", "necessary": "0", "indeterminate": "0"}}}]
#: CH5a1-R Q2: the assessment (state, limitations, claim level, intervals) comes from the dispatch body itself.
DISPATCH = {"status": "LIMITED", "limitations": LIMITATIONS, "intervals": INTERVALS}
MONEY = MoneyHead(True, "3.31", "3.97", "USD", {"state": "REGISTERED_SIMULATION"})
DEPTH = {
    "renewable": {"headroom_kw": {"low": "18", "high": "24.25"}, "eligible_days": 1, "assessed_days": 1},
    "fuel": {"opening_l": None},
    "service": {"delivered_load_kw": "11.2"},
    "backup": {"outage_count": 0, "start_success_count": None},
}


def head(fid: str, rid: str, lifecycle: str, start: datetime, end: datetime | None, no: int = 1) -> FindingHead:
    return FindingHead(fid, rid, no, lifecycle, None, start, end, "GENERATOR_SUPPORT_CANDIDATE", None)


F104 = head("f104", "f104r", "SUPPORTED", T(20, 6), T(20, 9))
F090 = head("f090", "f090r", "RETIRED", T(2, 6), T(2, 9))
#: CH-5a2b R1: `ChainRequest.placement_facts` (per revision id) and `ChainRequest.action_rows` (shaped rows).
PLACEMENT_F104 = {"f104r": {"source_state": "REGISTERED_SIMULATION", "recurs_after_finding_id": None,
                            "recurs_after_title": None}}
CHAIN_A48 = {"action_id": "a48", "application_state": "PENDING", "resolution_state": None,
             "verification_outcome": None,
             "_raw": {"_selected_recorded_at": T(19), "_verification_window": False, "_source_class": None}}
A48 = {"action_id": "a48", "action_code": "ACT-048", "origin": {"finding_id": "f104", "finding_revision_id": "f104r"},
       "selected_event": {"id": "e1"}, "state": {"application": "PENDING"},
       "links": {"selected_event": f"/sites/{C}/actions/a48?event_id=e1"}}
MR1 = {"case_id": "mr1", "code": "MR-001", "title": "Check generator stop", "state": "COMPLETED", "asset_id": "gen",
       "asset_label": "Generator", "asset_type": "GENERATOR", "finding_links": [{"finding_id": "f090"}], "occurred_at": iso(T(3))}
IN1 = {"case_id": "in1", "code": "IN-001", "title": "Feeder trip", "state": "OPEN", "asset_id": None,
       "asset_label": None, "finding_links": [{"finding_id": "f-old"}], "occurred_at": iso(T(1))}
PLANS = [{"canonical_plan_id": "p1", "code": "PM-001", "title": "Generator service", "trigger_kind": "RUN_HOURS",
          "next_due_at": None, "next_due_hours": "500.0", "state": "DRAFT", "asset_id": "gen"},
         {"canonical_plan_id": "p2", "code": "PM-002", "title": "Battery check", "trigger_kind": "CALENDAR",
          "next_due_at": iso(T(31, 22)), "next_due_hours": None, "state": "DRAFT", "asset_id": "bat"}]


class Fake:
    """Fake ports; `refuse` names the ports that raise, `calls` records every call. Overrides use the port names;
    `day` overrides `DayFacts` fields (default: settled, readiness LIMITED, no gaps), `verification` is the
    `VerificationService.summary` body `action_facts` reads (default PENDING) and `has_change` its flag (True)."""

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

        def chain_day(days, readiness_days):
            facts = replace(DayFacts(tuple(days), {}, True, "LIMITED", ()), **self.over.get("day", {}))
            return self._go("chain_day", facts, days, readiness_days)

        def opportunity(lo, hi):
            # CH9-R4 F2: the fake study mirrors the fake renewable cards unless `study` overrides it (None: no item).
            r = self.over.get("cards", DEPTH)["renewable"]
            study = self.over.get("study", {"headroom_kw": r.get("headroom_kw"), "eligible_days": r.get("eligible_days"),
                                            "assessed_days": r.get("assessed_days"), "status": "SUPPORTED"})
            ok = study is not None and int(study.get("eligible_days") or 0) >= 1
            return self._go("opportunity", [{"site_code": C, "state": "OPEN", "study": study}] if ok else [], lo, hi)

        def action_facts(ids):
            v, change = self.over.get("verification", {"state": "PENDING"}), self.over.get("has_change", True)
            return self._go("action_facts", tuple(ActionFacts(i, v.get("state"), v.get("cost_check"),
                                                              v.get("trial_hours"), change,
                                                              v.get("source_class", "REGISTERED_SIMULATION"))
                                                  for i in ids), ids)

        return MiniPorts(
            source=lambda: self._go("source", (True, "REGISTERED_SIMULATION")),
            depth=depth,
            dispatch=lambda d: self._go("dispatch", DISPATCH, d),
            assumption=lambda at: self._go("assumptions", {"selection": {"state": "PRICED", "price": {
                "value": "1.45", "currency": "USD"}}}, at),
            chain_day=chain_day,
            chain_findings=lambda lo, hi: self._go("chain_findings", (F104, F090), lo, hi),
            findings_settled=lambda: self._go("findings_settled", True),
            readings_began=lambda: self._go("readings_began", None),
            placement_facts=lambda ids: self._go("placement_facts",
                                                 {k: v for k, v in PLACEMENT_F104.items() if k in ids}, tuple(ids)),
            action_rows=lambda: self._go("action_rows", (CHAIN_A48,)),
            action_index=lambda lo, hi, cur: self._go("action_index", {"rows": [A48], "next_cursor": None}, lo, hi),
            action_facts=action_facts,
            money=lambda fid, rid, latest, src, settled: self._go("money_head", MONEY, fid, rid, latest, src, settled),
            work=lambda kind, lo, hi, cur: self._go(
                "work", {"rows": [MR1] if kind == "maintenance" else [IN1], "next_cursor": None}, kind, lo, hi),
            plans=lambda lo, hi: self._go("plans", PLANS, lo, hi),
            opportunity=opportunity,
        )


def run(fake: Fake | None = None, tz: str | None = ZONE):
    comp = compose((fake or Fake()).ports(), site_code=C, day=DAY, site_timezone=tz)
    return comp, {r["category"]: r for r in checked(assemble(comp.facts))}


def contributor(row: dict, key: str) -> dict:
    return next(c for c in row["contributors"] if c["key"] == key)


def outcome(row: dict, key: str) -> str:
    return next(o["state"] for o in row["outcomes"] if o["key"] == key)


def vocabulary_compositions():
    return [run()[0], run(Fake(refuse=("depth", "placement_facts", "action_rows", "dispatch",
                                                         "source")))[0], run(tz=None)[0]]


# --------------------------------------------------------------- happy path

def test_kobo_board_from_ports() -> None:
    comp, rows = run()
    assert comp.read_state == "AVAILABLE" and comp.failed == () and comp.timezone == ZONE
    # C: PM-002 (calendar, due 1 Nov) is due within 14 days, an early warning moving MG-4, so Protect is Watch
    assert [rows[c]["state"] for c in (GROW, COST, PROTECT, ASSURE)] == [
        "OPPORTUNITY", "NEEDS_ATTENTION", "WATCH", "WATCH"]
    assert [w.kind for w in comp.facts.warnings] == ["PLAN_DUE_SOON"]
    assert rows[GROW]["headline"] == "18–24.3 kW of daytime solar unused"
    assert contributor(rows[GROW], "productive_use")["text"] == ("Spare solar on 1 of 1 well-observed day"
                                                                " · 4 of the last 5 days not checked")
    assert rows[COST]["headline"] == "possible extra fuel cost on this day"
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
    assert contributor(rows[ASSURE], "readings")["text"] == "Example data · readiness Limited"
    assert contributor(rows[ASSURE], "battery_reporting")["text"] == "Battery output not reported"
    assert [i["text"] for i in rows[ASSURE]["issues"]] == ["Battery output not reported limits this conclusion"]
    assert [o["text"] for o in rows[ASSURE]["options"]] == ["Restore battery reporting"]
    assert rows[ASSURE]["subline"] == "Battery output not reported"


def test_depth_windows_follow_the_site_local_day() -> None:
    fake = Fake()
    run(fake)
    windows = {args[0]: args[1:] for name, args in fake.calls if name == "depth"}
    assert windows["renewable"] == (T(15, 21), T(20, 21))  # WALK1-5: local midnight 16 Oct .. 21 Oct (UTC+3)
    assert windows["service"] == windows["fuel"] == windows["backup"] == (T(20, 9), T(20, 10))  # local noon hour


def test_work_window_is_31_days_ending_with_the_day() -> None:
    fake = Fake()
    run(fake)
    # E4 (R6): the windows end at local midnight after the board day, not at UTC midnight.
    for name in ("chain_findings", "action_index", "plans"):
        args = next(a for n, a in fake.calls if n == name)
        assert args[:2] == (HI - timedelta(days=31), HI), name
    # CH-5a2b R1 (§B14 Q3): placement facts only for the heads on the Site-local board day; Action rows unbounded.
    assert next(a for n, a in fake.calls if n == "placement_facts") == (("f104r",),)
    assert next(a for n, a in fake.calls if n == "action_rows") == ()
    # CH5a1-R Q9: one snapshot read over the 31 Site-local days of the work window; readiness on the board day.
    days, ready = next(a for n, a in fake.calls if n == "chain_day")
    assert len(days) == 31 and days[-1] == DAY and ready == (DAY,)


# --------------------------------------------------------------- M1b and unresolved links (addendum 2 #4)

def test_every_linked_finding_is_supplied_closed_included() -> None:
    comp, rows = run()
    ids = {f.finding_id: f for f in comp.facts.findings}
    assert set(ids) == {"f104", "f090"}  # both index pages, closed head included
    assert ids["f104"].in_window and not ids["f090"].in_window
    linked = {a.origin_finding_id for a in comp.facts.actions} | {
        fid for case in comp.facts.cases if case.case_id == "mr1" for fid in case.finding_ids}
    assert linked <= set(ids)
    assert legacy(rows[COST]["earlier"]) == [{"text": "MR-001 · Check generator stop", "href": "/maintenance/requests/mr1",
                                      "result_label": "Not yet verified", "detail": None}]
    assert not [i for i in rows[COST]["issues"] if i["ref"] and i["ref"]["finding_id"] == "f090"]


def test_unresolved_link_is_kept_and_recorded_not_on_the_wire() -> None:
    comp, rows = run()
    assert comp.diagnostics == (("in1", "f-old"),)
    assert {"text": "IN-001 · Feeder trip", "href": f"/sites/{C}/work/incidents",
            "state_label": "Open · linked finding outside this view"} in legacy(rows[PROTECT]["in_hand"])
    assert "diagnostics" not in str(rows) and "f-old" not in str(rows)


def test_out_of_window_finding_drives_no_issue() -> None:
    later = replace(F104, episode_start=T(10, 6), episode_end=T(10, 9))
    fake = Fake(chain_findings=(later, F090))
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
    plan = next(i for i in rows[PROTECT]["in_hand"] if i["text"] == "PM-002 · Battery check")
    assert plan["state_label"] == "Due soon"  # C: the due cue fires; its date moves to the warning
    assert [w.seen for w in comp.facts.warnings] == ["Due 31 Oct · UTC (Site time zone unavailable)"]
    ok_comp, ok = run()
    assert next(i for i in ok[PROTECT]["in_hand"] if i["text"] == "PM-002 · Battery check")["state_label"] == "Due soon"
    assert [w.seen for w in ok_comp.facts.warnings] == ["Due 1 Nov"]


def test_one_depth_domain_refused_is_partial_and_unsettles() -> None:
    comp, rows = run(Fake(refuse=("depth:backup",)))
    assert comp.read_state == "PARTIAL" and outcome(rows[GROW], "MG-1") == "UNKNOWN"
    assert contributor(rows[PROTECT], "backup_readiness")["text"] == mini.NOT_LOADED


def test_missing_site_zone_skips_depth() -> None:
    fake = Fake()
    comp, rows = run(fake, tz=None)
    assert not [c for c in fake.calls if c[0] == "depth"] and "mini_depth" in comp.failed
    assert outcome(rows[GROW], "MG-1") == "UNKNOWN"


def test_dispatch_refusal_unsettles_the_measured_outcomes() -> None:
    """CH5a1-R Q2: `base = source_open and day.settled and dispatch is not None`. The overview's assessment was the
    dispatch read (`site_overview/read.py:347-379`), so a dispatch failure was an overview failure; the fake used
    to refuse them separately (MG-2 only). Now the dispatch read is the assessment itself."""
    comp, rows = run(Fake(refuse=("dispatch",)))
    assert comp.read_state == "PARTIAL"
    assert outcome(rows[COST], "MG-2") == "UNKNOWN" and outcome(rows[GROW], "MG-1") == "UNKNOWN"
    assert contributor(rows[COST], "generator_use")["text"] == mini.NOT_LOADED
    assert rows[COST]["subline"] is None


def test_chain_row_refusal_labels_not_loaded_and_nulls_confidence() -> None:
    """CH5a2b-R Q4: each R1 port's failure is named in `reads.failed` with the old estate notice behaviour."""
    comp, rows = run(Fake(refuse=("placement_facts", "action_rows")))
    assert comp.read_state == "PARTIAL" and comp.failed == ("placement_facts", "action_rows")
    assert rows[COST]["in_hand"][0]["state_label"] == mini.NOT_LOADED
    assert contributor(rows[COST], "generator_use")["confidence"] is None
    assert rows[COST]["state"] == "NEEDS_ATTENTION"  # degrade-only: no UNKNOWN


def test_degrade_only_ports_never_set_unknown() -> None:
    for port in ("work", "plans", "assumptions", "action_facts", "action_index"):  # CH-5a1 C6: one action read
        comp, rows = run(Fake(refuse=(port,)))
        assert comp.read_state == "PARTIAL", port
        # C: Protect is Watch from the PM-002 due cue unless the plan read itself is refused
        assert [rows[c]["state"] for c in (GROW, COST, PROTECT)] == [
            "OPPORTUNITY", "NEEDS_ATTENTION", "NO_OBJECTIVE" if port == "plans" else "WATCH"], port
    _, rows = run(Fake(refuse=("assumptions",)))
    assert contributor(rows[COST], "fuel_price")["text"] == mini.NOT_LOADED
    _, rows = run(Fake(refuse=("plans",)))
    assert contributor(rows[PROTECT], "generator")["text"] == mini.NOT_LOADED


def _assert_finding_source_unsettled(comp, rows) -> None:
    """Addendum 3 M1: MG-2 UNKNOWN, PARTIAL, the could-not-be-loaded suffix, and no outside-view suffix."""
    assert comp.read_state == "PARTIAL" and "chain_findings" in comp.failed
    assert outcome(rows[COST], "MG-2") == "UNKNOWN"
    assert outcome(rows[GROW], "MG-1") == "OPPORTUNITY"  # only the outcomes a mini Finding mechanism moves
    assert not comp.facts.findings_settled
    loaded = " · Not available yet · linked finding could not be loaded"
    assert {"text": "ACT-048", "href": f"/sites/{C}/actions/a48?event_id=e1",
            "state_label": "Pending" + loaded} in rows[PROTECT]["in_hand"]
    assert {"text": "IN-001 · Feeder trip", "href": f"/sites/{C}/work/incidents",
            "state_label": "Open" + loaded} in legacy(rows[PROTECT]["in_hand"])
    assert {"text": "MR-001 · Check generator stop", "href": "/maintenance/requests/mr1",
            "result_label": "Not yet verified" + loaded, "detail": None} in legacy(rows[PROTECT]["earlier"])
    assert "outside this view" not in str(rows)
    assert ("a48", "f104") in comp.diagnostics and ("in1", "f-old") in comp.diagnostics


def test_refused_finding_heads_unsettle_finding_outcomes() -> None:
    """Negative control of test_degrade_only_ports_never_set_unknown: the Finding source is a status producer."""
    _assert_finding_source_unsettled(*run(Fake(refuse=("chain_findings",))))
    _assert_finding_source_unsettled(*run(Fake(refuse=("findings_settled",), chain_findings=())))


#: IDX-GAPS U2: the 31 requested days of the board's Finding window, ending on the board day DAY.
REQUESTED = [(DAY - timedelta(days=30 - n)).isoformat() for n in range(31)]


def test_unsettled_findings_unsettle_finding_outcomes() -> None:
    """R8: an unconsumed Finding event leaves the Findings unsettled (the index's PENDING/STALE/FAILED bodies)."""
    _assert_finding_source_unsettled(*run(Fake(findings_settled=False, chain_findings=())))  # the index's rows []


def test_gap_line_names_the_gap_days_by_day_grade() -> None:
    """E3 (R8 / CH5a1-R Q9): the gap line names the work-window days whose day grade is NO_DATA or PENDING; it no
    longer gates settlement (R8 does), and `withheld` is always False (CH5a1-R Q4)."""
    every = tuple(date.fromisoformat(d) for d in REQUESTED)
    comp, rows = run(Fake(day={"gaps": every}))
    assert comp.facts.findings_settled and outcome(rows[COST], "MG-2") == "NEEDS_ATTENTION"
    assert comp.facts.finding_gaps == {"text": "31 of the last 31 days have no checked readings yet",
                                       "days": REQUESTED, "withheld": False}
    two = every[:2]
    comp, _ = run(Fake(day={"gaps": two}))
    assert comp.facts.finding_gaps == {"text": "2 of the last 31 days have no checked readings yet",
                                       "days": REQUESTED[:2], "withheld": False}
    pending = {two[1]: {"generator_runtime": {"gen": "PENDING"}}}
    comp, _ = run(Fake(day={"gaps": two, "grades": pending}))
    assert comp.facts.finding_gaps["text"] == "Not available yet · 2 of 31 days are not assessed yet"
    assert run()[0].facts.finding_gaps is None


def test_pb7_gap_line_counts_from_the_first_accepted_reading() -> None:
    """PB-7: the board reads the Site's first accepted reading; the count runs from its Site-local day."""
    every = tuple(date.fromisoformat(d) for d in REQUESTED)
    began = datetime.combine(every[20], datetime.min.time(), tzinfo=ZoneInfo(ZONE)) + timedelta(hours=6)
    comp, _ = run(Fake(day={"gaps": every}, readings_began=began))
    assert comp.facts.finding_gaps == {
        "text": f"Since readings began on {every[20].day} {every[20]:%b}: 11 of 11 days have no checked readings yet",
        "days": REQUESTED[20:], "withheld": False}
    early = datetime.combine(every[0], datetime.min.time(), tzinfo=ZoneInfo(ZONE)) - timedelta(days=40)
    comp, _ = run(Fake(day={"gaps": every[:2]}, readings_began=early))
    assert comp.facts.finding_gaps["text"] == "2 of the last 31 days have no checked readings yet"


def test_unsettled_board_day_unsettles_measured_outcomes() -> None:
    """R4 / CH5a1-R Q2: an unsettled board day (the overview's not-CURRENT freshness) unsettles `base`."""
    _, rows = run(Fake(day={"settled": False}))
    for key, cat in (("MG-1", GROW), ("MG-2", COST), ("MG-5", PROTECT), ("MG-7", ASSURE)):
        assert outcome(rows[cat], key) == "UNKNOWN", key


def test_missing_action_row_is_partial_and_recorded() -> None:
    """Addendum 3 L3, CH5a2b-R Q4: `action_rows` succeeds but lacks the Action, so the text and the notice agree."""
    comp, rows = run(Fake(action_rows=()))
    assert comp.read_state == "PARTIAL" and comp.failed == ("action_rows",)
    assert ("a48", mini.ACTION_ROW_MISSING) in comp.diagnostics
    assert rows[COST]["in_hand"][0]["state_label"] == mini.NOT_LOADED
    assert mini.ACTION_ROW_MISSING not in str(rows)
    _, chip = run(Fake(placement_facts={}))
    assert contributor(chip[COST], "generator_use")["confidence"] is None  # no facts: a null chip, no failure


def test_source_or_day_refusal_or_closed_source_unsettles_everything_measured() -> None:
    """The overview read's three cases on the reads that replace it (CH5a1-R Q2): refused, stale, CLOSED."""
    for port in ("source", "chain_day"):
        comp, rows = run(Fake(refuse=(port,)))
        assert comp.read_state == "PARTIAL" and port in comp.failed, port
        for key, cat in (("MG-1", GROW), ("MG-2", COST), ("MG-5", PROTECT), ("MG-7", ASSURE)):
            assert outcome(rows[cat], key) == "UNKNOWN", (port, key)
    _, rows = run(Fake(day={"settled": False}))
    assert outcome(rows[COST], "MG-2") == "UNKNOWN"
    _, rows = run(Fake(source=(False, "CLOSED")))
    assert outcome(rows[COST], "MG-2") == "UNKNOWN"


def test_unknown_readiness_unsettles_mg7() -> None:
    _, rows = run(Fake(day={"readiness": "UNKNOWN"}))
    assert outcome(rows[ASSURE], "MG-7") == "UNKNOWN"


# --------------------------------------------------------------- copy rules

def test_limitation_text_never_renders_raw_codes() -> None:
    assert limitation_text("PCS_CAPABILITY_UNAVAILABLE: x") == "Battery output not reported"
    assert limitation_text("EVIDENCE_GAP: over a..b: PCS_CAPABILITY_UNAVAILABLE") == "Battery output not reported"
    assert limitation_text("NO_COHORT: none usable") == "An evidence gap limits this conclusion"
    _, rows = run(Fake(dispatch=dict(DISPATCH, limitations=["NO_COHORT: x"])))
    assert [i["text"] for i in rows[ASSURE]["issues"]] == ["An evidence gap limits this conclusion"]


def test_unpriced_money_and_verified_headline() -> None:
    unpriced = replace(MONEY, priced=False)
    _, rows = run(Fake(money_head=unpriced, verification={"state": "VERIFIED"}))
    assert rows[COST]["headline"] == "No fuel cost estimated for this day" and rows[COST]["headline_money"] is None
    assert rows[ASSURE]["headline"] == "1 verified result"  # addendum 3 L7
    assert contributor(rows[ASSURE], "verified_results") == {
        "key": "verified_results", "label": "Verified results", "text": "ACT-048 verified on example data",
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
    one_minute = dict(DISPATCH, intervals=[{"result": {"portions_minutes": {"candidate": "1", "indeterminate": "0"}}}])
    plans = [dict(PLANS[0], next_due_hours="1")]
    _, rows = run(Fake(cards=cards, dispatch=one_minute, plans=plans))
    assert contributor(rows[PROTECT], "backup_readiness")["text"] == "1 backup start recorded"
    assert contributor(rows[GROW], "productive_use")["text"] == ("Spare solar on 2 of 3 well-observed days"
                                                                " · 2 of the last 5 days not checked")
    assert rows[COST]["subline"] == "Generator stayed on 1 minute longer than needed"
    assert contributor(rows[PROTECT], "generator")["text"].startswith("Service due at 1 operating hour ·")
    assert any(i["state_label"] == "Due at 1 operating hour" for i in rows[PROTECT]["in_hand"])


def test_source_words_match_the_portfolio() -> None:
    from assetops_backend.estate import placement
    # POLISH Addendum 13: the mini line starts with the source words, so the copy is the Portfolio's, first letter capitalised.
    assert mini.SOURCE_TEXT == {k: v[:1].upper() + v[1:] for k, v in placement._SOURCE_TEXT.items()}  # noqa: SLF001
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


# --------------------------------------------------------------- CH-5a1: the ChainReader ports and the thread join

def test_mini_ports_read_no_overview_index_readiness_or_history() -> None:
    """§A4 / §A5: the overview, Finding index, estate readiness, the two per-Action reads and the Finding history
    are not mini ports; one compose calls each ChainReader port once."""
    fields = set(MiniPorts.__dataclass_fields__)
    assert not fields & {"overview", "finding_index", "readiness", "verification", "action", "finding_history"}
    fake = Fake()
    run(fake)
    names = [n for n, _ in fake.calls]
    for name in ("source", "chain_day", "chain_findings", "findings_settled", "action_facts", "money_head"):
        assert names.count(name) == 1, name
    assert next(a for n, a in fake.calls if n == "action_facts") == (["a48"],)


def test_money_reads_the_lead_finding_on_the_board_day() -> None:
    """CH5a1-R Q5: the discovered head (greatest episode start on the board day), latest revision, source open."""
    fake = Fake()
    run(fake)
    assert next(a for n, a in fake.calls if n == "money_head") == ("f104", "f104r", True, True, True)
    off_day = Fake(chain_findings=(F090,))
    _, rows = run(off_day)
    assert "money_head" not in [n for n, _ in off_day.calls]
    assert rows[COST]["headline_money"] is None


def test_no_change_flag_drops_the_change_option() -> None:
    _, rows = run(Fake(has_change=False))
    assert [o["text"] for o in rows[COST]["options"]] == ["Trial a lower generator stop setting"]


def _threaded(action_revision: str, segment: int):
    """The happy-path board with A48 raised on `action_revision` and joined to f104's thread `t1` (segment 1)."""
    a = {**A48, "origin": {"finding_id": "f104", "finding_revision_id": action_revision}}
    comp, _ = run(Fake(action_index={"rows": [a], "next_cursor": None}))
    thread = {"id": "t1", "occurrence_no": 1, "occurrences": 1, "segment_no": 1, "state": "OPEN",
              "applied": False, "verified": False}
    facts = with_threads(comp.facts, {"findings": {"f104": thread}, "actions": {"a48": "t1"},
                                      "action_segments": {"a48": segment}})
    return {r["category"]: r for r in assemble(facts)}


def test_thread_join_links_an_action_raised_on_an_earlier_revision() -> None:
    """Deleted lineage (§A4): the link is the thread and segment, so an earlier origin revision still links."""
    rows = _threaded("f104r0", 1)
    assert rows[COST]["must_not_harm"]["href"] == f"/sites/{C}/actions/a48/verification?event_id=e1"


def test_thread_join_needs_the_same_segment() -> None:
    assert _threaded("f104r", 2)[COST]["must_not_harm"] is None


def test_no_thread_keeps_the_exact_revision_rule() -> None:
    a = {**A48, "origin": {"finding_id": "f104", "finding_revision_id": "f104r0"}}
    _, rows = run(Fake(action_index={"rows": [a], "next_cursor": None}))
    assert rows[COST]["must_not_harm"] is None  # LINK-LINEAGE's refresh link is gone (deleted lineage)
    assert run()[1][COST]["must_not_harm"] is not None
