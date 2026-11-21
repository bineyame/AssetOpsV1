"""OPS-01 harness naming and routing rules. No database is touched here."""

from __future__ import annotations

import pytest

import os

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


class _Config:
    """The two attributes the xdist checks read: a controller has `option.numprocesses`, a worker `workerinput`."""

    def __init__(self, numprocesses=None, workerinput=None) -> None:
        self.option = type("Option", (), {"numprocesses": numprocesses})()
        if workerinput is not None:
            self.workerinput = workerinput


@pytest.mark.parametrize("config", [_Config(numprocesses=2), _Config(workerinput={"workerid": "gw0"})],
                         ids=["controller", "worker"])
def test_the_template_opt_out_is_a_usage_error_under_xdist(clean_env, config) -> None:
    import conftest

    clean_env.setenv(pg_harness.ENV, BASE)
    clean_env.setenv(pg_harness.TEMPLATE_SWITCH, "0")
    with pytest.raises(pytest.UsageError, match="cannot be combined with pytest-xdist"):
        conftest.refuse_template_opt_out_under_xdist(config)
    assert pg_harness.RUN_ENV not in __import__("os").environ  # refused before any routing


@pytest.mark.parametrize("config", [_Config(), _Config(numprocesses=0)], ids=["serial", "n0"])
def test_the_template_opt_out_stays_valid_serially(clean_env, config) -> None:
    import conftest

    clean_env.setenv(pg_harness.TEMPLATE_SWITCH, "0")
    conftest.refuse_template_opt_out_under_xdist(config)
    clean_env.setenv(pg_harness.TEMPLATE_SWITCH, "1")
    conftest.refuse_template_opt_out_under_xdist(_Config(numprocesses=2))


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
                c.execute(text("SET LOCAL session_replication_role = replica"))  # 0070's TRUNCATE trigger is skipped
                c.execute(text(f"TRUNCATE {', '.join(ROOTS)} CASCADE"))
                tx.rollback()
                cascaded = {m.split('"')[1] for m in notices if m.startswith("truncate cascades to table")}
                closure = set(c.execute(text(pg_harness._CASCADE_CLOSURE), {"roots": list(ROOTS)}).scalars())
            assert cascaded, "TRUNCATE reported no cascade: the comparison would be vacuous"
            assert closure == set(ROOTS) | cascaded
        finally:
            eng.dispose()

    def test_the_controller_drops_every_database_of_its_run_and_nothing_else(self) -> None:
        """A crashed xdist worker leaves its database; the controller's `cleanup_run` removes it."""
        import os

        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url
        from sqlalchemy.pool import NullPool

        base = os.environ.get(pg_harness.BASE_ENV) or URL
        stem = make_url(base).database[: -len("_test")]
        dead = [pg_harness.database_name(stem, "dead0001", tag) for tag in ("tpl", "gw0", "gw1")]
        other = pg_harness.database_name(stem, "a11e0002", "gw0")
        eng = create_engine(base, poolclass=NullPool, isolation_level="AUTOCOMMIT")
        try:
            with eng.connect() as admin:
                for name in dead + [other]:
                    admin.execute(text(f'CREATE DATABASE "{name}"'))
                try:
                    assert sorted(pg_harness.cleanup_run("dead0001")) == sorted(dead)
                    left = set(admin.execute(text("SELECT datname FROM pg_database")).scalars())
                    assert not left & set(dead) and other in left
                finally:
                    for name in dead + [other]:
                        admin.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        finally:
            eng.dispose()


def _exists_database(name: str) -> bool:
    from sqlalchemy import text

    return pg_harness._admin().execute(text("SELECT count(*) FROM pg_database WHERE datname = :n"),
                                       {"n": name}).scalar_one() == 1


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
class TestCloneDatabase:
    """DS3 (D-DS3.14): the public clone helper registers what it clones, and the harness drops it."""

    def test_a_clone_is_a_registered_run_owned_test_database_and_drop_unregisters_it(self) -> None:
        import os

        from sqlalchemy.engine import make_url

        url = pg_harness.clone_database("ds3hone")
        name = make_url(url).database
        try:
            stem = make_url(os.environ[pg_harness.BASE_ENV]).database[: -len("_test")]
            match = pg_harness._owned_pattern(stem).match(name)
            assert match and match.group(1) == os.environ[pg_harness.RUN_ENV] and match.group(2) == "ds3hone" + (os.environ[pg_harness.TAG_ENV] if pg_harness._shared() else "")
            assert _exists_database(name) and name in pg_harness.registered_clones()
        finally:
            pg_harness.drop_database(url)
        assert not _exists_database(name) and name not in pg_harness.registered_clones()

    def test_cloning_a_source_with_an_open_session_fails_naming_the_count(self) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.engine import make_url

        source = pg_harness.clone_database("ds3hsrc")
        eng = create_engine(source)
        try:
            with eng.connect():
                with pytest.raises(AssertionError, match=r"it has 1 open session\(s\)"):
                    pg_harness.clone_database("ds3hdst", source)
            assert make_url(source).database in pg_harness.registered_clones()
        finally:
            eng.dispose()
            pg_harness.drop_database(source)

    def test_drop_and_clone_refuse_a_database_that_is_not_a_clone_or_audit(self) -> None:
        """F6: the same permitted_database rule as the world command, so the run template, the live walkthrough
        database and a serve or walk name cannot be dropped or cloned from, whatever the caller passes."""
        from sqlalchemy.engine import make_url

        base = make_url(os.environ[pg_harness.BASE_ENV])
        for name in (base.database, "assetops_polish_walk1113_test", "assetops_walk_audit1121_test", "assetops_serve_test"):
            url = base.set(database=name).render_as_string(hide_password=False)
            with pytest.raises(AssertionError, match="refusing to drop"):
                pg_harness.drop_database(url)
            with pytest.raises(AssertionError, match="refusing to clone from"):
                pg_harness.clone_database("ds3hdeny", url)

    def test_cleanup_drops_a_clone_still_registered(self, monkeypatch) -> None:
        from sqlalchemy.engine import make_url

        url = pg_harness.clone_database("ds3hleft")
        name = make_url(url).database
        # Keep this run's worker and template: cleanup drops ghost names instead, and the template marker comes back.
        monkeypatch.setattr(pg_harness, "_names", lambda: ("ds3_ghost_tpl_test", "ds3_ghost_main_test"))
        if "template" in pg_harness._state:
            monkeypatch.setitem(pg_harness._state, "template", pg_harness._state["template"])
        try:
            pg_harness.cleanup()
            assert not _exists_database(name)
            assert name not in pg_harness.registered_clones()
        finally:
            pg_harness.drop_database(url)
