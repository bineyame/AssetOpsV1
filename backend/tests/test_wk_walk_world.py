"""WK (spec `specs/WK-walkthrough-database/spec.md` rev 2 §4, T1 to T12): `tools/walk_world.py` with fakes; no database."""
from __future__ import annotations

import ast
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import walk_world as WK  # noqa: E402
import world  # noqa: E402

SOURCE = ROOT / "tools/walk_world.py"
DEFINITION = ROOT / "backend/conversions/world-layer4-v1.json"
WALK_DEFINITION = ROOT / "backend/conversions/walk-layer4-v1.json"
DERIVED = ROOT / "Docs/demo-sprint/product-direction-layer4/derived-values.json"
TID = "11111111-2222-4333-8444-555555555555"
L2 = "assetops_world_audit_l2_" + "a" * 12
WALK = "assetops_polish_walk1123_test"
COMMIT = "c" * 40
PORTFOLIO_OLD = "00000000-0000-4000-8000-0000000000aa"
PORTFOLIO = "00000000-0000-4000-8000-000000000000"
SITE_IDS = {"KISIWA-001": "00000000-0000-4000-8000-000000000001", "KOBO-001": "00000000-0000-4000-8000-000000000002",
            "MTO-001": "00000000-0000-4000-8000-000000000003"}
AS_OF = "2026-11-21T10:00:00.123456+00:00"
PARENT_CENSUS = {"commercial_accounts_statement": 0, "site": 3, "structure_snapshot": 4, "tenant": 1}
FORBIDDEN = {"PGDATABASE": "x", "PGHOST": "elsewhere", "PGPORT": "1", "PGSERVICE": "s", "PGHOSTADDR": "h",
             "PGSERVICEFILE": "f", "ASSETOPS_PSEUDONYM_KEY_DIR": "/k", "ASSETOPS_REAL_OPERATOR_DATA": "1",
             "ASSETOPS_OPERATIONAL_ENTRY": "1", "ASSETOPS_READING_UPLOAD_GATEWAY": "g", "ASSETOPS_GATEWAY_X": "1",
             "ASSETOPS_LIVE_FIELD_X": "1", "ASSETOPS_PERIOD_READ_KINDS": "k", "ASSETOPS_TENANT_SLUG": "other",
             "PW": "/pw", "AUDIT_LD_LIBRARY_PATH": "/lib", "SECRET": "s"}


# --- fakes -----------------------------------------------------------------------------------------------------------

class FakeAdmin:
    def __init__(self, log: list) -> None:
        self.log, self.dbs, self.sessions, self.allowconn = log, {L2}, {}, {L2: False}

    def __call__(self, sql, params=None):
        params = dict(params or {})
        self.log.append(("admin", sql, params))
        if sql.startswith("SELECT datname FROM pg_database WHERE datname LIKE"):
            return [(d,) for d in sorted(self.dbs) if d.startswith("assetops_polish_walk")]
        if sql.startswith("SELECT 1 FROM pg_database"):
            return [(1,)] if params["n"] in self.dbs else []
        if sql.startswith("SELECT count(*) FROM pg_stat_activity"):
            return [(self.sessions.get(params["n"], 0),)]
        if sql.startswith("SELECT datallowconn"):
            return [(self.allowconn[params["n"]],)] if params["n"] in self.allowconn else []
        m = re.match(r'CREATE DATABASE "([^"]+)"', sql)
        if m:
            self.dbs.add(m.group(1))
            return []
        m = re.match(r'DROP DATABASE "([^"]+)"', sql)
        if m:
            self.dbs.discard(m.group(1))
            return []
        raise AssertionError(sql)

    def ddl(self):
        return [s for _, s, _ in self.log if not s.startswith("SELECT")]


class FakeGit:
    def __init__(self) -> None:
        self.head_id = COMMIT

    def tree(self, path):
        return "id-" + path

    def dirty(self, paths):
        return []

    def head(self):
        return self.head_id


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def monotonic(self):
        self.t += 0.5
        return self.t

    def now(self):
        from datetime import datetime, timezone
        return datetime(2026, 11, 21, 10, 0, 0, tzinfo=timezone.utc)

    def sleep(self, s):
        self.t += s


class FakeRunner:
    def __init__(self, env: "Env") -> None:
        self.env, self.calls, self.fail_on = env, [], None
        self.verify_ok, self.tree_head, self.node_exit, self.after_node = True, COMMIT, 0, None

    def __call__(self, argv, cwd, env, timeout):
        argv = list(argv)
        self.calls.append((argv, dict(env), cwd))
        if argv[:2] == ["git", "-C"]:
            return subprocess.CompletedProcess(argv, 0, self.tree_head + "\n", "")
        if argv[:2] == ["bash", "-c"]:
            out = "PW=/pw/pc\nCHROME=/pw/chrome\nFONTCONFIG_FILE=/pw/fonts.conf\nAUDIT_LD_LIBRARY_PATH=/pw/lib\n"
            return subprocess.CompletedProcess(argv, 0, out, "")
        if argv[:1] == ["node"]:
            if self.after_node:
                self.after_node()
            return subprocess.CompletedProcess(argv, self.node_exit, "{}\n", "")
        args = argv[1:]
        label = " ".join(args[:3])
        if self.fail_on and self.fail_on in " ".join(args):
            return subprocess.CompletedProcess(argv, 3, "", "boom")
        if label == "-m assetops_backend.reconcile_month record":
            self.env.census["commercial_accounts_statement"] += 1
            return subprocess.CompletedProcess(argv, 0, json.dumps({"recorded": True}) + "\n", "")
        if label == "-m assetops_backend.build_structure_snapshot build":
            self.env.census["structure_snapshot"] += 1 + len(SITE_IDS)
            out = {"as_of": AS_OF, "portfolio_snapshot_id": PORTFOLIO, "sites": SITE_IDS, "excluded": [],
                   "rules_digest": "r" * 64}
            return subprocess.CompletedProcess(argv, 0, json.dumps(out) + "\n", "")
        if label == "-m assetops_backend.build_structure_snapshot verify":
            out = {"snapshot_id": PORTFOLIO, "matches": self.verify_ok, "differences": [], "rules_changed": False}
            return subprocess.CompletedProcess(argv, 0 if self.verify_ok else 4, json.dumps(out) + "\n", "")
        raise AssertionError(argv)

    def steps(self):
        return [c for c in self.calls if c[0][:1] == [sys.executable]]


