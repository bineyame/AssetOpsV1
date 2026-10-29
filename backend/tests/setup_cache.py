"""Build once, copy per test (PERF-02: T1 and T2 of the approved build-and-test performance plan).

The replay-chain and case fixtures build the same few site set-ups hundreds of times per run. This module wraps
the builder steps (the "ops", listed in OPS / FUNCTION_OPS) after collection. When an op is reached with the same
inputs as an earlier build, its result is restored instead of being rebuilt:

    database  the worker database is replaced by a copy of a saved template (CREATE DATABASE ... TEMPLATE)
    files     the op's working folder (a chain's tmp tree: run store, executions, stages, gateway state) is copied
              into this test's own tmp folder, with the old folder's absolute path rewritten in text files
    objects   the op's Python state (the chain's or runner's fields, or the function's return value) is unpickled,
              with live resources re-created: SQLAlchemy engines are new engines on the same URL, paths under the old
              tmp folder map to this test's folder, a chain's gateway child and its in-process central app start
              lazily on first use from the copied gateway state
    counter   the per-case UUID counter (`hold_uuids`) is set to where the original build left it

Every test still gets its own private copy; nothing is shared live. Assertions, test bodies and product code are
unchanged.

Key. An op's key is a SHA-256 over: the code fingerprint (product source, migrations, shipped config and
fixtures, the test helper and builder modules, this file), the op label, its plain arguments, the UUID counter
state, and - except for an op that starts from a fresh database - a digest of the worker database at the moment
the op starts (row counts of every table, a content hash of every table with at most 500 rows with timestamp
columns left out; sequence values are not part of it, so a restored build keeps the serial values of the
original build - the verify run reports any table where that shows). Two calls with equal keys start from equal states and run the same
code with the same inputs.

An op is never cached (it runs live, as before) when: a non-UUID monkeypatch is active in the test; another
session holds the worker database after our pools are disposed; an argument is not plain (except the known
fixture objects); or its state does not pickle. Nested ops run inside the outer one.

Switches (environment):
    ASSETOPS_SETUP_CACHE_DIR      enables the cache and names the folder for saved files and objects
    ASSETOPS_SETUP_CACHE=0        turns it off even when the folder is set (the old path, used for the proof run)
    ASSETOPS_SETUP_CACHE_VERIFY=1 every hit also runs live and compares its database rows, objects and UUID
                                  counter with the saved build (row fingerprints, copy against fresh build)
    ASSETOPS_SETUP_CACHE_LOG      folder for per-worker JSON lines of every op (hit/miss/live, reason, seconds)
Saved databases are named `assetops_sc_<code>_<key>_test` on the test server and are kept between runs (T2);
`tools/sweep-setup-cache.py` drops those of all but the newest three code fingerprints before each Docker run.
"""

from __future__ import annotations

import functools
import hashlib
import io
import json
import os
import pickle
import shutil
import sys
import threading
import time
import weakref
from pathlib import Path, PurePath

import pytest

DIR_ENV = "ASSETOPS_SETUP_CACHE_DIR"
SWITCH_ENV = "ASSETOPS_SETUP_CACHE"
VERIFY_ENV = "ASSETOPS_SETUP_CACHE_VERIFY"
LOG_ENV = "ASSETOPS_SETUP_CACHE_LOG"
CODE_ENV = "ASSETOPS_SETUP_CODE_FP"
REPO = Path(__file__).resolve().parents[2]
SMALL_TABLE = 500
TIME_TYPES = ("timestamp", "date", "time", "interval")

# (class, defining modules, methods, kind). "fresh-open": the op starts from pg_harness.fresh_database().
OPS = [
    ("Chain", ("test_w202_cold_replay_postgres", "test_w205b_ev_replay_postgres"), ("open",), "chain-open"),
    ("Chain", ("test_w202_cold_replay_postgres", "test_w205b_ev_replay_postgres"),
     ("start_release_upload", "release_and_upload", "advance_late"), "chain-step"),
]
# Not cached: CaseRunner (test_s4_finding_store_postgres). It shares the caller's live store and engine, whose
# in-memory state a restored copy cannot reproduce; a trial run failed its fences ("a cited evidence ID is not
# accepted in this Site"), so it keeps building live.
FUNCTION_OPS = [
    ("test_w402_reads_postgres", "_setup"),
    ("test_w402_reads_postgres", "_ingest"),
    ("test_w402_reads_postgres", "_reconcile"),
]
FINGERPRINT_TREES = ["backend/assetops_backend", "backend/migrations", "host", "gateway/assetops_gateway",
                     "gateway/tests", "simulator/assetops_simulator", "contracts/assetops_contracts", "config",
                     "contract-fixtures", "backend/tests/fixtures"]


class NotCached(Exception):
    """This op runs live; the message says why."""


# --- process state -----------------------------------------------------------------------------------------

_state: dict = {"depth": 0, "patches": 0, "engines": weakref.WeakSet(), "log": None, "stats": {}}


def enabled() -> bool:
    return bool(os.environ.get(DIR_ENV)) and os.environ.get(SWITCH_ENV, "1") != "0"


