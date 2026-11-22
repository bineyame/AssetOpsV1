"""3C2 (`specs/3C2-agreed-change-action/spec.md` §4, §5 tests 1 to 5; D-3C2.2 to D-3C2.14): the agreed change
recorded as an Action, without a database.

Text (D-3C2.14, commit 2): the state word ("Open", "Overdue") and each refusal's sentence are SC-1 statements
(`i18n/statements/en/agreed_action.py`); the tests below assert section 4's exact strings, written by hand, and pin
each sentence through the composer with plants that must fail.
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
                                             StoreUnavailable, refusal_sentence, state_code, state_words)
from test_3c0a_accounts_service import PW, MemoryStore

BACKEND = Path(__file__).resolve().parents[1]
PKG = BACKEND / "assetops_backend"
ADAPTER = PKG / "actions" / "adapters" / "postgres_agreed_action_store.py"
MIGRATION = BACKEND / "migrations" / "versions" / "0070_agreed_action.py"

SLUG = "lakeside-power"
EXEC, FIN, ANALYST, SM, TECH = ("OPERATOR_EXECUTIVE", "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST", "SITE_MANAGER",
                                "FIELD_TECHNICIAN")
T_R1 = datetime(2026, 11, 20, 9, 30, tzinfo=timezone.utc)
TITLE = "Lower the generator stop setting at Kobo to 70% battery charge"
KEYS = ["action_id", "title", "site_code", "factor_id", "owner", "created_by", "created_role", "created_by_script",
        "created_at", "due_on", "state", "already_recorded"]
R1_LINE = {"action_id": "00000000-0000-0000-0000-000000000001", "title": TITLE, "site_code": "KOBO-001",
           "factor_id": "candidate_l", "owner": "Peter", "created_by": "Amina", "created_role": EXEC,
           "created_by_script": True, "created_at": "2026-11-20T09:30:00Z", "due_on": "2026-12-15", "state": "Open",
           "already_recorded": False}


#: Spec §2.5's sentences, exact, by hand (W2).
SENTENCES = {
    "BAD_TITLE": "Write a title of 1 to 200 characters.",
    "UNKNOWN_TENANT": "No operator has that name.",
    "PERSON_NOT_FOUND": "The person agreeing is not an active person of this operator.",
    "PERSON_ROLE_REQUIRED": "Only the operator's executive records an agreed change.",
    "SITE_NOT_FOUND": "This operator has no Site with that code.",
    "FACTOR_NEEDS_SITE": "Name the Site the factor belongs to (--site).",
    "FACTOR_UNKNOWN": "No factor has that name.",
    "FACTOR_SITE_TYPE": "This factor does not apply to that Site's type.",
    "OWNER_NOT_FOUND": "The owner is not an active person of this operator.",
    "OWNER_SCOPE": "The owner's role does not cover where this change applies.",
    "DUE_IN_PAST": "The due date is before today.",
    "BAD_DUE": "Write the due date as YYYY-MM-DD, like 2026-12-15.",
    "NO_DATABASE": "Set DATABASE_URL to the operator's database.",
    "ACTIONS_UNAVAILABLE": "The Actions store cannot be reached right now.",
}


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
    assert (exit_code, out, err) == (status, "", f"{code} {SENTENCES[code]}\n")
    assert "@" not in out + err


# --- test 1: R1 and its re-runs -----------------------------------------------------------------------------------

def test_1_r1_prints_the_twelve_keys_and_stores_one_row(w, capsys) -> None:
    assert _ok(w.run(r1(), capsys)) == R1_LINE
    assert len(w.store.rows) == 1
    row = w.store.rows[0]
    assert (row.owner_person_id, row.created_by_person_id, row.due_on, row.created_by_script, row.origin) == (
        w.people["Peter"], w.people["Amina"], date(2026, 12, 15), True, "DEEP_DIVE")


@pytest.mark.parametrize("at, title, state", [
    (T_R1, TITLE, "Open"),
    (datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc), TITLE, "Open"),
    (datetime(2026, 12, 16, 8, 0, tzinfo=timezone.utc), TITLE, "Overdue"),
    (T_R1, f"  {TITLE}  ", "Open"),
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
    assert (line["state"], line["created_at"], w.clock.calls) == ("Open", "2026-11-20T09:30:00Z", 1)


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

def test_3_the_read_is_newest_first_with_names_and_state_words(capsys) -> None:
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
    assert [v.state_words for v in views] == ["Open", "Open", "Open", "Overdue", "Open"]
    assert w.service.for_tenant(w.other) == ()


def test_3_state_code_on_and_after_the_due_day() -> None:
    assert state_code(date(2026, 12, 15), date(2026, 12, 15)) == "OPEN"
    assert state_code(date(2026, 12, 15), date(2026, 12, 16)) == "OVERDUE"


def test_3_state_words_on_and_after_the_due_day() -> None:
    assert state_words(date(2026, 12, 15), date(2026, 12, 15)) == "Open"
    assert state_words(date(2026, 12, 15), date(2026, 12, 16)) == "Overdue"


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


# --- commit 2 (D-3C2.14): each served string through the SC-1 composer, and plants that must fail ------------------

import copy  # noqa: E402
import importlib.util  # noqa: E402
import sys  # noqa: E402

from assetops_backend.i18n import Count, State, StatementError, Word, message, render  # noqa: E402
from assetops_backend.i18n import catalogue as i18n_catalogue  # noqa: E402
from assetops_backend.i18n.catalogue import CatalogueError  # noqa: E402
from assetops_backend.i18n.schema import UNSERVED  # noqa: E402
from statement_cases import agreed_action as agreed_cases  # noqa: E402

REPO = BACKEND.parent
AGREED = "backend/assetops_backend/actions/agreed.py"


def _guard():
    spec = importlib.util.spec_from_file_location("statement_catalogue_3c2", REPO / "tools/checks/statement_catalogue.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def _refusal(code: str, **facts):
    return message("agreed_action.refused", **{"code": State(code), "least": Count(1, "character"),
                                                "most": Count(200, "character"), **facts})


def _shipped() -> tuple[dict, dict]:
    cat = i18n_catalogue.current()
    return copy.deepcopy(cat.statements["en"]), copy.deepcopy(cat.vocabulary["en"])


def _load_code(statements: dict, vocabulary: dict) -> str:
    with pytest.raises(CatalogueError) as e:
        i18n_catalogue._build({"en": [statements]}, {"en": vocabulary})
    return e.value.code


@pytest.mark.parametrize("code", sorted(SENTENCES))
def test_c2_every_refusal_sentence_is_rendered_by_the_composer(code) -> None:
    assert render(_refusal(code)) == SENTENCES[code]
    assert refusal_sentence(code) == SENTENCES[code]


def test_c2_the_refusal_codes_are_exactly_the_exit_table() -> None:
    statement = i18n_catalogue.current().statements["en"]["agreed_action.refused"]
    assert set(statement["slots"]["code"]["values"]) == set(agreed.REFUSAL_EXIT) == set(SENTENCES)
    assert statement["exhaustive"] == "code"


def test_c2_the_state_words_come_from_the_action_state_vocabulary() -> None:
    assert render(message("agreed_action.state", state=Word("action_state", "OPEN"))) == "Open"
    assert render(message("agreed_action.state", state=Word("action_state", "OVERDUE"))) == "Overdue"
    vocabulary = i18n_catalogue.current().vocabulary["en"]["action_state"]
    assert vocabulary["order"] == [agreed.STATE_OPEN, agreed.STATE_OVERDUE]


@pytest.mark.parametrize("case", agreed_cases.CASES, ids=lambda c: f"{c.key}-{c.variant}")
def test_c2_each_hand_case_renders_its_english(case) -> None:
    assert render(message(case.key, **case.facts)) == case.english


def test_c2_agreed_is_adopted_and_builds_no_english() -> None:
    guard = _guard()
    assert AGREED in guard.ADOPTED
    source = (REPO / AGREED).read_text(encoding="utf-8")
    assert guard.adopted_hits(AGREED, source, UNSERVED) == []


@pytest.mark.parametrize("plant", [
    'STATE_OPEN_WORD = "Open"\n',
    'def _line(code):\n    return f"{code} refused"\n',
    'def _join(a, b):\n    return a + " and " + b\n',
    'TITLE_RULE = "Write a title of 1 to 200 characters."\n',
    'def _pick(late):\n    return "Overdue" if late else "Open"\n',
    'def _say(code):\n    return " ".join(["The", "due", "date"])\n',
], ids=["word", "fstring", "concat", "sentence", "conditional", "join"])
def test_c2_plant_a_hand_built_string_in_agreed_fails_the_adopted_scan(plant) -> None:
    source = (REPO / AGREED).read_text(encoding="utf-8") + "\n\n" + plant
    assert _guard().adopted_hits(AGREED, source, UNSERVED)


def test_c2_plant_the_old_category_literal_fails_the_adopted_scan() -> None:
    # The spec's literal `"Cc"` form is not code form in an adopted module; the upper-cased form is (packet Q1).
    source = (REPO / AGREED).read_text(encoding="utf-8").replace('{"CC", "CF", "ZL", "ZP"}', '{"Cc", "Cf", "Zl", "Zp"}')
    assert _guard().adopted_hits(AGREED, source, UNSERVED)


def test_c2_the_upper_cased_categories_refuse_what_d_3c2_11_refuses() -> None:
    import unicodedata
    refused = {"Cc", "Cf", "Zl", "Zp"}
    for cp in range(0x110000):
        category = unicodedata.category(chr(cp))
        assert (category.upper() in agreed.TITLE_REFUSED_CATEGORIES) == (category in refused)


def test_c2_plant_a_digit_in_a_template_fails_the_load() -> None:
    statements, vocabulary = _shipped()
    statements["agreed_action.refused"]["variants"][0]["text"] = "Write a title of 1 to 200 characters."
    assert _load_code(statements, vocabulary) == "LITERAL_DIGIT"


def test_c2_plant_a_number_word_in_a_template_fails_the_load() -> None:
    statements, vocabulary = _shipped()
    statements["agreed_action.refused"]["variants"][0]["text"] = "Write a title of one to {most}."
    assert _load_code(statements, vocabulary) == "LITERAL_NUMBER_WORD"


def test_c2_plant_a_dropped_refusal_variant_fails_the_load() -> None:
    statements, vocabulary = _shipped()
    statements["agreed_action.refused"]["variants"].pop()
    assert _load_code(statements, vocabulary) == "NOT_EXHAUSTIVE"


def test_c2_plant_a_three_segment_key_fails_the_load() -> None:
    statements, vocabulary = _shipped()
    statements["agreed_action.refused.bad_title"] = statements.pop("agreed_action.state")
    assert _load_code(statements, vocabulary) == "KEY_FORM"


def test_c2_plant_a_missing_state_word_fails_the_load() -> None:
    statements, vocabulary = _shipped()
    del vocabulary["action_state"]["entries"]["OVERDUE"]
    assert _load_code(statements, vocabulary) == "VOCABULARY_SCHEMA"


def test_c2_an_unknown_state_word_or_missing_bound_refuses_to_render() -> None:
    with pytest.raises(StatementError) as e:
        render(message("agreed_action.state", state=Word("action_state", "CLOSED")))
    assert e.value.code == "VOCABULARY_UNKNOWN"
    with pytest.raises(StatementError) as e:
        render(message("agreed_action.refused", code=State("BAD_TITLE"), least=Count(1, "character")))
    assert e.value.code == "FACT_MISSING"
    with pytest.raises(StatementError) as e:
        render(message("agreed_action.refused", code="BAD_TITLE", least=Count(1, "character"),
                       most=Count(200, "character")))
    assert e.value.code == "FACT_TYPE"


def test_c2_the_guard_reports_a_missing_case() -> None:
    guard = _guard()
    cases = [c for c in agreed_cases.CASES if c.variant != "bad_due"]
    cat = i18n_catalogue.current()
    render_mod = importlib.import_module("assetops_backend.i18n.render")
    messages_mod = importlib.import_module("assetops_backend.i18n.messages")
    original = guard._cases
    guard._cases = lambda root: (("agreed_action", c) for c in cases)
    try:
        out = guard.coverage(REPO, cat, render_mod._render, messages_mod.message, set())
    finally:
        guard._cases = original
    assert "CASE_MISSING agreed_action.refused bad_due" in out


# Unit 2 (spec section 3, test 9(e); D-3C2.16): the screen's one source is the agreed-action service. Plant P16.
def test_9e_deep_dive_imports_only_the_agreed_seam_from_actions() -> None:
    allowed = {"assetops_backend.actions.agreed", "assetops_backend.actions.agreed_composition"}
    for name in ("actions.py", "composition.py"):
        path = PKG / "deep_dive" / name
        found = {m for m in _imports(path) if m == "assetops_backend.actions" or m.startswith("assetops_backend.actions.")}
        assert found <= allowed, (name, found - allowed)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module == "assetops_backend":
                assert not {a.name for a in node.names} & {"actions"}, name
    actions = PKG / "deep_dive" / "actions.py"
    tree = ast.parse(actions.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "StoreAgreedActions")
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    a = init.args
    assert [x.arg for x in a.args] == ["self", "service"] and not (a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg)