class FakeProcs(WK.Procs):
    """The real `Procs` over an injected process table: `/proc/<pid>/stat` and `cmdline`, `getpgid`, the PID list,
    `killpg` and `popen` are fakes. `table[pid]` is `{"cmd", "start", "pgrp", "sid"}`."""

    def __init__(self) -> None:
        super().__init__(read=self._read, getpgid=self._getpgid, pids=lambda: sorted(self.table),
                         killpg=self._kill, popen=self._popen)
        self.next, self.spawned, self.table, self.signals, self.busy, self.dead = 4000, [], {}, [], set(), set()
        self.ignore_term, self.spawn_error = set(), None
        self.clock = 1000

    def _popen(self, argv, cwd, env, stdout, stderr, start_new_session):
        assert start_new_session is True
        if self.spawn_error and argv[:1] == [self.spawn_error]:
            raise FileNotFoundError(argv[0])
        self.next += 1
        self.clock += 7
        pid = self.next
        self.table[pid] = {"cmd": list(argv), "start": self.clock, "pgrp": pid, "sid": pid}
        self.spawned.append({"pid": pid, "argv": list(argv), "cwd": cwd, "env": dict(env), "log": stdout.name})
        if argv[:1] == ["npm"]:
            self.busy.add(int(argv[argv.index("--port") + 1]))
        return SimpleNamespace(pid=pid, poll=lambda: 1 if pid in self.dead else None)

    def _read(self, path):
        _, _, pid, leaf = path.split("/")
        t = self.table.get(int(pid))
        if t is None:
            return None
        if leaf == "cmdline":
            return b"".join(c.encode() + b"\0" for c in t["cmd"])
        fields = ["S", "1", str(t["pgrp"]), str(t["sid"])] + ["0"] * 15 + [str(t["start"]), "0"]
        return f"{pid} (x y) {' '.join(fields)}\n".encode()

    def _getpgid(self, pid):
        t = self.table.get(pid)
        return None if t is None else t["pgrp"]

    def _kill(self, pgid, sig):
        self.signals.append((pgid, sig))
        for p in [p for p, t in self.table.items() if t["pgrp"] == pgid]:
            if sig == signal.SIGKILL or p not in self.ignore_term:
                del self.table[p]

    def set_cmd(self, pid, cmd):
        self.table[pid]["cmd"] = list(cmd)

    def port_busy(self, port):
        return port in self.busy


class FakeWorld(world.World):
    """The real `World` over fakes, with the ladder's answers set by the test."""

    def __init__(self, args, deps, env: "Env") -> None:
        super().__init__(args, deps)
        self.t = env

    def prepare(self, *, need_definition=True, clean=True):
        self.t.calls.append("prepare")
        self.state = world.state_dirs(Path(self.args.state))
        self.definition = world.read_definition(DEFINITION)

    def current_l2(self):
        self.t.calls.append("current_l2")
        if self.t.l2_refusal:
            raise world.Refused(*self.t.l2_refusal)
        return L2, self.t.l2

    def check_state(self, l2):
        self.t.calls.append("check_state")
        return self.t.check


def hand_payload(code):
    """A Site payload meeting C4's contract exactly, from `derived-values.json`."""
    derived = json.loads(DERIVED.read_text())
    name = {"KISIWA-001": "Kisiwa", "KOBO-001": "Kobo", "MTO-001": "Mto"}[code]
    exp = derived["sites"][f"lakeside-power/{name}"]
    sides = {}
    for side in ("actual", "plan"):
        sides[side] = {f: ({"value": str(x), "missing": None, "missing_leaves": []}
                           if world.site_class(code, side, f) == "E"
                           else {"value": None, "missing": {"record_kind": "REC"}, "missing_leaves": []})
                       for f, x in exp[side]["nodes"].items()}
    return {"site_code": code, "actual": sides["actual"], "targets": {"values": sides["plan"]}}


def month_ok():
    return {"state": "SERVED", "as_of": "2026-11-21T10:00:00Z", "fresh": {"current": True, "text": None,
                                                                        "untracked_text": None},
            "standing": {"reconciled": True, "reason": None, "text": "t", "details": []},
            "tiles": [{"key": "contribution", "bar": {"actual": "1443.00", "target": "2295.00"}},
                      {"key": "gap", "bar": None}]}


class Env:
    def __init__(self, tmp_path: Path) -> None:
        self.calls: list = []
        self.log: list = []
        self.admin = FakeAdmin(self.log)
        self.git = FakeGit()
        self.runner = FakeRunner(self)
        self.procs = FakeProcs()
        self.required: list = []
        self.state = tmp_path / "state"
        os.mkdir(self.state, 0o700)
        self.tree = tmp_path / "tree"
        (self.tree / "host").mkdir(parents=True)
        (self.tree / "frontend").mkdir()
        self.environ = {"PATH": "/usr/bin", "HOME": "/home/x", "LANG": "C.UTF-8", "ASSETOPS_PG_PORT": "55432",
                        "ASSETOPS_PG_PASSWORD": "pw"}
        self.l2 = {"database": L2, "rung": "L2", "key": "k" * 64, "tenants": {"lakeside-power": TID},
                   "key_dir": "/x/l1", "census": dict(PARENT_CENSUS),
                   "snapshots": {"lakeside-power:2026-10": {"portfolio_snapshot_id": PORTFOLIO_OLD, "sites": SITE_IDS}}}
        self.l2_refusal = None
        self.check = (True, None)
        self.census = dict(PARENT_CENSUS)
        self.walk_tenants = [(TID, "lakeside-power")]
        self.urls: list = []
        self.month = month_ok()
        self.http_answers: dict = {}
        self.disposed: list = []
        self.payloads = {c: hand_payload(c) for c in SITE_IDS}
        self.deps = WK.WalkDeps(
            world=world.Deps(admin=self.admin, query=self.query, runner=self.runner, git=self.git, clock=FakeClock(),
                             require=lambda tool, db=False: self.required.append((tool, db)), environ=self.environ,
                             snapshots=self.snapshot_service),
            http=self.http, procs=self.procs, world_factory=lambda ns, d: FakeWorld(ns, d, self),
            deep_dive=self.deep_dive, foundation=self.foundation)

    # walk database fakes
    def query(self, url, sqls):
        self.urls.append(url)
        out = []
        for s in sqls:
            if s == world.CENSUS_TABLES:
                out.append([(t,) for t in sorted(self.census)])
            elif s == world.TENANTS:
                out.append(list(self.walk_tenants))
            else:
                t = re.match(r'SELECT count\(\*\) FROM "([^"]+)"', s).group(1)
                out.append([(self.census[t],)])
        return out

    def snapshot_service(self, url):
        from assetops_backend.structure_snapshot import codec
        self.urls.append(url)
        codes = {v: k for k, v in SITE_IDS.items()}

        def get(tenant_id, ids):
            rows = []
            for i in ids:
                text = json.dumps(self.payloads[codes[str(i)]])
                rows.append(SimpleNamespace(payload=text, payload_sha256=codec.digest(text)))
            return tuple(rows)

        return SimpleNamespace(store=SimpleNamespace(get=get), dispose=lambda: self.disposed.append("snapshots"))

    def foundation(self, url):
        self.urls.append(url)
        env = self

        class Store:
            def resolve_tenant(self, slug):
                env.calls.append(("resolve_tenant", slug))
                return SimpleNamespace(id=TID, slug=slug, name="Lakeside Power")

            def list_sites(self, tid):
                rec = SimpleNamespace()
                return (SimpleNamespace(site_code="KOBO-001", name="Kobo Site", import_record=rec),
                        SimpleNamespace(site_code="DRAFT-001", name="Draft", import_record=None))
        return Store()

    def deep_dive(self, url):
        self.urls.append(url)
        env = self

        class Read:
            def month(self, tenant, month, names):
                env.calls.append(("month", tenant.name, month, dict(names), os.environ.get("ASSETOPS_TENANT_SLUG")))
                return env.month
        return Read(), lambda: self.disposed.append("deep_dive")

    def http(self, url, timeout):
        self.calls.append(("http", url))
        for k, v in self.http_answers.items():
            if url.endswith(k):
                return v
        if url.endswith("/api/health"):
            return 200, b"{}"
        if "/api/portfolio/month" in url:
            return 200, json.dumps(self.month).encode()
        return 404, b""

    def main(self, *argv):
        args = [argv[0], "--label", "1123", "--state", str(self.state), *argv[1:]]
        return WK.main(args, deps=self.deps)

    def manifest(self):
        p = self.state / "walks" / f"{WALK}.json"
        return json.loads(p.read_text()) if p.is_file() else None

    def write_manifest(self, m):
        (self.state / "walks").mkdir(mode=0o700, exist_ok=True)
        (self.state / "walks" / f"{WALK}.json").write_text(json.dumps(m))

    def copied(self):
        assert self.main("copy") == 0
        return self.manifest()

    def prepared(self):
        self.copied()
        assert self.main("prepare") == 0
        return self.manifest()

    def checked(self):
        self.prepared()
        assert self.main("check") == 0
        return self.manifest()

    def served(self):
        self.checked()
        assert self.main("serve", "--tree", str(self.tree)) == 0
        return self.manifest()


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("ASSETOPS_TENANT_SLUG", raising=False)
    return Env(tmp_path)


