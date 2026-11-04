"""MD-0 L3m and the input template (build sheet §6; MD0-S2 Kobo only; MD0-S3 Q1 template DB).

    python tools/mechanism_dataset.py build --variant states [--budget 540] [--resume]  # the input template
    python tools/mechanism_dataset.py build --variant full [--budget 540] [--resume]    # the 14-day L3m DB
    python tools/mechanism_dataset.py derive        # clone the template to the L3m DB, derive, write the work folder
    python tools/mechanism_dataset.py status        # the template tag against this checkout's input writers
    python tools/mechanism_dataset.py drop [--variant states|full]

- `states` builds `assetops_mechanism_tpl_test`: every seed step but `derive` (INPUTS only), then tags the DB with
  the input-writer fingerprint and the seed state (`mechanism_dataset.tag_template`). An unfinished build has no
  tag; a clone of an untagged or stale template is refused (`TEMPLATE_MISSING`, `TEMPLATE_STALE`).
- `full` builds `assetops_mechanism_test` with the full day set, `derive` included, then the work folder; it runs at
  the gates (G3, G4) and on demand, not per merge. `derive` gives the same L3m DB from the template in minutes.
- `--variant close` is MD-0b (MD0-PF Q3) and is refused.
- A build drops and recreates only its own name, migrates it to head, then runs the steps in order, saving the
  seed state after every step to its work folder. It stops before a step that would pass `--budget` seconds and
  exits 3 ("resume"), so no process runs past the 600 s foreground cap. The L3m DB is not ticked (§6);
  `chain_clone.py settle mechanism` ticks it.
- `drop` removes the DB and its work folder only when that folder carries the marker file.
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
NAME_RE = re.compile(r"^assetops_mechanism(_close|_tpl)?_test$")
REFUSED = ("assetops_polish_full_test", "assetops_demo3_full_test")
MARKER = ".mechanism-work"
EXIT_RESUME = 3


def _harness():
    """`backend/tests/mechanism_dataset.py`, loaded by path: this tool has the same module name and its folder is
    first on sys.path, so a plain import would find the tool itself. Registered under the harness name so the test
    modules the seed imports share it."""
    import importlib.util

    loaded = sys.modules.get("mechanism_dataset")
    if loaded is not None and Path(loaded.__file__).resolve() == REPO / "backend" / "tests" / "mechanism_dataset.py":
        return loaded
    spec = importlib.util.spec_from_file_location("mechanism_dataset", REPO / "backend" / "tests" / "mechanism_dataset.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["mechanism_dataset"] = module
    spec.loader.exec_module(module)
    return module


class Refused(SystemExit):
    pass


VARIANTS = {"states": ("assetops_mechanism_tpl_test", "mechanism-tpl", "states"),
            "full": ("assetops_mechanism_test", "mechanism", "full")}


def db_name(variant: str) -> str:
    if variant not in VARIANTS:
        raise Refused(f"refused: variant {variant!r} (close is MD-0b, MD0-PF Q3; known: {', '.join(VARIANTS)})")
    name = VARIANTS[variant][0]
    if not NAME_RE.fullmatch(name) or name in REFUSED or name.startswith(("assetops_polish", "assetops_demo")):
        raise Refused(f"refused: {name!r}")
    return name


def db_url(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise Refused(f"refused: {name!r} does not match {NAME_RE.pattern}")
    return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{name}"


def work_dir(variant: str) -> Path:
    db_name(variant)
    return REPO / "var" / VARIANTS[variant][1]


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


def _fresh_work(work: Path) -> None:
    if work.exists():
        _remove_work(work)
    work.mkdir(parents=True)
    (work / MARKER).write_text("MD-0 mechanism work folder (tools/mechanism_dataset.py)\n", encoding="utf-8")


def _size(engine) -> int:
    from sqlalchemy import text

    with engine.connect() as c:
        return c.execute(text("SELECT pg_database_size(current_database())")).scalar_one()


def build(variant: str, budget: float, resume: bool) -> int:
    name, work = db_name(variant), work_dir(variant)
    url, day_set = db_url(name), VARIANTS[variant][2]
    state_path = work / "seed-state.json"
    if resume:
        if not (work / MARKER).is_file() or not state_path.is_file():
            raise Refused(f"refused: nothing to resume in {work}")
        saved = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        _fresh_work(work)
        t0 = time.perf_counter()
        _recreate(name)  # an untagged DB: refused as a template until every input step has run
        saved = {"day_set": day_set, "done": [], "state": None,
                 "timings": {"create+migrate": round(time.perf_counter() - t0, 1)}}
        state_path.write_text(json.dumps(saved, indent=1), encoding="utf-8")
    _point_env(url)
    from sqlalchemy import create_engine

    md = _harness()
    import pg_harness
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    # MD0-S5 L2: the inputs are fingerprinted at build start and re-checked on every resume and before the tag; a
    # changed input refuses the resume (the template would mix rows written by two versions of its writers).
    if "inputs" not in saved:
        if resume:
            raise Refused("refused: TEMPLATE_INPUTS_CHANGED: this build's seed state has no start fingerprint; "
                          f"start a fresh build: python tools/mechanism_dataset.py build --variant {variant}")
        saved["inputs"] = md.record_inputs(md.input_hashes([]))
        state_path.write_text(json.dumps(saved, indent=1, default=str), encoding="utf-8")
    elif changed := md.inputs_changed(saved["inputs"]):
        raise Refused(f"refused: TEMPLATE_INPUTS_CHANGED since the build started: {changed[:5]} "
                      f"({len(changed)}); start a fresh build: python tools/mechanism_dataset.py build "
                      f"--variant {variant}")
    spec = md.load()
    steps = md.input_steps(spec, day_set) if variant == "states" else md.seed_steps(spec, day_set)
    todo = [s for s in steps if s not in saved["done"]]
    started, longest = time.perf_counter(), max([v for k, v in saved["timings"].items() if k in steps] or [60.0])
    engine, store = create_engine(url), PostgresFoundationStore(url)
    try:
        for step in todo:
            if saved["done"] and time.perf_counter() - started + longest > budget:
                print(f"budget: stopping before {step} ({len(saved['done'])}/{len(steps)} steps done); "
                      f"resume with: python tools/mechanism_dataset.py build --variant {variant} --resume")
                return EXIT_RESUME
            state = md.seed_part(store, engine, day_set, [step], saved["state"], work / "tmp")
            saved["state"], saved["done"] = state, saved["done"] + [step]
            saved["inputs"] = md.record_inputs(saved["inputs"])  # MD0-S5 M1: the modules this step loaded
            saved["timings"][step] = state["timings"][step]
            longest = max(longest, state["timings"][step])
            state_path.write_text(json.dumps(saved, indent=1, default=str), encoding="utf-8")
            print(f"{step}: {state['timings'][step]}s", flush=True)
        size = _size(engine)
        if variant == "full":
            manifest = saved["state"]["manifest"]
            md.build_work(url, work, manifest, "main")
            (work / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    finally:
        pg_harness.dispose(store)
        engine.dispose()
    seed_seconds = round(sum(v for k, v in saved["timings"].items() if k in steps), 1)
    out = {"db": name, "variant": variant, "day_set": day_set, "seed_seconds": seed_seconds,
           "create_migrate_seconds": saved["timings"].get("create+migrate"), "db_bytes": size,
           "readings": saved["state"]["site"]["readings"], "batches": saved["state"]["site"]["batches"]}
    if variant == "states":
        admin = md.admin_engine(url)
        try:
            if changed := md.inputs_changed(saved["inputs"]):
                raise Refused(f"refused: TEMPLATE_INPUTS_CHANGED during the build: {changed[:5]}; not tagged")
            tag = md.make_tag(saved["state"], day_set, modules=list(saved["inputs"]),
                              fingerprint=md.fingerprint_of(saved["inputs"]))
            md.tag_template(admin, tag, name)
        finally:
            admin.dispose()
        out["fingerprint"] = tag["fingerprint"]
    print(json.dumps(out))
    return 0


def derive() -> int:
    """MD0-S3 Q1 on the L3m DB: clone the template (refused when missing or stale), derive with this checkout's
    code, write the work folder. Prints the clone and derive times and `pg_database_size`."""
    name, work = db_name("full"), work_dir("full")
    url = db_url(name)
    _point_env(url)
    md = _harness()

    admin = md.admin_engine(url)
    try:
        t0 = time.perf_counter()
        try:
            tag = md.clone_template(admin, name)
        except md.MechanismRefused as refused:
            raise Refused(f"refused: {refused}") from None
        clone_s = round(time.perf_counter() - t0, 1)
    finally:
        admin.dispose()
    _fresh_work(work)
    t0 = time.perf_counter()
    manifest = md.derive_clone(url, tag, work / "tmp")
    derive_s = round(time.perf_counter() - t0, 1)
    md.build_work(url, work, manifest, "main")
    (work / "manifest.json").write_text(json.dumps(manifest, indent=1, default=str), encoding="utf-8")
    from sqlalchemy import create_engine

    engine = create_engine(url)
    try:
        size = _size(engine)
    finally:
        engine.dispose()
    print(json.dumps({"db": name, "from": md.TEMPLATE_DB, "day_set": tag["day_set"], "clone_seconds": clone_s,
                      "derive_seconds": derive_s, "db_bytes": size, "fingerprint": tag["fingerprint"]}))
    return 0


def status() -> int:
    md = _harness()

    admin = md.admin_engine(db_url(db_name("states")))
    try:
        tag = md.read_tag(admin)
    finally:
        admin.dispose()
    current = md.input_fingerprint(tag.get("modules") or ()) if tag else None
    usable = tag is not None and tag["fingerprint"] == current
    print(json.dumps({"template": md.TEMPLATE_DB, "tagged": tag is not None,
                      "template_fingerprint": tag and tag["fingerprint"], "checkout_fingerprint": current,
                      "usable": usable}))
    return 0 if usable else 1


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
    b.add_argument("--variant", default="states")
    b.add_argument("--budget", type=float, default=540.0)
    b.add_argument("--resume", action="store_true")
    sub.add_parser("derive")
    sub.add_parser("status")
    d = sub.add_parser("drop")
    d.add_argument("--variant", default="full")
    args = parser.parse_args(argv)
    if args.command == "build":
        return build(args.variant, args.budget, args.resume)
    if args.command == "derive":
        return derive()
    if args.command == "status":
        return status()
    return drop(args.variant)


if __name__ == "__main__":
    raise SystemExit(main())
