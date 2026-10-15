"""Real-Postgres test database harness (OPS-01).

The Postgres tests used to drop and re-migrate one shared `*_test` database at
the start of every module, which made Alembic-to-head the dominant fixed cost of
the suite. This module keeps the same guarantee - every module starts on a
fresh, fully migrated schema - by migrating once per run into a template and
re-cloning a run-owned database from it per module.

Routing. `route()` runs from `conftest.pytest_configure`, before any test
module is imported, and rewrites `ASSETOPS_TEST_DATABASE_URL` to a run-owned
database name. Module-level `URL` constants, skip markers, stores and child
processes therefore all see the run-owned database, never the base one. The
base URL is kept in `ASSETOPS_TEST_DATABASE_BASE_URL` and is used only as the
administrative connection that creates and drops run-owned databases.

Names. `<stem>_pt<run>_<tag>_test`, where `<stem>` is the base database name
without its `_test` suffix, `<run>` is the process id plus random hex, and
`<tag>` is `tpl` for the template or the worker tag (`main` when serial). Every
name is at most 63 characters and ends in `_test`.

Lifecycle. Provisioning is lazy: nothing is created for `--collect-only`, for a
command that selects no Postgres module, or when the URL is unset. The first
`fresh_database()` call takes a run lease (one admin session whose
`application_name` names the run), sweeps orphaned run-owned databases whose
run holds no live session, builds the template and clones the worker. Every
later call drops the worker `WITH (FORCE)` and clones it again. `cleanup()`
(from `pytest_sessionfinish`) drops only this run's databases; a killed run's
databases are removed by the next run's sweep, because its lease died with it.

Fallback. When routing is off (`ASSETOPS_TEST_TEMPLATE=0`) `fresh_database()`
performs the previous in-place reset: drop `public`, drop `btree_gist`, migrate
to head. Shared-database runs are serial only.
"""

from __future__ import annotations

import os
import re
import secrets
from pathlib import Path

ENV = "ASSETOPS_TEST_DATABASE_URL"
BASE_ENV = "ASSETOPS_TEST_DATABASE_BASE_URL"
RUN_ENV = "ASSETOPS_TEST_RUN_ID"
TAG_ENV = "ASSETOPS_TEST_DATABASE_TAG"
TEMPLATE_SWITCH = "ASSETOPS_TEST_TEMPLATE"
# Measurement knobs, off by default (see backend/TESTING.md).
STRATEGY_ENV = "ASSETOPS_TEST_CLONE_STRATEGY"  # WAL_LOG (server default) or FILE_COPY
SYNC_COMMIT_ENV = "ASSETOPS_TEST_SYNCHRONOUS_COMMIT"  # e.g. "off", applied per run-owned database only

BACKEND = Path(__file__).resolve().parents[1]
LEASE_PREFIX = "assetops-test-run:"
MAX_IDENTIFIER = 63

_state: dict = {}


def _stem(database: str) -> str:
    return database[: -len("_test")]


def database_name(stem: str, run: str, tag: str) -> str:
    name = f"{stem}_pt{run}_{tag}_test"
    if len(name) > MAX_IDENTIFIER:
        raise ValueError(f"run-owned database name {name!r} exceeds {MAX_IDENTIFIER} characters; shorten the base name")
    return name


def _owned_pattern(stem: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(stem)}_pt([0-9a-f]+)_([a-z0-9]+)_test$")


def route(tag: str = "main") -> str | None:
    """Point `ASSETOPS_TEST_DATABASE_URL` at this run's worker database.

    Returns the run id, or None when routing does not apply (URL unset, base not
    a `*_test` database, template switch off). An already-routed environment -
    a nested process started by a routed run - is left unchanged.
    """
    if os.environ.get(RUN_ENV):
        return os.environ[RUN_ENV]
    base = os.environ.get(ENV)
    if not base or os.environ.get(TEMPLATE_SWITCH, "1") == "0":
        return None
    from sqlalchemy.engine import make_url

    url = make_url(base)
    if not (url.database and url.database.endswith("_test")):
        return None  # the fixtures' own *_test guard refuses this before any DDL
    run = f"{os.getpid():x}{secrets.token_hex(2)}"
    worker = database_name(_stem(url.database), run, tag)
    database_name(_stem(url.database), run, "tpl")
    os.environ[BASE_ENV] = base
    os.environ[RUN_ENV] = run
    os.environ[TAG_ENV] = tag
    os.environ[ENV] = url.set(database=worker).render_as_string(hide_password=False)
    return run


