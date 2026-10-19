"""S4-02c phase 1: accepted generator-power evidence enqueues consequence work in the acceptance transaction.

Packet `tasks/S4-02c-evidence-consequence-work.md` items 1, 2 and 5 and carries C1, C3, C4 (Site half), N6:
migration 0012's accepted-disposition trigger, its rollback atomicity, replay/duplicate/conflict/rejection,
strict half-open and Site edges, the FindingRevision trigger still enqueuing exactly once beside evidence work,
the shared Site enqueue lock under a two-connection race, 0011 bootstrap rows, both downgrade paths, the
`chain()` evidence match with the typed `NO_WORK_RECORDED` discrepancy, and (phase 2, review L3) the no-op downgrade
refusal.
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
import re
import threading
import time
from datetime import timedelta
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import BACKEND, Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import SourceEnvelopeV3, _z, canonical_envelope_v3_text, v3_message_id
    from test_s4_consequence_store_postgres import POWER_DAY, STATE_DAY, PowerSite, _at, _release_connections  # noqa: F401
    import test_s4_finding_store_postgres as finding_cases

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from money_gate_stub import AUTHORED, ELIGIBLE
    from assetops_backend.financials.consequence_read import NO_WORK_RECORDED, ConsequenceReadService
    from assetops_backend.financials.recompute import ConsequenceRecomputeWorker
    from assetops_backend.finding_api import REASONS, bridge_consequence

LOCK_TEXT = "pg_advisory_xact_lock(hashtextextended('financial_consequence_enqueue:' || NEW.site_id::text, 0))"


@pytest.fixture()
def site(store, engine, capsys):  # noqa: F811
    s = PowerSite(store, engine, capsys)
    yield s
    s.prices.dispose()
    s.store.dispose()


def power(s, start, end, kw="20", *, epoch="epoch-late", seq=None, quality="GOOD", device="generator-controller",
          signal="ac-power", claim_signal=None):
    """One generator-power mean `[start, end)` as (device, envelope text), sequenced in its own epoch."""
    kit = s.runner.kit
    b = kit.binding(device, signal)
    key = (b["source_id"], epoch)
    if seq is None:
        s.runner.seq[key] = s.runner.seq.get(key, 0) + 1
        seq = s.runner.seq[key]
    e = SourceEnvelopeV3(
        message_id=v3_message_id(site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                 source_id=b["source_id"], sequence_epoch=epoch, sequence=seq),
        sequence_epoch=epoch, sequence=seq, site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
        source_id=b["source_id"], device_id=device, signal_id=claim_signal or signal,
        binding_set_id=kit.doc["mapping"]["binding_set_id"], binding_version=kit.doc["mapping"]["version"],
        source_time=_z(end), published_at=_z(end), interval_start=_z(start), interval_end=_z(end),
        family="MEASUREMENT", measurement="INTERVAL_MEAN", value=kw, unit=b["source_unit"], quality=quality,
        unavailable_reason=None)
    return device, canonical_envelope_v3_text(e)


def body(s, envelopes) -> bytes:
    (device,) = {d for d, _ in envelopes}
    return s.runner.kit.seal([t for _, t in envelopes], device_id=device).encode("utf-8")


def submit(s, payload: bytes, minutes: int = 1):
    at = Clock(s.runner.tick() + timedelta(minutes=minutes))
    # S4-07: the fixture's decision instant goes through the test-only override (never production).
    service = BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=at), at)
    return service.submit(s.runner.kit.principal, payload)


def evidence_work(engine, site_id) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT * FROM financial_consequence_work WHERE site_id = :s AND cause = 'EVIDENCE_ACCEPTED' "
            "ORDER BY enqueued_at, id"), {"s": site_id})]


def all_work(engine) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT * FROM financial_consequence_work ORDER BY enqueued_at, id"))]


def accepted_id(engine, site_id, start, end) -> UUID:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text(
            "SELECT e.id FROM accepted_evidence e JOIN ingestion_disposition d ON d.accepted_evidence_id = e.id "
            "AND d.decision = 'ACCEPTED' WHERE e.site_id = :s AND e.role = 'generator_power' "
            "AND e.interval_start = :a AND e.interval_end = :b ORDER BY d.decided_at DESC LIMIT 1"),
            {"s": site_id, "a": start, "b": end}).scalar_one()


def clone_revision(engine, rev: dict, **cols) -> UUID:  # noqa: F811
    """Append a new latest FindingRevision of the same Finding (as the matcher would), committed."""
    with engine.connect() as c:
        names = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'finding_revision' "
            "ORDER BY ordinal_position"))]
    nid = uuid4()
    over = {"id": "CAST(:nid AS uuid)", "revision_no": "revision_no + 1000", "basis_sha256": "repeat('c', 64)",
            **cols}
    with engine.begin() as c:
        c.execute(text(f"INSERT INTO finding_revision ({', '.join(names)}) SELECT "
                       f"{', '.join(over.get(n, n) for n in names)} FROM finding_revision WHERE id = :id"),
                  {"nid": str(nid), "id": rev["id"]})
    return nid


class TestTransactionalEnqueue:
    def test_an_accepted_power_mean_inside_an_episode_enqueues_one_row_for_the_latest_revision(
            self, site, engine) -> None:  # noqa: F811
        rev = site.on(POWER_DAY)
        assert rev["episode_start"] < rev["episode_end"]
        start = rev["episode_start"] + timedelta(minutes=5)
        answer = submit(site, body(site, [power(site, start, start + timedelta(minutes=5))]))
        assert answer.status == 200 and [d.decision for d in answer.receipt.dispositions] == ["ACCEPTED"]
        eid = accepted_id(engine, site.site, start, start + timedelta(minutes=5))
        (w,) = evidence_work(engine, site.site)
        assert (w["accepted_evidence_id"], w["finding_id"], w["finding_revision_id"]) == (
            eid, rev["finding_id"], rev["id"])
        assert (w["affected_from"], w["affected_to"]) == (start, start + timedelta(minutes=5))
        assert w["tenant_id"] == site.tenant and w["assumption_key"] is None and w["assumption_revision_id"] is None
        # The state-day Finding (another day) is not selected.
        assert site.on(STATE_DAY)["finding_id"] != w["finding_id"]

    def test_a_failing_enqueue_rolls_back_the_acceptance_and_its_disposition(self, site, engine) -> None:  # noqa: F811
        rev = site.on(POWER_DAY)
        start = rev["episode_start"]
        with engine.begin() as c:
            c.execute(text(
                "CREATE FUNCTION s402c_test_refuse() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                "RAISE EXCEPTION 's402c test: evidence work refused'; END; $$"))
            c.execute(text(
                "CREATE TRIGGER s402c_test_refuse BEFORE INSERT ON financial_consequence_work FOR EACH ROW "
                "WHEN (NEW.cause = 'EVIDENCE_ACCEPTED') EXECUTE FUNCTION s402c_test_refuse()"))
        try:
            with engine.connect() as c:
                before = c.execute(text("SELECT (SELECT count(*) FROM accepted_evidence WHERE site_id = :s), "
                                        "(SELECT count(*) FROM ingestion_disposition WHERE site_id = :s)"),
                                   {"s": site.site}).one()
            with pytest.raises(Exception, match="evidence work refused"):
                submit(site, body(site, [power(site, start, start + timedelta(minutes=5))]))
            with engine.connect() as c:
                after = c.execute(text("SELECT (SELECT count(*) FROM accepted_evidence WHERE site_id = :s), "
                                       "(SELECT count(*) FROM ingestion_disposition WHERE site_id = :s)"),
                                  {"s": site.site}).one()
            assert tuple(after) == tuple(before)
            assert evidence_work(engine, site.site) == []
        finally:
            with engine.begin() as c:
                c.execute(text("DROP TRIGGER s402c_test_refuse ON financial_consequence_work"))
                c.execute(text("DROP FUNCTION s402c_test_refuse()"))

    def test_replay_duplicate_conflict_and_rejection_never_enqueue(self, site, engine) -> None:  # noqa: F811
        rev = site.on(POWER_DAY)
        start = rev["episode_start"] + timedelta(minutes=10)
        late = power(site, start, start + timedelta(minutes=5), seq=1)
        payload = body(site, [late])
        assert [d.decision for d in submit(site, payload).receipt.dispositions] == ["ACCEPTED"]
        (first,) = evidence_work(engine, site.site)
        # A new latest revision: a later re-enqueue of the same accepted ID would now be a new row, so the checks
        # below are observable (ON CONFLICT alone would hide a re-enqueue for the same revision).
        clone_revision(engine, rev)
        # Exact replay of the same batch bytes: the stored receipt, no new disposition, no new work.
        assert [d.decision for d in submit(site, payload).receipt.dispositions] == ["ACCEPTED"]
        # New batches: the same envelope (DUPLICATE) with an unbound signal (REJECTED), then the same message
        # with another value (CONFLICT), each inside the episode.
        bad = power(site, start, start + timedelta(minutes=5), seq=2, claim_signal="unbound-signal")
        answer = submit(site, body(site, [late, bad]))
        assert [d.decision for d in answer.receipt.dispositions] == ["DUPLICATE", "REJECTED"]
        same_id_other_value = power(site, start, start + timedelta(minutes=5), kw="25", seq=1)
        # (A trailing accepted mean a day later keeps the batch ID distinct and overlaps no episode.)
        later = rev["episode_end"] + timedelta(days=1)
        answer = submit(site, body(site, [same_id_other_value, power(site, later, later + timedelta(minutes=5),
                                                                     seq=3)]))
        assert [d.decision for d in answer.receipt.dispositions] == ["CONFLICT", "ACCEPTED"]
        assert evidence_work(engine, site.site) == [first]

    def test_half_open_edges_zero_width_and_non_power_roles_enqueue_nothing(self, site, engine) -> None:  # noqa: F811
        rev = site.on(POWER_DAY)
        s0, s1 = rev["episode_start"], rev["episode_end"]
        # Ends exactly at episode_start; starts exactly at episode_end (C3).
        answer = submit(site, body(site, [power(site, s0 - timedelta(minutes=5), s0),
                                          power(site, s1, s1 + timedelta(minutes=5))]))
        assert [d.decision for d in answer.receipt.dispositions] == ["ACCEPTED", "ACCEPTED"]
        assert evidence_work(engine, site.site) == []
        # A non-power interval mean inside the episode (stored binding role, not a client claim).
        other = power(site, s0, s0 + timedelta(minutes=5), device="pv-inverter-controller",
                      signal=site.runner.kit.binding("pv-inverter-controller")["signal_id"],
                      epoch="epoch-pv-mean")
        assert [d.decision for d in submit(site, body(site, [other])).receipt.dispositions] == ["ACCEPTED"]
        with engine.connect() as c:
            role = c.execute(text("SELECT role FROM accepted_evidence WHERE site_id = :s AND interval_start = :a "
                                  "AND role <> 'generator_power'"), {"s": site.site, "a": s0}).scalar_one()
        assert role != "generator_power"
        assert evidence_work(engine, site.site) == []
        # Non-power point readings inside the episode.
        rules = finding_cases.SPEC["reading_rules"]
        rows = finding_cases.block_rows({"from": _z(s0), "to": _z(s1), "pv": "41", "only": ["pv"]}, rules)
        now, _ = site.runner.seal([(r, False) for r in sorted(rows, key=lambda x: x[2])], "epoch-pv-late")
        site.runner.submit(now, site.runner.tick())
        assert evidence_work(engine, site.site) == []
        # A zero-width latest revision overlaps nothing, even a reading spanning its instant (C3).
        clone_revision(engine, rev, episode_end="episode_start")
        submit(site, body(site, [power(site, s0 - timedelta(minutes=2), s0 + timedelta(minutes=3))]))
        assert evidence_work(engine, site.site) == []

    def test_a_revision_append_enqueues_once_and_coexists_with_evidence_work(self, site, engine) -> None:  # noqa: F811
        """C1: after 0012 the FindingRevision trigger still writes exactly one row; evidence work then targets
        the new latest revision with its own row."""
        rev = site.on(POWER_DAY)
        nid = clone_revision(engine, rev)
        mine = [w for w in all_work(engine) if w["finding_revision_id"] == nid]
        assert [w["cause"] for w in mine] == ["FINDING_REVISION_APPENDED"]
        start = rev["episode_start"]
        submit(site, body(site, [power(site, start, start + timedelta(minutes=5))]))
        mine = [w for w in all_work(engine) if w["finding_revision_id"] == nid]
        assert sorted(w["cause"] for w in mine) == ["EVIDENCE_ACCEPTED", "FINDING_REVISION_APPENDED"]
        (ev,) = evidence_work(engine, site.site)
        assert ev["finding_revision_id"] == nid  # the superseded revision is not selected
        # Each partial unique index holds for its own cause.
        for cause, cols, vals in (
                ("FINDING_REVISION_APPENDED", "", ""),
                ("EVIDENCE_ACCEPTED", ", accepted_evidence_id", ", CAST(:e AS uuid)")):
            with pytest.raises(DBAPIError, match="financial_consequence_work_(finding_revision|evidence)_once"):
                with engine.begin() as c:
                    c.execute(text(
                        f"INSERT INTO financial_consequence_work (tenant_id, site_id, cause, finding_id, "
                        f"finding_revision_id, affected_from, affected_to{cols}) VALUES (:t, :s, :c, :f, :r, :a, "
                        f":b{vals})"),
                        {"t": site.tenant, "s": site.site, "c": cause, "f": rev["finding_id"], "r": nid,
                         "a": ev["affected_from"], "b": ev["affected_to"], "e": str(ev["accepted_evidence_id"])})


class TestShapeAndScope:
    def test_three_arm_cause_shape_scoped_fk_and_typed_no_op_reason(self, site, engine) -> None:  # noqa: F811
        (pub,) = site.publish("v1")
        rev = site.on(POWER_DAY)
        start = rev["episode_start"]
        submit(site, body(site, [power(site, start, start + timedelta(minutes=5))]))
        (ev,) = evidence_work(engine, site.site)
        base = {"t": site.tenant, "s": site.site, "f": rev["finding_id"], "r": rev["id"], "a": ev["affected_from"],
                "b": ev["affected_to"], "e": ev["accepted_evidence_id"], "k": "diesel_price_per_litre",
                "p": pub["revision_id"] if "revision_id" in pub else pub["id"]}

        def refused(sql: str, match: str, **over) -> None:
            with pytest.raises(DBAPIError, match=match):
                with engine.begin() as c:
                    c.execute(text("INSERT INTO financial_consequence_work (tenant_id, site_id, cause, "
                                   "assumption_key, assumption_revision_id, finding_id, finding_revision_id, "
                                   "accepted_evidence_id, affected_from, affected_to) VALUES " + sql),
                              {**base, **over})

        shape = "financial_consequence_work_cause_shape"
        refused("(:t, :s, 'EVIDENCE_ACCEPTED', NULL, NULL, :f, :r, NULL, :a, :b)", shape)  # no accepted ID
        refused("(:t, :s, 'EVIDENCE_ACCEPTED', NULL, NULL, :f, NULL, :e, :a, :b)", shape)  # no revision
        refused("(:t, :s, 'EVIDENCE_ACCEPTED', NULL, NULL, :f, :r, :e, :a, NULL)", shape)  # open interval
        refused("(:t, :s, 'EVIDENCE_ACCEPTED', NULL, NULL, :f, :r, :e, :a, :a)", shape)  # empty interval
        refused("(:t, :s, 'EVIDENCE_ACCEPTED', :k, :p, :f, :r, :e, :a, :b)", shape)  # assumption locator
        refused("(:t, :s, 'FINDING_REVISION_APPENDED', NULL, NULL, :f, :r, :e, :a, :b)", shape)
        refused("(:t, :s, 'ASSUMPTION_PUBLISHED', :k, :p, NULL, NULL, :e, :a, :b)", shape)
        refused("(:t, :s, 'SOMETHING_ELSE', NULL, NULL, :f, :r, :e, :a, :b)", "financial_consequence_work_cause_check")
        # Scoped FK: an accepted ID that is not this Site's accepted evidence.
        refused("(:t, :s, 'EVIDENCE_ACCEPTED', NULL, NULL, :f, :r, :e, :a, :b)", "financial_consequence_work_evidence_fk",
                e=uuid4())

        def attempt(outcome: str, reason: str | None, ids: str = "[]", no: int = 1, code: str | None = None):
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO financial_consequence_work_attempt (id, work_id, tenant_id, site_id, attempt_no, "
                    "outcome, error_code, consequence_revision_ids, actor_id, finished_at, no_op_reason) VALUES "
                    "(:id, :w, :t, :s, :n, :o, :code, CAST(:ids AS jsonb), 'test', clock_timestamp(), :why)"),
                    {"id": uuid4(), "w": ev["id"], "t": site.tenant, "s": site.site, "n": no, "o": outcome,
                     "code": code, "ids": ids, "why": reason})

        check = "financial_consequence_attempt_no_op_reason"
        with pytest.raises(DBAPIError, match=check):
            attempt("FAILED", "FINDING_REVISION_SUPERSEDED", code="X")
        with pytest.raises(DBAPIError, match=check):
            attempt("SUCCEEDED", "FINDING_REVISION_SUPERSEDED", ids=f'["{uuid4()}"]')
        with pytest.raises(DBAPIError, match=check):
            attempt("SUCCEEDED", "BECAUSE")
        attempt("FAILED", None, no=1, code="X")
        attempt("SUCCEEDED", "FINDING_REVISION_SUPERSEDED", no=2)
        with engine.connect() as c:
            assert c.execute(text("SELECT no_op_reason FROM financial_consequence_work_attempt WHERE work_id = :w "
                                  "ORDER BY attempt_no"), {"w": ev["id"]}).scalars().all() == [
                None, "FINDING_REVISION_SUPERSEDED"]

    def test_a_site_b_reading_with_identical_times_enqueues_nothing_for_site_a(
            self, site, store, engine, monkeypatch) -> None:  # noqa: F811
        """C4 (enqueue half): selection is scoped by the disposition's own tenant/Site."""
        from test_s1_bindings_postgres import FIXTURE, NOW, imported
        from test_s2_evidence_ledger_postgres import enable

        from assetops_backend.sites.binding_conversion import convert
        from assetops_backend.sites.binding_service import BindingService

        def site_b(store_, engine_):
            result = imported(store_, code="KOBO-002")
            outcome = convert(store_, BindingService(store_, Clock(NOW - timedelta(hours=1))), result.tenant,
                              result.site, {**FIXTURE, "site_code": "KOBO-002"})
            enable(engine_, result.site.id)
            return result, outcome

        monkeypatch.setattr(finding_cases, "converted_enabled", site_b)
        monkeypatch.setattr(finding_cases, "DEMO", {**finding_cases.DEMO, "site_code": "KOBO-002"})
        b = PowerSite.__new__(PowerSite)
        b.runner = finding_cases.CaseRunner(store, engine)
        b.tenant, b.site = b.runner.tenant, b.runner.site
        assert b.site != site.site
        rev = site.on(POWER_DAY)
        start = rev["episode_start"]
        submit(b, body(b, [power(b, start, start + timedelta(minutes=5))]))
        assert accepted_id(engine, b.site, start, start + timedelta(minutes=5))
        assert [w for w in all_work(engine) if w["cause"] == "EVIDENCE_ACCEPTED"] == []
        # The same times in Site A do enqueue (the case above is not vacuous).
        submit(site, body(site, [power(site, start, start + timedelta(minutes=5))]))
        (w,) = [w for w in all_work(engine) if w["cause"] == "EVIDENCE_ACCEPTED"]
        assert w["site_id"] == site.site
        # A Site B accepted ID cannot be named by Site A work (scoped FK).
        eb = accepted_id(engine, b.site, start, start + timedelta(minutes=5))
        with pytest.raises(DBAPIError, match="financial_consequence_work_evidence_fk"):
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO financial_consequence_work (tenant_id, site_id, cause, finding_id, "
                    "finding_revision_id, accepted_evidence_id, affected_from, affected_to) VALUES (:t, :s, "
                    "'EVIDENCE_ACCEPTED', :f, :r, :e, :a, :b)"),
                    {"t": site.tenant, "s": site.site, "f": rev["finding_id"], "r": rev["id"], "e": eb,
                     "a": start, "b": start + timedelta(minutes=5)})


