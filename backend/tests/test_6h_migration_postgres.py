"""6h (`specs/6h-named-option-levers/spec.md` §3.4, §6.1, §10.2 test 5): migration 0073 on a test DB.

The two widened checks accept the new values and refuse others; `option_record`'s constraints refuse by name; the
table is append-only; the downgrade refuses while a new value is held, then restores both checks and drops the table."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_on1_onboarding_postgres import onboarded  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from test_6a_migration_postgres import (T, TABLES, _decision, _full_run, _insert, _option, _refused,  # noqa: F401
                                            world)

PAIR = ("0073_named_option_levers", "0072_decision_records")
VERSIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"
CHECKS = {"option_record_factor_id_check", "option_record_unit_check", "option_record_currency_check",
          "option_record_origin_check", "option_record_document_check", "option_record_basis_check",
          "option_record_declared_role_check", "option_record_declared_at_check"}
FKS = {"option_record_tenant_id_option_id_fkey", "option_record_tenant_id_declared_by_person_id_fkey"}


def _named_decision(w, period="2026-10") -> tuple[dict, list[dict]]:
    decision = _decision(w, period=period, site_id=w["sites"]["KOBO-001"], structure_key="COLD_CHAIN",
                         lever_id="storage_contract", purpose_factor_id="contract_crate_days", current_settings={})
    options = [_option(w, decision["id"], "no-action", 0, settings={}),
               _option(w, decision["id"], "storage-contract", 1, generator="STATED_OPTIONS", settings={})]
    return decision, options


def _record(w, option_id, **over) -> dict:
    row = dict(id=uuid4(), tenant_id=w["tenant"], option_id=option_id, factor_id="contract_crate_days",
               value="4500", unit="d", currency=None, origin="source-emulated",
               document="Draft storage contract, Mwea Horticulture Aggregators", basis="the contract's term",
               declared_by_person_id=w["people"]["Joseph"], declared_role="FINANCE_AND_COMMERCIAL_LEAD",
               declared_by_script=True, declared_at=T)
    row.update(over)
    return row


@pytest.fixture()
def named(world, engine):  # noqa: F811
    decision, options = _named_decision(world)
    with engine.begin() as c:
        _insert(c, "decision", decision)
        for option in options:
            _insert(c, "decision_option", option)
        rows = _full_run(world, decision["id"], options, outcome="BOUNDS_NOT_CHECKED", study_sha256=None,
                         study_identity=None)
        for table, row in rows:
            _insert(c, table, row)
        record = _record(world, options[1]["id"])
        _insert(c, "option_record", record)
    return {**world, "decision": decision, "options": options, "record": record}


def test_5_chain_names_and_catalogue(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory
    scripts = ScriptDirectory.from_config(pg_harness._alembic(URL))
    assert scripts.get_revision(PAIR[0]).down_revision == PAIR[1]
    files = sorted(p.name for p in VERSIONS.glob("[0-9][0-9][0-9][0-9]_*.py"))
    assert files[files.index(f"{PAIR[0]}.py") - 1] == f"{PAIR[1]}.py"
    with engine.connect() as c:
        defs = dict(c.execute(text(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname IN "
            "('decision_option_generator_check', 'option_evaluation_run_outcome_check')")).all())
        assert "STATED_OPTIONS" in defs["decision_option_generator_check"]
        assert "BOUNDS_NOT_CHECKED" in defs["option_evaluation_run_outcome_check"]
        found = {kind: set(c.execute(text(
            "SELECT conname FROM pg_constraint WHERE conrelid = CAST('option_record' AS regclass) AND contype = :k"),
            {"k": kind}).scalars()) for kind in "cuf"}
        assert found == {"c": CHECKS, "u": {"option_record_tenant_id_unique"}, "f": FKS}
        triggers = dict(c.execute(text("SELECT tgname, tgfoid::regproc::text FROM pg_trigger WHERE tgrelid = "
                                       "CAST('option_record' AS regclass) AND NOT tgisinternal")).all())
        assert triggers == {"option_record_immutable": "ledger_append_only",
                            "option_record_no_truncate": "ledger_append_only"}
        assert c.execute(text("SELECT count(*) FROM pg_indexes WHERE indexname = 'option_record_latest'")
                         ).scalar_one() == 1


def test_5_the_new_values_are_accepted_and_others_refused(named, engine) -> None:  # noqa: F811
    w = named
    with engine.connect() as c:
        assert c.execute(text("SELECT generator FROM decision_option WHERE id = :i"),
                         {"i": w["options"][1]["id"]}).scalar_one() == "STATED_OPTIONS"
    decision, options = _named_decision(w, "2026-11")
    options[1]["generator"] = "CHOICE_LIST"
    _refused(engine, [("decision", decision), *[("decision_option", o) for o in options]],
             "decision_option_generator_check")
    decision, options = _named_decision(w, "2026-12")
    run = _full_run(w, decision["id"], options, outcome="BOUNDS_UNKNOWN", study_sha256=None, study_identity=None)
    _refused(engine, [("decision", decision), *[("decision_option", o) for o in options], *run],
             "option_evaluation_run_outcome_check")


@pytest.mark.parametrize("over,name", [
    ({"factor_id": "Contract"}, "option_record_factor_id_check"),
    ({"unit": ""}, "option_record_unit_check"),
    ({"currency": "usd"}, "option_record_currency_check"),
    ({"origin": "demo-simulated"}, "option_record_origin_check"),
    ({"document": " padded"}, "option_record_document_check"),
    ({"basis": "x" * 201}, "option_record_basis_check"),
    ({"declared_role": "ANALYST"}, "option_record_declared_role_check"),
    ({"declared_at": T.replace(microsecond=5)}, "option_record_declared_at_check"),
    ({"option_id": uuid4()}, "option_record_tenant_id_option_id_fkey"),
])
def test_5_each_record_constraint_refuses_by_name(named, engine, over, name) -> None:  # noqa: F811
    row = {**_record(named, named["options"][1]["id"]), **over}
    _refused(engine, [("option_record", row)], name)


def test_5_records_are_append_only_and_the_downgrade_refuses_then_restores(named, engine) -> None:  # noqa: F811
    from alembic import command
    for sql in ("UPDATE option_record SET id = id", "DELETE FROM option_record", "TRUNCATE option_record"):
        with pytest.raises(Exception, match="option_record rows are append-only"):
            with engine.begin() as c:
                c.execute(text(sql))
    cfg = pg_harness._alembic(URL)
    with pytest.raises(Exception, match="Downgrade of 0073_named_option_levers refused: named-option rows exist"):
        command.downgrade(cfg, PAIR[1])
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("DELETE FROM option_record"))
    with pytest.raises(Exception, match="refused: named-option rows exist"):  # the STATED_OPTIONS option remains
        command.downgrade(cfg, PAIR[1])
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for table in reversed(TABLES):
            c.execute(text(f"DELETE FROM {table}"))
    command.downgrade(cfg, PAIR[1])
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('option_record')")).scalar_one() is None
        defs = dict(c.execute(text(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname IN "
            "('decision_option_generator_check', 'option_evaluation_run_outcome_check')")).all())
        assert "STATED_OPTIONS" not in defs["decision_option_generator_check"]
        assert "BOUNDS_NOT_CHECKED" not in defs["option_evaluation_run_outcome_check"]
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)
    from alembic.script import ScriptDirectory  # review L2: pin which head, not only that there is one
    assert len(ScriptDirectory.from_config(cfg).get_heads()) == 1  # DD3c: 0074 follows; one head, no longer this pair