def verify() -> bool:
    return os.environ.get(VERIFY_ENV) == "1"


def code_fingerprint() -> str:
    """SHA-256 of every file a set-up depends on (computed once per run by the controller, passed in the env)."""
    if os.environ.get(CODE_ENV):
        return os.environ[CODE_ENV]
    digest = hashlib.sha256()
    files = []
    for tree in FINGERPRINT_TREES:
        root = REPO / tree
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                         and not p.name.endswith((".pyc", ".sqlite3")))
    tests = REPO / "backend" / "tests"
    files.extend(p for p in tests.glob("*.py") if not p.name.startswith("test_"))
    for _, modules, _, _ in OPS:
        files.extend(tests / f"{m}.py" for m in modules)
    files.extend(tests / f"{m}.py" for m, _ in FUNCTION_OPS)
    files.extend([tests / "test_s1_bindings_postgres.py", tests / "conftest.py"])
    for path in sorted(set(files)):
        digest.update(str(path.relative_to(REPO)).replace("\\", "/").encode())
        digest.update(b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    os.environ[CODE_ENV] = digest.hexdigest()
    return os.environ[CODE_ENV]


def _log(record: dict) -> None:
    stats = _state["stats"]
    stats[record["outcome"]] = stats.get(record["outcome"], 0) + 1
    directory = os.environ.get(LOG_ENV)
    if not directory:
        return
    if _state["log"] is None:
        os.makedirs(directory, exist_ok=True)
        worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
        _state["log"] = open(os.path.join(directory, f"setup-cache-{worker}.jsonl"), "a", encoding="utf-8")
    _state["log"].write(json.dumps(record, default=str) + "\n")
    _state["log"].flush()


# --- the database ------------------------------------------------------------------------------------------


def _harness():
    import pg_harness

    return pg_harness


def _admin():
    return _harness()._admin()


def _worker_name() -> str:
    if "worker" not in _state:
        _state["worker"] = _harness()._names()[1]
    return _state["worker"]


def _url() -> str:
    return os.environ[_harness().ENV]


def _quote(name: str) -> str:
    return _harness()._quote(name)


def _dispose_engines() -> None:
    for engine in list(_state["engines"]):
        try:
            engine.dispose()
        except Exception:  # noqa: BLE001
            pass


def _other_sessions(database: str) -> int:
    from sqlalchemy import text

    return _admin().execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname = :d AND pid <> pg_backend_pid()"),
                            {"d": database}).scalar_one()


def _release_worker() -> None:
    """Close every pooled connection of this process to the worker database; refuse when another remains."""
    _dispose_engines()
    worker = _worker_name()
    for _ in range(20):
        if not _other_sessions(worker):
            return
        time.sleep(0.05)
    raise NotCached("another session holds the worker database")


def _with_worker(fn):
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool

    engine = create_engine(_url(), poolclass=NullPool)
    try:
        with engine.connect() as connection:
            return fn(connection)
    finally:
        engine.dispose()


def _columns(connection) -> dict:
    from sqlalchemy import text

    rows = connection.execute(text(
        "SELECT c.table_name, c.column_name, c.data_type FROM information_schema.columns c "
        "JOIN information_schema.tables t ON t.table_name = c.table_name AND t.table_schema = c.table_schema "
        "WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE' ORDER BY c.table_name, c.ordinal_position"))
    tables: dict[str, list[tuple[str, str]]] = {}
    for table, column, kind in rows:
        tables.setdefault(table, []).append((column, kind))
    return tables


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def state_digest() -> str:
    """Digest of the worker database's state: counts, small-table content (no time columns), sequences."""
    from sqlalchemy import text

    def run(connection):
        tables = _columns(connection)
        if not tables:
            return "empty-schema"
        counts = {r[0]: r[1] for r in connection.execute(text(" UNION ALL ".join(
            f"SELECT '{t}', count(*) FROM {_q(t)}" for t in sorted(tables))))}
        parts = [json.dumps(sorted(counts.items()))]
        small = [t for t in sorted(tables) if 0 < counts[t] <= SMALL_TABLE]
        if small:
            selects = []
            for t in small:
                cols = [c for c, kind in tables[t] if not kind.startswith(TIME_TYPES)] or [tables[t][0][0]]
                expr = " || '|' || ".join(f"coalesce(CAST({_q(c)} AS text), '~')" for c in cols)
                selects.append(f"SELECT '{t}', md5(string_agg({expr}, '#' ORDER BY {expr})) FROM {_q(t)}")
            parts.append(json.dumps(sorted((r[0], r[1]) for r in connection.execute(text(" UNION ALL ".join(selects))))))
        _state["last_nonempty"] = {t: n for t, n in counts.items() if n}
        return hashlib.sha256("\n".join(parts).encode()).hexdigest()

    return _with_worker(run)