class TestSiteEnqueueLock:
    def test_both_triggers_use_the_identical_site_lock_key(self, engine) -> None:  # noqa: F811
        """N6: one key expression, compared from the stored function bodies."""
        with engine.connect() as c:
            bodies = dict(c.execute(text(
                "SELECT proname, prosrc FROM pg_proc WHERE proname IN ('financial_consequence_dirty_on_evidence', "
                "'financial_consequence_dirty_on_finding_revision')")).all())
        assert len(bodies) == 2
        locks = {name: re.findall(r"pg_advisory_xact_lock\([^;]*\)", src) for name, src in bodies.items()}
        assert all(found == [LOCK_TEXT] for found in locks.values()), locks

    def test_acceptance_waits_for_a_concurrent_revision_append_and_selects_it(self, site, engine) -> None:  # noqa: F811
        """M4: connection 1 appends a FindingRevision and holds the Site lock; the acceptance on connection 2
        blocks in its trigger, then selects the committed new revision rather than the superseded one."""
        rev = site.on(POWER_DAY)
        with engine.connect() as c:
            names = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'finding_revision' "
                "ORDER BY ordinal_position"))]
        nid = uuid4()
        over = {"id": "CAST(:nid AS uuid)", "revision_no": "revision_no + 1000", "basis_sha256": "repeat('d', 64)"}
        start = rev["episode_start"]
        payload = body(site, [power(site, start, start + timedelta(minutes=5))])
        holder = engine.connect()
        tx = holder.begin()
        holder.execute(text(f"INSERT INTO finding_revision ({', '.join(names)}) SELECT "
                            f"{', '.join(over.get(n, n) for n in names)} FROM finding_revision WHERE id = :id"),
                       {"nid": str(nid), "id": rev["id"]})
        result: dict = {}

        def accept() -> None:
            try:
                result["answer"] = submit(site, payload)
            except Exception as error:  # noqa: BLE001
                result["error"] = error

        worker = threading.Thread(target=accept)
        worker.start()
        waited = False
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and not waited:
                with engine.connect() as c:
                    waited = c.execute(text(
                        "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted AND database = "
                        "(SELECT oid FROM pg_database WHERE datname = current_database()) AND objsubid = 1 AND "
                        "((classid::bigint << 32) | objid::bigint) = "
                        "hashtextextended('financial_consequence_enqueue:' || :s, 0)"),
                        {"s": str(site.site)}).scalar_one() > 0
                if not waited:
                    time.sleep(0.05)
            assert worker.is_alive() and "answer" not in result
        finally:
            tx.commit()
            holder.close()
            worker.join(60)
        assert waited, "the acceptance never waited on the Site enqueue lock"
        assert "error" not in result, result.get("error")
        assert [d.decision for d in result["answer"].receipt.dispositions] == ["ACCEPTED"]
        (w,) = evidence_work(engine, site.site)
        assert w["finding_revision_id"] == nid


