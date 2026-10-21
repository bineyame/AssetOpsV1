"""W4-02 final review ruling 3 (M4): the empty-legacy Overview reason.

A persisted NO_LEGACY_EVIDENCE cutover basis with no Dispatch comparison report states its own plain reason; a
legacy import without a passing comparison keeps the gate's existing reason. Never inferred from a missing report.
"""

from __future__ import annotations

import types

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics.performance_comparison import (
    NO_LEGACY_EVIDENCE_REASON,
    NO_REPORT_REASON,
    basis_aware_gate,
    basis_reason,
)
from assetops_backend.evidence_api import build_evidence_router
from assetops_backend.site_overview.route import SiteOverviewRoute
from assetops_backend.sites.ports import SiteStoreUnavailable
from test_s5_overview_read import Imported, LegacySites, S, T, World

RULED = "No legacy evidence was imported for this Site. Dispatch has no assessed comparison for this selection."


def test_ruled_reason_text_is_exact_and_plain() -> None:
    assert NO_LEGACY_EVIDENCE_REASON == RULED
    assert "file-backed" not in RULED


def test_basis_reason_only_replaces_the_no_report_reason_for_an_empty_legacy_basis() -> None:
    assert basis_reason(False, NO_REPORT_REASON, True) == RULED
    assert basis_reason(False, NO_REPORT_REASON, False) == NO_REPORT_REASON  # legacy import keeps the gate reason
    other = "The assessment lineage could not be read."
    assert basis_reason(False, other, True) == other
    assert basis_reason(True, "open", True) == "open"


def test_basis_aware_gate_reads_the_basis_only_when_needed_and_keeps_the_reason_on_failure() -> None:
    reads: list = []

    def basis(value):
        def read(t, s):
            reads.append((t, s))
            return value
        return read

    def closed(code, t, s):
        return False, NO_REPORT_REASON

    assert basis_aware_gate(closed, basis(True))("X", T, S) == (False, RULED)
    assert basis_aware_gate(closed, basis(False))("X", T, S) == (False, NO_REPORT_REASON)
    reads.clear()
    assert basis_aware_gate(lambda c, t, s: (True, "open"), basis(True))("X", T, S) == (True, "open")
    assert reads == []

    def down(t, s):
        raise SiteStoreUnavailable("down")

    assert basis_aware_gate(closed, down, (SiteStoreUnavailable,))("X", T, S) == (False, NO_REPORT_REASON)
    assert basis_aware_gate(closed, None) is closed


def _overview(*, empty_legacy: bool, passed: bool) -> TestClient:
    overview = SiteOverviewRoute(World().service(), {"KOBO-001": ("KOBO-001", T, S)}.get,
                                 lambda c, t, s: (False, NO_REPORT_REASON), lambda r, c: None, "DEV",
                                 no_legacy_basis=lambda t, s: empty_legacy)
    app = FastAPI()
    app.include_router(build_evidence_router(types.SimpleNamespace(store=None), LegacySites(),
                                             imported_reads=Imported(passed), site_overview=overview))
    return TestClient(app)


def test_overview_states_the_empty_legacy_reason_for_a_persisted_basis() -> None:
    body = _overview(empty_legacy=True, passed=False).get("/api/sites/KOBO-001/overview?date=2026-10-24").json()
    assert body["assessment"]["state"] == "CLOSED"
    assert body["assessment"]["reason"] == RULED
    assert "file-backed" not in str(body)


def test_overview_keeps_the_gate_reason_for_a_legacy_import() -> None:
    body = _overview(empty_legacy=False, passed=True).get("/api/sites/KOBO-001/overview?date=2026-10-24").json()
    assert body["assessment"]["state"] == "CLOSED"
    assert body["assessment"]["reason"] == NO_REPORT_REASON
    assert RULED not in str(body)
