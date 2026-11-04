"""MD-0 L3m and the input template (build sheet §6; MD0-S2 Kobo only; MD0-S3 Q1 template DB).

    python tools/mechanism_dataset.py build --variant states [--budget 540] [--resume]  # the input template
    python tools/mechanism_dataset.py build --variant full [--budget 540] [--resume]    # the 14-day L3m DB
    python tools/mechanism_dataset.py build --variant close [--budget 540] [--resume]   # the close input template
    python tools/mechanism_dataset.py derive [--variant states|close]   # clone a template to its L3m DB, derive
    python tools/mechanism_dataset.py status        # the templates against this checkout's input writers
    python tools/mechanism_dataset.py ensure [--close auto|yes|no]  # reuse/build the main template; the close one on demand (MD0b-R)
    python tools/mechanism_dataset.py drop [--variant states|full|legacy]

- `states` builds the input template: every seed step but `derive` (INPUTS only) into a staging DB
  `assetops_mechanism_tplb_<hex8>_test`, then tags it with the input-writer fingerprint and the seed state and renames
  it `assetops_mechanism_tpl_<fp8>_test` (CH5a1-R3 M4: one template per fingerprint; the two newest are kept, older
  ones dropped, so main and a branch never overwrite each other). An unfinished build has no tag; a clone with no
  matching template is refused (`TEMPLATE_MISSING`, `TEMPLATE_STALE`).
- `ensure` is the suite runner's step: exit 0 when a matching template exists, else a fresh `states` build with no
  budget; any failure exits non-zero.
- `assetops_mechanism_tpl_test` is the legacy single template (MD-0, CH-5a1's branch). This tool never reads, prunes
  or replaces it; `drop --variant legacy` removes it once no branch uses it.
- The server is 127.0.0.1:$ASSETOPS_PG_PORT (55432), or the host and port of `ASSETOPS_MECHANISM_SERVER_URL` when set
  (the container runner: postgres-test:5432).
- `full` builds `assetops_mechanism_test` with the full day set, `derive` included, then the work folder; it runs at
  the gates (G3, G4) and on demand, not per merge. `derive` gives the same L3m DB from the template in minutes.
- `--variant close` (MD-0b, build sheet §2.5) builds the close variant's input template the same way, named
  `assetops_mechanism_tplc_<fp8>_test`; `derive --variant close` clones it to `assetops_mechanism_close_test` with
  the work folder `var/mechanism_close/` for its L3m collect and check.
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
SERVER_URL = os.environ.get("ASSETOPS_MECHANISM_SERVER_URL")
NAME_RE = re.compile(r"^assetops_mechanism(_close|_tpl|_tplb_[0-9a-f]{8})?_test$")
LEGACY = "assetops_mechanism_tpl_test"
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


#: name None = the staging name of this build, chosen at build start and kept in the seed state for a resume (M4)
VARIANTS = {"states": (None, "mechanism-tpl", "states"),
            "close": (None, "mechanism-close-tpl", "close"),
            "full": ("assetops_mechanism_test", "mechanism", "full")}
#: `derive`: the template's day set -> (the L3m DB, its work folder)
DERIVED = {"states": ("assetops_mechanism_test", "mechanism"),
           "close": ("assetops_mechanism_close_test", "mechanism_close")}
#: the input templates the L2m tests clone (MD-0b: the close variant's too)
TEMPLATED = ("states", "close")


def _checked(name: str) -> str:
    if not NAME_RE.fullmatch(name) or name in REFUSED or name.startswith(("assetops_polish", "assetops_demo")):
        raise Refused(f"refused: {name!r}")
    return name


def staging_name() -> str:
    return _checked(f"assetops_mechanism_tplb_{os.urandom(4).hex()}_test")


def db_name(variant: str) -> str | None:
    if variant not in VARIANTS:
        raise Refused(f"refused: variant {variant!r} (known: {', '.join(VARIANTS)})")
    name = VARIANTS[variant][0]
    return None if name is None else _checked(name)


def server_url(name: str) -> str:
    """A database on the mechanism server, as the URL the tool connects with (no name check)."""
    if SERVER_URL:
        from sqlalchemy.engine import make_url

        return make_url(SERVER_URL).set(drivername="postgresql+psycopg", database=name).render_as_string(
            hide_password=False)
    return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{name}"


def db_url(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise Refused(f"refused: {name!r} does not match {NAME_RE.pattern}")
    return server_url(name)


def work_dir(variant: str) -> Path:
    db_name(variant)
    return REPO / "var" / VARIANTS[variant][1]


def _admin():
    import psycopg

    if SERVER_URL:
        from sqlalchemy.engine import make_url

        return psycopg.connect(make_url(SERVER_URL).set(drivername="postgresql", database="postgres")
                               .render_as_string(hide_password=False), autocommit=True)
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


def _estimate(timings: dict, steps: list[str], step: str) -> float:
    """The seconds a step is expected to take: its own earlier time, else the longest ordinary step seen (the drain
    is excluded from that, it runs alone), else 60."""
    if step in timings:
        return timings[step]
    return max([v for k, v in timings.items() if k in steps and k != "drain_mini"] or [60.0])


def build(variant: str, budget: float, resume: bool) -> int:
    name, work = db_name(variant), work_dir(variant)
    day_set = VARIANTS[variant][2]
    state_path = work / "seed-state.json"
    if resume:
        if not (work / MARKER).is_file() or not state_path.is_file():
            raise Refused(f"refused: nothing to resume in {work}")
        saved = json.loads(state_path.read_text(encoding="utf-8"))
        if name is None:
            if not saved.get("db") or saved.get("published"):
                raise Refused(f"refused: {state_path} names no unfinished staging database; start a fresh build: "
                              f"python tools/mechanism_dataset.py build --variant {variant}")
            name = _checked(saved["db"])
    else:
        if name is None and work.exists():
            _drop_staging(work)  # an abandoned staging build of this work folder
        _fresh_work(work)
        name = name or staging_name()
        t0 = time.perf_counter()
        _recreate(name)  # an untagged DB: refused as a template until every input step has run
        saved = {"db": name, "day_set": day_set, "done": [], "state": None,
                 "timings": {"create+migrate": round(time.perf_counter() - t0, 1)}}
        state_path.write_text(json.dumps(saved, indent=1), encoding="utf-8")
    url = db_url(name)
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
    templated = VARIANTS[variant][0] is None  # states and close: an input template (no derive)
    steps = md.input_steps(spec, day_set) if templated else md.seed_steps(spec, day_set)
    todo = [s for s in steps if s not in saved["done"]]
    started, part_done = time.perf_counter(), 0
    engine, store = create_engine(url), PostgresFoundationStore(url)
    try:
        for step in todo:
            # MD0b-R (Known deviation 5): the drain runs in its own part, so a part that ends at D14 is never
            # followed by the 335-430 s drain inside one foreground budget; its own time is its estimate.
            if budget != float("inf") and part_done and (
                    step == "drain_mini" or time.perf_counter() - started + _estimate(saved["timings"], steps, step) > budget):
                print(f"budget: stopping before {step} ({len(saved['done'])}/{len(steps)} steps done); "
                      f"resume with: python tools/mechanism_dataset.py build --variant {variant} --resume")
                return EXIT_RESUME
            state = md.seed_part(store, engine, day_set, [step], saved["state"], work / "tmp")
            saved["state"], saved["done"] = state, saved["done"] + [step]
            saved["inputs"] = md.record_inputs(saved["inputs"])  # MD0-S5 M1: the modules this step loaded
            saved["timings"][step] = state["timings"][step]
            part_done += 1
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
           "readings": saved["state"]["site"]["readings"], "batches": saved["state"]["site"]["batches"],
           "step_seconds": {k: v for k, v in saved["timings"].items() if k in steps}}  # MD0b-R: per-step seed timings
    if templated:
        admin = md.admin_engine(url)
        try:
            if changed := md.inputs_changed(saved["inputs"]):
                raise Refused(f"refused: TEMPLATE_INPUTS_CHANGED during the build: {changed[:5]}; not tagged")
            tag = md.make_tag(saved["state"], day_set, modules=list(saved["inputs"]),
                              fingerprint=md.fingerprint_of(saved["inputs"]))
            out["db"], out["dropped"] = md.publish_template(admin, name, tag)
        finally:
            admin.dispose()
        out["fingerprint"] = tag["fingerprint"]
        saved["published"] = out["db"]
        state_path.write_text(json.dumps(saved, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out))
    return 0


def derive(variant: str = "states") -> int:
    """MD0-S3 Q1 on the L3m DB: clone the template (refused when missing or stale), derive with this checkout's
    code, write the work folder. Prints the clone and derive times and `pg_database_size`. MD-0b: `close` clones the
    close template to `assetops_mechanism_close_test`."""
    if variant not in DERIVED:
        raise Refused(f"refused: derive variant {variant!r} (known: {', '.join(DERIVED)})")
    name, work = _checked(DERIVED[variant][0]), REPO / "var" / DERIVED[variant][1]
    url = db_url(name)
    _point_env(url)
    md = _harness()

    admin = md.admin_engine(url)
    try:
        t0 = time.perf_counter()
        try:
            template = md.find_template(admin, day_set=variant)
            tag = md.clone_template(admin, name, template)
        except md.MechanismRefused as refused:
            raise Refused(f"refused: {refused}") from None
        clone_s = round(time.perf_counter() - t0, 1)
    finally:
        admin.dispose()
    _fresh_work(work)
    t0 = time.perf_counter()
    manifest = md.derive_clone(url, tag, work / "tmp")
    derive_s = round(time.perf_counter() - t0, 1)
    md.build_work(url, work, manifest, manifest["variant"])
    (work / "manifest.json").write_text(json.dumps(manifest, indent=1, default=str), encoding="utf-8")
    from sqlalchemy import create_engine

    engine = create_engine(url)
    try:
        size = _size(engine)
    finally:
        engine.dispose()
    print(json.dumps({"db": name, "from": template, "day_set": tag["day_set"], "clone_seconds": clone_s,
                      "derive_seconds": derive_s, "db_bytes": size, "fingerprint": tag["fingerprint"]}))
    return 0


def _match(day_set: str = "states") -> tuple[str | None, list[dict], bool]:
    """(the template matching this checkout or None, every per-fingerprint template, legacy template present)."""
    md = _harness()

    admin = md.admin_engine(server_url("postgres"))
    try:
        found = [{"db": n, "tagged": t is not None, "fingerprint": t and t["fingerprint"],
                  "built_at": t and t.get("built_at")} for n, t in md.templates(admin, day_set)]
        try:
            match = md.find_template(admin, day_set=day_set)
        except md.MechanismRefused:
            match = None
        legacy = md.read_tag(admin, LEGACY) is not None
    finally:
        admin.dispose()
    return match, found, legacy


def status() -> int:
    usable = True
    for day_set in TEMPLATED:
        match, found, legacy = _match(day_set)
        usable &= match is not None
        print(json.dumps({"variant": day_set, "usable": match is not None, "template": match, "templates": found,
                          "legacy_template_present": legacy}))
    return 0 if usable else 1


#: MD0b-R: a slice that touches one of these needs the close template (the close L2m test clones it)
CLOSE_PATH_RE = re.compile(
    r"^(backend/assetops_backend/chain/(lifecycle[^/]*\.py|threads\.py)"
    r"|backend/assetops_backend/chain/adapters/postgres_thread_store\.py"
    r"|config/chain/thread-lifecycle-v1\.json"
    r"|backend/tests/mechanism_dataset\.py|tools/mechanism_dataset\.py)$")
FIXTURE = "backend/conversions/mechanism-v1.json"
CLOSE_TEST = ("backend/tests/test_md0_mechanism_postgres.py::"
              "test_close_variant_resolves_closes_after_seven_clean_days_and_recurs")


def close_needed(paths: list[str], base_fixture: str | None, now_fixture: str | None) -> list[str]:
    """The reasons the slice needs the close template (empty: it does not). `paths` are the slice's changed files;
    the fixture counts only when its `variants.close` differs from the base's."""
    reasons = [p for p in paths if CLOSE_PATH_RE.match(p)]
    if FIXTURE in paths:
        try:
            same = json.loads(base_fixture)["variants"]["close"] == json.loads(now_fixture)["variants"]["close"]
        except (TypeError, ValueError, KeyError):
            same = False  # unreadable either side: treat as changed
        if not same:
            reasons.append(f"{FIXTURE} (variants.close)")
    return reasons


