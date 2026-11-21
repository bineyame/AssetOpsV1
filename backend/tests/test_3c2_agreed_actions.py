"""3C2 (`specs/3C2-agreed-change-action/spec.md` §4, §5 tests 1 to 5; D-3C2.2 to D-3C2.14): the agreed change
recorded as an Action, without a database.

Commit 1 (D-3C2.14) serves no text: the state is `OPEN` or `OVERDUE` and a refusal is its code alone on stderr. The
exact sentences and words land with the SC-1 statements in commit 2.
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from itertools import count
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from assetops_backend import record_action
from assetops_backend.accounts.model import GrantRow
from assetops_backend.accounts.permissions import roles_of
from assetops_backend.accounts.service import AccountService
from assetops_backend.actions import agreed
from assetops_backend.actions.agreed import (OWNER_COVER, AgreedActionService, MemoryAgreedActionStore,
                                             StoreUnavailable, state_code)
from test_3c0a_accounts_service import PW, MemoryStore

BACKEND = Path(__file__).resolve().parents[1]
PKG = BACKEND / "assetops_backend"
ADAPTER = PKG / "actions" / "adapters" / "postgres_agreed_action_store.py"
MIGRATION = BACKEND / "migrations" / "versions" / "0069_agreed_action.py"

SLUG = "lakeside-power"
EXEC, FIN, ANALYST, SM, TECH = ("OPERATOR_EXECUTIVE", "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST", "SITE_MANAGER",
                                "FIELD_TECHNICIAN")
T_R1 = datetime(2026, 11, 20, 9, 30, tzinfo=timezone.utc)
TITLE = "Lower the generator stop setting at Kobo to 70% battery charge"
KEYS = ["action_id", "title", "site_code", "factor_id", "owner", "created_by", "created_role", "created_by_script",
        "created_at", "due_on", "state", "already_recorded"]
R1_LINE = {"action_id": "00000000-0000-0000-0000-000000000001", "title": TITLE, "site_code": "KOBO-001",
           "factor_id": "candidate_l", "owner": "Peter", "created_by": "Amina", "created_role": EXEC,
           "created_by_script": True, "created_at": "2026-11-20T09:30:00Z", "due_on": "2026-12-15", "state": "OPEN",
           "already_recorded": False}


def email(name: str) -> str:
    return f"{name}@lakeside-power.example"


def r1(**change: str | None) -> list[str]:
    """R1's arguments with the named ones changed (`None` drops the flag)."""
    args = {"--tenant": SLUG, "--as": email("amina"), "--title": TITLE, "--owner": email("peter"),
            "--due": "2026-12-15", "--site": "KOBO-001", "--factor": "candidate_l"}
    for flag, value in change.items():
        args["--" + flag.rstrip("_")] = value
    argv: list[str] = []
    for flag, value in args.items():
        if value is not None:
            argv += [flag, value]
    return argv


class Clock:
    def __init__(self, *values: datetime) -> None:
        self.values = list(values)
        self.calls = 0

    def set(self, value: datetime) -> None:
        self.values = [value]

    def __call__(self) -> datetime:
        self.calls += 1
        return self.values[min(self.calls - 1, len(self.values) - 1)]


@dataclass
class Composed:
    service: AgreedActionService


