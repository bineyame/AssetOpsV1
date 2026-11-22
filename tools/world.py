"""DS4 (spec `specs/DS4-template-ladder/spec.md`; D-DS4.1 to D-DS4.25): the demonstration world as a template ladder.

    python tools/world.py build --key-root DIR      L0 schema, L1 inputs, L2 computed; each rebuilt only when its key changes
    python tools/world.py clone --label L           a run's database, cloned from the current L2
    python tools/world.py reset --label L           drop that clone, then clone it again
    python tools/world.py check                     the world check on a check clone (C1 to C7)
    python tools/world.py list                      the manifests and whether each database exists
    python tools/world.py drop --database NAME      one database the tool built, children first
    python tools/world.py bench --key-root DIR --evidence DIR   the re-benchmark (spec §4); every bench database dropped

Common options: --definition, --state, --prefix, --cap-seconds. Every write into a world goes through the product's
own commands, run as subprocesses; this tool runs only the admin statements of spec §3.5. Exits: 0 done; 2 refused
before any database change (`<CODE> <detail>` on stderr); 3 a step failed; 4 the check found a FAIL; 5 the cap was
reached; 69 outside the heavy-tool slot (T1). Diagnostics for the coordinator only; nothing here is served.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

REPO = Path(__file__).resolve().parents[1]
for _p in ("backend", "contracts", "simulator", "tools"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

DEFINITION = "backend/conversions/world-layer4-v1.json"
DEFAULT_STATE = "/opt/assetecon/worlds"
DEFAULT_PREFIX = "assetops_world"
CODE_PATHS = ("backend/assetops_backend", "contracts/assetops_contracts", "simulator/assetops_simulator",
              "tools/world.py", "tools/world_history.py")
MIGRATIONS = "backend/migrations"
CHECK_CODE = ("tools/world.py", "backend/tests/test_ds3_parity_postgres.py", "backend/tests/test_ds3_bulk_load_postgres.py",
              "backend/tests/pg_harness.py", "tools/run-host-tests.ps1")
L2_STEPS = (("snapshot", "assetops_backend.build_structure_snapshot", "build"),
            ("observe", "assetops_backend.observe_structure", "run"))
FORMAT_DEFINITION = "assetops.world-definition/1"
FORMAT_BUILD = "assetops.world-build/1"

_PREFIX = re.compile(r"assetops_[a-z0-9]{1,24}", re.ASCII)
_LABEL = re.compile(r"[a-z0-9]{1,20}", re.ASCII)
_WORLD = re.compile(r"[a-z0-9]{1,16}", re.ASCII)
_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)
_SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,62}", re.ASCII)
_HEX4 = re.compile(r"[0-9a-f]{8}", re.ASCII)


class Refused(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code, self.detail = code, detail


class StepFailed(Exception):
    def __init__(self, database: str, step: str, exit_code: int) -> None:
        super().__init__(step)
        self.database, self.step, self.exit_code = database, step, exit_code


class CapExceeded(Exception):
    def __init__(self, step: str) -> None:
        super().__init__(step)
        self.step = step


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def key(parts: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical(parts).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- the definition (§3.1) --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Tenant:
    slug: str
    onboarding: str
    submit_as: str
    accept_as: str
    sites: dict


@dataclass(frozen=True)
class Definition:
    path: Path
    raw: bytes
    world: str
    manifest: str
    derived_values: str
    months: tuple
    built_by: str
    tenants: tuple
    not_built: tuple
    telemetry: dict
    projection: dict


def _keys(obj: Any, want: set, where: str) -> None:
    if not isinstance(obj, dict) or set(obj) != want:
        raise Refused("WORLD_DEFINITION_INVALID", where)


def _repo_file(value: Any, where: str, root: Path) -> str:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise Refused("WORLD_DEFINITION_INVALID", where)
    resolved = (root / value).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise Refused("WORLD_DEFINITION_INVALID", where)
    return value


def read_definition(path: Path | str, root: Path = REPO) -> Definition:
    from assetops_backend.structure_snapshot.model import BUILT_BY

    path = Path(path)
    raw = path.read_bytes()
    try:
        d = json.loads(raw)
    except ValueError:
        raise Refused("WORLD_DEFINITION_INVALID", "$") from None
    _keys(d, {"format", "world", "manifest", "derived_values", "months", "built_by", "tenants", "not_built",
              "telemetry", "projection"}, "$")
    if d["format"] != FORMAT_DEFINITION:
        raise Refused("WORLD_DEFINITION_INVALID", "$.format")
    if not isinstance(d["world"], str) or not _WORLD.fullmatch(d["world"]):
        raise Refused("WORLD_DEFINITION_INVALID", "$.world")
    _repo_file(d["manifest"], "$.manifest", root)
    _repo_file(d["derived_values"], "$.derived_values", root)
    months = d["months"]
    if (not isinstance(months, list) or not months or not all(isinstance(m, str) and _MONTH.fullmatch(m) for m in months)
            or months != sorted(set(months))):
        raise Refused("WORLD_DEFINITION_INVALID", "$.months")
    if not isinstance(d["built_by"], str) or not BUILT_BY.fullmatch(d["built_by"]):
        raise Refused("WORLD_DEFINITION_INVALID", "$.built_by")
    if not isinstance(d["tenants"], list) or not d["tenants"]:
        raise Refused("WORLD_DEFINITION_INVALID", "$.tenants")
    tenants, slugs = [], set()
    for i, t in enumerate(d["tenants"]):
        w = f"$.tenants[{i}]"
        _keys(t, {"slug", "onboarding", "submit_as", "accept_as", "sites"}, w)
        if not isinstance(t["slug"], str) or not _SLUG.fullmatch(t["slug"]) or t["slug"] in slugs:
            raise Refused("WORLD_DEFINITION_INVALID", f"{w}.slug")
        slugs.add(t["slug"])
        _repo_file(t["onboarding"], f"{w}.onboarding", root)
        for k in ("submit_as", "accept_as"):
            if not isinstance(t[k], str) or not t[k]:
                raise Refused("WORLD_DEFINITION_INVALID", f"{w}.{k}")
        if t["submit_as"] == t["accept_as"]:
            raise Refused("WORLD_DEFINITION_INVALID", f"{w}.accept_as")
        if (not isinstance(t["sites"], dict) or not t["sites"]
                or not all(isinstance(k, str) and k and isinstance(v, str) and v for k, v in t["sites"].items())):
            raise Refused("WORLD_DEFINITION_INVALID", f"{w}.sites")
        tenants.append(Tenant(t["slug"], t["onboarding"], t["submit_as"], t["accept_as"], dict(t["sites"])))
    if not isinstance(d["not_built"], list):
        raise Refused("WORLD_DEFINITION_INVALID", "$.not_built")
    for i, n in enumerate(d["not_built"]):
        _keys(n, {"tenant", "reason"}, f"$.not_built[{i}]")
        if not isinstance(n["tenant"], str) or not _SLUG.fullmatch(n["tenant"]):
            raise Refused("WORLD_DEFINITION_INVALID", f"$.not_built[{i}].tenant")
        if n["reason"] not in {"NO_ONBOARDING_FILE"}:
            raise Refused("WORLD_DEFINITION_INVALID", f"$.not_built[{i}].reason")
    _keys(d["telemetry"], {"source", "reason"}, "$.telemetry")
    if d["telemetry"]["source"] != "none":
        raise Refused("WORLD_DEFINITION_INVALID", "$.telemetry.source")
    if not isinstance(d["telemetry"]["reason"], str) or not d["telemetry"]["reason"]:
        raise Refused("WORLD_DEFINITION_INVALID", "$.telemetry.reason")
    _keys(d["projection"], {"sites", "days", "basis"}, "$.projection")
    for k in ("sites", "days"):
        v = d["projection"][k]
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise Refused("WORLD_DEFINITION_INVALID", f"$.projection.{k}")
    if not isinstance(d["projection"]["basis"], str):
        raise Refused("WORLD_DEFINITION_INVALID", "$.projection.basis")
    return Definition(path, raw, d["world"], d["manifest"], d["derived_values"], tuple(months), d["built_by"],
                      tuple(tenants), tuple(d["not_built"]), dict(d["telemetry"]), dict(d["projection"]))


# --- git, keys, staleness (§3.2) -------------------------------------------------------------------------------------

class Git:
    """The one git reader: tree and blob ids at HEAD, the clean-tree status and the commit."""

    def __init__(self, root: Path = REPO) -> None:
        self.root = Path(root)

    def _git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True).stdout

    def tree(self, path: str) -> str:
        return self._git("rev-parse", f"HEAD:{path}").strip()

    def dirty(self, paths: Sequence[str]) -> list[str]:
        out = self._git("status", "--porcelain", "--untracked-files=all", "--", *paths)
        return [line for line in out.splitlines() if line.strip()]

    def head(self) -> str:
        return self._git("rev-parse", "HEAD").strip()


def parts_l0(git: Any) -> dict:
    return {"rung": "L0", "migrations": git.tree(MIGRATIONS)}


def parts_l1(git: Any, key0: str, definition_raw: bytes, inputs_digest: str) -> dict:
    return {"rung": "L1", "l0": key0, "definition": hashlib.sha256(definition_raw).hexdigest(),
            "inputs": inputs_digest, "code": {p: git.tree(p) for p in CODE_PATHS}}


def parts_l2(key1: str) -> dict:
    return {"rung": "L2", "l1": key1, "steps": hashlib.sha256(canonical(L2_STEPS).encode("utf-8")).hexdigest()}


def _flat(chain: Sequence[Mapping[str, Any]]) -> list[tuple[str, Any]]:
    """The comparable parts of a ladder in §3.2's order: migrations, definition, inputs, code.<path>, steps."""
    l0, l1, l2 = chain
    out = [("migrations", l0.get("migrations")), ("definition", l1.get("definition")), ("inputs", l1.get("inputs"))]
    code = l1.get("code") or {}
    out += [(f"code.{p}", code.get(p)) for p in CODE_PATHS]
    out.append(("steps", l2.get("steps")))
    return out


