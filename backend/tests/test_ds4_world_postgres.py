"""DS4 (spec `specs/DS4-template-ladder/spec.md` §5, T12 to T14): `tools/world.py` for real on Postgres.

Every database carries the prefix `assetops_ds4t<8 hex>` (`<prefix>_audit_*`, plus C5's own harness base), and the
module's `finally` drops them all through the tool, children first, then sweeps any left. Keys and state live in
temporary 0700 directories. The git reader is this checkout's `HEAD` with a clean status, so a dirty build tree does
not refuse; the parity run (C5) is injected to exit 0, since the regression set runs that DS3 file itself.
Requires ASSETOPS_TEST_DATABASE_URL (backend/TESTING.md); the tool's admin URL is 127.0.0.1 (spec §3.5).
"""
from __future__ import annotations

import io
import json
import os
import secrets
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import world  # noqa: E402

PREFIX = f"assetops_ds4t{secrets.token_hex(4)}"


class HeadGit(world.Git):
    """HEAD's ids, read by the real git reader; the status is clean by injection."""

    def dirty(self, paths):
        return []


def _runner(argv, cwd, env, timeout):
    if str(argv[0]).endswith("pwsh"):
        return subprocess.CompletedProcess(argv, 0, "parity injected: 0\n", "")
    return world._real_runner(argv, cwd, env, timeout)