class World:
    def __init__(self, ids: tuple[int, ...] | None = None) -> None:
        self.accounts_store = MemoryStore()
        self.accounts = AccountService(self.accounts_store, clock=lambda: T_R1)
        self.store = MemoryAgreedActionStore()
        self.clock = Clock(T_R1)
        numbers = iter(ids) if ids is not None else count(1)
        self.service = AgreedActionService(self.store, self.accounts, clock=self.clock,
                                           new_id=lambda: UUID(int=next(numbers)))
        self.tenant = self.accounts_store.add_tenant(SLUG, "Lakeside Power")
        self.sites = {code: self._site(self.tenant, code, kind)
                      for code, kind in (("KISIWA-001", "MINIGRID"), ("KOBO-001", "MINIGRID"),
                                         ("MTO-001", "MINIGRID"), ("FRIDGE-001", "COLDCHAIN"))}
        self.people: dict[str, UUID] = {}
        self._person(SLUG, email("amina"), "Amina", executive=True)
        for name, role, site in (("Joseph", FIN, None), ("Wanjiru", ANALYST, None), ("Peter", SM, "KOBO-001"),
                                 ("Halima", SM, "KISIWA-001"), ("David", SM, "MTO-001"), ("Musa", TECH, None)):
            self._person(SLUG, email(name.lower()), name)
            self.accounts.onboard_grant(SLUG, email(name.lower()), role, site)
        # Fatuma: a second executive of Lakeside, disabled (the memory store refuses a second executive account).
        pid = self._person(SLUG, email("fatuma"), "Fatuma")
        row_id = uuid4()
        self.accounts_store.grants.append(GrantRow(row_id, row_id, self.tenant, pid, "Fatuma", EXEC, None, None,
                                                   "GRANTED", None, None, "service:onboarding", T_R1))
        self.accounts_store.statuses.append((pid, "DISABLED", None, T_R1 + timedelta(seconds=1), uuid4()))
        self.other = self.accounts_store.add_tenant("other-op", "Other Op")
        self._person("other-op", "zara@other-op.example", "Zara", executive=True)

    def _site(self, tenant: UUID, code: str, kind: str) -> UUID:
        sid = self.accounts_store.add_site(tenant, code)
        self.store.add_site(tenant, code, kind, sid)
        return sid

    def _person(self, slug: str, address: str, name: str, *, executive: bool = False) -> UUID:
        pid = self.accounts.onboard_create(slug, address, name, PW, executive=executive)
        self.store.add_person(pid, name)
        self.people[name] = pid
        return pid

    def run(self, argv: list[str], capsys, *, services=None) -> tuple[int, str, str]:
        code = record_action.main(argv, services=services or Composed(self.service))
        out, err = capsys.readouterr()
        return code, out, err


@pytest.fixture(autouse=True)
def _cheap_hash(monkeypatch):
    """The people's passwords are never checked here; one scrypt hash serves every account."""
    from assetops_backend.accounts import passwords

    stored = passwords.hash_password(PW)
    monkeypatch.setattr(passwords, "hash_password", lambda _pw: stored)


@pytest.fixture()
def w() -> World:
    return World()


def _ok(result: tuple[int, str, str]) -> dict:
    code, out, err = result
    assert (code, err) == (0, ""), err
    assert out.endswith("\n") and out.count("\n") == 1
    line = json.loads(out)
    assert list(line) == KEYS
    assert "@" not in out
    return line


def _refused(result: tuple[int, str, str], code: str, status: int = 2) -> None:
    exit_code, out, err = result
    assert (exit_code, out, err) == (status, "", f"{code}\n")
    assert "@" not in out + err


# --- test 1: R1 and its re-runs -----------------------------------------------------------------------------------

def test_1_r1_prints_the_twelve_keys_and_stores_one_row(w, capsys) -> None:
    assert _ok(w.run(r1(), capsys)) == R1_LINE
    assert len(w.store.rows) == 1
    row = w.store.rows[0]
    assert (row.owner_person_id, row.created_by_person_id, row.due_on, row.created_by_script, row.origin) == (
        w.people["Peter"], w.people["Amina"], date(2026, 12, 15), True, "DEEP_DIVE")


@pytest.mark.parametrize("at, title, state", [
    (T_R1, TITLE, "OPEN"),
    (datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc), TITLE, "OPEN"),
    (datetime(2026, 12, 16, 8, 0, tzinfo=timezone.utc), TITLE, "OVERDUE"),
    (T_R1, f"  {TITLE}  ", "OPEN"),
], ids=["same-time", "later-same-day", "after-due-date", "padded-title"])
def test_1_a_re_run_records_nothing_new(w, capsys, at, title, state) -> None:
    _ok(w.run(r1(), capsys))
    w.clock.set(at)
    again = _ok(w.run(r1(title=title), capsys))
    assert again == {**R1_LINE, "state": state, "already_recorded": True}
    assert len(w.store.rows) == 1