def _lines(capsys):
    out = capsys.readouterr()
    return [json.loads(x) for x in out.out.splitlines() if x.strip()], out.err


def _refusal(capsys):
    return capsys.readouterr().err.strip().split("\n")[-1]


# --- T1 names and the walk URL (D-WK.11) ------------------------------------------------------------------------------

def test_t1_labels_and_names():
    env = {"ASSETOPS_PG_PORT": "55432"}
    assert WK.walk_name("1123") == WALK
    assert WK.walk_url("1123", env).endswith(f"@127.0.0.1:55432/{WALK}")
    assert WK.walk_name("1123b") == "assetops_polish_walk1123b_test"
    with pytest.raises(world.Refused) as r:
        WK.walk_name("1113")
    assert r.value.code == "WALK_PROTECTED"
    for bad in ("abc", "11234", "1123B", "", "112", "1123bb", "1123_"):
        with pytest.raises(world.Refused) as r:
            WK.walk_url(bad, env)
        assert r.value.code == "WALK_LABEL_INVALID", bad
    from assetops_backend.database_target import is_operator_name
    for label in ("0000", "9999z", "1123", "1123b"):
        name = WK.walk_name(label)
        assert len(name.encode()) <= 63 and not is_operator_name(name) and WK.walk_name_ok(name)


def test_t1_walk_name_ok_refuses():
    for name in ("assetops_polish_walk1113_test", "assetops_op_lakeside", "ASSETOPS_OP_X", "assetops_opx_test",
                 "assetops_world_audit_l2_1906a5d074a0", "assetops_polish_walk1123", "Assetops_polish_walk1123_test",
                 "assetops_polish_walk1123_test2", "assetops_polish_walk1123B_test"):
        assert not WK.walk_name_ok(name), name
    assert WK.walk_name_ok(WALK)


def test_t1_walk_url_target_checks(monkeypatch):
    for env, why in (({"ASSETOPS_PG_PORT": "5490"}, "port"), ({"ASSETOPS_PG_PORT": "55432", "PGHOST": "x"},
                                                              "ENVIRONMENT PGHOST"),
                     ({"ASSETOPS_PG_PORT": "55432", "PGDATABASE": "other"}, "ENVIRONMENT PGDATABASE")):
        with pytest.raises(world.Refused) as r:
            WK.walk_url("1123", env)
        assert (r.value.code, r.value.detail) == ("WALK_TARGET_UNCLEAR", why)
    monkeypatch.setattr(world, "rung_url", lambda n, e: f"postgresql+psycopg://a:b@10.0.0.5:55432/{n}")
    with pytest.raises(world.Refused) as r:
        WK.walk_url("1123", {"ASSETOPS_PG_PORT": "55432"})
    assert (r.value.code, r.value.detail) == ("WALK_TARGET_UNCLEAR", "host")
    monkeypatch.setattr(world, "rung_url", lambda n, e: "postgresql+psycopg://a:b@127.0.0.1:55432/assetops_other_test")
    with pytest.raises(world.Refused) as r:
        WK.walk_url("1123", {"ASSETOPS_PG_PORT": "55432"})
    assert (r.value.code, r.value.detail) == ("WALK_TARGET_UNCLEAR", "name")


def test_t1_cli_label_refusals(env, capsys):
    for label, code in (("1113", "WALK_PROTECTED"), ("abc", "WALK_LABEL_INVALID")):
        assert WK.main(["copy", "--label", label, "--state", str(env.state)], deps=env.deps) == 2
        assert _refusal(capsys).startswith(code)
    assert env.admin.ddl() == [] and "current_l2" not in env.calls


# --- the walk definition (§2) ------------------------------------------------------------------------------------------

def _walkdef(tmp_path, mutate):
    d = json.loads(WALK_DEFINITION.read_text())
    mutate(d)
    p = tmp_path / "walk.json"
    p.write_text(json.dumps(d))
    return p


def test_walk_definition_committed_reads():
    wd = WK.read_walk_definition(WALK_DEFINITION, world.read_definition(DEFINITION))
    assert [s["fuel_cost"] for s in wd.statements] == ["5100.00", "5000.00"]
    assert all(s["source_ref"].startswith("Emulated management accounts, October 2026, ") for s in wd.statements)
    assert wd.serve == {"tenant": "lakeside-power", "port": 8991, "web_port": 5491}
    assert wd.expect["contribution_actual"] == "1443.00" and wd.expect["reconciled"] is True
    assert "site_id" not in WALK_DEFINITION.read_text() and "site_code" not in WALK_DEFINITION.read_text()


@pytest.mark.parametrize("mutate,where", [
    (lambda d: d.update(extra=1), "$"),
    (lambda d: d.update(world="other"), "$.world"),
    (lambda d: d["statements"][0].update(tenant="nobody"), "$.statements[0].tenant"),
    (lambda d: d["statements"][1].update(period="2026-09"), "$.statements[1].period"),
    (lambda d: d["statements"][0].update(revenue="9700.0"), "$.statements[0].revenue"),
    (lambda d: d["statements"][0].update(fuel_cost="-1.00"), "$.statements[0].fuel_cost"),
    (lambda d: d.update(rebuild_by="robot"), "$.rebuild_by"),
    (lambda d: d["serve"].update(port=8990), "$.serve.port"),
    (lambda d: d["serve"].update(web_port=5490), "$.serve.web_port"),
    (lambda d: d["serve"].update(port=80), "$.serve.port"),
    (lambda d: d["serve"].update(port="8991"), "$.serve.port"),
    (lambda d: d["expect"].update(reconciled="yes"), "$.expect.reconciled"),
    (lambda d: d["pages"].append("/sites/{code}/x"), "$.pages"),
    (lambda d: d["pages"].remove("/sites/{code}"), "$.pages"),
])
def test_walk_definition_strict(tmp_path, mutate, where):
    with pytest.raises(world.Refused) as r:
        WK.read_walk_definition(_walkdef(tmp_path, mutate), world.read_definition(DEFINITION))
    assert (r.value.code, r.value.detail) == ("WALK_DEFINITION_INVALID", where)


# --- T2 copy refusals -------------------------------------------------------------------------------------------------

def test_t2_copy_refusals_in_order(env, capsys):
    env.l2_refusal = ("WORLD_TEMPLATE_STALE", "code.backend/assetops_backend")
    assert env.main("copy") == 2
    assert _refusal(capsys) == "WORLD_TEMPLATE_STALE code.backend/assetops_backend"
    env.l2_refusal = None
    for state, want in (((None, "manifest"), "WALK_CHECK_STALE manifest"), ((None, None), "WALK_NOT_CHECKED"),
                        ((False, None), "WALK_CHECK_FAILED")):
        env.check = state
        assert env.main("copy") == 2
        assert _refusal(capsys).startswith(want)
    env.check = (True, None)
    env.admin.dbs.add(WALK)
    assert env.main("copy") == 2
    assert _refusal(capsys) == f"WALK_EXISTS {WALK}"
    env.admin.dbs.discard(WALK)
    env.write_manifest({"database": WALK})
    assert env.main("copy") == 2
    assert _refusal(capsys) == f"WALK_EXISTS {WALK}"
    (env.state / "walks" / f"{WALK}.json").unlink()
    env.admin.sessions[L2] = 1
    assert env.main("copy") == 2
    assert _refusal(capsys) == f"WALK_DATABASE_IN_USE {L2}"
    assert env.admin.ddl() == []
    assert env.required and all(r == ("walk", True) for r in env.required)


