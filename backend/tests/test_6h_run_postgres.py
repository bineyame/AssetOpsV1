"""6h (`specs/6h-named-option-levers/spec.md` §10.2 test 6): N1 and T1 end to end through the Postgres adapter, the
option records stored, read back as the newest per option and factor, and the run's evidence and source class accepted
by 0073's checks. Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal as D

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

from option_fixtures import n1_base, t1_base

T = datetime(2026, 11, 24, 9, 0, 0, tzinfo=timezone.utc)
SLUG = "lakeside-power"
WANJIRU, JOSEPH = "wanjiru@lakeside-power.example", "joseph@lakeside-power.example"


class _Read:
    def __init__(self, leaves) -> None:
        self.leaves = leaves

    def site_inputs(self, site, month, known_at=None):
        from types import SimpleNamespace
        return SimpleNamespace(leaves=self.leaves, stated={})


def _cold_world(engine, onboarded):  # noqa: F811
    with engine.begin() as c:  # a cold Site of the test fixtures: the onboarded Lakeside has mini-grids only
        c.execute(text("UPDATE site SET site_type = 'COLDCHAIN' WHERE site_code = 'KISIWA-001'"))
    adapter = PostgresDecisionStore(URL)
    accounts = build_account_service(URL)
    return adapter, accounts, DecisionService(adapter, accounts, clock=lambda: T)


def _prepare(decisions, lever_id, horizon):
    return decisions.prepare(tenant_slug=SLUG, as_email=WANJIRU, site_code="KISIWA-001", lever_id=lever_id,
                             period="2026-10", current={}, finding_id=None, horizon_months=horizon)


def _state(decisions, prepared, key, factor, value, unit, currency=None):
    return decisions.state_option_record(
        tenant_slug=SLUG, as_email=JOSEPH, decision_id=prepared.decision.id, option_key=key, factor_id=factor,
        value=D(value), unit=unit, currency=currency, document="Signed contract", basis="Clause 4", emulated=False)


def _one_off(decisions, prepared, key, amount):
    decisions.state_one_off(tenant_slug=SLUG, as_email=JOSEPH, decision_id=prepared.decision.id, option_key=key,
                            amount=D(amount), currency="USD", crew_visits=0, basis="The set-up fee")


def test_6_n1_and_t1_through_the_adapter(onboarded, engine) -> None:  # noqa: F811
    adapter, accounts, decisions = _cold_world(engine, onboarded)
    try:
        n1 = _prepare(decisions, "storage_contract", 4)
        _one_off(decisions, n1, "storage-contract", "270.00")
        _state(decisions, n1, "storage-contract", "contract_crate_days", 4500, "DAY")
        _state(decisions, n1, "storage-contract", "contract_rate", "0.18", "MONEY/DAY", "USD")
        _state(decisions, n1, "storage-contract", "handling", "100.00", "MONEY", "USD")
        _state(decisions, n1, "storage-contract", "handling", "100.00", "MONEY", "USD")  # a later one replaces
        assert len(adapter.latest_option_records(n1.decision.tenant_id, n1.decision.id)) == 3
        service = EvaluationService(adapter, accounts, _Read(n1_base()), clock=lambda: T,
                                    read_bytes=read_study_bytes)
        run = service.evaluate(tenant_slug=SLUG, as_email=WANJIRU, decision_id=n1.decision.id, study_path=None)
        back = adapter.latest_run(run.tenant_id, n1.decision.id)
        row = next(e for e in back.evaluations if e.disposition == "RECOMMENDED")
        assert (back.outcome, back.study_sha256, back.study_identity, row.value, row.rank, row.source_class) == (
            "RECOMMENDED", None, None, D("1670.00"), 1, "RECORDED")
        assert (row.monthly_change, row.horizon_change, row.currency) == (D("485.00"), D("1940.00"), "USD")

        t1 = _prepare(decisions, "backup_cover", 1)
        _one_off(decisions, t1, "stopgap-and-claim", "100.00")
        _state(decisions, t1, "stopgap-and-claim", "uncovered_nights", 0, "DAY")
        service = EvaluationService(adapter, accounts, _Read(t1_base()), clock=lambda: T,
                                    read_bytes=read_study_bytes)
        run = service.evaluate(tenant_slug=SLUG, as_email=WANJIRU, decision_id=t1.decision.id, study_path=None)
        back = adapter.latest_run(run.tenant_id, t1.decision.id)
        by_value = {e.value: e for e in back.evaluations}
        stopgap = by_value[D("-100.00")]
        assert (back.outcome, stopgap.disposition, stopgap.reason_code, stopgap.rank, stopgap.evidence_class,
                stopgap.source_class) == ("BOUNDS_NOT_CHECKED", "CONDITIONAL", "BOUNDS_NOT_CHECKED", None, "DECLARED",
                                          "RECORDED")
        repair = by_value[None]  # self-repair: no record and no one-off; the DECLARED row is accepted by the checks
        assert (repair.disposition, repair.evidence_class) == ("DEFERRED", "DECLARED")
    finally:
        adapter.dispose()
        accounts._store.dispose()