# --- test 2: every refusal and every accepted case ----------------------------------------------------------------

REFUSALS = [
    ("as-joseph", r1(as_=email("joseph")), None, "PERSON_ROLE_REQUIRED"),
    ("as-peter", r1(as_=email("peter")), None, "PERSON_ROLE_REQUIRED"),
    ("as-nobody", r1(as_=email("nobody")), None, "PERSON_NOT_FOUND"),
    ("as-zara", r1(as_="zara@other-op.example"), None, "PERSON_NOT_FOUND"),
    ("as-fatuma-disabled", r1(as_=email("fatuma")), None, "PERSON_NOT_FOUND"),
    ("owner-halima", r1(owner=email("halima")), None, "OWNER_SCOPE"),
    ("owner-david", r1(owner=email("david")), None, "OWNER_SCOPE"),
    ("owner-wanjiru", r1(owner=email("wanjiru")), None, "OWNER_SCOPE"),
    ("owner-musa", r1(owner=email("musa")), None, "OWNER_SCOPE"),
    ("site-mto-owner-peter", r1(site="MTO-001"), None, "OWNER_SCOPE"),
    ("no-site-owner-peter", r1(site=None, factor=None), None, "OWNER_SCOPE"),
    ("no-site-owner-wanjiru", r1(site=None, factor=None, owner=email("wanjiru")), None, "OWNER_SCOPE"),
    ("owner-zara", r1(owner="zara@other-op.example"), None, "OWNER_NOT_FOUND"),
    ("owner-fatuma-disabled", r1(owner=email("fatuma")), None, "OWNER_NOT_FOUND"),
    ("factor-without-site", r1(site=None), None, "FACTOR_NEEDS_SITE"),
    ("factor-nonsense", r1(factor="nonsense"), None, "FACTOR_UNKNOWN"),
    ("factor-site-type", r1(site="FRIDGE-001"), None, "FACTOR_SITE_TYPE"),
    ("site-nope", r1(site="NOPE-001"), None, "SITE_NOT_FOUND"),
    ("site-nope-and-owner-zara", r1(site="NOPE-001", owner="zara@other-op.example"), None, "SITE_NOT_FOUND"),
    ("due-yesterday", r1(due="2026-11-19"), None, "DUE_IN_PAST"),
    ("clock-after-due", r1(), datetime(2026, 12, 16, 8, 0, tzinfo=timezone.utc), "DUE_IN_PAST"),
    ("due-format", r1(due="15/12/2026"), None, "BAD_DUE"),
    ("title-spaces", r1(title="  "), None, "BAD_TITLE"),
    ("title-201", r1(title="x" * 201), None, "BAD_TITLE"),
    ("title-tab", r1(title="Title\twith tab"), None, "BAD_TITLE"),
    ("title-line-separator", r1(title="Title two"), None, "BAD_TITLE"),
    ("title-leading-nbsp", r1(title="\u00a0Title"), None, "BAD_TITLE"),
    ("tenant-nope", r1(tenant="nope"), None, "UNKNOWN_TENANT"),
]


@pytest.mark.parametrize("argv, at, code", [r[1:] for r in REFUSALS], ids=[r[0] for r in REFUSALS])
def test_2_refusals(w, capsys, argv, at, code) -> None:
    if at is not None:
        w.clock.set(at)
    _refused(w.run(argv, capsys), code)
    assert w.store.rows == []


def test_2_no_database_url_and_no_services(monkeypatch, capsys) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    code = record_action.main(r1())
    out, err = capsys.readouterr()
    _refused((code, out, err), "NO_DATABASE")


