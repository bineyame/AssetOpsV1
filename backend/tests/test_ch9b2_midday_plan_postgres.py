"""CH-9b2 L2 (build sheet CH-9b R1-R2, CH9b2-R): the mill Action's `midday-productive-shift-1` plan on Postgres (0052).

On the W4-02 MINIGRID Site with CH-4's seeded opportunity (the CH-9b1 `mill` fixture): the MINI Action is created,
its case COMPLETEd and linked (CH9b1-R2 order), and `VerificationService.freeze_domain_plan` freezes the plan from
real `site_day_snapshot` rows read through the real `SnapshotReader`:

- freeze at apply: the effective day (the case's COMPLETE `occurred_at`, Site-local) is in neither window; the baseline
  is the last 3 COMPLETE days before it (a LOW day and a COMPLETE effective day are skipped); the owner's target
  verbatim, `guardrails = {}`; one plan per Action (a second call replays it);
- SHORT: fewer than 3 COMPLETE days still freezes, `state = "SHORT"`, with the not-judged text;
- refusals: a MINI Action without a COMPLETE linked case, and an unknown Action (no plan row written);
- 0052's CHECKs: exactly one of action/domain_action on plan, request and outcome; the family coupling;
- 0052 downgrades to 0051 (refused while a domain plan exists) and upgrades back, the reserve-shaped plan columns
  unchanged.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_ch9b1_opportunity_actions_postgres import _complete_case, _create, mill  # noqa: F401
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_w203_cold_migration_postgres import head

    import pg_harness
    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.actions.ports import ActionRefused
    from assetops_backend.actions.verification import VerificationPorts, VerificationService
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.ports import SnapshotRow
    from assetops_backend.chain.reader import SnapshotReader


def _service(mill, now):
    snaps = PostgresSnapshotStore(URL)
    actions = SimpleNamespace(store=PostgresActionStore(URL), clock=lambda: now,
                              verification_ports=VerificationPorts(snapshots=SnapshotReader(snaps)))
    mill.disposables = [actions.store, snaps]
    return VerificationService(actions)


def _effective(mill, case_id):
    with mill.engine.connect() as c:
        occurred = c.execute(text("SELECT occurred_at FROM work_event WHERE case_id = :c AND kind = 'COMPLETE'"),
                             {"c": case_id}).scalar_one()
        tz = c.execute(text("SELECT timezone FROM site WHERE id = :s"), {"s": mill.s}).scalar_one()
    return occurred, tz, occurred.astimezone(ZoneInfo(tz)).date()


def _snap(mill, day, grade, subject="asset:mill"):
    PostgresSnapshotStore(URL).append(SnapshotRow(
        tenant_id=mill.t, site_id=mill.s, local_day=day, subject_kind="ASSET", subject_ref=subject,
        measure="productive_kwh", evidence_class="MEASURED", revision=1, expected=True, required_seconds=36000,
        covered_seconds=36000 if grade == "COMPLETE" else 1000, coverage_pct="100.0", grade=grade,
        value={"kwh": "12.5"}, money=None, policy_version="p1", calendar_version="c1", catalogue_version=1,
        input_fp=hashlib.sha256(f"{day}-{subject}-{grade}".encode()).hexdigest()))


def _applied(mill, tag="ch9b2"):
    action = _create(mill, idempotency_key=f"{tag}-mill-0001")
    case_id = _complete_case(mill, action["id"], tag)
    return action, case_id


def _close(mill):
    pg_harness.dispose(*getattr(mill, "disposables", []))


def test_freeze_at_apply_baseline_effective_day_target_and_replay(mill) -> None:
    action, case_id = _applied(mill)
    occurred, tz, eff = _effective(mill, case_id)
    for back in (1, 3, 4, 5, 6):
        _snap(mill, eff - timedelta(days=back), "COMPLETE")
    _snap(mill, eff - timedelta(days=1), "LOW", subject="asset:pump")  # day -1: one weak row, so it does not count
    _snap(mill, eff - timedelta(days=2), "LOW")
    _snap(mill, eff, "COMPLETE")  # the effective day is in neither window
    svc = _service(mill, occurred + timedelta(hours=1))
    try:
        status, body = svc.freeze_domain_plan(mill.t, mill.s, action["id"])
        assert status == 201 and body["replayed"] is False, body
        plan = body["plan"]
        sel = plan["baseline_selection"]
        assert sel["state"] == "COMPLETE" and sel["days"] == [(eff - timedelta(days=b)).isoformat() for b in (5, 4, 3)]
        assert plan["not_judged_text"] is None
        assert plan["rule_id"] == "midday-productive-shift-1"
        assert plan["plan_version"] == "midday-productive-shift-verification-1"
        assert plan["target"]["rule"] == "10*mean(later) >= 11*mean(baseline) productive_kwh[midday]"
        assert plan["target"]["ratio"] == [11, 10] and plan["guardrails"] == {}
        assert plan["triggering_fixture"] == "productive-load-midday@1"
        assert plan["basis"]["effective_day"] == eff.isoformat()
        assert plan["later_selection_rule"]["candidates"] == {
            "from": (eff + timedelta(days=1)).isoformat(), "to": (eff + timedelta(days=14)).isoformat()}
        assert [p["day"] for p in sel["pins"]] == sel["days"]
        with mill.engine.connect() as c:
            stored = c.execute(text(
                "SELECT action_id, domain_action_id, origin_finding_revision_id, origin_opportunity_revision_id, "
                "applied_event_id, applied_work_event_id, baseline_end, later_start, later_end, effective_from "
                "FROM verification_plan")).one()
            complete_id = c.execute(text("SELECT id FROM work_event WHERE case_id = :c AND kind = 'COMPLETE'"),
                                    {"c": case_id}).scalar_one()
            origin = c.execute(text("SELECT origin_opportunity_revision_id FROM domain_action WHERE id = :a"),
                               {"a": action["id"]}).scalar_one()
        assert stored.action_id is None and str(stored.domain_action_id) == action["id"]
        assert stored.origin_finding_revision_id is None
        assert str(stored.origin_opportunity_revision_id) == str(origin) == str(mill.seed["b_r2"])
        assert stored.applied_event_id is None and stored.applied_work_event_id == complete_id
        assert stored.baseline_end <= stored.effective_from < stored.later_start
        assert stored.later_start.astimezone(ZoneInfo(tz)).date() == eff + timedelta(days=1)
        assert stored.later_end - stored.later_start == timedelta(days=14)
        again_status, again = svc.freeze_domain_plan(mill.t, mill.s, action["id"])
        assert again_status == 200 and again["replayed"] is True and again["plan"]["plan_id"] == plan["plan_id"]
        with mill.engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM verification_plan")).scalar_one() == 1
    finally:
        _close(mill)


def test_short_baseline_freezes_with_the_not_judged_text(mill) -> None:
    action, case_id = _applied(mill, "ch9b2-short")
    occurred, _, eff = _effective(mill, case_id)
    for back in (2, 9):
        _snap(mill, eff - timedelta(days=back), "COMPLETE")
    _snap(mill, eff - timedelta(days=15), "COMPLETE")  # outside the 14-day look-back
    svc = _service(mill, occurred + timedelta(hours=1))
    try:
        status, body = svc.freeze_domain_plan(mill.t, mill.s, action["id"])
        assert status == 201, body
        assert body["plan"]["baseline_selection"]["state"] == "SHORT"
        assert body["plan"]["baseline_selection"]["found"] == 2
        assert body["plan"]["not_judged_text"] == "Not judged yet: only 2 of 3 fully checked days before the change"
    finally:
        _close(mill)


def test_refused_without_a_complete_linked_case_and_for_an_unknown_action(mill) -> None:
    action = _create(mill, idempotency_key="ch9b2-open-0001")
    svc = _service(mill, datetime.now(timezone.utc))
    try:
        with pytest.raises(ActionRefused) as refused:
            svc.freeze_domain_plan(mill.t, mill.s, action["id"])
        assert refused.value.code == "VERIFICATION_ACTION_NOT_APPLIED"
        with pytest.raises(ActionRefused) as missing:
            svc.freeze_domain_plan(mill.t, mill.s, uuid4())
        assert missing.value.code == "ACTION_NOT_FOUND"
        with mill.engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM verification_plan")).scalar_one() == 0
    finally:
        _close(mill)


def _plan_row(c):
    return dict(c.execute(text("SELECT * FROM verification_plan")).one()._mapping)


def _insert(c, table, row):
    cols = ", ".join(row)
    vals = ", ".join(f"CAST(:{k} AS jsonb)" if isinstance(v, (dict, list)) and k != "reasons" else f":{k}"
                     for k, v in row.items())
    c.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"),
              {k: json.dumps(v) if isinstance(v, (dict, list)) and k != "reasons" else v for k, v in row.items()})


def test_0052_checks_exactly_one_action_and_family_coupling(mill) -> None:
    action, case_id = _applied(mill, "ch9b2-checks")
    occurred, _, _ = _effective(mill, case_id)
    svc = _service(mill, occurred + timedelta(hours=1))
    try:
        svc.freeze_domain_plan(mill.t, mill.s, action["id"])
    finally:
        _close(mill)
    with mill.engine.connect() as c:
        plan = _plan_row(c)
    base = {k: v for k, v in plan.items() if v is not None}
    bad = {
        "both_actions": {**base, "action_id": uuid4()},
        "reserve_column_on_midday": {**base, "field": "reserve-state-of-charge"},
        "midday_superseded": {**base, "supersedes_plan_id": plan["id"]},
        "wrong_fixture": {**base, "triggering_fixture": "other@1"},
        "short_later_range": {**base, "later_end": plan["later_start"] + timedelta(days=13)},
        "midday_rule_reserve_version": {**base, "plan_version": "reserve-trial-verification-1"},
    }
    # Each row breaks one CHECK, which fires before the unique and FK checks: the constraint named is the proof.
    for name, row in bad.items():
        with mill.engine.connect() as c:
            with pytest.raises(IntegrityError) as err:
                _insert(c, "verification_plan", {**row, "id": uuid4()})
        named = err.value.orig.diag.constraint_name
        assert named in ("verification_plan_family", "verification_plan_one_action"), (name, named)
    request = {"id": uuid4(), "tenant_id": mill.t, "site_id": mill.s, "action_id": None, "domain_action_id": None,
               "plan_id": plan["id"], "actor_kind": "SYSTEM", "actor_id": "service:x", "source_channel":
               "SYSTEM_DEMONSTRATION_API", "authorization_basis": "b", "triggering_service": "s",
               "triggering_fixture": "f", "idempotency_key": "ch9b2-req-0001", "payload": {},
               "payload_sha256": "0" * 64, "recorded_at": occurred}
    outcome = {"id": uuid4(), "tenant_id": mill.t, "site_id": mill.s, "action_id": None, "domain_action_id": None,
               "plan_id": plan["id"], "outcome": "INCONCLUSIVE", "reasons": [], "basis": {}, "basis_sha256": "0" * 64,
               "details": {}, "actor_kind": "SYSTEM", "actor_id": "service:verification-evaluator",
               "triggering_job": "j", "idempotency_key": "ch9b2-out-0001", "recorded_at": occurred}
    for table, row in (("verification_evaluation_request", request), ("verification_outcome", outcome)):
        for name, over in (("neither", {}), ("both", {"action_id": uuid4(), "domain_action_id": action["id"]})):
            with mill.engine.connect() as c:
                with pytest.raises(IntegrityError, match=f"{table}_one_action"):
                    _insert(c, table, {**row, **over})
        with mill.engine.begin() as c:  # the domain twin FK admits the mill plan's own Action
            _insert(c, table, {**row, "domain_action_id": action["id"], "id": uuid4()})
    with mill.engine.connect() as c:
        with pytest.raises(IntegrityError, match="domain_plan_fk"):  # another domain Action's plan is refused
            _insert(c, "verification_outcome", {**outcome, "id": uuid4(), "domain_action_id": uuid4(),
                                                "idempotency_key": "ch9b2-out-0002"})


def test_0052_round_trip_and_refusal(mill) -> None:
    from alembic import command

    action, case_id = _applied(mill, "ch9b2-trip")
    occurred, _, _ = _effective(mill, case_id)
    svc = _service(mill, occurred + timedelta(hours=1))
    try:
        svc.freeze_domain_plan(mill.t, mill.s, action["id"])
    finally:
        _close(mill)
    assert head(mill.engine) == pg_harness.alembic_head()
    command.downgrade(_alembic(), "0052_verification_plan_domain")
    assert head(mill.engine) == "0052_verification_plan_domain"
    with pytest.raises(Exception) as refused:
        command.downgrade(_alembic(), "0051_action_opportunity_origin")
    assert "0052" in str(refused.value), refused.value
    assert head(mill.engine) == "0052_verification_plan_domain"
    with mill.engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("DELETE FROM verification_plan WHERE domain_action_id IS NOT NULL"))
    command.downgrade(_alembic(), "0051_action_opportunity_origin")
    with mill.engine.connect() as c:
        cols = set(c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = "
                                  "'verification_plan'")).scalars())
        nullable = dict(c.execute(text("SELECT column_name, is_nullable FROM information_schema.columns "
                                       "WHERE table_name = 'verification_plan'")).all())
    assert "domain_action_id" not in cols and nullable["action_id"] == "NO" and nullable["field"] == "NO"
    command.upgrade(_alembic(), "head")
    assert head(mill.engine) == pg_harness.alembic_head()


def test_q10_site_action_rows_read_no_domain_plan(mill) -> None:
    """CH9b2-R Q10: the Site-wide `action_rows` plan read stays W1-only, so a domain plan never surfaces as action
    `None` (its existing bodies stay byte-equal)."""
    from assetops_backend.chain.adapters.postgres_chain_read import PostgresChainRead

    action, case_id = _applied(mill, "ch9b2-q10")
    occurred, _, _ = _effective(mill, case_id)
    svc = _service(mill, occurred + timedelta(hours=1))
    reader = PostgresChainRead(URL, action_window=lambda *a, **k: {"actions": (), "events": ()})
    try:
        svc.freeze_domain_plan(mill.t, mill.s, action["id"])
        with mill.engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM verification_plan")).scalar_one() == 1
        assert reader.action_rows(mill.t, mill.s, None)["plans"] == ()
    finally:
        _close(mill)
        pg_harness.dispose(reader)
