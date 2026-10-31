"""FIX-S4-DOMAIN (build-sheet DEMO-SPARSE Addendum 3, ruling 1): the mini dispatch matcher reads only
mini_grid / dispatch Findings.

A Site holding an open cold Finding (`episode_end` NULL, as `cold_apply` writes an open excursion) beside the
mini dispatch evidence: before the fix `PostgresFindingStore.episodes` returned the cold Finding too and
`plan_pass` failed in `margin_windows` on `None + timedelta`. The pass must complete and plan only the mini
episode, and the cold Finding must stay readable under its own domain and analytic.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_finding_store_postgres import SPEC, CaseRunner

    from assetops_backend.analytics.adapters.postgres_finding_store import (
        COLD_MATCHER_VERSION, COLD_MECHANISMS, COLD_TITLES)
    from assetops_backend.analytics.cold import EXCURSION_ANALYTIC

COLD_AT = datetime(2026, 10, 6, 7, 0, tzinfo=timezone.utc)


def insert_open_cold_finding(runner) -> str:
    """One cold excursion Finding whose only revision is open (no `episode_end`), on the runner's Site."""
    t, s = runner.tenant, runner.site
    with runner.engine.begin() as c:
        rev, run = c.execute(text("SELECT id, analytic_run_id FROM assessment_revision WHERE tenant_id = :t "
                                  "AND site_id = :s ORDER BY window_start LIMIT 1"), {"t": t, "s": s}).one()
        asset = c.execute(text("SELECT id FROM asset WHERE tenant_id = :t AND site_id = :s ORDER BY id LIMIT 1"),
                          {"t": t, "s": s}).scalar_one()
        fid = uuid4()
        c.execute(text(
            "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
            "generator_asset_id, subject_asset_id, anchor_start, anchor_assessment_revision_id, cohort_sha256, "
            "matcher_version, opened_at, created_at) VALUES (:id, :t, :s, :k, 'cold_chain', :m, :a, NULL, "
            ":subject, :anchor, :rev, NULL, :mv, :now, :now)"),
            {"id": fid, "t": t, "s": s, "k": f"cold:EXCURSION:{fid}", "m": COLD_MECHANISMS["EXCURSION"],
             "a": EXCURSION_ANALYTIC, "subject": asset, "anchor": COLD_AT, "rev": rev, "mv": COLD_MATCHER_VERSION,
             "now": COLD_AT})
        # The cold-consequence enqueue trigger needs a cold assessment whose Foundation basis has one COLD_ROOM;
        # this mini Site has none. It is disabled for this one insert, inside this transaction only (DDL is
        # transactional in Postgres), and re-enabled before commit: the matcher read never depends on it.
        c.execute(text("ALTER TABLE finding_revision DISABLE TRIGGER cold_consequence_dirty_on_finding_revision"))
        c.execute(text(
            "INSERT INTO finding_revision (id, tenant_id, site_id, finding_id, domain, revision_no, transition, "
            "lifecycle, claim_level, title, mechanism, matcher_version, analytic_id, model_version, "
            "assessment_revision_id, analytic_run_id, episode_start, episode_end, claim, limitations, basis_sha256, "
            "support_sha256, cited_evidence_sha256, input_evidence_sha256, created_at) VALUES (:id, :t, :s, :f, "
            "'cold_chain', 1, 'OPENED', 'SUPPORTED', 'UNKNOWN', :title, :m, :mv, :a, '1', :rev, :run, :es, NULL, "
            "CAST(:claim AS jsonb), '[]'::jsonb, :b, :b, :b, :b, :now)"),
            {"id": uuid4(), "t": t, "s": s, "f": fid, "title": COLD_TITLES["EXCURSION"],
             "m": COLD_MECHANISMS["EXCURSION"], "mv": COLD_MATCHER_VERSION, "a": EXCURSION_ANALYTIC, "rev": rev,
             "run": run, "es": COLD_AT, "claim": json.dumps({"kind": "EXCURSION", "open": True}), "b": "0" * 64,
             "now": COLD_AT})
        c.execute(text("ALTER TABLE finding_revision ENABLE TRIGGER cold_consequence_dirty_on_finding_revision"))
    return str(fid)


@pytest.fixture()
def runner(store, engine):
    owned = CaseRunner(store, engine)
    yield owned
    pg_harness.dispose(owned.findings)


def test_an_open_cold_finding_does_not_reach_the_mini_matcher(runner) -> None:
    f01 = SPEC["cases"][0]
    for step in f01["steps"][:2]:  # deliver and assess: the mini dispatch window, no Finding yet
        runner.step(step)
    cold = insert_open_cold_finding(runner)
    # non-vacuous: the open cold episode is on this Site, readable under its own domain and analytic
    [held] = runner.findings.episodes(runner.tenant, runner.site, "cold_chain", EXCURSION_ANALYTIC)
    assert held.finding_id == cold and held.episode_end is None
    assert runner.findings.episodes(runner.tenant, runner.site) == []  # the default is mini_grid / dispatch

    outcome = runner.match()  # failed in margin_windows (None + timedelta) before the fix

    assert outcome.planned == 1 and len(outcome.finding_ids) == 1
    rows = runner.reload()
    mini = [f for f in rows["findings"] if f["domain"] == "mini_grid"]
    assert [str(f["id"]) for f in mini] == list(outcome.finding_ids)
    assert mini[0]["anchor_start"] == datetime(2026, 10, 6, 8, tzinfo=timezone.utc)
    [episode] = runner.findings.episodes(runner.tenant, runner.site)
    assert str(episode.finding_id) == outcome.finding_ids[0] and episode.episode_end is not None
    # the cold Finding is untouched: still one revision, still open
    cold_revs = [r for r in rows["revisions"] if str(r["finding_id"]) == cold]
    assert len(cold_revs) == 1 and cold_revs[0]["episode_end"] is None
    assert runner.match().revision_ids == ()  # a replay plans nothing
