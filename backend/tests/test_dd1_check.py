"""DD1.3 (spec `specs/DD-demo-data/spec.md` §7 DD1.3, §8.1; D-DD.14, D-DD.31): the independent checker, no database.

C-DD1's judgement on rows, C-DD13's on a fake product client, the history pin, the stubs, and the seam: the checker
imports nothing from the simulator or the generators.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import dd_check  # noqa: E402


@pytest.fixture(scope="module")
def inputs() -> dd_check.Inputs:
    return dd_check.read_inputs("postgresql+psycopg://u:p@dd.invalid:1/x_test")


def _expected_rows(manifest: dict):
    sites, names = dd_check.expected_cast(manifest)
    return {k: set(v) for k, v in sites.items()}, dd_check.expected_triples(manifest, names)


def test_history_is_pinned_by_the_golden(tmp_path) -> None:
    changed = tmp_path / "history.json"
    changed.write_bytes(dd_check.HISTORY.read_bytes() + b" ")
    with pytest.raises(dd_check.InputError, match="is not the golden's"):
        dd_check.read_inputs("x", history=changed)


def test_cast_is_the_manifests_three_tenants_and_nine_sites(inputs) -> None:
    sites, triples = _expected_rows(inputs.manifest)
    assert sorted(sites) == ["harvest-cold", "lakeside-power", "metro-bus"]
    assert sum(len(v) for v in sites.values()) == 9
    assert ("COLD-THIKA", "COLDCHAIN") in sites["harvest-cold"] and ("EV-RUI", "EV_CHARGING") in sites["metro-bus"]
    assert ("Brian", "SITE_MANAGER", "COLD-THIKA") in triples["harvest-cold"]
    assert ("Achieng", "ANALYST", "") in triples["metro-bus"]


def test_c_dd1_passes_on_the_cast_and_fails_on_each_plant(inputs) -> None:
    sites, triples = _expected_rows(inputs.manifest)
    assert dd_check.judge_cast(inputs.manifest, sites, triples).passed
    plants = {
        "a site manager bound to another Site": lambda s, t: (
            t["lakeside-power"].discard(("Peter", "SITE_MANAGER", "KOBO-001")),
            t["lakeside-power"].add(("Peter", "SITE_MANAGER", "MTO-001"))),
        "a person missing": lambda s, t: t["metro-bus"].discard(("Lucy", "FINANCE_AND_COMMERCIAL_LEAD", "")),
        "a wrong product type": lambda s, t: (s["harvest-cold"].discard(("COLD-KIRI", "COLDCHAIN")),
                                              s["harvest-cold"].add(("COLD-KIRI", "MINIGRID"))),
        "a fourth tenant": lambda s, t: s.setdefault("demo", set()),
    }
    for name, plant in plants.items():
        s, t = _expected_rows(inputs.manifest)
        plant(s, t)
        result = dd_check.judge_cast(inputs.manifest, s, t)
        assert not result.passed and result.detail, name


class _Response:
    def __init__(self, status: int, body=None) -> None:
        self.status_code, self._body = status, body

    def json(self):
        return self._body


class _FakeClient:
    def __init__(self, own: list[str], leak: str | None = None) -> None:
        self.own, self.leak = own, leak

    def get(self, path: str) -> _Response:
        if path == "/api/sites":
            return _Response(200, {"sites": [{"site_id": c} for c in self.own]})
        code = path.rsplit("/", 1)[1]
        return _Response(200 if code in self.own or code == self.leak else 404)


def test_c_dd13_judges_reads_and_fails_on_a_leak(inputs) -> None:
    sites, _ = _expected_rows(inputs.manifest)
    own = {slug: [c for c, _ in rows] for slug, rows in sites.items()}
    ok = dd_check.check_tenant_isolation(inputs, lambda _url, slug: _FakeClient(own[slug]))
    assert ok.passed and ok.pending == ["TENANT-1 refused and counted: planted by DD5.2"]
    leak = dd_check.check_tenant_isolation(
        inputs, lambda _url, slug: _FakeClient(own[slug], leak="EV-EMB" if slug == "harvest-cold" else None))
    assert not leak.passed and "harvest-cold: GET /api/sites/EV-EMB" in leak.detail[0]
    listed = dd_check.check_tenant_isolation(
        inputs, lambda _url, slug: _FakeClient(own[slug] + (["KOBO-001"] if slug == "metro-bus" else [])))
    assert not listed.passed


def test_stubs_fail_naming_their_unit(inputs) -> None:
    stubs = tuple(c for c in dd_check.ORDER if c in dd_check.STUBS)
    results = dd_check.run(inputs, stubs)
    assert [r.check for r in results] == list(stubs) and not any(r.passed for r in results)
    assert set(dd_check.STUBS) | {"C-DD1", "C-DD2", "C-DD3", "C-DD4", "C-DD6", "C-DD11", "C-DD12", "C-DD13", "C-DD16", "C-DD21"} == set(dd_check.ORDER)
    assert not set(dd_check.STUBS) & set(dd_check.LIVE)
    assert dd_check.stub("C-DD5").detail == ["not live: its unit DD4.4 has not landed"]


def test_unknown_check_is_a_usage_error(capsys) -> None:
    assert dd_check.main(["--database-url", "x", "--only", "C-DD99"]) == 2
    assert "DD_CHECK_USAGE" in capsys.readouterr().err


def test_checker_shares_no_module_with_the_generators() -> None:
    tree = ast.parse((ROOT / "tools/dd_check.py").read_text(encoding="utf-8"))
    # C-DD21 compares the writer's table with the backend's, so its one function imports the writer's `telemetry`
    # (DD3.1); every other function and the module level stay free of it.
    inside = {id(n) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) and f.name == "check_property_table_parity"
              for n in ast.walk(f)}
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) and id(n) not in inside for a in n.names}
    names |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module and id(n) not in inside}
    banned = ("assetops_simulator", "simulator", "world", "world_history", "walk_world", "check_manifest",
              "check_alignment", "generate", "exports")
    assert not [n for n in names if n.split(".")[0] in banned], names
    assert json.loads(dd_check.HISTORY_GOLDEN.read_text())["file_sha256"]