def row_fingerprint(tmp_root: str | None) -> dict:
    """Per-table row count and content hash (time columns left out; the tmp folder path normalised)."""
    from sqlalchemy import text

    def run(connection):
        out = {}
        for table, cols in sorted(_columns(connection).items()):
            kept = [c for c, kind in cols if not kind.startswith(TIME_TYPES)] or [cols[0][0]]
            rows = connection.execute(text(
                f"SELECT {', '.join(f'CAST({_q(c)} AS text)' for c in kept)} FROM {_q(table)}")).all()
            texts = sorted("|".join("~" if v is None else v for v in r) for r in rows)
            joined = "#".join(texts)
            has_tmp = bool(tmp_root) and tmp_root in joined
            if tmp_root:
                joined = joined.replace(tmp_root, "<TMP>")
            out[table] = [len(rows), hashlib.sha256(joined.encode()).hexdigest()[:16], has_tmp]
        return out

    return _with_worker(run)


def _snapshot_name(key: str) -> str:
    return f"assetops_sc_{code_fingerprint()[:8]}_{key[:20]}_test"


def _exists(name: str) -> bool:
    from sqlalchemy import text

    return bool(_admin().execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name}).scalar())


def _save_database(key: str) -> str:
    from sqlalchemy import text

    name = _snapshot_name(key)
    staging = name[: -len("_test")] + "_wip_test"  # every name stays *_test
    _release_worker()
    admin = _admin()
    admin.execute(text(f"DROP DATABASE IF EXISTS {_quote(staging)}"))
    admin.execute(text(f"CREATE DATABASE {_quote(staging)} TEMPLATE {_quote(_worker_name())}"))
    admin.execute(text(f"ALTER DATABASE {_quote(staging)} WITH ALLOW_CONNECTIONS false"))
    admin.execute(text(f"ALTER DATABASE {_quote(staging)} RENAME TO {_quote(name)}"))
    return name


def _reset_pristine() -> None:
    """The worker database back to a clean clone of the run's migrated template."""
    from sqlalchemy import text

    template = _harness()._ensure_template()
    _release_worker()
    worker = _worker_name()
    _admin().execute(text(f"DROP DATABASE IF EXISTS {_quote(worker)} WITH (FORCE)"))
    _harness()._create(worker, template)


def _restore_database(name: str) -> None:
    from sqlalchemy import text

    _release_worker()
    worker = _worker_name()
    _admin().execute(text(f"DROP DATABASE IF EXISTS {_quote(worker)} WITH (FORCE)"))
    _harness()._create(worker, name)


# --- files -------------------------------------------------------------------------------------------------


def _copy_tree(source: Path, target: Path, old: str | None = None, new: str | None = None) -> int:
    count = 0
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir() and not path.is_symlink():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        if not path.is_file():
            continue  # sockets, pipes: the gateway recreates them
        destination.parent.mkdir(parents=True, exist_ok=True)
        if old and new and old != new and path.suffix in (".json", ".yaml", ".yml", ".txt", "") \
                and path.stat().st_size < 4_000_000:
            data = path.read_bytes()
            if old.encode() in data:
                destination.write_bytes(data.replace(old.encode(), new.encode()))
                shutil.copymode(path, destination)
                count += 1
                continue
        shutil.copy2(path, destination)
        count += 1
    return count


# --- objects -----------------------------------------------------------------------------------------------


class _LazyGateway:
    """Stands in for a restored chain's gateway child and central app; starts them on first use."""

    def __init__(self, chain) -> None:
        self._chain = chain
        self._process = None
        self._central = None
        self._requests: list = []  # what the original central app had recorded (tests read central.requests)

    def _start(self):
        if self._process is None:
            self._process, self._central = _start_gateway(self._chain)
            self._central.requests[:0] = self._requests
        return self._process

    def requests_so_far(self) -> list:
        return list(self._central.requests) if self._central is not None else list(self._requests)

    def __getattr__(self, name):
        return getattr(self._start(), name)

    def kill(self) -> None:
        if self._process is not None:
            self._process.kill()

    def close_central(self) -> None:
        if self._central is not None:
            self._central.close()


class _LazyCentral:
    def __init__(self, gateway: _LazyGateway) -> None:
        self._gateway = gateway

    def __getattr__(self, name):
        self._gateway._start()
        return getattr(self._gateway._central, name)

    def close(self) -> None:
        self._gateway.close_central()


class _LazyLink:
    def __init__(self, gateway: _LazyGateway) -> None:
        self._gateway = gateway

    def __getattr__(self, name):
        return getattr(self._gateway._start().link, name)