def stale_part(old: Sequence[Mapping[str, Any]], new: Sequence[Mapping[str, Any]]) -> str | None:
    for (name, a), (_, b) in zip(_flat(old), _flat(new)):
        if a != b:
            return name
    return None


def inputs_digest(files: Mapping[str, str], onboarding: Mapping[str, str]) -> str:
    """§3.2: one line per input file and per tenant's onboarding file, sorted, hashed as UTF-8."""
    lines = [f"{rel}\t{sha}\n" for rel, sha in files.items()]
    lines += [f"onboarding/{slug}.json\t{sha}\n" for slug, sha in onboarding.items()]
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()


def clean_tree_paths(definition: Definition | None, definition_rel: str) -> list[str]:
    paths = [*CODE_PATHS, MIGRATIONS, definition_rel]
    if definition is not None:
        paths += [t.onboarding for t in definition.tenants] + [definition.manifest, definition.derived_values]
    paths += [p for p in CHECK_CODE if p not in paths]
    return paths


# --- names (§3.2) ----------------------------------------------------------------------------------------------------

def name_for(prefix: str, rung: str, key12_or_label: str) -> str:
    tag = {"L0": "l0", "L1": "l1", "L2": "l2", "CLONE": "c"}[rung]
    return f"{prefix}_audit_{tag}_{key12_or_label}"


def harness_base_name(which: str, hex8: str | None = None) -> str:
    if which not in ("c5", "b5"):
        raise ValueError(which)
    return f"assetops_w{which}_pt{hex8 or secrets.token_hex(4)}_base_test"


def rung_url(name: str, environ: Mapping[str, str]) -> str:
    password = environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
    port = environ.get("ASSETOPS_PG_PORT", "55432")
    return f"postgresql+psycopg://assetops:{password}@127.0.0.1:{port}/{name}"


def check_name(name: str, environ: Mapping[str, str]) -> str:
    from assetops_backend.evidence.bulk_load import permitted_database

    env = {k: environ[k] for k in ("ASSETOPS_PG_PORT",) if k in environ}
    if len(name.encode("utf-8")) > 63 or not permitted_database(rung_url(name, environ), env):
        raise Refused("WORLD_NAME_NOT_PERMITTED", name)
    return name


def check_prefix(prefix: str, environ: Mapping[str, str]) -> None:
    if not _PREFIX.fullmatch(prefix):
        raise Refused("WORLD_NAME_NOT_PERMITTED", prefix)
    for rung in ("L0", "L1", "L2"):
        check_name(name_for(prefix, rung, "0" * 12), environ)


def check_label(prefix: str, label: str, environ: Mapping[str, str]) -> str:
    if not _LABEL.fullmatch(label or ""):
        raise Refused("WORLD_LABEL_INVALID", label or "")
    return check_name(name_for(prefix, "CLONE", label), environ)


# --- directories (§3.4) ----------------------------------------------------------------------------------------------

def _private_dir(path: Path, code: str) -> Path:
    try:
        st = path.stat()
    except OSError:
        raise Refused(code, str(path)) from None
    resolved = path.resolve()
    if (not stat.S_ISDIR(st.st_mode) or st.st_mode & 0o077 or st.st_uid != os.getuid()
            or resolved.is_relative_to(REPO.resolve())):
        raise Refused(code, str(path))
    return resolved


def state_dirs(state: Path) -> Path:
    root = _private_dir(Path(state), "WORLD_STATE_INVALID")
    for sub in ("manifests", "inputs", "tmp"):
        p = root / sub
        if not p.exists():
            os.mkdir(p, 0o700)
            os.chmod(p, 0o700)
    return root


def key_dir_for(key_root: Path, l1_name: str) -> Path:
    path = Path(key_root) / l1_name
    if path.exists():
        _private_dir(path, "WORLD_KEY_ROOT_INVALID")
        if stat.S_IMODE(path.stat().st_mode) != 0o700:
            raise Refused("WORLD_KEY_ROOT_INVALID", str(path))
        return path
    os.mkdir(path, 0o700)
    st = path.stat()
    if stat.S_IMODE(st.st_mode) != 0o700:
        os.chmod(path, 0o700)
        if stat.S_IMODE(path.stat().st_mode) != 0o700:
            raise Refused("WORLD_KEY_ROOT_INVALID", str(path))
    return path


# --- dependencies (real ones; tests replace them) --------------------------------------------------------------------

class Admin:
    """The admin connection on the `postgres` maintenance database (§3.5): NullPool, AUTOCOMMIT."""

    def __init__(self, environ: Mapping[str, str]) -> None:
        self.environ = environ
        self._engine = None

    def __call__(self, sql: str, params: Mapping[str, Any] | None = None) -> list[tuple]:
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool

        if self._engine is None:
            self._engine = create_engine(rung_url("postgres", self.environ), poolclass=NullPool,
                                         isolation_level="AUTOCOMMIT")
        with self._engine.connect() as c:
            result = c.execute(text(sql), dict(params or {}))
            return [tuple(r) for r in result] if result.returns_rows else []

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()


