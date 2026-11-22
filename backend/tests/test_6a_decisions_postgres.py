"""6a (`specs/6a-decision-records/spec.md` §4, §6 test 7): the Postgres decision store, end to end through the commands.

F-P1 to F-C1 on Lakeside (the `onboarded` fixture, as 3C2's Postgres test), the prepare race (the lock removed in a scratch
copy, the unique index still catches), `for_tenant` newest first with names, the five states, `recommended` null
under an incomplete ranking, the period filter, another tenant absent, `site_name`, `site_by_id`, and one row of each
jsonb column stored and read back exactly (D-P6.27).

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database. Run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import dataclasses
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_on1_onboarding_postgres import onboarded  # noqa: F401 - Lakeside onboarded through ON1's command
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend import choose_option, prepare_decision, record_action, state_one_off
    from assetops_backend.decisions.adapters import postgres_decision_store as store_module
    from assetops_backend.decisions.adapters.postgres_decision_store import PostgresDecisionStore
    from assetops_backend.decisions.composition import build_decisions
    from assetops_backend.decisions.records import (ChoiceRow, EffectRow, EvaluationRow, MissingInput, RunRow,
                                                    StoreUnavailable)
    from test_3c0a_accounts_postgres import seed_tenant
    from test_3c2_agreed_actions import r1

SLUG = "lakeside-power"
T = datetime(2026, 11, 24, 9, 0, 0, tzinfo=timezone.utc)
D = Decimal
OPTION_70 = "stop-70-reserve-30"
BASIS = "Technician sets the controller on a routine visit"
TABLES = ("decision", "decision_option", "option_one_off", "option_evaluation_run", "option_evaluation",
          "option_effect", "decision_choice")


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


@pytest.fixture()
def lake(onboarded, engine, monkeypatch):  # noqa: F811
    with engine.connect() as c:
        tenant = c.execute(text("SELECT id FROM tenant WHERE slug = :s"), {"s": SLUG}).scalar_one()
        people = dict(c.execute(text("SELECT display_name, id FROM operator_account WHERE tenant_id = :t"),
                                {"t": tenant}).all())
        sites = dict(c.execute(text("SELECT site_code, id FROM site WHERE tenant_id = :t"), {"t": tenant}).all())
    monkeypatch.setenv("DATABASE_URL", URL)
    adapter = PostgresDecisionStore(URL)
    yield {"tenant": tenant, "people": people, "sites": sites, "adapter": adapter, "clock": Clock(T)}
    adapter.dispose()


def email(name: str) -> str:
    return f"{name}@lakeside-power.example"


def _run(module, argv: list[str], capsys, at: datetime = T) -> tuple[int, str, str]:
    code = module.main(argv, clock=Clock(at))
    out, err = capsys.readouterr()
    return code, out, err


def _prepare(capsys, *, period="2026-10", at=T, who="wanjiru", site="KOBO-001", extra=()) -> tuple[int, str, str]:
    return _run(prepare_decision, ["--tenant", SLUG, "--as", email(who), "--site", site, "--lever",
                                   "generator_stop_reserve", "--period", period, "--current",
                                   "stop_soc_pct=90,reserve_soc_pct=30", *extra], capsys, at)


def _count(engine, table: str) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


def _counts(engine) -> dict[str, int]:  # noqa: F811
    return {t: _count(engine, t) for t in TABLES}


def _store_run(lake, decision_id: UUID, *, recommended: str | None = None, at: datetime = T,
               outcome: str | None = None, rich: bool = False) -> RunRow:
    """A run covering every option: `no-action` COMPARISON, `stop-60-reserve-25` REJECTED, `recommended` RECOMMENDED
    (rank 1, value 120), every other option ACCEPTABLE."""
    _, options = lake["adapter"].decision(lake["tenant"], decision_id)
    missing = (MissingInput("RECORD", "FUEL", "candidate_l"), MissingInput("RECORD", "TARIFF", None))
    evaluations = []
    for o in options:
        if o.option_key == "no-action":
            args = ("COMPARISON", None, None, None, None, None, D(0), None)
        elif o.option_key == "stop-60-reserve-25":
            args = ("REJECTED", "ABOVE_BOUND", None, None, None, None, D("5"), "USD")
        elif o.option_key == recommended:
            args = ("RECOMMENDED", None, 1, D("12.5"), D("150"), None, D("120"), "USD")
        else:
            args = ("ACCEPTABLE", None, None, None, None, None, D("10"), "USD")
        disposition, reason, rank, monthly, horizon, one_off, value, currency = args
        miss, assumed, admission, dawn, effects = (), (), None, None, ()
        if rich and o.option_key == OPTION_70:
            miss, assumed = missing, ("candidate_l", "fuel_cost")
            admission = {"ratio": "1/3", "bound": {"min": 2, "max": 9}, "ok": True}
            dawn = {"hours": [5, 6], "share": "2/5"}
            effects = (EffectRow("candidate_l", 0, None, "litres", None, missing[:1]),
                       EffectRow("fuel_cost", 1, D("-3.25"), "currency", "USD", ()))
            value, currency = None, None
        evaluations.append(EvaluationRow(uuid4(), o.id, disposition, reason, rank, monthly, horizon, one_off, value,
                                         currency, "SIMULATED", "MODELLED", miss, assumed, admission, dawn, effects))
    run = RunRow(uuid4(), lake["tenant"], decision_id, "option-evaluator-1",
                 outcome or ("RECOMMENDED" if recommended else "RANKING_INCOMPLETE"), "a" * 64 if rich else None,
                 {"rows": 3, "sha": "x"} if rich else None, at, lake["people"]["Wanjiru"], "ANALYST", True, at,
                 tuple(evaluations))
    return lake["adapter"].add_run(run)


def test_7a_f_p1_end_to_end_a_re_run_and_the_row_counts(lake, engine, capsys) -> None:  # noqa: F811
    code, out, err = _prepare(capsys)
    line = json.loads(out)
    assert (code, err) == (0, "") and "@" not in out
    assert line["already_prepared"] is False and line["home_category"] == "OPTIMIZE_COST"
    assert [o["option_key"] for o in line["options"]][:3] == ["no-action", "stop-90-reserve-25", "stop-85-reserve-30"]
    assert len(line["options"]) == 14 and line["prepared_by"] == "Wanjiru"
    assert _counts(engine)["decision"] == 1 and _counts(engine)["decision_option"] == 14
    with engine.connect() as c:
        stored = c.execute(text("SELECT prepared_by_script, prepared_role, prepared_at FROM decision")).one()
    assert (stored.prepared_by_script, stored.prepared_role, stored.prepared_at) == (True, "ANALYST", T)
    again = json.loads(_prepare(capsys)[1])
    assert again["already_prepared"] is True and again["decision_id"] == line["decision_id"]
    assert _counts(engine)["decision"] == 1 and _counts(engine)["decision_option"] == 14
    code, _, err = _prepare(capsys, extra=("--horizon", "6"))
    assert (code, err.split()[0]) == (2, "ALREADY_PREPARED_OTHER")
    code, _, err = _prepare(capsys, who="peter")
    assert (code, err.split()[0]) == (2, "PERSON_ROLE_REQUIRED")


def _two_at_once(capsys, lake) -> tuple[list[int], list[dict], str]:
    gate = threading.Barrier(2)
    codes: list[int] = []

    def go() -> None:
        gate.wait()
        codes.append(prepare_decision.main(["--tenant", SLUG, "--as", email("wanjiru"), "--site", "KOBO-001",
                                            "--lever", "generator_stop_reserve", "--period", "2026-10", "--current",
                                            "stop_soc_pct=90,reserve_soc_pct=30"], clock=lake["clock"]))

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    out, err = capsys.readouterr()
    return codes, [json.loads(x) for x in out.splitlines()], err


def test_7b_the_prepare_race_one_row_with_the_lock_and_without_it(lake, engine, capsys, monkeypatch) -> None:  # noqa: F811
    codes, lines, err = _two_at_once(capsys, lake)
    assert codes == [0, 0] and err == "" and sorted(x["already_prepared"] for x in lines) == [False, True]
    assert _counts(engine)["decision"] == 1 and _counts(engine)["decision_option"] == 14
    with engine.begin() as c:  # the test empties the tables the only way the triggers allow
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for table in reversed(TABLES):
            c.execute(text(f"DELETE FROM {table}"))
    # The scratch copy: the advisory lock removed. The unique index `decision_once` alone still gives one row.
    monkeypatch.setattr(store_module, "_LOCK", text("SELECT 1"))
    codes, lines, err = _two_at_once(capsys, lake)
    assert codes == [0, 0] and err == "" and sorted(x["already_prepared"] for x in lines) == [False, True]
    assert len({x["decision_id"] for x in lines}) == 1
    assert _counts(engine)["decision"] == 1 and _counts(engine)["decision_option"] == 14


def test_7c_f_o1_the_latest_statement_wins_and_refusals(lake, engine, capsys) -> None:  # noqa: F811
    decision = json.loads(_prepare(capsys)[1])["decision_id"]

    def say(who, amount, at, option=OPTION_70, decision_id=decision):
        return _run(state_one_off, ["--tenant", SLUG, "--as", email(who), "--decision", decision_id, "--option",
                                    option, "--amount", amount, "--currency", "USD", "--crew-visits", "0", "--basis",
                                    BASIS], capsys, at)

    code, out, err = say("peter", "90.00", T)
    assert (code, err) == (0, "") and json.loads(out)["declared_by"] == "Peter"
    assert json.loads(out)["amount"] == "90.00" and json.loads(out)["declared_at"] == "2026-11-24T09:00:00Z"
    assert say("peter", "120.00", T + timedelta(minutes=5))[0] == 0
    assert say("joseph", "100.00", T + timedelta(minutes=6), option="stop-65-reserve-30")[0] == 0
    assert _count(engine, "option_one_off") == 3
    latest = lake["adapter"].latest_one_offs(lake["tenant"], UUID(decision))
    assert sorted(r.amount for r in latest.values()) == [D("100.00"), D("120.00")]
    assert say("david", "1.00", T, decision_id=decision)[2].startswith("PERSON_ROLE_REQUIRED")
    assert say("musa", "1.00", T)[2].startswith("PERSON_ROLE_REQUIRED")
    assert say("peter", "1.00", T, option="no-action")[2].startswith("NO_ACTION_ONE_OFF")
    assert say("peter", "1.00", T, decision_id=str(uuid4()))[2].startswith("DECISION_NOT_FOUND")


def _service(lake):
    built = build_decisions(URL, clock=lake["clock"])
    return built


def test_7d_f_c1_choose_once_states_and_the_read(lake, engine, capsys) -> None:  # noqa: F811
    d1 = json.loads(_prepare(capsys)[1])["decision_id"]
    assert _run(record_action, r1(), capsys)[0] == 0
    with engine.connect() as c:
        action = str(c.execute(text("SELECT id FROM agreed_action")).scalar_one())
    built = _service(lake)
    try:
        view = {v.decision_id: v for v in built.service.for_tenant(lake["tenant"])}[d1]
        assert (view.state, view.recommended, view.run, view.choice) == ("NOT_VALUED", None, None, None)
        with engine.connect() as c:
            assert view.site_name == c.execute(text("SELECT name FROM site WHERE site_code = 'KOBO-001'")).scalar_one()
        code, _, err = _run(choose_option, ["--tenant", SLUG, "--as", email("amina"), "--decision", d1, "--option",
                                            OPTION_70], capsys)
        assert (code, err.split()[0]) == (2, "NOT_EVALUATED")
        run = _store_run(lake, UUID(d1))
        view = built.service.for_tenant(lake["tenant"])[0]
        assert (view.state, view.recommended, view.run.outcome) == ("WAITING", None, "RANKING_INCOMPLETE")
        assert view.run.run_by_name == "Wanjiru" and view.run.source_class == "SIMULATED"
        argv = ["--tenant", SLUG, "--as", email("amina"), "--decision", d1, "--option", OPTION_70, "--action", action]
        code, out, err = _run(choose_option, argv, capsys)
        line = json.loads(out)
        assert (code, err) == (0, "") and line["already_chosen"] is False and line["run_id"] == str(run.id)
        assert (line["agreed_action_id"], line["chosen_by"], line["option_key"]) == (action, "Amina", OPTION_70)
        assert json.loads(_run(choose_option, argv, capsys)[1])["already_chosen"] is True
        code, _, err = _run(choose_option, argv[:-4] + ["--option", "stop-80-reserve-30", "--action", action], capsys)
        assert (code, err.split()[0]) == (2, "ALREADY_CHOSEN")
        code, _, err = _run(choose_option, ["--tenant", SLUG, "--as", email("peter"), "--decision", d1, "--none"],
                            capsys)
        assert (code, err.split()[0]) == (2, "PERSON_ROLE_REQUIRED")
        assert _count(engine, "decision_choice") == 1
        assert built.service.for_tenant(lake["tenant"])[0].state == "UNDER_WAY"
        # CHOSEN without an Action; KEPT_AS_IS under --none; the one-off the other tests state is not needed here.
        d2 = json.loads(_prepare(capsys, period="2026-09", at=T + timedelta(hours=1))[1])["decision_id"]
        d3 = json.loads(_prepare(capsys, period="2026-08", at=T + timedelta(hours=2))[1])["decision_id"]
        for d in (d2, d3):
            _store_run(lake, UUID(d), at=T + timedelta(hours=3))
        assert _run(choose_option, ["--tenant", SLUG, "--as", email("amina"), "--decision", d2, "--option",
                                    "stop-80-reserve-30"], capsys)[0] == 0
        assert _run(choose_option, ["--tenant", SLUG, "--as", email("amina"), "--decision", d3, "--none"],
                    capsys)[0] == 0
        views = built.service.for_tenant(lake["tenant"])
        assert [v.decision_id for v in views] == [d3, d2, d1]  # newest first
        assert [v.state for v in views] == ["KEPT_AS_IS", "CHOSEN", "UNDER_WAY"]
        assert views[0].choice.option_key is None and views[1].choice.agreed_action_id is None
        assert all("@" not in repr(v) for v in views)
        # the period filter
        only = built.service.for_tenant(lake["tenant"], period_from="2026-10", period_to="2026-10")
        assert [v.decision_id for v in only] == [d1]
        assert built.service.for_tenant(lake["tenant"], period_from="2026-11", period_to="2026-12") == ()
        # another tenant's decisions are absent
        other = seed_tenant(engine, "other-op")
        assert built.service.for_tenant(other) == ()
    finally:
        built.dispose()


def test_7e_recommended_is_the_runs_recommended_row(lake, capsys) -> None:  # noqa: F811
    d = json.loads(_prepare(capsys)[1])["decision_id"]
    _store_run(lake, UUID(d), recommended=OPTION_70, at=T)
    built = _service(lake)
    try:
        view = built.service.for_tenant(lake["tenant"])[0]
        assert (view.recommended.option_key, view.recommended.value, view.recommended.currency) == (
            OPTION_70, D("120"), "USD")
    finally:
        built.dispose()


def test_7f_site_by_id_found_and_missing(lake) -> None:
    adapter = lake["adapter"]
    kobo = lake["sites"]["KOBO-001"]
    ref = adapter.site_by_id(lake["tenant"], kobo)
    assert (ref.site_id, ref.site_code, ref.site_type, ref.tenant_id) == (kobo, "KOBO-001", "MINIGRID", lake["tenant"])
    assert ref.timezone
    assert adapter.site_by_id(lake["tenant"], uuid4()) is None
    assert adapter.site_by_id(uuid4(), kobo) is None
    assert adapter.site(lake["tenant"], "kobo-001").site_id == kobo and adapter.site(lake["tenant"], "NOPE") is None
    assert adapter.finding(lake["tenant"], kobo, uuid4()) is None


def test_7g_every_jsonb_column_is_stored_and_read_back_exactly(lake, capsys) -> None:  # noqa: F811
    d = json.loads(_prepare(capsys)[1])["decision_id"]
    stored, options = lake["adapter"].decision(lake["tenant"], UUID(d))
    assert dict(stored.current_settings) == {"stop_soc_pct": D(90), "reserve_soc_pct": D(30)}
    assert options[0].settings == {"stop_soc_pct": D(90), "reserve_soc_pct": D(30)} and options[0].position == 0
    assert [o.position for o in options] == list(range(14))
    run = _store_run(lake, UUID(d), rich=True)
    back = lake["adapter"].latest_run(lake["tenant"], UUID(d))
    assert back == run
    rich = next(e for e in back.evaluations if e.missing)
    assert rich.missing[0] == MissingInput("RECORD", "FUEL", "candidate_l") and rich.missing[1].factor_id is None
    assert rich.assumed == ("candidate_l", "fuel_cost") and rich.admission["bound"] == {"min": 2, "max": 9}
    assert rich.effects[1].change_per_month == D("-3.25") and rich.effects[0].change_per_month is None
    assert back.study_identity == {"rows": 3, "sha": "x"}
    assert lake["adapter"].latest_run(lake["tenant"], uuid4()) is None


def test_7h_a_run_missing_an_option_is_refused_at_commit(lake, engine, capsys) -> None:  # noqa: F811
    d = json.loads(_prepare(capsys)[1])["decision_id"]
    run = _store_run(lake, UUID(d))
    fresh = tuple(dataclasses.replace(e, id=uuid4()) for e in run.evaluations)
    whole = RunRow(uuid4(), run.tenant_id, run.decision_id, run.evaluator_version, run.outcome, None, None, T,
                   run.run_by_person_id, "ANALYST", True, T, fresh)
    short = dataclasses.replace(whole, id=uuid4(), evaluations=tuple(dataclasses.replace(e, id=uuid4())
                                                                      for e in run.evaluations[:-1]))
    with pytest.raises(StoreUnavailable):  # the deferred trigger refuses it at commit
        lake["adapter"].add_run(short)
    assert _count(engine, "option_evaluation_run") == 1 and _count(engine, "option_evaluation") == 14
    lake["adapter"].add_run(whole)  # the same rows, complete, with fresh ids: stored
    assert _count(engine, "option_evaluation_run") == 2 and _count(engine, "option_evaluation") == 28


def test_7i_an_unreachable_store_is_exit_three(monkeypatch, capsys) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:y@127.0.0.1:1/none")
    code = prepare_decision.main(["--tenant", SLUG, "--as", email("wanjiru"), "--site", "KOBO-001", "--lever",
                                  "generator_stop_reserve", "--period", "2026-10", "--current",
                                  "stop_soc_pct=90,reserve_soc_pct=30"])
    out, err = capsys.readouterr()
    assert (code, out, err.split()[0]) == (3, "", "DECISIONS_UNAVAILABLE")
    adapter = PostgresDecisionStore("postgresql+psycopg://x:y@127.0.0.1:1/none")
    try:
        with pytest.raises(StoreUnavailable):
            adapter.site(uuid4(), "KOBO-001")
    finally:
        adapter.dispose()
    assert ChoiceRow  # the row type the adapter reads
