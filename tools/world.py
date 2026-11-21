"""DS4 (spec `specs/DS4-template-ladder/spec.md`; D-DS4.1 to D-DS4.25): the demonstration world as a template ladder.

    python tools/world.py build --key-root DIR      L0 schema, L1 inputs, L2 computed; each rebuilt only when its key changes
    python tools/world.py clone --label L           a run's database, cloned from the current L2
    python tools/world.py reset --label L           drop that clone, then clone it again
    python tools/world.py check                     the world check on a check clone (C1 to C7)
    python tools/world.py list                      the manifests and whether each database exists
    python tools/world.py drop --database NAME      one database the tool built, children first

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

    # output
    def emit(self, obj: Mapping[str, Any]) -> None:
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
            argv = ["tools/world_history.py", "exports", "--manifest", d.manifest, "--out", str(exports)]
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
            files = {p.relative_to(staged).as_posix(): sha256_file(p) for p in sorted(staged.rglob("*")) if p.is_file()}
            digest = inputs_digest(files, {t.slug: sha256_file(REPO / t.onboarding) for t in d.tenants})
            final = self.state / "inputs" / digest[:12]
            if not final.exists():
                os.replace(staged, final)
            return digest, final, files
        finally:
            shutil.rmtree(exports, ignore_errors=True)
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
        parts, keys, _ = self.ladder_parts()
        name = check_name(name_for(self.prefix, "L2", keys[2][:12]), self.environ)
        m = self.read_manifest(name)
        if m is not None and m.get("key") == keys[2] and self.exists(name):
            return name, m
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

    _rung(world, "L2", keys[2], parts[2], m1["database"], l2)
    return 0


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


# --- check (§3.6) and bench (§4): unit 2 and unit 3 -----------------------------------------------------------------

def cmd_check(world: World) -> int:
    raise Refused("WORLD_NO_TEMPLATE", "check is unit 2")


COMMANDS = {"build": cmd_build, "clone": cmd_clone, "reset": cmd_reset, "list": cmd_list, "drop": cmd_drop,
            "check": cmd_check}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python tools/world.py", description="The demonstration world's template ladder.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        p.add_argument("--definition", default=DEFINITION)
        p.add_argument("--state", default=DEFAULT_STATE)
        p.add_argument("--prefix", default=DEFAULT_PREFIX)
        p.add_argument("--cap-seconds", type=float, default=7200.0 if name == "bench" else 3600.0)
        if name == "build":
            p.add_argument("--key-root", required=True)
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