class TestReadAndWorkerGuard:
    def test_chain_matches_evidence_work_then_no_work_recorded(
            self, site, engine) -> None:  # noqa: F811
        site.publish("v1")
        worker = ConsequenceRecomputeWorker(site.store, site.prices, CONSEQUENCE_UNAVAILABLE)
        reads = ConsequenceReadService(site.store, site.prices, eligibility=ELIGIBLE, provenance=AUTHORED)
        assert all(o.succeeded for o in worker.run_pending(site.tenant, site.site))
        rev = site.on(POWER_DAY)

        def read() -> dict:
            return reads.read(site.tenant, site.site, rev["finding_id"], rev["id"], finding_revision_is_latest=True,
                              source_open=True)

        assert read()["currentness"]["state"] == "CURRENT"
        start = rev["episode_start"] + timedelta(minutes=5)
        submit(site, body(site, [power(site, start, start + timedelta(minutes=5), kw="30")]))
        (ev,) = evidence_work(engine, site.site)
        stale = read()
        c = stale["currentness"]
        assert c["state"] == "STALE" and "TECHNICAL_INPUT_CHANGED" in c["reasons"]
        assert NO_WORK_RECORDED not in c["reasons"]
        assert [(w["work_id"], w["cause"], w["accepted_evidence_id"], w["finding_revision_id"])
                for w in c["pending_work"]] == [
            (str(ev["id"]), "EVIDENCE_ACCEPTED", str(ev["accepted_evidence_id"]), str(rev["id"]))]
        bridged = bridge_consequence(stale)
        assert bridged["reason"] == REASONS["STALE_QUEUED"] and bridged["recalculation_queued"] is True

        # Stale with no unsucceeded work touching the read: the typed discrepancy, with the reviewed STALE copy.
        site.store.record_attempt(site.tenant, site.site, ev["id"], succeeded=True)
        orphan = read()
        assert orphan["currentness"]["state"] == "STALE" and orphan["currentness"]["pending_work"] == []
        assert NO_WORK_RECORDED in orphan["currentness"]["reasons"]
        bridged = bridge_consequence(orphan)
        assert bridged["reason"] == REASONS["STALE"] and bridged["recalculation_queued"] is False
        assert NO_WORK_RECORDED in bridged["currentness_reasons"]
        assert NO_WORK_RECORDED not in REASONS


