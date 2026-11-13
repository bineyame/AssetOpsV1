"""UP-1 (D-UP.9, D-UP.10): migration 0061 and the reading-upload store on a real `*_test` database.

The flow (upload -> accepted evidence -> drain -> assessed) and the `analysed(row)` read (D-UP.3) are separate
(resume points in `.agent/UP-1-packet.md`); this file covers the table, its append-only trigger and CHECKs, the store's
insert/get round trip, the ledger reads on an empty ledger, and the refused downgrade.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""
from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import bindparam, text
    from sqlalchemy.dialects.postgresql import ARRAY
    from sqlalchemy.types import Text
    from assetops_backend.analytics.dispatch import ANALYTIC_ID
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    import test_w402_reads_postgres as w402
    from assetops_backend.reading_upload.adapters.postgres_reading_upload_store import PostgresReadingUploadStore
    from assetops_backend.reading_upload.service import ReadingUploadService, UploadRow

START = datetime(2026, 11, 17, 0, 0, tzinfo=timezone.utc)
ENTRY = "service:operator-entry"


def _sent(t, s, **changes) -> "UploadRow":
    row = UploadRow(id=uuid4(), tenant_id=t, site_id=s, file_name="kobo.csv", file_sha256="a" * 64,
                    profile_sha256="b" * 64, state="SENT", refusal_code=None, refusal_field=None, refusal_detail=None,
                    period_start=START, period_end=START + timedelta(hours=6), row_count=24, reading_count=90,
                    blank_count=6, admitted_count=90, held_count=0, message_ids=("m-1", "m-2"),
                    session_ref="field:csv:1", entered_by=ENTRY)
    return replace(row, **changes)


def test_0061_round_trip_append_only_and_checks(store, engine) -> None:  # noqa: F811
    with engine.connect() as c:
        triggers = {r[0] for r in c.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgrelid = 'reading_upload'::regclass AND NOT tgisinternal"))}
        indexes = {r[0] for r in c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'reading_upload'"))}
    assert "reading_upload_immutable" in triggers and "reading_upload_site" in indexes

    _, t, s = w402._setup(store, engine)
    uploads = PostgresReadingUploadStore(URL)
    try:
        sent = uploads.insert(_sent(t, s))
        assert sent.entered_at is not None
        assert uploads.get(t, s, sent.id) == sent  # message_ids come back as a tuple, entered_at as stored
        refused = uploads.insert(_sent(t, s, state="REFUSED", refusal_code="SPAN_MISMATCH",
                                       refusal_field="rows[6].timestamp_utc", refusal_detail="d", period_start=None,
                                       period_end=None, admitted_count=0, message_ids=(), session_ref=None))
        again = uploads.get(t, s, refused.id)
        assert (again.state, again.refusal_code, again.message_ids) == ("REFUSED", "SPAN_MISMATCH", ())
        assert uploads.get(t, uuid4(), sent.id) is None and uploads.get(t, s, uuid4()) is None

        # The ledger reads on a Site with no accepted evidence.
        assert uploads.latest_accepted_by_role(t, s, ["pv_power", "feeder_demand"]) == {}
        assert uploads.latest_accepted_by_role(t, s, []) == {}
        progress = uploads.progress(sent)
        assert (progress.accepted, progress.analysed) == (0, False)
        assert uploads.progress(refused).accepted == 0

        for sql in ("UPDATE reading_upload SET state = 'HELD'", "DELETE FROM reading_upload"):
            with pytest.raises(DBAPIError):
                with engine.begin() as c:
                    c.execute(text(sql))
        for bad in (_sent(t, s, state="REFUSED", refusal_code="SPAN_MISMATCH", admitted_count=0),  # ids on a refusal
                    _sent(t, s, held_count=3),  # held readings without the HELD state
                    _sent(t, s, file_sha256="not-a-sha")):
            with pytest.raises(DBAPIError):
                uploads.insert(bad)
        with engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM reading_upload")).scalar_one() == 2
    finally:
        uploads.dispose()


def test_downgrade_refused_with_uploads_then_allowed(store, engine) -> None:  # noqa: F811
    from alembic import command

    _, t, s = w402._setup(store, engine)
    uploads = PostgresReadingUploadStore(URL)
    try:
        uploads.insert(_sent(t, s))
    finally:
        uploads.dispose()
    cfg = pg_harness._alembic(URL)
    with pytest.raises(Exception, match="reading uploads exist"):
        command.downgrade(cfg, "0060_site_admin_price_entry")
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only trigger does not fire on it
        c.execute(text("TRUNCATE reading_upload"))
    command.downgrade(cfg, "0060_site_admin_price_entry")
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('reading_upload')")).scalar_one() is None
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)


# --- D-UP.12: which FAILED jobs count, and the order Still processing > Analysed > Not analysed ---------------------


def _analysis_case(store, engine, jobs, run_cutoff_after_decided):
    """Ingest real readings, take the upload's message ids and decision time, add the given recompute jobs
    (status, created_at offset, lease_until offset, minutes from the decision) and optionally a qualifying run."""
    installed, t, s = w402._setup(store, engine)
    w402._ingest(engine, installed)
    with engine.begin() as c:
        ids = [r[0] for r in c.execute(text("SELECT message_id FROM accepted_evidence WHERE site_id = :s ORDER BY id"),
                                       {"s": s})][:3]
        lo, decided = c.execute(text(
            "SELECT min(e.source_time), (SELECT max(d.decided_at) FROM ingestion_disposition d JOIN accepted_evidence x "
            "ON x.id = d.accepted_evidence_id AND x.site_id = d.site_id WHERE d.site_id = :s AND d.decision = 'ACCEPTED' "
            "AND x.message_id = ANY(:ids)) FROM accepted_evidence e WHERE e.site_id = :s AND e.message_id = ANY(:ids)"
        ).bindparams(bindparam("ids", type_=ARRAY(Text))), {"s": s, "ids": ids}).one()
        c.execute(text("UPDATE recompute_job SET status = 'DONE', lease_until = NULL WHERE site_id = :s"), {"s": s})  # settle the ingest's own jobs
        job_ids = []
        for status, created, lease in jobs:
            jid = uuid4()
            job_ids.append(jid)
            c.execute(text(
                "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
                "available_at, lease_until, created_at) VALUES (:i, :t, :s, 'dispatch', :lo, :hi, :st, :c, :l, :c)"),
                {"i": jid, "t": t, "s": s, "lo": lo - timedelta(hours=1), "hi": lo + timedelta(hours=8), "st": status,
                 "c": decided + timedelta(minutes=created),
                 "l": None if lease is None else decided + timedelta(minutes=lease)})
        if run_cutoff_after_decided is not None:
            c.execute(text(
                "INSERT INTO analytic_run (id, tenant_id, site_id, analytic_id, model_version, window_start, window_end, "
                "knowledge_cutoff, input_sha256, cohort_status, cohort_sha256, cohort, configuration_sha256, "
                "foundation_revision_ids, binding_set_revision_ids, role_coverage, watermarks, selection, job_id, "
                "status, started_at, completed_at) VALUES (:i, :t, :s, :a, 'v', :lo, :hi, :k, 'x', 'c', 'x', '{}', 'x', "
                "'[]', '[]', '{}', '{}', 'DEFAULT', :j, 'COMPLETED', :k, :k)"),
                {"i": uuid4(), "t": t, "s": s, "a": ANALYTIC_ID, "lo": lo - timedelta(hours=1),
                 "hi": lo + timedelta(hours=8), "k": decided + timedelta(minutes=run_cutoff_after_decided),
                 "j": next((j for j, (st, _, _) in zip(job_ids, jobs) if st == "DONE"), None) or uuid4()})
    row = _sent(t, s, message_ids=tuple(ids), period_start=lo, period_end=lo + timedelta(hours=6))
    uploads = PostgresReadingUploadStore(URL)
    try:
        progress = uploads.progress(row)
        return ReadingUploadService.derived_state(row, progress)
    finally:
        uploads.dispose()


DAY_OLD = -600  # minutes before the decision
CASES = [
    # (id, jobs [(status, created, lease)], run cutoff after decided, expected state)
    ("old-failed-and-later-run", [("FAILED", DAY_OLD, DAY_OLD), ("DONE", 5, None)], 10, "ANALYSED"),
    ("old-failed-no-run", [("FAILED", DAY_OLD, DAY_OLD)], None, "PROCESSING"),
    ("new-failed-no-run", [("FAILED", 5, None)], None, "NOT_ANALYSED"),
    ("old-created-but-leased-after-decided", [("FAILED", DAY_OLD, 5)], None, "NOT_ANALYSED"),
    ("pending-beside-qualifying-run", [("DONE", 5, None), ("PENDING", 6, None)], 10, "PROCESSING"),
]


@pytest.mark.parametrize("name,jobs,run,expected", CASES, ids=[c[0] for c in CASES])
def test_the_analysis_state_follows_d_up_12(store, engine, name, jobs, run, expected) -> None:  # noqa: F811
    assert _analysis_case(store, engine, jobs, run) == expected
