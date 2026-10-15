"""S5-01 phase 1: the imported-Site Overview read on real Postgres, through the existing Overview route.

Packet `tasks/S5-01-site-overview.md` phase 1. The LR-01 late-power fixture (`Walk`, day 2026-10-24) is walked
through the durable workers, and a real schedule tick observes the Site so the S4-02d upstream seam can be
CURRENT. The S5 read is the production composition (`build_site_overview_read`: one upstream seam, the consequence
read with the persisted LR-01 money gate, the Finding store and the evidence ledger). The route is the evidence
router's existing `GET /api/sites/{site}/overview` with the S5 delegate; the S2 comparison and the Performance gate
are injected so each can be closed independently. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
import time
import types
from datetime import timedelta
from decimal import ROUND_CEILING, Decimal

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    import test_s4_finding_store_postgres as finding_cases
    from test_lr01_money_eligibility_postgres import DAY0, Walk, _release_connections  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_assumptions_postgres import run_fixture
    from test_s4_schedule_tick_postgres import FAST, UTC, import_site, make_tick

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_reads import AwaitingComparison
    from assetops_backend.evidence_api import build_evidence_router
    from assetops_backend.scheduling.health import HealthThresholds
    from assetops_backend.scheduling.tick import TickLimits
    from assetops_backend.site_overview.composition import build_site_overview_read
    from assetops_backend.site_overview.route import SiteOverviewRoute
    from assetops_backend.sites.ports import SiteNotFound

DAY = "2026-10-24"


class Gates:
    def __init__(self) -> None:
        self.s2, self.performance = True, True


class Imported:
    def __init__(self, gates) -> None:
        self.gates = gates

    def scope(self, code):
        if not self.gates.s2:
            raise AwaitingComparison("no passing Evidence comparison")
        return types.SimpleNamespace(site_code=code)


class NoLegacy:
    def get_site(self, code):
        raise SiteNotFound(code)


def overview_client(read, scopes: dict, gates: Gates) -> TestClient:
    route = SiteOverviewRoute(read, scopes.get, lambda c, t, s: (gates.performance, f"performance {gates.performance}"),
                              lambda request, code: None, "DEVELOPMENT_TENANT_OPERATOR_CONTEXT (test)")
    app = FastAPI()
    app.include_router(build_evidence_router(types.SimpleNamespace(store=None), NoLegacy(),
                                             imported_reads=Imported(gates), site_overview=route))
    return TestClient(app)


def display_high(text: str) -> str:
    return format(Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_CEILING), "f")


def no_amount(money: dict, state: str) -> None:
    assert money["state"] == state, money
    assert money["amount_low"] is None and money["amount_high"] is None and money["currency"] is None


def test_late_power_day_through_the_overview_route(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    monkeypatch.setattr(finding_cases, "SETUP_AT", DAY0.replace(day=10, hour=12))
    w = Walk(store, engine, capsys, on_time=False)
    tick, _ = make_tick(TickLimits(**FAST))
    ledger = PostgresEvidenceLedger(URL)
    read = build_site_overview_read(URL, ledger, environment=tick.environment)
    tight = build_site_overview_read(URL, ledger, HealthThresholds(stop_after_seconds=1, site_stop_after_seconds=1),
                                     environment=tick.environment)
    other = import_site(store, "KOBO-902", tenant="other-tenant").site
    gates = Gates()
    scopes = {"KOBO-001": ("KOBO-001", w.r.tenant, w.r.site),
              "KOBO-902": ("KOBO-902", other.tenant_id, other.id)}
    client = overview_client(read, scopes, gates)

    def get(query: str = f"date={DAY}", site: str = "KOBO-001", status: int = 200) -> dict:
        response = client.get(f"/api/sites/{site}/overview?{query}")
        assert response.status_code == status, response.text
        return response.json()

    def settle_and_tick() -> None:
        w.settle()
        assert tick.tick().outcome == "COMPLETED"

    try:
        # The S2 comparison gates the whole imported Overview, whatever the Performance gate says.
        gates.s2 = False
        assert get(status=409)["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"
        gates.s2 = True

        # Nothing delivered: an unassessed day is Unknown, never ABSENT or zero.
        body = get()
        assert body["window"] == {"start": "2026-10-24T00:00:00Z", "end": "2026-10-25T00:00:00Z",
                                  "utc_date": DAY, "bounds": "[start, end)"}
        assert body["assessment"]["state"] == "UNKNOWN" and body["known_finding"] is None
        no_amount(body["money"], "UPSTREAM_UNASSESSED")
        assert body["finding_list"]["state"] == "UNAVAILABLE"

        # Delivered, not yet assessed: S3 work pending.
        w.deliver_first()
        body = get()
        assert body["freshness"]["state"] in ("PENDING", "STALE_PROJECTION")
        no_amount(body["money"], "UPSTREAM_PENDING")
        assert body["watermarks"]["accepted_source"]["count"] > 0

        # Settled, priced and observed: the Finding is selected; the late mean is missing, so its quantity is not
        # available (a real POWER_COVERAGE_GAP), no amount.
        run_fixture(w.prices, capsys, "v1")
        settle_and_tick()
        body = get()
        r1 = w.latest()
        assert body["freshness"]["state"] == "CURRENT", body["freshness"]
        assert (body["known_finding"]["id"], body["known_finding"]["revision_id"]) == (
            str(r1["finding_id"]), str(r1["id"]))
        assert body["assessment"]["run_id"] and body["assessment"]["window_assessment_revision_id"]
        no_amount(body["money"], "QUANTITY_UNAVAILABLE")
        assert body["money"]["eligibility"]["state"] == "ELIGIBLE"
        first_head = body["money"]["consequence_revision_id"]
        assert first_head == w.read(r1)["consequence"]["id"]
        pin = f"date={DAY}&finding_id={r1['finding_id']}&finding_revision_id={r1['id']}"

        # Late acceptance: S3 work pending; the pinned Finding is retained with its exact links, no amount.
        w.deliver_late()
        late = get(pin)
        assert late["known_finding"]["id"] == str(r1["finding_id"])
        assert late["known_finding"]["selected_by"] == "PINNED_RETAINED_WHILE_BASIS_INCOMPLETE"
        no_amount(late["money"], "UPSTREAM_STALE")  # an older result exists under advanced basis

        # Settled: the series limit withholds money; the recorded consequence ID is kept.
        settle_and_tick()
        r2 = w.latest()
        withheld = get(pin)
        assert withheld["known_finding"]["id"] == str(r2["finding_id"])
        assert withheld["known_finding"]["revision_id"] == str(r2["id"])
        no_amount(withheld["money"], "WITHHELD_GENERATOR_SERIES")
        recorded = withheld["money"]["consequence_revision_id"]
        assert recorded and recorded != first_head

        # Attested before the tick: the raw gate pends; the S5 upstream status names the reason; no amount.
        w.attest()
        pending = get(f"date={DAY}&finding_id={r2['finding_id']}&finding_revision_id={r2['id']}")
        assert pending["money"]["eligibility"]["state"] == "PENDING_REASSESSMENT"
        assert pending["known_finding"]["id"] == str(r2["finding_id"])
        # Packet precedence puts upstream before the LR gate, so the visible state is UPSTREAM_STALE (the requeued
        # S3 job) while the raw gate reads PENDING_REASSESSMENT; the owner walkthrough wording follows this.
        no_amount(pending["money"], "UPSTREAM_STALE")
        assert {"S3_STALE_PROJECTION", "LIVE_JOB"} <= set(pending["freshness"]["reasons"])

        # Reassessed and observed: ELIGIBLE, exact-head CURRENT PRICED, upstream CURRENT -> the display amount.
        settle_and_tick()
        r3 = w.latest()
        body = get()
        money = body["money"]
        assert money["state"] == "PRICED", money
        assert money["finding_revision_id"] == str(r3["id"]) != str(r2["id"])
        head = w.read(r3)["consequence"]
        assert money["consequence_revision_id"] == head["id"] == money["seam_head_consequence_revision_id"]
        assert money["consequence_revision_id"] not in (recorded, first_head)
        assert (money["amount_low"], money["amount_high"]) == (head["display"]["amount_low"],
                                                                head["display"]["amount_high"])
        assert money["amount_high"] == "15.82" == display_high(head["amount"]["high"])
        assert money["links"]["consequence"] == (f"/api/sites/KOBO-001/findings/{r3['finding_id']}/financial-"
                                                 f"consequences?revision_id={r3['id']}&consequence_revision_id="
                                                 f"{head['id']}")
        assert set(money["links"]["evidence_records"]) == set(head["lineage"]["evidence_ids"])
        same_day = get("from=2026-10-24T00:00:00Z&to=2026-10-25T00:00:00Z")
        assert same_day["money"]["consequence_revision_id"] == head["id"]  # reload of the same day

        # Architect LR-01 deviations item 2: a stopped schedule leaves the raw gate ELIGIBLE and blocks the amount.
        time.sleep(1.5)
        stopped = overview_client(tight, scopes, gates).get(f"/api/sites/KOBO-001/overview?date={DAY}").json()
        assert stopped["money"]["eligibility"]["state"] == "ELIGIBLE"
        no_amount(stopped["money"], "UPSTREAM_STALE")
        assert "SCHEDULE_STOPPED" in stopped["freshness"]["reasons"]

        # Performance closed with the comparison passed: no current claim; only a pinned Finding as audit.
        gates.performance = False
        closed = get()
        assert closed["assessment"]["state"] == "CLOSED" and closed["known_finding"] is None
        no_amount(closed["money"], "SOURCE_CLOSED")
        audit = get(f"date={DAY}&finding_id={r3['finding_id']}&finding_revision_id={r3['id']}")
        assert audit["known_finding"]["audit_only"] is True and audit["known_finding"]["id"] == str(r3["finding_id"])
        no_amount(audit["money"], "SOURCE_CLOSED")
        gates.performance = True

        # Tenant/Site scope: another tenant's Site cannot pin this Finding.
        assert get(pin, site="KOBO-902", status=404)["detail"]["code"] == "FINDING_PIN_NOT_FOUND"

        # Another day: a different selection, never this Finding's amount.
        other_day = get("date=2026-10-26")
        assert other_day["window"]["utc_date"] == "2026-10-26" and other_day["money"]["amount_high"] is None
    finally:
        read.dispose()
        tight.dispose()
        ledger.dispose() if hasattr(ledger, "dispose") else None
        w.close()
