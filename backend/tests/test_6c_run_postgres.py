"""6c (`specs/6c-option-evaluator/spec.md` §6 test 6): F1b's run written through 6a's Postgres adapter, the deferred
completeness check holding at commit, the run read back as stored, and one `alembic heads`.
Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database. Run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import dataclasses
import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text

    from test_on1_onboarding_postgres import onboarded  # noqa: F401 - Lakeside onboarded through ON1's command
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from assetops_backend.accounts.composition import build_account_service
    from assetops_backend.decisions.adapters.postgres_decision_store import PostgresDecisionStore
    from assetops_backend.decisions.adapters.study_file import read_study_bytes
    from assetops_backend.decisions.records import DecisionService
    from assetops_backend.decisions.run import EvaluationService

from option_fixtures import CURRENT, FIXTURES, TEST_GRID, TEST_LEVER, f1_base

T = datetime(2026, 11, 24, 9, 0, 0, tzinfo=timezone.utc)
SLUG = "lakeside-power"


class _Read:
    def site_inputs(self, site, month, known_at=None):
        from types import SimpleNamespace
        return SimpleNamespace(leaves=f1_base(), stated={})


def test_6_f1b_through_the_adapter(onboarded, engine) -> None:  # noqa: F811
    from test_6c_evaluate import run_f1

    adapter = PostgresDecisionStore(URL)
    accounts = build_account_service(URL)
    try:
        levers = {"test_stop_reserve": TEST_LEVER}
        decisions = DecisionService(adapter, accounts, clock=lambda: T, levers=levers)
        prepared = decisions.prepare(tenant_slug=SLUG, as_email="wanjiru@lakeside-power.example",
                                     site_code="KOBO-001", lever_id="test_stop_reserve", period="2026-10",
                                     current=CURRENT, finding_id=None)
        for option in prepared.options[1:]:
            decisions.state_one_off(tenant_slug=SLUG, as_email="peter@lakeside-power.example",
                                    decision_id=prepared.decision.id, option_key=option.option_key,
                                    amount=Decimal("90.00"), currency="USD", crew_visits=0,
                                    basis="Technician sets the controller on a routine visit")
        service = EvaluationService(adapter, accounts, _Read(), clock=lambda: T, levers=levers,
                                    grid_changes=TEST_GRID, read_bytes=read_study_bytes)
        run = service.evaluate(tenant_slug=SLUG, as_email="wanjiru@lakeside-power.example",
                               decision_id=prepared.decision.id, study_path=FIXTURES / "study-f1.json")
        back = adapter.latest_run(run.tenant_id, prepared.decision.id)
        assert back is not None and back.id == run.id and back.outcome == "RECOMMENDED"
        assert dict(back.study_identity) == dict(run.study_identity) and back.study_sha256 == run.study_sha256
        _, rows, _, _ = run_f1()
        keys = {o.id: o.option_key for o in prepared.options}
        for e in back.evaluations:
            mine = rows[keys[e.option_id]]
            strip = dict(id=None, option_id=None, one_off_id=None)
            assert dataclasses.replace(e, **strip) == dataclasses.replace(mine, **strip), keys[e.option_id]
        with engine.connect() as c:  # the deferred completeness check held: every option has its evaluation
            n = c.execute(text("SELECT count(*) FROM option_evaluation WHERE run_id = :r"), {"r": run.id}).scalar_one()
        assert n == len(prepared.options) == 8
    finally:
        adapter.dispose()
        accounts._store.dispose()


FUEL = ("EXPENSE (FUEL)", "COMMERCIAL_RECORD", "diesel_price")
WEAR = ("battery_wear_rate_assumption", "DECLARED", "wear_rate")
#: what the evaluation says of each option when only ON1's onboarding is stored for KOBO-001 (see the packet): the
#: option's disposition, reason and the records its figure lacks
E2E = {
    "stop-90-reserve-25": ("DEFERRED", "VALUE_NOT_AVAILABLE", [FUEL]),
    "stop-80-reserve-30": ("DEFERRED", "VALUE_NOT_AVAILABLE", [FUEL, WEAR]),
    "stop-80-reserve-25": ("REJECTED", "NOT_ADMITTED_STARTS", [FUEL, WEAR]),
    "stop-70-reserve-30": ("DEFERRED", "VALUE_NOT_AVAILABLE", [FUEL, WEAR]),
    "stop-70-reserve-25": ("DEFERRED", "VALUE_NOT_AVAILABLE", [FUEL, WEAR]),
    "stop-60-reserve-30": ("DEFERRED", "VALUE_NOT_AVAILABLE", [FUEL, WEAR]),
    "stop-60-reserve-25": ("REJECTED", "NOT_ADMITTED_FULL_CHARGE", [FUEL, WEAR]),
}


def test_6_build_evaluation_end_to_end_on_lakeside_kobo(onboarded, engine) -> None:  # noqa: F811
    """D-P6.41: the real composition (decision store, accounts, the structure read over Postgres) on KOBO-001's
    2026-10, F1's test lever, grid and study. ON1 stores no fuel price, no wear rate and no dispatch for the Site, so
    no option has a money figure: each names the records it lacks and the run is RANKING_INCOMPLETE."""
    from assetops_backend.decisions.composition import build_evaluation

    levers = {"test_stop_reserve": TEST_LEVER}
    adapter = PostgresDecisionStore(URL)
    accounts = build_account_service(URL)
    built = build_evaluation(URL, levers=levers, grid_changes=TEST_GRID)
    try:
        decisions = DecisionService(adapter, accounts, clock=lambda: T, levers=levers)
        prepared = decisions.prepare(tenant_slug=SLUG, as_email="wanjiru@lakeside-power.example",
                                     site_code="KOBO-001", lever_id="test_stop_reserve", period="2026-10",
                                     current=CURRENT, finding_id=None)
        for option in prepared.options[1:]:
            decisions.state_one_off(tenant_slug=SLUG, as_email="peter@lakeside-power.example",
                                    decision_id=prepared.decision.id, option_key=option.option_key,
                                    amount=Decimal("90.00"), currency="USD", crew_visits=0,
                                    basis="Technician sets the controller on a routine visit")
        run = built.service.evaluate(tenant_slug=SLUG, as_email="wanjiru@lakeside-power.example",
                                     decision_id=prepared.decision.id, study_path=FIXTURES / "study-f1.json")
        back = adapter.latest_run(run.tenant_id, prepared.decision.id)
        assert back is not None and back.id == run.id and back.outcome == "RANKING_INCOMPLETE"
        keys = {o.id: o.option_key for o in prepared.options}
        rows = {keys[e.option_id]: e for e in back.evaluations}
        assert (rows["no-action"].disposition, rows["no-action"].value, rows["no-action"].source_class) \
            == ("COMPARISON", Decimal(0), "SIMULATED")
        for key, (disposition, reason, missing) in E2E.items():
            row = rows[key]
            assert (row.disposition, row.reason_code, row.rank, row.value, row.monthly_change, row.horizon_change) \
                == (disposition, reason, None, None, None, None), key
            assert [(m.record_kind, m.source_family, m.factor_id) for m in row.missing] == missing, key
            assert row.assumed == (), key
    finally:
        built.dispose()
        adapter.dispose()
        accounts._store.dispose()


def test_6_one_alembic_head() -> None:
    import pg_harness
    from alembic.script import ScriptDirectory

    assert len(ScriptDirectory.from_config(pg_harness._alembic(URL)).get_heads()) == 1