def rung_query(url: str, sqls: Sequence[str]) -> list[list[tuple]]:
    """Read statements on one rung before its freeze, or on the check clone; every engine disposed on return."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool

    engine = create_engine(url, poolclass=NullPool)
    try:
        with engine.connect() as c:
            return [[tuple(r) for r in c.execute(text(s))] for s in sqls]
    finally:
        engine.dispose()


class Clock:
    def monotonic(self) -> float:
        return time.monotonic()

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


def _real_runner(argv: Sequence[str], cwd: str, env: Mapping[str, str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(list(argv), cwd=cwd, env=dict(env), capture_output=True, text=True, timeout=timeout)


def _real_require(tool: str, *, db: bool = False) -> None:
    from heavy_slot_check import require

    require(tool, db=db)


@dataclass
class Deps:
    admin: Callable[..., list] | None = None
    query: Callable[[str, Sequence[str]], list] = rung_query
    runner: Callable[..., subprocess.CompletedProcess] = _real_runner
    git: Any = None
    clock: Any = field(default_factory=Clock)
    require: Callable[..., None] = _real_require
    environ: Mapping[str, str] | None = None
    which: Callable[..., str | None] = shutil.which
    snapshots: Callable[[str], Any] | None = None   # C4: url -> the snapshot service (tests: a fake)
    python: str = sys.executable


# --- the run context -------------------------------------------------------------------------------------------------

CENSUS_TABLES = ("SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
                 "AND table_type = 'BASE TABLE' AND table_name <> 'alembic_version' ORDER BY table_name")
TENANTS = "SELECT id, slug FROM tenant"


class World:
    def __init__(self, args: argparse.Namespace, deps: Deps) -> None:
        self.args, self.deps = args, deps
        self.environ = dict(os.environ if deps.environ is None else deps.environ)
        self.admin = deps.admin or Admin(self.environ)
        self.git = deps.git or Git(REPO)
        self.prefix = args.prefix
        self.deadline = deps.clock.monotonic() + args.cap_seconds
        self.state: Path | None = None
        self.definition: Definition | None = None
        self.definition_rel = args.definition
        self.out: list[str] = []
        self.ladder_inputs: tuple[str, Path, dict] | None = None
        self.quiet = False  # bench: the rung lines are kept in `out`, stdout carries only the report line

    # output
    def emit(self, obj: Mapping[str, Any]) -> None:
        if self.quiet:
            self.out.append(json.dumps(obj, sort_keys=True))
            return
        sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")

    # environment (§3.5)
    def env(self, database: str | None, tenant: str | None = None, key_dir: str | None = None) -> dict:
        e = {k: self.environ[k] for k in ("PATH", "HOME", "LANG") if k in self.environ}
        e["PYTHONPATH"] = f"{REPO}/backend:{REPO}/contracts:{REPO}/simulator"
        if database is not None:
            e["DATABASE_URL"] = rung_url(database, self.environ)
        if tenant is not None:
            e["ASSETOPS_TENANT_SLUG"] = tenant
        if key_dir is not None:
            e["ASSETOPS_PSEUDONYM_KEY_DIR"] = str(key_dir)
        for k in ("ASSETOPS_PG_PORT", "ASSETOPS_PG_PASSWORD"):
            if k in self.environ:
                e[k] = self.environ[k]
        return e

    def left(self, step: str) -> float:
        remaining = self.deadline - self.deps.clock.monotonic()
        if remaining <= 0:
            raise CapExceeded(step)
        return remaining

    def run_step(self, database: str, step: str, argv: list[str], env: Mapping[str, str], *,
                 cwd: Path = REPO, log: list | None = None, fail: bool = True) -> tuple[int, str, dict]:
        start = self.deps.clock.monotonic()
        try:
            done = self.deps.runner([self.deps.python, *argv], str(cwd), env, self.left(step))
        except subprocess.TimeoutExpired:
            raise CapExceeded(step) from None
        seconds = round(self.deps.clock.monotonic() - start, 3)
        lines = (done.stdout or "").strip().splitlines()
        last = lines[-1] if lines else ""
        try:
            out = json.loads(last) if last else None
        except ValueError:
            out = None
        record = {"step": step, "argv": list(argv), "seconds": seconds, "exit": done.returncode, "out": out}
        if log is not None:
            log.append(record)
        if done.returncode != 0 and fail:
            raise StepFailed(database, step, done.returncode)
        return done.returncode, last, record

    # setup checks, before any database call
    def prepare(self, *, need_definition: bool = True, clean: bool = True) -> None:
        if not _PREFIX.fullmatch(self.prefix or ""):
            raise Refused("WORLD_NAME_NOT_PERMITTED", self.prefix or "")
        check_prefix(self.prefix, self.environ)
        self.state = state_dirs(Path(self.args.state))
        if need_definition:
            self.definition = read_definition(REPO / self.definition_rel if not Path(self.definition_rel).is_absolute()
                                              else Path(self.definition_rel))
        if clean:
            dirty = self.git.dirty(clean_tree_paths(self.definition, self.definition_rel))
            if dirty:
                raise Refused("WORLD_TREE_DIRTY", dirty[0][3:].strip())

    # manifests (§3.3)
    def manifest_path(self, database: str) -> Path:
        return self.state / "manifests" / f"{database}.json"

    def read_manifest(self, database: str) -> dict | None:
        p = self.manifest_path(database)
        return json.loads(p.read_text()) if p.is_file() else None

    def write_manifest(self, database: str, body: Mapping[str, Any]) -> None:
        p = self.manifest_path(database)
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_text(canonical(body))
        os.replace(tmp, p)

    def manifests(self) -> list[dict]:
        out = []
        for p in sorted((self.state / "manifests").glob("*.json")):
            out.append(json.loads(p.read_text()))
        return out

    # admin statements (§3.5), each on a checked name
    def exists(self, name: str) -> bool:
        return bool(self.admin("SELECT 1 FROM pg_database WHERE datname = :n", {"n": check_name(name, self.environ)}))

    def sessions(self, name: str) -> int:
        rows = self.admin("SELECT count(*) FROM pg_stat_activity WHERE datname = :n", {"n": check_name(name, self.environ)})
        return int(rows[0][0]) if rows else 0

    def wait_idle(self, name: str, seconds: float = 5.0) -> bool:
        end = self.deps.clock.monotonic() + seconds
        while True:
            if self.sessions(name) == 0:
                return True
            if self.deps.clock.monotonic() >= end:
                return False
            self.deps.clock.sleep(0.25)

    def create(self, name: str, template: str | None = None) -> float:
        check_name(name, self.environ)
        start = self.deps.clock.monotonic()
        if template is None:
            self.admin(f'CREATE DATABASE "{name}"')
        else:
            check_name(template, self.environ)
            if not self.wait_idle(template):
                raise Refused("WORLD_DATABASE_IN_USE", template)
            self.admin(f'CREATE DATABASE "{name}" TEMPLATE "{template}" STRATEGY FILE_COPY')
        return round(self.deps.clock.monotonic() - start, 3)

    def freeze(self, name: str) -> None:
        self.admin(f'ALTER DATABASE "{check_name(name, self.environ)}" WITH ALLOW_CONNECTIONS false')

    def drop_db(self, name: str) -> None:
        self.admin(f'DROP DATABASE "{check_name(name, self.environ)}"')

    def census(self, name: str) -> tuple[dict, int]:
        url = rung_url(check_name(name, self.environ), self.environ)
        (tables,) = self.deps.query(url, [CENSUS_TABLES])
        names = [t[0] for t in tables]
        counts = self.deps.query(url, [f'SELECT count(*) FROM "{t}"' for t in names]) if names else []
        size = self.admin("SELECT pg_database_size(:n)", {"n": name})
        return ({t: int(c[0][0]) for t, c in zip(names, counts)}, int(size[0][0]) if size else 0)

    def tenant_ids(self, name: str) -> dict:
        (rows,) = self.deps.query(rung_url(check_name(name, self.environ), self.environ), [TENANTS])
        return {str(slug): str(tid) for tid, slug in rows}

    # inputs (§3.2)
    def inputs(self) -> tuple[str, Path, dict]:
        d = self.definition
        pid = os.getpid()
        exports = self.state / "tmp" / f"exports-{pid}"
        staged = self.state / "tmp" / f"inputs-{pid}"
        try:
            extras = self.state / "tmp" / f"extras-{pid}"
            argv = ["tools/world_history.py", "exports", "--manifest", d.manifest, "--out", str(exports),
                    "--extras", str(extras)]
            self.run_step("-", "L1.exports", argv, self.env(None))
            slugs = [t.slug for t in d.tenants]
            for slug in slugs:
                (staged / slug / "commercial").mkdir(parents=True, exist_ok=True)
            for f in sorted(exports.iterdir(), key=lambda p: p.name):
                if f.name == "unwritten.json":
                    for slug in slugs:
                        shutil.copyfile(f, staged / slug / "commercial" / f.name)
                    continue
                owner = next((s for s in slugs if f.name.startswith(f"{s}.")), None)
                if owner is None:
                    raise Refused("WORLD_INPUT_UNPLACED", f.name)
                shutil.copyfile(f, staged / owner / "commercial" / f.name)
            # D-DD.54: DS1b's staged JSON is placed for the tenants the definition names; a tenant it does not name has
            # no world, so its file is not placed. The statements reader is DD5 / WK: the loader refuses that file in
            # commercial/, so it is not staged.
            for f in sorted(extras.iterdir(), key=lambda p: p.name) if extras.is_dir() else []:
                owner = next((s for s in slugs if f.name.startswith(f"{s}.")), None)
                if owner is not None and not f.name.endswith(".statements.json"):
                    shutil.copyfile(f, staged / owner / "commercial" / f.name)
            files = {p.relative_to(staged).as_posix(): sha256_file(p) for p in sorted(staged.rglob("*")) if p.is_file()}
            digest = inputs_digest(files, {t.slug: sha256_file(REPO / t.onboarding) for t in d.tenants})
            final = self.state / "inputs" / digest[:12]
            if not final.exists():
                os.replace(staged, final)
            return digest, final, files
        finally:
            shutil.rmtree(exports, ignore_errors=True)
            shutil.rmtree(self.state / "tmp" / f"extras-{pid}", ignore_errors=True)
            shutil.rmtree(staged, ignore_errors=True)

    # keys
    def ladder_parts(self) -> tuple[list[dict], list[str], tuple[str, Path, dict]]:
        p0 = parts_l0(self.git)
        k0 = key(p0)
        inputs = self.inputs()
        p1 = parts_l1(self.git, k0, self.definition.raw, inputs[0])
        k1 = key(p1)
        p2 = parts_l2(k1)
        return [p0, p1, p2], [k0, k1, key(p2)], inputs

    def current_l2(self) -> tuple[str, dict]:
        parts, keys, self.ladder_inputs = self.ladder_parts()
        name = check_name(name_for(self.prefix, "L2", keys[2][:12]), self.environ)
        m = self.read_manifest(name)
        if m is not None and m.get("key") == keys[2]:
            if self.exists(name):
                return name, m
            raise Refused("WORLD_NO_TEMPLATE", f"{name} (database missing)")
        l2s = [x for x in self.manifests() if x.get("rung") == "L2" and x["database"].startswith(f"{self.prefix}_audit_")]
        if not l2s:
            raise Refused("WORLD_NO_TEMPLATE", self.prefix)
        latest = max(l2s, key=lambda x: x.get("built_at", ""))
        l1 = self.read_manifest(latest["parent"]) or {}
        l0 = self.read_manifest(l1.get("parent", "")) or {}
        part = stale_part([l0.get("parts", {}), l1.get("parts", {}), latest.get("parts", {})], parts)
        raise Refused("WORLD_TEMPLATE_STALE", part or "key")

    # check staleness (§3.3; D-DS4.21)
    def check_inputs(self) -> dict:
        d = self.definition
        return {"derived_values": self.git.tree(d.derived_values), "manifest": self.git.tree(d.manifest),
                "code": {p: self.git.tree(p) for p in CHECK_CODE}}

    def check_state(self, l2: Mapping[str, Any]) -> tuple[bool | None, str | None]:
        block = l2.get("check")
        if not block:
            return None, None
        old, new = block.get("check_inputs") or {}, self.check_inputs()
        order = [("derived_values", old.get("derived_values"), new["derived_values"]),
                 ("manifest", old.get("manifest"), new["manifest"])]
        order += [(f"code.{p}", (old.get("code") or {}).get(p), new["code"][p]) for p in CHECK_CODE]
        for part, a, b in order:
            if a != b:
                return None, part
        return bool(block.get("passed")), None


# --- build (§3.2, §3.5) ----------------------------------------------------------------------------------------------

def _now_iso(world: World) -> str:
    return world.deps.clock.now().astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rung(world: World, rung: str, k: str, parts: dict, parent: str | None, body: Callable[[str, list], dict]) -> dict:
    name = check_name(name_for(world.prefix, rung, k[:12]), world.environ)
    m = world.read_manifest(name)
    start = world.deps.clock.monotonic()
    if m is not None and m.get("key") == k and world.exists(name):
        world.emit({"database": name, "rung": rung, "key12": k[:12], "reused": True, "seconds": 0.0})
        return m
    if world.exists(name):  # a partial: no manifest (or a manifest of another key)
        if world.sessions(name) != 0:
            raise Refused("WORLD_DATABASE_IN_USE", name)
        world.drop_db(name)
    if m is not None:
        world.manifest_path(name).unlink()
    world.create(name, parent)
    steps: list = []
    extra = body(name, steps)
    census, size = world.census(name)
    world.freeze(name)
    manifest = {"format": FORMAT_BUILD, "database": name, "rung": rung, "key": k, "parts": parts, "parent": parent,
                "commit": world.git.head(), "built_at": _now_iso(world), "world": world.definition.world,
                "telemetry": world.definition.telemetry, "steps": steps, "census": census, "size_bytes": size}
    manifest.update(extra)
    if rung == "L2":
        manifest["check"] = None
    world.write_manifest(name, manifest)
    world.emit({"database": name, "rung": rung, "key12": k[:12], "reused": False,
                "seconds": round(world.deps.clock.monotonic() - start, 3)})
    return manifest


def cmd_build(world: World) -> int:
    key_root = _private_dir(Path(world.args.key_root), "WORLD_KEY_ROOT_INVALID")
    world.prepare()
    _build(world, key_root)
    return 0


def _build(world: World, key_root: Path) -> list[dict]:
    """§3.2 L0, L1, L2 in order, reusing current rungs; returns the three manifests."""
    d = world.definition
    parts, keys, (digest, inputs_dir, files) = world.ladder_parts()

    def l0(name: str, steps: list) -> dict:
        world.run_step(name, "L0.migrate", ["-m", "alembic", "upgrade", "head"], world.env(name), cwd=REPO / "backend",
                       log=steps)
        return {}

    m0 = _rung(world, "L0", keys[0], parts[0], None, l0)

    def l1(name: str, steps: list) -> dict:
        kd = str(key_dir_for(key_root, name))
        for t in d.tenants:
            env = world.env(name, t.slug, kd)
            mod = "assetops_backend.onboard_operator"
            _, digest_line, _ = world.run_step(name, f"L1.onboard_digest:{t.slug}",
                                               ["-m", mod, "digest", "--file", t.onboarding], env, log=steps)
            world.run_step(name, f"L1.onboard_check:{t.slug}",
                           ["-m", mod, "check", "--file", t.onboarding, "--key-dir", kd], env, log=steps)
            world.run_step(name, f"L1.onboard_apply:{t.slug}",
                           ["-m", mod, "apply", "--file", t.onboarding, "--key-dir", kd, "--confirmed-digest",
                            digest_line.strip()], env, log=steps)
        for t in d.tenants:
            _, _, rec = world.run_step(name, f"L1.load:{t.slug}",
                                       ["-m", "assetops_backend.load_world_inputs", "--world", str(inputs_dir),
                                        "--tenant", t.slug, "--submit-as", t.submit_as, "--accept-as", t.accept_as],
                                       world.env(name, t.slug, kd), log=steps)
            out = rec["out"] or {}
            if out.get("commercial_exit") != 0 or out.get("batches") != 0:
                rec["exit"] = 3
                raise StepFailed(name, f"L1.load:{t.slug}", 3)
        return {"inputs_dir": str(inputs_dir), "inputs": files, "key_dir": kd, "tenants": world.tenant_ids(name)}

    m1 = _rung(world, "L1", keys[1], parts[1], m0["database"], l1)

    def l2(name: str, steps: list) -> dict:
        snaps = {}
        for t in d.tenants:
            env = world.env(name, t.slug, m1["key_dir"])
            for month in d.months:
                _, _, rec = world.run_step(name, f"L2.snapshot:{t.slug}:{month}",
                                           ["-m", L2_STEPS[0][1], L2_STEPS[0][2], "--tenant", t.slug, "--month", month,
                                            "--by", d.built_by], env, log=steps)
                out = rec["out"] or {}
                snaps[f"{t.slug}:{month}"] = {"portfolio_snapshot_id": out.get("portfolio_snapshot_id"),
                                              "sites": out.get("sites") or {}}
                world.run_step(name, f"L2.observe:{t.slug}:{month}",
                               ["-m", L2_STEPS[1][1], L2_STEPS[1][2], "--tenant", t.slug, "--month", month], env,
                               log=steps)
        return {k: m1[k] for k in ("inputs_dir", "inputs", "key_dir", "tenants")} | {"snapshots": snaps}

    m2 = _rung(world, "L2", keys[2], parts[2], m1["database"], l2)
    return [m0, m1, m2]


# --- clone, reset, list, drop (§3.4) ---------------------------------------------------------------------------------

def _clone(world: World, label: str, l2_name: str, l2: dict) -> dict:
    name = check_label(world.prefix, label, world.environ)
    if world.exists(name) or world.read_manifest(name) is not None:
        raise Refused("WORLD_CLONE_EXISTS", name)
    seconds = world.create(name, l2_name)
    passed, stale = world.check_state(l2)
    manifest = {"format": FORMAT_BUILD, "database": name, "rung": "CLONE", "key": l2["key"], "parent": l2_name,
                "commit": world.git.head(), "built_at": _now_iso(world), "world": l2.get("world"),
                "key_dir": l2.get("key_dir"), "tenants": l2.get("tenants"), "snapshots": l2.get("snapshots"),
                "check_passed": passed, "check_stale": stale, "seconds": seconds}
    world.write_manifest(name, manifest)
    return manifest


def _clone_line(m: Mapping[str, Any]) -> dict:
    return {"database": m["database"], "rung": "CLONE", "parent": m["parent"], "seconds": m["seconds"],
            "key_dir": m.get("key_dir"), "check_passed": m.get("check_passed"), "check_stale": m.get("check_stale")}


def cmd_clone(world: World) -> int:
    check_label(world.prefix, world.args.label, world.environ)
    world.prepare()
    l2_name, l2 = world.current_l2()
    world.emit(_clone_line(_clone(world, world.args.label, l2_name, l2)))
    return 0


def cmd_reset(world: World) -> int:
    name = check_label(world.prefix, world.args.label, world.environ)
    world.prepare()
    l2_name, l2 = world.current_l2()
    if world.read_manifest(name) is not None:
        _drop(world, name)
    world.emit(_clone_line(_clone(world, world.args.label, l2_name, l2)))
    return 0


def cmd_list(world: World) -> int:
    world.prepare(need_definition=False, clean=False)
    definition = None
    try:
        world.definition = definition = read_definition(REPO / world.definition_rel)
    except (Refused, OSError):
        definition = None
    names = {r[0] for r in world.admin("SELECT datname FROM pg_database")}
    by_name = {m["database"]: m for m in world.manifests()}
    for m in by_name.values():
        passed, stale = None, None
        if m.get("rung") == "L2" and definition is not None:
            passed, stale = world.check_state(m)
        elif m.get("rung") == "CLONE":
            parent = by_name.get(m.get("parent"))
            if parent is not None and definition is not None:
                passed, stale = world.check_state(parent)
            else:
                passed, stale = m.get("check_passed"), m.get("check_stale")
        world.emit({"database": m["database"], "rung": m.get("rung"), "key12": (m.get("key") or "")[:12],
                    "parent": m.get("parent"), "built_at": m.get("built_at"), "exists": m["database"] in names,
                    "check_passed": passed, "check_stale": stale})
    return 0


def _drop_pattern(prefix: str) -> re.Pattern:
    return re.compile(rf"{re.escape(prefix)}_audit_(?:(?:l0|l1|l2)_[0-9a-f]{{12}}|c_[a-z0-9]{{1,20}})", re.ASCII)


def _drop(world: World, name: str) -> dict:
    if not _drop_pattern(world.prefix).fullmatch(name or ""):
        raise Refused("WORLD_UNKNOWN_DATABASE", name or "")
    m = world.read_manifest(name)
    if m is None:
        raise Refused("WORLD_UNKNOWN_DATABASE", name)
    check_name(name, world.environ)
    for child in world.manifests():
        if child.get("parent") == name and world.exists(child["database"]):
            raise Refused("WORLD_HAS_DESCENDANTS", child["database"])
    if world.exists(name) and world.sessions(name) != 0:
        raise Refused("WORLD_DATABASE_IN_USE", name)
    line: dict = {"database": name, "dropped": True}
    if m.get("rung") == "L1":
        kd = m.get("key_dir")
        for slug, tid in sorted((m.get("tenants") or {}).items()):
            world.run_step(name, f"drop.erase:{slug}",
                           ["-m", "assetops_backend.commercial.pseudonym_key", "erase", "--dir", kd, "--tenant-id", tid],
                           world.env(None))
        line["key_dir"] = kd
        line["keys_left"] = sum(1 for _ in Path(kd).glob("*.key")) if kd and Path(kd).is_dir() else 0
    if world.exists(name):
        world.drop_db(name)
    world.manifest_path(name).unlink()
    return line


def cmd_drop(world: World) -> int:
    world.prepare(need_definition=False, clean=False)
    world.emit(_drop(world, world.args.database))
    return 0


# --- check (§3.6; D-DS4.8, D-DS4.16, D-DS4.20, D-DS4.21, D-DS4.26) -------------------------------------------------

# §2.1 as a literal: the classes of the 47 mini-grid factors per side, as they hold at Kobo and Mto (D-DS4.16).
C4_CONTRACT = {
    "actual": {
        "metered_kwh": "B", "billed_kwh": "E", "revenue": "E", "collected": "E", "diesel_l": "B", "fuel_cost": "E",
        "battery_wear": "E", "cost_to_serve": "E", "contribution": "E", "obligation_hours_without_redundancy": "B",
        "shortfall_backed": "B", "obligation_hours_without_backup": "B", "replayed_dawn_days_below_safeguard": "B",
        "asset_days_out_of_service": "B", "asset_days_total": "B", "asset_days_available": "B", "delivered_kwh": "B",
        "technical_loss_kwh": "B", "unexplained_loss_kwh": "B", "adjustments_kwh": "B", "unmapped_kwh": "B",
        "tariff": "E", "productive_kwh": "E", "productive_tariff": "B", "in_transit": "E", "outstanding": "E",
        "necessary_l": "B", "candidate_l": "B", "unexplained_l": "B", "extra_l": "E", "diesel_price": "E",
        "battery_throughput_kwh": "E", "wear_rate": "B", "om": "E", "staff": "E", "collection_cost": "E",
        "reduced_days": "B", "hours_per_day": "B", "major_assets": "B", "unserved_critical_kwh": "B",
        "customer_hours_interrupted": "B", "field_visits": "B", "liability": "B", "period_days": "E",
        "standby_kw": "B", "lost_unit_kw": "B", "dawn_days_below": "B"},
    "plan": {
        "metered_kwh": "E", "billed_kwh": "E", "revenue": "E", "collected": "E", "diesel_l": "E", "fuel_cost": "E",
        "battery_wear": "E", "cost_to_serve": "E", "contribution": "E", "obligation_hours_without_redundancy": "B",
        "shortfall_backed": "B", "obligation_hours_without_backup": "B", "replayed_dawn_days_below_safeguard": "E",
        "asset_days_out_of_service": "E", "asset_days_total": "B", "asset_days_available": "B", "delivered_kwh": "E",
        "technical_loss_kwh": "E", "unexplained_loss_kwh": "E", "adjustments_kwh": "E", "unmapped_kwh": "E",
        "tariff": "E", "productive_kwh": "E", "productive_tariff": "B", "in_transit": "E", "outstanding": "E",
        "necessary_l": "E", "candidate_l": "E", "unexplained_l": "E", "extra_l": "E", "diesel_price": "E",
        "battery_throughput_kwh": "E", "wear_rate": "B", "om": "E", "staff": "E", "collection_cost": "E",
        "reduced_days": "E", "hours_per_day": "B", "major_assets": "B", "unserved_critical_kwh": "E",
        "customer_hours_interrupted": "E", "field_visits": "E", "liability": "E", "period_days": "E",
        "standby_kw": "B", "lost_unit_kw": "B", "dawn_days_below": "E"},
}
# Kisiwa's October O&M invoice was not received: three actual cells are blank there (D-DS4.26).
C4_SITE_CLASSES = {"KISIWA-001": {"actual": {"om": "B", "cost_to_serve": "B", "contribution": "B"}}}
# Filled only by the Architect (D-DS4.16). D-DS4.27: emptied once 5a fix F1 merged (do not re-add).
C4_KNOWN_FINDINGS: tuple[str, ...] = ()
CHECK_CLONE_LABEL = "check"
SITE_TIMEZONE = "SELECT timezone FROM site WHERE id = '{site}'"


def site_class(code: str, side: str, factor: str) -> str | None:
    """A Site's class for a factor on a side: its override when present, else the contract's (D-DS4.26)."""
    override = C4_SITE_CLASSES.get(code, {}).get(side, {})
    return override[factor] if factor in override else C4_CONTRACT[side].get(factor)


def _equal(v: Any, x: Any) -> bool:
    if v is None or x is None or isinstance(x, bool):
        return False  # unknown is never equal to anything, zero included
    try:
        return Decimal(str(v)) == Decimal(repr(x))
    except (ArithmeticError, ValueError):
        return False


def judge_side(slug: str, code: str, side: str, product: Mapping[str, Any], expected: Mapping[str, Any]) -> dict:
    """C4 on one Site and side: every factor of the union of the payload's and the contract's keys is judged."""
    contract = C4_CONTRACT[side]
    counts, fails, blanks = {"E": 0, "B": 0}, [], []
    for f in sorted(set(product) | set(contract)):
        where = f"{slug}/{code} {side}.{f}"
        entry = product.get(f)
        v = entry.get("value") if isinstance(entry, Mapping) else None
        if f not in contract:
            fails.append(f"{where} class=uncontracted product={v} expected={expected.get(f)}")
            continue
        c = site_class(code, side, f)
        counts[c] += 1
        if not isinstance(entry, Mapping):
            fails.append(f"{where} class=not_in_product product=None expected={expected.get(f)}")
            continue
        x = expected.get(f)
        missing, leaves = entry.get("missing"), list(entry.get("missing_leaves") or ())
        blank = v is None and bool(missing or leaves)
        if blank:  # the honesty list: every blank cell with the record it names, whatever its class
            record = missing.get("record_kind") if isinstance(missing, Mapping) else None
            blanks.append(f"{where} {record if record else 'leaves=' + ','.join(leaves)}")
        if c == "E" and not _equal(v, x):
            fails.append(f"{where} class=E product={v} expected={x}")
        elif c == "B" and not blank:
            fails.append(f"{where} class=B product={v} expected={x}")
    return {"site": f"{slug}/{code}", "side": side, "E": counts["E"], "B": counts["B"], "fails": fails,
            "blanks": blanks}


def site_set_fails(rows: Sequence[tuple[str, Mapping[str, Any]]], definition: Definition,
                   snapshots: Mapping[str, int]) -> list[str]:
    """Which Sites were judged: each Site the definition declares, once per snapshot of its tenant (D-DS4.16)."""
    got: dict[tuple[str, str], int] = {}
    for slug, payload in rows:
        k = (slug, str(payload.get("site_code")))
        got[k] = got.get(k, 0) + 1
    out = []
    for t in sorted(definition.tenants, key=lambda x: x.slug):
        for code in sorted(t.sites):
            n, want = got.pop((t.slug, code), 0), snapshots.get(t.slug, 0)
            if n < want:
                out.append(f"site_missing {t.slug}/{code}")
            elif n > want:
                out.append(f"site_duplicate {t.slug}/{code}")
    out += [f"site_undeclared {s}/{c}" for (s, c) in sorted(got)]
    return out


def c4_oracle(rows: Sequence[tuple[str, Mapping[str, Any]]], definition: Definition, derived: Mapping[str, Any],
              snapshots: Mapping[str, int] | None = None) -> dict:
    """C4 over `(slug, payload)` Site rows: PASS only when no factor FAILs; a known finding is still a FAIL.

    With `snapshots` (tenant slug to its snapshot count) the set of Sites judged must be exactly the definition's.
    """
    names = {t.slug: t.sites for t in definition.tenants}
    set_fails = site_set_fails(rows, definition, snapshots) if snapshots is not None else []
    rows = [r for r in rows if r[1].get("site_code") in names.get(r[0], {})]
    known = {" ".join(k.split(" ")[:2]): k.split(" ")[2] for k in C4_KNOWN_FINDINGS}
    sides, fails, blanks = [], [{"line": x, "mark": "new"} for x in set_fails], []
    for slug, payload in sorted(rows, key=lambda r: (r[0], r[1].get("site_code", ""))):
        code = payload["site_code"]
        expected = derived["sites"][f"{slug}/{names[slug][code]}"]
        for side, product, exp in (("actual", payload.get("actual") or {}, expected["actual"]["nodes"]),
                                   ("plan", (payload.get("targets") or {}).get("values") or {},
                                    expected["plan"]["nodes"])):
            j = judge_side(slug, code, side, product, exp)
            sides.append({k: j[k] for k in ("site", "side", "E", "B")})
            for line in j["fails"]:
                head = " ".join(line.split(" ")[:2])
                fails.append({"line": line, "mark": f"known {known[head]}" if head in known and " product=None " in line else "new"})
            blanks += j["blanks"]
    return {"state": "FAIL" if fails or not rows else "PASS",
            "detail": {"sites": sides, "fails": fails, "blanks": blanks}}


HARNESS_ENV_ALLOW = ("ASSETOPS_TEST_PYTHON", "ASSETOPS_HEAVY_SLOT", "ASSETOPS_HEAVY_DB")


def harness_run(world: World, which: str, test: str, extra_env: Mapping[str, str],
                args: Sequence[str] = ()) -> tuple[int, str]:
    """C5 and B5 (D-DS4.20): DS3's tests under a base of their own, never the parent's test database."""
    env = world.env(None)  # built from an explicit allow-list; the parent environment is never inherited
    pwsh = world.deps.which("pwsh", path=env.get("PATH"))
    if pwsh is None:
        return 127, "pwsh not found"
    base = check_name(harness_base_name(which), world.environ)
    stem = base[: -len("_test")]
    env["ASSETOPS_TEST_DATABASE_URL"] = rung_url(base, world.environ)
    for k in HARNESS_ENV_ALLOW:
        if k in world.environ:
            env[k] = world.environ[k]
    env.update(extra_env)
    world.create(base)
    code, out, leftovers = 1, "", []
    try:
        try:
            done = world.deps.runner([pwsh, "-NoProfile", "-File", "tools/run-host-tests.ps1", "--", test, *args],
                                     str(REPO), env, world.left(f"harness:{test}"))
        except subprocess.TimeoutExpired:
            raise CapExceeded(f"harness:{test}") from None
        code, out = done.returncode, done.stdout or ""
    finally:
        pattern = re.compile(rf"^{re.escape(stem)}_pt[0-9a-f]+_[a-z0-9]+_test$")
        for (name,) in world.admin("SELECT datname FROM pg_database"):
            if pattern.match(name):
                if world.wait_idle(name):
                    world.drop_db(name)
                else:
                    leftovers.append(name)
        if world.wait_idle(base):
            world.drop_db(base)
        else:
            leftovers.append(base)
    if leftovers:
        return (code or 1), f"{out.strip().splitlines()[-1] if out.strip() else ''} in use: {' '.join(leftovers)}"
    return code, out


def _line(check: str, ok: bool, detail: Any) -> dict:
    return {"check": check, "state": "PASS" if ok else "FAIL", "detail": detail}


def _c1(world: World, l1: Mapping[str, Any]) -> dict:
    files = world.ladder_inputs[2] if world.ladder_inputs else world.inputs()[2]
    recorded = l1.get("inputs") or {}
    diff = [f"differs {p}" for p in sorted(set(files) & set(recorded)) if files[p] != recorded[p]]
    diff += [f"missing {p}" for p in sorted(set(recorded) - set(files))]
    diff += [f"extra {p}" for p in sorted(set(files) - set(recorded))]
    return _line("C1", not diff, "; ".join(diff) or f"{len(files)} files")


def _c2(world: World, clone: str, l2: Mapping[str, Any]) -> dict:
    census, _ = world.census(clone)
    recorded = l2.get("census") or {}
    diff = [f"{t} {recorded.get(t)} != {census.get(t)}" for t in sorted(set(census) | set(recorded))
            if census.get(t) != recorded.get(t)]
    return _line("C2", not diff, "; ".join(diff) or f"{len(census)} tables")


def _c3(world: World, clone: str, l2: Mapping[str, Any]) -> dict:
    bad = []
    for key_, snap in sorted((l2.get("snapshots") or {}).items()):
        slug = key_.split(":")[0]
        rc, last, rec = world.run_step(clone, f"check.verify:{key_}",
                                       ["-m", "assetops_backend.build_structure_snapshot", "verify", "--tenant", slug,
                                        "--snapshot", str(snap.get("portfolio_snapshot_id"))],
                                       world.env(clone, slug, l2.get("key_dir")), fail=False)
        out = rec["out"] if isinstance(rec["out"], dict) else {}
        if rc != 0 or out.get("matches") is not True:
            bad.append(f"{key_} exit={rc} differences={out.get('differences')}")
    return _line("C3", not bad, "; ".join(bad) or f"{len(l2.get('snapshots') or {})} snapshots match")


def _c4(world: World, clone: str, l2: Mapping[str, Any]) -> dict:
    from uuid import UUID

    derived = json.loads((REPO / world.definition.derived_values).read_text())
    url = rung_url(clone, world.environ)
    if world.deps.snapshots is not None:
        service = world.deps.snapshots(url)
    else:
        from assetops_backend.structure_snapshot.composition import build_structure_snapshot

        service = build_structure_snapshot(url)
    from assetops_backend.structure_snapshot import codec

    rows: list = []
    try:
        for key_, snap in sorted((l2.get("snapshots") or {}).items()):
            slug = key_.split(":")[0]
            tid = UUID((l2.get("tenants") or {})[slug])
            ids = [UUID(x) for _, x in sorted((snap.get("sites") or {}).items())]
            rows += [(slug, codec.payload_of(r)) for r in service.store.get(tid, ids)]
    finally:
        service.dispose()
    counts = {slug.split(":")[0]: 0 for slug in (l2.get("snapshots") or {})}
    for key_ in (l2.get("snapshots") or {}):
        counts[key_.split(":")[0]] += 1
    result = c4_oracle(rows, world.definition, derived, counts)
    return _line("C4", result["state"] == "PASS", result["detail"])


def _c5(world: World) -> dict:
    code, out = harness_run(world, "c5", "backend/tests/test_ds3_parity_postgres.py", {})
    tail = out.strip().splitlines()[-1] if out.strip() else ""
    return _line("C5", code == 0 and " in use: " not in out, f"exit {code} {tail}".strip())


def _c6(world: World, clone: str, l1: Mapping[str, Any]) -> dict:
    from uuid import UUID

    from assetops_backend.evidence.bulk_load import BatchTimeUnreadable, cover_gap, envelope_span
    from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text
    from assetops_contracts.source_envelope_v4 import parse_canonical_source_envelope_text

    files = sorted(Path(l1.get("inputs_dir") or "/nonexistent").rglob("*.batch.json"))
    if not files:
        return _line("C6", True, "0 batches (telemetry none)")
    url, bad = rung_url(clone, world.environ), []
    for f in files:
        batch = parse_canonical_batch_v2_text(f.read_text(encoding="utf-8"))
        ((tz,),) = world.deps.query(url, [SITE_TIMEZONE.format(site=UUID(batch.site_id))])[0]
        try:
            spans = []
            for e in batch.envelopes:
                env = parse_canonical_source_envelope_text(e)
                spans.append(envelope_span(env.source_time, env.interval_start, env.interval_end))
            gap = cover_gap(spans, tz)
        except BatchTimeUnreadable as u:
            gap = f"time unreadable {u.field}"
        if gap is not None:
            bad.append(f"{f.name} {gap}")
    return _line("C6", not bad, "; ".join(bad) or f"{len(files)} batches")


def _c7(manifests: Sequence[Mapping[str, Any]]) -> dict:
    bad = [f"{m['database']} {s['step']} exit {s['exit']}" for m in manifests for s in m.get("steps") or []
           if s.get("exit") != 0]
    return _line("C7", not bad, "; ".join(bad) or f"{sum(len(m.get('steps') or []) for m in manifests)} steps")


def _guard(name: str, fn: Callable[[], dict]) -> dict:
    try:
        return fn()
    except (Refused, StepFailed, CapExceeded):
        raise
    except Exception as error:  # a check that raises is a FAIL; the others still run
        return _line(name, False, f"raised {type(error).__name__}: {error}")


def cmd_check(world: World) -> int:
    world.prepare()
    l2_name, l2 = world.current_l2()
    l1 = world.read_manifest(l2["parent"]) or {}
    l0 = world.read_manifest(l1.get("parent", "")) or {}
    clone = check_label(world.prefix, CHECK_CLONE_LABEL, world.environ)
    if world.exists(clone):  # a leftover, under drop's rules: never while in use
        if world.sessions(clone) != 0:
            raise Refused("WORLD_DATABASE_IN_USE", clone)
        world.drop_db(clone)
    if world.read_manifest(clone) is not None:
        world.manifest_path(clone).unlink()
    world.create(clone, l2_name)
    try:
        lines = [_guard("C1", lambda: _c1(world, l1)), _guard("C2", lambda: _c2(world, clone, l2)),
                 _guard("C3", lambda: _c3(world, clone, l2)), _guard("C4", lambda: _c4(world, clone, l2)),
                 _guard("C5", lambda: _c5(world)), _guard("C6", lambda: _c6(world, clone, l1)),
                 _guard("C7", lambda: _c7([l0, l1, l2]))]
    finally:
        stuck = not world.wait_idle(clone)
        if not stuck:
            world.drop_db(clone)
    passed = all(x["state"] == "PASS" for x in lines)
    l2 = dict(l2)
    l2["check"] = {"at": _now_iso(world), "commit": world.git.head(), "check_inputs": world.check_inputs(),
                   "passed": passed, "checks": lines}
    world.write_manifest(l2_name, l2)
    for x in lines:
        world.emit(x)
    world.emit({"check": "ALL", "state": "PASS" if passed else "FAIL"})
    if stuck:  # never forced: a coded refusal, the check clone left for `drop`
        raise Refused("WORLD_DATABASE_IN_USE", clone)
    return 0 if passed else 4


# --- bench (§4; D-DS4.11, D-DS4.12) ----------------------------------------------------------------------------------

BENCH_PREFIX = "assetops_worldbench"
FORMAT_BENCH = "assetops.world-bench/2"
BENCH_CLONES = ("b1", "b2", "b3")
LATE_LABEL = "bl"
LATE_SITE = "KOBO-001"
LATE_PLUS = Decimal("10.00")
PIPELINE_TEST = "backend/tests/test_ds4_bench_pipeline_postgres.py"
PIPELINE_MARK = "DS4_PIPELINE "
DS7_THRESHOLD_SECONDS = 2700
NOT_BUILT_CHANGES = ({"kind": "option_change", "state": "NOT_BUILT", "unit": "6a"},
                     {"kind": "contract_term_edit", "state": "NOT_BUILT", "unit": "9a0"})
#: What every figure is (§4 "What the numbers mean"); codes, the packet states them in words.
BENCH_MEANING = {"clock": "WALL_ONE_RUN_THIS_VPS", "includes": ["SUBPROCESS_START", "PYTHON_IMPORTS"],
                 "synchronous_commit": "SERVER_DEFAULT", "samples": 1, "noise_below": "10_IN_100",
                 "world": "ONE_TENANT_THREE_SITES_ONE_MONTH_NO_TELEMETRY"}


def bench_evidence_dir(path: str | Path) -> Path:
    """`--evidence` resolves under `/opt/assetecon/evidence/` or outside the repository, never inside it."""
    resolved = Path(path).resolve()
    if resolved.is_relative_to(REPO.resolve()):
        raise Refused("WORLD_EVIDENCE_IN_REPO", str(path))
    return resolved


def _pipeline_lines(stdout: str) -> list[str]:
    return [x.strip() for x in (stdout or "").splitlines() if x.strip().startswith(PIPELINE_MARK)]


def pipeline_line(stdout: str) -> dict | None:
    """The last `DS4_PIPELINE {json}` line of B5's output, parsed; None when there is none or it is malformed."""
    lines = _pipeline_lines(stdout)
    if not lines:
        return None
    try:
        found = json.loads(lines[-1][len(PIPELINE_MARK):])
    except ValueError:
        return None
    return found if isinstance(found, dict) else None


