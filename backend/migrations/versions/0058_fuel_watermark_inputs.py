"""DIESEL-1-R3j3: the CH-5c W2 change log covers the two fuel tables the stored routes read since K4b.

The stored board, summary and Portfolio read `fuel_balance_window` and `fuel_residual_consequence_revision` (K4b).
Both are append-only (`ledger_append_only`), so in practice only the INSERT trigger fires; all four triggers are
created because the W6 guard requires them. The generator is 0047's own (`_columns`, `_trigger_sql`), loaded the way
0048 loads 0029; 0047 and its frozen `INPUT_TABLES` are not edited. Both tables carry `tenant_id` and `site_id`, so
the change rows are Site-scoped. No backfill row: the new head changes `code_version`, so stored bodies rebuild once.

Downgrade drops the triggers and functions; `chain_input_change` rows already written stay (the log is append-only).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from alembic import op

revision = "0058_fuel_watermark_inputs"
down_revision = "0057_fuel_verification"
branch_labels = None
depends_on = None


def _m0047():
    path = Path(__file__).with_name("0047_chain_response.py")
    spec = importlib.util.spec_from_file_location("_m0047_chain_response", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_M = _m0047()
INPUT_TABLES = ("fuel_balance_window", "fuel_residual_consequence_revision")


def upgrade() -> None:
    bind = op.get_bind()
    for table in INPUT_TABLES:
        cols = _M._columns(bind, table)
        if not cols:
            raise RuntimeError(f"watermark input table {table!r} does not exist")
        tenant = _M._TENANT_COLUMN.get(table, "tenant_id" if "tenant_id" in cols else None)
        site = _M._SITE_COLUMN.get(table, "site_id" if "site_id" in cols else None)
        op.execute(_M._trigger_sql(table, tenant, site))


def downgrade() -> None:
    for table in reversed(INPUT_TABLES):
        for suffix in ("trunc", "del", "upd", "ins"):
            op.execute(f"DROP TRIGGER IF EXISTS {table}_cic_{suffix} ON {table}")
        op.execute(f"DROP FUNCTION IF EXISTS chain_input_change_{table}()")