class TestMigrationPaths:
    def _config(self):
        from alembic.config import Config

        config = Config(str(BACKEND / "alembic.ini"))
        config.attributes["database_url"] = URL
        return config

    def test_bootstrap_rows_survive_upgrade_and_an_empty_downgrade_restores_0011(self, site, engine) -> None:  # noqa: F811
        from alembic import command

        config = self._config()
        site.store.dispose()
        site.prices.dispose()
        engine.dispose()
        cols = ("id", "cause", "finding_id", "finding_revision_id", "affected_from", "affected_to")
        try:
            command.downgrade(config, "0010_financial_assumptions")
            command.upgrade(config, "0011_financial_consequences")
            boot = sorted(tuple(w[k] for k in cols) for w in all_work(engine))
            assert boot and {b[1] for b in boot} == {"FINDING_REVISION_APPENDED"}
            command.upgrade(config, "head")
            after = all_work(engine)
            assert sorted(tuple(w[k] for k in cols) for w in after) == boot
            assert all(w["accepted_evidence_id"] is None for w in after)
            # Empty-case downgrade: the original 0011 trigger body, two-arm CHECK and UNIQUE constraint return.
            command.downgrade(config, "0011_financial_consequences")
            with engine.connect() as c:
                src = c.execute(text("SELECT prosrc FROM pg_proc WHERE proname = "
                                     "'financial_consequence_dirty_on_finding_revision'")).scalar_one()
                kinds = dict(c.execute(text(
                    "SELECT conname, contype FROM pg_constraint WHERE conrelid = "
                    "'financial_consequence_work'::regclass")).all())
                shape = c.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = "
                                       "'financial_consequence_work_cause_shape'")).scalar_one()
                gone = c.execute(text(
                    "SELECT count(*) FROM information_schema.columns WHERE column_name IN "
                    "('accepted_evidence_id', 'no_op_reason') AND table_name LIKE 'financial_consequence_work%'"
                )).scalar_one()
                trig = c.execute(text("SELECT count(*) FROM pg_trigger WHERE tgname = "
                                      "'financial_consequence_dirty_on_evidence'")).scalar_one()
            assert "financial_consequence_enqueue" not in src and "ON CONFLICT (finding_revision_id) DO NOTHING" in src
            assert kinds.get("financial_consequence_work_finding_revision_once") == "u"
            assert "EVIDENCE_ACCEPTED" not in shape and "accepted_evidence_id" not in shape
            assert (gone, trig) == (0, 0)
            assert sorted(tuple(w[k] for k in cols) for w in all_work(engine)) == boot
            # A FindingRevision append still enqueues under the restored 0011 trigger.
            nid = clone_revision(engine, site.on(POWER_DAY))
            assert [w["cause"] for w in all_work(engine) if w["finding_revision_id"] == nid] == [
                "FINDING_REVISION_APPENDED"]
        finally:
            command.upgrade(config, "head")

    def test_downgrade_refuses_while_evidence_work_exists(self, site, engine) -> None:  # noqa: F811
        from alembic import command

        rev = site.on(POWER_DAY)
        submit(site, body(site, [power(site, rev["episode_start"], rev["episode_start"] + timedelta(minutes=5))]))
        before = all_work(engine)
        assert any(w["cause"] == "EVIDENCE_ACCEPTED" for w in before)
        config = self._config()
        site.store.dispose()
        site.prices.dispose()
        engine.dispose()
        try:
            with pytest.raises(Exception, match="refused: EVIDENCE_ACCEPTED consequence work exists"):
                command.downgrade(config, "0011_financial_consequences")
            with engine.connect() as c:
                assert c.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
                    "0023_w2_cold_consequence")  # the whole downgrade rolled back: still head
            assert all_work(engine) == before
        finally:
            command.upgrade(config, "head")

    def test_downgrade_refuses_while_a_no_op_reason_exists(self, site, engine) -> None:  # noqa: F811
        """Phase 1 review L3: a typed no-op attempt on FindingRevision work alone blocks the downgrade."""
        from alembic import command

        (w,) = [x for x in all_work(engine) if x["cause"] == "FINDING_REVISION_APPENDED"
                and x["finding_revision_id"] == site.on(POWER_DAY)["id"]]
        site.store.record_attempt(site.tenant, site.site, w["id"], succeeded=True,
                                  no_op_reason="FINDING_REVISION_SUPERSEDED")
        assert not any(x["cause"] == "EVIDENCE_ACCEPTED" for x in all_work(engine))
        config = self._config()
        site.store.dispose()
        site.prices.dispose()
        engine.dispose()
        try:
            with pytest.raises(Exception, match="refused: work attempts record a no-op reason"):
                command.downgrade(config, "0011_financial_consequences")
            with engine.connect() as c:
                assert c.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
                    "0023_w2_cold_consequence")  # the whole downgrade rolled back: still head
                assert c.execute(text("SELECT no_op_reason FROM financial_consequence_work_attempt "
                                      "WHERE work_id = :w"), {"w": w["id"]}).scalar_one() == (
                    "FINDING_REVISION_SUPERSEDED")
        finally:
            command.upgrade(config, "head")
