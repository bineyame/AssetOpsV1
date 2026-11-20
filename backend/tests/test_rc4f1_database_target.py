"""RC4-F1 (spec §4): `database_target` names the database psycopg is handed, or refuses; every RC4 decision uses it.

No database: every URL uses the unresolvable host `rc4.invalid` port 1 except where the host is the point.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

from assetops_backend import database_target as dt
from assetops_backend.chain import backfill
from assetops_backend.commercial.composition import commercial_upload_settings
from assetops_backend.config import ConfigurationError
from assetops_backend.database_target import DatabaseTarget, DatabaseTargetUnclear, database_target
from test_3a2_commercial_upload_api import _env

REPO = Path(__file__).resolve().parents[2]
BASE = "postgresql+psycopg://u:s3cret@rc4.invalid:1/"

ADMITTED = [
    (BASE + "assetops_test", DatabaseTarget("rc4.invalid", 1, "assetops_test")),
    (BASE + "assetops_test?connect_timeout=2", DatabaseTarget("rc4.invalid", 1, "assetops_test")),
    (BASE + "assetops_test?sslmode=disable&application_name=x", DatabaseTarget("rc4.invalid", 1, "assetops_test")),
    ("postgresql://u:s3cret@rc4.invalid/assetops_op_pilot1", DatabaseTarget("rc4.invalid", None, "assetops_op_pilot1")),
    (BASE + "assetops%5Fop_x", DatabaseTarget("rc4.invalid", 1, "assetops_op_x")),
]


# --- 1, 2: admitted, and the dialect agrees -------------------------------------------------------------------------

@pytest.mark.parametrize("url, expected", ADMITTED)
def test_1_admitted(url, expected) -> None:
    assert database_target(url, {}) == expected


@pytest.mark.parametrize("url, expected", ADMITTED)
def test_2_the_dialect_is_handed_the_same_database(url, expected) -> None:
    parsed = make_url(url)
    args = parsed.get_dialect()().create_connect_args(parsed)[1]  # instantiated, never connected
    target = database_target(url, {})
    assert args["dbname"] == target.name and args["host"] == target.host


# --- 3: refused, one per reason -------------------------------------------------------------------------------------

REFUSED = [
    ("not a url", "URL_UNREADABLE"),
    ("sqlite:///x.db", "DRIVER_NOT_POSTGRES"),
    (BASE + "assetops_test?dbname=assetops_op_x", "QUERY_KEY dbname"),
    (BASE + "assetops_test?service=op", "QUERY_KEY service"),
    (BASE + "assetops_test?host=other", "QUERY_KEY host"),
    (BASE + "assetops_test?hostaddr=10.0.0.1", "QUERY_KEY hostaddr"),
    (BASE + "assetops_test?port=5", "QUERY_KEY port"),
    (BASE + "assetops_test?options=-csearch_path%3Dx", "QUERY_KEY options"),
    (BASE + "assetops_test?connect_timeout=2&connect_timeout=3", "QUERY_REPEATED connect_timeout"),
    ("postgresql+psycopg://u:s3cret@/assetops_test", "HOST_MISSING"),
    ("postgresql+psycopg://u:s3cret@h1,h2/assetops_test", "HOST_MULTIPLE"),
    (BASE + "?dbname=assetops_op_x", "QUERY_KEY dbname"),
    (BASE, "NAME_MISSING"),
    (BASE.rstrip("/"), "NAME_MISSING"),
    (BASE + "dbname%3Dassetops_op_x", "NAME_NOT_PLAIN"),
    (BASE + "assetops test", "NAME_NOT_PLAIN"),
]


@pytest.mark.parametrize("url, reason", REFUSED)
def test_3_refused(url, reason) -> None:
    with pytest.raises(DatabaseTargetUnclear) as caught:
        database_target(url, {})
    assert caught.value.reason == reason and str(caught.value) == reason
    assert "s3cret" not in caught.value.reason


@pytest.mark.parametrize("variable", dt.PG_TARGET_ENV)
def test_3_refused_environment(variable) -> None:
    with pytest.raises(DatabaseTargetUnclear) as caught:
        database_target(BASE + "assetops_test", {variable: "assetops_op_x"})
    assert caught.value.reason == f"ENVIRONMENT {variable}" and "s3cret" not in caught.value.reason


def test_3_an_empty_variable_is_admitted() -> None:
    assert database_target(BASE + "assetops_test", {"PGDATABASE": ""}).name == "assetops_test"


def test_3_environ_defaults_to_the_process(monkeypatch) -> None:
    monkeypatch.setenv("PGDATABASE", "assetops_op_x")
    with pytest.raises(DatabaseTargetUnclear, match="ENVIRONMENT PGDATABASE"):
        database_target(BASE + "assetops_test")


# --- 4: the settings (extends 3A2's test_8) -------------------------------------------------------------------------

@pytest.mark.parametrize("switch, url, environ, reason", [
    ("off", BASE + "assetops_test?dbname=assetops_op_x", {}, "QUERY_KEY dbname"),
    ("off", BASE + "?dbname=assetops_op_x", {}, "QUERY_KEY dbname"),
    ("off", BASE, {}, "NAME_MISSING"),
    ("off", BASE + "assetops_test", {"PGSERVICE": "x"}, "ENVIRONMENT PGSERVICE"),
    ("on", BASE + "assetops_op_x?dbname=assetops_test", {}, "QUERY_KEY dbname"),
])
def test_4_settings_refuse_an_unclear_url(monkeypatch, switch, url, environ, reason) -> None:
    _env(monkeypatch, switch, key_dir="/keys")
    for name, value in environ.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(ConfigurationError) as caught:
        commercial_upload_settings(url)
    assert str(caught.value) == f"DATABASE_URL must name one database plainly ({reason})."


# --- 5: the backfill ------------------------------------------------------------------------------------------------

class _Reader:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def database_name(self) -> str:
        return "other"

    def __getattr__(self, name):
        raise AssertionError(f"the reader was read: {name}")


class _Store:
    def __getattr__(self, name):
        raise AssertionError(f"the store was touched: {name}")


@pytest.mark.parametrize("url, words", [
    (BASE + "assetops_polish_full_test?connect_timeout=2", "read-only"),
    (BASE + "x_test?dbname=assetops_polish_full_test", "not plain"),
])
def test_5_backfill_decides_on_the_url(monkeypatch, capsys, url, words) -> None:
    monkeypatch.setattr(backfill, "database_url", lambda: url)
    assert backfill.main(["--steps", "b"], reader=_Reader(), store=_Store()) == 2
    err = capsys.readouterr().err
    assert words in err and "s3cret" not in err


# --- 6: the demo strips the PG* target variables --------------------------------------------------------------------

def test_6_demo_env_holds_no_pg_target(monkeypatch) -> None:
    sys.path.insert(0, str(REPO / "tools"))
    import demo_combined as tool

    assert tool.PG_TARGET_ENV == dt.PG_TARGET_ENV
    for name in ("PGDATABASE", "PGHOST", "PGSERVICE"):
        monkeypatch.setenv(name, "assetops_op_x")
    env = tool.Demo("assetops_polish_full_test", "var/polish_full").env()
    assert not set(dt.PG_TARGET_ENV) & set(env)


# --- 7: no caller left ----------------------------------------------------------------------------------------------

#: Backlog `RC4-F1-tools` (spec §2.2): walkthrough tools guarding their own scratch names, not changed by this unit.
BACKLOG_TOOLS = frozenset({"sweep-setup-cache.py"})


def _sources():
    for root in (REPO / "backend" / "assetops_backend", REPO / "tools"):
        for path in root.rglob("*.py"):
            if path.name not in BACKLOG_TOOLS:
                yield path


def test_7_no_caller_reads_the_path_name() -> None:
    found = []
    for path in _sources():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), str(path))):
            if (isinstance(node, ast.Attribute) and node.attr == "database" and isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "id", getattr(node.value.func, "attr", None)) == "make_url"):
                found.append(f"{path}:{node.lineno}")
            if (isinstance(node, ast.ImportFrom) and (node.module or "").endswith("postgres_commercial_store")
                    and any(a.name == "database_name" for a in node.names)):
                found.append(f"{path}:{node.lineno}")
    assert found == []


def test_7_the_scan_sees_a_path_name_read() -> None:
    """The scan's set is non-empty on a real read (the backlog tool holds one)."""
    tree = ast.parse((REPO / "tools" / "sweep-setup-cache.py").read_text(encoding="utf-8"))
    assert any(isinstance(n, ast.Attribute) and n.attr == "database" and isinstance(n.value, ast.Call)
               and getattr(n.value.func, "id", None) == "make_url" for n in ast.walk(tree))
