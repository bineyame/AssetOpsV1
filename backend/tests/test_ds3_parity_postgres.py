"""DS3 (spec `specs/DS3-bulk-loader/spec.md` §3, §4 test 8; D-DS3.3, D-DS3.10, D-DS3.11): the bulk path stores what
central ingestion stores.

One seed (`ds3pseed`: the converted Kobo Site, enabled, its binding sets relabelled `minigrid-roles-4`), two clones of
it (`ds3preal`, `ds3pbulk`), the same eleven batches into each: two Kobo days by `BatchIngestionService.submit`, the
same bytes by `BulkEvidenceLoad.load`, plus one v4 batch. Every comparison reads both databases with its own SELECT,
never through the bulk path or the ledger adapter (W2). The census counts every base table at run time.
Requires ASSETOPS_TEST_DATABASE_URL (backend/TESTING.md).
"""

from __future__ import annotations

import json
import os

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text
    from test_ds3_bulk_load_postgres import DAY6, DAY7, census, kobo_days, seed_database
    from test_w200_source_events_postgres import patched_v4

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.bulk_load import BulkEvidenceLoad, BulkLoaded
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text

#: Hand counts (spec §3): 5 devices x 2 days, 96 envelopes per device per day; the v4 slice adds one batch of three (D-DS3.20).
KOBO_BATCHES, KOBO_ENVELOPES = 10, 960
V4_ENVELOPES = 3
#: Tables a load writes on this seed besides the two with their own rules: the delta on both paths (literals, W2).
#: `recompute_job` and `chain_input_change` hold per-statement or per-chunk rows and are compared by their rules.
EQUAL_DELTAS = {"ingestion_batch": KOBO_BATCHES, "accepted_evidence": KOBO_ENVELOPES,
                "ingestion_disposition": KOBO_ENVELOPES}
V4_EQUAL_DELTAS = {"ingestion_batch": 1, "accepted_evidence": V4_ENVELOPES, "ingestion_disposition": V4_ENVELOPES}
OWN_RULES = ("recompute_job", "chain_input_change", "event_outbox")
#: D-DS3.10's stated limit: no Finding or assessment revision exists on the seed, so nothing is written here.
ZERO_BY_LIMIT = ("financial_consequence_work", "ev_consequence_work", "evidence_rejection", "batch_refusal",
                 "batch_publication_link")

EVIDENCE_SQL = (
    "SELECT tenant_id, site_id, ordinal, gateway_id, source_id, message_id, sequence_epoch, sequence, device_id, "
    "signal_id, asset_id, role, family, measurement, source_time, published_at, interval_start, interval_end, quality, "
    "unavailable_reason, original_value_text, original_unit, normalized_value_text, normalized_unit, conversion_kind, "
    "envelope_sha256, envelope_text, foundation_revision_id, binding_set_revision_id, binding_revision_id, "
    "configuration_outdated, source_mode, record_kind, event_id, correlation_id, session_id, connector_id, actor, "
    "outcome FROM accepted_evidence ORDER BY source_id, message_id"
)
BATCH_SQL = (
    "SELECT tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, schema_version, source_mode, "
    "foundation_revision_id, binding_set_revision_id, snapshot_sha256, batch_text, status, total_count, "
    "processed_count, accepted_count, duplicate_count, rejected_count, conflict_count "
    "FROM ingestion_batch ORDER BY external_batch_id"
)
DISPOSITION_SQL = (
    "SELECT b.external_batch_id, d.ordinal, d.message_id, d.decision, e.message_id FROM ingestion_disposition d "
    "JOIN ingestion_batch b ON b.id = d.batch_id LEFT JOIN accepted_evidence e ON e.id = d.accepted_evidence_id "
    "ORDER BY b.external_batch_id, d.ordinal"
)


def _columns(c) -> set[str]:
    return set(c.execute(text("SELECT column_name FROM information_schema.columns "
                              "WHERE table_schema = current_schema() AND table_name = 'accepted_evidence'")).scalars())


def _readings(c):
    """Every accepted v3 reading's instant (interval start, else source time)."""
    rows = c.execute(text("SELECT coalesce(interval_start, source_time) AS at, envelope_text FROM accepted_evidence")).all()
    instants = [r.at for r in rows if json.loads(r.envelope_text)["schema"]["version"] == 3]
    assert len(instants) == KOBO_ENVELOPES
    return instants


def _dispatch_jobs(c):
    return c.execute(text("SELECT window_start, window_end FROM recompute_job "
                          "WHERE domain = 'dispatch' AND status = 'PENDING'")).all()


