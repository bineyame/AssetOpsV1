"""ON1 (spec §3.1, §3.3, §5, §6 "Service, no database"; D-ON1.1, D-ON1.6, D-ON1.10, D-ON1.12, D-ON1.15): onboarding
an operator over in-memory ports.

The world: `InMemoryFoundationStore` (counting its writes), the 3C0a `MemoryStore` reading tenants and Sites from it
(counting its writes), an in-memory `KeyFiles`. No test here can connect to a database: the autouse no-connect fixture
makes every connection attempt raise (D-ON1.12), and every URL naming a database uses host `rc4.invalid` port 1.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
import sqlalchemy.engine
from sqlalchemy import create_engine

from assetops_backend import onboard_operator as command
from assetops_backend.accounts.model import AccountRefused, ONBOARDING, PersonPrincipal
from assetops_backend.accounts.service import AccountService
from assetops_backend.database_target import PG_TARGET_ENV
from assetops_backend.onboarding.operator_file import OnboardRefused, parse_operator_file, roles_digest
from assetops_backend.onboarding.service import OperatorOnboarding
from foundation_fakes import InMemoryFoundationStore
from test_3c0a_accounts_service import MemoryStore
from test_on1_operator_file import DIGEST, FIXTURE

NOW = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)
SLUG = "lakeside-power"
EXEC, FIN, ANALYST = "OPERATOR_EXECUTIVE", "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST"


def _no_connect(*_a, **_k):
    raise AssertionError("connection attempted")


@pytest.fixture(autouse=True)
def no_connect(monkeypatch):
    monkeypatch.setattr(psycopg, "connect", _no_connect)
    monkeypatch.setattr(psycopg.Connection, "connect", classmethod(_no_connect))
    monkeypatch.setattr(sqlalchemy.engine.Engine, "connect", _no_connect)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    for variable in ("DATABASE_URL", "ASSETOPS_REAL_OPERATOR_DATA", "ASSETOPS_TENANT_SLUG",
                     "ASSETOPS_PSEUDONYM_KEY_DIR"):
        monkeypatch.delenv(variable, raising=False)


def test_no_connect_fixture_holds() -> None:
    with pytest.raises(AssertionError, match="^connection attempted$"):
        create_engine("postgresql+psycopg://u:p@rc4.invalid:1/x").connect()
    with pytest.raises(AssertionError, match="^connection attempted$"):
        psycopg.connect("host=rc4.invalid port=1 dbname=x")


# --- the in-memory world ---------------------------------------------------------------------------------------------

class Foundation(InMemoryFoundationStore):
    def __init__(self) -> None:
        super().__init__()
        self.writes = 0

    def ensure_tenant(self, slug, name, *, now):
        self.writes += 1
        return super().ensure_tenant(slug, name, now=now)

    def insert_import(self, tenant_id, plan):
        self.writes += 1
        return super().insert_import(tenant_id, plan)


class Accounts(MemoryStore):
    """3C0a's store, its tenants and Sites read from the Foundation fake; writes counted; `fail_on_create` makes the
    n-th `create_account` raise (service 5)."""

    def __init__(self, foundation: Foundation) -> None:
        super().__init__()
        self.foundation = foundation
        self.writes = 0
        self.creates = 0
        self.fail_on_create: int | None = None

    def tenant_by_slug(self, slug):
        t = self.foundation.tenants.get(slug)
        return None if t is None else (t.id, t.name)

    def tenant(self, tenant_id):
        t = next((t for t in self.foundation.tenants.values() if t.id == tenant_id), None)
        return None if t is None else (t.slug, t.name)

    def tenant_slug(self, tenant_id):
        found = self.tenant(tenant_id)
        return None if found is None else found[0]

    def site_id(self, tenant_id, site_code):
        site = self.foundation.find_site(tenant_id, site_code)
        return None if site is None else site.id

    def _site_code(self, site_id):
        return next((s.site_code for s in self.foundation.sites if s.id == site_id), None)

    def create_account(self, *args, **kwargs):
        self.creates += 1
        if self.fail_on_create == self.creates:
            raise RuntimeError("the store fell over")
        self.writes += 1
        return super().create_account(*args, **kwargs)

    def add_grant(self, *args, **kwargs):
        self.writes += 1
        return super().add_grant(*args, **kwargs)

    def add_onboarding_grant(self, row):
        self.writes += 1
        return super().add_onboarding_grant(row)


class Keys:
    def __init__(self) -> None:
        self.ok = True
        self.states: dict[UUID, str] = {}
        self.writes = 0

    def directory_ok(self) -> bool:
        return self.ok

    def state(self, tenant_id: UUID) -> str:
        return self.states.get(tenant_id, "MISSING")

    def create(self, tenant_id: UUID) -> None:
        assert self.state(tenant_id) == "MISSING"
        self.writes += 1
        self.states[tenant_id] = "PRESENT"


class World:
    def __init__(self, *, real_data: bool = False, served: str = SLUG) -> None:
        self.foundation = Foundation()
        self.store = Accounts(self.foundation)
        self.accounts = AccountService(self.store, clock=lambda: NOW)
        self.keys = Keys()
        self.svc = OperatorOnboarding(self.foundation, self.accounts, self.keys, clock=lambda: NOW,
                                      real_data=real_data, served_slug=served)

    def writes(self) -> int:
        return self.foundation.writes + self.store.writes + self.keys.writes

    def tenant_id(self) -> UUID:
        return self.foundation.tenants[SLUG].id

    def person(self, name: str):
        return self.accounts.onboard_person(f"{name.lower()}@lakeside-power.example")

    def roles_of(self, name: str) -> set[str]:
        return {role for role, _ in self.person(name).roles}


def raw() -> dict:
    return json.loads(FIXTURE.read_bytes())


def file(doc: dict | None = None):
    return parse_operator_file(json.dumps(raw() if doc is None else doc).encode("utf-8"))


def refused(call, code: str, where: str | None = None) -> OnboardRefused:
    with pytest.raises(OnboardRefused) as caught:
        call()
    assert (caught.value.code, caught.value.where) == (code, where)
    return caught.value


@pytest.fixture()
def applied() -> World:
    w = World()
    w.svc.apply(file(), confirmed_digest=DIGEST)
    return w


# --- 1, 2: check then apply ------------------------------------------------------------------------------------------

def test_1_check_on_an_empty_world() -> None:
    w = World()
    plan = w.svc.check(file()).as_json()
    assert plan["tenant"] == {"slug": SLUG, "id": None, "action": "create"}
    assert [(s["code"], s["action"]) for s in plan["sites"]] == [
        ("KISIWA-001", "create"), ("KOBO-001", "create"), ("MTO-001", "create")]
    assert [p["action"] for p in plan["people"]] == ["create"] * 7
    assert plan["key"] == "create"
    assert [(r["index"], r["role"], r["site"], r["action"]) for r in plan["roles"]] == [
        (1, FIN, None, "grant"), (2, ANALYST, None, "grant"), (3, "SITE_MANAGER", "KOBO-001", "grant"),
        (4, "SITE_MANAGER", "KISIWA-001", "grant"), (5, "SITE_MANAGER", "MTO-001", "grant"),
        (6, "FIELD_TECHNICIAN", None, "grant")]
    assert plan["roles_digest"] == DIGEST
    assert w.writes() == 0


def test_2_apply_creates_everything_by_service_onboarding(applied: World) -> None:
    w = applied
    tenant = w.foundation.tenants[SLUG]
    assert tenant.name == "Lakeside Power"
    sites = w.foundation.list_sites(tenant.id)
    assert [(s.site_code, s.import_record.source_path) for s in sites] == [
        (code, f"onboarding:{SLUG}/{code}") for code in ("KISIWA-001", "KOBO-001", "MTO-001")]
    assert len([a for a in w.store.accounts.values() if a.tenant_id == tenant.id]) == 7
    grants = [g for g in w.store.grants if g.tenant_id == tenant.id]
    assert len(grants) == 7
    assert all(g.by_service == ONBOARDING and g.by_person_id is None for g in grants)
    assert w.roles_of("Amina") == {EXEC}
    assert w.keys.states == {tenant.id: "PRESENT"}


def test_2_the_printed_plan_holds_no_email_name_or_password(capsys) -> None:
    w = World()
    plan = w.svc.apply(file(), confirmed_digest=DIGEST)
    text = json.dumps(plan.as_json())
    assert "@" not in text and "Amina" not in text and "Joseph" not in text
    assert plan.as_json()["tenant"]["id"] == str(w.tenant_id())
    code = command.main(["apply", "--file", str(FIXTURE), "--key-dir", "/k", "--confirmed-digest", DIGEST],
                        onboarding=w.svc)
    out, err = capsys.readouterr()
    assert code == 0 and err == ""
    assert "@" not in out and "Amina" not in out and json.loads(out)["key"] == "keep"


# --- 3: real data waits for ON1b -------------------------------------------------------------------------------------

def test_3_a_real_file_is_refused_before_any_write() -> None:
    doc = raw()
    doc["data"] = "real"
    w = World(real_data=True, served=SLUG)
    refused(lambda: w.svc.check(file(doc)), "ONBOARD_REAL_AWAITS_APPROVAL", "data")
    refused(lambda: w.svc.apply(file(doc), confirmed_digest=DIGEST), "ONBOARD_REAL_AWAITS_APPROVAL", "data")
    assert w.writes() == 0 and w.foundation.tenants == {} and w.store.accounts == {} and w.store.grants == []


def test_3_no_person_holds_both_a_submitting_and_an_accepting_role(applied: World) -> None:
    w = applied
    assert ANALYST in w.roles_of("Wanjiru") and FIN in w.roles_of("Joseph")
    for name in ("Amina", "Joseph", "Wanjiru", "Peter", "Halima", "David", "Musa"):
        roles = w.roles_of(name)
        assert not (ANALYST in roles and roles & {FIN, EXEC}), name


# --- 4, 5: re-runs converge ------------------------------------------------------------------------------------------

def test_4_a_second_apply_keeps_everything_and_writes_nothing(applied: World) -> None:
    w = applied
    before = w.writes()
    plan = w.svc.apply(file(), confirmed_digest=DIGEST).as_json()
    assert plan["tenant"]["action"] == "keep" and plan["key"] == "keep"
    assert {s["action"] for s in plan["sites"]} == {p["action"] for p in plan["people"]} == {"keep"}
    assert {r["action"] for r in plan["roles"]} == {"keep"}
    assert w.writes() == before


def _state(w: World):
    tid = w.tenant_id()
    return (sorted(s.site_code for s in w.foundation.list_sites(tid)),
            sorted((a.email, a.display_name) for a in w.store.accounts.values() if a.tenant_id == tid),
            sorted((w.store.accounts[g.person_id].email, g.role, g.site_code, g.by_service, g.by_person_id)
                   for g in w.store._held(tid)),
            w.keys.states.get(tid))


def test_5_a_partial_run_completes_on_the_rerun(applied: World) -> None:
    w = World()
    w.store.fail_on_create = 4
    with pytest.raises(RuntimeError):
        w.svc.apply(file(), confirmed_digest=DIGEST)
    assert w.svc.wrote and len(w.store.accounts) == 3
    w.store.fail_on_create = None
    plan = w.svc.apply(file(), confirmed_digest=DIGEST).as_json()
    assert [p["action"] for p in plan["people"]] == ["keep"] * 3 + ["create"] * 4
    assert _state(w) == _state(applied)


# --- 6: changes are refused ------------------------------------------------------------------------------------------

def test_6_changes_are_refused_not_applied(applied: World) -> None:
    w = applied
    before = w.writes()
    doc = raw()
    doc["sites"][1]["name"] = "Kobo mini-grid II"
    refused(lambda: w.svc.check(file(doc)), "ONBOARD_SITE_CHANGED", "sites[1]")
    doc = raw()
    doc["operator"]["name"] = "Lakeside Energy"
    refused(lambda: w.svc.check(file(doc)), "ONBOARD_TENANT_DIFFERS", "operator.name")
    doc = raw()
    doc["people"][1]["name"] = "Joe"
    refused(lambda: w.svc.check(file(doc)), "ONBOARD_PERSON_DIFFERS", "people[1]")
    acme = w.foundation.ensure_tenant("acme", "Acme Power", now=NOW)
    w.accounts.onboard_create("acme", "zawadi@acme.example", "Zawadi", "correct horse battery", executive=True)
    doc = raw()
    doc["people"][6]["email"] = "zawadi@acme.example"
    refused(lambda: w.svc.check(file(doc)), "ONBOARD_EMAIL_TAKEN", "people[6]")
    doc = raw()
    doc["people"][0]["roles"] = [{"role": "FIELD_TECHNICIAN"}]
    doc["people"][6]["roles"] = [{"role": EXEC}]
    refused(lambda: w.svc.check(file(doc)), "ONBOARD_EXECUTIVE_DIFFERS", "people[6]")
    refused(lambda: w.svc.apply(file(doc), confirmed_digest=roles_digest(file(doc))), "ONBOARD_EXECUTIVE_DIFFERS",
            "people[6]")
    off = DIGEST[:-1] + ("0" if DIGEST[-1] != "0" else "1")
    refused(lambda: w.svc.apply(file(), confirmed_digest=off), "ONBOARD_DIGEST_DIFFERS")
    assert w.writes() == before + 2 and acme.slug == "acme"  # the two writes are this test's own acme set-up


def test_6_a_changed_site_is_refused_by_apply_too(applied: World) -> None:
    w = applied
    before = w.writes()
    doc = raw()
    doc["sites"][1]["name"] = "Kobo mini-grid II"
    refused(lambda: w.svc.apply(file(doc), confirmed_digest=DIGEST), "ONBOARD_SITE_CHANGED", "sites[1]")
    assert w.writes() == before
    assert w.foundation.find_site(w.tenant_id(), "KOBO-001").name == "Kobo mini-grid"


# --- 7: onboarding closes once a person grants -----------------------------------------------------------------------

def test_7_onboarding_closes_after_a_person_made_grant(applied: World) -> None:
    w = applied
    amina, musa = w.person("Amina"), w.person("Musa")
    boss = PersonPrincipal(amina.person_id, amina.tenant_id, "Amina", frozenset({(EXEC, None)}), uuid4(), NOW, NOW)
    w.accounts.grant(boss, musa.person_id, ANALYST, None)
    assert w.accounts.onboarding_open(SLUG) is False
    before = w.writes()
    doc = raw()
    doc["people"][3]["roles"].append({"role": "FIELD_TECHNICIAN"})
    refused(lambda: w.svc.check(file(doc)), "ONBOARDING_CLOSED", "people[3]")
    refused(lambda: w.svc.apply(file(doc), confirmed_digest=roles_digest(file(doc))), "ONBOARDING_CLOSED",
            "people[3]")
    assert w.writes() == before
    plan = w.svc.apply(file(), confirmed_digest=DIGEST).as_json()
    assert {r["action"] for r in plan["roles"]} == {"keep"} and w.writes() == before


# --- 8: RC4, by names only -------------------------------------------------------------------------------------------

def test_8_rc4_matrix() -> None:
    doc = raw()
    doc["data"] = "real"
    refused(lambda: World(real_data=False).svc.check(file(doc)), "ONBOARD_DATA_MISMATCH", "data")
    refused(lambda: World(real_data=True).svc.check(file()), "ONBOARD_DATA_MISMATCH", "data")
    refused(lambda: World(served="demo").svc.check(file()), "ONBOARD_TENANT_NOT_SERVED", "operator.slug")
    w = World(real_data=True)
    w.foundation.ensure_tenant("acme", "Acme Power", now=NOW)
    refused(lambda: w.svc.check(file(doc)), "ONBOARD_DATABASE_NOT_EMPTY")
    w = World(real_data=True)
    refused(lambda: w.svc.check(file(doc)), "ONBOARD_REAL_AWAITS_APPROVAL", "data")
    w.foundation.ensure_tenant(SLUG, "Lakeside Power", now=NOW)  # the operator's own tenant only: still the same
    refused(lambda: w.svc.apply(file(doc), confirmed_digest=DIGEST), "ONBOARD_REAL_AWAITS_APPROVAL", "data")
    assert w.store.writes == w.keys.writes == 0


@pytest.mark.parametrize("url", [
    "postgresql+psycopg://u:p@rc4.invalid:1/assetops_test?dbname=assetops_op_x",
    "postgresql+psycopg://u:p@rc4.invalid:1/",
])
@pytest.mark.parametrize("verb", ["check", "apply"])
def test_8_the_command_refuses_an_unclear_database_before_connecting(monkeypatch, capsys, url, verb) -> None:
    monkeypatch.setenv("DATABASE_URL", url)
    argv = [verb, "--file", str(FIXTURE), "--key-dir", "/k"] + (["--confirmed-digest", DIGEST] if verb == "apply"
                                                                 else [])
    assert command.main(argv) == 2
    out, err = capsys.readouterr()
    assert out == "" and err.startswith("CONFIGURATION ")


def test_8_the_command_needs_a_database_url_and_a_key_directory(capsys) -> None:
    assert command.main(["check", "--file", str(FIXTURE)]) == 2
    assert capsys.readouterr().err.startswith("ONBOARD_KEY_DIR_REQUIRED ")
    assert command.main(["check", "--file", str(FIXTURE), "--key-dir", "/k"]) == 2
    assert capsys.readouterr().err.startswith("DATABASE_URL_REQUIRED ")


def test_8_an_operator_database_with_emulated_data_or_the_demo_tenant_is_refused(monkeypatch, capsys) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@rc4.invalid:1/assetops_op_pilot1")
    assert command.main(["check", "--file", str(FIXTURE), "--key-dir", "/k"]) == 2
    assert capsys.readouterr().err.startswith("CONFIGURATION ")  # switch off on an operator database
    monkeypatch.setenv("ASSETOPS_REAL_OPERATOR_DATA", "on")
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "Lakeside")
    assert command.main(["check", "--file", str(FIXTURE), "--key-dir", "/k"]) == 2
    assert capsys.readouterr().err == "CONFIGURATION ASSETOPS_TENANT_SLUG must be a tenant slug.\n"


# --- 9: the key ------------------------------------------------------------------------------------------------------

def test_9_an_erased_key_and_a_bad_directory_are_refused_before_any_write(applied: World) -> None:
    w = applied
    before = w.writes()
    w.keys.states[w.tenant_id()] = "ERASED"
    refused(lambda: w.svc.check(file()), "ONBOARD_KEY_ERASED")
    refused(lambda: w.svc.apply(file(), confirmed_digest=DIGEST), "ONBOARD_KEY_ERASED")
    w = World()
    w.keys.ok = False
    refused(lambda: w.svc.check(file()), "ONBOARD_KEY_DIR")
    refused(lambda: w.svc.apply(file(), confirmed_digest=DIGEST), "ONBOARD_KEY_DIR")
    assert w.writes() == 0 and applied.writes() == before


# --- 10: onboard_grant refusals --------------------------------------------------------------------------------------

def _grant_refused(w: World, email: str, role: str, site: str | None, code: str, status: int) -> None:
    with pytest.raises(AccountRefused) as caught:
        w.accounts.onboard_grant(SLUG, email, role, site)
    assert (caught.value.code, caught.value.status) == (code, status)


def test_10_onboard_grant_refusals(applied: World) -> None:
    w = applied
    joseph, wanjiru = "joseph@lakeside-power.example", "wanjiru@lakeside-power.example"
    before = len(w.store.grants)
    with pytest.raises(AccountRefused) as caught:
        w.accounts.onboard_grant("nowhere", joseph, FIN, None)
    assert (caught.value.code, caught.value.status) == ("TENANT_NOT_FOUND", 404)
    _grant_refused(w, joseph, EXEC, None, "ONBOARD_EXECUTIVE_GRANT", 422)
    _grant_refused(w, joseph, "JANITOR", None, "ROLE_UNKNOWN", 422)
    _grant_refused(w, joseph, "SITE_MANAGER", None, "ROLE_SITE_RULE", 422)
    _grant_refused(w, joseph, "SITE_MANAGER", "NOWHERE-001", "SITE_NOT_FOUND", 404)
    w.foundation.ensure_tenant("acme", "Acme Power", now=NOW)
    w.accounts.onboard_create("acme", "zawadi@acme.example", "Zawadi", "correct horse battery", executive=True)
    _grant_refused(w, "zawadi@acme.example", FIN, None, "PERSON_NOT_FOUND", 404)
    _grant_refused(w, joseph, FIN, None, "ROLE_ALREADY_HELD", 409)
    _grant_refused(w, wanjiru, FIN, None, "ROLES_SEPARATE", 409)
    _grant_refused(w, joseph, ANALYST, None, "ROLES_SEPARATE", 409)
    _grant_refused(w, "amina@lakeside-power.example", ANALYST, None, "ROLES_SEPARATE", 409)
    assert len([g for g in w.store.grants if g.tenant_id == w.tenant_id()]) == before
    row = w.accounts.onboard_grant(SLUG, "musa@lakeside-power.example", "SITE_MANAGER", "KOBO-001")
    assert (row.by_service, row.by_person_id, row.site_code) == (ONBOARDING, None, "KOBO-001")


def test_10_the_store_refuses_onboarding_grants_once_closed(applied: World) -> None:
    w = applied
    amina, musa = w.person("Amina"), w.person("Musa")
    boss = PersonPrincipal(amina.person_id, amina.tenant_id, "Amina", frozenset({(EXEC, None)}), uuid4(), NOW, NOW)
    w.accounts.grant(boss, musa.person_id, "SITE_MANAGER", "MTO-001")
    _grant_refused(w, "musa@lakeside-power.example", "SITE_MANAGER", "KOBO-001", "ONBOARDING_CLOSED", 409)
    assert w.accounts.executive_of(SLUG) == amina.person_id and w.accounts.executive_of("nowhere") is None
    assert w.accounts.onboarding_open("nowhere") is True


# --- the command's words ---------------------------------------------------------------------------------------------

def test_a_refusal_prints_code_place_and_sentence_and_exits_2_or_3(applied: World, capsys, tmp_path) -> None:
    doc = raw()
    doc["people"][1]["name"] = "Joe"
    changed = tmp_path / "f.json"
    changed.write_text(json.dumps(doc), encoding="utf-8")
    assert command.main(["check", "--file", str(changed), "--key-dir", "/k"], onboarding=applied.svc) == 2
    assert capsys.readouterr().err == (
        "ONBOARD_PERSON_DIFFERS people[1] This person already exists with another name, or is disabled.\n")
    assert command.main(["digest", "--file", str(changed)]) == 0
    assert capsys.readouterr().out == roles_digest(file(doc)) + "\n"
    doc["people"][1]["name"] = " Joe"
    changed.write_text(json.dumps(doc), encoding="utf-8")
    assert command.main(["digest", "--file", str(changed)]) == 2
    assert capsys.readouterr().err == (
        "ONBOARD_NAME people[1].name A name must be 1 to 120 characters with no surrounding spaces.\n")
    fresh = World()
    original = fresh.accounts.onboard_grant

    def refuse(*_a, **_k):
        raise AccountRefused("ROLES_SEPARATE", 409)

    fresh.accounts.onboard_grant = refuse
    assert command.main(["apply", "--file", str(FIXTURE), "--key-dir", "/k", "--confirmed-digest", DIGEST],
                        onboarding=fresh.svc) == 3
    assert capsys.readouterr().err.startswith("ROLES_SEPARATE")
    fresh.accounts.onboard_grant = original
    assert command.main(["apply", "--file", str(FIXTURE), "--key-dir", "/k", "--confirmed-digest", DIGEST[::-1]],
                        onboarding=fresh.svc) == 2
    assert capsys.readouterr().err.startswith("ONBOARD_DIGEST_DIFFERS ")
