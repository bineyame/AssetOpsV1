"""CH-0 U2 (build sheet §3.4): the L3 clone helper for the chain coherence check.

    python tools/chain_clone.py create <name> [--migrate]   # assetops_chainclone_<name>_test FROM TEMPLATE the polish DB
    python tools/chain_clone.py settle <name>                # S2 comparison + one bounded tick on the clone (CH3-R)
    python tools/chain_clone.py drop   <name>                   # the clone and exactly the files settle created

The source is the fixed constant `SOURCE_DB`; there is no option to change it. The target must match
`TARGET_RE`. `create` refuses while the source has any other session (it never terminates one); `--migrate` upgrades
the clone to this worktree's Alembic head the way `tools/demo_combined.py` `prepare` does. `drop` removes only a
name matching the pattern. `settle` (ruling CH3-R, the L3 settle step) first runs prepare's Kobo S2 comparison
(`evidence_migration run`, as `tools/demo_combined.py` does) on the clone, then ONE scheduler tick with the serve's
tick arguments (`demo_combined.TICK`), then the serve's Kobo performance step, so the producers are settled before a
collect. It runs this worktree's code and needs no work dir. CH3-R M2: the comparison record is a file under this
worktree's gitignored `var/` (bound to this tree), so `settle` records every file it created under `var/` in
`var/chainclone_<name>/created.json`, and `drop` deletes exactly those files (and the directories it created), never
a file that existed before. It refuses any name that is not an `assetops_chainclone_*_test` clone, so it can never
tick the polish DB or any other database. The tool never serves or writes anything else.
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
#: MD-0 (P7): `settle` alone also accepts the two mechanism DBs (`tools/mechanism_dataset.py`), by these names.
MECHANISM_RE = re.compile(r"^assetops_mechanism(_close)?_test$")
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


def settle_db(name: str) -> str:
    """The database `settle` ticks: a chain clone, or (MD-0 P7) `mechanism` / `mechanism_close`. create and drop
    keep `target_db`, so they never touch a mechanism DB."""
    if name in ("mechanism", "mechanism_close"):
        db = f"assetops_{name}_test"
        assert MECHANISM_RE.fullmatch(db)
        return db
    return target_db(name)


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


#: CH3-R M2: prepare's S2 comparison (`demo_combined.Demo.finish`), which writes the Kobo comparison record.
COMPARISON = ("-m", "assetops_backend.evidence_migration", "run", "--tenant", "demo", "--site", "KOBO-001")
#: The serve's performance step after each tick (`demo_combined.Demo.tick`).
PERFORMANCE = ("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", "KOBO-001")
#: Per-child wall cap: twice the scheduler's own `TickLimits.tick_seconds` (240 s).
SETTLE_CAP_SECONDS = 480
_PATHS = ("backend", "backend/tests", "contracts", "gateway", "simulator", "host", "host/tests", "gateway/tests",
          "tools")


def settle_env(name: str) -> dict[str, str]:
    """The serve's tick environment, pointed at the clone only (`clone_url` refuses a non-clone name)."""
    import os

    url = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{settle_db(name)}"
    out = dict(os.environ)
    out["PYTHONPATH"] = os.pathsep.join(str(REPO / p) for p in _PATHS)
    out["DATABASE_URL"] = out["ASSETOPS_TEST_DATABASE_URL"] = url
    out["PYTHONUNBUFFERED"] = "1"
    for k in ("ASSETOPS_TEST_RUN_ID", "ASSETOPS_TEST_DATABASE_BASE_URL", *KEY_NAMES):
        out.pop(k, None)
    return out


SETTLE_STEPS = (("s2-comparison", COMPARISON), ("tick", TICK), ("performance", PERFORMANCE))
VAR = REPO / "var"