def pipeline_marker(stdout: str) -> str:
    """`PARSED` (the last marker line parses), `MALFORMED` (it does not) or `MISSING` (there is none)."""
    if not _pipeline_lines(stdout):
        return "MISSING"
    return "PARSED" if pipeline_line(stdout) is not None else "MALFORMED"


def assemble_bench(start: Mapping[str, Any], ladder: Sequence[Mapping[str, Any]], clones: Sequence[Mapping[str, Any]],
                   late: Mapping[str, Any] | None, pipeline: Mapping[str, Any] | None,
                   projection: Mapping[str, Any]) -> dict:
    """The report (§4): B1 to B6, `ds7` and the five strategy targets. Pure: T10 feeds it literals."""
    totals = {r["rung"]: float(r["seconds"]) for r in ladder}
    l1, l2 = totals.get("L1"), totals.get("L2")
    measured = pipeline.get("measured") if pipeline else None
    drain = ((measured or {}).get("drain") or {}).get("verdict")
    proj: dict = {"kind": "PROJECTION_NOT_MEASUREMENT", "role": "INFORMATION_ONLY", "sites": projection["sites"],
                  "days": projection["days"], "basis": projection["basis"], "input_drain": drain,
                  "per_site_day_seconds": None, "per_site_day_includes": ["BULK_LOAD", "MINI_DEPTH", "TICKS"],
                  "projected_l2_seconds": None}
    if measured and measured.get("site_days") and measured.get("mini_depth_seconds") is not None and l2 is not None:
        per = (float(measured["load_seconds"]) + float(measured["mini_depth_seconds"])
               + float(measured["tick_wall_seconds"])) / int(measured["site_days"])
        proj["per_site_day_seconds"] = round(per, 3)
        proj["projected_l2_seconds"] = round(l2 + per * int(projection["sites"]) * int(projection["days"]), 3)
    projected = proj["projected_l2_seconds"]
    ds7 = {"threshold_seconds": DS7_THRESHOLD_SECONDS, "reading": "MEASURED_L2", "measured_l2_seconds": l2,
           "triggered": None if l2 is None else l2 > DS7_THRESHOLD_SECONDS, "decide_at": "FIRST_WORLD_TELEMETRY",
           "basis": projection["basis"],
           "projection": {"role": "INFORMATION_ONLY", "input_drain": drain, "projected_l2_seconds": projected,
                          "exceeds_threshold": None if projected is None else projected > DS7_THRESHOLD_SECONDS}}
    clone_seconds = [float(c["seconds"]) for c in clones]
    targets = [
        {"operation": "load_inputs", "target": "under 1 min", "against": "B1.L1", "measured_seconds": l1},
        {"operation": "run_pipeline_l2", "target": "under 45 min", "against": "B1.L2+B6", "measured_seconds": l2,
         "projected_seconds": projected},
        {"operation": "run_database", "target": "under 10 s", "against": "B2",
         "measured_seconds": max(clone_seconds) if clone_seconds else None},
        {"operation": "one_option_change", "target": "about 2 min", "state": "NOT_BUILT", "unit": "6a"},
        {"operation": "advance_one_day", "target": "under 1 min", "state": "NOT_BUILT", "unit": "DS6"},
    ]
    return {"format": FORMAT_BENCH, "meaning": BENCH_MEANING, "start": dict(start), "ladder": list(ladder),
            "clones": list(clones), "changes": {"late_commercial": late, "not_built": list(NOT_BUILT_CHANGES)},
            "pipeline": pipeline, "projection": proj, "ds7": ds7, "targets": targets}


