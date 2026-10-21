"""W4-02 closure 5: the resolved Site type gates cold enqueue in `PostgresEvidenceLedger.decide_chunk`.

Even a future role name shared with `COLD_ROLE_NAMES` enqueues no `cold_chain` job on a MINIGRID Site; a cold v4
batch on COLD-LAB-001 still does; a missing tenant/Site lookup fails the chunk with nothing written.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import enable
    from test_w402_authored_v4_postgres import INSTALLED, cases, ingestion, install, principal, snapshot

    from assetops_backend.evidence.adapters import postgres_evidence_ledger as adapter
    from assetops_backend.evidence.ledger import LedgerUnavailable
    from assetops_contracts.source_envelope import canonical_json
    from assetops_backend.sites.cold_lab import V4_EFFECTIVE_FROM, install_cold_lab


def jobs(engine, site_id) -> dict[str, int]:
    with engine.connect() as c:
        return {r.domain: r.n for r in c.execute(text(
            "SELECT domain, count(*) AS n FROM recompute_job WHERE site_id = :s GROUP BY domain"), {"s": site_id})}


def dispositions(engine, site_id) -> int:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM ingestion_disposition WHERE site_id = :s"),
                         {"s": site_id}).scalar_one()


def chain_batches(engine, store):
    installed = install(store)
    enable(engine, installed.result.site.id)
    doc, sha = snapshot(engine, installed.binding_set.id)
    variant = {"variant": "gate", "sequence_epoch": "w402-gate", "hours": [], "means_kw": [], "points": [],
               "backup_chain": {"day": "2026-10-06", "correlation_id": "w402-gate", "mean_overrides_kw": [],
                                "states": [{"device": "mini-primary-bus-meter", "signal": "state",
                                            "at": "2026-10-06T09:10:00Z", "value": "LOST"}],
                                "events": []}}
    spec = {**cases.load_spec(), "variants": [variant]}
    return installed.result.site.id, doc, cases.build_batches(spec, doc, sha, "gate")


def test_site_type_gates_cold_jobs_even_for_shared_role(store, engine, monkeypatch) -> None:
    # A mini v4 STATE row whose role is (temporarily) also a cold role name: mini work only, no cold_chain job.
    mg_site, doc, batches = chain_batches(engine, store)
    monkeypatch.setattr(adapter, "COLD_ROLE_NAMES", adapter.COLD_ROLE_NAMES | {"site_supply_state"})
    for b in batches:
        (d,) = ingestion().submit(principal(doc), b.body.encode("utf-8")).receipt.dispositions
        assert d.decision == "ACCEPTED"
    got = jobs(engine, mg_site)
    assert got.get("cold_chain", 0) == 0 and got.get("mini_backup", 0) >= 1, got
    with engine.connect() as c:  # the accepted row's own local hour is queued (coalesced with any pending one)
        hour = c.execute(text(
            "SELECT count(*) FROM recompute_job WHERE site_id = :s AND domain = 'mini_backup' AND status = 'PENDING' "
            "AND window_start = '2026-10-06T09:00:00Z' AND window_end = '2026-10-06T10:00:00Z'"),
            {"s": mg_site}).scalar_one()
    assert hour == 1

    # A cold v4 batch on COLD-LAB-001 still creates its cold_chain job.
    cold = install_cold_lab(store, tenant_slug="demo", clock=Clock(INSTALLED))
    enable(engine, cold.site.id)
    current = next(s for s in store.binding_sets(cold.tenant.id, cold.site.id)
                   if s.valid_from == V4_EFFECTIVE_FROM and s.superseded_at is None)
    cold_doc, cold_sha = snapshot(engine, current.id)
    probe = next(r for r in cold_doc["bindings"] if (r["device_id"], r["signal_id"]) == ("chamber-probe", "temperature"))
    planned = cases.Planned("chamber-probe", "temperature", datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc),
                            "POINT", "3", "degC")
    document = json.loads(cases._envelope(cold_doc, probe, "w402-cold", 1, planned))
    document["schema"]["version"] = 4
    document["payload"].update(session_id=None, connector_id=None)
    body = cases.seal_for(cold_doc, cold_sha, probe, [canonical_json(document)])
    (d,) = ingestion().submit(principal(cold_doc), body.encode("utf-8")).receipt.dispositions
    assert d.decision == "ACCEPTED", d
    assert jobs(engine, cold.site.id).get("cold_chain") == 1

    # A missing tenant/Site lookup aborts the chunk: no new disposition, no job.
    before = (dispositions(engine, mg_site), jobs(engine, mg_site))
    real = adapter._site_type_on
    monkeypatch.setattr(adapter, "_site_type_on", lambda c, tenant_id, site_id: real(c, tenant_id, uuid4()))
    resent = cases.build_batches({**cases.load_spec(), "variants": [{
        "variant": "gate2", "sequence_epoch": "w402-gate-2", "hours": [], "means_kw": [], "points": [],
        "backup_chain": {"day": "2026-10-06", "correlation_id": "w402-gate-2", "mean_overrides_kw": [], "events": [],
                         "states": [{"device": "mini-primary-bus-meter", "signal": "state",
                                     "at": "2026-10-06T09:20:00Z", "value": "ENERGIZED"}]}}]},
        doc, snapshot(engine, install(store).binding_set.id)[1], "gate2")
    with pytest.raises(LedgerUnavailable):
        ingestion().submit(principal(doc), resent[0].body.encode("utf-8"))
    assert (dispositions(engine, mg_site), jobs(engine, mg_site)) == before