# --- T3 copy success --------------------------------------------------------------------------------------------------

def test_t3_copy_issues_one_ddl_and_writes_the_manifest(env, capsys):
    env.admin.dbs.add("assetops_polish_walk1120_test")
    assert env.main("copy") == 0
    assert env.admin.ddl() == [f'CREATE DATABASE "{WALK}" TEMPLATE "{L2}" STRATEGY FILE_COPY']
    m = env.manifest()
    assert set(m) == {"format", "database", "label", "parent", "parent_key", "commit", "copied_at", "seconds",
                      "tenants", "key_dir", "parent_census", "parent_snapshots", "steps", "walks_before", "snapshots",
                      "check", "serve"}
    assert (m["format"], m["database"], m["label"], m["parent"], m["parent_key"], m["commit"]) == (
        "assetops.walk-build/1", WALK, "1123", L2, "k" * 64, COMMIT)
    assert m["walks_before"] == ["assetops_polish_walk1120_test"] and m["steps"] == [] and m["snapshots"] is None
    assert m["parent_census"] == PARENT_CENSUS and m["tenants"] == {"lakeside-power": TID}
    assert m["copied_at"] == "2026-11-21T10:00:00Z"
    assert oct(os.stat(env.state / "walks").st_mode & 0o777) == "0o700"
    (line,), _ = _lines(capsys)
    assert line == {"database": WALK, "parent": L2, "parent_key12": "k" * 12, "seconds": m["seconds"]}


# --- T4 prepare -------------------------------------------------------------------------------------------------------

def test_t4_prepare_refused_with_a_pg_target_variable(env, capsys):
    # D-WK.11: `database_target(url, environ)` refuses a PG* target variable, so the walk is never reached with one
    env.copied()
    env.environ["PGDATABASE"] = "assetops_test"
    assert env.main("prepare") == 2
    assert _refusal(capsys) == "WALK_TARGET_UNCLEAR ENVIRONMENT PGDATABASE"
    assert env.runner.steps() == []


def test_t4_prepare_argv_and_env(env):
    env.environ.update({"ASSETOPS_REAL_OPERATOR_DATA": "on", "ASSETOPS_OPERATIONAL_ENTRY": "on",
                        "ASSETOPS_READING_UPLOAD_GATEWAY": "g", "SECRET": "s"})
    m = env.prepared()
    steps = env.runner.steps()
    s = "Emulated management accounts, October 2026, "
    assert [c[0][1:] for c in steps] == [
        ["-m", "assetops_backend.reconcile_month", "record", "--tenant", "lakeside-power", "--as",
         "joseph@lakeside-power.example", "--period", "2026-10", "--currency", "USD", "--revenue", "9700.00",
         "--fuel-cost", "5100.00", "--source-ref", s + "draft"],
        ["-m", "assetops_backend.reconcile_month", "record", "--tenant", "lakeside-power", "--as",
         "joseph@lakeside-power.example", "--period", "2026-10", "--currency", "USD", "--revenue", "9700.00",
         "--fuel-cost", "5000.00", "--source-ref", s + "final"],
        ["-m", "assetops_backend.build_structure_snapshot", "build", "--tenant", "lakeside-power", "--month",
         "2026-10", "--by", "service:world-build"]]
    for argv, e, cwd in steps:
        assert set(e) == {"PATH", "HOME", "LANG", "PYTHONPATH", "DATABASE_URL", "ASSETOPS_TENANT_SLUG",
                          "ASSETOPS_PSEUDONYM_KEY_DIR", "ASSETOPS_PG_PORT", "ASSETOPS_PG_PASSWORD"}
        assert e["DATABASE_URL"].endswith(f"/{WALK}") and e["ASSETOPS_TENANT_SLUG"] == "lakeside-power"
        assert e["ASSETOPS_PSEUDONYM_KEY_DIR"] == "/x/l1" and cwd == str(WK.REPO)
    assert [r["step"] for r in m["steps"]] == ["prepare.statement:0", "prepare.statement:1",
                                               "prepare.snapshot:lakeside-power:2026-10"]
    assert m["snapshots"] == {"lakeside-power:2026-10": {"as_of": AS_OF, "portfolio_snapshot_id": PORTFOLIO,
                                                         "sites": SITE_IDS, "rules_digest": "r" * 64}}


def test_t4_prepare_refusals(env, capsys):
    assert env.main("prepare") == 2
    assert _refusal(capsys) == f"WALK_UNKNOWN {WALK}"
    env.copied()
    env.git.head_id = "d" * 40
    assert env.main("prepare") == 2
    assert _refusal(capsys).startswith("WALK_COMMIT_MOVED")
    env.git.head_id = COMMIT
    assert env.main("prepare") == 0
    assert env.main("prepare") == 2
    assert _refusal(capsys) == f"WALK_PREPARED {WALK}"


def test_t4_failed_second_step(env, capsys):
    env.copied()
    env.runner.fail_on = "October 2026, final"
    assert env.main("prepare") == 3
    assert _refusal(capsys) == f"STEP_FAILED {WALK} prepare.statement:1 3"
    m = env.manifest()
    assert [r["exit"] for r in m["steps"]] == [0, 3] and m["snapshots"] is None


# --- T5 census judge (W3 and S4) --------------------------------------------------------------------------------------

SNAPS = {"lakeside-power:2026-10": {"sites": SITE_IDS}}


def test_t5_census_judge():
    after = dict(PARENT_CENSUS, commercial_accounts_statement=2, structure_snapshot=8)
    assert WK.census_judge(PARENT_CENSUS, after, 2, SNAPS) == (True, "4 tables")
    ok, detail = WK.census_judge(PARENT_CENSUS, dict(after, site=4), 2, SNAPS)
    assert not ok and detail == "site 3 != 4"
    ok, detail = WK.census_judge(PARENT_CENSUS, dict(after, response_cache=1), 2, SNAPS)
    assert not ok and detail == "response_cache None != 1"
    ok, detail = WK.census_judge(PARENT_CENSUS, dict(after, commercial_accounts_statement=1), 2, SNAPS)
    assert not ok and detail == "commercial_accounts_statement 2 != 1"
    two = {"a:2026-10": {"sites": {"X": "1"}}, "b:2026-10": {"sites": {"Y": "2", "Z": "3"}}}
    assert WK.census_judge(PARENT_CENSUS, dict(after, structure_snapshot=4 + 2 + 3), 2, two)[0]
    assert not WK.census_judge(PARENT_CENSUS, after, 2, two)[0]


def test_t5_w3_fails_on_an_undeclared_row(env, capsys):
    env.prepared()
    capsys.readouterr()
    env.census["site"] += 1
    assert env.main("check") == 4
    lines, _ = _lines(capsys)
    w3 = next(x for x in lines if x["check"] == "W3")
    assert w3 == {"check": "W3", "state": "FAIL", "detail": "site 3 != 4"}