def _start_gateway(chain):
    """The second half of the chain's `_gateway()`: the in-process central app and the gateway child, on the copied
    gateway state, with the new central address written into the copied config."""
    module = sys.modules[type(chain).__module__]
    g = module.__dict__
    url = g["URL"]
    central_app = g["FastAPI"]()
    g["install_gateway_tls_boundary"](central_app)
    if hasattr(chain, "decision_clock"):
        ledger = g["PostgresEvidenceLedger"](url, test_decision_clock_override=chain.decision_clock)
        batch = g["BatchIngestionService"](ledger, chain.decision_clock)
    else:
        from datetime import datetime, timezone

        batch = g["BatchIngestionService"](g["PostgresEvidenceLedger"](url), lambda: datetime.now(timezone.utc))
    central_app.include_router(g["build_evidence_router"](
        g["IngestionService"](None, g["_NoSites"]()), g["_NoSites"](), batch_ingestion=batch,
        gateway_principals=g["StoreGatewayPrincipals"](g["PostgresGatewayAccess"](url))))
    client = g["TestClient"](central_app, base_url="https://testserver")

    def forward(path, headers, body):
        wanted = {k: v for k, v in headers.items() if k.lower() in ("authorization", "content-type")}
        answer = client.post(path, content=body, headers=wanted)
        return answer.status_code, answer.content

    central = g["FakeCentral"](forward)
    config = Path(chain.tmp) / "gateway" / "gateway.json"
    document = json.loads(config.read_text(encoding="utf-8"))
    document["upload"]["server_url"] = central.url
    config.write_text(json.dumps(document), encoding="utf-8")
    process = g["GatewayProcess"](config)
    assert process.ready, process.first_line
    # A restarted gateway makes one upload pass at start (a diagnostic for the current clock slot). Finish it now,
    # under the gateway's own lock, so it cannot land in the middle of the test's next step.
    g["RegisteredGatewayPublisher"](process.link).deliver(50)
    time.sleep(0.2)
    return process, central


_RLOCK_TYPE = type(threading.RLock())
_LOCK_TYPES = (type(threading.Lock()), _RLOCK_TYPE)


class _Pickler(pickle.Pickler):
    def __init__(self, file, context) -> None:
        super().__init__(file, protocol=pickle.HIGHEST_PROTOCOL)
        self.context = context

    def persistent_id(self, obj):
        from sqlalchemy.engine import Engine

        c = self.context
        for i, arg in enumerate(c["args"]):
            if obj is arg and not isinstance(arg, (str, int, float, bool, type(None), tuple)):
                return ("arg", i)
        if obj is c.get("self"):
            return ("self",)
        if isinstance(obj, Engine):
            return ("engine", obj.url.render_as_string(hide_password=False))
        if isinstance(obj, _LOCK_TYPES):
            return ("lock", isinstance(obj, _RLOCK_TYPE))  # a store's write lock: a new, free lock
        if isinstance(obj, type(sys)):
            return ("module", obj.__name__)
        name = type(obj).__name__
        if name in ("GatewayProcess", "_LazyGateway"):
            return ("gateway",)
        if name == "FakeCentral":
            return ("central", list(obj.requests))
        if name == "_LazyCentral":
            return ("central", obj._gateway.requests_so_far())
        if name == "GatewayLink" or name == "_LazyLink":
            return ("link",)
        if name == "CachedScenarioRepository":
            return ("scenarios",)
        if isinstance(obj, PurePath) and c.get("tmp"):
            text = str(obj)
            if text == c["tmp"] or text.startswith(c["tmp"] + os.sep):
                return ("tmp", os.path.relpath(text, c["tmp"]))
        return None


class _Unpickler(pickle.Unpickler):
    def __init__(self, file, context) -> None:
        super().__init__(file)
        self.context = context
        self.engines: dict[str, object] = {}

    def persistent_load(self, pid):
        from sqlalchemy import create_engine

        c = self.context
        kind = pid[0]
        if kind == "arg":
            return c["args"][pid[1]]
        if kind == "self":
            return c["self"]
        if kind == "engine":
            if pid[1] not in self.engines:
                self.engines[pid[1]] = create_engine(_url())
            return self.engines[pid[1]]
        if kind == "lock":
            return threading.RLock() if pid[1] else threading.Lock()
        if kind == "module":
            import importlib

            return importlib.import_module(pid[1])
        if kind == "gateway":
            return c["gateway"]
        if kind == "central":
            c["gateway"]._requests = list(pid[1]) if len(pid) > 1 else []
            return _LazyCentral(c["gateway"])
        if kind == "link":
            return _LazyLink(c["gateway"])
        if kind == "scenarios":
            from scenario_cache import cached_scenario_repository

            return cached_scenario_repository()
        if kind == "tmp":
            return Path(c["tmp"]) / pid[1] if pid[1] != "." else Path(c["tmp"])
        raise pickle.UnpicklingError(pid)


def _dumps(value, context) -> bytes:
    buffer = io.BytesIO()
    try:
        _Pickler(buffer, context).dump(value)
    except Exception as error:  # noqa: BLE001
        where = ""
        fields = value.get("fields") if isinstance(value, dict) else None
        if isinstance(fields, dict):  # name the fields that do not pickle
            bad = []
            for k, v in fields.items():
                try:
                    _Pickler(io.BytesIO(), context).dump(v)
                except Exception:  # noqa: BLE001
                    bad.append(f"{k}:{type(v).__name__}")
            where = f" (fields {', '.join(bad)})"
        raise NotCached(f"state does not pickle: {type(error).__name__}: {str(error)[:120]}{where}") from error
    return buffer.getvalue()


def _loads(data: bytes, context):
    return _Unpickler(io.BytesIO(data), context).load()


