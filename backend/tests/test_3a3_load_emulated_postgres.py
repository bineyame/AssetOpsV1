"""3A3 P1 to P3 (spec `specs/3A3-emulators-contract-test/spec.md` §2.6 to §2.8, §5 "Postgres"): the loader on its
composition path, `AccountService.onboard_person` and `CommercialStore.held_uploads` over Postgres.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. No test here names or creates an `assetops_op*` database.
"""
from __future__ import annotations

import json
import os
from datetime import timedelta
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy.engine import make_url
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend import load_emulated_exports as loader
    from assetops_backend.accounts.adapters.postgres_account_store import PostgresAccountStore
    from assetops_backend.accounts.service import AccountService
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.composition import create_key_file
    from assetops_backend.commercial.uploads import Actor, UploadScope
    from assetops_backend.database_target import PG_TARGET_ENV
    from test_3a1_commercial_postgres import Seeder
    from test_3a1_commercial_service import Clock
    from test_3a2_commercial_upload_service import KISIWA, KOBO, T_SUBMIT
    from test_3a3_load_emulated import KEYS, emulated, write_files  # noqa: F401 - the module-scoped fixture

PW = "correct horse battery"
FIN, ANALYST = "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST"


def test_url_is_a_test_database() -> None:
    name = make_url(URL).database
    assert name.endswith("_test") and not name.lower().startswith("assetops_op")


@pytest.fixture()
def acme(store, engine, tmp_path, monkeypatch):  # noqa: F811 - `store` empties the tenant closure
    seeder = Seeder(engine)
    tid = seeder.add_tenant("acme")
    seeder.add_site(tid, KOBO)
    seeder.add_site(tid, KISIWA)
    clock = Clock(T_SUBMIT)
    accounts = AccountService(PostgresAccountStore(URL), clock=clock)
    accounts.onboard_create("acme", "amina@acme.example", "Amina", PW, executive=True)
    boss = accounts.sign_in("amina@acme.example", PW).principal
    ids = {}
    for name, role in (("ana", ANALYST), ("fiona", FIN)):
        ids[name] = accounts.onboard_create("acme", f"{name}@acme.example", name.title(), PW, executive=False)
        accounts.grant(boss, ids[name], role, None)
    keys = tmp_path / "keys"
    keys.mkdir()
    create_key_file(keys, tid)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", str(keys))
    commercial = PostgresCommercialStore(URL)
    yield dict(tid=tid, accounts=accounts, ids=ids, commercial=commercial, clock=clock)
    commercial.dispose()


def _load(directory, capsys, accept: str | None = "fiona@acme.example") -> tuple[int, list[dict], str]:
    argv = ["--dir", str(directory), "--tenant", "acme", "--submit-as", "ana@acme.example"]
    if accept is not None:
        argv += ["--accept-as", accept]
    code = loader.main(argv)
    out, err = capsys.readouterr()
    return code, [json.loads(line) for line in out.splitlines()], err


def test_p1_load_through_the_composition_and_rerun(acme, tmp_path, emulated, capsys) -> None:  # noqa: F811
    directory = write_files(tmp_path / "x", emulated)
    code, lines, err = _load(directory, capsys)
    assert code == 0, err
    assert [(l["file"], l["state"], l["decided_by_script"]) for l in lines] == [
        (f"acme.{k}.csv", "ACCEPTED", True) for k in KEYS]
    store = acme["commercial"]
    held = store.held_uploads(acme["tid"])
    assert len(held) == 4 and not any(h.waiting for h in held)
    rows = sum(len(emulated[k]) for k in KEYS)
    assert len(store.latest_revisions(acme["tid"])) == rows
    code, lines, _ = _load(directory, capsys)
    assert code == 0 and [l["state"] for l in lines] == ["NOTHING_NEW"] * 4
    assert len(store.held_uploads(acme["tid"])) == 4 and len(store.latest_revisions(acme["tid"])) == rows


def test_p2_onboard_person_round_trips(acme) -> None:
    fiona = acme["accounts"].onboard_person("Fiona@ACME.example")
    assert (fiona.person_id, fiona.tenant_id, fiona.tenant_slug, fiona.display_name, fiona.active) == (
        acme["ids"]["fiona"], acme["tid"], "acme", "Fiona", True)
    assert fiona.roles == frozenset({(FIN, None)})
    assert acme["accounts"].onboard_person("nobody@acme.example") is None
    assert acme["accounts"].onboard_person("not an email") is None
    acme["clock"].now = T_SUBMIT + timedelta(minutes=1)  # a later status row
    acme["accounts"].onboard_set_status("ana@acme.example", "DISABLED", "Left.")
    assert acme["accounts"].onboard_person("ana@acme.example").active is False


def test_p3_held_uploads(acme, tmp_path, emulated, capsys) -> None:  # noqa: F811
    directory = write_files(tmp_path / "x", emulated)
    assert _load(directory, capsys)[0] == 0
    store = acme["commercial"]
    assert [h.waiting for h in store.held_uploads(acme["tid"])] == [False] * 4
    uploads = loader.build_commercial_uploads(URL, loader.commercial_upload_settings(URL))
    ana = Actor(acme["ids"]["ana"], ANALYST)
    fiona = Actor(acme["ids"]["fiona"], FIN)
    org = UploadScope(None, None)
    budget = (directory / "acme.budget.csv").read_bytes()
    one = budget.replace(b"gen:KOBO-001:2026-10:plan:revenue,1,", b"gen:KOBO-001:2026-10:plan:revenue,2,")
    two = budget.replace(b"gen:KOBO-001:2026-10:plan:fuel_cost,1,", b"gen:KOBO-001:2026-10:plan:fuel_cost,2,")
    assert one != budget and two != budget
    kept = uploads.submit(acme["tid"], org, ana, one, file_name="acme.budget.csv",
                          reader_id="budget-illustrative-1", media_type="text/csv")
    declined = uploads.submit(acme["tid"], org, ana, two, file_name="acme.budget.csv",
                              reader_id="budget-illustrative-1", media_type="text/csv")
    uploads.decide(acme["tid"], org, fiona, declined["upload_id"], "DECLINE", "Not this one.")
    held = store.held_uploads(acme["tid"])
    assert len(held) == 5 and [h.upload_id for h in held if h.waiting] == [UUID(kept["upload_id"])]
    assert UUID(declined["upload_id"]) not in {h.upload_id for h in held}
    assert {h.reader for h in held} == {f"{k}-illustrative-1" for k in KEYS}
    assert [h.upload_id for h in held] == sorted(h.upload_id for h in held)