def routed() -> bool:
    return bool(os.environ.get(RUN_ENV) and os.environ.get(BASE_ENV))


def _guard(url_text: str) -> None:
    from sqlalchemy.engine import make_url

    database = make_url(url_text).database
    assert database and database.endswith("_test"), "Refusing to run destructive tests against a database not named *_test"


def _alembic(url_text: str):
    from alembic.config import Config

    config = Config(str(BACKEND / "alembic.ini"))
    config.attributes["database_url"] = url_text
    return config


def _heads() -> set[str]:
    if "heads" not in _state:
        from alembic.script import ScriptDirectory

        _state["heads"] = set(ScriptDirectory.from_config(_alembic("postgresql://unused/unused_test")).get_heads())
    return _state["heads"]


def assert_at_head(engine) -> None:
    from sqlalchemy import text

    with engine.connect() as connection:
        versions = set(connection.execute(text("SELECT version_num FROM alembic_version")).scalars())
    assert versions == _heads(), f"database is at {sorted(versions)}, migration head is {sorted(_heads())}"


def _reset_in_place(url_text: str) -> None:
    """The pre-OPS-01 module setup, kept for the unrouted path."""
    from alembic import command
    from sqlalchemy import create_engine, text

    eng = create_engine(url_text)
    try:
        with eng.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
            connection.execute(text("DROP EXTENSION IF EXISTS btree_gist"))
    finally:
        eng.dispose()
    command.upgrade(_alembic(url_text), "head")


def _admin():
    """One AUTOCOMMIT admin connection on the base database, held as the run lease."""
    if "admin" not in _state:
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        run = os.environ[RUN_ENV]
        eng = create_engine(
            os.environ[BASE_ENV],
            poolclass=NullPool,
            isolation_level="AUTOCOMMIT",
            connect_args={"application_name": f"{LEASE_PREFIX}{run}"},
        )
        _state["admin_engine"] = eng
        _state["admin"] = eng.connect()
    return _state["admin"]


def _quote(name: str) -> str:
    assert re.fullmatch(r"[a-z0-9_]+", name), name
    return f'"{name}"'


def sweep_orphans() -> list[str]:
    """Drop run-owned databases of runs that hold no live session. Returns the names dropped."""
    from sqlalchemy import text
    from sqlalchemy.engine import make_url

    admin = _admin()
    stem = _stem(make_url(os.environ[BASE_ENV]).database)
    pattern = _owned_pattern(stem)
    current = os.environ[RUN_ENV]
    names = list(admin.execute(text("SELECT datname FROM pg_database")).scalars())
    by_run: dict[str, list[str]] = {}
    for name in names:
        match = pattern.match(name)
        if match and match.group(1) != current:
            by_run.setdefault(match.group(1), []).append(name)
    dropped = []
    for run, owned in by_run.items():
        live = admin.execute(
            text(
                "SELECT count(*) FROM pg_stat_activity "
                "WHERE application_name = :lease OR datname = ANY(:owned)"
            ),
            {"lease": f"{LEASE_PREFIX}{run}", "owned": owned},
        ).scalar_one()
        if live:
            continue
        for name in owned:
            try:
                admin.execute(text(f"DROP DATABASE IF EXISTS {_quote(name)}"))
                dropped.append(name)
            except Exception:  # a session appeared in between: leave it for a later sweep
                pass
    return dropped


def _names() -> tuple[str, str]:
    from sqlalchemy.engine import make_url

    stem = _stem(make_url(os.environ[BASE_ENV]).database)
    run = os.environ[RUN_ENV]
    return database_name(stem, run, "tpl"), database_name(stem, run, os.environ[TAG_ENV])


def _create(name: str, template: str | None = None) -> None:
    from sqlalchemy import text

    clause = f" TEMPLATE {_quote(template)}" if template else ""
    strategy = os.environ.get(STRATEGY_ENV, "").upper()
    if strategy:
        assert strategy in {"WAL_LOG", "FILE_COPY"}, strategy
        clause += f" STRATEGY {strategy}"
    admin = _admin()
    admin.execute(text(f"CREATE DATABASE {_quote(name)}{clause}"))
    sync = os.environ.get(SYNC_COMMIT_ENV)
    if sync:
        assert sync in {"on", "off", "local", "remote_write", "remote_apply"}, sync
        admin.execute(text(f"ALTER DATABASE {_quote(name)} SET synchronous_commit = {sync}"))


