"""T1b: the second Postgres test lane, the Python side (specs/T1-heavy-tool-slot-pool/spec-T1b.md §4, §6, §8).

No database and no URL: the lane checks are pure functions, the runner check is a text check (the script never prints
the URL), and the list of files that create databases keeps the fixed-name class closed (§6).
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools" / "run-host-tests.ps1"


def _checker():
    spec = importlib.util.spec_from_file_location("heavy_slot_check_t1b", ROOT / "tools" / "heavy_slot_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


h = _checker()
URL = "postgresql+psycopg://u:p@{host}:1/{name}"


def _line(lane: str, name: str, why: str) -> str:
    return f"heavy-slot: refused: pytest with Postgres in database lane {lane} may not use {name}: {why}."


# ---- T-L1: lane_database_refusal, the five rules of §4 ----
@pytest.mark.parametrize(("lane", "url", "want"), [
    ("b", URL.format(host="127.0.0.1", name="assetops_test"), _line("b", "assetops_test", "it is lane a's database")),
    ("a", URL.format(host="localhost", name="assetops_b_test"), _line("a", "assetops_b_test", "it is lane b's database")),
    ("a", URL.format(host="127.0.0.1", name="assetops"), _line("a", "assetops", "its name does not end in _test")),
    ("b", URL.format(host="10.0.0.9", name="assetops_b_test"),
     _line("b", "assetops_b_test", "the server is not this machine's development server (host 10.0.0.9)")),
    ("a", "mysql://u:p@127.0.0.1:1/assetops_test", _line("a", "that URL", "the target is unclear (DRIVER_NOT_POSTGRES)")),
    ("a", None, _line("a", "that URL", "the target is unclear (URL_UNREADABLE)")),
    ("a", URL.format(host="127.0.0.1", name="assetops_test"), None),
    ("b", URL.format(host="127.0.0.1", name="assetops_b_test"), None),
    ("b", "postgresql+psycopg://u:p@[::1]:1/assetops_b_test", None),
    ("a", URL.format(host="127.0.0.1", name="assetops_x_test"), None),  # a private base stays allowed
    ("b", URL.format(host="127.0.0.1", name="assetops_x_test"), None),
])
def test_l1_lane_database_refusal(lane, url, want) -> None:
    assert h.lane_database_refusal(lane, url, environ={}) == want


def test_l1_an_unclear_environment_is_refused_and_an_import_failure_is_named(monkeypatch) -> None:
    got = h.lane_database_refusal("a", URL.format(host="127.0.0.1", name="assetops_test"), environ={"PGHOST": "x"})
    assert got == _line("a", "that URL", "the target is unclear (ENVIRONMENT PGHOST)")
    import builtins

    real = builtins.__import__

    def no_backend(name, *args, **kwargs):
        if name.startswith("assetops_backend"):
            raise ImportError(name)
        return real(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_backend)
    got = h.lane_database_refusal("a", URL.format(host="127.0.0.1", name="assetops_test"), environ={})
    assert got == _line("a", "that URL", "assetops_backend does not import")


# ---- T-L2: lane_workers_refusal (D-T1.25) ----
WORKERS = "heavy-slot: refused: a database-lane run uses at most -n 2 (T1b); use --db for more."


@pytest.mark.parametrize(("lane", "exclusive", "n", "refused"), [
    ("b", False, None, False), ("b", False, 0, False), ("b", False, 1, False), ("b", False, 2, False),
    ("b", False, 3, True), ("a", False, "auto", True), ("a", False, 8, True),
    ("a", True, 3, False), ("a", True, "auto", False), ("a", True, 16, False),
])
def test_l2_lane_workers_refusal(monkeypatch, lane, exclusive, n, refused) -> None:
    monkeypatch.setattr(h, "_in_container", lambda: False)
    monkeypatch.setattr(h, "held_lane", lambda env, **opts: lane)
    monkeypatch.setattr(h, "exclusive", lambda env, **opts: exclusive)
    assert h.lane_workers_refusal(n, env={}) == (WORKERS if refused else None)


def test_l2_no_lane_and_a_container_pass(monkeypatch) -> None:
    monkeypatch.setattr(h, "held_lane", lambda env, **opts: None)
    monkeypatch.setattr(h, "exclusive", lambda env, **opts: False)
    monkeypatch.setattr(h, "_in_container", lambda: False)
    assert h.lane_workers_refusal(8, env={}) is None
    monkeypatch.setattr(h, "held_lane", lambda env, **opts: "b")
    monkeypatch.setattr(h, "_in_container", lambda: True)
    assert h.lane_workers_refusal(8, env={}) is None


# ---- T-L3: _case_db_name is stem-derived; lane a's names are byte-identical (A7) ----
def test_l3_case_db_name_follows_the_base(monkeypatch) -> None:
    import pg_harness
    import test_out_b4_board_postgres as b4

    monkeypatch.setenv(pg_harness.BASE_ENV, URL.format(host="127.0.0.1", name="assetops_test"))
    assert b4._case_db_name("kobo", "d") == "assetops_out_d_kobo_test"
    assert b4._case_db_name("ev") == "assetops_out_b_ev_test"
    monkeypatch.setenv(pg_harness.BASE_ENV, URL.format(host="127.0.0.1", name="assetops_b_test"))
    assert b4._case_db_name("kobo", "d") == "assetops_b_out_d_kobo_test"


# ---- T-L4 / T-L6: the host runner picks the lane's database (text check) ----
def test_l4_runner_picks_the_lane_database() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))  # code, not comments
    assert "'assetops_test'" in code and "'assetops_b_test'" in code
    assert re.search(r"GetFileName\(\$env:ASSETOPS_HEAVY_DB_LANE\)[^\n]*\n[^\n]*-eq 'db-job-b\.lock'", code), \
        "run-host-tests.ps1 must test the leaf of ASSETOPS_HEAVY_DB_LANE against db-job-b.lock"
    assert not re.search(r"(Write-Output|Write-Host|echo)[^\n]*ASSETOPS_TEST_DATABASE_URL", text), "never print the URL"


def test_l6_lane_databases_match_the_runner() -> None:
    names = set(re.findall(r"\b(assetops_(?:b_)?test)\b", RUNNER.read_text(encoding="utf-8")))
    assert names == set(h.LANE_DATABASES.values()) == {"assetops_test", "assetops_b_test"}
    assert h.LANE_DATABASES == {"a": "assetops_test", "b": "assetops_b_test"}


# ---- T-L5: the files that create databases and why each cannot collide across runs (§6, A8) ----
CREATE_SITES = {
    "backend/tests/mechanism_dataset.py": "content-keyed mechanism template, built exclusively, staged and renamed",
    "backend/tests/pg_harness.py": "stem + run id",
    "backend/tests/setup_cache.py": "content-keyed snapshot under an advisory lock, staged and renamed",
    "backend/tests/test_ds4_world.py": "a fake (no server)",
    "backend/tests/test_md0_mechanism_postgres.py": "random token",
    "backend/tests/test_out_b4_board_postgres.py": "stem-derived (_case_db_name, T1b)",
    "backend/tests/test_pg_harness.py": "stem-derived",
    "backend/tests/test_w504_ev_work_producer_postgres.py": "random token",
    "backend/tests/test_wk_walk_world.py": "a fake (no server)",
}


def test_l5_every_create_database_site_is_listed() -> None:
    needle = "CREATE " + "DATABASE"  # not the literal, so this file is not a site itself
    r = subprocess.run(["git", "grep", "-l", needle, "--", "backend/tests", "host"], cwd=ROOT,
                       capture_output=True, text=True, check=False)
    assert r.returncode in (0, 1), r.stderr
    found = {line for line in r.stdout.splitlines() if line}
    assert found == set(CREATE_SITES), (
        f"new or removed {needle} sites: {sorted(found ^ set(CREATE_SITES))}; list each with the reason its "
        "name cannot collide between two runs on one server (spec-T1b.md §6)")
