"""OWN-G2 (build sheet OWN-GAPS §2.3, §2.4, §2.7; R2-G2 Q4, Q11): `run_site` and the `fuel_night` stage child, with
fake stores (no DB)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from test_own_g2_fuel_night_due import L, FakeFindings, FakeStore, inputs, seen

from assetops_backend.fuel_balance import scheduled
from assetops_backend.fuel_balance.model import CLOCK_BACKWARDS, WINDOW_INVALID, WINDOW_OPEN, FuelBalanceRefused
from assetops_backend.fuel_balance.scheduled import run_site
from assetops_backend.scheduling import stages
from test_own_g2_fuel_night_due import FakeService

PREV = L - timedelta(days=1)


@pytest.fixture(autouse=True)
def fake_service(monkeypatch):
    monkeypatch.setattr(scheduled, "FuelBalanceService", FakeService)


def test_reused_then_unchanged_writes_nothing_new() -> None:
    store = FakeStore(inputs(seen(L)), {L: ("REUSED", 1)})
    out = run_site(store, FakeFindings({L: "UNCHANGED"}), "t", "s", 10, None)
    assert out["nights"] == [{"night_date": L.isoformat(), "assess": "REUSED", "revision": 1,
                              "state": "WITHIN_MARGIN", "raise": "UNCHANGED"}]
    assert (out["appended"], out["reused"], out["raised"]) == (0, 1, {"UNCHANGED": 1})


def test_appended_then_opened_is_counted() -> None:
    store = FakeStore(inputs(seen(PREV, L)), {PREV: ("APPENDED", 2)})
    out = run_site(store, FakeFindings({PREV: "OPENED"}), "t", "s", 10, None)
    assert (out["appended"], out["reused"], out["raised"]) == (2, 0, {"OPENED": 1, "NO_FINDING": 1})
    assert out["nights"][0]["assess"] == "APPENDED" and out["nights"][0]["revision"] == 2


def test_window_open_is_skipped_without_a_raise_and_counts_as_processed() -> None:
    store = FakeStore(inputs(seen(PREV, L)), {PREV: FuelBalanceRefused(WINDOW_OPEN, "not yet")})
    findings = FakeFindings()
    out = run_site(store, findings, "t", "s", 10, None)
    assert out["nights"][0] == {"night_date": PREV.isoformat(), "assess": "OPEN", "revision": None, "state": None,
                                "raise": None}
    assert findings.calls == [L]  # no raise for the OPEN night
    assert out["processed"] + out["deferred"] == 2 and out["processed"] == 2


def test_clock_backwards_on_one_night_still_checks_later_nights_then_fails_the_stage() -> None:
    """D-R3.10. Fails on the old re-raise (L is never assessed) and on swallowing the refusal (no raise)."""
    store = FakeStore(inputs(seen(PREV, L)), {PREV: FuelBalanceRefused(CLOCK_BACKWARDS, "before revision 1")})
    findings = FakeFindings()
    with pytest.raises(FuelBalanceRefused) as refused:
        run_site(store, findings, "t", "s", 10, None)
    assert [c[1] for c in store.calls if c[0] == "assess"] == [PREV, L] and findings.calls == [L]
    assert refused.value.code == CLOCK_BACKWARDS and PREV.isoformat() in str(refused.value)
    assert stages.classify(refused.value) == "FAILED" and CLOCK_BACKWARDS in str(refused.value)


def test_any_other_refusal_still_fails_at_once() -> None:
    store = FakeStore(inputs(seen(PREV, L)), {PREV: FuelBalanceRefused(WINDOW_INVALID, "bad window")})
    with pytest.raises(FuelBalanceRefused) as refused:
        run_site(store, FakeFindings(), "t", "s", 10, None)
    assert refused.value.code == WINDOW_INVALID and [c[1] for c in store.calls if c[0] == "assess"] == [PREV]


def test_a_passed_deadline_starts_no_night_and_defers_them() -> None:
    store = FakeStore(inputs(seen(PREV, L)))
    out = run_site(store, FakeFindings(), "t", "s", 10, lambda: True)
    assert (out["processed"], out["deferred"]) == (0, 2) and [c for c in store.calls if c[0] == "assess"] == []


def test_the_stage_child_composes_db_clock_stores_and_passes_its_deadline(monkeypatch) -> None:
    from assetops_backend.fuel_balance import composition

    built, seen_args = [], {}

    class Holder:
        def __init__(self, name):
            self.name = name

        def dispose(self):
            built.append(("dispose", self.name))

    def store(url, **kw):
        built.append(("store", url, kw))
        return Holder("store")

    def findings(url, **kw):
        built.append(("findings", url, kw))
        return Holder("findings")

    def fake_run(store_, findings_, t, s, limit, deadline):
        seen_args.update(limit=limit, deadline=deadline, t=t, s=s)
        return {"code": "OK", "eligible": True, "processed": 0, "deferred": 0}

    monkeypatch.setattr(composition, "build_fuel_balance_store", store)
    monkeypatch.setattr(composition, "build_fuel_finding_service", findings)
    monkeypatch.setattr(scheduled, "run_site", fake_run)
    args = {"tenant_id": "00000000-0000-0000-0000-000000000001", "site_id": "00000000-0000-0000-0000-000000000002",
            "limit": 10, "deadline_at": 1e12}
    out = stages.STAGES["fuel_night"]("postgresql://x", args)
    assert out["code"] == "OK" and seen_args["limit"] == 10 and seen_args["deadline"] is not None
    assert seen_args["deadline"]() is False  # far-future deadline_at
    assert ("store", "postgresql://x", {}) in built and ("findings", "postgresql://x", {}) in built  # no clock override
    assert {b[1] for b in built if b[0] == "dispose"} == {"store", "findings"}
