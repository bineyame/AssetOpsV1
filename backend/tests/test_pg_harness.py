"""OPS-01 harness naming and routing rules. No database is touched here."""

from __future__ import annotations

import pytest

import pg_harness

BASE = "postgresql+psycopg://assetops:pw@127.0.0.1:55432/assetops_test"


@pytest.fixture()
def clean_env(monkeypatch):
    for name in (pg_harness.ENV, pg_harness.BASE_ENV, pg_harness.RUN_ENV, pg_harness.TAG_ENV, pg_harness.TEMPLATE_SWITCH):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_routing_points_the_url_at_a_run_owned_test_database(clean_env) -> None:
    import os

    clean_env.setenv(pg_harness.ENV, BASE)
    run = pg_harness.route()
    assert run and os.environ[pg_harness.BASE_ENV] == BASE
    routed = os.environ[pg_harness.ENV]
    assert routed.endswith(f"/assetops_pt{run}_main_test")
    assert ":pw@" in routed  # the password survives rendering, or every connection fails


def test_an_already_routed_environment_is_left_alone(clean_env) -> None:
    import os

    clean_env.setenv(pg_harness.ENV, BASE)
    first = pg_harness.route()
    url = os.environ[pg_harness.ENV]
    assert pg_harness.route() == first and os.environ[pg_harness.ENV] == url


@pytest.mark.parametrize("url", [None, "postgresql+psycopg://a:b@h/assetops"])
def test_no_routing_without_a_test_database(clean_env, url) -> None:
    import os

    if url:
        clean_env.setenv(pg_harness.ENV, url)
    assert pg_harness.route() is None
    assert os.environ.get(pg_harness.ENV) == url and pg_harness.RUN_ENV not in os.environ


def test_the_template_switch_turns_routing_off(clean_env) -> None:
    clean_env.setenv(pg_harness.ENV, BASE)
    clean_env.setenv(pg_harness.TEMPLATE_SWITCH, "0")
    assert pg_harness.route() is None


def test_names_fit_postgres_identifiers_and_refuse_overflow() -> None:
    assert pg_harness.database_name("assetops", "1a2b3c4d", "gw12") == "assetops_pt1a2b3c4d_gw12_test"
    with pytest.raises(ValueError, match="exceeds 63"):
        pg_harness.database_name("x" * 50, "1a2b3c4d", "main")


def test_the_orphan_sweep_matches_only_run_owned_names() -> None:
    pattern = pg_harness._owned_pattern("assetops")
    assert pattern.match("assetops_pt1a2b_main_test").group(1) == "1a2b"
    assert pattern.match("assetops_pt1a2b_tpl_test")
    for foreign in ("assetops_test", "assetops_s402b_test", "assetops_s402b3_full_test", "assetops_pt1a2b_main",
                    "other_pt1a2b_main_test", "assetops_ptxyz_main_test"):
        assert not pattern.match(foreign), foreign
