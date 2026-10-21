"""W4-02 unit 4 step 2: `mini_depth/inputs.py` over the installed MG-W402-001 Site and its authored accepted rows.

Pins the Site zone, Foundation properties, the critical LOAD asset, SFC and loads; the Q13 cutoff includes a row
received/decided exactly at the cutoff and excludes one a microsecond later (q5 ruling 5); fuel and backup see only
pinned rows. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
import re
from datetime import date, timedelta
from decimal import Decimal

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import enable
    from test_w203_cold_migration_postgres import _replica
    from test_w402_authored_v4_postgres import RECEIVED, cases, ingestion, install, principal, snapshot

    from assetops_backend.financials.fuel_cost import MULTIPLIER
    from assetops_backend.mini_depth import rules
    from assetops_backend.mini_depth.inputs import load_hour_inputs, local_noon


def test_w402_hour_inputs_pins_and_cutoff(store, engine) -> None:  # noqa: F811
    installed = install(store)
    site_id = installed.result.site.id
    enable(engine, site_id)
    doc, sha = snapshot(engine, installed.binding_set.id)
    service = ingestion()
    for b in cases.build_batches(cases.load_spec(), doc, sha, "positive"):
        service.submit(principal(doc), b.body.encode("utf-8"))
    tenant_id = installed.result.site.tenant_id
    window = local_noon(date(2026, 10, 6), "Africa/Nairobi")
    with engine.connect() as c:
        assets = dict(c.execute(text("SELECT asset_code, id FROM asset WHERE site_id = :s"), {"s": site_id}).all())

    def load(k):
        with engine.connect() as c:
            c.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
            return load_hour_inputs(c, tenant_id, site_id, window, k)

    hi = load(RECEIVED)
    assert (hi.site_timezone, hi.local_day, hi.knowledge_cutoff) == ("Africa/Nairobi", date(2026, 10, 6), RECEIVED)
    assert hi.binding_set_revision_id == installed.binding_set.id
    assert (hi.renewable.pv_uncertainty_kw, hi.renewable.retained_margin_kw, hi.recovery_target_min) == (
        Decimal("1.0"), Decimal("3.0"), Decimal("5.0"))
    assert set(hi.property_revision_ids.values()) == {hi.foundation_revision_id}
    assert hi.critical_asset_id == assets["load-clinic"] == hi.renewable.critical_asset_id
    clinic = next(load_ for load_ in hi.loads if load_.asset_id == assets["load-clinic"])
    assert (clinic.critical, clinic.feeder_request_bound, clinic.load_label) == (True, False, "Health clinic")
    assert [s.value_l_per_kwh for s in hi.fuel.sfc] == [Decimal("0.3")] and hi.fuel.upper_multiplier == MULTIPLIER
    assert hi.generator_asset_id == assets["generator"] and hi.tank_asset_id == assets["fuel-tank"]
    assert hi.selected and hi.committed_watermark == RECEIVED
    assert hi.digest_basis()["site_timezone"] == "Africa/Nairobi" and re.fullmatch(r"sha256:[0-9a-f]{64}", hi.input_sha256)
    # Pinned-only domain inputs (q4 ruling 3, q5 ruling 4).
    assert {r.asset_id for r in hi.fuel_readings()} <= {hi.generator_asset_id, hi.tank_asset_id}
    assert {r.asset_id for r in hi.backup_readings()} <= {hi.generator_asset_id, hi.critical_asset_id}
    hour = rules.assess_backup_hour(hi.window, hi.observations, hi.backup_readings(), hi.recovery_target_min,
                                    critical_asset_id=hi.critical_asset_id)
    assert hour.outage_count == 1
    # q3 ruling 4: the outage's ENERGIZED witness is selected (in the hour or as the last state before it).
    assert any(o.role == rules.SITE_SUPPLY and o.state == "ENERGIZED" and o.source_time < hour.chains[0].outage_start
               for o in hi.observations)

    # Q13 / q5 ruling 5: equality at the cutoff is included; a microsecond later (received or decided) is not.
    late_received, late_decided = hi.readings[0].evidence_id, hi.readings[1].evidence_id
    after = RECEIVED + timedelta(microseconds=1)
    _replica(engine, f"UPDATE accepted_evidence SET received_at = '{after.isoformat()}' WHERE id = '{late_received}'",
             f"UPDATE ingestion_disposition SET decided_at = '{after.isoformat()}' "
             f"WHERE accepted_evidence_id = '{late_decided}'")
    cut = load(RECEIVED)
    assert {late_received, late_decided}.isdisjoint(cut.evidence_ids)
    assert set(cut.evidence_ids) == set(hi.evidence_ids) - {late_received, late_decided}
    assert cut.input_sha256 != hi.input_sha256
    assert {late_received, late_decided} <= set(load(after).evidence_ids)
    assert not load(RECEIVED - timedelta(microseconds=1)).selected