def test_t5_smoke_s4_fails_on_a_row_written_after_the_serve(env, capsys):
    env.served()
    capsys.readouterr()

    def wrote():
        env.census["response_store"] = 1
    env.runner.after_node = wrote
    assert env.main("smoke") == 4
    lines, _ = _lines(capsys)
    assert [x["check"] for x in lines] == ["S1", "S2", "S3", "S4", "ALL"]
    s4 = lines[3]
    assert s4["state"] == "FAIL" and s4["detail"] == "response_store None != 1"
    assert all(x["state"] == "PASS" for x in lines[:3])


# --- T6 check ---------------------------------------------------------------------------------------------------------

def test_t6_check_all_pass(env, capsys, monkeypatch):
    env.prepared()
    capsys.readouterr()
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "other")
    assert env.main("check") == 0
    assert os.environ["ASSETOPS_TENANT_SLUG"] == "other"   # unset only during the read, then restored
    lines, _ = _lines(capsys)
    assert [x["check"] for x in lines] == ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "ALL"]
    assert all(x["state"] == "PASS" for x in lines), lines
    m = env.manifest()
    assert m["check"]["passed"] is True and m["check"]["commit"] == COMMIT and len(m["check"]["lines"]) == 7
    assert ("month", "Lakeside Power", "2026-10", {"KOBO-001": "Kobo Site"}, None) in env.calls
    assert ("resolve_tenant", "lakeside-power") in env.calls
    assert env.disposed.count("deep_dive") == 1 and env.disposed.count("snapshots") == 1
    assert env.urls and all(u.endswith(f"/{WALK}") for u in env.urls)


def test_t6_check_runs_every_check_after_w1_fails(env, capsys):
    env.prepared()
    capsys.readouterr()
    env.l2_refusal = ("WORLD_TEMPLATE_STALE", "code.backend/assetops_backend")
    assert env.main("check") == 4
    lines, _ = _lines(capsys)
    assert [x["check"] for x in lines] == ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "ALL"]
    assert lines[0] == {"check": "W1", "state": "FAIL", "detail": "WORLD_TEMPLATE_STALE code.backend/assetops_backend"}
    assert all(x["state"] == "PASS" for x in lines[1:7]) and lines[7]["state"] == "FAIL"
    assert env.manifest()["check"]["passed"] is False


@pytest.mark.parametrize("plant,check", [
    (lambda e: setattr(e, "check", (False, None)), "W1"),
    (lambda e: setattr(e.git, "head_id", "d" * 40), "W1"),
    (lambda e: setattr(e.runner, "verify_ok", False), "W2"),
    (lambda e: e.payloads["KOBO-001"]["actual"].update(
        {next(iter(e.payloads["KOBO-001"]["actual"])): {"value": "1.23", "missing": None, "missing_leaves": []}}), "W5"),
    (lambda e: e.admin.allowconn.update({L2: True}), "W6"),
    (lambda e: e.admin.dbs.add("assetops_polish_walk1124_test"), "W6"),
    (lambda e: setattr(e, "walk_tenants", [(TID, "lakeside-power"), ("t2", "other")]), "W6"),
])
def test_t6_each_check_can_fail(env, capsys, plant, check):
    env.prepared()
    capsys.readouterr()
    plant(env)
    assert env.main("check") == 4
    lines, _ = _lines(capsys)
    assert [x["check"] for x in lines if x["state"] == "FAIL"] == [check, "ALL"], lines


def test_t6_w7_fails_on_a_failed_or_missing_step(env, capsys):
    m = env.prepared()
    m["steps"] = m["steps"][:2]
    env.write_manifest(m)
    capsys.readouterr()
    assert env.main("check") == 4
    lines, _ = _lines(capsys)
    assert next(x for x in lines if x["check"] == "W7")["detail"] == "snapshots 0 != 1"


def test_t6_check_refused_unprepared(env, capsys):
    env.copied()
    assert env.main("check") == 2
    assert _refusal(capsys) == f"WALK_NOT_PREPARED {WALK}"


# --- T7 the month judge (W4 and S2) -----------------------------------------------------------------------------------

EXPECT = {"tenant": "lakeside-power", "month": "2026-10", "contribution_actual": "1443.00",
          "contribution_target": "2295.00", "reconciled": True}


def test_t7_month_judge():
    assert WK.judge_month(month_ok(), EXPECT, AS_OF) == []
    b = month_ok()
    b["state"] = "REBUILD_NEEDED"
    assert WK.judge_month(b, EXPECT, AS_OF) == ["state REBUILD_NEEDED"]
    b = month_ok()
    b["fresh"]["current"] = False
    assert WK.judge_month(b, EXPECT, AS_OF) == ["fresh.current False"]
    b = month_ok()
    b["fresh"]["untracked_text"] = "x"
    assert WK.judge_month(b, EXPECT, AS_OF) == ["fresh.untracked_text"]
    b = month_ok()
    b["standing"]["reconciled"] = False
    assert WK.judge_month(b, EXPECT, AS_OF) == ["standing.reconciled False"]
    b = month_ok()
    b["tiles"][0]["bar"]["actual"] = "1443.01"
    assert WK.judge_month(b, EXPECT, AS_OF) == ["contribution.actual 1443.01"]
    b = month_ok()
    b["tiles"][0]["bar"]["target"] = "2295"
    assert WK.judge_month(b, EXPECT, AS_OF) == []   # compared as Decimals
    assert WK.judge_month(month_ok(), EXPECT, "2026-11-21T10:00:01+00:00") == ["as_of 2026-11-21T10:00:00Z"]
    b = month_ok()
    b["tiles"] = [{"key": "gap", "bar": None}]
    assert WK.judge_month(b, EXPECT, AS_OF) == ["contribution.bar"]


def test_t7_w4_and_s2_fail_on_rebuild_needed(env, capsys):
    env.prepared()
    capsys.readouterr()
    env.month = {"state": "REBUILD_NEEDED"}
    assert env.main("check") == 4
    lines, _ = _lines(capsys)
    assert next(x for x in lines if x["check"] == "W4") == {"check": "W4", "state": "FAIL",
                                                           "detail": "state REBUILD_NEEDED"}
    env.month = month_ok()
    assert env.main("check") == 0
    assert env.main("serve", "--tree", str(env.tree)) == 0
    capsys.readouterr()
    env.month = dict(month_ok(), fresh={"current": False, "untracked_text": None})
    assert env.main("smoke") == 4
    lines, _ = _lines(capsys)
    assert lines[1] == {"check": "S2", "state": "FAIL", "detail": "fresh.current False"}


# --- T8 serve, its environments and refusals --------------------------------------------------------------------------