def _bench_sweep(world: World) -> list[str]:
    """Drop every bench database, children before parents: the tool's own drop for each manifest, then any
    partial of the prefix without one. Returns the names dropped."""
    order = {"CLONE": 0, "L2": 1, "L1": 2, "L0": 3}
    dropped = []
    mine = [m for m in world.manifests() if _drop_pattern(world.prefix).fullmatch(m.get("database", ""))]
    for m in sorted(mine, key=lambda x: order.get(x.get("rung"), 9)):
        _drop(world, m["database"])
        dropped.append(m["database"])
    pattern = _drop_pattern(world.prefix)
    partials = sorted((r[0] for r in world.admin("SELECT datname FROM pg_database") if pattern.fullmatch(r[0])),
                      key=lambda n: 0 if "_audit_c_" in n else (1 if "_audit_l2_" in n else (2 if "_audit_l1_" in n else 3)))
    for name in partials:
        if not world.wait_idle(name):
            raise Refused("WORLD_DATABASE_IN_USE", name)
        world.drop_db(name)
        dropped.append(name)
    return dropped


def _rung_row(m: Mapping[str, Any], line: Mapping[str, Any] | None) -> dict:
    steps = [{"step": s["step"], "seconds": s["seconds"], "exit": s["exit"]} for s in m.get("steps") or []]
    return {"rung": m["rung"], "database": m["database"], "key12": m["key"][:12],
            "seconds": (line or {}).get("seconds", round(sum(s["seconds"] for s in steps), 3)),
            "steps_seconds": round(sum(s["seconds"] for s in steps), 3), "size_bytes": m.get("size_bytes"),
            "steps": steps}