@pytest.fixture(scope="module")
def tool(tmp_path_factory):
    base = tmp_path_factory.mktemp("ds4w")
    state, keys = base / "state", base / "keys"
    os.mkdir(state, 0o700)
    os.mkdir(keys, 0o700)
    admin = world.Admin(os.environ)
    deps = world.Deps(admin=admin, runner=_runner, git=HeadGit(world.REPO), require=lambda tool, db=False: None,
                      which=lambda name, path=None: "/usr/bin/pwsh")

    def run(*argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = world.main([argv[0], "--state", str(state), "--prefix", PREFIX, *argv[1:]], deps=deps)
        return code, [json.loads(x) for x in out.getvalue().splitlines() if x.strip()], err.getvalue()

    t = type("Tool", (), {})()
    t.run, t.state, t.keys, t.admin, t.deps = run, state, keys, admin, deps
    try:
        yield t
    finally:
        try:
            order = {"CLONE": 0, "L2": 1, "L1": 2, "L0": 3}
            ms = sorted((json.loads(p.read_text()) for p in (state / "manifests").glob("*.json")),
                        key=lambda m: order.get(m.get("rung"), 0))
            for m in ms:
                run("drop", "--database", m["database"])
        finally:
            for (name,) in admin("SELECT datname FROM pg_database"):
                if name.startswith(f"{PREFIX}_audit_"):
                    admin(f'DROP DATABASE "{world.check_name(name, os.environ)}"')
            admin.dispose()


def _world(t):
    import argparse

    args = argparse.Namespace(prefix=PREFIX, state=str(t.state), definition=world.DEFINITION, cap_seconds=600.0)
    w = world.World(args, t.deps)
    w.state = t.state
    return w


def _ours(t):
    return sorted(n for (n,) in t.admin("SELECT datname FROM pg_database") if n.startswith(PREFIX))


@pytest.fixture(scope="module")
def built(tool):
    code, lines, err = tool.run("build", "--key-root", str(tool.keys))
    assert code == 0, err
    return {x["rung"]: x["database"] for x in lines}


def test_t12_build_clone_check(tool, built):
    names = built
    assert sorted(names) == ["L0", "L1", "L2"]
    for n in names.values():
        assert tool.admin("SELECT datallowconn FROM pg_database WHERE datname = :n", {"n": n}) == [(False,)]
    m = {r: json.loads((tool.state / "manifests" / f"{n}.json").read_text()) for r, n in names.items()}
    c1 = m["L1"]["census"]
    assert c1["tenant"] == 1 and c1["site"] == 3 and c1["commercial_record"] > 0 and c1["accepted_evidence"] == 0
    assert m["L2"]["census"]["structure_snapshot"] == 4
    assert [s["exit"] for s in m["L2"]["steps"] if s["step"].startswith("L2.observe")] == [0]
    before = _ours(tool)
    code, lines, err = tool.run("build", "--key-root", str(tool.keys))
    assert code == 0 and [x["reused"] for x in lines] == [True, True, True] and _ours(tool) == before, err
    code, (line,), err = tool.run("clone", "--label", "t1")
    assert code == 0, err
    census, _ = _world(tool).census(line["database"])
    assert census == m["L2"]["census"]

    code, lines, err = tool.run("check")
    by = {x["check"]: x for x in lines}
    for c in ("C1", "C2", "C3", "C6", "C7"):
        assert by[c]["state"] == "PASS", by[c]
    assert by["C5"]["state"] == "PASS", by["C5"]
    c4 = by["C4"]["detail"]
    news = [f["line"] for f in c4["fails"] if f["mark"] == "new"]
    assert news == [], news   # a difference here is a finding for the Architect, never a loosened rule
    known = {f["line"].split(" class=")[0] for f in c4["fails"]}
    assert known == {" ".join(k.split(" ")[:2]) for k in world.C4_KNOWN_FINDINGS}
    assert by["C4"]["state"] == ("FAIL" if world.C4_KNOWN_FINDINGS else "PASS")
    assert code == (4 if world.C4_KNOWN_FINDINGS else 0)
    blanks = {" ".join(b.split(" ")[:2]) for b in c4["blanks"]}
    want = {f"lakeside-power/{code_} {side}.{f}" for code_ in ("KISIWA-001", "KOBO-001", "MTO-001")
            for side in ("actual", "plan") for f in world.C4_CONTRACT[side] if world.site_class(code_, side, f) == "B"}
    want |= {" ".join(k.split(" ")[:2]) for k in world.C4_KNOWN_FINDINGS}
    assert blanks == want, (sorted(blanks - want), sorted(want - blanks))
    block = json.loads((tool.state / "manifests" / f"{names['L2']}.json").read_text())["check"]
    assert block["passed"] is (not world.C4_KNOWN_FINDINGS) and len(block["checks"]) == 7
    assert f"{PREFIX}_audit_c_check" not in _ours(tool)
    assert not [n for (n,) in tool.admin("SELECT datname FROM pg_database") if n.startswith("assetops_wc5_")]
    sys.stderr.write("DS4 T12 check lines:\n" + "\n".join(json.dumps(x, sort_keys=True) for x in lines) + "\n")


def test_t14_in_use(tool, built):
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool

    code, (line,), err = tool.run("clone", "--label", "t2")
    assert code == 0, err
    engine = create_engine(world.rung_url(line["database"], os.environ), poolclass=NullPool)
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
            code, _, err = tool.run("drop", "--database", line["database"])
            assert code == 2 and err.startswith("WORLD_DATABASE_IN_USE")
            assert line["database"] in _ours(tool)
    finally:
        engine.dispose()
    code, _, err = tool.run("drop", "--database", line["database"])
    assert code == 0, err


def test_t13_drop_order(tool, built):
    from uuid import UUID

    from assetops_backend.commercial.adapters.file_key_store import key_state

    names = built
    l1 = json.loads((tool.state / "manifests" / f"{names['L1']}.json").read_text())
    code, _, err = tool.run("drop", "--database", names["L0"])
    assert code == 2 and err.startswith("WORLD_HAS_DESCENDANTS")
    clones = [json.loads(p.read_text())["database"] for p in (tool.state / "manifests").glob("*.json")
              if json.loads(p.read_text())["rung"] == "CLONE"]
    for n in [*clones, names["L2"]]:
        code, _, err = tool.run("drop", "--database", n)
        assert code == 0, err
    code, (line,), err = tool.run("drop", "--database", names["L1"])
    assert code == 0, err
    assert line["keys_left"] == 0 and line["key_dir"] == l1["key_dir"]
    for tid in l1["tenants"].values():
        assert key_state(l1["key_dir"], UUID(tid)) == "ERASED"
    code, _, err = tool.run("drop", "--database", names["L0"])
    assert code == 0, err
    assert _ours(tool) == []
    assert not list((tool.state / "manifests").glob(f"{PREFIX}*"))