def test_t8_serve_envs_and_argv(env, capsys):
    env.environ.update(FORBIDDEN)
    env.environ.pop("PGHOST"), env.environ.pop("PGDATABASE"), env.environ.pop("PGPORT"), env.environ.pop("PGSERVICE")
    env.environ.pop("PGHOSTADDR"), env.environ.pop("PGSERVICEFILE")   # the walk URL refuses these; the env never has them
    env.checked()
    capsys.readouterr()
    assert env.main("serve", "--tree", str(env.tree)) == 0
    api, web = env.procs.spawned
    tree = str(env.tree.resolve())
    assert api["argv"] == [sys.executable, "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", "8991"]
    assert api["cwd"] == f"{tree}/host"
    assert set(api["env"]) == {"PATH", "HOME", "LANG", "PYTHONPATH", "DATABASE_URL", "ASSETOPS_TENANT_SLUG",
                               "ASSETOPS_PG_PORT", "ASSETOPS_PG_PASSWORD", "PYTHONUNBUFFERED"}
    assert api["env"]["PYTHONPATH"] == os.pathsep.join(f"{tree}/{p}" for p in
                                                       ("backend", "contracts", "gateway", "simulator", "host"))
    assert api["env"]["ASSETOPS_TENANT_SLUG"] == "lakeside-power" and api["env"]["DATABASE_URL"].endswith(f"/{WALK}")
    assert web["argv"] == ["npm", "run", "dev", "--", "--port", "5491", "--strictPort", "--host", "127.0.0.1"]
    assert web["cwd"] == f"{tree}/frontend"
    assert web["env"] == {"PATH": "/usr/bin", "HOME": "/home/x", "LANG": "C.UTF-8", "ASSETOPS_API_PORT": "8991"}
    assert api["log"].startswith(f"{tree}/var/polish_walk1123/logs/")
    (line,), _ = _lines(capsys)
    assert line == {"api": "http://127.0.0.1:8991", "web": "http://127.0.0.1:5491", "api_pid": api["pid"],
                    "web_pid": web["pid"]}
    s = env.manifest()["serve"]
    assert set(s) == {"tree", "port", "web_port", "api", "web", "started_at"} and s["api"]["pid"] == api["pid"]


def test_t8_api_env_drops_every_forbidden_name():
    e = WK.api_env(Path("/t"), {"PATH": "/p", "HOME": "/h", **FORBIDDEN}, "lakeside-power", "postgresql://u@h/d")
    assert set(e) == {"PATH", "HOME", "PYTHONPATH", "DATABASE_URL", "ASSETOPS_TENANT_SLUG", "PYTHONUNBUFFERED"}


def test_t8_smoke_node_env_is_exactly_six(env, capsys):
    env.served()
    env.environ.update({"SECRET": "s", "NODE_OPTIONS": "--x", "ASSETOPS_HEAVY_SLOT": "1"})
    capsys.readouterr()
    assert env.main("smoke") == 0
    (bash, benv, _), = [c for c in env.runner.calls if c[0][:1] == ["bash"]]
    assert "/opt/assetecon/tools/pw/env.sh" in bash[2] and set(benv) == {"PATH", "HOME", "LANG"}
    (argv, nenv, _), = [c for c in env.runner.calls if c[0][:1] == ["node"]]
    assert nenv == {"PATH": "/usr/bin", "HOME": "/home/x", "PW": "/pw/pc", "CHROME": "/pw/chrome",
                    "FONTCONFIG_FILE": "/pw/fonts.conf", "LD_LIBRARY_PATH": "/pw/lib"}
    assert argv[:4] == ["node", "tools/walk_world_smoke.cjs", "--base", "http://127.0.0.1:5491"]
    assert len(json.loads(argv[5])) == 10 and argv[7] == "/opt/assetecon/evidence/WK/1123/"
    assert ("walk-smoke", False) in env.required                       # M2: smoke takes a heavy-tool slot


def test_t8_smoke_requires_a_slot_before_chromium(env, capsys):
    """M2: outside a heavy-tool slot, `require` exits 69 and S3 never launches the browser."""
    env.served()

    def require(tool, db=False):
        env.required.append((tool, db))
        raise SystemExit(69)
    env.deps.world.require = require
    capsys.readouterr()
    with pytest.raises(SystemExit) as stop:
        env.main("smoke")
    assert stop.value.code == 69 and env.required[-1] == ("walk-smoke", False)
    assert not [c for c in env.runner.calls if c[0][:1] in (["node"], ["bash"])]


def test_t8_tree_refusal(env, capsys, tmp_path):
    env.checked()
    link = tmp_path / "to-walk"
    link.symlink_to("/opt/assetecon/AssetOpsV1-walk")
    for tree in ("/opt/assetecon/AssetOpsV1-walk", "/opt/assetecon/AssetOpsV1-walk/frontend", str(link)):
        assert env.main("serve", "--tree", tree) == 2
        assert _refusal(capsys).startswith("WALK_TREE_MISMATCH")
    assert env.procs.spawned == [] and not [c for c in env.runner.calls if c[0][:1] == ["git"]]


def test_t8_protected_ports(env, capsys, tmp_path):
    env.checked()
    for flag, port in (("--port", "8990"), ("--web-port", "5490"), ("--port", "5490")):
        assert env.main("serve", "--tree", str(env.tree), flag, port) == 2
        assert _refusal(capsys) == f"WALK_PORT_PROTECTED {port}"
    for key_, port in (("port", 8990), ("web_port", 5490)):
        p = _walkdef(tmp_path, lambda d: d["serve"].update({key_: port}))
        assert env.main("serve", "--tree", str(env.tree), "--walk-definition", str(p)) == 2
        assert _refusal(capsys) == f"WALK_DEFINITION_INVALID $.serve.{key_}"
    assert env.procs.spawned == []


def test_t8_serve_refusals(env, capsys):
    env.prepared()
    assert env.main("serve", "--tree", str(env.tree)) == 2
    assert _refusal(capsys) == f"WALK_NOT_PASSED {WALK}"
    assert env.main("check") == 0
    env.runner.tree_head = "d" * 40
    assert env.main("serve", "--tree", str(env.tree)) == 2
    assert _refusal(capsys).startswith("WALK_TREE_MISMATCH")
    env.runner.tree_head = COMMIT
    env.procs.busy.add(8991)
    assert env.main("serve", "--tree", str(env.tree)) == 2
    assert _refusal(capsys) == "WALK_PORT_BUSY 8991"
    env.procs.busy.clear()
    assert env.main("serve", "--tree", str(env.tree)) == 0
    assert env.main("serve", "--tree", str(env.tree)) == 2
    assert _refusal(capsys) == f"WALK_SERVING {WALK}"
    assert len(env.procs.spawned) == 2


def test_t8_serve_failed_kills_both(env, capsys):
    env.checked()
    env.http_answers["/api/health"] = (0, b"")
    assert env.main("serve", "--tree", str(env.tree)) == 4
    assert _refusal(capsys).startswith("WALK_SERVE_FAILED api ")
    pids = [s["pid"] for s in env.procs.spawned]
    assert sorted(p for p, sig in env.procs.signals if sig == signal.SIGKILL) == sorted(pids)
    assert env.manifest()["serve"] is None


def test_t8_smoke_refused_when_not_serving(env, capsys):
    env.checked()
    assert env.main("smoke") == 2
    assert _refusal(capsys) == f"WALK_NOT_SERVING {WALK}"


# --- T9 stop ----------------------------------------------------------------------------------------------------------

NPM_TITLE = ["npm run dev --port 5491 --strictPort --host 127.0.0.1"]   # npm 11.19.1's retitle, observed (H1)


def test_t9_serve_records_start_time_and_group(env):
    s = env.served()["serve"]
    for w in ("api", "web"):
        rec = s[w]
        t = env.procs.table[rec["pid"]]
        assert rec["start_time"] == t["start"] and rec["pgid"] == rec["pid"] and rec["argv"] == t["cmd"]


def test_t9_stop_signals_matching_pids_and_leaves_reused(env, capsys):
    m = env.served()
    api, web = m["serve"]["api"]["pid"], m["serve"]["web"]["pid"]
    env.procs.set_cmd(web, ["/usr/bin/vim", "notes"])   # same start time, other command: secondary check refuses
    capsys.readouterr()
    assert env.main("stop") == 0
    assert (api, signal.SIGTERM) in env.procs.signals and all(p != web for p, _ in env.procs.signals)
    assert f"WALK_PID_REUSED {web} cmdline" in capsys.readouterr().err
    assert env.manifest()["serve"] is None