def _git(*args: str) -> str | None:
    import subprocess

    try:
        r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def slice_inputs(paths_file: str | None, base_fixture_file: str | None) -> tuple[list[str] | None, str | None, str | None]:
    """(changed paths, base fixture text, current fixture text), or paths None when the slice diff cannot be read.
    The host runner writes the two files (the container has no usable git); otherwise git is asked directly."""
    now = (REPO / FIXTURE).read_text(encoding="utf-8") if (REPO / FIXTURE).is_file() else None
    if paths_file and Path(paths_file).is_file():
        base = Path(base_fixture_file).read_text(encoding="utf-8-sig") if base_fixture_file and Path(base_fixture_file).is_file() else None
        return [p.strip() for p in Path(paths_file).read_text(encoding="utf-8-sig").splitlines() if p.strip()], base, now
    for ref in ("main", "origin/main"):
        base_sha = (_git("merge-base", "HEAD", ref) or "").strip()
        if base_sha:
            out = _git("diff", "--name-only", base_sha)  # committed and uncommitted changes since the base
            if out is not None:
                return [p for p in out.splitlines() if p], _git("show", f"{base_sha}:{FIXTURE}"), now
    return None, None, now


def ensure(close: str = "auto", paths_file: str | None = None, base_fixture_file: str | None = None) -> int:
    """The suite runner's step (FIX-MAIN-1): reuse each matching template, else build it now, with no budget.
    MD0b-R: the main template always; the close template only when `close` is `yes`, or `auto` and the slice
    touches a close input (CLOSE_PATH_RE, `variants.close`), or it already matches (reuse costs nothing). When it is
    not selected this prints `ensure: close not selected` and the runner deselects the close test; never silent."""
    wanted = ["states"]
    paths, base_fx, now_fx = (None, None, None) if close != "auto" else slice_inputs(paths_file, base_fixture_file)
    if close == "yes":
        wanted.append("close")
        print("ensure: close template requested explicitly", flush=True)
    elif close == "auto":
        match, _, _ = _match("close")
        reasons = None if paths is None else close_needed(paths, base_fx, now_fx)
        if match:
            wanted.append("close")
        elif paths is None:
            wanted.append("close")
            print("ensure: the slice diff cannot be read; building the close template to be safe", flush=True)
        elif reasons:
            wanted.append("close")
            print(f"ensure: the slice touches close inputs ({', '.join(reasons[:4])}); building the close template",
                  flush=True)
    if "close" not in wanted:
        print(json.dumps({"ensure": "close not selected", "deselect": CLOSE_TEST,
                          "why": "the slice touches no close input; pass --close yes (E1/E4, the post-merge job) to run it"}),
              flush=True)
    for day_set in wanted:
        match, _, _ = _match(day_set)
        if match:
            print(json.dumps({"ensure": "reused", "variant": day_set, "template": match}))
            continue
        print(f"ensure: no {day_set} template matches this checkout; building one (15-25 min)", flush=True)
        code = build(day_set, float("inf"), False)
        if code != 0:
            raise Refused(f"refused: TEMPLATE_BUILD_FAILED ({day_set} build exit {code})")
        match, _, _ = _match(day_set)
        if not match:
            raise Refused(f"refused: TEMPLATE_BUILD_FAILED: the new {day_set} template does not match this checkout")
        print(json.dumps({"ensure": "built", "variant": day_set, "template": match}))
    return 0


