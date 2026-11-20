"""ON1 (spec §6 "Postgres"; D-ON1.1, D-ON1.5, D-ON1.15): onboarding the Lakeside rehearsal tenant into a routed
`*_test` database through the command's composition, then serving it and loading its emulated exports.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. No test here names or creates an `assetops_op*` database.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.engine import make_url
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend import load_emulated_exports as loader
    from assetops_backend import onboard_operator as command
    from assetops_backend.accounts.adapters.postgres_account_store import PostgresAccountStore
    from assetops_backend.accounts.model import GrantRow, PersonPrincipal
    from assetops_backend.accounts.service import AccountService
    from assetops_backend.accounts.store import StoreConflict
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.database_target import PG_TARGET_ENV
    from test_3a3_load_emulated import KEYS, generated  # noqa: F401 - module fixture
    from test_on1_operator_file import DIGEST, FIXTURE

SLUG = "lakeside-power"
EXEC, FIN, ANALYST = "OPERATOR_EXECUTIVE", "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST"
NOW = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)
COUNTED = ("tenant", "site", "site_import", "operator_account", "role_grant")


def test_url_is_a_test_database() -> None:
    name = make_url(URL).database
    assert name.endswith("_test") and not name.lower().startswith("assetops_op")


@pytest.fixture()
def onboarded(store, engine, tmp_path, monkeypatch, capsys):  # noqa: F811 - `store` empties the tenant closure
    keys = tmp_path / "keys"
    keys.mkdir(mode=0o700)
    os.chmod(keys, 0o700)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", SLUG)
    monkeypatch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", str(keys))
    code = command.main(["apply", "--file", str(FIXTURE), "--confirmed-digest", DIGEST])
    out, err = capsys.readouterr()
    assert code == 0, err
    return {"plan": json.loads(out), "keys": keys}


def _counts(engine) -> dict[str, int]:
    with engine.connect() as c:
        return {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in COUNTED}


def test_p1_apply_creates_the_tenant_and_the_app_serves_it(onboarded, engine) -> None:  # noqa: F811
    with engine.connect() as c:
        tenant = c.execute(text("SELECT id, name FROM tenant WHERE slug = :s"), {"s": SLUG}).one()
        sites = c.execute(text("SELECT s.site_code, i.source_path FROM site s JOIN site_import i ON i.site_id = s.id "
                               "WHERE s.tenant_id = :t ORDER BY s.site_code"), {"t": tenant.id}).all()
        accounts = c.execute(text("SELECT count(*) FROM operator_account WHERE tenant_id = :t"),
                             {"t": tenant.id}).scalar()
        grants = c.execute(text("SELECT by_service, by_person_id FROM role_grant WHERE tenant_id = :t"),
                           {"t": tenant.id}).all()
    assert tenant.name == "Lakeside Power" and onboarded["plan"]["tenant"]["id"] == str(tenant.id)
    assert [tuple(s) for s in sites] == [(c, f"onboarding:{SLUG}/{c}") for c in ("KISIWA-001", "KOBO-001", "MTO-001")]
    assert accounts == 7
    assert len(grants) == 7 and all(g.by_service == "service:onboarding" and g.by_person_id is None for g in grants)
    assert (onboarded["keys"] / f"{tenant.id}.key").stat().st_size == 32
    from assetops_backend.main import create_app

    app = create_app()
    registry = app.state.site_registry
    assert registry.served_tenant_slug == SLUG
    scope = registry.ledger_scope("KOBO-001")
    assert scope is not None and scope[0] == "KOBO-001" and scope[1] == tenant.id


def test_p2_a_second_apply_writes_no_row(onboarded, engine, capsys) -> None:  # noqa: F811
    before = _counts(engine)
    assert command.main(["apply", "--file", str(FIXTURE), "--confirmed-digest", DIGEST]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["tenant"]["action"] == "keep" and {r["action"] for r in plan["roles"]} == {"keep"}
    assert _counts(engine) == before


def _row(accounts: AccountService, email: str, role: str) -> GrantRow:
    person = accounts.onboard_person(email)
    row_id = uuid4()
    return GrantRow(row_id, row_id, person.tenant_id, person.person_id, "x", role, None, None, "GRANTED", None, None,
                    "service:onboarding", NOW)


def test_p3_under_the_lock(onboarded, engine) -> None:  # noqa: F811
    pg = PostgresAccountStore(URL)
    try:
        accounts = AccountService(pg, clock=lambda: NOW)
        # two concurrent grants of the same (person, role): one recorded, the other ROLE_ALREADY_HELD
        rows = [_row(accounts, "musa@lakeside-power.example", "SITE_MANAGER") for _ in range(2)]
        site = accounts.onboard_person("musa@lakeside-power.example")
        with engine.connect() as c:
            kobo = c.execute(text("SELECT id FROM site WHERE tenant_id = :t AND site_code = 'KOBO-001'"),
                             {"t": site.tenant_id}).scalar()
        rows = [GrantRow(r.row_id, r.grant_id, r.tenant_id, r.person_id, r.display_name, r.role, kobo, "KOBO-001",
                         r.action, None, None, r.by_service, r.at) for r in rows]
        barrier, outcomes = threading.Barrier(2), []

        def grant(row):
            barrier.wait()
            try:
                pg.add_onboarding_grant(row)
                outcomes.append("ok")
            except StoreConflict as conflict:
                outcomes.append(conflict.code)

        threads = [threading.Thread(target=grant, args=(r,)) for r in rows]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert sorted(outcomes) == ["ROLE_ALREADY_HELD", "ok"]
        # the file rule bypassed: the adapter still refuses one person submitting and accepting
        for email, role in (("wanjiru@lakeside-power.example", FIN), ("joseph@lakeside-power.example", ANALYST),
                            ("amina@lakeside-power.example", ANALYST)):
            with pytest.raises(StoreConflict) as caught:
                pg.add_onboarding_grant(_row(accounts, email, role))
            assert caught.value.code == "ROLES_SEPARATE"
        # a person-made grant closes onboarding grants
        amina = accounts.onboard_person("amina@lakeside-power.example")
        boss = PersonPrincipal(amina.person_id, amina.tenant_id, "Amina", frozenset({(EXEC, None)}), uuid4(), NOW, NOW)
        musa = accounts.onboard_person("musa@lakeside-power.example")
        accounts.grant(boss, musa.person_id, ANALYST, None)
        assert accounts.onboarding_may_grant(SLUG) is False and accounts.executive_of(SLUG) == amina.person_id
        with pytest.raises(StoreConflict) as caught:
            pg.add_onboarding_grant(_row(accounts, "david@lakeside-power.example", "FIELD_TECHNICIAN"))
        assert caught.value.code == "ONBOARDING_CLOSED"
    finally:
        pg.dispose()


def test_p4_the_emulated_exports_load_wanjiru_submitting_and_joseph_accepting(onboarded, generated,
                                                                            capsys) -> None:  # noqa: F811
    code = loader.main(["--dir", str(generated / "exports"), "--tenant", SLUG,
                        "--submit-as", "wanjiru@lakeside-power.example", "--accept-as", "joseph@lakeside-power.example"])
    out, err = capsys.readouterr()
    assert code == 0, err
    lines = [json.loads(line) for line in out.splitlines()]
    assert [(l["file"], l["state"]) for l in lines] == [(f"{SLUG}.{k}.csv", "ACCEPTED") for k in KEYS]
    commercial = PostgresCommercialStore(URL)
    try:
        tid = AccountService(PostgresAccountStore(URL), clock=lambda: NOW).onboard_person(
            "joseph@lakeside-power.example").tenant_id
        held = commercial.held_uploads(tid)
        assert len(held) == 4 and not any(h.waiting for h in held)
    finally:
        commercial.dispose()