def test_t9_stop_kills_after_the_wait(env):
    m = env.served()
    api = m["serve"]["api"]["pid"]
    env.procs.ignore_term.add(api)
    assert env.main("stop") == 0
    assert [s for p, s in env.procs.signals if p == api] == [signal.SIGTERM, signal.SIGKILL]


def test_t9_stop_stops_npm_retitled(env, capsys):
    """H1: npm rewrites its cmdline to one title without the `--`; the web child is still recognised and stopped."""
    m = env.served()
    web = m["serve"]["web"]["pid"]
    env.procs.set_cmd(web, NPM_TITLE)
    capsys.readouterr()
    assert env.main("status") == 0
    (line,), _ = _lines(capsys)
    assert line["alive"] == {"api": True, "web": True}
    assert env.main("stop") == 0
    assert (web, signal.SIGTERM) in env.procs.signals and web not in env.procs.table
    out = capsys.readouterr()
    assert "WALK_PID_REUSED" not in out.err and json.loads(out.out)["reused"] == []


@pytest.mark.parametrize("wrapper", [
    ["bash", "-c", "npm run dev -- --port 5491 --strictPort --host 127.0.0.1"],
    ["sh", "-c", "npm run dev --port 5491 --strictPort --host 127.0.0.1"],
    ["timeout", "60", "npm", "run", "dev", "--", "--port", "5491", "--strictPort", "--host", "127.0.0.1"],
    ["bash -c npm run dev --port 5491 --strictPort --host 127.0.0.1"],
])
def test_t9_stop_refuses_a_wrapper_on_the_same_port(env, capsys, wrapper):
    m = env.served()
    web = m["serve"]["web"]["pid"]
    env.procs.set_cmd(web, wrapper)
    capsys.readouterr()
    assert env.main("stop") == 0
    assert all(p != web for p, _ in env.procs.signals) and web in env.procs.table
    assert f"WALK_PID_REUSED {web} cmdline" in capsys.readouterr().err


def test_t9_stop_refuses_a_reused_pid_with_another_start_time(env, capsys):
    m = env.served()
    web = m["serve"]["web"]["pid"]
    env.procs.table[web]["start"] += 99          # same PID and cmdline, a different process
    env.procs.set_cmd(web, NPM_TITLE)
    capsys.readouterr()
    assert env.main("stop") == 0
    assert all(p != web for p, _ in env.procs.signals) and web in env.procs.table
    assert f"WALK_PID_REUSED {web} start_time" in capsys.readouterr().err


def test_t9_stop_refuses_a_child_not_leading_its_group(env, capsys):
    m = env.served()
    web = m["serve"]["web"]["pid"]
    env.procs.table[web]["pgrp"] = 77            # M1: the matching PID sits in someone else's group
    capsys.readouterr()
    assert env.main("stop") == 0
    assert all(p not in (web, 77) for p, _ in env.procs.signals) and web in env.procs.table
    assert f"WALK_PID_REUSED {web} not_leader" in capsys.readouterr().err


def test_t9_stop_refuses_a_group_other_than_the_recorded_one(env, capsys):
    m = env.served()
    web = m["serve"]["web"]["pid"]
    m["serve"]["web"]["pgid"] = web + 1
    env.write_manifest(m)
    capsys.readouterr()
    assert env.main("stop") == 0
    assert all(p not in (web, web + 1) for p, _ in env.procs.signals)
    assert f"WALK_PID_REUSED {web} pgid" in capsys.readouterr().err


def test_t9_stop_refuses_an_unrecorded_child(env, capsys):
    m = env.served()
    api = m["serve"]["api"]["pid"]
    del m["serve"]["api"]["start_time"]
    env.write_manifest(m)
    capsys.readouterr()
    assert env.main("stop") == 0
    assert all(p != api for p, _ in env.procs.signals)
    assert f"WALK_PID_REUSED {api} unrecorded" in capsys.readouterr().err


def test_t9_stop_group_survives_its_leader(env, capsys):
    """L4: npm died, Vite lives on in the recorded group: the group is stopped after the members' start-time check."""
    m = env.served()
    rec = m["serve"]["web"]
    web = rec["pid"]
    env.procs.table[9001] = {"cmd": ["node", "vite"], "start": rec["start_time"] + 1, "pgrp": web, "sid": web}
    del env.procs.table[web]
    capsys.readouterr()
    assert env.main("status") == 0
    (line,), _ = _lines(capsys)
    assert line["alive"]["web"] is True
    assert env.main("stop") == 0
    assert (web, signal.SIGTERM) in env.procs.signals and 9001 not in env.procs.table
    assert "WALK_PID_REUSED" not in capsys.readouterr().err


def test_t9_stop_refuses_a_group_member_older_than_the_leader(env, capsys):
    m = env.served()
    rec = m["serve"]["web"]
    web = rec["pid"]
    env.procs.table[9001] = {"cmd": ["sh"], "start": rec["start_time"] - 1, "pgrp": web, "sid": web}
    del env.procs.table[web]
    capsys.readouterr()
    assert env.main("stop") == 0
    assert all(p != web for p, _ in env.procs.signals) and 9001 in env.procs.table
    assert f"WALK_PID_REUSED {web} group_unverified" in capsys.readouterr().err


def test_t9_stop_with_both_gone_signals_nothing(env, capsys):
    m = env.served()
    for w in ("api", "web"):
        del env.procs.table[m["serve"][w]["pid"]]
    capsys.readouterr()
    assert env.main("stop") == 0
    assert env.procs.signals == [] and "WALK_PID_REUSED" not in capsys.readouterr().err


def test_t9_parse_stat_reads_field_22_past_a_comm_with_spaces():
    raw = b"123 (a) b (c)) S 1 123 123 0 -1 0 0 0 0 0 0 0 0 0 20 0 1 0 987654 0 0\n"
    assert WK.parse_stat(raw) == {"pgrp": 123, "session": 123, "start_time": 987654}
    assert WK.parse_stat(None) is None and WK.parse_stat(b"1 (x) S") is None


def test_t9_cmdline_matches():
    argv = ["npm", "run", "dev", "--", "--port", "5491", "--strictPort", "--host", "127.0.0.1"]
    assert WK.cmdline_matches(argv, argv)
    assert WK.cmdline_matches(NPM_TITLE, argv)
    assert WK.cmdline_matches(["npm run dev -- --port 5491 --strictPort --host 127.0.0.1"], argv)
    assert WK.cmdline_matches(["node", "/usr/lib/node_modules/npm/bin/npm-cli.js", *argv[1:]], argv)
    assert WK.cmdline_matches(["node", "/usr/bin/npm", *argv[1:]], argv)
    assert not WK.cmdline_matches(["npm run dev --port 5492 --strictPort --host 127.0.0.1"], argv)
    assert not WK.cmdline_matches(["npm run dev --port 54911 --strictPort --host 127.0.0.1"], argv)
    assert not WK.cmdline_matches(["node", "/usr/bin/npm", "run", "dev", "--", "--port", "5492", "--strictPort",
                                   "--host", "127.0.0.1"], argv)
    assert not WK.cmdline_matches(["vim", *argv[1:]], argv)
    assert not WK.cmdline_matches(["timeout", "60", *argv], argv)
    assert not WK.cmdline_matches(["bash", "-c", " ".join(argv)], argv)
    assert not WK.cmdline_matches(None, argv)
    api = ["/v/bin/python", "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", "8991"]
    assert WK.cmdline_matches(api, api)
    assert not WK.cmdline_matches(["timeout", "60", *api], api)
    assert not WK.cmdline_matches(["bash", "-c", "cd x && " + " ".join(api)], api)
    assert not WK.cmdline_matches(["/v/bin/python -m uvicorn lab_app:app --host 127.0.0.1 --port 8991"], [
        "npm", "run", "dev", "--", "--port", "8991"])


