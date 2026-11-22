"""ON1 (spec §3.4, §6 "Settings, demo and runbook, no database"; D-ON1.5, D-ON1.11, D-ON1.12, D-ON1.13): the served
tenant, the demo pin and the runbook.

No database: the autouse no-connect fixture makes every connection attempt raise, and every URL naming a database uses
host `rc4.invalid` port 1.
"""
from __future__ import annotations

import argparse
import ast
import re
import shlex
import sys
from pathlib import Path
from typing import Callable

import psycopg
import pytest
import sqlalchemy.engine
from sqlalchemy import create_engine

from assetops_backend.config import ConfigurationError, served_tenant_slug
from assetops_backend.database_target import PG_TARGET_ENV
from foundation_fakes import InMemoryFoundationStore

SETTINGS = ("DATABASE_URL", "ASSETOPS_REAL_OPERATOR_DATA", "ASSETOPS_TENANT_SLUG", "ASSETOPS_PSEUDONYM_KEY_DIR")


def _no_connect(*_a, **_k):
    raise AssertionError("connection attempted")


@pytest.fixture(autouse=True)
def no_connect(monkeypatch):
    monkeypatch.setattr(psycopg, "connect", _no_connect)
    monkeypatch.setattr(psycopg.Connection, "connect", classmethod(_no_connect))
    monkeypatch.setattr(sqlalchemy.engine.Engine, "connect", _no_connect)
    for variable in PG_TARGET_ENV + SETTINGS:
        monkeypatch.delenv(variable, raising=False)


def test_no_connect_fixture_holds() -> None:
    with pytest.raises(AssertionError, match="^connection attempted$"):
        create_engine("postgresql+psycopg://u:p@rc4.invalid:1/x").connect()


# --- 1: the setting --------------------------------------------------------------------------------------------------

def test_1_served_tenant_slug(monkeypatch) -> None:
    assert served_tenant_slug() == "demo"
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "lakeside-power")
    assert served_tenant_slug() == "lakeside-power"
    for bad in ("", "Lakeside", "a b"):
        monkeypatch.setenv("ASSETOPS_TENANT_SLUG", bad)
        with pytest.raises(ConfigurationError, match="^ASSETOPS_TENANT_SLUG must be a tenant slug.$"):
            served_tenant_slug()


# --- 2: the app ------------------------------------------------------------------------------------------------------

def test_2_an_operator_database_never_serves_the_demo_tenant(monkeypatch) -> None:
    from assetops_backend.main import create_app

    monkeypatch.setenv("ASSETOPS_REAL_OPERATOR_DATA", "on")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@rc4.invalid:1/assetops_op_pilot1")
    with pytest.raises(ConfigurationError, match="^An operator database serves its operator's tenant"):
        create_app()


def test_2_the_app_serves_the_named_tenant(monkeypatch) -> None:
    from assetops_backend.main import create_app

    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "lakeside-power")
    app = create_app(foundation_store=InMemoryFoundationStore())
    assert app.state.site_registry.served_tenant_slug == "lakeside-power"
    assert app.state.site_registry.service.tenant_slug == "lakeside-power"


# --- 3: the runbook (D-ON1.13) ---------------------------------------------------------------------------------------

REPO = Path(__file__).resolve().parents[2]
RUNBOOK = REPO / "Docs" / "engineering" / "operator-deep-dive-runbook.md"
SPEC_RUNBOOK = REPO / "specs" / "ON1-operator-tenant" / "runbook.md"
#: Spec §6 settings 3: exactly these command lines, in this order (rev 3: the rehearsal and erasure).
EXPECTED = ["onboard_operator digest", "onboard_operator check", "onboard_operator apply",
            "accounts.onboard set-password", "source_profile admit", "source_profile list", "world_history exports",
            "load_emulated_exports", "reconcile_month record", "build_structure_snapshot build", "record_action",
            "rehearsal_check", "commercial.pseudonym_key erase"]
#: One value per variable the runbook declares in its "Shell variables" line.
VALUES = {"REHEARSAL": "ddr1", "FILE": "backend/tests/fixtures/on1/lakeside-power.onboarding.json",
          "DIGEST": "0" * 64, "KEY_DIR": "/opt/assetecon/keys/assetops_rehearsal_ddr1_test", "DB_PASSWORD": "pw",
          "EMAIL": "amina@lakeside-power.example", "DIR": "/tmp/exports",
          "TENANT_ID": "00000000-0000-0000-0000-000000000001",
          "ADMITTED_BY": "00000000-0000-0000-0000-000000000002", "PERIOD": "2026-10", "REVENUE": "9700.00",
          "FUEL_COST": "5100.00", "SOURCE_REF": "Management accounts, October 2026, draft"}
_VAR = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")


def _parsers() -> dict[str, Callable[[], argparse.ArgumentParser]]:
    from assetops_backend import (build_structure_snapshot, load_emulated_exports, onboard_operator, reconcile_month,
                                  record_action, rehearsal_check, source_profile)
    from assetops_backend.accounts import onboard
    from assetops_backend.commercial import pseudonym_key

    sys.path.insert(0, str(REPO / "tools"))
    import world_history

    return {"onboard_operator": onboard_operator.build_parser, "accounts.onboard": onboard.build_parser,
            "load_emulated_exports": load_emulated_exports.build_parser,
            "commercial.pseudonym_key": pseudonym_key.build_parser, "world_history": world_history.build_parser,
            "source_profile": source_profile.build_parser, "reconcile_month": reconcile_month.build_parser,
            "build_structure_snapshot": build_structure_snapshot.build_parser,
            "record_action": record_action.build_parser, "rehearsal_check": rehearsal_check.build_parser}