def _remove_work(work: Path) -> None:
    if not (work / MARKER).is_file():
        raise Refused(f"refused: {work} has no {MARKER} marker; not removing it")
    shutil.rmtree(work)


def _drop_staging(work: Path) -> None:
    """The unpublished staging DB a `states` work folder names, if any (a published one was renamed)."""
    state_path = work / "seed-state.json"
    if not state_path.is_file():
        return
    saved = json.loads(state_path.read_text(encoding="utf-8"))
    if saved.get("db") and not saved.get("published"):
        with _admin() as c:
            c.execute(f'DROP DATABASE IF EXISTS "{_checked(saved["db"])}" WITH (FORCE)')
        print(f"dropped {saved['db']}")


def drop(variant: str) -> int:
    if variant == "legacy":  # M4: only on request, once no branch clones the single MD-0 template
        with _admin() as c:
            c.execute(f'DROP DATABASE IF EXISTS "{LEGACY}" WITH (FORCE)')
        print(f"dropped {LEGACY}")
        return 0
    name, work = db_name(variant), work_dir(variant)
    if name is None:  # states: the staging build only; published templates are pruned by the next build
        _drop_staging(work)
    else:
        with _admin() as c:
            c.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        print(f"dropped {name}")
    if work.exists():
        _remove_work(work)
        print(f"removed {work}")
    if variant == "close":  # MD-0b: also the derived close L3m DB and its work folder (`derive --variant close`)
        derived, derived_work = _checked(DERIVED["close"][0]), REPO / "var" / DERIVED["close"][1]
        with _admin() as c:
            c.execute(f'DROP DATABASE IF EXISTS "{derived}" WITH (FORCE)')
        print(f"dropped {derived}")
        if derived_work.exists():
            _remove_work(derived_work)
            print(f"removed {derived_work}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python tools/mechanism_dataset.py")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--variant", default="states")
    b.add_argument("--budget", type=float, default=540.0)
    b.add_argument("--resume", action="store_true")
    dv = sub.add_parser("derive")
    dv.add_argument("--variant", default="states")
    sub.add_parser("status")
    e = sub.add_parser("ensure")
    e.add_argument("--close", choices=("auto", "yes", "no"), default=os.environ.get("ASSETOPS_MECHANISM_CLOSE", "auto"),
                   help="build the close template: yes (E1/E4, post-merge), auto (when the slice touches a close input)")
    e.add_argument("--slice-paths", default=os.environ.get("ASSETOPS_MECHANISM_SLICE_PATHS"))
    e.add_argument("--base-fixture", default=os.environ.get("ASSETOPS_MECHANISM_BASE_FIXTURE"))
    d = sub.add_parser("drop")
    d.add_argument("--variant", default="full")
    args = parser.parse_args(argv)
    if args.command == "build":
        return build(args.variant, args.budget, args.resume)
    if args.command == "derive":
        return derive(args.variant)
    if args.command == "status":
        return status()
    if args.command == "ensure":
        return ensure(args.close, args.slice_paths, args.base_fixture)
    return drop(args.variant)


if __name__ == "__main__":
    raise SystemExit(main())
