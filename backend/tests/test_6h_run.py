"""6h2 (`specs/6h-named-option-levers/spec.md` §4.1, §10.2 test 3): the evaluation service on a STATED_OPTIONS lever,
memory store. No study is read (E2), the newest option records are (E5), the run stores no study identity."""
from __future__ import annotations

from decimal import Decimal as D
from itertools import count
from uuid import UUID

import pytest

from assetops_backend.decisions.adapters.study_file import read_study_bytes
from assetops_backend.decisions.records import DecisionRefused, DecisionService, MemoryDecisionStore
from assetops_backend.decisions.run import EvaluationService
from lakeside_people import SLUG, LakesidePeople, email
from option_fixtures import n1_base, t1_base
from test_6c_run import CLOCK, FakeRead, _cheap_hash  # noqa: F401 - the autouse password stand-in


class World:
    def __init__(self, lever_id, base, period, horizon, site="FRIDGE-001") -> None:
        self.store = MemoryDecisionStore()
        self.p = LakesidePeople(self.store.add_site, self.store.add_person)
        numbers = count(1)
        new_id = lambda: UUID(int=next(numbers))  # noqa: E731
        self.decisions = DecisionService(self.store, self.p.accounts, clock=lambda: CLOCK, new_id=new_id)
        prepared = self.decisions.prepare(tenant_slug=SLUG, as_email=email("wanjiru"), site_code=site,
                                          lever_id=lever_id, period=period, current={}, finding_id=None,
                                          horizon_months=horizon)
        self.decision_id = prepared.decision.id
        self.read = FakeRead(base)
        self.service = EvaluationService(self.store, self.p.accounts, self.read, clock=lambda: CLOCK, new_id=new_id,
                                         read_bytes=read_study_bytes)

    def one_off(self, key, amount):
        self.decisions.state_one_off(tenant_slug=SLUG, as_email=email("joseph"), decision_id=self.decision_id,
                                     option_key=key, amount=D(amount), currency="USD", crew_visits=0,
                                     basis="The contract's set-up fee")

    def record(self, key, factor, value, unit, currency=None, emulated=False):
        return self.decisions.state_option_record(
            tenant_slug=SLUG, as_email=email("joseph"), decision_id=self.decision_id, option_key=key, factor_id=factor,
            value=D(value), unit=unit, currency=currency, document="Signed contract", basis="Clause 4",
            emulated=emulated)

    def evaluate(self, study=None):
        return self.service.evaluate(tenant_slug=SLUG, as_email=email("wanjiru"), decision_id=self.decision_id,
                                     study_path=study)


def _n1():
    w = World("storage_contract", n1_base(), "2026-10", 4)
    w.one_off("storage-contract", "270.00")
    w.record("storage-contract", "contract_crate_days", 4500, "DAY")
    w.record("storage-contract", "contract_rate", "0.18", "MONEY/DAY", "USD")
    w.record("storage-contract", "handling", "100.00", "MONEY", "USD")
    return w


def test_n1_runs_with_no_study_and_the_stored_records():
    w = _n1()
    run = w.evaluate()
    row = next(e for e in run.evaluations if e.disposition == "RECOMMENDED")
    assert (run.outcome, run.study_sha256, run.study_identity, row.value, row.rank) == (
        "RECOMMENDED", None, None, D("1670.00"), 1)
    assert run.run_by_person_id == w.p.people["Wanjiru"]


def test_a_newer_record_replaces_the_older_in_the_next_run():
    w = _n1()
    w.record("storage-contract", "handling", "200.00", "MONEY", "USD")
    row = next(e for e in w.evaluate().evaluations if e.disposition != "COMPARISON")
    assert row.value == D("1270.00")  # 4 x (810 - 225 - 200) - 270


def test_a_study_given_to_a_stated_lever_is_refused_before_anything_is_read(tmp_path):
    w = _n1()
    with pytest.raises(DecisionRefused) as caught:
        w.evaluate(study=tmp_path / "study.json")
    assert caught.value.code == "STUDY_NOT_FOR_LEVER" and w.read.calls == [] and w.store.runs == []


def test_t1_runs_to_bounds_not_checked_with_no_study():
    w = World("backup_cover", t1_base(), "2026-10", 1)
    w.one_off("stopgap-and-claim", "100.00")
    w.record("stopgap-and-claim", "uncovered_nights", 0, "DAY")
    run = w.evaluate()
    by_option = {e.option_id: e for e in run.evaluations}
    stopgap = next(e for e in run.evaluations if e.value == D("-100.00"))
    assert (run.outcome, stopgap.disposition, stopgap.reason_code) == ("BOUNDS_NOT_CHECKED", "CONDITIONAL",
                                                                       "BOUNDS_NOT_CHECKED")
    assert len(by_option) == 3