def _other_jobs(c):
    return sorted(c.execute(text("SELECT domain, window_start, window_end, status FROM recompute_job "
                                 "WHERE domain NOT IN ('dispatch', 'cold_chain')")).all())


def _change_scopes(c, baseline_ids):
    rows = c.execute(text("SELECT change_id, tenant_id, site_id, table_name FROM chain_input_change")).all()
    new = [r for r in rows if r.change_id not in baseline_ids]
    return {(r.tenant_id, r.site_id, r.table_name) for r in new}, len(new)


_COVER_KEYS = frozenset({"roles", "asset_ids", "analytic_ids", "domain", "status", "key", "span", "window", "valid",
                         "windows"})


def _cover(subjects) -> dict:
    """D-DS3.21: what a consumer reads from event subjects (roles, asset and analytic ids, domain, status, key, and the
    least start and greatest end over span, window, valid and each pair of windows), computed from the JSON here."""
    sets: dict[str, set] = {name: set() for name in ("roles", "asset_ids", "analytic_ids", "domain", "status", "key")}
    starts, ends = [], []
    for s in subjects:
        unknown = set(s) - _COVER_KEYS
        assert not unknown, f"subject key(s) {sorted(unknown)} are outside the D-DS3.21 cover: add them to _cover or rule them out"
        for name in ("roles", "asset_ids", "analytic_ids"):
            sets[name] |= set(s.get(name) or ())
        for name in ("domain", "status", "key"):
            if s.get(name) is not None:
                sets[name].add(s[name])
        pairs = [s[k] for k in ("span", "window", "valid") if s.get(k)] + list(s.get("windows") or ())
        for start, end in pairs:
            if start is not None:
                starts.append(start)
            if end is not None:
                ends.append(end)
    return {**{k: sorted(v) for k, v in sets.items()}, "start": min(starts, default=None), "end": max(ends, default=None)}


def _outbox_groups(c, baseline_ids) -> dict:
    rows = c.execute(text("SELECT event_id, tenant_id, site_id, source, type, subject FROM event_outbox")).all()
    groups: dict = {}
    for r in rows:
        if r.event_id not in baseline_ids:
            groups.setdefault((r.tenant_id, r.site_id, r.source, r.type), []).append(r.subject)
    return groups


def _v4_batch(kit, monkeypatch) -> bytes:
    """D-DS3.20: the v4 slice is the three shapes the real path accepts (a refused `v4.delta` is a test-6 case)."""
    v4 = patched_v4(kit, monkeypatch)
    return kit.seal([v4.event(100001, "START_RESULT", "evt-1", "FAILED"), v4.start(100002, "start-1"),
                     v4.point(100003)]).encode("utf-8")


