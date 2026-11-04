"""MD-0 L3m (build sheet §6, as reduced by Architect MD0-S2 to KOBO-001): the mechanism dataset in its own DB.

    python tools/mechanism_dataset.py build [--day-set full|states] [--budget 540]   # new DB, then seed parts
    python tools/mechanism_dataset.py build --resume [--budget 540]                  # continue the seed
    python tools/mechanism_dataset.py drop                                           # the DB and var/mechanism/

- The DB is `assetops_mechanism_test` (variant main). `--variant close` is MD-0b (MD0-PF Q3) and is refused.
- `build` drops and recreates only that name, migrates it to head, then runs `mechanism_dataset.seed_steps` in
  order, saving the seed state after every step to `var/mechanism/seed-state.json`. It stops before a step that
  would pass `--budget` seconds and exits 3 ("resume"), so no process runs past the 600 s foreground cap. The last
  step writes the work folder (`build_work`: story.json, days.json, keys.json, expected-threads.json) and prints the
  timings and `pg_database_size`. It is not ticked (§6); `chain_clone.py settle mechanism` ticks it.
- `drop` removes the DB and `var/mechanism/` only when that folder carries the marker file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("backend", "backend/tests", "contracts", "gateway", "simulator", "host", "host/tests", "tools"):
    if str(REPO / _p) not in sys.path:
        sys.path.append(str(REPO / _p))

PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
NAME_RE = re.compile(r"^assetops_mechanism(_close)?_test$")
REFUSED = ("assetops_polish_full_test", "assetops_demo3_full_test")
MARKER = ".mechanism-work"
EXIT_RESUME = 3


class Refused(SystemExit):
    pass


def db_name(variant: str) -> str:
    if variant != "main":
        raise Refused(f"refused: variant {variant!r} is MD-0b (MD0-PF Q3)")
    name = "assetops_mechanism_test"
    if not NAME_RE.fullmatch(name) or name in REFUSED or name.startswith(("assetops_polish", "assetops_demo")):
        raise Refused(f"refused: {name!r}")
    return name


def db_url(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise Refused(f"refused: {name!r} does not match {NAME_RE.pattern}")
    return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{name}"


def work_dir(variant: str) -> Path:
    db_name(variant)
    return REPO / "var" / "mechanism"


def _admin():
    import psycopg

    return psycopg.connect(PG_ADMIN, autocommit=True)


def _recreate(name: str) -> None:
    from alembic import command

    import pg_harness

    with _admin() as c:
        c.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        c.execute(f'CREATE DATABASE "{name}"')
    command.upgrade(pg_harness._alembic(db_url(name)), "head")


def _point_env(url: str) -> None:
    """The s6 harness and `app_client` read the module-global test URL: point it at the mechanism DB before any
    test module is imported."""
    os.environ["ASSETOPS_TEST_DATABASE_URL"] = os.environ["DATABASE_URL"] = url
    for k in ("ASSETOPS_TEST_RUN_ID", "ASSETOPS_TEST_DATABASE_BASE_URL"):
        os.environ.pop(k, None)


def build(variant: str, day_set: str | None, budget: float, resume: bool) -> int:
    name, work = db_name(variant), work_dir(variant)
    url = db_url(name)
    state_path = work / "seed-state.json"
    if resume:
        if not (work / MARKER).is_file() or not state_path.is_file():
            raise Refused(f"refused: nothing to resume in {work}")
        saved = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        if work.exists():
            _remove_work(work)
        work.mkdir(parents=True)
        (work / MARKER).write_text("MD-0 mechanism work folder (tools/mechanism_dataset.py)\n", encoding="utf-8")
        t0 = time.perf_counter()
        _recreate(name)
        saved = {"day_set": day_set or "full", "done": [], "state": None,
                 "timings": {"create+migrate": round(time.perf_counter() - t0, 1)}}
        state_path.write_text(json.dumps(saved, indent=1), encoding="utf-8")
    _point_env(url)
    from sqlalchemy import create_engine

    import mechanism_dataset as md
    import pg_harness
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    steps = md.seed_steps(md.load(), saved["day_set"])
    todo = [s for s in steps if s not in saved["done"]]
    started, longest = time.perf_counter(), max([v for k, v in saved["timings"].items() if k in steps] or [60.0])
    engine, store = create_engine(url), PostgresFoundationStore(url)
    try:
        for step in todo:
            if saved["done"] and time.perf_counter() - started + longest > budget:
                print(f"budget: stopping before {step} ({len(saved['done'])}/{len(steps)} steps done); "
                      f"resume with: python tools/mechanism_dataset.py build --resume")
                return EXIT_RESUME
            state = md.seed_part(store, engine, saved["day_set"], [step], saved["state"], work / "tmp")
            saved["state"], saved["done"] = state, saved["done"] + [step]
            saved["timings"][step] = state["timings"][step]
            longest = max(longest, state["timings"][step])
            state_path.write_text(json.dumps(saved, indent=1, default=str), encoding="utf-8")
            print(f"{step}: {state['timings'][step]}s", flush=True)
        manifest = saved["state"]["manifest"]
        md.build_work(url, work, manifest, variant)
        (work / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        with engine.connect() as c:
            from sqlalchemy import text

            size = c.execute(text("SELECT pg_database_size(current_database())")).scalar_one()
    finally:
        pg_harness.dispose(store)
        engine.dispose()
    seed_seconds = round(sum(v for k, v in saved["timings"].items() if k in steps), 1)
    print(json.dumps({"db": name, "day_set": saved["day_set"], "seed_seconds": seed_seconds,
                      "create_migrate_seconds": saved["timings"].get("create+migrate"),
                      "db_bytes": size, "readings": manifest["readings"], "batches": manifest["batches"]}))
    return 0


def _remove_work(work: Path) -> None:
    if not (work / MARKER).is_file():
        raise Refused(f"refused: {work} has no {MARKER} marker; not removing it")
    shutil.rmtree(work)


def drop(variant: str) -> int:
    name, work = db_name(variant), work_dir(variant)
    with _admin() as c:
        c.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    print(f"dropped {name}")
    if work.exists():
        _remove_work(work)
        print(f"removed {work}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python tools/mechanism_dataset.py")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--variant", default="main")
    b.add_argument("--day-set", choices=("full", "states"))
    b.add_argument("--budget", type=float, default=540.0)
    b.add_argument("--resume", action="store_true")
    d = sub.add_parser("drop")
    d.add_argument("--variant", default="main")
    args = parser.parse_args(argv)
    if args.command == "build":
        return build(args.variant, args.day_set, args.budget, args.resume)
    return drop(args.variant)


if __name__ == "__main__":
    raise SystemExit(main())