# --- L1, L2, L3 ---------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("flags, detail", [
    (("--port", "80"), "80"),
    (("--web-port", "70000"), "70000"),
    (("--port", "0"), "0"),
    (("--port", "5491"), "5491 = 5491"),
    (("--web-port", "8991"), "8991 = 8991"),
])
def test_l1_port_overrides_in_range_and_different(env, capsys, flags, detail):
    env.checked()
    capsys.readouterr()
    assert env.main("serve", "--tree", str(env.tree), *flags) == 2
    assert _refusal(capsys) == f"WALK_PORT_INVALID {detail}"
    assert env.procs.spawned == []


@pytest.mark.parametrize("make", ["symlink", "group_writable", "world_writable", "file"])
def test_l2_walks_folder_must_be_private(env, capsys, tmp_path, make):
    d = env.state / "walks"
    if make == "symlink":
        real = tmp_path / "elsewhere"
        os.mkdir(real, 0o700)
        d.symlink_to(real)
    elif make == "file":
        d.write_text("")
    else:
        os.mkdir(d, 0o700)
        os.chmod(d, 0o770 if make == "group_writable" else 0o707)
    assert env.main("copy") == 2
    assert _refusal(capsys) == f"WORLD_STATE_INVALID {d}"


def test_l2_walks_folder_of_another_user(env, capsys, monkeypatch):
    d = env.state / "walks"
    os.mkdir(d, 0o700)
    real = os.lstat

    def lstat(path, *a, **k):
        st = real(path, *a, **k)
        if Path(path) == d:
            return os.stat_result((st.st_mode, st.st_ino, st.st_dev, st.st_nlink, st.st_uid + 1, *tuple(st)[5:10]))
        return st
    monkeypatch.setattr(WK.os, "lstat", lstat)
    assert env.main("copy") == 2
    assert _refusal(capsys) == f"WORLD_STATE_INVALID {env.state / 'walks'}"


def test_l3_second_spawn_fails_stops_the_first(env, capsys):
    env.checked()
    env.procs.spawn_error = "npm"
    capsys.readouterr()
    assert env.main("serve", "--tree", str(env.tree)) == 4
    assert _refusal(capsys) == "WALK_SERVE_FAILED web spawn FileNotFoundError"
    (api,) = env.procs.spawned
    assert env.procs.signals == [(api["pid"], signal.SIGKILL)] and api["pid"] not in env.procs.table
    assert env.manifest()["serve"] is None


def test_l3_second_spawn_fails_first_unverified_is_reported(env, capsys):
    env.checked()
    env.procs.spawn_error = "npm"
    real_popen = env.procs.popen

    def popen(argv, **kw):
        child = real_popen(argv, **kw)
        env.procs.table[child.pid]["pgrp"] = 77      # the API child does not lead its group: no signal
        return child
    env.procs.popen = popen
    capsys.readouterr()
    assert env.main("serve", "--tree", str(env.tree)) == 4
    err = capsys.readouterr().err
    (api,) = env.procs.spawned
    assert f"WALK_PID_REUSED {api['pid']} not_leader" in err and "WALK_SERVE_FAILED web spawn" in err
    assert env.procs.signals == []


# --- T10 drop ---------------------------------------------------------------------------------------------------------

def test_t10_drop(env, capsys):
    env.served()
    assert env.main("drop") == 2
    assert _refusal(capsys) == f"WALK_SERVING {WALK}"
    assert env.main("stop") == 0
    env.admin.sessions[WALK] = 1
    assert env.main("drop") == 2
    assert _refusal(capsys) == f"WALK_DATABASE_IN_USE {WALK}"
    env.admin.sessions[WALK] = 0
    before = len(env.admin.log)
    other = env.state / "manifests" / f"{L2}.json"
    other.write_text("{}")
    assert env.main("drop") == 0
    assert env.admin.ddl()[-1] == f'DROP DATABASE "{WALK}"'
    assert all("FORCE" not in s for s in env.admin.ddl())
    assert not any(L2 in s or L2 in json.dumps(p) for _, s, p in env.admin.log[before:])
    assert env.manifest() is None and other.is_file() and WALK not in env.admin.dbs and L2 in env.admin.dbs
    assert env.main("drop") == 2
    assert _refusal(capsys) == f"WALK_UNKNOWN {WALK}"


# --- T11 smoke pages --------------------------------------------------------------------------------------------------

def test_t11_smoke_pages():
    d = world.read_definition(DEFINITION)
    pages = WK.smoke_pages(WK.read_walk_definition(WALK_DEFINITION, d), d)
    assert pages == ["/portfolio", "/portfolio/month?month=2026-10", "/sites", "/sites/KISIWA-001", "/sites/KOBO-001",
                     "/sites/MTO-001", "/findings", "/actions", "/evidence", "/financials"]


def test_t11_smoke_script_help():
    done = subprocess.run(["node", str(ROOT / "tools/walk_world_smoke.cjs"), "--help"], capture_output=True, text=True,
                          timeout=30, env={"PATH": os.environ.get("PATH", "")})
    assert done.returncode == 0 and "usage:" in done.stdout


# --- T12 static -------------------------------------------------------------------------------------------------------

def _tree():
    return ast.parse(SOURCE.read_text())


def _enclosing(tree):
    """Each node with the name of its top-level definition (function, class, or assigned name)."""
    out = []
    for top in tree.body:
        if isinstance(top, (ast.FunctionDef, ast.ClassDef)):
            owner = top.name
        elif isinstance(top, ast.Assign) and isinstance(top.targets[0], ast.Name):
            owner = top.targets[0].id
        else:
            owner = None
        for node in ast.walk(top):
            out.append((owner, node))
    return out


def test_t12_protected_literals_only_in_their_constants():
    nodes = _enclosing(_tree())
    for value, home in (("assetops_polish_walk1113_test", "PROTECTED_DATABASES"), (8990, "PROTECTED_PORTS"),
                        (5490, "PROTECTED_PORTS"), ("/opt/assetecon/AssetOpsV1-walk", "refuse_walk_tree")):
        owners = {o for o, n in nodes if isinstance(n, ast.Constant) and n.value == value}
        assert owners == {home}, (value, owners)
    text = SOURCE.read_text()
    assert "/opt/assetecon/keys" not in text
    assert text.count("1113") == 1 and text.count("8990") == 1 and text.count("5490") == 1


def test_t12_no_world_write_or_name_check_on_the_walk():
    forbidden = {"create", "drop_db", "freeze", "census", "exists", "check_name"}
    nodes = _enclosing(_tree())
    calls = []
    for owner, n in nodes:
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                base = f.value
                is_world = (isinstance(base, ast.Name) and base.id in ("world", "W")) or (
                    isinstance(base, ast.Attribute) and base.attr == "world")
                if f.attr == "check_name" or (is_world and f.attr in forbidden):
                    calls.append((owner, f.attr))
                if f.attr == "rung_url":
                    calls.append((owner, "rung_url"))
            elif isinstance(f, ast.Name) and f.id in ("check_name", "rung_url"):
                calls.append((owner, f.id))
    assert calls == [("walk_url", "rung_url")], calls
    text = SOURCE.read_text()
    assert "World.census" not in text and "World.exists" not in text and "check_name" not in text
