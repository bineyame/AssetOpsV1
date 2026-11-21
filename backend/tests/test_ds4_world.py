"""DS4 (spec `specs/DS4-template-ladder/spec.md` §5): `tools/world.py` with fakes; no database."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import world  # noqa: E402

DEFINITION = ROOT / "backend/conversions/world-layer4-v1.json"
DERIVED = ROOT / "Docs/demo-sprint/product-direction-layer4/derived-values.json"
MANIFEST = ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
MARKER = "KEY-MARKER-7f3a"
TID = "11111111-2222-4333-8444-555555555555"
PORTFOLIO = "00000000-0000-4000-8000-000000000000"
SITE_IDS = {"KISIWA-001": "00000000-0000-4000-8000-000000000001", "KOBO-001": "00000000-0000-4000-8000-000000000002",
            "MTO-001": "00000000-0000-4000-8000-000000000003"}


# --- fakes -----------------------------------------------------------------------------------------------------------

class FakeAdmin:
    def __init__(self, log: list) -> None:
        self.log, self.dbs, self.sessions, self.frozen = log, set(), {}, set()

    def __call__(self, sql, params=None):
        n = (params or {}).get("n")
        self.log.append(("admin", sql if n is None else f"{sql} [{n}]"))
        if sql.startswith("SELECT 1 FROM pg_database"):
            return [(1,)] if n in self.dbs else []
        if sql.startswith("SELECT count(*) FROM pg_stat_activity"):
            return [(self.sessions.get(n, 0),)]
        if sql.startswith("SELECT pg_database_size"):
            return [(4096,)]
        if sql.startswith("SELECT datname FROM pg_database"):
            return [(d,) for d in sorted(self.dbs)]
        m = re.match(r'CREATE DATABASE "([^"]+)"', sql)
        if m:
            self.dbs.add(m.group(1))
            return []
        m = re.match(r'DROP DATABASE "([^"]+)"', sql)
        if m:
            self.dbs.discard(m.group(1))
            return []
        m = re.match(r'ALTER DATABASE "([^"]+)" WITH ALLOW_CONNECTIONS false', sql)
        if m:
            self.frozen.add(m.group(1))
            return []
        raise AssertionError(sql)


class FakeGit:
    def __init__(self) -> None:
        self.ids: dict = {}
        self.dirty_lines: list = []
        self.calls: list = []

    def tree(self, path):
        return self.ids.get(path, "id-" + hashlib.sha1(path.encode()).hexdigest()[:10])

    def dirty(self, paths):
        self.calls.append(list(paths))
        return list(self.dirty_lines)

    def head(self):
        return "c" * 40


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
    def __init__(self, log: list) -> None:
        self.log, self.envs, self.fail_on, self.timeout_on = log, [], None, None
        self.harness_exit, self.verify_exit, self.harness_hook = 0, 0, None

    def __call__(self, argv, cwd, env, timeout):
        args = list(argv[1:])
        self.envs.append((args, dict(env)))
        if str(argv[0]).endswith("pwsh"):
            self.log.append(("step", "harness"))
            if self.harness_hook:
                self.harness_hook(env)
            return subprocess.CompletedProcess(argv, self.harness_exit, "1 passed\n", "")
        label = self._label(args)
        self.log.append(("step", label))
        if self.timeout_on and self.timeout_on in label:
            raise subprocess.TimeoutExpired(argv, timeout)
        if self.fail_on and self.fail_on in label:
            return subprocess.CompletedProcess(argv, 3, "", "boom")
        out = ""
        if "exports" in args:
            o = Path(args[args.index("--out") + 1])
            o.mkdir(parents=True)
            (o / "lakeside-power.billing.csv").write_text("a,b\n1,2\n")
            (o / "unwritten.json").write_text("[]")
        elif "digest" in args:
            out = "d" * 64
        elif "apply" in args:
            kd = Path(args[args.index("--key-dir") + 1])
            (kd / f"{TID}.key").write_text(MARKER)
            out = json.dumps({"key": "create"})
        elif "assetops_backend.load_world_inputs" in args:
            out = json.dumps({"tenant": "lakeside-power", "commercial_exit": 0, "batches": 0})
        elif "assetops_backend.build_structure_snapshot" in args and "build" in args:
            out = json.dumps({"portfolio_snapshot_id": PORTFOLIO, "sites": SITE_IDS})
        elif "assetops_backend.build_structure_snapshot" in args and "verify" in args:
            if self.timeout_on == "verify":
                raise subprocess.TimeoutExpired(argv, timeout)
            out = json.dumps({"matches": self.verify_exit == 0, "differences": [] if self.verify_exit == 0 else ["x"]})
            return subprocess.CompletedProcess(argv, self.verify_exit, out + "\n", "")
        elif "erase" in args:
            kd = Path(args[args.index("--dir") + 1])
            (kd / f"{TID}.key").unlink(missing_ok=True)
            (kd / f"{TID}.erased").write_text("tomb")
            out = "Erased."
        return subprocess.CompletedProcess(argv, 0, out + "\n", "")

    @staticmethod
    def _label(args):
        if args[:1] == ["tools/world_history.py"]:
            return "exports"
        if args[:2] == ["-m", "alembic"]:
            return "migrate"
        mod = args[1].rsplit(".", 1)[-1]
        return f"{mod}.{args[2]}"


def fake_query(log):
    def q(url, sqls):
        out = []
        for s in sqls:
            if s == world.CENSUS_TABLES:
                log.append(("query", "census"))
                out.append([("site",), ("tenant",)])
            elif s == world.TENANTS:
                out.append([(TID, "lakeside-power")])
            else:
                out.append([(3 if '"site"' in s else 1,)])
        return out
    return q


class Env:
    def __init__(self, tmp_path: Path) -> None:
        self.log: list = []
        self.admin = FakeAdmin(self.log)
        self.git = FakeGit()
        self.runner = FakeRunner(self.log)
        self.required: list = []
        self.state = tmp_path / "state"
        os.mkdir(self.state, 0o700)
        self.keys = tmp_path / "keys"
        os.mkdir(self.keys, 0o700)
        self.environ = {"PATH": "/usr/bin", "HOME": "/home/x", "PGDATABASE": "assetops_test", "PGHOST": "elsewhere",
                        "ASSETOPS_REAL_OPERATOR_DATA": "on", "ASSETOPS_PG_PORT": "55432"}
        self.deps = world.Deps(admin=self.admin, query=fake_query(self.log), runner=self.runner, git=self.git,
                               clock=FakeClock(), require=lambda tool, db=False: self.required.append((tool, db)),
                               environ=self.environ, which=lambda name, path=None: "/opt/pw/bin/pwsh",
                               snapshots=self.snapshot_service)
        self.payloads = {code: hand_payload(code) for code in SITE_IDS}
        self.snapshot_error = None
        self.rows_for = None   # a hook that changes which Site ids the store returns
        self.disposed = 0

    def snapshot_service(self, url):
        from types import SimpleNamespace

        from assetops_backend.structure_snapshot import codec

        env = self

        def get(tenant_id, ids):
            if env.snapshot_error:
                raise env.snapshot_error
            assert str(tenant_id) == TID
            codes = {v: k for k, v in SITE_IDS.items()}
            rows = []
            for i in (env.rows_for(list(ids)) if env.rows_for else ids):
                text = json.dumps(env.payloads[codes[str(i)]])
                rows.append(SimpleNamespace(payload=text, payload_sha256=codec.digest(text)))
            return tuple(rows)

        def dispose():
            env.disposed += 1

        return SimpleNamespace(store=SimpleNamespace(get=get), dispose=dispose)

    def main(self, *argv, capsys=None, prefix="assetops_ds4tfake"):
        common = ["--state", str(self.state), "--prefix", prefix]
        args = [argv[0], *common, *argv[1:]]
        code = world.main(args, deps=self.deps)
        return code

    def build(self):
        return self.main("build", "--key-root", str(self.keys))

    def manifests(self):
        return {p.stem: json.loads(p.read_text()) for p in (self.state / "manifests").glob("*.json")}


def hand_payload(code, over=None):
    """A Site payload that meets the contract exactly, from `derived-values.json` read with `json`."""
    derived = json.loads(DERIVED.read_text())
    name = {"KISIWA-001": "Kisiwa", "KOBO-001": "Kobo", "MTO-001": "Mto"}[code]
    exp = derived["sites"][f"lakeside-power/{name}"]
    sides = {}
    for side in ("actual", "plan"):
        out = {}
        for f, x in exp[side]["nodes"].items():
            if world.site_class(code, side, f) == "E":
                out[f] = {"value": str(x), "missing": None, "missing_leaves": []}
            else:
                out[f] = {"value": None, "missing": {"record_kind": "REC"}, "missing_leaves": []}
        sides[side] = out
    return {"site_code": code, "actual": sides["actual"], "targets": {"values": sides["plan"]}}


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


def _lines(capsys):
    out = capsys.readouterr()
    return [json.loads(x) for x in out.out.splitlines() if x.strip()], out.err


# --- T1 definition -----------------------------------------------------------------------------------------------------

def _definition(tmp_path, mutate):
    d = json.loads(DEFINITION.read_text())
    mutate(d)
    p = tmp_path / "def.json"
    p.write_text(json.dumps(d))
    return p


@pytest.mark.parametrize("mutate, where", [
    (lambda d: d.update(extra=1), "$"),
    (lambda d: d["tenants"][0].update(slug="Lakeside-power"), "$.tenants[0].slug"),
    (lambda d: d["tenants"][0].update(onboarding="backend/tests/fixtures/on1/missing.json"), "$.tenants[0].onboarding"),
    (lambda d: d.update(months=["2026-10", "2026-09"]), "$.months"),
    (lambda d: d.update(built_by="system"), "$.built_by"),
    (lambda d: d["tenants"][0].update(accept_as=d["tenants"][0]["submit_as"]), "$.tenants[0].accept_as"),
    (lambda d: d["telemetry"].update(source="simulator"), "$.telemetry.source"),
])
def test_t1_definition_breaches_are_refused(tmp_path, mutate, where):
    assert world.read_definition(DEFINITION).world == "layer4"
    with pytest.raises(world.Refused) as r:
        world.read_definition(_definition(tmp_path, mutate))
    assert (r.value.code, r.value.detail) == ("WORLD_DEFINITION_INVALID", where)


def test_t1b_definition_matches_the_manifest_and_derived_values():
    d = json.loads(DEFINITION.read_text())
    m = yaml.safe_load(MANIFEST.read_text())
    dv = json.loads(DERIVED.read_text())
    assert sorted([t["slug"] for t in d["tenants"]] + [n["tenant"] for n in d["not_built"]]) == \
        sorted(t["tenant"] for t in m["tenants"])
    for t in d["tenants"]:
        (mt,) = [x for x in m["tenants"] if x["tenant"] == t["slug"]]
        assert t["sites"] == {s["code"]: s["site"] for s in mt["sites"]}
        for name in t["sites"].values():
            assert f"{t['slug']}/{name}" in dv["sites"]


# --- T2 keys -----------------------------------------------------------------------------------------------------------

def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    for p in [world.MIGRATIONS + "/v.py", *[c if c.endswith(".py") else c + "/x.py" for c in world.CODE_PATHS]]:
        (root / p).parent.mkdir(parents=True, exist_ok=True)
        (root / p).write_text("stub\n")
    _git(root, "init", "-q")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "s")
    return root


def _keys(git, definition=b"def", files=None, onboarding=None):
    k0 = world.key(world.parts_l0(git))
    dig = world.inputs_digest(files or {"t/commercial/a.csv": "aa"}, onboarding or {"t": "oo"})
    k1 = world.key(world.parts_l1(git, k0, definition, dig))
    return k0, k1, world.key(world.parts_l2(k1))


def _commit(root, path, text="changed\n"):
    (root / path).write_text(text)
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "c")


def test_t2_keys_change_with_exactly_their_parts(repo, monkeypatch):
    git = world.Git(repo)
    base = _keys(git)
    assert _keys(git) == base
    _commit(repo, world.MIGRATIONS + "/v.py")
    k = _keys(git)
    assert all(a != b for a, b in zip(base, k))
    base = k
    for variant in (dict(definition=b"def2"), dict(files={"t/commercial/a.csv": "ab"}), dict(onboarding={"t": "op"})):
        k = _keys(git, **variant)
        assert k[0] == base[0] and k[1] != base[1] and k[2] != base[2]
    for c in world.CODE_PATHS:
        _commit(repo, c if c.endswith(".py") else c + "/x.py", f"changed {c}\n")
        k = _keys(git)
        assert k[0] == base[0] and k[1] != base[1] and k[2] != base[2], c
        base = k
    monkeypatch.setattr(world, "L2_STEPS", world.L2_STEPS + (("x", "y", "z"),))
    k = _keys(git)
    assert k[:2] == base[:2] and k[2] != base[2]
    parts = {"rung": "L0", "migrations": "abc"}
    assert world.key(parts) == hashlib.sha256(b'{"migrations":"abc","rung":"L0"}').hexdigest()


def test_t2_stale_part_names_the_first_difference():
    def chain(**over):
        p0 = {"rung": "L0", "migrations": over.get("migrations", "m")}
        p1 = {"rung": "L1", "l0": "k0", "definition": over.get("definition", "d"), "inputs": over.get("inputs", "i"),
              "code": {c: over.get(c, "t") for c in world.CODE_PATHS}}
        p2 = {"rung": "L2", "l1": "k1", "steps": over.get("steps", "s")}
        return [p0, p1, p2]
    assert world.stale_part(chain(), chain()) is None
    assert world.stale_part(chain(), chain(migrations="x", steps="y")) == "migrations"
    assert world.stale_part(chain(), chain(inputs="x", steps="y")) == "inputs"
    assert world.stale_part(chain(), chain(**{"tools/world.py": "x"})) == "code.tools/world.py"
    assert world.stale_part(chain(), chain(steps="y")) == "steps"


# --- T3 clean tree -------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("line, path", [("?? backend/assetops_backend/new.py", "backend/assetops_backend/new.py"),
                                        (" M backend/conversions/world-layer4-v1.json", "backend/conversions/world-layer4-v1.json")])
def test_t3_dirty_tree_refuses_before_any_statement(env, capsys, line, path):
    env.git.dirty_lines = [line]
    assert env.build() == 2
    assert capsys.readouterr().err.strip() == f"WORLD_TREE_DIRTY {path}"
    assert env.log == []
    covered = env.git.calls[0]
    for p in [*world.CODE_PATHS, world.MIGRATIONS, "backend/conversions/world-layer4-v1.json", *world.CHECK_CODE,
              "backend/tests/fixtures/on1/lakeside-power.onboarding.json",
              "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml",
              "Docs/demo-sprint/product-direction-layer4/derived-values.json"]:
        assert p in covered


def test_t3_real_git_reports_an_untracked_file(repo):
    (repo / "backend/assetops_backend/new.py").write_text("x")
    assert world.Git(repo).dirty(["backend/assetops_backend"]) == ["?? backend/assetops_backend/new.py"]


# --- T4 names ----------------------------------------------------------------------------------------------------------

def test_t4_names_have_their_form_and_pass_permitted_database():
    from assetops_backend.evidence.bulk_load import permitted_database
    env = {"ASSETOPS_PG_PORT": "55432"}
    prefix = "assetops_" + "a" * 24
    names = [world.name_for(prefix, r, "0123456789ab") for r in ("L0", "L1", "L2")]
    names.append(world.name_for(prefix, "CLONE", "a" * 20))
    for n in names:
        assert re.fullmatch(rf"{prefix}_audit_(l0|l1|l2)_[0-9a-f]{{12}}|{prefix}_audit_c_[a-z0-9]{{1,20}}", n)
        assert world.check_name(n, env) == n and len(n.encode()) <= 63
    for which in ("c5", "b5"):
        base = world.harness_base_name(which)
        assert re.fullmatch(rf"assetops_w{which}_pt[0-9a-f]{{8}}_base_test", base)
        longest = base[: -len("_test")] + "_pt" + "f" * 10 + "_tpl_test"
        assert len(longest.encode()) <= 63
        assert permitted_database(world.rung_url(longest, env), env)
        assert world.check_name(base, env) == base


@pytest.mark.parametrize("prefix", ["assetops_walk1", "assetops_opx", "Assetops_x", "assetops_" + "a" * 25])
def test_t4_bad_prefix_is_refused_before_any_statement(env, capsys, prefix):
    assert env.main("build", "--key-root", str(env.keys), prefix=prefix) == 2
    assert capsys.readouterr().err.startswith("WORLD_NAME_NOT_PERMITTED")
    assert env.log == []


@pytest.mark.parametrize("label, code", [("walk1", "WORLD_NAME_NOT_PERMITTED"), ("observe", "WORLD_NAME_NOT_PERMITTED"),
                                         ("reserve", "WORLD_NAME_NOT_PERMITTED"), ("Bad", "WORLD_LABEL_INVALID"),
                                         ("a" * 21, "WORLD_LABEL_INVALID")])
def test_t4_bad_label_is_refused_before_any_statement(env, capsys, label, code):
    assert env.main("clone", "--label", label) == 2
    assert capsys.readouterr().err.startswith(code)
    assert env.log == []


@pytest.mark.parametrize("name", ["assetops_test", "assetops_polish_walk1113_test", "assetops_ds4tfake_audit_l0_0123456789ab"])
def test_t4_drop_of_unknown_names(env, capsys, name):
    assert env.main("drop", "--database", name) == 2
    assert capsys.readouterr().err.startswith(f"WORLD_UNKNOWN_DATABASE {name}")
    assert [x for x in env.log if x[0] == "admin" and not x[1].startswith("SELECT")] == []


# --- T5 build ----------------------------------------------------------------------------------------------------------

EXPECTED_BUILD = [
    "CREATE DATABASE {L0}", "step migrate", "census", "ALTER {L0}",
    "step exports",  # (inputs are exported before the L1 key; listed where they run)
    "CREATE DATABASE {L1} TEMPLATE {L0}", "step onboard_operator.digest", "step onboard_operator.check",
    "step onboard_operator.apply", "step load_world_inputs.--world", "census", "ALTER {L1}",
    "CREATE DATABASE {L2} TEMPLATE {L1}", "step build_structure_snapshot.build", "step observe_structure.run", "census",
    "ALTER {L2}",
]


def _shape(log, names):
    inv = {v: k for k, v in names.items()}
    out = []
    for kind, what in log:
        if kind == "step":
            out.append(f"step {what}")
        elif kind == "query":
            out.append("census")
        elif what.startswith("CREATE"):
            m = re.match(r'CREATE DATABASE "([^"]+)"(?: TEMPLATE "([^"]+)" STRATEGY FILE_COPY)?$', what)
            out.append("CREATE DATABASE {%s}" % inv[m.group(1)] + (" TEMPLATE {%s}" % inv[m.group(2)] if m.group(2) else ""))
        elif what.startswith("ALTER"):
            out.append("ALTER {%s}" % inv[re.search(r'"([^"]+)"', what).group(1)])
        elif what.startswith("DROP"):
            out.append("DROP {%s}" % inv[re.search(r'"([^"]+)"', what).group(1)])
    return out


def test_t5_cold_build_then_reuse(env, capsys):
    assert env.build() == 0
    lines, err = _lines(capsys)
    names = {x["rung"]: x["database"] for x in lines}
    assert [x["rung"] for x in lines] == ["L0", "L1", "L2"] and not any(x["reused"] for x in lines)
    shape = _shape(env.log, names)
    # exports run before the L0 rung is reused or built; move it for the literal comparison
    assert shape.pop(0) == "step exports"
    expected = [e for e in EXPECTED_BUILD if e != "step exports"]
    assert shape == expected
    assert not any("FORCE" in w for _, w in env.log)
    ms = env.manifests()
    assert set(ms) == set(names.values())
    l1, l2 = ms[names["L1"]], ms[names["L2"]]
    for m in ms.values():
        for f in ("format", "database", "rung", "key", "parts", "parent", "commit", "built_at", "world", "telemetry",
                  "steps", "census", "size_bytes"):
            assert f in m
        assert m["telemetry"] == {"source": "none", "reason": "DS2_NOT_BUILT"}
    assert l1["tenants"] == {"lakeside-power": TID} and l1["key_dir"] == str(env.keys / names["L1"])
    assert l2["snapshots"] == {"lakeside-power:2026-10": {"portfolio_snapshot_id": PORTFOLIO, "sites": SITE_IDS}}
    assert l2["check"] is None and l1["parent"] == names["L0"] and l2["parent"] == names["L1"]
    assert l1["census"] == {"site": 3, "tenant": 1}
    # freeze before the manifest: every frozen database has its manifest, and the order in the log is ALTER then nothing
    assert env.admin.frozen == set(names.values())
    # §3.5 environment, exactly
    kd = str(env.keys / names["L1"])
    for args, e in env.runner.envs:
        assert "PGDATABASE" not in e and "PGHOST" not in e and "ASSETOPS_REAL_OPERATOR_DATA" not in e
        allowed = {"PATH", "HOME", "LANG", "PYTHONPATH", "DATABASE_URL", "ASSETOPS_TENANT_SLUG",
                   "ASSETOPS_PSEUDONYM_KEY_DIR", "ASSETOPS_PG_PORT", "ASSETOPS_PG_PASSWORD"}
        assert set(e) <= allowed
        if "onboard_operator" in " ".join(args) and "digest" not in args or "build_structure_snapshot" in " ".join(args):
            assert e["ASSETOPS_PSEUDONYM_KEY_DIR"] == kd and e["ASSETOPS_TENANT_SLUG"] == "lakeside-power"
    # no key file name or content anywhere
    text = json.dumps(lines) + err + "".join(p.read_text() for p in (env.state / "manifests").glob("*.json"))
    assert MARKER not in text and ".key" not in text
    assert (env.state / "manifests").stat().st_mode & 0o777 == 0o700
    assert (env.state / "inputs").stat().st_mode & 0o777 == 0o700
    assert list((env.state / "tmp").iterdir()) == []
    # second build: nothing runs, three reused
    env.log.clear()
    assert env.build() == 0
    lines, _ = _lines(capsys)
    assert [x["reused"] for x in lines] == [True, True, True]
    assert [w for k, w in env.log if k == "step"] == ["exports"]
    assert not [w for k, w in env.log if k == "admin" and not w.startswith("SELECT")]


def test_t5_partial_is_dropped_and_rebuilt(env, capsys):
    assert env.build() == 0
    names = {x["rung"]: x["database"] for x in _lines(capsys)[0]}
    (env.state / "manifests" / f"{names['L1']}.json").unlink()
    (env.state / "manifests" / f"{names['L2']}.json").unlink()
    env.admin.dbs.discard(names["L2"])
    env.log.clear()
    assert env.build() == 0
    shape = _shape(env.log, names)
    assert "DROP {L1}" in shape and shape.index("DROP {L1}") < shape.index("CREATE DATABASE {L1} TEMPLATE {L0}")
    assert names["L1"] + "" in env.manifests()


def test_t5_failed_step_writes_no_manifest(env, capsys):
    env.runner.fail_on = "observe_structure"
    assert env.build() == 3
    out, err = _lines(capsys)
    assert err.startswith("STEP_FAILED ") and "L2.observe:lakeside-power:2026-10 3" in err
    assert [m["rung"] for m in env.manifests().values()].count("L2") == 0
    assert sorted(m["rung"] for m in env.manifests().values()) == ["L0", "L1"]


def test_t5_timeout_is_exit_5_without_manifest(env, capsys):
    env.runner.timeout_on = "onboard_operator.apply"
    assert env.build() == 5
    assert capsys.readouterr().err.startswith("WORLD_CAP_EXCEEDED L1.onboard_apply")
    assert sorted(m["rung"] for m in env.manifests().values()) == ["L0"]


def test_t5_state_directory_rules(env, tmp_path, capsys):
    bad = tmp_path / "open"
    os.mkdir(bad, 0o755)
    os.chmod(bad, 0o755)
    for state in (tmp_path / "missing", bad, ROOT / "backend"):
        assert world.main(["build", "--state", str(state), "--prefix", "assetops_ds4tfake", "--key-root",
                           str(env.keys)], deps=env.deps) == 2
        assert capsys.readouterr().err.startswith("WORLD_STATE_INVALID")
    assert env.log == []


def test_t5_key_root_rules(env, tmp_path, capsys):
    bad = tmp_path / "openkeys"
    os.mkdir(bad, 0o755)
    os.chmod(bad, 0o755)
    assert env.main("build", "--key-root", str(bad)) == 2
    assert capsys.readouterr().err.startswith("WORLD_KEY_ROOT_INVALID")


def test_t5_existing_l1_key_directory(env, capsys):
    assert env.build() == 0
    names = {x["rung"]: x["database"] for x in _lines(capsys)[0]}
    kd = env.keys / names["L1"]
    for n in (names["L1"], names["L2"]):
        (env.state / "manifests" / f"{n}.json").unlink()
        env.admin.dbs.discard(n)
    (kd / f"{TID}.key").unlink()
    os.chmod(kd, 0o755)
    assert env.build() == 2
    assert capsys.readouterr().err.startswith("WORLD_KEY_ROOT_INVALID")
    os.chmod(kd, 0o700)
    (kd / f"{TID}.erased").write_text("tomb")
    assert env.build() == 0


# --- T6 clone, reset, drop ---------------------------------------------------------------------------------------------

def test_t6_clone_without_template_and_stale(env, capsys):
    assert env.main("clone", "--label", "t1") == 2
    assert capsys.readouterr().err.startswith("WORLD_NO_TEMPLATE")
    assert env.build() == 0
    capsys.readouterr()
    env.git.ids["backend/assetops_backend"] = "new-tree"
    assert env.main("clone", "--label", "t1") == 2
    assert capsys.readouterr().err.strip() == "WORLD_TEMPLATE_STALE code.backend/assetops_backend"


def test_t6_clone_reset_drop(env, capsys):
    assert env.build() == 0
    names = {x["rung"]: x["database"] for x in _lines(capsys)[0]}
    assert env.main("clone", "--label", "t1") == 0
    (line,), _ = _lines(capsys)
    assert line["database"] == "assetops_ds4tfake_audit_c_t1" and line["parent"] == names["L2"]
    assert "check_passed" in line and line["check_passed"] is None and line["key_dir"] == str(env.keys / names["L1"])
    m = env.manifests()["assetops_ds4tfake_audit_c_t1"]
    assert m["rung"] == "CLONE" and m["parent"] == names["L2"] and "check_passed" in m
    assert env.main("clone", "--label", "t1") == 2
    assert capsys.readouterr().err.startswith("WORLD_CLONE_EXISTS")
    env.log.clear()
    assert env.main("reset", "--label", "t1") == 0
    shape = [w for k, w in env.log if k == "admin" and w[:4] in ("DROP", "CREA")]
    assert shape == ['DROP DATABASE "assetops_ds4tfake_audit_c_t1"',
                     f'CREATE DATABASE "assetops_ds4tfake_audit_c_t1" TEMPLATE "{names["L2"]}" STRATEGY FILE_COPY']
    capsys.readouterr()
    assert env.main("drop", "--database", names["L0"]) == 2
    assert capsys.readouterr().err.strip() == f"WORLD_HAS_DESCENDANTS {names['L1']}"
    env.admin.sessions["assetops_ds4tfake_audit_c_t1"] = 1
    assert env.main("drop", "--database", "assetops_ds4tfake_audit_c_t1") == 2
    assert capsys.readouterr().err.startswith("WORLD_DATABASE_IN_USE")
    assert "assetops_ds4tfake_audit_c_t1" in env.admin.dbs
    env.admin.sessions.clear()
    for n in ("assetops_ds4tfake_audit_c_t1", names["L2"]):
        assert env.main("drop", "--database", n) == 0
    env.log.clear()
    assert env.main("drop", "--database", names["L1"]) == 0
    (line,), _ = _lines(capsys)[0][-1:], None
    assert line == {"database": names["L1"], "dropped": True, "key_dir": str(env.keys / names["L1"]), "keys_left": 0}
    order = [w for k, w in env.log if k == "step" or w.startswith("DROP")]
    assert order == ["pseudonym_key.erase", f'DROP DATABASE "{names["L1"]}"']
    assert names["L1"] not in env.manifests()


def test_t6_list_reports_manifests(env, capsys):
    assert env.build() == 0
    capsys.readouterr()
    assert env.main("list") == 0
    lines, _ = _lines(capsys)
    assert sorted(x["rung"] for x in lines) == ["L0", "L1", "L2"] and all(x["exists"] for x in lines)


def _checked(env, capsys):
    """A build, then a check that passes on hand payloads; returns the rung names."""
    assert env.build() == 0
    names = {x["rung"]: x["database"] for x in _lines(capsys)[0]}
    assert env.main("check") == 0, capsys.readouterr()
    capsys.readouterr()
    return names


def test_t6_staleness_of_a_passed_check(env, capsys):
    names = _checked(env, capsys)
    assert env.manifests()[names["L2"]]["check"]["passed"] is True
    assert env.main("clone", "--label", "same") == 0
    (line,), _ = _lines(capsys)
    assert (line["check_passed"], line["check_stale"]) == (True, None)
    env.git.ids["Docs/demo-sprint/product-direction-layer4/derived-values.json"] = "new-blob"
    assert env.main("clone", "--label", "dv") == 0
    (line,), _ = _lines(capsys)
    assert (line["check_passed"], line["check_stale"]) == (None, "derived_values")
    m = env.manifests()["assetops_ds4tfake_audit_c_dv"]
    assert (m["check_passed"], m["check_stale"]) == (None, "derived_values")
    del env.git.ids["Docs/demo-sprint/product-direction-layer4/derived-values.json"]
    env.git.ids[world.read_definition(DEFINITION).manifest] = "new-blob"
    assert env.main("clone", "--label", "mf") == 0
    (line,), _ = _lines(capsys)
    assert (line["check_passed"], line["check_stale"]) == (None, "manifest")
    del env.git.ids[world.read_definition(DEFINITION).manifest]
    env.git.ids["backend/tests/pg_harness.py"] = "new-blob"
    assert env.main("clone", "--label", "code") == 0
    (line,), _ = _lines(capsys)
    assert (line["check_passed"], line["check_stale"]) == (None, "code.backend/tests/pg_harness.py")
    del env.git.ids["backend/tests/pg_harness.py"]
    # tools/world.py is also a key part: `clone` refuses the template as stale, and `list` names the check part.
    env.git.ids["tools/world.py"] = "new-blob"
    assert env.main("list") == 0
    lines, _ = _lines(capsys)
    l2 = next(x for x in lines if x["rung"] == "L2")
    assert (l2["check_passed"], l2["check_stale"]) == (None, "code.tools/world.py")
    assert all((x["check_passed"], x["check_stale"]) == (None, "code.tools/world.py")
               for x in lines if x["rung"] == "CLONE")
    del env.git.ids["tools/world.py"]
    assert env.main("list") == 0
    lines, _ = _lines(capsys)
    assert all((x["check_passed"], x["check_stale"]) == (True, None) for x in lines if x["rung"] in ("L2", "CLONE"))


# --- T9 check ----------------------------------------------------------------------------------------------------------

def _check(env, capsys):
    code = env.main("check")
    lines, err = _lines(capsys)
    return code, {x["check"]: x for x in lines}, err


def test_t9_all_checks_pass_and_the_clone_is_dropped(env, capsys):
    assert env.build() == 0
    names = {x["rung"]: x["database"] for x in _lines(capsys)[0]}
    env.log.clear()
    code, by, _ = _check(env, capsys)
    assert code == 0 and sorted(by) == ["ALL"] + [f"C{n}" for n in range(1, 8)]
    assert all(x["state"] == "PASS" for x in by.values()), by
    assert by["ALL"] == {"check": "ALL", "state": "PASS"}
    assert by["C6"]["detail"] == "0 batches (telemetry none)"
    assert by["C4"]["detail"]["fails"] == [] and len(by["C4"]["detail"]["sites"]) == 6
    clone = "assetops_ds4tfake_audit_c_check"
    ddl = [w for k, w in env.log if k == "admin" and w[:4] in ("CREA", "DROP")]
    assert ddl[0] == f'CREATE DATABASE "{clone}" TEMPLATE "{names["L2"]}" STRATEGY FILE_COPY'
    assert f'DROP DATABASE "{clone}"' in ddl and clone not in env.admin.dbs
    block = env.manifests()[names["L2"]]["check"]
    assert block["passed"] is True and len(block["checks"]) == 7
    assert set(block["check_inputs"]["code"]) == set(world.CHECK_CODE) and env.disposed == 1


def test_t9_equal_has_no_tolerance_and_manifest_staleness():
    assert world._equal("1.000", 1.0) and not world._equal("1.001", 1.0) and not world._equal(None, 0.0)


def test_t9_c1_c2_c3_fail_naming_what_differs(env, capsys):
    assert env.build() == 0
    names = {x["rung"]: x["database"] for x in _lines(capsys)[0]}
    l1 = env.manifests()[names["L1"]]
    l1["inputs"]["lakeside-power/commercial/lakeside-power.billing.csv"] = "0" * 64
    (env.state / "manifests" / f"{names['L1']}.json").write_text(world.canonical(l1))
    l2 = env.manifests()[names["L2"]]
    l2["census"]["site"] = 4
    (env.state / "manifests" / f"{names['L2']}.json").write_text(world.canonical(l2))
    env.runner.verify_exit = 4
    code, by, _ = _check(env, capsys)
    assert code == 4
    assert by["C1"]["state"] == "FAIL" and "lakeside-power/commercial/lakeside-power.billing.csv" in by["C1"]["detail"]
    assert by["C2"]["state"] == "FAIL" and by["C2"]["detail"] == "site 4 != 3"
    assert by["C3"]["state"] == "FAIL" and "exit=4" in by["C3"]["detail"]
    assert env.manifests()[names["L2"]]["check"]["passed"] is False
    assert env.main("clone", "--label", "after") == 0
    (line,), _ = _lines(capsys)
    assert line["check_passed"] is False


def _oracle(payloads):
    d = world.read_definition(DEFINITION)
    derived = json.loads(DERIVED.read_text())
    return world.c4_oracle([("lakeside-power", p) for p in payloads], d, derived)


def _fail_lines(result):
    return [f["line"] for f in result["detail"]["fails"]]


def test_t9_oracle_on_hand_payloads():
    good = [hand_payload(c) for c in SITE_IDS]
    assert _oracle(good)["state"] == "PASS"
    # a plan-side E mismatch
    p = hand_payload("KOBO-001")
    p["targets"]["values"]["revenue"]["value"] = "1.00"
    assert _fail_lines(_oracle([p])) == ["lakeside-power/KOBO-001 plan.revenue class=E product=1.00 expected=3420.0"]
    # None on an E factor whose expected value is 0.0: never equal
    p = hand_payload("KOBO-001")
    p["actual"]["extra_l"] = {"value": None, "missing": {"record_kind": "X"}, "missing_leaves": []}
    assert _fail_lines(_oracle([p])) == ["lakeside-power/KOBO-001 actual.extra_l class=E product=None expected=0.0"]
    # a B factor carrying a value, and a B factor blank without its record
    p = hand_payload("KOBO-001")
    p["actual"]["adjustments_kwh"] = {"value": "0", "missing": None, "missing_leaves": []}
    p["actual"]["delivered_kwh"] = {"value": None, "missing": None, "missing_leaves": []}
    assert _fail_lines(_oracle([p])) == [
        "lakeside-power/KOBO-001 actual.adjustments_kwh class=B product=0 expected=45.0",
        "lakeside-power/KOBO-001 actual.delivered_kwh class=B product=None expected=" +
        str(json.loads(DERIVED.read_text())["sites"]["lakeside-power/Kobo"]["actual"]["nodes"]["delivered_kwh"])]
    # uncontracted and not_in_product
    p = hand_payload("KOBO-001")
    p["actual"]["new_factor"] = {"value": "1", "missing": None, "missing_leaves": []}
    del p["targets"]["values"]["staff"]
    lines = _fail_lines(_oracle([p]))
    assert any(x.startswith("lakeside-power/KOBO-001 actual.new_factor class=uncontracted") for x in lines)
    assert any(x.startswith("lakeside-power/KOBO-001 plan.staff class=not_in_product") for x in lines)
    # all blank: every E factor fails
    p = hand_payload("KOBO-001")
    for side in (p["actual"], p["targets"]["values"]):
        for f in side:
            side[f] = {"value": None, "missing": {"record_kind": "X"}, "missing_leaves": []}
    assert len(_fail_lines(_oracle([p]))) == 18 + 36
    # Kisiwa's three actual cells are judged by C4_SITE_CLASSES; Kobo's om blank fails
    p = hand_payload("KOBO-001")
    p["actual"]["om"] = {"value": None, "missing": {"record_kind": "EXPENSE"}, "missing_leaves": []}
    assert _fail_lines(_oracle([p]))[0].startswith("lakeside-power/KOBO-001 actual.om class=E product=None")
    p = hand_payload("KISIWA-001")
    assert p["actual"]["om"]["value"] is None and _oracle([p])["state"] == "PASS"


def test_t9_known_findings_are_marked_and_still_fail(monkeypatch):
    monkeypatch.setattr(world, "C4_KNOWN_FINDINGS", ("lakeside-power/MTO-001 plan.tariff D-DS4.27",))
    p = hand_payload("MTO-001")
    p["targets"]["values"]["tariff"] = {"value": None, "missing": {"record_kind": "BUDGET_LINE"}, "missing_leaves": []}
    p["actual"]["staff"]["value"] = "1"
    r = _oracle([p])
    assert r["state"] == "FAIL"
    marks = {f["line"].split(" class=")[0]: f["mark"] for f in r["detail"]["fails"]}
    assert marks == {"lakeside-power/MTO-001 plan.tariff": "known D-DS4.27", "lakeside-power/MTO-001 actual.staff": "new"}
    # a known cell carrying a wrong number is a new finding, not a known one
    p = hand_payload("MTO-001")
    p["targets"]["values"]["tariff"] = {"value": "9.99", "missing": None, "missing_leaves": []}
    assert [f["mark"] for f in _oracle([p])["detail"]["fails"]] == ["new"]


def test_c4_known_findings_are_empty():
    assert world.C4_KNOWN_FINDINGS == ()   # D-DS4.27: emptied after 5a F1; never re-added by a builder


def test_t9_c4_judges_exactly_the_declared_sites():
    d = world.read_definition(DEFINITION)
    derived = json.loads(DERIVED.read_text())
    rows = [("lakeside-power", hand_payload(c)) for c in SITE_IDS]
    assert world.c4_oracle(rows, d, derived, {"lakeside-power": 1})["state"] == "PASS"
    r = world.c4_oracle(rows[:2], d, derived, {"lakeside-power": 1})   # a Site missing
    assert r["state"] == "FAIL" and _fail_lines(r) == ["site_missing lakeside-power/MTO-001"]
    r = world.c4_oracle(rows[:2] + [rows[1]], d, derived, {"lakeside-power": 1})   # one Site twice, one missing
    assert r["state"] == "FAIL" and _fail_lines(r) == ["site_duplicate lakeside-power/KOBO-001",
                                                         "site_missing lakeside-power/MTO-001"]
    r = world.c4_oracle(rows + [rows[0]], d, derived, {"lakeside-power": 1})   # one Site twice
    assert r["state"] == "FAIL" and _fail_lines(r) == ["site_duplicate lakeside-power/KISIWA-001"]
    foreign = dict(hand_payload("KOBO-001"), site_code="NOPE-001")
    r = world.c4_oracle(rows + [("lakeside-power", foreign)], d, derived, {"lakeside-power": 1})
    assert r["state"] == "FAIL" and _fail_lines(r) == ["site_undeclared lakeside-power/NOPE-001"]
    two = rows + rows   # two snapshots of the tenant: every Site twice is right
    assert world.c4_oracle(two, d, derived, {"lakeside-power": 2})["state"] == "PASS"


def test_t9_c4_site_set_through_the_command(env, capsys):
    assert env.build() == 0
    capsys.readouterr()
    ids = list(SITE_IDS.values())
    env.rows_for = lambda got: ids[:2]
    code, by, _ = _check(env, capsys)
    assert code == 4 and by["C4"]["state"] == "FAIL" and by["ALL"]["state"] == "FAIL"
    assert [f["line"] for f in by["C4"]["detail"]["fails"]] == ["site_missing lakeside-power/MTO-001"]
    env.rows_for = lambda got: ids[:2] + [ids[1]]
    code, by, _ = _check(env, capsys)
    assert code == 4 and [f["line"] for f in by["C4"]["detail"]["fails"]] == [
        "site_duplicate lakeside-power/KOBO-001", "site_missing lakeside-power/MTO-001"]


def test_t9_c4_and_raising_checks_through_the_command(env, capsys):
    assert env.build() == 0
    capsys.readouterr()
    env.payloads["KOBO-001"]["targets"]["values"]["om"]["value"] = "1"
    env.snapshot_error = None
    code, by, _ = _check(env, capsys)
    assert code == 4 and by["C4"]["state"] == "FAIL"
    assert [f["mark"] for f in by["C4"]["detail"]["fails"]] == ["new"]
    env.snapshot_error = RuntimeError("store down")
    code, by, _ = _check(env, capsys)
    assert code == 4 and by["C4"]["state"] == "FAIL" and "store down" in by["C4"]["detail"]
    assert "assetops_ds4tfake_audit_c_check" not in env.admin.dbs
    env.runner.timeout_on = "verify"
    assert env.main("check") == 5
    assert "assetops_ds4tfake_audit_c_check" not in env.admin.dbs
    assert capsys.readouterr().err.startswith("WORLD_CAP_EXCEEDED")


def test_t9_c5_runs_under_its_own_base(env, capsys):
    env.environ.update({"ASSETOPS_TEST_DATABASE_URL": "postgresql+psycopg://a:b@127.0.0.1:55432/assetops_test",
                        "ASSETOPS_HEAVY_SLOT": "1", "ASSETOPS_HEAVY_DB": "1", "LANG": "C.UTF-8",
                        "DATABASE_URL": "postgresql://x/assetops_test", "ASSETOPS_TEST_DATABASE_BASE_URL": "x",
                        "ASSETOPS_TENANT_SLUG": "t", "ASSETOPS_PSEUDONYM_KEY_DIR": "/k",
                        "UNRELATED_PARENT_VAR": "1"})
    assert env.build() == 0
    capsys.readouterr()
    seen = {}

    def hook(e):
        seen.update(e)
        stem = e["ASSETOPS_TEST_DATABASE_URL"].rsplit("/", 1)[1][: -len("_test")]
        env.admin.dbs.add(f"{stem}_pt0a1b_tpl_test")   # a harness clone left behind

    env.runner.harness_hook = hook
    env.log.clear()
    code, by, _ = _check(env, capsys)
    assert code == 0 and by["C5"]["state"] == "PASS"
    base = seen["ASSETOPS_TEST_DATABASE_URL"].rsplit("/", 1)[1]
    assert re.fullmatch(r"assetops_wc5_pt[0-9a-f]{8}_base_test", base)
    assert not {"DATABASE_URL", "ASSETOPS_TENANT_SLUG", "ASSETOPS_PSEUDONYM_KEY_DIR"} & set(seen)
    # an explicit allow-list: nothing of the parent's (PG*, ASSETOPS_*, unrelated) reaches the child unless named
    assert set(seen) == {"PATH", "HOME", "LANG", "PYTHONPATH", "ASSETOPS_PG_PORT", "ASSETOPS_TEST_DATABASE_URL",
                         "ASSETOPS_HEAVY_SLOT", "ASSETOPS_HEAVY_DB"}
    assert seen["ASSETOPS_TEST_DATABASE_URL"].endswith("_base_test")
    assert seen["ASSETOPS_HEAVY_SLOT"] == "1" and seen["ASSETOPS_HEAVY_DB"] == "1"
    steps = [w for _, w in env.log]
    i_create = steps.index(f'CREATE DATABASE "{base}"')
    i_run = steps.index("harness")
    i_drop = steps.index(f'DROP DATABASE "{base}"')
    assert i_create < i_run < i_drop
    assert f'DROP DATABASE "{base[: -len("_test")]}_pt0a1b_tpl_test"' in steps
    assert not any("assetops_test" in w and "_base_test" not in w and "pt0a1b" not in w for w in steps)
    assert not any(w.endswith("[assetops_test]") or '"assetops_test"' in w for w in steps)
    env.runner.harness_exit = 1
    code, by, _ = _check(env, capsys)
    assert code == 4 and by["C5"]["state"] == "FAIL"
    env.runner.harness_exit = 0
    env.deps.which = lambda name, path=None: None
    env.log.clear()
    code, by, _ = _check(env, capsys)
    assert code == 4 and by["C5"]["state"] == "FAIL" and "pwsh not found" in by["C5"]["detail"]
    assert "harness" not in [w for _, w in env.log]


def test_t9b_contract_against_derived_values_and_manifest():
    derived = json.loads(DERIVED.read_text())
    for side, (e, b) in (("actual", (18, 29)), ("plan", (36, 11))):
        keys = set(derived["sites"]["lakeside-power/Kobo"][side]["nodes"])
        assert set(world.C4_CONTRACT[side]) == keys and len(keys) == 47
        classes = list(world.C4_CONTRACT[side].values())
        assert (classes.count("E"), classes.count("B")) == (e, b), side
    assert world.C4_CONTRACT["actual"]["adjustments_kwh"] == "B"
    assert world.C4_SITE_CLASSES == {"KISIWA-001": {"actual": {"om": "B", "cost_to_serve": "B", "contribution": "B"}}}
    manifest = yaml.safe_load(MANIFEST.read_text())
    assert manifest["accounting_period"] == "2026-10"   # each Site's `period` block is October
    (lake,) = [t for t in manifest["tenants"] if t["tenant"] == "lakeside-power"]
    assert lake["vertical"] == "MINI_GRID"
    estimated = {(site["code"], f) for site in lake["sites"]
                 for f, c in site["period"]["coverage"].items() if c == "ESTIMATED"}
    assert estimated == {("KISIWA-001", "om")}
    for code, (e, b) in (("KISIWA-001", (15, 32)), ("KOBO-001", (18, 29)), ("MTO-001", (18, 29))):
        cls = [world.site_class(code, "actual", f) for f in world.C4_CONTRACT["actual"]]
        assert (cls.count("E"), cls.count("B")) == (e, b), code
        cls = [world.site_class(code, "plan", f) for f in world.C4_CONTRACT["plan"]]
        assert (cls.count("E"), cls.count("B")) == (36, 11), code


# --- T7 slot -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("argv", [["build", "--key-root", "/nonexistent"], ["clone", "--label", "t1"],
                                  ["reset", "--label", "t1"], ["check"], ["drop", "--database", "x"]])
def test_t7_require_before_anything(env, argv):
    calls = []

    def require(tool, db=False):
        calls.append((tool, db, list(env.log)))
        raise SystemExit(69)
    env.deps.require = require
    with pytest.raises(SystemExit):
        world.main(argv, deps=env.deps)
    assert calls == [("world", True, [])]


def test_t7_list_does_not_require(env):
    env.deps.require = lambda *a, **k: (_ for _ in ()).throw(AssertionError("require"))
    assert env.main("list") == 0


# --- T11 seams ---------------------------------------------------------------------------------------------------------

SQL_SHAPES = [
    r"SELECT timezone FROM site WHERE id = '\{site\}'",
    r'CREATE DATABASE "\{[a-z_]+\}"( TEMPLATE "\{[a-z_]+\}" STRATEGY FILE_COPY)?',
    r'ALTER DATABASE "\{[^}]+\}" WITH ALLOW_CONNECTIONS false',
    r'DROP DATABASE "\{[^}]+\}"',
    r"SELECT 1 FROM pg_database WHERE datname = :n",
    r"SELECT count\(\*\) FROM pg_stat_activity WHERE datname = :n",
    r"SELECT datname FROM pg_database",
    r"SELECT pg_database_size\(:n\)",
    r"SELECT table_name FROM information_schema\.tables .*",
    r'SELECT count\(\*\) FROM "\{t\}"',
    r"SELECT id, slug FROM tenant",
]


def test_t11_world_tool_seams():
    src = (ROOT / "tools/world.py").read_text()
    for word in ("INSERT", "UPDATE", "DELETE", "COPY", "TRUNCATE", "FORCE"):
        assert not re.search(rf"\b{word}\b", src), word
    tree = ast.parse(src)
    sql = []
    parts = {id(v) for n in ast.walk(tree) if isinstance(n, ast.JoinedStr) for v in n.values}
    for node in ast.walk(tree):
        if id(node) in parts:
            continue
        if isinstance(node, ast.JoinedStr):
            text = "".join(v.value if isinstance(v, ast.Constant) else "{" + ast.unparse(v.value) + "}" for v in node.values)
            text = re.sub(r"\{check_name\([^}]*\}", "{n}", text)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
        else:
            continue
        if re.match(r"(CREATE|ALTER|DROP|SELECT) ", text):
            sql.append(text)
    assert sql
    for s in sql:
        assert any(re.fullmatch(p, s, re.S) for p in SQL_SHAPES), s
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        for n in names:
            assert not n.endswith("_api") and ".adapters" not in n, n
    backend = ROOT / "backend/assetops_backend"
    for p in [*backend.rglob("main.py"), *backend.rglob("*_api.py")]:
        assert "bulk_load" not in p.read_text(), p
    bulk = (backend / "evidence/bulk_load.py").read_text()
    for banned in ("assetops_simulator", "assetops_backend.host", "assetops_backend.commercial"):
        assert banned not in bulk