def test_2_a_store_error_is_actions_unavailable(w, capsys, monkeypatch) -> None:
    def down(*_a, **_k):
        raise StoreUnavailable()

    monkeypatch.setattr(w.store, "add", down)
    _refused(w.run(r1(), capsys), "ACTIONS_UNAVAILABLE", 3)


def test_2_a_composition_error_is_actions_unavailable(monkeypatch, capsys) -> None:
    import assetops_backend.actions.agreed_composition as composition

    def broken(*_a, **_k):
        raise RuntimeError("no engine")

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@agreed.invalid:1/x_test")
    monkeypatch.setattr(composition, "build_agreed_actions", broken)
    code = record_action.main(r1())
    out, err = capsys.readouterr()
    _refused((code, out, err), "ACTIONS_UNAVAILABLE", 3)


ACCEPTED = [
    ("owner-joseph-at-kobo", r1(owner=email("joseph")), {"owner": "Joseph"}),
    ("operator-wide-owner-joseph", r1(site=None, factor=None, owner=email("joseph")),
     {"owner": "Joseph", "site_code": None, "factor_id": None}),
    ("owner-is-the-creator", r1(owner=email("amina")), {"owner": "Amina"}),
    ("mto-owner-david", r1(site="MTO-001", owner=email("david")), {"owner": "David", "site_code": "MTO-001"}),
    ("due-today", r1(due="2026-11-20"), {"due_on": "2026-11-20"}),
    ("title-200", r1(title="y" * 200), {"title": "y" * 200}),
]


@pytest.mark.parametrize("argv, expected", [a[1:] for a in ACCEPTED], ids=[a[0] for a in ACCEPTED])
def test_2_accepted(w, capsys, argv, expected) -> None:
    line = _ok(w.run(argv, capsys))
    assert line == {**R1_LINE, **expected}
    assert (line["created_role"], line["created_by"]) == (EXEC, "Amina")


def test_2_microseconds_are_dropped_from_the_clock(w, capsys) -> None:
    w.clock.set(datetime(2026, 11, 20, 9, 30, 0, 654321, tzinfo=timezone.utc))
    assert _ok(w.run(r1(), capsys))["created_at"] == "2026-11-20T09:30:00Z"
    assert w.store.rows[0].created_at == T_R1


def test_2_one_clock_read_per_record(w, capsys) -> None:
    w.clock.values = [T_R1, datetime(2026, 12, 16, tzinfo=timezone.utc)]
    line = _ok(w.run(r1(), capsys))
    assert (line["state"], line["created_at"], w.clock.calls) == ("OPEN", "2026-11-20T09:30:00Z", 1)


def test_2_rights_are_checked_on_a_re_run(w, capsys) -> None:
    _ok(w.run(r1(), capsys))
    peter = next(g for g in w.accounts_store.grants if g.person_id == w.people["Peter"])
    w.accounts_store.grants.remove(peter)
    _refused(w.run(r1(), capsys), "OWNER_SCOPE")


def test_2_a_naive_clock_is_a_programming_error(w) -> None:
    w.clock.set(datetime(2026, 11, 20, 9, 30))
    with pytest.raises(ValueError):
        w.service.for_tenant(w.tenant)


# --- test 3: the read -----------------------------------------------------------------------------------------------