def _late_csv(source: Path, target: Path) -> None:
    """B3's file: the generated billing file's header and its first `KOBO-001` row, `Revision` 2, `Amount` + 10.00."""
    import csv
    import io

    with source.open(newline="") as f:
        rows = list(csv.reader(f))
    header = rows[0]
    site, rev, amount = header.index("Site"), header.index("Revision"), header.index("Amount")
    row = list(next(r for r in rows[1:] if r[site] == LATE_SITE))
    row[rev] = "2"
    row[amount] = str((Decimal(row[amount]) + LATE_PLUS).quantize(Decimal("0.01")))
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows([header, row])
    target.write_text(buf.getvalue())


def _revenue(world: World, clone: str, tenant_id: str, snapshot_ids: Sequence[str]) -> list:
    """`actual.revenue` of each snapshot id on the bench clone, through the snapshot store (C4's read)."""
    from uuid import UUID

    url = rung_url(clone, world.environ)
    if world.deps.snapshots is not None:
        service = world.deps.snapshots(url)
    else:
        from assetops_backend.structure_snapshot.composition import build_structure_snapshot

        service = build_structure_snapshot(url)
    from assetops_backend.structure_snapshot import codec

    try:  # `get` returns the rows in the order given
        rows = [codec.payload_of(r) for r in service.store.get(UUID(tenant_id), [UUID(x) for x in snapshot_ids])]
    finally:
        service.dispose()
    out = []
    for p in rows:
        entry = (p.get("actual") or {}).get("revenue")
        out.append(entry.get("value") if isinstance(entry, Mapping) else None)
    return out


