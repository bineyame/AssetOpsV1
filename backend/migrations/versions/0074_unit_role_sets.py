"""DD3c part 2 (D-DD.109, D-DD.108 Q1): the mini-depth enqueue gate reads `minigrid-roles-4` or `minigrid-roles-5`.

Built from 0048's own texts (loaded as 0048 loads 0029). Upgrade: 0048's three enqueue functions as `CREATE OR
REPLACE`, with the final gate in `mini_enqueue_hour` counting a current `minigrid-roles-4` or `minigrid-roles-5`
binding set (two overlapping sets of either name give no work), and `mini_renewable_hour` reading a
`pv_available_power` binding of either set. `mini_enqueue_accepted` and `mini_enqueue_configuration` hold no role-set
text and are re-created unchanged inside the same body. Each replacement is counted exactly once; any other count
raises. No table, no data change, no trigger change. Downgrade restores 0048's bodies unchanged.

The migration writes its own literals (migrations do not import live code); `test_dd3c_migration_0074.py` asserts
they equal `sites/binding_roles.MINI_DEPTH_ROLE_SETS`.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from alembic import op

revision = "0074_unit_role_sets"
down_revision = "0073_named_option_levers"
branch_labels = None
depends_on = None

#: D-DD.109: equal to `MINI_DEPTH_ROLE_SETS` (asserted by test, not imported).
ROLE_SETS: tuple[str, ...] = ("minigrid-roles-4", "minigrid-roles-5")


def _m0048():
    path = Path(__file__).with_name("0048_daylight_enqueue.py")
    spec = importlib.util.spec_from_file_location("_m0048_daylight_enqueue", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_M = _m0048()
_R4 = _M.ROLE_SET_4
_LIST = "(" + ", ".join(f"'{s}'" for s in ROLE_SETS) + ")"


def _replace_once(body: str, old: str, new: str) -> str:
    if body.count(old) != 1:
        raise RuntimeError(f"0074: expected one 0048 text {old[:40]!r}, found {body.count(old)}")
    return body.replace(old, new)


def _or_replace(body: str) -> str:
    return _replace_once(body, "CREATE FUNCTION", "CREATE OR REPLACE FUNCTION")


def functions_0074() -> str:
    body = _replace_once(_M._functions_0048(), f"b.role_set = '{_R4}'", f"b.role_set IN {_LIST}")
    return _replace_once(body, f"current `{_R4}` binding set", f"current `{_R4}` or `{ROLE_SETS[1]}` binding set")


def renewable_hour_0074() -> str:
    return _replace_once(_or_replace(_M.RENEWABLE_HOUR), f"s.role_set = '{_R4}'", f"s.role_set IN {_LIST}")


def downgrade_bodies() -> tuple[str, str]:
    return _or_replace(_M.RENEWABLE_HOUR), _M._functions_0048()


def upgrade() -> None:
    op.execute(renewable_hour_0074())
    op.execute(functions_0074())


def downgrade() -> None:
    for body in downgrade_bodies():
        op.execute(body)
