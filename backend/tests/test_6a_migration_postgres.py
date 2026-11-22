"""6a (`specs/6a-decision-records/spec.md` §2, §6 test 6; handshake R4): migration 0072, the decision records.

Every check, unique and foreign key of §2 on a hand row, each violation asserted by constraint name; the catalogue
holds exactly the named constraints; the two deferred triggers (`decision_has_no_action`,
`option_evaluation_run_complete`); each table's UPDATE, DELETE and TRUNCATE refused; the downgrade refused with rows
and done empty; one `alembic heads`.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise. Run through
`tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_on1_onboarding_postgres import onboarded  # noqa: F401 - Lakeside onboarded through ON1's command
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.accounts.composition import build_account_service
    from test_3c0a_accounts_postgres import seed_tenant
    from test_3c0a_accounts_service import PW

#: Gate A's hand pair (spec §0): built on `main`'s head 0071; renumbered at gate B with the file.
HAND_PAIR = ("0072_decision_records", "0071_person_on_actions")
VERSIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"
SLUG = "lakeside-power"
TABLES = ("decision", "decision_option", "option_one_off", "option_evaluation_run", "option_evaluation",
          "option_effect", "decision_choice")
T = datetime(2026, 11, 24, 9, 0, 0, tzinfo=timezone.utc)
MICRO = datetime(2026, 11, 24, 9, 0, 0, 5, tzinfo=timezone.utc)
JSONB = {"current_settings", "settings", "study_identity", "missing", "assumed", "admission", "dawn"}
NO_ACTION = "has no no-action option"

#: Handshake R4: table-level and multi-column CHECKs by name; column checks keep `<table>_<column>_check`.
CHECKS = {
    "decision": {"decision_structure_key_check", "decision_lever_id_check", "decision_purpose_factor_id_check",
                 "decision_period_check", "decision_horizon_months_check", "decision_current_settings_check",
                 "decision_rule_version_check", "decision_prepared_role_check", "decision_prepared_at_check"},
    "decision_option": {"decision_option_option_key_check", "decision_option_generator_check",
                        "decision_option_settings_check", "decision_option_position_check",
                        "decision_option_no_action_key", "decision_option_no_action_first"},
    "option_one_off": {"option_one_off_amount_check", "option_one_off_currency_check",
                       "option_one_off_crew_visits_check", "option_one_off_basis_check",
                       "option_one_off_declared_role_check", "option_one_off_declared_at_check"},
    "option_evaluation_run": {"option_evaluation_run_evaluator_version_check", "option_evaluation_run_outcome_check",
                              "option_evaluation_run_study_sha256_check", "option_evaluation_run_study_identity_check",
                              "option_evaluation_run_known_at_check", "option_evaluation_run_run_role_check",
                              "option_evaluation_run_run_at_check", "option_evaluation_run_study_pair"},
    "option_evaluation": {"option_evaluation_disposition_check", "option_evaluation_reason_code_check",
                          "option_evaluation_rank_check", "option_evaluation_currency_check",
                          "option_evaluation_source_class_check", "option_evaluation_evidence_class_check",
                          "option_evaluation_missing_check", "option_evaluation_assumed_check",
                          "option_evaluation_admission_check", "option_evaluation_dawn_check",
                          "option_evaluation_value_or_missing", "option_evaluation_value_currency",
                          "option_evaluation_comparison", "option_evaluation_recommended_first"},
    "option_effect": {"option_effect_factor_id_check", "option_effect_position_check", "option_effect_unit_check",
                      "option_effect_currency_check", "option_effect_missing_check",
                      "option_effect_change_or_missing"},
    "decision_choice": {"decision_choice_chosen_role_check", "decision_choice_chosen_at_check"},
}
UNIQUES = {
    "decision": {"decision_tenant_id_unique"},
    "decision_option": {"decision_option_tenant_id_unique", "decision_option_key_unique",
                        "decision_option_position_unique"},
    "option_one_off": {"option_one_off_tenant_id_unique"},
    "option_evaluation_run": {"option_evaluation_run_tenant_id_unique"},
    "option_evaluation": {"option_evaluation_tenant_id_unique", "option_evaluation_once"},
    "option_effect": {"option_effect_once"},
    "decision_choice": {"decision_choice_once"},
}
#: Postgres's default names for §2's unnamed foreign keys.
FKS = {
    "decision": {"decision_tenant_id_fkey", "decision_tenant_id_site_id_fkey",
                 "decision_tenant_id_site_id_finding_id_fkey", "decision_tenant_id_prepared_by_person_id_fkey"},
    "decision_option": {"decision_option_tenant_id_decision_id_fkey"},
    "option_one_off": {"option_one_off_tenant_id_option_id_fkey", "option_one_off_tenant_id_declared_by_person_id_fkey"},
    "option_evaluation_run": {"option_evaluation_run_tenant_id_decision_id_fkey",
                              "option_evaluation_run_tenant_id_run_by_person_id_fkey"},
    "option_evaluation": {"option_evaluation_tenant_id_run_id_fkey", "option_evaluation_tenant_id_option_id_fkey",
                          "option_evaluation_tenant_id_one_off_id_fkey"},
    "option_effect": {"option_effect_tenant_id_evaluation_id_fkey"},
    "decision_choice": {"decision_choice_tenant_id_decision_id_fkey", "decision_choice_tenant_id_option_id_fkey",
                        "decision_choice_tenant_id_run_id_fkey", "decision_choice_tenant_id_agreed_action_id_fkey",
                        "decision_choice_tenant_id_chosen_by_person_id_fkey"},
}
INDEXES = {"decision_once", "decision_tenant", "option_one_off_latest", "option_evaluation_run_latest",
           "option_evaluation_one_recommended"}


#: D-P6.32: `option_effect_change_or_missing` is guarded on the array type, so a non-array `missing` reaches
#: `option_effect_missing_check` and is refused by its name like every other constraint.


# --- hand rows ------------------------------------------------------------------------------------------------------

def _insert(conn, table: str, row: dict) -> None:
    cols = ", ".join(row)
    vals = ", ".join(f"CAST(:{c} AS jsonb)" if c in JSONB else f":{c}" for c in row)
    params = {c: (json.dumps(v) if c in JSONB and v is not None else v) for c, v in row.items()}
    conn.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"), params)


def _decision(w, **over) -> dict:
    row = dict(id=uuid4(), tenant_id=w["tenant"], site_id=w["sites"]["KOBO-001"], structure_key="MINI_GRID",
               lever_id="generator_stop_reserve", purpose_factor_id="candidate_l", finding_id=None, period="2026-10",
               horizon_months=12, current_settings={"stop_soc_pct": "90", "reserve_soc_pct": "30"},
               rule_version="decision-prepare-1", prepared_by_person_id=w["people"]["Wanjiru"],
               prepared_role="ANALYST", prepared_by_script=True, prepared_at=T)
    row.update(over)
    return row


def _option(w, decision_id, key: str, position: int, **over) -> dict:
    generator = "NO_ACTION" if key == "no-action" else "SETTING_GRID"
    row = dict(id=uuid4(), tenant_id=w["tenant"], decision_id=decision_id, option_key=key, generator=generator,
               settings={"stop_soc_pct": "90", "reserve_soc_pct": "30"}, position=position)
    row.update(over)
    return row


def _one_off(w, option_id, **over) -> dict:
    row = dict(id=uuid4(), tenant_id=w["tenant"], option_id=option_id, amount="90.00", currency="USD",
               crew_visits=0, basis="Technician sets the controller on a routine visit",
               declared_by_person_id=w["people"]["Peter"], declared_role="SITE_MANAGER", declared_by_script=True,
               declared_at=T)
    row.update(over)
    return row


def _run(w, decision_id, **over) -> dict:
    row = dict(id=uuid4(), tenant_id=w["tenant"], decision_id=decision_id, evaluator_version="option-evaluator-1",
               outcome="RANKING_INCOMPLETE", study_sha256="a" * 64, study_identity={"study": "kobo"}, known_at=T,
               run_by_person_id=w["people"]["Wanjiru"], run_role="ANALYST", run_by_script=True, run_at=T)
    row.update(over)
    return row


def _evaluation(w, run_id, option_id, **over) -> dict:
    row = dict(id=uuid4(), tenant_id=w["tenant"], run_id=run_id, option_id=option_id, disposition="ACCEPTABLE",
               reason_code=None, rank=None, monthly_change="12.5", horizon_change="150", one_off_id=None,
               value="60", currency="USD", source_class="SIMULATED", evidence_class="MODELLED", missing=[],
               assumed=["fuel_price"], admission={"admitted": "13/14"}, dawn={"limit_pct": 30})
    row.update(over)
    return row


def _comparison(w, run_id, option_id, **over) -> dict:
    return _evaluation(w, run_id, option_id, disposition="COMPARISON", value="0", currency=None, **over)


def _effect(w, evaluation_id, **over) -> dict:
    row = dict(id=uuid4(), tenant_id=w["tenant"], evaluation_id=evaluation_id, factor_id="fuel_cost", position=0,
               change_per_month="-12.5", unit="USD", currency="USD", missing=[])
    row.update(over)
    return row


def _choice(w, decision_id, run_id, option_id, **over) -> dict:
    row = dict(id=uuid4(), tenant_id=w["tenant"], decision_id=decision_id, option_id=option_id, run_id=run_id,
               agreed_action_id=None, chosen_by_person_id=w["people"]["Amina"], chosen_role="OPERATOR_EXECUTIVE",
               chosen_by_script=True, chosen_at=T)
    row.update(over)
    return row


def _full_run(w, decision_id, options: list[dict], **over) -> list[tuple[str, dict]]:
    """A run and one evaluation per option (no-action COMPARISON), so the deferred trigger passes."""
    run = _run(w, decision_id, **over)
    rows = [("option_evaluation_run", run)]
    for option in options:
        make = _comparison if option["option_key"] == "no-action" else _evaluation
        rows.append(("option_evaluation", make(w, run["id"], option["id"])))
    return rows


@pytest.fixture()
def world(onboarded, engine):  # noqa: F811
    """Lakeside (ON1) with D1 (three options, a run R1, an effect, a one-off, a choice with an agreed Action) and D2
    (the same options and a run R2, no choice); `other-op` with Zara."""
    with engine.connect() as c:
        tenant = c.execute(text("SELECT id FROM tenant WHERE slug = :s"), {"s": SLUG}).scalar_one()
        people = dict(c.execute(text("SELECT display_name, id FROM operator_account WHERE tenant_id = :t"),
                                {"t": tenant}).all())
        sites = dict(c.execute(text("SELECT site_code, id FROM site WHERE tenant_id = :t"), {"t": tenant}).all())
    other = seed_tenant(engine, "other-op")
    zara = build_account_service(URL).onboard_create("other-op", "zara@other-op.example", "Zara", PW, executive=True)
    w = {"tenant": tenant, "people": people, "sites": sites, "other": other, "zara": zara}
    action = dict(id=uuid4(), tenant_id=tenant, title="Lower the generator stop point", site_id=sites["KOBO-001"],
                  factor_id="candidate_l", owner_person_id=people["Peter"], created_by_person_id=people["Amina"],
                  created_role="OPERATOR_EXECUTIVE", created_by_script=True, created_at=T, due_on=date(2026, 12, 15),
                  origin="DEEP_DIVE")
    w["action"] = action["id"]
    with engine.begin() as c:
        _insert(c, "agreed_action", action)
        for name, period in (("d1", "2026-10"), ("d2", "2026-11")):
            decision = _decision(w, period=period)
            options = [_option(w, decision["id"], "no-action", 0),
                       _option(w, decision["id"], "stop-90-reserve-25", 1,
                               settings={"stop_soc_pct": "90", "reserve_soc_pct": "25"}),
                       _option(w, decision["id"], "stop-70-reserve-30", 2,
                               settings={"stop_soc_pct": "70", "reserve_soc_pct": "30"})]
            _insert(c, "decision", decision)
            for option in options:
                _insert(c, "decision_option", option)
            one_off = _one_off(w, options[2]["id"])
            _insert(c, "option_one_off", one_off)
            run_rows = _full_run(w, decision["id"], options)
            for table, row in run_rows:
                _insert(c, table, row)
            evaluation = run_rows[3][1]
            _insert(c, "option_effect", _effect(w, evaluation["id"]))
            w[name] = {"decision": decision, "options": options, "one_off": one_off, "run": run_rows[0][1],
                       "evaluation": evaluation}
        _insert(c, "decision_choice", _choice(w, w["d1"]["decision"]["id"], w["d1"]["run"]["id"],
                                              w["d1"]["options"][2]["id"], agreed_action_id=action["id"]))
    return w


def _refused(engine, rows: list[tuple[str, dict]], match: str) -> None:  # noqa: F811
    with pytest.raises(Exception, match=match):
        with engine.begin() as c:
            for table, row in rows:
                _insert(c, table, row)


def _counts(engine) -> dict[str, int]:  # noqa: F811
    with engine.connect() as c:
        return {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in TABLES}


# --- test 6a: the catalogue -----------------------------------------------------------------------------------------

def test_6a_chain_and_catalogue(engine) -> None:  # noqa: F811
    cfg = pg_harness._alembic(URL)
    from alembic.script import ScriptDirectory

    scripts = ScriptDirectory.from_config(cfg)
    ours = [s for s in scripts.walk_revisions() if "decision" in getattr(s.module, "TABLES", ())]
    assert [(s.revision, s.down_revision) for s in ours] == [HAND_PAIR]
    files = sorted(p.name for p in VERSIONS.glob("[0-9][0-9][0-9][0-9]_*.py"))
    assert files[files.index(f"{HAND_PAIR[0]}.py") - 1] == f"{HAND_PAIR[1]}.py"
    assert len(scripts.get_heads()) == 1  # 6h: 0073 follows; one head, no longer this pair's
    with engine.connect() as c:
        for table in TABLES:
            found = {kind: set(c.execute(text(
                "SELECT conname FROM pg_constraint WHERE conrelid = CAST(:t AS regclass) AND contype = :k"),
                {"t": table, "k": kind}).scalars()) for kind in "cuf"}
            assert found == {"c": CHECKS[table], "u": UNIQUES[table], "f": FKS[table]}, table
            triggers = dict(c.execute(text(
                "SELECT tgname, tgfoid::regproc::text FROM pg_trigger WHERE tgrelid = CAST(:t AS regclass) "
                "AND NOT tgisinternal"), {"t": table}).all())
            expected = {f"{table}_immutable": "ledger_append_only", f"{table}_no_truncate": "ledger_append_only"}
            expected.update({"decision": {"decision_has_no_action": "decision_has_no_action"},
                             "option_evaluation_run": {"option_evaluation_run_complete": "run_covers_options"}}
                            .get(table, {}))
            assert triggers == expected, table
        deferred = dict(c.execute(text(
            "SELECT tgname, tgdeferrable AND tginitdeferred FROM pg_trigger WHERE tgname IN "
            "('decision_has_no_action', 'option_evaluation_run_complete')")).all())
        assert deferred == {"decision_has_no_action": True, "option_evaluation_run_complete": True}
        indexes = set(c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = ANY(:t)"),
                                {"t": list(TABLES)}).scalars())
        assert INDEXES <= indexes
        assert c.execute(text("SELECT count(*) FROM pg_constraint WHERE conname = 'agreed_action_tenant_id_unique' "
                              "AND conrelid = CAST('agreed_action' AS regclass) AND contype = 'u'")).scalar_one() == 1


# --- test 6b: every constraint on a hand row ------------------------------------------------------------------------

def _cases(w) -> list[tuple[str, list[tuple[str, dict]]]]:
    """(constraint name or message, rows inserted in one transaction). Each case breaks one rule."""
    d1, d2 = w["d1"], w["d2"]
    did, opt = d2["decision"]["id"], d2["options"]
    stop70 = d1["options"][2]["id"]
    zara, rand = w["zara"], uuid4

    def dec(name, **over):  # a fresh decision with its no-action option
        d = _decision(w, **{"period": "2026-12", **over})
        return (name, [("decision", d), ("decision_option", _option(w, d["id"], "no-action", 0))])

    def one(name, table, row):
        return (name, [(table, row)])

    def new_run(name, *rows):  # a fresh run on D1, then the rows under test (FK/unique fire before commit)
        run = _run(w, d1["decision"]["id"])
        return (name, [("option_evaluation_run", run)] + [(t, r(run["id"])) for t, r in rows])

    cases = [
        dec("decision_structure_key_check", structure_key="SOLAR"),
        dec("decision_lever_id_check", lever_id="Generator"),
        dec("decision_purpose_factor_id_check", purpose_factor_id="9candidate"),
        dec("decision_period_check", period="2026-13"),
        dec("decision_horizon_months_check", horizon_months=0),
        dec("decision_horizon_months_check", horizon_months=61),
        dec("decision_current_settings_check", current_settings=[]),
        dec("decision_rule_version_check", rule_version="decision-prepare-2"),
        dec("decision_prepared_role_check", prepared_role="OPERATOR_EXECUTIVE"),
        dec("decision_prepared_at_check", prepared_at=MICRO),
        dec("decision_tenant_id_fkey", tenant_id=rand()),
        dec("decision_tenant_id_site_id_fkey", site_id=rand()),
        dec("decision_tenant_id_site_id_finding_id_fkey", finding_id=rand()),
        dec("decision_tenant_id_prepared_by_person_id_fkey", prepared_by_person_id=zara),
        dec("decision_once", period="2026-10"),
        one("decision_option_option_key_check", "decision_option", _option(w, did, "Stop-1", 5)),
        one("decision_option_generator_check", "decision_option", _option(w, did, "stop-1", 5, generator="GRID")),
        one("decision_option_settings_check", "decision_option", _option(w, did, "stop-1", 5, settings=[])),
        one("decision_option_position_check", "decision_option", _option(w, did, "stop-1", -1)),
        one("decision_option_no_action_key", "decision_option",
            _option(w, did, "stop-1", 0, generator="NO_ACTION")),
        one("decision_option_no_action_key", "decision_option",
            _option(w, did, "no-action", 5, generator="SETTING_GRID")),
        one("decision_option_no_action_first", "decision_option", _option(w, did, "no-action", 5)),
        one("decision_option_no_action_first", "decision_option", _option(w, did, "stop-1", 0)),
        one("decision_option_key_unique", "decision_option", _option(w, did, "stop-90-reserve-25", 5)),
        one("decision_option_position_unique", "decision_option", _option(w, did, "stop-1", 1)),
        one("decision_option_tenant_id_decision_id_fkey", "decision_option", _option(w, rand(), "stop-1", 5)),
        one("decision_option_tenant_id_decision_id_fkey", "decision_option",
            _option(w, did, "stop-1", 5, tenant_id=w["other"])),
        one("option_one_off_amount_check", "option_one_off", _one_off(w, stop70, amount="-0.01")),
        one("option_one_off_currency_check", "option_one_off", _one_off(w, stop70, currency="usd")),
        one("option_one_off_crew_visits_check", "option_one_off", _one_off(w, stop70, crew_visits=-1)),
        one("option_one_off_basis_check", "option_one_off", _one_off(w, stop70, basis="")),
        one("option_one_off_basis_check", "option_one_off", _one_off(w, stop70, basis=" padded")),
        one("option_one_off_basis_check", "option_one_off", _one_off(w, stop70, basis="x" * 201)),
        one("option_one_off_declared_role_check", "option_one_off", _one_off(w, stop70, declared_role="ANALYST")),
        one("option_one_off_declared_at_check", "option_one_off", _one_off(w, stop70, declared_at=MICRO)),
        one("option_one_off_tenant_id_option_id_fkey", "option_one_off", _one_off(w, rand())),
        one("option_one_off_tenant_id_declared_by_person_id_fkey", "option_one_off",
            _one_off(w, stop70, declared_by_person_id=zara)),
        one("option_evaluation_run_evaluator_version_check", "option_evaluation_run",
            _run(w, did, evaluator_version="option-evaluator-x")),
        one("option_evaluation_run_outcome_check", "option_evaluation_run", _run(w, did, outcome="BEST")),
        one("option_evaluation_run_study_sha256_check", "option_evaluation_run", _run(w, did, study_sha256="A" * 64)),
        one("option_evaluation_run_study_identity_check", "option_evaluation_run", _run(w, did, study_identity=[])),
        one("option_evaluation_run_study_pair", "option_evaluation_run", _run(w, did, study_identity=None)),
        one("option_evaluation_run_study_pair", "option_evaluation_run", _run(w, did, study_sha256=None)),
        one("option_evaluation_run_known_at_check", "option_evaluation_run", _run(w, did, known_at=MICRO)),
        one("option_evaluation_run_run_role_check", "option_evaluation_run", _run(w, did, run_role="SITE_MANAGER")),
        one("option_evaluation_run_run_at_check", "option_evaluation_run", _run(w, did, run_at=MICRO)),
        one("option_evaluation_run_tenant_id_decision_id_fkey", "option_evaluation_run", _run(w, rand())),
        one("option_evaluation_run_tenant_id_run_by_person_id_fkey", "option_evaluation_run",
            _run(w, did, run_by_person_id=zara)),
    ]
    o = d1["options"]
    ev = "option_evaluation"
    for name, over in (
            ("option_evaluation_disposition_check", {"disposition": "BEST"}),
            ("option_evaluation_reason_code_check", {"reason_code": "too_low"}),
            ("option_evaluation_rank_check", {"rank": 0}),
            ("option_evaluation_currency_check", {"currency": "usd"}),
            ("option_evaluation_source_class_check", {"source_class": "GUESSED"}),
            ("option_evaluation_evidence_class_check", {"evidence_class": "GUESSED"}),
            ("option_evaluation_missing_check", {"missing": {}}),
            ("option_evaluation_assumed_check", {"assumed": {}}),
            ("option_evaluation_admission_check", {"admission": []}),
            ("option_evaluation_dawn_check", {"dawn": []}),
            ("option_evaluation_value_or_missing", {"value": None}),
            ("option_evaluation_value_or_missing", {"missing": [["READING", "telemetry", None]]}),
            ("option_evaluation_value_currency", {"currency": None}),
            ("option_evaluation_comparison", {"disposition": "COMPARISON", "value": "3"}),
            ("option_evaluation_comparison", {"disposition": "COMPARISON", "value": "0", "rank": 1}),
            ("option_evaluation_comparison",
             {"disposition": "COMPARISON", "value": "0", "one_off_id": d1["one_off"]["id"]}),
            ("option_evaluation_recommended_first", {"disposition": "RECOMMENDED", "rank": 2}),
            ("option_evaluation_tenant_id_option_id_fkey", {"option_id": rand()}),
            ("option_evaluation_tenant_id_one_off_id_fkey", {"one_off_id": rand()})):
        cases.append(new_run(name, (ev, lambda r, over=over: _evaluation(w, r, **{"option_id": o[1]["id"], **over}))))
    cases += [
        one("option_evaluation_once", ev, _evaluation(w, d1["run"]["id"], o[1]["id"])),
        one("option_evaluation_tenant_id_run_id_fkey", ev, _evaluation(w, rand(), o[1]["id"])),
        new_run("option_evaluation_one_recommended",
                (ev, lambda r: _evaluation(w, r, o[1]["id"], disposition="RECOMMENDED", rank=1)),
                (ev, lambda r: _evaluation(w, r, o[2]["id"], disposition="RECOMMENDED", rank=1))),
    ]
    eid = d1["evaluation"]["id"]
    cases += [
        one("option_effect_factor_id_check", "option_effect", _effect(w, eid, factor_id="Fuel")),
        one("option_effect_position_check", "option_effect", _effect(w, eid, factor_id="hours", position=-1)),
        one("option_effect_unit_check", "option_effect", _effect(w, eid, factor_id="hours", unit="")),
        one("option_effect_unit_check", "option_effect", _effect(w, eid, factor_id="hours", unit="u" * 33)),
        one("option_effect_currency_check", "option_effect", _effect(w, eid, factor_id="hours", currency="US")),
        one("option_effect_missing_check", "option_effect", _effect(w, eid, factor_id="hours", missing={})),
        one("option_effect_change_or_missing", "option_effect",
            _effect(w, eid, factor_id="hours", change_per_month=None)),
        one("option_effect_change_or_missing", "option_effect",
            _effect(w, eid, factor_id="hours", missing=[["READING", "telemetry", "hours"]])),
        one("option_effect_once", "option_effect", _effect(w, eid)),
        one("option_effect_tenant_id_evaluation_id_fkey", "option_effect", _effect(w, rand())),
    ]
    run2 = d2["run"]["id"]
    cases += [
        one("decision_choice_chosen_role_check", "decision_choice",
            _choice(w, did, run2, opt[1]["id"], chosen_role="ANALYST")),
        one("decision_choice_chosen_at_check", "decision_choice", _choice(w, did, run2, opt[1]["id"], chosen_at=MICRO)),
        one("decision_choice_once", "decision_choice",
            _choice(w, d1["decision"]["id"], d1["run"]["id"], d1["options"][1]["id"])),
        one("decision_choice_tenant_id_decision_id_fkey", "decision_choice", _choice(w, rand(), run2, opt[1]["id"])),
        one("decision_choice_tenant_id_option_id_fkey", "decision_choice", _choice(w, did, run2, rand())),
        one("decision_choice_tenant_id_run_id_fkey", "decision_choice", _choice(w, did, rand(), opt[1]["id"])),
        one("decision_choice_tenant_id_agreed_action_id_fkey", "decision_choice",
            _choice(w, did, run2, opt[1]["id"], agreed_action_id=rand())),
        one("decision_choice_tenant_id_chosen_by_person_id_fkey", "decision_choice",
            _choice(w, did, run2, opt[1]["id"], chosen_by_person_id=zara)),
    ]
    return cases


def test_6b_every_constraint_refuses_by_name(world, engine) -> None:  # noqa: F811
    before = _counts(engine)
    assert before == {"decision": 2, "decision_option": 6, "option_one_off": 2, "option_evaluation_run": 2,
                      "option_evaluation": 6, "option_effect": 2, "decision_choice": 1}
    cases = _cases(world)
    named = {name for name, _ in cases}
    every = set().union(*CHECKS.values(), *UNIQUES.values(), *FKS.values(), INDEXES)
    # The tenant-scoped uniques back the foreign keys; a duplicate id is refused by the primary key first. The
    # non-unique indexes order reads and refuse nothing.
    unreachable = {u for u in every if u.endswith("_tenant_id_unique")} | {
        "decision_tenant", "option_one_off_latest", "option_evaluation_run_latest"}
    assert every - unreachable <= named, sorted(every - unreachable - named)
    for name, rows in cases:
        _refused(engine, rows, rf'"{name}"')
    # Positive controls: a choice of none on D2 (null option) with no agreed Action is stored.
    with engine.begin() as c:
        _insert(c, "decision_choice", _choice(world, world["d2"]["decision"]["id"], world["d2"]["run"]["id"], None))
    assert _counts(engine) == {**before, "decision_choice": 2}


# --- test 6c: the deferred triggers ---------------------------------------------------------------------------------

def test_6c_no_action_and_complete_run_are_enforced_at_commit(world, engine) -> None:  # noqa: F811
    w = world
    before = _counts(engine)
    alone = _decision(w, period="2027-01")
    _refused(engine, [("decision", alone)], NO_ACTION)
    grid_only = _decision(w, period="2027-01")
    _refused(engine, [("decision", grid_only), ("decision_option", _option(w, grid_only["id"], "stop-1", 1))],
             NO_ACTION)
    d1 = w["d1"]
    options = d1["options"]
    short = _full_run(w, d1["decision"]["id"], options)[:-1]
    _refused(engine, short, "evaluates 2 of 3 options")
    _refused(engine, [("option_evaluation_run", _run(w, d1["decision"]["id"]))], "evaluates 0 of 3 options")
    assert _counts(engine) == before
    with engine.begin() as c:  # SQLSTATE 23514 (check_violation) for both
        for rows in ([("decision", _decision(w, period="2027-02"))],
                     [("option_evaluation_run", _run(w, d1["decision"]["id"]))]):
            c.execute(text("SAVEPOINT s"))
            for table, row in rows:
                _insert(c, table, row)
            with pytest.raises(Exception) as caught:
                c.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            assert caught.value.orig.sqlstate == "23514"  # psycopg 3
            c.execute(text("ROLLBACK TO SAVEPOINT s"))
    good = _decision(w, period="2027-03")
    with engine.begin() as c:
        _insert(c, "decision", good)
        _insert(c, "decision_option", _option(w, good["id"], "no-action", 0))
        for table, row in _full_run(w, d1["decision"]["id"], options):
            _insert(c, table, row)
    assert _counts(engine)["decision"] == before["decision"] + 1


# --- test 6d: append-only, the downgrade, one head ------------------------------------------------------------------

def test_6d_append_only_downgrade_and_one_head(world, engine) -> None:  # noqa: F811
    from alembic import command

    before = _counts(engine)
    for table in TABLES:
        with pytest.raises(Exception, match=f"{table} rows are append-only"):
            with engine.begin() as c:
                c.execute(text(f"UPDATE {table} SET id = id"))
        with pytest.raises(Exception, match=f"{table} rows are append-only"):
            with engine.begin() as c:
                c.execute(text(f"DELETE FROM {table}"))
        # CASCADE takes the referencing tables along; the statement trigger of the named table refuses first.
        with pytest.raises(Exception, match=f"{table} rows are append-only"):
            with engine.begin() as c:
                c.execute(text(f"TRUNCATE {table} CASCADE"))
    assert _counts(engine) == before
    cfg = pg_harness._alembic(URL)
    with pytest.raises(Exception, match="Downgrade of 0072_decision_records refused: decision rows exist"):
        command.downgrade(cfg, HAND_PAIR[1])
    with engine.begin() as c:  # the test empties the tables the only way the triggers allow
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for table in reversed(TABLES):
            c.execute(text(f"DELETE FROM {table}"))
    command.downgrade(cfg, HAND_PAIR[1])
    with engine.connect() as c:
        for table in TABLES:
            assert c.execute(text("SELECT to_regclass(:t)"), {"t": table}).scalar_one() is None
        assert c.execute(text("SELECT count(*) FROM pg_proc WHERE proname IN "
                              "('decision_has_no_action', 'run_covers_options')")).scalar_one() == 0
        assert c.execute(text("SELECT count(*) FROM pg_proc WHERE proname = 'ledger_append_only'")).scalar_one() == 1
        assert c.execute(text("SELECT count(*) FROM pg_constraint WHERE conname = 'agreed_action_tenant_id_unique'")
                         ).scalar_one() == 0
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)
    assert len(pg_harness._heads()) == 1  # 6h: 0073 follows; one head, no longer this pair's