def _late_record(world: World, l2_name: str, l2: Mapping[str, Any]) -> dict:
    """B3: one late commercial record on clone `bl`, end to end; a refusal or another delta is recorded as found."""
    d = world.definition
    t = d.tenants[0]
    month = d.months[-1]
    kd = l2.get("key_dir")
    clone = _clone(world, LATE_LABEL, l2_name, l2)["database"]
    env = world.env(clone, t.slug, kd)
    late_dir = world.state / "tmp" / f"late-{os.getpid()}"
    steps: list = []
    found: dict = {"clone": clone, "steps": steps, "revenue_delta": None, "expected_delta": str(LATE_PLUS),
                   "state": "FOUND"}
    try:
        late_dir.mkdir(mode=0o700)
        _late_csv(Path(l2["inputs_dir"]) / t.slug / "commercial" / f"{t.slug}.billing.csv",
                  late_dir / f"{t.slug}.billing.csv")
        plan = [("B3.load", ["-m", "assetops_backend.load_emulated_exports", "--dir", str(late_dir), "--tenant", t.slug,
                             "--submit-as", t.submit_as, "--accept-as", t.accept_as]),
                ("B3.snapshot", ["-m", L2_STEPS[0][1], L2_STEPS[0][2], "--tenant", t.slug, "--month", month,
                                 "--by", d.built_by]),
                ("B3.observe", ["-m", L2_STEPS[1][1], L2_STEPS[1][2], "--tenant", t.slug, "--month", month])]
        new_sites: dict = {}
        for step, argv in plan:
            rc, _, rec = world.run_step(clone, step, argv, env, log=steps, fail=False)
            if step == "B3.snapshot":
                new_sites = (rec["out"] or {}).get("sites") or {}
            if rc != 0:
                found["refused_at"] = step
                break
        found["seconds"] = round(sum(s["seconds"] for s in steps), 3)
        old_id = ((l2.get("snapshots") or {}).get(f"{t.slug}:{month}") or {}).get("sites", {}).get(LATE_SITE)
        new_id = new_sites.get(LATE_SITE)
        if "refused_at" not in found and old_id and new_id:
            old, new = _revenue(world, clone, (l2.get("tenants") or {})[t.slug], [old_id, new_id])
            if old is not None and new is not None:
                delta = (Decimal(str(new)) - Decimal(str(old))).quantize(Decimal("0.01"))
                found["revenue_delta"] = str(delta)
                found["state"] = "AS_EXPECTED" if delta == LATE_PLUS else "FOUND"
            found["old_snapshot"], found["new_snapshot"] = old_id, new_id
    finally:
        shutil.rmtree(late_dir, ignore_errors=True)
        _drop(world, clone)
    for s in steps:
        s.pop("argv", None)
    return found