def test_3_the_read_is_newest_first_with_names_and_state_codes(capsys) -> None:
    w = World(ids=(1, 2, 3, 5, 4))
    records = [(T_R1, r1()),
               (datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc),
                r1(title="Change B", owner=email("joseph"), due="2026-11-30", site=None, factor=None)),
               (datetime(2026, 11, 20, 10, 30, tzinfo=timezone.utc),
                r1(title="Change C", due="2026-12-01", factor=None)),
               (datetime(2026, 11, 20, 11, 0, tzinfo=timezone.utc),
                r1(title="Change E", owner=email("joseph"), due="2026-12-20", site=None, factor=None)),
               (datetime(2026, 11, 20, 11, 0, tzinfo=timezone.utc),
                r1(title="Change D", owner=email("joseph"), due="2026-12-20", site=None, factor=None))]
    for at, argv in records:
        w.clock.set(at)
        _ok(w.run(argv, capsys))
    w.clock.set(datetime(2026, 12, 1, tzinfo=timezone.utc))
    w.clock.calls = 0
    views = w.service.for_tenant(w.tenant)
    assert w.clock.calls == 1
    assert [v.action_id.int for v in views] == [5, 4, 3, 2, 1]
    assert [v.title for v in views] == ["Change E", "Change D", "Change C", "Change B", TITLE]
    assert [(v.owner_name, v.created_by_name, v.site_code) for v in views] == [
        ("Joseph", "Amina", None), ("Joseph", "Amina", None), ("Peter", "Amina", "KOBO-001"),
        ("Joseph", "Amina", None), ("Peter", "Amina", "KOBO-001")]
    assert [v.state_code for v in views] == ["OPEN", "OPEN", "OPEN", "OVERDUE", "OPEN"]
    assert w.service.for_tenant(w.other) == ()


def test_3_state_code_on_and_after_the_due_day() -> None:
    assert state_code(date(2026, 12, 15), date(2026, 12, 15)) == "OPEN"
    assert state_code(date(2026, 12, 15), date(2026, 12, 16)) == "OVERDUE"


# --- test 4: the role tables ----------------------------------------------------------------------------------------

def test_4_only_the_executive_agrees_and_the_owner_cover_is_d_3c2_6() -> None:
    assert roles_of("action.agree") == (EXEC,)
    assert dict(OWNER_COVER) == {EXEC: "ALL", FIN: "ALL", SM: "SITE"}


def test_4_the_epilog_states_the_utc_rule() -> None:
    assert record_action.build_parser().epilog == "Overdue counts from the day after the due date, by the UTC calendar."


# --- test 5: the seams, by grep -------------------------------------------------------------------------------------

def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
        elif isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
    return found


def _sql_strings(path: Path) -> list[str]:
    """Every string literal of the module joined per expression (implicit concatenation is one constant)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]


def test_5_agreed_imports_no_adapter_and_no_s6_action_module() -> None:
    banned = {"assetops_backend.actions.service", "assetops_backend.actions.lifecycle",
              "assetops_backend.actions.ports", "assetops_backend.actions.composition"}
    imports = _imports(Path(agreed.__file__))
    assert not {m for m in imports if ".adapters" in m or m in banned
                or m.startswith("assetops_backend.actions.verification")}


def test_5_only_actions_composition_imports_the_adapter() -> None:
    importers = {p.relative_to(PKG).as_posix() for p in PKG.rglob("*.py")
                 if "assetops_backend.actions.adapters.postgres_agreed_action_store" in _imports(p)}
    assert importers == {"actions/composition.py"}
    shim = Path(PKG / "actions/agreed_composition.py")
    tree = ast.parse(shim.read_text(encoding="utf-8"))
    assert not [m for m in _imports(shim) if ".adapters" in m]
    assert [type(n) for n in tree.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))] \
        == [ast.ImportFrom, ast.Assign]


def test_5_the_adapter_reads_only_its_three_tables() -> None:
    sql = " ".join(_sql_strings(ADAPTER))
    tables = {t.lower() for t in re.findall(r"(?i)\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-z_][a-z0-9_]*)", sql)}
    assert tables and tables <= {"agreed_action", "operator_account", "site"}
    source = ADAPTER.read_text(encoding="utf-8")
    assert not re.search(r"\baction\b", source) and not re.search(r"\baction_event\b", source)


def test_5_no_value_word_in_the_migration_or_the_adapter_sql() -> None:
    value_word = re.compile(r"(?i)\b(commercial_\w+|value|amount|currency|price|cost|money)\b")
    assert not value_word.search(MIGRATION.read_text(encoding="utf-8"))
    assert not value_word.search(" ".join(_sql_strings(ADAPTER)))
