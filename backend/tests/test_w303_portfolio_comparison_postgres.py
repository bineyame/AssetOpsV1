"""W3-03 run 1b: the Portfolio B4 Action/verification proof and the persisted money comparison declines.

* `test_selected_action_window_workflow_and_withdrawal` (r1b "Progress and B4"): the S4/S6 mini-grid producer and
  evaluator chain read through the unmounted Portfolio router over **one** `[2026-11-01,2026-11-03)` request at
  successive cutoffs: producer-created Action and frozen plan -> `Outcome pending`; evaluator VERIFIED ->
  `Verified`; later accepted evidence and evaluator `RESOLUTION_WITHDRAWN` -> `Resolution withdrawn`. Each cutoff
  compares the selected Action/event/plan/outcome IDs and times with the W3-01 Action root and the stored records.
  No resolution is hand-appended; only the evaluator's pure window evidence is the labelled TEST-SCOPED complete
  window of `test_s6_verification_evaluator_postgres.complete_windows`.
* The money tests read the one-day three-domain 0b fixture (`build_portfolio_fixture`) and compare exact line keys,
  group keys and IDs with the public W3-02 Financials root; never a displayed page-row sum.

Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text

    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4/S6 mini-grid fixtures
    from test_s4_finding_store_postgres import CaseRunner, run_case
    from test_s6_action_store_postgres import CASES as S4_CASES
    from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: F401 - the replay factories
    from test_w301_estate_index_postgres import Estate, add_empty_site, imported_before, iso
    from test_w303_portfolio_fixture_postgres import build_portfolio_fixture, pin_snapshots
    from test_w303_portfolio_scope_snapshot_postgres import Portfolio

    import pg_harness
    from assetops_backend.estate import portfolio
    from assetops_backend.estate.scope import wire_time

UTC = timezone.utc
NOVEMBER = {"from": "2026-11-01T00:00:00Z", "to": "2026-11-03T00:00:00Z"}
OPERATING_COST, GROSS_TARIFF = "CANDIDATE_OPERATING_COST_EXPOSURE", "GROSS_TARIFF_SCENARIO"
DECLINE = {"combined_value": None, "combined_value_state": "NOT_COMPARABLE"}


@pytest.fixture(autouse=True)
def _cursor_key(monkeypatch):
    """r1b Q-1b-1: every Portfolio request needs the deployment key; a test-only value, never a default."""
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "4d" * 32)


@pytest.fixture()
def portfolio_fixture(request, monkeypatch, capsys):
    return build_portfolio_fixture(request, monkeypatch, capsys)


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def assert_declined(body: dict) -> None:
    """The four closure-1 decline assertions that a success body carries (the pulse note is run 2's)."""
    assert {k: body["summary"][k] for k in DECLINE} == DECLINE
    assert body["money"]["estate_total"] is None


# --- B4: the November producer/evaluator chain ---------------------------------------------------------------------

def test_selected_action_window_workflow_and_withdrawal(store, engine, monkeypatch) -> None:  # noqa: F811
    from test_s6_verification_evaluator_postgres import (
        CLOSED, bound_plan, complete_windows, evaluate, kinds, late_reading, verifying)

    runner = CaseRunner(store, engine)
    run_case(runner, S4_CASES["F01"])
    run_case(runner, S4_CASES["F02"])
    h = verifying(runner)
    pin: dict = {"at": None}
    present = lambda: pin["at"] or max(h.clock.at, runner.now) + timedelta(minutes=1)  # noqa: E731
    pin_snapshots(monkeypatch, present)
    imported_before(engine, runner.tenant, runner.site, datetime(2026, 10, 1, tzinfo=UTC))
    view, estate = Portfolio(engine, runner.tenant), Estate(engine, runner.tenant)
    captured: list = []
    real_progress = portfolio.progress

    def spy(a_sites, a_rows, k, selected_pairs):  # the full-scope selected Action rows (never a page)
        captured[:] = [a_rows, selected_pairs]
        return real_progress(a_sites, a_rows, k, selected_pairs)

    monkeypatch.setattr(portfolio, "progress", spy)

    def stored(sql: str, **params) -> list[tuple]:
        with engine.connect() as c:
            return [tuple(r) for r in c.execute(text(sql), params)]

    def read(known_at: datetime | None, label: str) -> tuple[dict, dict]:
        """One Portfolio read at `known_at` over the one November request; asserts the label of the one selected
        Action and its IDs/times against the Action root and the stored selected records."""
        params = {} if known_at is None else {"known_at": iso(known_at)}
        body = view.ok(**NOVEMBER, limit=100, **params)
        root = estate.ok("actions", **NOVEMBER, limit=100, **params)
        assert body["window"] == root["window"]
        (row,) = body["progress"]["rows"]
        (selected,) = captured[0]
        # r1b2 R10: the origin disclosure against the public Finding root's full selected revisions (all
        # lifecycles), read over the same window and cutoff; never inferred from the paged Finding table.
        findings = estate.ok("findings", **NOVEMBER, limit=100, **params)
        selected_pairs = {(r["finding_id"], r["finding_revision_id"]) for r in findings["rows"]}
        assert findings["next_cursor"] is None and captured[1] == selected_pairs
        assert body["progress"]["rows"][0]["origin_revision_selected"] is (origin in selected_pairs)
        (public,) = root["rows"]
        assert portfolio.workflow_label(selected) == label
        assert (row["action_id"], row["selected_action_event_id"]) == (public["action_id"],
                                                                      public["selected_event_id"])
        assert (row["application_state"], row["resolution_state"], row["verification_outcome"]) == (
            public["application_state"], public["resolution_state"], public["verification_outcome"])
        # The exact cutoff (the wire `known_at` is whole seconds): the requested instant, else the pinned read time.
        k = known_at or present()
        assert body["window"]["known_at"] == wire_time(k)
        (event,) = stored("SELECT CAST(id AS text), kind, recorded_at FROM action_event WHERE id = :e",
                          e=row["selected_action_event_id"])
        (latest,) = stored("SELECT max(recorded_at) FROM action_event WHERE action_id = :a AND recorded_at <= :k",
                           a=action_id, k=k)
        # The stored latest event recorded by the cutoff; the wire time is whole seconds (W3-01 run 6 reading 7).
        assert event[2] == latest[0] and row["recorded_at"] == wire_time(event[2])
        plans = stored("SELECT CAST(id AS text), recorded_at, later_start, later_end FROM verification_plan "
                       "WHERE action_id = :a AND recorded_at <= :k", a=action_id, k=k)
        active = [p for p in plans if p[2] <= k < p[3]]
        expected_plan = max(active or plans, key=lambda p: (p[1], p[0]), default=None)
        assert row["verification_plan_id"] == (None if expected_plan is None else expected_plan[0])
        outcomes = {o[0]: o[1] for o in stored(
            "SELECT CAST(id AS text), recorded_at FROM verification_outcome WHERE action_id = :a AND recorded_at <= :k",
            a=action_id, k=k)}
        assert row["verification_outcome_id"] is None or row["verification_outcome_id"] in outcomes
        # B4 boundary: a Finding-row label only when the exact origin revision is selected in this request window.
        for finding_row in body["rows"]:
            if (finding_row["finding_id"], finding_row["finding_revision_id"]) == origin:
                assert finding_row["workflow_label"] == label
        return body, event

    try:
        complete_windows(monkeypatch, h, inject=(inject := set()))
        action_id, plan, _ = bound_plan(runner, h)
        (origin,) = stored("SELECT CAST(origin_finding_id AS text), CAST(origin_finding_revision_id AS text) "
                           "FROM action WHERE id = :a", a=action_id)
        start, end = at(plan["later_start"]), at(plan["later_end"])
        (frozen_at,) = [r[0] for r in stored("SELECT recorded_at FROM verification_plan WHERE id = :p",
                                             p=plan["plan_id"])]
        assert frozen_at <= start  # the producer froze the plan before its later window opened

        # 1. The producer-created Action and frozen plan, inside the later window: `Outcome pending`.
        pending, _ = read(start, "Outcome pending")
        assert pending["progress"]["rows"][0]["verification_plan_id"] == plan["plan_id"]
        assert pending["progress"]["rows"][0]["verification_outcome_id"] is None
        assert (pending["progress"]["pending_trial_count"], pending["progress"]["verified_resolution_count"]) == (1, 0)
        assert pending["summary"]["accepted_action_count"] == 1 and pending["status"] == "HISTORICAL"
        assert pending["progress"]["completed_activity_count"] is None
        assert pending["progress"]["recovered_value"] is None
        # r1b2 R10: the F01 origin revision is not a selected Finding revision in the November window. No window of
        # this chain selects both: the Action is created 11-01 and only the one-day 10-06 window selects F01's
        # revisions; `[2026-10-06,2026-11-03)` leaves the mini-grid Finding coverage UNKNOWN (unassessed days), so
        # its selected set is empty and the flag is False too (r1b3 P-1b-6: the persisted True case is not
        # produced; the pure `test_two_actions_one_exact_origin_latest_event_then_id_tie` proves both values).
        assert pending["progress"]["rows"][0]["origin_revision_selected"] is False
        (accepted_at,) = [r[0] for r in stored(
            "SELECT recorded_at FROM action_event WHERE action_id = :a AND kind = 'ACCEPTED'", a=action_id)]
        wide = {"from": "2026-10-06T00:00:00Z", "to": "2026-11-03T00:00:00Z"}
        early = view.ok(**wide, known_at=iso(accepted_at), limit=1)
        (mine,) = [r for r in early["progress"]["rows"] if r["action_id"] == action_id]
        assert early["coverage"]["finding_state"] == "UNKNOWN" and captured[1] == set()
        assert mine["origin_revision_selected"] is False
        # Control: before the window opens the same plan is selected but not active (no `Outcome pending`).
        before, _ = read(start - timedelta(microseconds=1), "Applied")
        assert before["progress"]["pending_trial_count"] == 0
        assert before["progress"]["rows"][0]["verification_plan_id"] == plan["plan_id"]

        # 2. The evaluator's VERIFIED resolution: `Verified` from its recorded instant.
        h.clock.at = CLOSED + timedelta(hours=1)
        made = evaluate(h, action_id, "eval-0001")
        assert made.status_code == 201, made.text
        first = made.json()["outcome"]
        assert first["outcome"] == "VERIFIED" and kinds(runner, action_id)[-1] == "RESOLVED"
        # The selected resolution is the evaluator's RESOLVED Action event, recorded at or after its outcome.
        (decided,) = [r[0] for r in stored(
            "SELECT recorded_at FROM action_event WHERE action_id = :a AND kind = 'RESOLVED'", a=action_id)]
        assert decided >= at(first["recorded_at"])
        verified, event = read(decided, "Verified")
        row = verified["progress"]["rows"][0]
        assert event[2] == decided and row["verification_outcome_id"] == first["outcome_id"]
        assert (row["resolution_state"], row["verification_outcome"]) == ("RESOLVED", "VERIFIED")
        assert (verified["progress"]["pending_trial_count"], verified["progress"]["verified_resolution_count"]) == (
            0, 1)
        assert verified["summary"]["verified_resolution_count"] == 1
        assert verified["selection_token"] != pending["selection_token"]
        # The cutoff just before the outcome still reads the applied, unresolved Action.
        read(decided - timedelta(microseconds=1), "Applied")

        # 3. Later accepted evidence, then the evaluator's RESOLUTION_WITHDRAWN: `Resolution withdrawn`.
        late = late_reading(runner, "2026-11-02T13:00:00Z")
        inject.update(late)
        assert late  # a real accepted reading inside the bound later window
        h.clock.at = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
        withdrawn = evaluate(h, action_id, "eval-0002")
        assert withdrawn.json()["withdrawn"] is True, withdrawn.text
        assert kinds(runner, action_id)[-1] == "RESOLUTION_WITHDRAWN"
        live, _ = read(None, "Resolution withdrawn")
        row = live["progress"]["rows"][0]
        assert row["resolution_state"] == "RESOLUTION_WITHDRAWN"
        assert row["verification_outcome"] is None and live["progress"]["verified_resolution_count"] == 0
        assert live["status"] in ("CURRENT", "PENDING")  # the late reading may leave S3 work unsettled
        (withdrawn_at,) = [r[0] for r in stored(
            "SELECT recorded_at FROM action_event WHERE action_id = :a AND kind = 'RESOLUTION_WITHDRAWN'",
            a=action_id)]
        assert read(withdrawn_at, "Resolution withdrawn")[1][2] == withdrawn_at
        # The earlier cutoffs are unchanged by the later records (successive cutoffs, one request window).
        read(decided, "Verified")
        read(start, "Outcome pending")
        assert end > start
    finally:
        h.close()
        pg_harness.dispose(runner.findings)


# --- money: the clean four-Site fixture -----------------------------------------------------------------------------

def _by_category(lines: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for line in lines:
        out.setdefault(line["category"], []).append(line)
    return out


def test_operating_cost_first_match_wins_across_partitions(portfolio_fixture) -> None:
    """Closure 2 N2 over every selected operating-cost head before paging: the one eligible W1 line in its one
    SINGLE_LINE partition is SITE_OWNED (rule 3), even though another category's partition (EV gross tariff) is
    COMPARABLE and another (cold) is not eligible; the card never draws on those partitions' lines or groups."""
    fx = portfolio_fixture
    view = Portfolio(fx.engine, fx.tenant_id)
    body = view.ok(**fx.window, limit=1)
    financial = fx.money().ok("financials", **fx.window, limit=100)
    by_cat = _by_category(financial["rows"])
    (w1,) = by_cat[OPERATING_COST]
    parts = [g for g in financial["groups"] if g["category"] == OPERATING_COST and g["line_keys"]]
    assert [(g["state"], g["line_keys"]) for g in parts] == [("SINGLE_LINE", [w1["line_key"]])]
    assert w1["eligibility"] == "ELIGIBLE" and w1["amount"]["currency"]
    others = {g["category"]: g["state"] for g in financial["groups"] if g["category"] != OPERATING_COST}
    assert others.get(GROSS_TARIFF) == "COMPARABLE" and len(others) >= 2
    card = body["value_cards"][0]
    assert card == {"key": "OPERATING_COST", "state": "SITE_OWNED", "display_value": None,
                    "currency": w1["amount"]["currency"], "line_keys": [w1["line_key"]],
                    "group_key": parts[0]["group_key"], "basis": None, "destination": card["destination"],
                    "detail": None, "basis_text": card["basis_text"], "tone": card["tone"]}
    foreign = {x["line_key"] for c, xs in by_cat.items() if c != OPERATING_COST for x in xs}
    assert not foreign & set(card["line_keys"]) and foreign
    assert card["group_key"] not in {g["group_key"] for g in financial["groups"] if g["category"] != OPERATING_COST}
    # r1b2 R5, both priced states: one W1 Site gives no persisted COMPARABLE operating-cost partition (P-1b-4), so
    # rule 2 runs the real `operating_cost_card` over the persisted W1 DTO and a second copy in one COMPARABLE
    # partition. Both priced states leave `display_value`/`basis` null (run 2 formats the exact line/group).
    mate = {**w1, "line_key": w1["line_key"] + "-mate"}
    group = {**parts[0], "state": "COMPARABLE", "line_keys": [w1["line_key"], mate["line_key"]]}
    comparable = portfolio.operating_cost_card([w1, mate], {OPERATING_COST: True}, [group])
    assert (comparable["state"], comparable["display_value"], comparable["basis"]) == ("COMPARABLE_GROUP", None, None)
    assert comparable["group_key"] == parts[0]["group_key"] and comparable["line_keys"] == sorted(group["line_keys"])
    assert (card["display_value"], card["basis"]) == (None, None)
    # The card is a full-scope projection: equal at the page sizes 1 and 100.
    assert view.ok(**fx.window, limit=100)["value_cards"] == body["value_cards"]
    assert_declined(body)


def test_ineligible_overlap_and_unknown_coverage_decline_total(portfolio_fixture) -> None:
    """Closure 1 declines: an INELIGIBLE (cold UNPRICED) group, a COMPARABLE EV group with its exact amount, and,
    after an authorized empty EV Site joins, an UNKNOWN_COVERAGE gross-tariff group with no amount. No estate total
    or combined value at any step; exclusions are W3-02's exact rows. The OVERLAPPING_BASIS variant (d) has no
    reviewed persisted producer; r1b3 P-1b-3 rules the pure W3-02
    `test_w302_money_overlap_by_group_ids_and_citations` sufficient. This test proves the persisted INELIGIBLE,
    COMPARABLE and UNKNOWN_COVERAGE states only and claims no persisted overlap."""
    fx = portfolio_fixture
    view = Portfolio(fx.engine, fx.tenant_id)
    clean = view.ok(**fx.window, limit=100)
    financial = fx.money().ok("financials", **fx.window, limit=100)
    states = {g["category"]: g["state"] for g in financial["groups"] if g["line_keys"]}
    assert states[GROSS_TARIFF] == "COMPARABLE" and "INELIGIBLE" in states.values(), states
    assert clean["money"]["groups"] == financial["groups"] and clean["money"]["exclusions"] == financial["exclusions"]
    ineligible = [g for g in financial["groups"] if g["state"] == "INELIGIBLE"]
    assert all(g["amount"] is None for g in ineligible)
    excluded = {x["line_key"] for x in financial["exclusions"]}
    assert {k for g in ineligible for k in g["line_keys"]} <= excluded
    assert_declined(clean)

    empty = add_empty_site(fx.engine, fx.site_ids["EV-LAB-001"], "W303-EMPTY-001")
    partial = view.ok(**fx.window, limit=100)
    financial = fx.money().ok("financials", **fx.window, limit=100)
    (tariff,) = [g for g in partial["money"]["groups"] if g["category"] == GROSS_TARIFF and g["line_keys"]]
    assert tariff["state"] == "UNKNOWN_COVERAGE" and tariff["amount"] is None
    assert "UNKNOWN_COVERAGE" in tariff["reason_codes"]
    assert partial["money"]["groups"] == financial["groups"]
    assert partial["money"]["exclusions"] == financial["exclusions"]
    assert set(tariff["line_keys"]) <= {x["line_key"] for x in financial["exclusions"]}
    assert partial["status"] == "UNKNOWN" and partial["coverage"]["money_state"] == "PARTIAL"
    assert partial["value_cards"][0]["state"] == "SITE_OWNED"  # W1 operating cost stays covered
    assert empty in {o["site_id"] for o in partial["objectives"]}
    assert_declined(partial)


def test_ev_window_money_has_no_finding_attribution(portfolio_fixture) -> None:
    """EV window money (gross tariff) is Site-window money: no selected EV line names a Finding, no Portfolio
    Finding row carries an EV consequence revision, and neither the cards nor the footer attach one."""
    fx = portfolio_fixture
    body = Portfolio(fx.engine, fx.tenant_id).ok(**fx.window, limit=100)
    ev = [x for x in body["selected_lines"] if x["domain"] == "ev_charging"]
    assert ev and all(x["finding_id"] is None for x in ev)
    assert {x["category"] for x in ev} == {GROSS_TARIFF}
    ev_revisions = {x["consequence_revision_id"] for x in ev}
    for row in body["rows"]:
        consequence = row["consequence"] or {}
        assert consequence.get("source_revision_id") not in ev_revisions
        assert not {x["line_key"] for x in ev} & set(str(v) for v in consequence.values())
    ev_keys = {x["line_key"] for x in ev}
    assert not ev_keys & {k for card in body["value_cards"] for k in card["line_keys"]}
    assert body["footer"]["line_key"] in ev_keys and "finding" not in str(body["footer"]["destination"])
    assert set(body["footer"]) == {"line_key", "site_name", "quantity_display", "amount_display",
                                   "source_provenance", "window_start", "window_end", "destination"}
    assert_declined(body)
