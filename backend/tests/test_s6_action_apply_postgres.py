"""S6-01a phase 2: the controlled application of an accepted `reserve-trial-1` Action (PostgreSQL).

One transaction: the Action adapter locks the same-Site Action row, then the S1 caller-owned-connection publish
locks the Site and checks the expected covering Foundation revision and its reserve, writes Foundation/SPLIT/binding
rows, and the Action adapter's callback inserts the change artifact and APPLIED before the single commit. Proves
the lock order, rollback, concurrent applies, FAILED after rollback (stale 409, invalid/no-change/backdate 422),
the identical-retry and already-applied rules, refusals that append nothing, and the change read.
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import threading
import time
from datetime import timedelta
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL, CaseRunner, run_case  # noqa: F401
from test_s6_action_store_postgres import CASES, T_ACCEPT, harness, runner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.actions.capability import no_capability
    from assetops_backend.actions.composition import foundation_publish
    from assetops_backend.sites.foundation_service import FoundationService

T_APPLY = T_ACCEPT + timedelta(hours=1)
EFFECTIVE = T_ACCEPT + timedelta(days=1)
FOUNDATION_TABLES = ("foundation_revision", "signal_binding_set_revision", "signal_binding_revision")


class Registry:
    """The imported-Site registry surface `foundation_publish` uses (`sites.cutover.ImportedSiteRegistry`)."""

    def __init__(self, runner) -> None:
        self.runner = runner
        self.service = FoundationService(runner.store, "demo")

    def tenant(self):
        return self.runner.result.tenant

    def imported(self, site_code: str):
        return self.runner.result.site if site_code == "KOBO-001" else None


def applying(runner, **kwargs):
    h = harness(runner, **kwargs)
    h.service.publish = foundation_publish(Registry(runner))
    h.clock.at = T_ACCEPT
    return h


def accepted(h, day: str, key: str = "accept-0001") -> tuple[str, dict]:
    finding = h.findings()[day]
    proposal = h.recommendation(finding).json()["proposal"]
    made = h.accept(finding, proposal, idempotency_key=key)
    assert made.status_code == 201, made.text
    return made.json()["action"]["action_id"], proposal


def current_foundation(h, action_id: str) -> str:
    return h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()["application_basis"][
        "current_foundation_revision_id"]


def apply(h, action_id: str, expected: str, key: str, site: str = "KOBO-001", **over):
    body = {"expected_foundation_revision_id": expected, "value": "15", "effective_from": EFFECTIVE.isoformat(),
            "idempotency_key": key, **over}
    return h.client.post(f"/api/sites/{site}/actions/{action_id}/apply", json=body)


def table_counts(runner) -> dict[str, int]:
    with runner.engine.connect() as c:
        return {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one()
                for t in (*FOUNDATION_TABLES, "action_event", "action_policy_change", "action_policy_change_binding")}


def kinds(h, action_id: str) -> list[str]:
    return [e["kind"] for e in h.client.get(f"/api/sites/KOBO-001/actions/{action_id}/events").json()["events"]]


class TestApplyPublishesAtomically:
    def test_apply_artifact_reload_retry_and_already_applied(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = applying(runner)
        try:
            action_id, proposal = accepted(h, "2026-10-06")
            expected = current_foundation(h, action_id)
            assert expected == proposal["foundation_revision_id"]
            before = table_counts(runner)
            h.clock.at = T_APPLY
            made = apply(h, action_id, expected, "apply-0001")
            assert made.status_code == 201, made.text
            body = made.json()
            event, change = body["event"], body["change"]
            assert body["replayed"] is False and body["outcome"]["state"] == "PENDING"
            assert event["kind"] == "APPLIED" and event["recorded_at"] == T_APPLY.isoformat()
            assert event["occurred_at"] == event["recorded_at"] and event["failure_code"] is None
            assert event["actor"]["triggering"]["command"] == "APPLY"
            assert event["expected_foundation_revision_id"] == expected
            assert event["current_foundation_revision_id"] == change["new_foundation_revision_id"]
            assert (change["old_value"], change["new_value"], change["unit"]) == ("20", "15", "%")
            assert change["field"] == "reserve-state-of-charge" and change["asset_id"] == proposal["asset_id"]
            assert change["applied_event_id"] == event["id"] and change["effective_from"] == EFFECTIVE.isoformat()
            assert change["recorded_at"] == T_APPLY.isoformat()
            assert change["expected_foundation_revision_id"] == expected
            assert change["superseded_foundation_revision_id"] == expected
            assert change["split_foundation_revision_id"] is not None

            # Every written row is in the database exactly as the artifact names it.
            with runner.engine.connect() as c:
                rows = {str(r.id): r for r in c.execute(text(
                    "SELECT id, origin, valid_from, valid_to, recorded_at, superseded_at, derived_from_revision_id, "
                    "content FROM foundation_revision WHERE site_id = :s"), {"s": runner.site})}
                published = rows[change["new_foundation_revision_id"]]
                split = rows[change["split_foundation_revision_id"]]
                old = rows[expected]
                sets = c.execute(text(
                    "SELECT id, foundation_revision_id, superseded_at, recorded_at FROM signal_binding_set_revision "
                    "WHERE site_id = :s"), {"s": runner.site}).all()
            assert published.origin == "PUBLISH" and published.valid_from == EFFECTIVE
            assert split.origin == "SPLIT" and split.valid_to == EFFECTIVE
            assert str(published.derived_from_revision_id) == str(split.derived_from_revision_id) == expected
            assert old.superseded_at == T_APPLY and published.recorded_at == T_APPLY
            reserve = [p for comp in published.content["components"] if comp["component_type"] == "BATTERY"
                       for p in comp["properties"] if p["property_key"] == "reserve-state-of-charge"]
            assert [float(p["value"]) for p in reserve] == [15.0]
            inserted = {str(s.id) for s in sets if s.recorded_at == T_APPLY}
            superseded = {str(s.id) for s in sets if s.superseded_at == T_APPLY}
            assert inserted and set(change["binding_set_revisions"]["inserted"]) == inserted
            assert set(change["binding_set_revisions"]["superseded"]) == superseded
            after = table_counts(runner)
            assert after["foundation_revision"] == before["foundation_revision"] + 2
            assert after["action_policy_change"] == 1 and after["action_event"] == before["action_event"] + 1

            # Change read, Action reload, exact-history read before APPLIED.
            read = h.client.get(f"/api/sites/KOBO-001/foundation/changes/{change['change_id']}")
            assert read.status_code == 200 and read.json()["change"] == change
            assert {r["id"] for r in change["foundation_revisions"]} == {
                expected, change["split_foundation_revision_id"], change["new_foundation_revision_id"]}
            reload = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
            assert reload["state"]["application"] == "APPLIED" and reload["change"] == change
            assert reload["state"]["outcome"]["state"] == "PENDING"
            accepted_id = next(e for e in h.client.get(
                f"/api/sites/KOBO-001/actions/{action_id}/events").json()["events"] if e["kind"] == "ACCEPTED")["id"]
            pinned = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}", params={"event_id": accepted_id}).json()
            assert pinned["state"]["application"] == "PENDING" and pinned["change"] is None

            # An identical retry returns the committed artifact before any no-change validation.
            h.clock.at = T_APPLY + timedelta(minutes=5)
            again = apply(h, action_id, expected, "apply-0001")
            assert again.status_code == 200, again.text
            assert again.json()["replayed"] is True and again.json()["event"]["id"] == event["id"]
            assert again.json()["change"] == change
            # Same key, different payload: 409, nothing written.
            clash = apply(h, action_id, expected, "apply-0001", effective_from=(EFFECTIVE + timedelta(hours=1)).isoformat())
            assert clash.status_code == 409 and clash.json()["detail"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"
            # A new key on an APPLIED Action: typed 409, no FAILED and no publish attempt.
            current = current_foundation(h, action_id)
            for key, exp in (("apply-0002", expected), ("apply-0003", current)):
                refused = apply(h, action_id, exp, key)
                assert refused.status_code == 409 and refused.json()["detail"]["code"] == "ACTION_ALREADY_APPLIED"
                assert refused.json()["detail"]["applied_event_id"] == event["id"]
            assert table_counts(runner) == after
            assert kinds(h, action_id) == ["ACCEPTED", "APPLIED"]
        finally:
            h.close()


class TestFailedAfterRollback:
    def test_stale_invalid_backdate_retry_then_apply_then_no_change(self, runner) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = applying(runner)
        try:
            action_id, proposal = accepted(h, "2026-10-06")
            other_id, _ = accepted(h, "2026-10-08", key="accept-0002")
            expected = current_foundation(h, action_id)
            with runner.engine.connect() as c:
                older = str(c.execute(text(
                    "SELECT id FROM foundation_revision WHERE site_id = :s AND id <> :e ORDER BY version LIMIT 1"),
                    {"s": runner.site, "e": expected}).scalar_one())
            start = table_counts(runner)
            h.clock.at = T_APPLY

            stale = apply(h, action_id, older, "apply-stale-1")
            assert stale.status_code == 409, stale.text
            detail = stale.json()["detail"]
            assert detail["code"] == "ACTION_FOUNDATION_STALE" and detail["replayed"] is False
            assert detail["foundation_code"] == "FOUNDATION_EXPECTED_REVISION_STALE"
            failed = detail["event"]
            assert failed["kind"] == "FAILED" and failed["failure_code"] == "ACTION_FOUNDATION_STALE"
            assert failed["expected_foundation_revision_id"] == older
            assert failed["current_foundation_revision_id"] == expected
            # The same key again returns the stored FAILED event; it is not a second attempt.
            h.clock.at = T_APPLY + timedelta(minutes=1)
            retry = apply(h, action_id, older, "apply-stale-1")
            assert retry.status_code == 409 and retry.json()["detail"]["replayed"] is True
            assert retry.json()["detail"]["event"]["id"] == failed["id"]
            clash = apply(h, action_id, expected, "apply-stale-1")
            assert clash.status_code == 409 and clash.json()["detail"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"

            invalid = apply(h, action_id, expected, "apply-value-1", value="14")
            assert invalid.status_code == 422 and invalid.json()["detail"]["code"] == "ACTION_VALUE_INVALID"
            assert invalid.json()["detail"]["event"]["kind"] == "FAILED"
            backdated = apply(h, action_id, expected, "apply-early-1",
                              effective_from=(T_APPLY - timedelta(hours=2)).isoformat())
            assert backdated.status_code == 422
            assert backdated.json()["detail"]["code"] == "ACTION_EFFECTIVE_TIME_INVALID"
            # Nothing but three FAILED events was written; the application is still pending.
            mid = table_counts(runner)
            assert {t: mid[t] - start[t] for t in mid} == {**{t: 0 for t in mid}, "action_event": 3}
            body = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
            assert body["state"]["application"] == "PENDING" and body["state"]["failed_attempts"] == 3
            assert body["change"] is None

            # A fresh key can still apply.
            h.clock.at = T_APPLY + timedelta(minutes=2)
            made = apply(h, action_id, expected, "apply-fresh-1")
            assert made.status_code == 201, made.text
            body = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
            assert body["state"]["application"] == "APPLIED" and body["state"]["failed_attempts"] == 3
            assert kinds(h, action_id) == ["ACCEPTED", "FAILED", "FAILED", "FAILED", "APPLIED"]

            # The second Action's trial (20 -> 15) is now a no-change on the current Foundation: typed 422 + FAILED.
            h.clock.at = T_APPLY + timedelta(minutes=3)
            # The read-time basis is the SPLIT (the change is effective tomorrow); the revision covering the
            # requested effective time is the PUBLISH one, and the expectation is checked against that.
            assert current_foundation(h, other_id) == made.json()["change"]["split_foundation_revision_id"]
            same = apply(h, other_id, made.json()["change"]["new_foundation_revision_id"], "apply-same-1")
            assert same.status_code == 422 and same.json()["detail"]["code"] == "ACTION_NO_CHANGE"
            assert kinds(h, other_id) == ["ACCEPTED", "FAILED"]
        finally:
            h.close()

    def test_changed_reserve_is_stale_basis(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = applying(runner)
        try:
            action_id, _ = accepted(h, "2026-10-06")
            runner.step({"do": "reserve", "value": 25, "effective_from": "2026-10-31T00:00:00Z",
                         "decided": "2026-10-31T20:00:00Z"})
            current = current_foundation(h, action_id)
            h.clock.at = T_APPLY
            refused = apply(h, action_id, current, "apply-basis-1")
            assert refused.status_code == 409, refused.text
            detail = refused.json()["detail"]
            assert detail["code"] == "ACTION_FOUNDATION_STALE"
            assert detail["foundation_code"] == "FOUNDATION_EXPECTED_VALUE_STALE"
            assert detail["event"]["current_foundation_revision_id"] == current
            assert kinds(h, action_id) == ["ACCEPTED", "FAILED"]
        finally:
            h.close()

    def test_refusals_append_nothing(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = applying(runner)
        anon = applying(runner, command_access=lambda r, c: 401)
        scoped = applying(runner, command_access=lambda r, c: 403)
        denied = applying(runner, capability=no_capability)
        try:
            action_id, _ = accepted(h, "2026-10-06")
            expected = current_foundation(h, action_id)
            start = table_counts(runner)
            h.clock.at = T_APPLY
            assert apply(anon, action_id, expected, "apply-anon-1").status_code == 401
            assert apply(scoped, action_id, expected, "apply-scope-1").status_code == 403
            got = apply(denied, action_id, expected, "apply-deny-1")
            assert got.status_code == 403 and got.json()["detail"]["code"] == "SYSTEM_DEMO_CAPABILITY_DENIED"
            assert apply(h, action_id, expected, "apply-wrong-1", site="OTHER-001").status_code == 404
            assert apply(h, str(uuid4()), expected, "apply-unknown1").status_code == 404
            missing = apply(h, action_id, str(uuid4()), "apply-nofound1")
            assert missing.status_code == 404 and missing.json()["detail"]["code"] == "FOUNDATION_REVISION_NOT_FOUND"
            for over, code in (({"value": "fifteen"}, "COMMAND_INVALID"), ({"effective_from": "2026-11-02"},
                                                                          "COMMAND_INVALID"),
                               ({"actor": "ops"}, "CLIENT_AUTHORITY_FORBIDDEN"), ({"extra": 1}, "COMMAND_INVALID")):
                bad = apply(h, action_id, expected, "apply-bad-0001", **over)
                assert bad.status_code == 422 and bad.json()["detail"]["code"] == code, (over, bad.text)
            assert h.client.get(f"/api/sites/KOBO-001/foundation/changes/{uuid4()}").status_code == 404
            assert table_counts(runner) == start
            assert kinds(h, action_id) == ["ACCEPTED"]
        finally:
            for x in (h, anon, scoped, denied):
                x.close()


class TestLockOrderRollbackAndRaces:
    def test_action_row_is_locked_before_the_site(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = applying(runner)
        holder = create_engine(runner.engine.url)
        try:
            action_id, _ = accepted(h, "2026-10-06")
            expected = current_foundation(h, action_id)
            h.clock.at = T_APPLY
            out: list = []
            with holder.connect() as site_lock:
                tx = site_lock.begin()
                site_lock.execute(text("SELECT id FROM site WHERE id = :s FOR UPDATE"), {"s": runner.site})
                worker = threading.Thread(target=lambda: out.append(apply(h, action_id, expected, "apply-lock-1")))
                worker.start()
                waited = False
                deadline = time.monotonic() + 4
                while time.monotonic() < deadline and not waited:
                    with holder.connect() as probe:
                        waited = probe.execute(text(
                            "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock' "
                            "AND query LIKE 'SELECT id FROM site%FOR UPDATE'")).scalar_one() > 0
                    time.sleep(0.05)
                assert waited, "the apply never reached the Site lock"
                # While it waits for the Site, the apply already holds the Action row.
                with holder.connect() as probe:
                    with pytest.raises(OperationalError):
                        probe.execute(text("SELECT id FROM action WHERE id = :a FOR UPDATE NOWAIT"),
                                      {"a": action_id})
                tx.rollback()
                worker.join(timeout=30)
            assert out and out[0].status_code == 201, out and out[0].text
        finally:
            holder.dispose()
            h.close()

    def test_failure_after_the_s1_writes_rolls_everything_back(self, runner, monkeypatch) -> None:
        run_case(runner, CASES["F01"])
        h = applying(runner)
        try:
            action_id, _ = accepted(h, "2026-10-06")
            expected = current_foundation(h, action_id)
            start = table_counts(runner)
            original = PostgresActionStore._insert_applied

            def broken(self, c, *args, **kwargs):
                original(self, c, *args, **kwargs)  # Foundation, bindings, artifact and APPLIED all written...
                raise RuntimeError("injected failure before the commit")  # ...then the transaction aborts.

            monkeypatch.setattr(PostgresActionStore, "_insert_applied", broken)
            h.clock.at = T_APPLY
            with pytest.raises(RuntimeError, match="injected failure"):
                apply(h, action_id, expected, "apply-boom-1")
            assert table_counts(runner) == start  # no Foundation, binding, artifact, APPLIED or FAILED row
            monkeypatch.setattr(PostgresActionStore, "_insert_applied", original)
            assert current_foundation(h, action_id) == expected
            made = apply(h, action_id, expected, "apply-boom-1")
            assert made.status_code == 201, made.text
        finally:
            h.close()

    def test_concurrent_identical_applies_publish_once(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = applying(runner)
        try:
            action_id, _ = accepted(h, "2026-10-06")
            expected = current_foundation(h, action_id)
            start = table_counts(runner)
            h.clock.at = T_APPLY
            out = race(lambda: apply(h, action_id, expected, "apply-same-key"))
            assert sorted(r.status_code for r in out) == [200, 200, 200, 201], [r.text for r in out]
            assert len({r.json()["event"]["id"] for r in out}) == 1
            assert len({r.json()["change"]["change_id"] for r in out}) == 1
            end = table_counts(runner)
            assert end["foundation_revision"] == start["foundation_revision"] + 2
            assert end["action_policy_change"] == 1 and kinds(h, action_id) == ["ACCEPTED", "APPLIED"]
        finally:
            h.close()

    def test_concurrent_distinct_applies_publish_once(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = applying(runner)
        try:
            action_id, _ = accepted(h, "2026-10-06")
            expected = current_foundation(h, action_id)
            start = table_counts(runner)
            h.clock.at = T_APPLY
            keys = iter([f"apply-race-{i:04d}" for i in range(4)])
            lock = threading.Lock()

            def go():
                with lock:
                    key = next(keys)
                return apply(h, action_id, expected, key)

            out = race(go)
            assert sorted(r.status_code for r in out) == [201, 409, 409, 409], [r.text for r in out]
            assert {r.json()["detail"]["code"] for r in out if r.status_code == 409} == {"ACTION_ALREADY_APPLIED"}
            end = table_counts(runner)
            assert end["foundation_revision"] == start["foundation_revision"] + 2
            assert kinds(h, action_id) == ["ACCEPTED", "APPLIED"]
        finally:
            h.close()


def race(call, n: int = 4) -> list:
    out: list = []
    gate = threading.Barrier(n)

    def go() -> None:
        gate.wait()
        out.append(call())

    threads = [threading.Thread(target=go) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out
