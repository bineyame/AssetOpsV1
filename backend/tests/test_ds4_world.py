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

    def __call__(self, argv, cwd, env, timeout):
        args = list(argv[1:])
        self.envs.append((args, dict(env)))
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
            out = json.dumps({"portfolio_snapshot_id": "p-1", "sites": {"KOBO-001": "s-1"}})
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
                               environ=self.environ)

    def main(self, *argv, capsys=None, prefix="assetops_ds4tfake"):
        common = ["--state", str(self.state), "--prefix", prefix]
        args = [argv[0], *common, *argv[1:]]
        code = world.main(args, deps=self.deps)
        return code

    def build(self):
        return self.main("build", "--key-root", str(self.keys))

    def manifests(self):
        return {p.stem: json.loads(p.read_text()) for p in (self.state / "manifests").glob("*.json")}


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
    assert l2["snapshots"] == {"lakeside-power:2026-10": {"portfolio_snapshot_id": "p-1", "sites": {"KOBO-001": "s-1"}}}
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
