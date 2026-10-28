"""CC-M (owner Q14): migrations `0036_cc_mini_contribution` and `0037_cc_trial_cost_comparison` against Postgres.

`.agent/build-spec-commercial-2026-10-27.md` "CC-M" gates: the chain and sole head; the exact
`trial_cost_comparison_revision` catalog (columns, named CHECKs, FKs, UNIQUEs, index, trigger); the new mini scenario
kind is admitted after 0036 and refused before it, and 0036's downgrade refuses while a row uses it; `downgrade
0035_w5_ev_work` then `upgrade head`; the append-only trigger refuses UPDATE and DELETE; the chain CHECK refuses
revision 2 without `supersedes_revision_id`; the outcome must belong to the Action.

The trial rows hang off a real verification outcome: S4 F01/F02, the S6-01 apply and the S6-02a real roles-2 path
(INCONCLUSIVE, as in `test_s6_verification_evaluator_postgres`). The mini scenario kind rows are direct SQL written in
the replica role (CHECKs still apply; the FK and append-only triggers do not), because they exercise only the CHECK
and the downgrade guard. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import pg_harness
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s6_action_store_postgres import CASES, runner  # noqa: F401
    from test_s6_verification_evaluator_postgres import CLOSED, bind, caught_up, evaluate, later_generator_off
    from test_s6_verification_plan_postgres import applied_action, freeze, release_engines, verifying  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head

HEAD = "0037_cc_trial_cost_comparison"
CONTRIBUTION = "0036_cc_mini_contribution"
PREVIOUS = "0035_w5_ev_work"
TABLE = "trial_cost_comparison_revision"
KIND = "PRODUCTIVE_USE_CONTRIBUTION"
KIND_CHECK = "mini_scenario_revision_kind_check"
REFUSED = "Downgrade of 0036_cc_mini_contribution refused: PRODUCTIVE_USE_CONTRIBUTION scenario revisions exist."
SHA = "a" * 64

CHECKS = sorted([f"{TABLE}_{c}_check" for c in ("revision_no", "chain", "formula", "state", "reason",
                                                "reason_state", "basis_sha256", "actor_kind", "actor_id",
                                                "source_channel", "authorization_basis", "triggering_service",
                                                "triggering_fixture", "idempotency_key", "payload_sha256")])
FKS = sorted(f"{TABLE}_{n}" for n in ("site_fk", "action_fk", "outcome_fk", "supersedes_fk"))
UNIQUES = sorted(f"{TABLE}_{n}" for n in ("revision_no_unique", "outcome_id_unique", "basis_unique",
                                          "idempotency_unique"))
COLUMNS = [
    ("id", "uuid", True), ("tenant_id", "uuid", True), ("site_id", "uuid", True), ("action_id", "uuid", True),
    ("verification_outcome_id", "uuid", True), ("revision_no", "integer", True),
    ("supersedes_revision_id", "uuid", False), ("formula", "text", True), ("state", "text", True),
    ("reason", "text", False), ("result", "jsonb", True), ("intervention_cost", "jsonb", True),
    ("price_revision_id", "uuid", False), ("basis_sha256", "text", True), ("actor_kind", "text", True),
    ("actor_id", "text", True), ("source_channel", "text", True), ("authorization_basis", "text", True),
    ("triggering_service", "text", True), ("triggering_fixture", "text", True), ("idempotency_key", "text", True),
    ("payload_sha256", "text", True), ("recorded_at", "timestamp with time zone", True),
]

SCENARIO_INSERT = (
    "INSERT INTO mini_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, name, kind, narrative, "
    "assumptions, calculation, actor_kind, actor_id, authorization_basis, attestation, idempotency_key, "
    "payload_sha256) VALUES (:id, :t, :s, :sc, 1, 'CC-M probe', :kind, 'probe', CAST('[]' AS jsonb), "
    "CAST('{}' AS jsonb), 'SERVICE', 'service:cc-m', 'probe', 'probe', :key, :sha)")
TRIAL_INSERT = (
    f"INSERT INTO {TABLE} (id, tenant_id, site_id, action_id, verification_outcome_id, revision_no, "
    "supersedes_revision_id, formula, state, reason, result, intervention_cost, price_revision_id, basis_sha256, "
    "actor_kind, actor_id, source_channel, authorization_basis, triggering_service, triggering_fixture, "
    "idempotency_key, payload_sha256, recorded_at) VALUES (:id, :t, :s, :a, :o, :no, :sup, :formula, :state, "
    ":reason, CAST(:result AS jsonb), CAST(:cost AS jsonb), NULL, :basis, 'SYSTEM', 'service:cc-m-probe', "
    "'SYSTEM_DEMONSTRATION_API', 'CC-M schema probe', 'cc-m', 'cc-m-schema', :key, :sha, clock_timestamp())")


def scalar(engine, sql: str, **params):  # noqa: F811
    with engine.connect() as c:
        return c.execute(text(sql), params).scalar()


def names(engine, contype: str) -> list[str]:  # noqa: F811
    with engine.connect() as c:
        return sorted(c.execute(text("SELECT conname FROM pg_constraint WHERE contype = :k AND conrelid = "
                                     f"'{TABLE}'::regclass"), {"k": contype}).scalars())


def rejects(engine, sql: str, params: dict, constraint: str | None = None, match: str | None = None) -> None:  # noqa: F811
    with pytest.raises(DBAPIError, match=match) as caught:
        with engine.begin() as c:
            c.execute(text(sql), params)
    if constraint is not None:
        assert getattr(getattr(caught.value.orig, "diag", None), "constraint_name", None) == constraint, caught.value


def scenario_row(kind: str) -> dict:
    return {"id": str(uuid4()), "t": str(uuid4()), "s": str(uuid4()), "sc": str(uuid4()), "kind": kind,
            "key": f"cc-m-{uuid4().hex[:12]}", "sha": SHA}


def insert_scenario(engine, row: dict) -> None:  # noqa: F811
    """Replica role: the CHECKs apply, the scenario FK and append-only triggers do not (CHECK probe only)."""
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text(SCENARIO_INSERT), row)


def test_chain_sole_head_and_trial_catalog(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [HEAD] and head(engine) == HEAD
    pg_harness.assert_at_head(engine)
    assert script.get_revision(HEAD).down_revision == CONTRIBUTION
    assert script.get_revision(CONTRIBUTION).down_revision == PREVIOUS
    with engine.connect() as c:
        columns = [tuple(r) for r in c.execute(text(
            "SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull FROM pg_attribute a "
            f"WHERE a.attrelid = '{TABLE}'::regclass AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum"))]
        index = c.execute(text("SELECT indexdef FROM pg_indexes WHERE indexname = :n"),
                          {"n": f"{TABLE}_order"}).scalar()
        triggers = sorted(c.execute(text(
            "SELECT t.tgname || ':' || p.proname FROM pg_trigger t JOIN pg_proc p ON p.oid = t.tgfoid "
            f"WHERE NOT t.tgisinternal AND t.tgrelid = '{TABLE}'::regclass")).scalars())
    assert columns == COLUMNS
    assert names(engine, "p") == [f"{TABLE}_pkey"]
    assert names(engine, "c") == CHECKS and names(engine, "f") == FKS and names(engine, "u") == UNIQUES
    assert index.endswith("(tenant_id, site_id, action_id, recorded_at)"), index
    assert triggers == [f"{TABLE}_immutable:w4_append_only"]
    assert KIND in scalar(engine, "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :n",
                          n=KIND_CHECK)


def test_contribution_kind_gate_downgrade_refusal_and_round_trip(engine) -> None:  # noqa: F811
    from alembic import command

    used = scenario_row(KIND)
    insert_scenario(engine, used)  # admitted at head (after 0036)
    config = _alembic()
    engine.dispose()
    with pytest.raises(DBAPIError, match=REFUSED):
        command.downgrade(config, PREVIOUS)
    assert head(engine) == HEAD and scalar(engine, f"SELECT to_regclass('{TABLE}') IS NOT NULL")
    _replica(engine, f"DELETE FROM mini_scenario_revision WHERE id = '{used['id']}'")

    engine.dispose()
    command.downgrade(config, PREVIOUS)
    assert head(engine) == PREVIOUS and not scalar(engine, f"SELECT to_regclass('{TABLE}') IS NOT NULL")
    with pytest.raises(DBAPIError) as caught:
        insert_scenario(engine, scenario_row(KIND))  # refused before 0036
    assert caught.value.orig.diag.constraint_name == KIND_CHECK
    old = scenario_row("TARIFF_ONLY")
    insert_scenario(engine, old)  # the four 0030 kinds still pass at 0035
    _replica(engine, f"DELETE FROM mini_scenario_revision WHERE id = '{old['id']}'")

    engine.dispose()
    command.upgrade(config, "head")
    assert head(engine) == HEAD
    pg_harness.assert_at_head(engine)
    again = scenario_row(KIND)
    insert_scenario(engine, again)
    _replica(engine, f"DELETE FROM mini_scenario_revision WHERE id = '{again['id']}'")


def real_outcome(runner) -> tuple[str, str, str, str]:  # noqa: F811
    """One real INCONCLUSIVE verification outcome over S4 F01/F02 (the S6-02a real roles-2 path)."""
    run_case(runner, CASES["F01"])
    run_case(runner, CASES["F02"])
    h = verifying(runner)
    try:
        action_id = applied_action(runner, h)
        plan = freeze(h, action_id).json()["plan"]
        h.clock.at = CLOSED
        later_generator_off(runner)
        caught_up(runner, h, CLOSED)
        assert bind(h, action_id, plan["plan_id"], "bind-0001").status_code == 201
        made = evaluate(h, action_id, "eval-0001")
        assert made.status_code == 201, made.text
        outcome_id = made.json()["outcome"]["outcome_id"]
    finally:
        h.close()
    with runner.engine.connect() as c:
        t, s = c.execute(text("SELECT CAST(tenant_id AS text), CAST(site_id AS text) FROM verification_outcome "
                              "WHERE id = :o"), {"o": outcome_id}).one()
    return t, s, action_id, outcome_id


def trial(t: str, s: str, a: str, o: str, no: int, sup: str | None, **over) -> dict:
    row = {"id": str(uuid4()), "t": t, "s": s, "a": a, "o": o, "no": no, "sup": sup,
           "formula": "trial-fuel-comparison/1", "state": "UNAVAILABLE", "reason": "OUTCOME_INCONCLUSIVE",
           "result": json.dumps({"state": "UNAVAILABLE"}),
           "cost": json.dumps({"amount": "0", "currency": None, "source": "DEFAULT"}),
           "basis": uuid4().hex + uuid4().hex, "key": f"cc-m-{uuid4().hex[:12]}", "sha": SHA}
    return {**row, **over}


def test_trial_rows_chain_scope_and_append_only(runner, engine) -> None:  # noqa: F811
    t, s, a, o = real_outcome(runner)
    try:
        first = trial(t, s, a, o, 1, None)
        with engine.begin() as c:
            c.execute(text(TRIAL_INSERT), first)

        # Chain: revision 2 needs `supersedes_revision_id`; revision 1 must not carry one.
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 2, None), f"{TABLE}_chain_check")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 1, first["id"]), f"{TABLE}_chain_check")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 0, first["id"]), f"{TABLE}_revision_no_check")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 2, str(uuid4())), f"{TABLE}_supersedes_fk")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 1, None), f"{TABLE}_revision_no_unique")
        second = trial(t, s, a, o, 2, first["id"], state="MODELLED_IMPROVEMENT", reason=None)
        with engine.begin() as c:
            c.execute(text(TRIAL_INSERT), second)

        # State, reason and formula vocabularies; reason iff UNAVAILABLE.
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 3, second["id"], reason=None), f"{TABLE}_reason_state_check")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 3, second["id"], state="MODELLED_NO_IMPROVEMENT"),
                f"{TABLE}_reason_state_check")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 3, second["id"], reason="NOT_A_REASON"),
                f"{TABLE}_reason_check")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 3, second["id"], state="SAVED", reason=None),
                f"{TABLE}_state_check")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 3, second["id"], formula="trial-fuel-comparison/2"),
                f"{TABLE}_formula_check")

        # Uniques: one basis per outcome, one idempotency key per Action.
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 3, second["id"], basis=first["basis"]),
                f"{TABLE}_basis_unique")
        rejects(engine, TRIAL_INSERT, trial(t, s, a, o, 3, second["id"], key=first["key"]),
                f"{TABLE}_idempotency_unique")

        # Scope: the outcome belongs to the Action, the Action to the Site.
        rejects(engine, TRIAL_INSERT, trial(t, s, a, str(uuid4()), 1, None), f"{TABLE}_outcome_fk")
        rejects(engine, TRIAL_INSERT, trial(t, s, str(uuid4()), o, 3, second["id"]), f"{TABLE}_action_fk")
        rejects(engine, TRIAL_INSERT, trial(t, str(uuid4()), a, o, 3, second["id"]), f"{TABLE}_site_fk")

        # Append-only: the 0027 `w4_append_only()` trigger refuses UPDATE and DELETE.
        rejects(engine, f"UPDATE {TABLE} SET state = 'UNAVAILABLE' WHERE id = :id", {"id": second["id"]},
                match="append only")
        rejects(engine, f"DELETE FROM {TABLE} WHERE id = :id", {"id": first["id"]}, match="append only")
        assert scalar(engine, f"SELECT count(*) FROM {TABLE} WHERE verification_outcome_id = :o", o=o) == 2
    finally:
        _replica(engine, f"DELETE FROM {TABLE}")
