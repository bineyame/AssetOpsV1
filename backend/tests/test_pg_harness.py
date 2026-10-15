"""OPS-01 harness naming and routing rules. No database is touched here."""

from __future__ import annotations

import pytest

import pg_harness

BASE = "postgresql+psycopg://assetops:pw@127.0.0.1:55432/assetops_test"


@pytest.fixture()
def clean_env(monkeypatch):
    for name in (pg_harness.ENV, pg_harness.BASE_ENV, pg_harness.RUN_ENV, pg_harness.TAG_ENV, pg_harness.TEMPLATE_SWITCH,
                 pg_harness.SHARED_ENV):
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


def test_an_xdist_worker_routes_to_its_own_database_in_the_controllers_run(clean_env) -> None:
    import os

    clean_env.setenv(pg_harness.ENV, BASE)
    assert pg_harness.route(tag="gw1", run="abc12345") == "abc12345"
    assert os.environ[pg_harness.ENV].endswith("/assetops_ptabc12345_gw1_test")
    assert os.environ[pg_harness.BASE_ENV] == BASE and os.environ[pg_harness.SHARED_ENV] == "1"


def test_a_worker_under_an_already_routed_parent_routes_from_the_base(clean_env) -> None:
    """A parallel pytest started inside a routed run inherits the parent's routed URL."""
    import os

    clean_env.setenv(pg_harness.ENV, BASE)
    pg_harness.route()
    assert pg_harness.route(tag="gw0", run="def67890") == "def67890"
    assert os.environ[pg_harness.ENV].endswith("/assetops_ptdef67890_gw0_test")
    assert os.environ[pg_harness.BASE_ENV] == BASE


def test_serial_routing_owns_its_template(clean_env) -> None:
    import os

    clean_env.setenv(pg_harness.ENV, BASE)
    clean_env.setenv(pg_harness.SHARED_ENV, "1")  # a stale marker must not survive serial routing
    pg_harness.route()
    assert pg_harness.SHARED_ENV not in os.environ


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


URL = __import__("os").environ.get("ASSETOPS_TEST_DATABASE_URL")
ROOTS = ("foundation_revision", "source", "gateway", "asset", "site_import", "site", "tenant")


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
class TestAgainstPostgres:
    def test_a_module_database_is_a_run_owned_clone_at_head(self) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.engine import make_url

        pg_harness.fresh_database()
        eng = create_engine(URL)
        try:
            pg_harness.assert_at_head(eng)
        finally:
            eng.dispose()
        if pg_harness.routed():
            assert f"_pt{__import__('os').environ[pg_harness.RUN_ENV]}_" in make_url(URL).database

    def test_delete_cleanup_empties_exactly_the_tables_truncate_cascade_reaches(self) -> None:
        from sqlalchemy import create_engine, text

        pg_harness.fresh_database()
        eng = create_engine(URL)
        try:
            with eng.connect() as c:
                notices: list[str] = []
                raw = c.connection.dbapi_connection
                raw.add_notice_handler(lambda diag: notices.append(diag.message_primary or ""))
                tx = c.begin()
                c.execute(text(f"TRUNCATE {', '.join(ROOTS)} CASCADE"))
                tx.rollback()
                cascaded = {m.split('"')[1] for m in notices if m.startswith("truncate cascades to table")}
                closure = set(c.execute(text(pg_harness._CASCADE_CLOSURE), {"roots": list(ROOTS)}).scalars())
            assert cascaded, "TRUNCATE reported no cascade: the comparison would be vacuous"
            assert closure == set(ROOTS) | cascaded
        finally:
            eng.dispose()
