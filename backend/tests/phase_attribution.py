"""Measured time attribution per test (PERF-01, owner 2026-10-29: "i want the actual run to be timed and actual
time attributed").

Off unless `ASSETOPS_TEST_ATTRIBUTION` names an output directory. When on, each test process (every xdist worker,
or the single serial process) wraps a fixed list of functions after collection and records, per test, the wall
time spent inside them by category. Exclusive time: a call nested in another wrapped call counts for the inner
category only, so the categories of one test never overlap and sum to at most its measured duration:

    db        run-database create/clone/drop, table cleanup, Alembic migrations (pg_harness, alembic.command)
    install   Site / Foundation install and gateway credential issue (install_*_lab, install_mg_w402_site,
              provision_gateway.main)
    gateway   gateway subprocess start and stop (GatewayProcess.__init__ / kill)
    build     replay / ingest / seed: the replay chains (Chain.open and its release/upload steps), the host lab
              execution and gateway publisher, batch ingestion, and the named seed helpers (portfolio, estate,
              mixed replay, CaseRunner, the W4 mini-grid set-up / ingest / reconcile, s3/s6 record builders)
    app       FastAPI app, router and TestClient construction and lifespan
    subprocess any other child process waited on (subprocess.run, Popen.wait / communicate)

The remainder of the set-up phase is `setup_other` (other fixture work), of the call phase `checks` (the test's own
work), and the teardown phase is `teardown` in full. One JSON line per test goes to
`<dir>/attribution-<worker>.jsonl`, with wall-clock start/end, the pytest phase durations, the categories, SQL
statement and write counts per category (a SQLAlchemy `before_cursor_execute` listener on every engine in the
process), and the fingerprint of every root site build (the builder and its plain arguments, plus the ordered
replay steps on a chain object), so distinct set-ups and their rebuild counts can be counted.

It changes no test body, fixture, assertion or return value: wrappers call through and re-raise. Statements from
child processes (gateway, tick children) are not seen; the gateway's uploads are, because they are ingested
in-process. Overhead is measured by `tools/attribution-overhead.py`.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import sys
import threading
import time

import pytest

ENV = "ASSETOPS_TEST_ATTRIBUTION"
CATEGORIES = ("db", "install", "gateway", "build", "app", "subprocess")
WRITE_VERBS = ("INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE", "COPY", "MERGE", "GRANT")

# (module names, attribute path, category, root-build fingerprint kind or None)
FUNCTIONS = [
    (("pg_harness",), "fresh_database", "db", None),
    (("pg_harness",), "empty_tables", "db", None),
    (("alembic.command",), "upgrade", "db", None),
    (("alembic.command",), "downgrade", "db", None),
    (("assetops_backend.sites.cold_lab",), "install_cold_lab", "install", None),
    (("assetops_backend.sites.ev_lab",), "install_ev_lab", "install", None),
    (("assetops_backend.sites.w402_demo",), "install_mg_w402_site", "install", None),
    (("assetops_backend.evidence.provision_gateway",), "main", "install", None),
    (("test_w303_portfolio_fixture_postgres",), "build_portfolio_fixture", "build", "call"),
    (("test_w301_estate_index_postgres",), "power_estate", "build", "call"),
    (("test_w301_estate_golden_postgres",), "mixed_replay", "build", "call"),
    (("test_w402_reads_postgres",), "_setup", "build", "call"),
    (("test_w402_reads_postgres",), "_ingest", "build", "call"),
    (("test_w402_reads_postgres",), "_reconcile", "build", "call"),
    (("s3_claim_limit_records",), "build", "build", "call"),
    (("s6_action_records",), "build", "build", "call"),
    (("subprocess",), "run", "subprocess", None),
]
# (class name, defining-module candidates, methods, category, fingerprint kind)
METHODS = [
    ("GatewayProcess", ("gateway_process",), ("__init__", "kill"), "gateway", None),
    ("Chain", ("test_w202_cold_replay_postgres", "test_w205b_ev_replay_postgres"), ("open",), "build", "chain-open"),
    ("Chain", ("test_w202_cold_replay_postgres", "test_w205b_ev_replay_postgres"),
     ("start_release_upload", "release_and_upload", "advance_late", "attest"), "build", "chain-step"),
    ("CaseRunner", ("test_s4_finding_store_postgres",), ("__init__",), "build", "runner-init"),
    ("CaseRunner", ("test_s4_finding_store_postgres",), ("step",), "build", "runner-step"),
    ("HostLabExecution", ("lab_execution",), ("start", "release_registered", "advance_publication"), "build", None),
    ("RegisteredGatewayPublisher", ("gateway_publication",), ("deliver",), "build", None),
    ("BatchIngestionService", ("assetops_backend.evidence.ledger_service",), None, "build", None),
    ("FastAPI", ("fastapi.applications", "fastapi"), ("__init__", "include_router"), "app", None),
    ("APIRouter", ("fastapi.routing",), ("add_api_route", "include_router"), "app", None),
    ("TestClient", ("starlette.testclient",), ("__init__", "__enter__", "__exit__"), "app", None),
    ("Popen", ("subprocess",), ("wait", "communicate"), "subprocess", None),
]


def _plain(value, depth: int = 0):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if depth < 3 and isinstance(value, (list, tuple)):
        return [_plain(v, depth + 1) for v in value]
    if depth < 3 and isinstance(value, dict):
        return {str(k): _plain(v, depth + 1) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # noqa: BLE001
            pass
    if hasattr(value, "param") and type(value).__name__ in ("SubRequest", "FixtureRequest", "TopRequest"):
        return {"request.param": _plain(getattr(value, "param", None), depth + 1)}
    name = getattr(value, "__name__", None)
    return f"<{name or type(value).__name__}>"


class Recorder:
    def __init__(self, directory: str, worker: str) -> None:
        os.makedirs(directory, exist_ok=True)
        self._out = open(os.path.join(directory, f"attribution-{worker}.jsonl"), "a", encoding="utf-8")
        self.worker = worker
        self.thread = None
        self.stack: list[list] = []  # [category, start, child_seconds, fingerprint-or-None]
        self.wrapped_calls = 0
        self.statements = 0
        self.patched: list[str] = []
        self.listening = False
        self._reset()

    def _reset(self) -> None:
        self.cats = {c: 0.0 for c in CATEGORIES}
        self.phase_cats = {"setup": {c: 0.0 for c in CATEGORIES}, "call": {c: 0.0 for c in CATEGORIES}}
        self.stmts: dict[str, int] = {}
        self.writes: dict[str, int] = {}
        self.builds: list = []
        self.check_tables: dict[str, int] = {}
        self.chain_steps: dict[int, list] = {}
        self.phase = None

    # --- wrapping ---------------------------------------------------------------------------------------

    def wrap(self, original, category: str, kind: str | None, label: str):
        recorder = self

        @functools.wraps(original)
        def wrapper(*args, **kwargs):
            if recorder.phase is None or threading.get_ident() != recorder.thread:
                return original(*args, **kwargs)
            stack = recorder.stack
            if category == "subprocess" and any(f[0] == "gateway" for f in stack):
                return original(*args, **kwargs)
            recorder.wrapped_calls += 1
            fingerprint = None
            if kind is not None and not any(f[3] is not None for f in stack):
                fingerprint = recorder._fingerprint(kind, label, args, kwargs)
            frame = [category, time.perf_counter(), 0.0, fingerprint]
            stack.append(frame)
            try:
                return original(*args, **kwargs)
            finally:
                stack.pop()
                elapsed = time.perf_counter() - frame[1]
                own = elapsed - frame[2]
                if stack:
                    stack[-1][2] += elapsed
                bucket = recorder.phase_cats.get(recorder.phase)
                if bucket is not None:
                    bucket[category] += own

        wrapper.__assetops_attribution__ = original
        return wrapper

    def _fingerprint(self, kind: str, label: str, args, kwargs):
        if kind == "chain-open":
            chain = args[0]
            key = [label, getattr(chain, "case", None), _plain(kwargs)]
            self.chain_steps[id(chain)] = key
            self.builds.append(key)
            return key
        if kind == "chain-step":
            key = self.chain_steps.get(id(args[0]))
            if key is not None:
                key.append(label.rsplit(".", 1)[-1])
                return key
            key = [label]
            self.builds.append(key)
            return key
        if kind == "runner-init":
            key = [label, _plain(args[3:]), _plain(kwargs)]
            self.chain_steps[id(args[0])] = key
            self.builds.append(key)
            return key
        if kind == "runner-step":
            key = self.chain_steps.get(id(args[0]))
            if key is not None:
                key.append(hashlib.sha256(json.dumps(_plain(args[1:]), sort_keys=True).encode()).hexdigest()[:8])
                return key
        key = [label, _plain(args), _plain(kwargs)]
        self.builds.append(key)
        return key

    def on_statement(self, statement: str) -> None:
        if self.phase is None:
            return
        self.statements += 1
        top = self.stack[-1][0] if self.stack else ("checks" if self.phase == "call" else
                                                     "setup_other" if self.phase == "setup" else "teardown")
        self.stmts[top] = self.stmts.get(top, 0) + 1
        verb = statement.lstrip()[:8].upper()
        if verb.startswith(WRITE_VERBS):
            self.writes[top] = self.writes.get(top, 0) + 1
            if top == "checks":
                shape = " ".join(statement.split()[:4])[:80]
                self.check_tables[shape] = self.check_tables.get(shape, 0) + 1

    # --- per test ---------------------------------------------------------------------------------------

    def start_test(self) -> None:
        self._reset()
        self.thread = threading.get_ident()
        self.t0 = time.time()

    def finish_test(self, item, durations: dict) -> None:
        setup, call, teardown = (durations.get(k, 0.0) for k in ("setup", "call", "teardown"))
        cats = {c: round(self.phase_cats["setup"][c] + self.phase_cats["call"][c], 4) for c in CATEGORIES}
        row = {
            "nodeid": item.nodeid, "worker": self.worker, "t0": self.t0, "t1": time.time(),
            "setup": round(setup, 4), "call": round(call, 4), "teardown": round(teardown, 4),
            "cats": cats,
            "setup_cats": {c: round(v, 4) for c, v in self.phase_cats["setup"].items() if v},
            "setup_other": round(max(0.0, setup - sum(self.phase_cats["setup"].values())), 4),
            "checks": round(max(0.0, call - sum(self.phase_cats["call"].values())), 4),
            "stmts": self.stmts, "writes": self.writes,
            "builds": [json.dumps(b, sort_keys=True, default=str) for b in self.builds],
            "check_writes": dict(sorted(self.check_tables.items(), key=lambda kv: -kv[1])[:8]),
        }
        self._out.write(json.dumps(row) + "\n")
        self._out.flush()
        self._reset()

    def close(self) -> None:
        self._out.write(json.dumps({"summary": True, "worker": self.worker, "wrapped_calls": self.wrapped_calls,
                                    "statements": self.statements, "patched": self.patched}) + "\n")
        self._out.close()


def _replace_everywhere(original, wrapper) -> int:
    count = 0
    for module in list(sys.modules.values()):
        namespace = getattr(module, "__dict__", None)
        if not isinstance(namespace, dict):
            continue
        for name, value in list(namespace.items()):
            if value is original:
                try:
                    setattr(module, name, wrapper)
                    count += 1
                except Exception:  # noqa: BLE001
                    pass
    return count


def install(recorder: Recorder) -> None:
    """Wrap the targets that are loaded now (called after collection, so test modules are imported)."""
    for modules, attr, category, kind in FUNCTIONS:
        seen = set()
        for name in modules:
            for module_name in (name, f"tests.{name}"):
                module = sys.modules.get(module_name)
                original = getattr(module, attr, None) if module else None
                if original is None or id(original) in seen or hasattr(original, "__assetops_attribution__"):
                    continue
                seen.add(id(original))
                wrapper = recorder.wrap(original, category, kind, f"{name}.{attr}")
                _replace_everywhere(original, wrapper)
                recorder.patched.append(f"{module_name}.{attr}")
    for class_name, modules, methods, category, kind in METHODS:
        classes = []
        for name in modules:
            for module_name in (name, f"tests.{name}"):
                module = sys.modules.get(module_name)
                cls = getattr(module, class_name, None) if module else None
                if isinstance(cls, type) and cls not in classes:
                    classes.append(cls)
        for cls in classes:
            names = methods or [n for n, v in vars(cls).items() if callable(v) and not n.startswith("__")]
            for method in names:
                original = vars(cls).get(method)
                if original is None or hasattr(original, "__assetops_attribution__"):
                    continue
                label = f"{cls.__module__}.{cls.__name__}.{method}"
                setattr(cls, method, recorder.wrap(original, category, kind, label))
                recorder.patched.append(label)
    if not recorder.listening:
        try:
            from sqlalchemy import event
            from sqlalchemy.engine import Engine

            def listener(conn, cursor, statement, parameters, context, executemany):
                recorder.on_statement(statement)

            event.listen(Engine, "before_cursor_execute", listener)
            recorder.listening = True
            recorder.patched.append("sqlalchemy.Engine.before_cursor_execute")
        except Exception:  # noqa: BLE001
            pass


class AttributionPlugin:
    def __init__(self, directory: str, worker: str) -> None:
        self.recorder = Recorder(directory, worker)
        self._durations: dict = {}
        self._modules = 0

    def pytest_collection_finish(self, session) -> None:
        install(self.recorder)
        self._modules = len(sys.modules)

    def _phase(self, name):
        self.recorder.phase = name

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        self._durations = {}
        self.recorder.start_test()
        yield
        self.recorder.phase = None
        self.recorder.finish_test(item, self._durations)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        self._phase("setup")
        yield
        self._phase(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        if len(sys.modules) != self._modules:  # a module imported lazily by an earlier test may hold a target
            install(self.recorder)
            self._modules = len(sys.modules)
        self._phase("call")
        yield
        self._phase(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item, nextitem):
        self._phase("teardown")
        yield
        self._phase(None)

    def pytest_runtest_logreport(self, report) -> None:
        self._durations[report.when] = report.duration

    def pytest_sessionfinish(self) -> None:
        self.recorder.close()


def register(config, worker: str) -> None:
    directory = os.environ.get(ENV)
    if directory and not config.pluginmanager.has_plugin("assetops-attribution"):
        config.pluginmanager.register(AttributionPlugin(directory, worker), "assetops-attribution")
