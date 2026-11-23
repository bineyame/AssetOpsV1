"""DD3c part 2 T6 (D-DD.109): migration `0074_unit_role_sets` text, no database.

Each replacement is counted once, the downgrade bodies are byte-equal to 0048's, the migration's own literals equal
`MINI_DEPTH_ROLE_SETS`, and every Python gate reads the constant (none names roles-4 alone).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from assetops_backend.sites import binding_roles

VERSIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"
R4, R5 = "minigrid-roles-4", "minigrid-roles-5"


def _load(name: str):
    path = VERSIONS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_dd3c_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def m74():
    return _load("0074_unit_role_sets")


@pytest.fixture(scope="module")
def m48():
    return _load("0048_daylight_enqueue")


def test_constant_is_roles4_and_roles5() -> None:
    assert binding_roles.MINI_DEPTH_ROLE_SETS == (R4, R5)


def test_migration_literals_equal_the_constant(m74) -> None:
    assert m74.ROLE_SETS == binding_roles.MINI_DEPTH_ROLE_SETS
    assert (m74.revision, m74.down_revision) == ("0074_unit_role_sets", "0073_named_option_levers")


def test_upgrade_replaces_each_text_once(m74, m48) -> None:
    old, new = m48._functions_0048(), m74.functions_0074()
    assert old.count(f"b.role_set = '{R4}'") == 1 and new.count(f"b.role_set = '{R4}'") == 0
    assert new.count(f"b.role_set IN ('{R4}', '{R5}')") == 1
    assert new.count(f"current `{R4}` or `{R5}` binding set") == 1
    assert old.replace(f"b.role_set = '{R4}'", f"b.role_set IN ('{R4}', '{R5}')").replace(
        f"current `{R4}` binding set", f"current `{R4}` or `{R5}` binding set") == new
    hour = m74.renewable_hour_0074()
    assert hour.count(f"s.role_set IN ('{R4}', '{R5}')") == 1 and f"s.role_set = '{R4}'" not in hour
    assert hour.startswith("\nCREATE OR REPLACE FUNCTION mini_renewable_hour(")
    # the two other functions hold no role-set text and are re-created unchanged inside the same body
    for name in ("mini_enqueue_accepted", "mini_enqueue_configuration"):
        assert f"CREATE OR REPLACE FUNCTION {name}(" in new


def test_a_count_other_than_one_raises(m74) -> None:
    with pytest.raises(RuntimeError, match="0074"):
        m74._replace_once("abc", "x", "y")
    with pytest.raises(RuntimeError, match="0074"):
        m74._replace_once("x x", "x", "y")


def test_downgrade_bodies_are_byte_equal_to_0048(m74, m48) -> None:
    assert m74.downgrade_bodies() == (m48.RENEWABLE_HOUR.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1),
                                      m48._functions_0048())


def test_no_python_gate_names_roles4_alone() -> None:
    """D-DD.109: every Python gate reads `MINI_DEPTH_ROLE_SETS`."""
    root = Path(binding_roles.__file__).resolve().parents[1]
    for rel in ("mini_depth/inputs.py", "mini_depth/read.py", "mini_depth/store.py"):
        body = (root / rel).read_text()
        assert "ROLE_SET_MINIGRID_4" not in body, rel
        assert "MINI_DEPTH_ROLE_SETS" in body, rel


def test_dispatch_roles_by_set_is_the_served_minigrid_sets() -> None:  # D-DD.109 P5
    from assetops_backend.analytics import assessment_worker

    served = binding_roles.SERVED_ROLE_SETS_BY_SITE_TYPE["MINIGRID"]
    assert list(assessment_worker.ROLES_BY_SET) == sorted(served)
    assert assessment_worker.ROLES_BY_SET[R5] == tuple(binding_roles.roles_for(R5))
