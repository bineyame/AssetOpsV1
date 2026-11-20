"""3C0a (spec §7, §9; R7, R10, D-3C0A.7): the onboarding command, run as a subprocess against this run's routed
`*_test` database. The subprocess environment is built from scratch: `DATABASE_URL` is the `engine` fixture's routed
URL, never an inherited one.
"""
from __future__ import annotations

import os
import subprocess
import sys
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.accounts.composition import build_account_service
    from assetops_backend.accounts.model import AccountRefused
    from test_3c0a_accounts_postgres import seed_tenant

PW = "correct horse battery"
NEW_PW = "a newer passphrase"


@pytest.fixture()
def routed(store, engine) -> str:  # noqa: F811
    url = engine.url
    assert url.database and url.database.endswith("_test") and url.database != "assetops_test", url.database
    seed_tenant(engine, "acme", "Acme Power")
    seed_tenant(engine, "beta", "Beta Cold")
    return url.render_as_string(hide_password=False)


def onboard(database_url: str | None, *args: str, stdin: str = PW + "\n") -> subprocess.CompletedProcess:
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": os.environ.get("PYTHONPATH", "")}
    if database_url is not None:
        env["DATABASE_URL"] = database_url
    return subprocess.run([sys.executable, "-m", "assetops_backend.accounts.onboard", *args], input=stdin,
                          capture_output=True, text=True, env=env, timeout=120)


def _refusal(result: subprocess.CompletedProcess, code: str) -> None:
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert result.stderr.startswith(code + " "), result.stderr
    assert result.stdout == ""


def test_without_database_url_the_command_exits_2() -> None:
    _refusal(onboard(None, "create", "--tenant", "acme", "--email", "a@b.example", "--name", "A"),
             "DATABASE_URL_REQUIRED")


def test_the_onboarding_command(routed: str) -> None:
    created = onboard(routed, "create", "--tenant", "acme", "--email", "amina@acme.example", "--name", "Amina",
                      "--executive")
    assert created.returncode == 0, created.stderr
    amina = UUID(created.stdout.strip())

    _refusal(onboard(routed, "create", "--tenant", "acme", "--email", "zara@acme.example", "--name", "Zara",
                     "--executive"), "EXECUTIVE_EXISTS")
    _refusal(onboard(routed, "disable", "--email", "amina@acme.example", "--reason", "left"), "LAST_EXECUTIVE")
    _refusal(onboard(routed, "create", "--tenant", "nope", "--email", "x@acme.example", "--name", "X"),
             "TENANT_NOT_FOUND")
    _refusal(onboard(routed, "create", "--tenant", "acme", "--email", "not an email", "--name", "X"), "BAD_EMAIL")
    _refusal(onboard(routed, "create", "--tenant", "beta", "--email", "AMINA@acme.example", "--name", "A"),
             "EMAIL_TAKEN")
    _refusal(onboard(routed, "create", "--tenant", "acme", "--email", "x@acme.example", "--name", "X",
                     stdin="short\n"), "PASSWORD_POLICY")
    _refusal(onboard(routed, "set-password", "--email", "nobody@acme.example"), "PERSON_NOT_FOUND")

    joined = onboard(routed, "create", "--tenant", "acme", "--email", "joseph@acme.example", "--name", "Joseph")
    assert joined.returncode == 0, joined.stderr
    joseph = UUID(joined.stdout.strip())

    svc = build_account_service(routed)
    signed = svc.sign_in("amina@acme.example", PW)
    assert signed.principal.person_id == amina and signed.principal.has_role("OPERATOR_EXECUTIVE")
    assert svc.sign_in("joseph@acme.example", PW).principal.roles == frozenset()  # no role from the command
    assert svc.grant_record(signed.principal)[-1].by_service == "service:onboarding"

    changed = onboard(routed, "set-password", "--email", "joseph@acme.example", stdin=NEW_PW + "\n")
    assert changed.returncode == 0 and UUID(changed.stdout.strip()) == joseph
    with pytest.raises(AccountRefused):
        svc.sign_in("joseph@acme.example", PW)
    assert svc.sign_in("joseph@acme.example", NEW_PW).principal.person_id == joseph

    disabled = onboard(routed, "disable", "--email", "joseph@acme.example", "--reason", "left the company")
    assert disabled.returncode == 0, disabled.stderr
    with pytest.raises(AccountRefused) as refused:
        svc.sign_in("joseph@acme.example", NEW_PW)
    assert refused.value.code == "SIGN_IN_REFUSED"
    enabled = onboard(routed, "enable", "--email", "joseph@acme.example")
    assert enabled.returncode == 0, enabled.stderr
    assert svc.sign_in("joseph@acme.example", NEW_PW).principal.person_id == joseph