# --- keys --------------------------------------------------------------------------------------------------

_FIXTURE_TYPES = ("Engine", "PostgresFoundationStore", "SubRequest", "MonkeyPatch", "CaptureFixture",
                  "FixtureRequest", "MgW402Install")


def _plain(value, depth=0):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)) and depth < 4:
        return [_plain(v, depth + 1) for v in value]
    if isinstance(value, dict) and depth < 4:
        return {str(k): _plain(v, depth + 1) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if callable(value) and hasattr(value, "__code__"):
        code = value.__code__
        if value.__closure__:
            raise NotCached(f"argument {value.__qualname__} is a closure")
        return f"fn:{value.__module__}.{value.__qualname__}:{hashlib.sha256(code.co_code).hexdigest()[:12]}"
    if type(value).__name__ == "module":
        return f"module:{value.__name__}"
    name = type(value).__name__
    if name in _FIXTURE_TYPES:
        if name == "MgW402Install":  # a W4 set-up's return value: its identity is the database state
            return f"<{name}>"
        if hasattr(value, "param"):
            return {"request.param": _plain(getattr(value, "param", None), depth + 1)}
        return f"<{name}>"
    raise NotCached(f"argument of type {name} is not plain")


def _uuid_counter():
    """The `hold_uuids` counter cell, or None when IDs are not pinned."""
    module = sys.modules.get("assetops_backend.runs.identity")
    holder = getattr(module, "uuid", None)
    fn = getattr(holder, "uuid4", None)
    closure = getattr(fn, "__closure__", None)
    if not closure:
        return None
    for name, cell in zip(fn.__code__.co_freevars, closure):
        if name == "counter":
            return cell.cell_contents
    return None


def _uuid_state():
    counter = _uuid_counter()
    if counter is None:
        return None
    fn = sys.modules["assetops_backend.runs.identity"].uuid.uuid4
    tag = dict(zip(fn.__code__.co_freevars, (c.cell_contents for c in fn.__closure__))).get("tag")
    return [tag, counter["n"]]


# --- the op wrapper ----------------------------------------------------------------------------------------


# --- code that an op runs: no function or class may have been swapped by direct assignment -----------------------

_REPO_TEXT = str(REPO)


_BUILDER_MODULES = {m for _, modules, _, _ in OPS for m in modules} | {m for m, _ in FUNCTION_OPS}


def _repo_modules():
    """Product, host, gateway, simulator and contract modules, test helpers and the builder test modules."""
    for name, module in list(sys.modules.items()):
        path = str(getattr(module, "__file__", "") or "")
        if not path.startswith(_REPO_TEXT) or ".venv" in path or "site-packages" in path:
            continue
        base = name.rsplit(".", 1)[-1]
        if base in ("setup_cache", "phase_attribution", "phase_timing", "conftest"):
            continue
        if base.startswith("test_") and base not in _BUILDER_MODULES:
            continue
        yield name, module



def _callables(module):
    for attr, value in list(vars(module).items()):
        if attr in _UUID_NAMES or attr.startswith("__"):
            continue
        if callable(value):
            yield attr, value
            if isinstance(value, type) and getattr(value, "__module__", None) == module.__name__:
                for method, function in list(vars(value).items()):
                    if callable(function) and not method.startswith("__"):
                        yield f"{attr}.{method}", function


def _code_baseline() -> None:
    _state["baseline"] = {name: {a: id(v) for a, v in _callables(m)} for name, m in _repo_modules()}


def _swapped() -> str | None:
    """The first repository function or class rebound since the baseline (a direct-assignment patch), if any."""
    baseline = _state.get("baseline")
    if baseline is None:
        return None
    for name, module in _repo_modules():
        known = baseline.get(name)
        if known is None:
            baseline[name] = {a: id(v) for a, v in _callables(module)}
            continue
        for attr, value in _callables(module):
            if known.get(attr, id(value)) != id(value) and not getattr(value, "__setup_cache__", False):
                return f"{name}.{attr}"
    return None


def _context(kind, args, chain_tmp):
    return {"args": list(args), "self": args[0] if kind != "function" else None, "tmp": chain_tmp}


def run_op(original, kind: str, label: str, args, kwargs):
    if not enabled() or _state["depth"] or not _harness().routed():
        return original(*args, **kwargs)
    started = time.perf_counter()
    record = {"op": label, "kind": kind, "test": os.environ.get("PYTEST_CURRENT_TEST", "").split(" ")[0]}
    try:
        if _state["patches"]:
            raise NotCached("a monkeypatch other than the UUID counter is active: "
                            + ", ".join(_state.get("patch_names", [])[-4:]))
        swapped = _swapped()
        if swapped:
            raise NotCached(f"{swapped} is rebound by direct assignment")
        fresh = kind == "chain-open" and kwargs.get("fresh", True)
        if kind == "chain-open" and kwargs.get("scenarios") is not None:
            raise NotCached("an injected scenario repository")
        plain_args = _plain(list(args[1:] if kind != "function" else args))
        self_fields = None
        if kind == "chain-step":
            self_fields = {k: _plain(v) for k, v in vars(args[0]).items()
                           if isinstance(v, (str, int, float, bool, type(None)))}
        if kind == "chain-open":
            self_fields = {"case": args[0].case, "site_code": getattr(args[0], "site_code", None),
                           "seed": getattr(args[0], "seed", None)}
        pristine = False
        if not fresh and kind in ("object", "function") and not _state.get("ops_in_test") \
                and not _state.get("test_writes") and not _state.get("seeded", {}).get(_state.get("module")):
            # The first op of a test that wrote nothing itself, in a module whose fixtures seed nothing: its start
            # state is the module's clone plus other tests' leftovers, which it is not meant to see. It starts
            # from the clean clone instead, so equal ops share one saved build.
            pristine = True
        start_state = None if fresh else ("pristine-clone" if pristine else state_digest())
        fresh_start = fresh
        key = hashlib.sha256(json.dumps([code_fingerprint(), label, plain_args, _plain(kwargs), self_fields,
                                         _uuid_state(), start_state], default=str).encode()).hexdigest()
        record["key"] = key[:20]
    except Exception as reason:  # noqa: BLE001 - the cache never fails a test before the op: it runs live
        record.update(outcome="live", reason=f"{type(reason).__name__}: {str(reason)[:300]}")
        _state["depth"] += 1
        try:
            return original(*args, **kwargs)
        finally:
            _state["depth"] -= 1
            record["seconds"] = round(time.perf_counter() - started, 3)
            _log(record)
    _state["ops_in_test"] = _state.get("ops_in_test", 0) + 1
    folder = Path(os.environ[DIR_ENV]) / code_fingerprint()[:8] / key[:20]
    name = _snapshot_name(key)
    meta_path = folder / "meta.pkl"
    chain_tmp = str(args[0].tmp) if kind.startswith("chain") else None
    hit = meta_path.exists() and _exists(name)
    if hit and not verify():
        try:
            result = _restore(kind, args, folder, name, chain_tmp)
            record.update(outcome="hit", seconds=round(time.perf_counter() - started, 3))
            _log(record)
            return result
        except NotCached as reason:
            record["restore_refused"] = str(reason)
    if pristine:
        _reset_pristine()
        record["reset_to_clone"] = True
    _state["depth"] += 1
    try:
        result = original(*args, **kwargs)
    finally:
        _state["depth"] -= 1
    record["build_seconds"] = round(time.perf_counter() - started, 3)
    try:
        if hit and verify():
            record.update(outcome="verify", **_compare(kind, args, result, folder, chain_tmp))
        elif not hit:
            _save(kind, args, result, folder, key, chain_tmp)
            record["outcome"] = "miss"
            if not fresh_start:
                record["start_nonempty"] = _state.get("last_nonempty")
        else:
            record["outcome"] = "live"
    except Exception as reason:  # noqa: BLE001 - after a live op the result stands; the save is skipped
        record.update(outcome="live", reason=f"{type(reason).__name__}: {str(reason)[:300]}")
    record["seconds"] = round(time.perf_counter() - started, 3)
    _log(record)
    return result


def _state_to_save(kind, args, result):
    if kind.startswith("chain") or kind == "object":
        fields = dict(vars(args[0]))
        if kind.startswith("chain"):
            fields.pop("tmp", None)
            fields.pop("host", None)  # rebuilt from the copied folders, see _rebind_host
        return {"fields": fields, "result_is_self": result is args[0] or result is None}
    return {"result": result}


def _save(kind, args, result, folder, key, chain_tmp) -> None:
    context = _context(kind, args, chain_tmp)
    payload = _dumps(_state_to_save(kind, args, result), context)
    fingerprint = row_fingerprint(chain_tmp) if verify() else None
    lock = f"assetops-setup-cache:{key[:20]}"
    from sqlalchemy import text

    admin = _admin()
    admin.execute(text("SELECT pg_advisory_lock(hashtext(:k))"), {"k": lock})
    try:
        if _exists(_snapshot_name(key)):
            return
        staging = folder.with_name(folder.name + f".{os.getpid()}")
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        if chain_tmp and Path(chain_tmp).exists():
            _copy_tree(Path(chain_tmp), staging / "files")
        meta = {"payload": payload, "tmp": chain_tmp, "uuid": _uuid_state(), "fingerprint": fingerprint,
                "kind": kind, "result_is_self": kind != "function"}
        (staging / "meta.pkl").write_bytes(pickle.dumps(meta))
        shutil.rmtree(folder, ignore_errors=True)
        staging.rename(folder)
        _save_database(key)
    finally:
        admin.execute(text("SELECT pg_advisory_unlock(hashtext(:k))"), {"k": lock})


def _restore(kind, args, folder, name, chain_tmp):
    meta = pickle.loads((folder / "meta.pkl").read_bytes())
    if (meta["uuid"] is None) != (_uuid_counter() is None):
        raise NotCached("UUID pinning differs from the saved build")
    chain = args[0] if kind.startswith("chain") else None
    gateway = None
    if chain is not None:
        old = getattr(chain, "process", None)
        started = (old is not None and type(old).__name__ == "GatewayProcess") or             (isinstance(old, _LazyGateway) and old._process is not None)
        if started:  # a gateway running on the files about to be replaced: stop it, a lazy one takes over
            for closing in (old.kill, getattr(chain, "central", None) and chain.central.close):
                try:
                    closing and closing()
                except Exception:  # noqa: BLE001
                    pass
        gateway = old if isinstance(old, _LazyGateway) and not started else _LazyGateway(chain)
    _restore_database(name)
    if chain is not None:
        target = Path(chain_tmp)
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        if (folder / "files").exists():
            _copy_tree(folder / "files", target, meta["tmp"], chain_tmp)
    context = _context(kind, args, chain_tmp)
    context["gateway"] = gateway
    state = _loads(meta["payload"], context)
    if meta["uuid"] is not None:
        _uuid_counter()["n"] = meta["uuid"][1]
    if kind == "function":
        return state["result"]
    obj = args[0]
    for k, v in state["fields"].items():
        setattr(obj, k, v)
    if chain is not None:
        _rebind_host(chain, gateway)
        return chain
    return None


def _rebind_host(chain, gateway) -> None:
    g = sys.modules[type(chain).__module__].__dict__
    tmp = Path(chain.tmp)
    inputs = {}
    if "StoreEvInputs" in g and hasattr(chain, "decision_clock"):
        inputs["ev_inputs"] = g["StoreEvInputs"](chain.store, g["cached_scenario_repository"]())
    else:
        inputs["cold_inputs"] = g["StoreColdInputs"](chain.store, g["cached_scenario_repository"]())
    chain.host = g["HostLabExecution"](
        artifacts=g["YamlExecutionArtifacts"](tmp / "executions"), stages=g["JsonSourceStages"](tmp / "stages"),
        gateway=g["RegisteredGatewayPublisher"](_LazyLink(gateway)),
        schedules=g["JsonPublicationSchedules"](tmp / "schedules"), source_publisher=g["publisher_for"](g["URL"]),
        **inputs)


def _compare(kind, args, result, folder, chain_tmp) -> dict:
    meta = pickle.loads((folder / "meta.pkl").read_bytes())
    out = {"uuid_equal": meta["uuid"] == _uuid_state()}
    saved = meta.get("fingerprint")
    if saved is None:
        out["rows"] = "no saved fingerprint (cache not built in verify mode)"
        return out
    live = row_fingerprint(chain_tmp)
    tables = sorted(set(saved) | set(live))
    out["tables"] = len(tables)
    out["count_mismatch"] = [t for t in tables if (saved.get(t) or [None])[0] != (live.get(t) or [None])[0]]
    out["content_mismatch"] = [t for t in tables if t not in out["count_mismatch"]
                               and (saved.get(t) or [0, None])[1] != (live.get(t) or [0, None])[1]]
    out["tmp_path_in_rows"] = [t for t in tables if (live.get(t) or [0, 0, False])[2]]
    out["rows_equal"] = not out["count_mismatch"] and not out["content_mismatch"]
    return out


# --- installation ------------------------------------------------------------------------------------------


def _wrap_method(cls, method, kind):
    original = vars(cls)[method]
    if getattr(original, "__setup_cache__", False):
        return
    label = f"{cls.__module__}.{cls.__name__}.{method}"

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        return run_op(original, kind, label, args, kwargs)

    wrapper.__setup_cache__ = True
    setattr(cls, method, wrapper)


def _wrap_function(module_name, attr):
    module = sys.modules.get(module_name)
    original = getattr(module, attr, None) if module else None
    if original is None or getattr(original, "__setup_cache__", False):
        return
    label = f"{module_name}.{attr}"

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        return run_op(original, "function", label, args, kwargs)

    wrapper.__setup_cache__ = True
    for m in list(sys.modules.values()):
        namespace = getattr(m, "__dict__", None)
        if isinstance(namespace, dict):
            for name, value in list(namespace.items()):
                if value is original:
                    try:
                        setattr(m, name, wrapper)
                    except Exception:  # noqa: BLE001
                        pass


def install() -> None:
    for class_name, modules, methods, kind in OPS:
        for module_name in modules:
            module = sys.modules.get(module_name)
            cls = getattr(module, class_name, None) if module else None
            if isinstance(cls, type):
                for method in methods:
                    if method in vars(cls):
                        _wrap_method(cls, method, kind)
    for module_name, attr in FUNCTION_OPS:
        _wrap_function(module_name, attr)


_WRITES = ("INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE", "COPY", "MERGE")


def _track_engines() -> None:
    """Pools to dispose before a save or restore, and the test's own writes to the worker database."""
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    if _state.get("tracking"):
        return

    def on_connect(connection):
        _state["engines"].add(connection.engine)

    def on_execute(conn, cursor, statement, parameters, context, executemany):
        if _state["depth"] or _state.get("emptying") or _state.get("phase") is None:
            return
        if not statement.lstrip()[:8].upper().startswith(_WRITES):
            return
        try:
            if conn.engine.url.database != _worker_name():
                return  # the harness's admin connection, not the worker database
        except Exception:  # noqa: BLE001
            return
        scope = _state.get("fixture_scope")
        if scope and scope != "function":  # a wider fixture seeds the module's database: no clean-clone start
            _state.setdefault("seeded", {})[_state.get("module")] = True
        else:
            _state["test_writes"] = _state.get("test_writes", 0) + 1

    event.listen(Engine, "engine_connect", on_connect)
    event.listen(Engine, "before_cursor_execute", on_execute)
    _state["tracking"] = True


def _track_emptying() -> None:
    harness = _harness()
    original = harness.empty_tables
    if getattr(original, "__setup_cache__", False):
        return

    @functools.wraps(original)
    def empty_tables(*args, **kwargs):
        _state["emptying"] = True
        try:
            return original(*args, **kwargs)
        finally:
            _state["emptying"] = False

    empty_tables.__setup_cache__ = True
    for m in list(sys.modules.values()):
        namespace = getattr(m, "__dict__", None)
        if isinstance(namespace, dict):
            for name, value in list(namespace.items()):
                if value is original:
                    try:
                        setattr(m, name, empty_tables)
                    except Exception:  # noqa: BLE001
                        pass


_UUID_NAMES = {"uuid4", "uuid"}


def _track_monkeypatch() -> None:
    """Count active non-UUID monkeypatches of the running test (the cache refuses while any is active)."""
    if _state.get("mp"):
        return
    original_setattr = pytest.MonkeyPatch.setattr
    original_setenv = pytest.MonkeyPatch.setenv
    original_setitem = pytest.MonkeyPatch.setitem
    original_delattr = pytest.MonkeyPatch.delattr
    original_undo = pytest.MonkeyPatch.undo

    def counted(fn, name_of):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            name = name_of(args)
            target = args[0] if args else None
            internal = (getattr(type(target), "__module__", "") or "").startswith(("_pytest", "pytest")) or                 (getattr(target, "__name__", "") or "").startswith(("_pytest", "pytest"))
            if name not in _UUID_NAMES and not internal:  # pytest's own session patches are not the test's
                _state["patches"] += 1
                _state.setdefault("patch_names", []).append(f"{fn.__name__}:{_describe(args)}")
                self.__dict__["_setup_cache_patches"] = self.__dict__.get("_setup_cache_patches", 0) + 1
            return fn(self, *args, **kwargs)
        return wrapper

    def _describe(args):
        target = args[0] if args else None
        what = target if isinstance(target, str) else getattr(target, "__name__", type(target).__name__)
        return f"{what}.{args[1]}" if len(args) > 1 and isinstance(args[1], str) else str(what)[:60]

    def setattr_name(args):
        if len(args) >= 2 and isinstance(args[0], str) and not isinstance(args[1], str):
            return args[0].rsplit(".", 1)[-1]  # monkeypatch.setattr("pkg.mod.name", value)
        return args[1] if len(args) >= 2 and isinstance(args[1], str) else None

    pytest.MonkeyPatch.setattr = counted(original_setattr, setattr_name)
    pytest.MonkeyPatch.setenv = counted(original_setenv, lambda a: "env")
    pytest.MonkeyPatch.setitem = counted(original_setitem, lambda a: "item")
    pytest.MonkeyPatch.delattr = counted(original_delattr, lambda a: "del")

    @functools.wraps(original_undo)
    def undo(self):
        _state["patches"] = max(0, _state["patches"] - self.__dict__.pop("_setup_cache_patches", 0))
        if not _state["patches"]:
            _state["patch_names"] = []
        return original_undo(self)

    pytest.MonkeyPatch.undo = undo
    _state["mp"] = True


class SetupCachePlugin:
    def pytest_collection_finish(self, session) -> None:
        install()
        _track_emptying()
        self._modules = len(sys.modules)


    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        if len(sys.modules) != getattr(self, "_modules", 0):
            install()
            self._modules = len(sys.modules)
            _state["baseline"] = None
        if _state.get("baseline") is None:  # after every wrapper of this process is installed
            _code_baseline()
        _state.update(ops_in_test=0, test_writes=0, phase="setup", module=getattr(item.module, "__name__", ""))
        yield
        _state["phase"] = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef, request):
        outer = _state.get("fixture_scope")
        _state["fixture_scope"] = fixturedef.scope
        try:
            yield
        finally:
            _state["fixture_scope"] = outer

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        _state["phase"] = "call"
        yield
        _state["phase"] = None

    def pytest_sessionfinish(self) -> None:
        if _state["log"] is not None:
            _state["log"].write(json.dumps({"summary": True, "stats": _state["stats"]}) + "\n")
            _state["log"].close()
            _state["log"] = None


def register(config) -> None:
    if not enabled() or config.pluginmanager.has_plugin("assetops-setup-cache"):
        return
    code_fingerprint()
    _track_engines()
    _track_monkeypatch()
    config.pluginmanager.register(SetupCachePlugin(), "assetops-setup-cache")