def _run_child(label: str, argv: tuple[str, ...], env: dict[str, str], name: str) -> int:
    import subprocess
    import time

    started = time.monotonic()
    proc = subprocess.Popen([sys.executable, *argv], cwd=str(REPO), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    print(f"{label}: PID {proc.pid} on {settle_db(name)}", flush=True)
    try:
        out, _ = proc.communicate(timeout=SETTLE_CAP_SECONDS)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        raise SystemExit(f"WALL CAP {SETTLE_CAP_SECONDS}s reached during {label}; stopped PID {proc.pid}")
    last = (out.strip().splitlines() or ["(no output)"])[-1]
    print(f"{label}: exit {proc.returncode} in {time.monotonic() - started:.0f}s: {masked(last)[:400]}")
    return proc.returncode


def created_record(name: str, var: Path = VAR) -> Path:
    """`var/chainclone_<name>/created.json` (the name is checked first; `settle_db` also admits the mechanism
    names, so `drop` of a chain clone and `settle` of a mechanism DB share the record rule)."""
    settle_db(name)
    return var / f"chainclone_{name}" / "created.json"


def _tree(var: Path) -> tuple[set[str], set[str]]:
    """(files, directories) under `var`, as POSIX paths relative to it."""
    files: set[str] = set()
    dirs: set[str] = set()
    if var.is_dir():
        for p in var.rglob("*"):
            (files if p.is_file() else dirs).add(p.relative_to(var).as_posix())
    return files, dirs


def settle(name: str, var: Path = VAR, run=_run_child) -> int:
    """The S2 comparison, one bounded tick and the performance step on the clone; prints each child's PID and last
    output line, and records the files the steps created under `var/` (CH3-R M2), also when a step fails."""
    import json

    env = settle_env(name)  # refuses first, before any process starts
    record = created_record(name, var)
    before_files, before_dirs = _tree(var)
    worst = 0
    try:
        for label, argv in SETTLE_STEPS:
            worst = max(worst, run(label, argv, env, name))
    finally:
        after_files, after_dirs = _tree(var)
        prior = json.loads(record.read_text(encoding="utf-8")) if record.is_file() else {"files": [], "dirs": []}
        own = {record.relative_to(var).as_posix(), record.parent.relative_to(var).as_posix()}
        made = {"files": sorted(set(prior["files"]) | (after_files - before_files - own)),
                "dirs": sorted(set(prior["dirs"]) | (after_dirs - before_dirs - own))}
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps(made, indent=2), encoding="utf-8")
        print(f"settle: {len(made['files'])} file(s) created under var/, recorded in {record}")
    return worst


def cleanup(name: str, var: Path = VAR) -> list[str]:
    """Deletes exactly the files (then the emptied directories) `settle` recorded as created, and the record. A
    recorded path outside `var` is refused. Returns the deleted file paths."""
    import json

    record = created_record(name, var)
    if not record.is_file():
        return []
    made = json.loads(record.read_text(encoding="utf-8"))
    root = var.resolve()
    paths = [(rel, (var / rel).resolve()) for rel in made.get("files", [])]
    for rel, p in paths:  # refuse before deleting anything
        if p == root or not p.is_relative_to(root):
            raise CloneRefused(f"refused: recorded path {rel!r} is outside {var}")
    deleted = []
    for rel, p in paths:
        if p.is_file():
            p.unlink()
            deleted.append(rel)
    for rel in sorted(made.get("dirs", []), key=lambda r: r.count("/"), reverse=True):
        p = (var / rel).resolve()
        if p != root and p.is_relative_to(root) and p.is_dir() and not any(p.iterdir()):
            p.rmdir()
    record.unlink()
    if not any(record.parent.iterdir()):
        record.parent.rmdir()
    return deleted


def drop(name: str) -> None:
    sql = drop_sql(name)
    with _admin() as c:
        c.execute(sql)
    print(f"dropped {target_db(name)}")
    gone = cleanup(name)
    print(f"deleted {len(gone)} file(s) settle created under var/")


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