def _ensure_template() -> str:
    from alembic import command
    from sqlalchemy import text
    from sqlalchemy.engine import make_url

    template, _ = _names()
    if _state.get("template") == template:
        return template
    _guard(os.environ[BASE_ENV])
    _state["swept"] = sweep_orphans()
    admin = _admin()
    admin.execute(text(f"DROP DATABASE IF EXISTS {_quote(template)} WITH (FORCE)"))
    _create(template)
    template_url = make_url(os.environ[BASE_ENV]).set(database=template).render_as_string(hide_password=False)
    command.upgrade(_alembic(template_url), "head")  # migrations/env.py uses NullPool: no session survives
    # A template that accepts no connections cannot be dirtied between clones.
    admin.execute(text(f"ALTER DATABASE {_quote(template)} WITH ALLOW_CONNECTIONS false"))
    _state["template"] = template
    return template


def fresh_database() -> str:
    """Give the caller a freshly migrated database at `ASSETOPS_TEST_DATABASE_URL` and return that URL."""
    url_text = os.environ[ENV]
    _guard(url_text)
    if not routed():
        _reset_in_place(url_text)
        return url_text
    from sqlalchemy import text

    template = _ensure_template()
    _, worker = _names()
    admin = _admin()
    admin.execute(text(f"DROP DATABASE IF EXISTS {_quote(worker)} WITH (FORCE)"))
    _create(worker, template)
    _state["clones"] = _state.get("clones", 0) + 1
    return url_text


CLEANUP_ENV = "ASSETOPS_TEST_CLEANUP"  # "delete" (default) or "truncate"
_CASCADE_CLOSURE = """
WITH RECURSIVE closure(oid) AS (
    SELECT unnest(CAST(:roots AS regclass[]))::oid
    UNION
    SELECT c.conrelid FROM pg_constraint c JOIN closure ON c.confrelid = closure.oid WHERE c.contype = 'f'
)
SELECT relname FROM pg_class WHERE oid IN (SELECT oid FROM closure) ORDER BY relname
"""


def empty_tables(engine, roots: tuple[str, ...]) -> None:
    """Empty exactly the tables `TRUNCATE <roots> CASCADE` would empty, without TRUNCATE.

    Why. On this Docker Desktop host TRUNCATE gives every table a new file and
    rebuilds every index, and on PostgreSQL 16 each rebuilt index ends in a
    forced data-file sync (`DataFileImmediateSync`). Measured per call: about
    1.4 s quiet and 22-25 s under disk pressure, against 0.14 s for this. The
    content result is the same: the same FK closure of tables ends empty;
    sequences are not reset by either; no TRUNCATE triggers exist. Row triggers
    and FK checks are bypassed with `session_replication_role = replica`
    because TRUNCATE bypasses them too (append-only guards refuse DELETE).
    `ASSETOPS_TEST_CLEANUP=truncate` restores the TRUNCATE statement.
    """
    from sqlalchemy import text

    if os.environ.get(CLEANUP_ENV, "delete") == "truncate":
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {', '.join(roots)} CASCADE"))
        return
    with engine.begin() as connection:
        tables = list(connection.execute(text(_CASCADE_CLOSURE), {"roots": list(roots)}).scalars())
        connection.execute(text("SET LOCAL session_replication_role = replica"))
        for table in tables:
            connection.execute(text(f"DELETE FROM {_quote(table)}"))


def dispose(*holders) -> None:
    """Dispose the SQLAlchemy engine each store or engine holds, if it opened one."""
    for holder in holders:
        engine = holder if hasattr(holder, "dispose") and hasattr(holder, "connect") else getattr(holder, "_engine", None)
        if engine is not None:
            engine.dispose()


def cleanup() -> None:
    """Drop this run's databases and release the lease. Safe to call when nothing was provisioned."""
    if "admin" not in _state:
        return
    from sqlalchemy import text

    admin = _state["admin"]
    try:
        for name in reversed(_names()):
            admin.execute(text(f"DROP DATABASE IF EXISTS {_quote(name)} WITH (FORCE)"))
    finally:
        admin.close()
        _state["admin_engine"].dispose()
        for key in ("admin", "admin_engine", "template"):
            _state.pop(key, None)
