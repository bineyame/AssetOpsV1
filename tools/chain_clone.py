"""CH-0 U2 (build sheet §3.4): the L3 clone helper for the chain coherence check.

    python tools/chain_clone.py create <name> [--migrate]   # assetops_chainclone_<name>_test FROM TEMPLATE the polish DB
    python tools/chain_clone.py settle <name>                # one bounded scheduler tick on the clone (CH3-R)
    python tools/chain_clone.py drop   <name>

The source is the fixed constant `SOURCE_DB`; there is no option to change it. The target must match
`TARGET_RE`. `create` refuses while the source has any other session (it never terminates one); `--migrate` upgrades
the clone to this worktree's Alembic head the way `tools/demo_combined.py` `prepare` does. `drop` removes only a
name matching the pattern. `settle` (ruling CH3-R, the L3 settle step) runs ONE scheduler tick on the clone with
the serve's tick arguments (`demo_combined.TICK`), then the serve's Kobo performance step, so the producers are
settled before a collect; it runs this worktree's code, needs no work dir and writes no file (the output is captured
here, not logged into a work dir). It refuses any name that is not an `assetops_chainclone_*_test` clone, so it can
never tick the polish DB or any other database. The tool never serves or writes anything else.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from demo_combined import KEY_NAMES, PG_ADMIN, PG_PORT, PW, TICK  # noqa: E402 - as demo_combined makes them

SOURCE_DB = "assetops_polish_full_test"
TARGET_RE = re.compile(r"^assetops_chainclone_[a-z0-9]{1,20}_test$")
SESSIONS_SQL = ("SELECT count(*) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()")
BUSY = "stop serve and any client of the polish DB first"


class CloneRefused(SystemExit):
    pass


def target_db(name: str) -> str:
    """The clone database for a short name; refuses any name that does not make an `assetops_chainclone_*_test`."""
    db = f"assetops_chainclone_{name}_test"
    if not TARGET_RE.fullmatch(db):
        raise CloneRefused(f"refused: {db!r} does not match {TARGET_RE.pattern}")
    return db


def create_sql(name: str) -> str:
    db = target_db(name)
    return f'CREATE DATABASE "{db}" TEMPLATE "{SOURCE_DB}"'


def drop_sql(name: str) -> str:
    db = target_db(name)
    return f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)'


def clone_url(name: str, driver: str = "postgresql+psycopg") -> str:
    return f"{driver}://assetops:{PW}@127.0.0.1:{PG_PORT}/{target_db(name)}"


def _admin():
    import psycopg

    return psycopg.connect(PG_ADMIN, autocommit=True)


def create(name: str, migrate: bool) -> str:
    sql = create_sql(name)
    with _admin() as c:
        others = c.execute(SESSIONS_SQL, (SOURCE_DB,)).fetchone()[0]
        if others:
            raise CloneRefused(f"refused: {SOURCE_DB} has {others} other session(s); {BUSY}")
        c.execute(sql)
    print(f"created {target_db(name)} from {SOURCE_DB}")
    if migrate:
        sys.path.insert(0, str(REPO / "backend" / "tests"))
        import pg_harness
        from alembic import command

        command.upgrade(pg_harness._alembic(clone_url(name)), "head")
        print(f"migrated {target_db(name)} to head")
    print(masked(clone_url(name)))  # the password is never printed (CH-0 review L2)
    return clone_url(name)


def masked(url: str) -> str:
    """`url` with any password replaced by `***`."""
    return re.sub(r"(://[^:/@]*:)[^@]*@", r"\1***@", url)


#: The serve's performance step after each tick (`demo_combined.Demo.tick`).
PERFORMANCE = ("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", "KOBO-001")
#: Per-child wall cap: twice the scheduler's own `TickLimits.tick_seconds` (240 s).
SETTLE_CAP_SECONDS = 480
_PATHS = ("backend", "backend/tests", "contracts", "gateway", "simulator", "host", "host/tests", "gateway/tests",
          "tools")


def settle_env(name: str) -> dict[str, str]:
    """The serve's tick environment, pointed at the clone only (`clone_url` refuses a non-clone name)."""
    import os

    url = clone_url(name)
    out = dict(os.environ)
    out["PYTHONPATH"] = os.pathsep.join(str(REPO / p) for p in _PATHS)
    out["DATABASE_URL"] = out["ASSETOPS_TEST_DATABASE_URL"] = url
    out["PYTHONUNBUFFERED"] = "1"
    for k in ("ASSETOPS_TEST_RUN_ID", "ASSETOPS_TEST_DATABASE_BASE_URL", *KEY_NAMES):
        out.pop(k, None)
    return out


def settle(name: str) -> int:
    """One bounded tick plus the performance step on the clone; prints each child's PID and last output line."""
    import subprocess
    import time

    env = settle_env(name)  # refuses first, before any process starts
    worst = 0
    for label, argv in (("tick", TICK), ("performance", PERFORMANCE)):
        started = time.monotonic()
        proc = subprocess.Popen([sys.executable, *argv], cwd=str(REPO), env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        print(f"{label}: PID {proc.pid} on {target_db(name)}", flush=True)
        try:
            out, _ = proc.communicate(timeout=SETTLE_CAP_SECONDS)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            raise SystemExit(f"WALL CAP {SETTLE_CAP_SECONDS}s reached during {label}; stopped PID {proc.pid}")
        last = (out.strip().splitlines() or ["(no output)"])[-1]
        print(f"{label}: exit {proc.returncode} in {time.monotonic() - started:.0f}s: {masked(last)[:400]}")
        worst = max(worst, proc.returncode)
    return worst


def drop(name: str) -> None:
    sql = drop_sql(name)
    with _admin() as c:
        c.execute(sql)
    print(f"dropped {target_db(name)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python tools/chain_clone.py")
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("create")
    c.add_argument("name")
    c.add_argument("--migrate", action="store_true")
    st = sub.add_parser("settle")
    st.add_argument("name")
    d = sub.add_parser("drop")
    d.add_argument("name")
    args = parser.parse_args(argv)
    if args.command == "create":
        create(args.name, args.migrate)
    elif args.command == "settle":
        return settle(args.name)
    else:
        drop(args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