def run_parity(monkeypatch, *, with_v4: bool) -> str:
    """Runs §3 and asserts every rule but the unnamed-table census rule; returns the unnamed tables as text."""
    seed, kit, baseline = seed_database("ds3pseed", relabel=True)
    urls = [seed]
    try:
        real = pg_harness.clone_database("ds3preal", seed)
        urls.append(real)
        bulk = pg_harness.clone_database("ds3pbulk", seed)
        urls.append(bulk)
        with _engine(seed) as c:
            baseline_changes = set(c.execute(text("SELECT change_id FROM chain_input_change")).scalars())
            baseline_events = set(c.execute(text("SELECT event_id FROM event_outbox")).scalars())

        batches = kobo_days(kit, [DAY6, DAY7])
        assert (len(batches), sum(len(_envelopes(b)) for b in batches)) == (KOBO_BATCHES, KOBO_ENVELOPES)
        expected = dict(EQUAL_DELTAS)
        if with_v4:
            batches.append(_v4_batch(kit, monkeypatch))
            expected = {t: n + V4_EQUAL_DELTAS[t] for t, n in expected.items()}

        real_ledger = PostgresEvidenceLedger(real)
        try:
            service = BatchIngestionService(real_ledger)
            for body in batches:
                answer = service.submit(kit.principal, body)
                assert answer.status == 200 and answer.receipt.status == "COMPLETED", answer
                # Spec §3: the real path accepts every ordinal (the v4 slice's four included).
                assert answer.receipt.counts.accepted == answer.receipt.counts.total, answer.receipt.dispositions
        finally:
            pg_harness.dispose(real_ledger)
        bulk_ledger = PostgresEvidenceLedger(bulk)
        try:
            assert BulkEvidenceLoad(bulk_ledger).load(batches) == BulkLoaded(
                len(batches), 0, expected["accepted_evidence"])
        finally:
            pg_harness.dispose(bulk_ledger)

        with _engine(real) as r, _engine(bulk) as b:
            # Equal rows, receipt and decision instants and generated IDs apart.
            assert {"record_kind", "event_id", "correlation_id", "session_id", "connector_id", "actor",
                    "outcome"} <= _columns(r)
            real_evidence = r.execute(text(EVIDENCE_SQL)).all()
            assert len(real_evidence) == expected["accepted_evidence"]
            assert b.execute(text(EVIDENCE_SQL)).all() == real_evidence
            if with_v4:
                assert sum(1 for row in real_evidence if row.record_kind is not None) == 2  # the v4 columns compared (event, start; the point has none)
            assert b.execute(text(BATCH_SQL)).all() == r.execute(text(BATCH_SQL)).all()
            assert b.execute(text(DISPOSITION_SQL)).all() == r.execute(text(DISPOSITION_SQL)).all()

            # Recompute jobs (D-DS3.3, D-DS3.10).
            for c in (r, b):
                windows = _dispatch_jobs(c)
                assert all(any(s <= t < e for s, e in windows) for t in _readings(c))
            assert len(_dispatch_jobs(b)) <= min(len(_dispatch_jobs(r)), len(batches))
            real_other = _other_jobs(r)
            assert any(job.domain.startswith("mini") for job in real_other), real_other  # the relabel took effect
            assert _other_jobs(b) == real_other

            # Census: every base table of the schema, enumerated at run time.
            after_real, after_bulk = census(r), census(b)
            delta_real = {t: n - baseline.get(t, 0) for t, n in after_real.items()}
            delta_bulk = {t: n - baseline.get(t, 0) for t, n in after_bulk.items()}
            assert set(delta_real) == set(delta_bulk) == set(baseline)
            for table, count in expected.items():
                assert (delta_real[table], delta_bulk[table]) == (count, count), table
            for table in ZERO_BY_LIMIT:
                if table in delta_real:
                    assert (delta_real[table], delta_bulk[table]) == (0, 0), table
            unnamed = {t for t in delta_real if (delta_real[t] or delta_bulk[t]) and t not in expected
                       and t not in OWN_RULES}
            unnamed_text = ", ".join(f"{t}={delta_real[t]}/{delta_bulk[t]}" for t in sorted(unnamed))
            real_scopes, real_count = _change_scopes(r, baseline_changes)
            bulk_scopes, bulk_count = _change_scopes(b, baseline_changes)
            assert real_scopes and bulk_scopes == real_scopes and bulk_count <= real_count
            print("\nDS3 parity census deltas (real/bulk): " + ", ".join(
                f"{t}={delta_real[t]}/{delta_bulk[t]}" for t in sorted(delta_real) if delta_real[t] or delta_bulk[t]))
            # event_outbox (D-DS3.21): the event cover per (Site, source, type); never loosened to pass.
            real_groups, bulk_groups = _outbox_groups(r, baseline_events), _outbox_groups(b, baseline_events)
            assert real_groups and set(bulk_groups) == set(real_groups)
            for key, subjects in real_groups.items():
                assert len(bulk_groups[key]) <= len(subjects), key
                real_cover, bulk_cover = _cover(subjects), _cover(bulk_groups[key])
                assert bulk_cover == real_cover, f"event cover differs for {key[2:]}: real {real_cover} bulk {bulk_cover}"
            print("DS3 parity event_outbox (source, type: real/bulk rows): " + ", ".join(
                f"{k[2]} {k[3]}: {len(v)}/{len(bulk_groups[k])}" for k, v in sorted(real_groups.items(), key=str)))
            return unnamed_text
    finally:
        for url in urls:
            pg_harness.drop_database(url)


def test_the_bulk_path_stores_the_rows_central_ingestion_stores_for_two_kobo_days(monkeypatch) -> None:
    """Equal rows, the recompute-job rules, the named census deltas and the change-log rule (D-DS3.10)."""
    run_parity(monkeypatch, with_v4=False)


def test_the_census_names_every_table_the_load_writes(monkeypatch) -> None:
    unnamed = run_parity(monkeypatch, with_v4=False)
    assert not unnamed, f"tables written by the load that the census does not name: {unnamed}"


def test_the_bulk_path_stores_the_rows_central_ingestion_stores_with_the_v4_slice(monkeypatch) -> None:
    unnamed = run_parity(monkeypatch, with_v4=True)
    assert not unnamed, f"tables written by the load that the census does not name: {unnamed}"


class _engine:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url)

    def __enter__(self):
        self.connection = self.engine.connect()
        return self.connection

    def __exit__(self, *exc) -> None:
        self.connection.close()
        self.engine.dispose()


def _envelopes(body: bytes) -> tuple:
    return parse_canonical_batch_v2_text(body.decode("utf-8")).envelopes