def _declared(text: str) -> set[str]:
    start = text.index("Shell variables")
    paragraph = text[start:text.index("\n\n", start)]
    return set(re.findall(r"`([A-Z][A-Z0-9_]*)`", paragraph))


def runbook_commands(text: str) -> list[str]:
    """Every checked line of the runbook's `sh` blocks, parsed; the (program, sub-command) list it holds."""
    declared = _declared(text)
    assert declared == set(VALUES), "the runbook's declared variables and the test's table differ"
    parsers = _parsers()
    found: list[str] = []
    for block in re.findall(r"^```sh\n(.*?)^```$", text, flags=re.M | re.S):
        depth = 0
        for line in block.splitlines():
            stripped = line.strip()
            if stripped == "(":
                depth += 1
                continue
            if stripped == ")":
                depth -= 1
                continue
            assert not (depth == 0 and stripped.startswith("export ")), f"export outside a subshell: {stripped}"
            if not stripped.startswith(("python -m assetops_backend.", "python -m uvicorn ",
                                        "python tools/world_history.py")):
                continue
            tokens = []
            for token in shlex.split(stripped):
                for name in _VAR.findall(token):
                    assert name in declared, f"undeclared variable ${name}"
                tokens.append(_VAR.sub(lambda m: VALUES[m.group(1)], token))
            if tokens[:3] == ["python", "-m", "uvicorn"]:
                assert tokens[3] == "assetops_backend.main:app"
                tree = ast.parse((REPO / "backend" / "assetops_backend" / "main.py").read_text(encoding="utf-8"))
                assert any(isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "app" for t in n.targets)
                           for n in tree.body)
                found.append("uvicorn")
                continue
            if tokens[1] == "tools/world_history.py":
                program, argv = "world_history", tokens[2:]
            else:
                program, argv = tokens[2].removeprefix("assetops_backend."), tokens[3:]
            assert program in parsers, f"no parser for {program}"
            try:
                args = parsers[program]().parse_args(argv)
            except SystemExit:
                raise AssertionError(f"the parser of {program} refuses: {stripped}") from None
            command = getattr(args, "command", None)
            found.append(program if command is None else f"{program} {command}")
        assert depth == 0, "an unclosed subshell"
    return found


def test_3_the_runbook_commands_parse_and_are_exactly_the_listed_ones() -> None:
    assert runbook_commands(RUNBOOK.read_text(encoding="utf-8")) == EXPECTED


def test_3_the_runbook_is_the_spec_text() -> None:
    spec = SPEC_RUNBOOK.read_text(encoding="utf-8")
    assert RUNBOOK.read_text(encoding="utf-8") == spec[spec.index("\n# ") + 1:]


@pytest.mark.parametrize("plant", ["flag", "export", "missing", "extra", "undeclared"])
def test_3_the_runbook_test_sees_each_planted_fault(plant) -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    apply = "--confirmed-digest \"$DIGEST\""
    changed = {
        "flag": lambda t: t.replace(apply, apply + " --force", 1),
        "export": lambda t: t.replace("```sh\nFILE=", "```sh\nexport ASSETOPS_TENANT_SLUG=lakeside-power\nFILE=", 1),
        "missing": lambda t: t.replace(
            "  python -m assetops_backend.onboard_operator check --file \"$FILE\" --key-dir \"$KEY_DIR\"\n", "", 1),
        "extra": lambda t: t.replace(
            "  python -m assetops_backend.accounts.onboard set-password --email \"$EMAIL\"\n",
            "  python -m assetops_backend.accounts.onboard set-password --email \"$EMAIL\"\n" * 2, 1),
        "undeclared": lambda t: t.replace("--email \"$EMAIL\"", "--email \"$PERSON\"", 1),
    }[plant](text)
    assert changed != text
    with pytest.raises(AssertionError):
        assert runbook_commands(changed) == EXPECTED


# --- 4: the demo serves the demo tenant (D-ON1.11) -------------------------------------------------------------------

def test_4_the_demo_pins_its_tenant_whatever_the_shell_holds(monkeypatch, tmp_path) -> None:
    sys.path.insert(0, str(REPO / "tools"))
    import demo_combined as tool

    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "lakeside-power")
    monkeypatch.setenv("ASSETOPS_REAL_OPERATOR_DATA", "on")
    monkeypatch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", "/k")
    monkeypatch.setenv(tool.PERIOD_READ_KINDS_ENV, "")
    demo = tool.Demo("assetops_polish_full_test", "var/polish_full")
    env = demo.env()
    assert env["ASSETOPS_TENANT_SLUG"] == "demo"
    assert "ASSETOPS_REAL_OPERATOR_DATA" not in env and "ASSETOPS_PSEUDONYM_KEY_DIR" not in env
    demo.work = tmp_path  # serve_env reads the work folder's keys file; an empty one here
    (tmp_path / "keys.json").write_text("{}", encoding="utf-8")
    served = demo.serve_env()
    assert served["ASSETOPS_TENANT_SLUG"] == "demo"
    assert "ASSETOPS_REAL_OPERATOR_DATA" not in served and "ASSETOPS_PSEUDONYM_KEY_DIR" not in served