def _bench_start(world: World) -> dict:
    load = list(os.getloadavg())
    try:
        done = world.deps.runner(["bash", "tools/heavy-slot.sh", "--status"], str(REPO), world.env(None), 30.0)
        lines = (done.stdout or done.stderr or "").strip().splitlines()
        slot = lines[0] if lines else ""
    except (OSError, subprocess.TimeoutExpired) as error:
        slot = f"unread {type(error).__name__}"
    return {"loadavg": load, "slot": slot, "commit": world.git.head(), "at": _now_iso(world)}


def cmd_bench(world: World) -> int:
    evidence = bench_evidence_dir(world.args.evidence)
    key_root = _private_dir(Path(world.args.key_root), "WORLD_KEY_ROOT_INVALID")
    if world.prefix == DEFAULT_PREFIX:
        world.prefix = BENCH_PREFIX
    world.prepare()
    start = _bench_start(world)
    world.quiet = True
    ladder: list = []
    clones: list = []
    late = pipeline = None
    swept: dict = {}
    try:
        swept["before"] = _bench_sweep(world)
        manifests = _build(world, key_root)
        lines = {json.loads(x)["rung"]: json.loads(x) for x in world.out}
        ladder = [_rung_row(m, lines.get(m["rung"])) for m in manifests]
        l2 = manifests[2]
        made = []
        try:
            for label in BENCH_CLONES:
                m = _clone(world, label, l2["database"], l2)
                made.append(m["database"])
                size = world.admin("SELECT pg_database_size(:n)", {"n": m["database"]})
                clones.append({"label": label, "database": m["database"], "seconds": m["seconds"],
                               "size_bytes": int(size[0][0]) if size else None})
        finally:
            for name in made:
                _drop(world, name)
        late = _late_record(world, l2["database"], l2)
        code, out = harness_run(world, "b5", PIPELINE_TEST, {"ASSETOPS_DS4_BENCH": "1"}, args=("-s",))
        tail = out.strip().splitlines()[-1] if out.strip() else ""
        pipeline = {"exit": code, "tail": tail[:300], "marker": pipeline_marker(out),
                    "measured": pipeline_line(out)}
    finally:
        swept["after"] = _bench_sweep(world)
        world.quiet = False
    report = assemble_bench(start, ladder, clones, late, pipeline, world.definition.projection)
    report["dropped"] = swept
    evidence.mkdir(parents=True, exist_ok=True)
    path = evidence / "bench.json"
    path.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    world.emit({"report": str(path), "ds7": report["ds7"]})
    return 0


COMMANDS = {"build": cmd_build, "clone": cmd_clone, "reset": cmd_reset, "list": cmd_list, "drop": cmd_drop,
            "check": cmd_check, "bench": cmd_bench}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python tools/world.py", description="The demonstration world's template ladder.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        p.add_argument("--definition", default=DEFINITION)
        p.add_argument("--state", default=DEFAULT_STATE)
        p.add_argument("--prefix", default=DEFAULT_PREFIX)
        p.add_argument("--cap-seconds", type=float, default=7200.0 if name == "bench" else 3600.0)
        if name in ("build", "bench"):
            p.add_argument("--key-root", required=True)
        if name == "bench":
            p.add_argument("--evidence", required=True)
        if name in ("clone", "reset"):
            p.add_argument("--label", required=True)
        if name == "drop":
            p.add_argument("--database", required=True)
    return parser


def main(argv: Sequence[str] | None = None, *, deps: Deps | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    deps = deps or Deps()
    if args.command != "list":
        deps.require("world", db=True)
    world = World(args, deps)
    try:
        return COMMANDS[args.command](world)
    except Refused as r:
        sys.stderr.write(f"{r.code} {r.detail}\n")
        return 2
    except StepFailed as f:
        sys.stderr.write(f"STEP_FAILED {f.database} {f.step} {f.exit_code}\n")
        return 3
    except CapExceeded as c:
        sys.stderr.write(f"WORLD_CAP_EXCEEDED {c.step}\n")
        return 5
    finally:
        if deps.admin is None and isinstance(world.admin, Admin):
            world.admin.dispose()


if __name__ == "__main__":
    sys.exit(main())
