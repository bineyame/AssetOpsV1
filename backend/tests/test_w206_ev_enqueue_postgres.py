"""W2-06 commit 3a: the 0025 deferred `enqueue_ev_assessment` constraint trigger and
`PostgresAssessmentStore.ev_enqueue_configuration` (`.agent/W2-06-build-spec.md` "Q10-Q13: enqueue and worker").

Accepted rows are written in the S2 writer's shape (accepted row then its ACCEPTED disposition, one transaction) by
cloning one accepted row of the mini-grid Site fixture; the trigger reads only role, family/kind, asset, session and
times, never the Site type. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections, site  # noqa: F401
    from test_w203_cold_migration_postgres import _replica
    from test_w206_ev_migration_postgres import Ctx

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore

DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
ORDINAL = 100_000
OUTCOME = {"EV_SESSION_START": "STARTED", "EV_SESSION_END": "COMPLETED", "EV_SESSION_ABORT": "ABORTED"}


def at(hh: int, mm: int, ss: int = 0) -> datetime:
    return DAY.replace(hour=hh, minute=mm, second=ss)


class Ev:
    def __init__(self, site, engine) -> None:  # noqa: F811
        self.ctx = Ctx(site, engine)
        self.engine = engine
        self.template = self.ctx.evidence[0]
        with engine.connect() as c:
            self.columns = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'accepted_evidence' "
                "ORDER BY ordinal_position"))]
            self.batch = c.execute(text("SELECT batch_id FROM accepted_evidence WHERE id = :e"),
                                   {"e": self.template}).scalar()
        self.ordinal = ORDINAL

    def write(self, c, *, role: str, when: datetime, decided: datetime, kind: str | None = None,
              session: str | None = None, disposition: str | None = "ACCEPTED") -> UUID:
        """One accepted row and its disposition on `c`, as the S2 writer orders them."""
        self.ordinal += 1
        eid, msg = uuid4(), f"w206-enq-{uuid4()}"
        over: dict[str, str] = {
            "id": ":id", "ordinal": ":o", "message_id": ":m", "sequence": ":seq", "role": ":role",
            "source_time": ":at", "published_at": ":pub", "received_at": ":pub", "interval_start": "NULL",
            "interval_end": "NULL", "session_id": ":sess", "asset_id": ":asset"}
        if kind is not None:
            over.update({
                "family": "'EVENT'", "measurement": "NULL", "conversion_kind": "NULL", "original_unit": "NULL",
                "original_value_text": "NULL", "normalized_unit": "NULL", "normalized_value_text": "NULL",
                "quality": "'GOOD'", "unavailable_reason": "NULL", "record_kind": ":kind", "event_id": ":m",
                "correlation_id": ":m", "actor": "'CONTROLLER'", "outcome": ":outcome", "connector_id": "'c1'"})
        cols = ", ".join(self.columns)
        values = ", ".join(over.get(col, col) for col in self.columns)
        c.execute(text(f"INSERT INTO accepted_evidence ({cols}) SELECT {values} FROM accepted_evidence "
                       "WHERE id = :template"),
                  {"id": eid, "o": self.ordinal, "m": msg, "seq": 10_000_000 + self.ordinal, "role": role,
                   "at": when, "pub": when + timedelta(minutes=1), "sess": session, "kind": kind,
                   "outcome": OUTCOME.get(kind or ""), "template": self.template, "asset": self.ctx.connector})
        if disposition is not None:
            self.dispose(c, eid, msg, disposition, decided)
        return eid

    def dispose(self, c, eid: UUID, msg: str, decision: str, decided: datetime) -> None:
        if decision != "ACCEPTED":
            self.ordinal += 1
        c.execute(text(
            "INSERT INTO ingestion_disposition (batch_id, ordinal, tenant_id, site_id, message_id, decision, "
            "accepted_evidence_id, rejection_id, decided_at) VALUES (:b, :o, :t, :s, :m, :d, :e, NULL, :at)"),
            self.ctx.p(b=self.batch, o=self.ordinal, m=msg, d=decision, e=eid, at=decided))

    @staticmethod
    def pending_on(c, site_id: UUID) -> list[dict]:
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT window_start, window_end FROM recompute_job WHERE site_id = :s AND domain = 'ev_charging' "
            "AND status = 'PENDING' ORDER BY window_start"), {"s": site_id})]

    def accept(self, **kw) -> UUID:
        with self.engine.begin() as c:
            return self.write(c, **kw)

    def select(self, lo: datetime, hi: datetime) -> None:
        with self.engine.begin() as c:
            c.execute(text(
                "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, "
                "run_id, job_id, selected_at) VALUES (:t, :s, 'ev-session/1', :lo, :hi, :r, NULL, now())"),
                self.ctx.p(lo=lo, hi=hi, r=self.ctx.run))

    def jobs(self, status: str | None = None) -> list[dict]:
        with self.engine.connect() as c:
            return [dict(r._mapping) for r in c.execute(text(
                "SELECT id, window_start, window_end, cause_evidence_id, status, available_at, created_at "
                "FROM recompute_job WHERE site_id = :s AND domain = 'ev_charging' "
                "AND (CAST(:st AS text) IS NULL OR status = :st) ORDER BY window_start, created_at"),
                {"s": self.ctx.s, "st": status})]

    def link(self, c) -> None:
        """q3 P7: append the source-publication link of the fixture batch on `c` (W2-04 test precedent)."""
        b = c.execute(text("SELECT * FROM ingestion_batch WHERE id = :b"), {"b": self.batch}).mappings().one()
        pid = uuid4()
        p = {"p": pid, "b": b["id"], "t": b["tenant_id"], "s": b["site_id"], "g": b["gateway_id"],
             "src": b["source_id"], "x": b["external_batch_id"], "h": b["payload_sha256"]}
        c.execute(text(
            "INSERT INTO evidence_publication (id, tenant_id, site_id, gateway_id, source_id, external_batch_id, "
            "payload_sha256, source_class, fixture_id, fixture_version, actor_kind, actor_id, authorization_basis, "
            "channel, publication_trigger, recorded_at) VALUES (:p, :t, :s, :g, :src, :x, :h, "
            "'AUTHORED_DEMONSTRATION', 'w206', '1', 'SYSTEM', 'test', 'test', 'SYSTEM_FIXTURE', 'test', now())"), p)
        c.execute(text(
            "INSERT INTO batch_publication_link (batch_id, publication_id, tenant_id, site_id, gateway_id, "
            "source_id, external_batch_id, payload_sha256, linked_at) VALUES (:b, :p, :t, :s, :g, :src, :x, :h, "
            "now())"), p)

    def set_status(self, job_id: UUID, status: str) -> None:
        with self.engine.begin() as c:
            c.execute(text("UPDATE recompute_job SET status = :st, lease_until = CASE WHEN :st = 'LEASED' "
                           "THEN now() + interval '5 minutes' END WHERE id = :id"), {"st": status, "id": job_id})


@pytest.fixture()
def ev(site, engine):  # noqa: F811
    built = Ev(site, engine)
    yield built
    _replica(engine, "DELETE FROM batch_publication_link WHERE publication_id IN "
                     "(SELECT id FROM evidence_publication WHERE fixture_id = 'w206')",
             "DELETE FROM evidence_publication WHERE fixture_id = 'w206'",
             "DELETE FROM recompute_job WHERE domain = 'ev_charging'",
             "DELETE FROM analytic_run_selection WHERE analytic_id = 'ev-session/1'",
             f"DELETE FROM ingestion_disposition WHERE ordinal > {ORDINAL}",
             "DELETE FROM accepted_evidence WHERE message_id LIKE 'w206-enq-%'")


def window(job: dict) -> tuple[datetime, datetime]:
    return job["window_start"], job["window_end"]


class TestEvEnqueueTrigger:
    def test_a_relevant_accepted_row_enqueues_its_bracket_at_its_decision_instant(self, ev) -> None:
        decided = at(9, 0)
        eid = ev.accept(role="ev_site_import", when=at(8, 2, 30), decided=decided)
        (job,) = ev.jobs()
        assert window(job) == (at(8, 0), at(8, 5))
        assert job["cause_evidence_id"] == eid and job["status"] == "PENDING"
        assert job["available_at"] == decided and job["created_at"] == decided

    def test_a_boundary_instant_brackets_forward_half_open(self, ev) -> None:
        ev.accept(role="ev_connector_state", when=at(8, 5), decided=at(9, 0))
        assert [window(j) for j in ev.jobs()] == [(at(8, 5), at(8, 10))]

    def test_a_duplicate_receipt_enqueues_nothing(self, ev) -> None:
        eid = ev.accept(role="ev_site_import", when=at(8, 2), decided=at(9, 0))
        before = ev.jobs()
        with ev.engine.begin() as c:
            ev.dispose(c, eid, f"w206-enq-{uuid4()}", "DUPLICATE", at(9, 30))
        assert ev.jobs() == before

    def test_non_ev_rows_enqueue_no_ev_charging_job(self, ev) -> None:
        with ev.engine.connect() as c:
            role = c.execute(text("SELECT role FROM accepted_evidence WHERE id = :e"), {"e": ev.template}).scalar()
        assert not role.startswith("ev_")
        ev.accept(role=role, when=at(8, 2), decided=at(9, 0))
        assert ev.jobs() == []

    def test_an_ev_row_without_an_accepted_disposition_in_its_transaction_enqueues_nothing(self, ev) -> None:
        with ev.engine.begin() as c:
            eid = ev.write(c, role="ev_site_import", when=at(8, 2), decided=at(9, 0), disposition=None)
        assert ev.jobs() == []
        with ev.engine.begin() as c:  # a later disposition is not the row's own transaction: still nothing
            ev.dispose(c, eid, f"w206-enq-{uuid4()}", "DUPLICATE", at(9, 30))
        assert ev.jobs() == []

    def test_pending_widening_lifts_available_at_and_keeps_created_at(self, ev) -> None:
        first = ev.accept(role="ev_site_import", when=at(8, 2), decided=at(10, 0))
        ev.accept(role="ev_site_import", when=at(8, 12), decided=at(10, 30))
        (job,) = ev.jobs()
        assert window(job) == (at(8, 0), at(8, 15))
        assert job["available_at"] == at(10, 30) and job["created_at"] == at(10, 0)
        assert job["cause_evidence_id"] == first

    def test_work_within_the_ten_minute_bridge_coalesces_and_beyond_it_is_separate(self, ev) -> None:
        ev.accept(role="ev_site_import", when=at(8, 2), decided=at(10, 0))
        ev.accept(role="ev_site_import", when=at(8, 22), decided=at(10, 0))  # 15 minutes after 08:05
        ev.accept(role="ev_site_import", when=at(8, 37), decided=at(10, 0))  # exactly ten minutes after 08:25
        assert [window(j) for j in ev.jobs()] == [(at(8, 0), at(8, 5)), (at(8, 20), at(8, 40))]

    @pytest.mark.parametrize("status", ["LEASED", "FAILED", "DONE"])
    def test_a_leased_failed_or_done_job_keeps_a_new_pending_job(self, ev, status) -> None:
        ev.accept(role="ev_site_import", when=at(8, 2), decided=at(10, 0))
        (held,) = ev.jobs()
        ev.set_status(held["id"], status)
        later = ev.accept(role="ev_site_import", when=at(8, 3), decided=at(10, 30))
        (kept,) = [j for j in ev.jobs() if j["id"] == held["id"]]
        assert kept["status"] == status and window(kept) == (at(8, 0), at(8, 5))
        (pending,) = ev.jobs("PENDING")
        assert window(pending) == (at(8, 0), at(8, 5)) and pending["cause_evidence_id"] == later
        assert pending["available_at"] == at(10, 30)

    def test_a_late_end_dirties_the_selected_window_containing_its_start(self, ev) -> None:
        ev.accept(role="ev_session_event", kind="EV_SESSION_START", session="s-1", when=at(8, 1), decided=at(9, 0))
        (first,) = ev.jobs()
        ev.set_status(first["id"], "DONE")
        ev.select(at(8, 0), at(9, 0))
        end = ev.accept(role="ev_session_event", kind="EV_SESSION_END", session="s-1", when=at(8, 31),
                        decided=at(9, 5))
        (pending,) = ev.jobs("PENDING")
        assert window(pending) == (at(8, 0), at(9, 0)) and pending["cause_evidence_id"] == end
        assert pending["available_at"] == at(9, 5)

    def test_a_late_end_without_a_selection_also_enqueues_its_start_bracket(self, ev) -> None:
        ev.accept(role="ev_session_event", kind="EV_SESSION_START", session="s-2", when=at(8, 1), decided=at(9, 0))
        (first,) = ev.jobs()
        ev.set_status(first["id"], "DONE")
        ev.accept(role="ev_session_event", kind="EV_SESSION_END", session="s-2", when=at(8, 31), decided=at(9, 5))
        assert [window(j) for j in ev.jobs("PENDING")] == [(at(8, 0), at(8, 5)), (at(8, 30), at(8, 35))]

    def test_disjoint_selected_windows_are_enqueued_separately(self, ev) -> None:
        ev.select(at(8, 0), at(9, 0))
        ev.select(at(9, 0), at(10, 0))
        ev.accept(role="ev_session_event", kind="EV_SESSION_START", session="s-3", when=at(8, 50), decided=at(10, 0))
        ev.accept(role="ev_session_event", kind="EV_SESSION_END", session="s-3", when=at(9, 10), decided=at(10, 5))
        assert [window(j) for j in ev.jobs("PENDING")] == [(at(8, 0), at(9, 0)), (at(9, 0), at(10, 0))]


class TestEvEnqueueConfiguration:
    def test_configuration_enqueue_rolls_back_with_its_publication(self, ev) -> None:
        ev.select(at(8, 0), at(9, 0))
        with pytest.raises(RuntimeError):
            with ev.engine.begin() as c:
                PostgresAssessmentStore.ev_enqueue_configuration(
                    c, ev.ctx.t, ev.ctx.s, at(7, 0), None, "FOUNDATION_PUBLISHED", at(10, 0))
                assert len(ev.jobs()) == 0  # not visible outside the publishing transaction
                raise RuntimeError("publication refused")
        assert ev.jobs() == []

    def test_configuration_dirties_each_intersecting_selected_window_with_no_cause(self, ev) -> None:
        ev.select(at(8, 0), at(9, 0))
        ev.select(at(9, 0), at(10, 0))
        ev.select(at(12, 0), at(13, 0))
        with ev.engine.begin() as c:
            PostgresAssessmentStore.ev_enqueue_configuration(
                c, ev.ctx.t, ev.ctx.s, at(8, 30), at(11, 0), "BINDING_PUBLISHED", at(10, 0))
        jobs = ev.jobs("PENDING")
        assert [window(j) for j in jobs] == [(at(8, 0), at(9, 0)), (at(9, 0), at(10, 0))]
        assert all(j["cause_evidence_id"] is None and j["available_at"] == at(10, 0) for j in jobs)

    def test_configuration_without_a_selection_seeds_its_change_bracket(self, ev) -> None:
        with ev.engine.begin() as c:
            PostgresAssessmentStore.ev_enqueue_configuration(
                c, ev.ctx.t, ev.ctx.s, at(8, 7, 30), None, "FOUNDATION_PUBLISHED", at(10, 0))
        (job,) = ev.jobs()
        assert window(job) == (at(8, 5), at(8, 10)) and job["cause_evidence_id"] is None


class TestEvSourceGateLink:
    """q3 P7: the deferred `enqueue_ev_assessment_on_source_gate` constraint trigger on `batch_publication_link`."""

    def _done(self, ev) -> None:
        for job in ev.jobs("PENDING"):
            ev.set_status(job["id"], "DONE")

    def test_a_link_dirties_each_selected_window_of_its_accepted_ev_rows(self, ev) -> None:
        ev.accept(role="ev_session_event", kind="EV_SESSION_START", session="g-1", when=at(8, 1), decided=at(9, 0))
        ev.accept(role="ev_session_event", kind="EV_SESSION_END", session="g-1", when=at(9, 20), decided=at(9, 30))
        ev.accept(role="ev_site_import", when=at(12, 2), decided=at(9, 10))
        self._done(ev)
        for lo, hi in ((at(8, 0), at(9, 0)), (at(9, 0), at(10, 0)), (at(10, 0), at(11, 0))):
            ev.select(lo, hi)
        with ev.engine.begin() as c:
            ev.link(c)
        jobs = ev.jobs("PENDING")
        # The session's full accepted extent (08:01 START to 09:20 END) reaches both of its selected windows; the
        # 10:00 selection meets no affected row; the 12:02 row has no selected window and seeds nothing.
        assert [window(j) for j in jobs] == [(at(8, 0), at(9, 0)), (at(9, 0), at(10, 0))]
        assert all(j["cause_evidence_id"] is None and j["available_at"] == at(9, 30) for j in jobs)

    def test_a_link_without_accepted_ev_rows_enqueues_nothing(self, ev) -> None:
        ev.select(at(8, 0), at(9, 0))
        with ev.engine.begin() as c:
            ev.link(c)
        assert ev.jobs() == []

    def test_an_ev_row_without_an_accepted_disposition_is_not_a_link_input(self, ev) -> None:
        with ev.engine.begin() as c:
            ev.write(c, role="ev_site_import", when=at(8, 2), decided=at(9, 0), disposition=None)
        ev.select(at(8, 0), at(9, 0))
        with ev.engine.begin() as c:
            ev.link(c)
        assert ev.jobs() == []

    def test_the_link_enqueue_rolls_back_with_its_publication(self, ev) -> None:
        ev.accept(role="ev_site_import", when=at(8, 2), decided=at(9, 0))
        self._done(ev)
        ev.select(at(8, 0), at(9, 0))
        with pytest.raises(RuntimeError):
            with ev.engine.begin() as c:
                ev.link(c)
                c.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))  # fire the deferred trigger inside the transaction
                assert [window(j) for j in Ev.pending_on(c, ev.ctx.s)] == [(at(8, 0), at(9, 0))]
                raise RuntimeError("publication refused")
        assert ev.jobs("PENDING") == []
