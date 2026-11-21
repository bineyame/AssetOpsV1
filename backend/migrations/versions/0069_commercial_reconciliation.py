"""3A7 (`specs/3A7-month-reconciled/spec.md` §4; D-3A7.4, D-3A7.5, D-3A7.12, D-3A6.12): one closed month reconciled.

- `commercial_accounts_statement`: one row per closed month's totals the finance lead records from the operator's
  management accounts, for one Site or (`site_id` NULL) the organisation. `result_at_record` and
  `tolerance_at_record` keep what the finance lead saw when recording; the standing never reads them back (D-3A7.3).
- `commercial_reconciliation_tolerance`: the owner's tolerance for one tenant, citing an owner file by path and
  SHA-256 (D-3A7.12). The latest row at an instant applies; with none, 1 in 100 (RC8).
- No column defaults: every value and time comes from the service. The 0005 `ledger_append_only()` trigger refuses
  UPDATE and DELETE on both.

Revision ID: 0069_commercial_reconciliation
Revises: 0068_structure_finding
Create Date: 2026-11-21
"""
from alembic import op

revision = "0069_commercial_reconciliation"
down_revision = "0068_structure_finding"
branch_labels = None
depends_on = None

TABLES = ("commercial_accounts_statement", "commercial_reconciliation_tolerance")

UPGRADE = r"""
CREATE TABLE commercial_accounts_statement (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NULL,
    period text NOT NULL CHECK (period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    revenue text NOT NULL CHECK (revenue ~ '^(0|[1-9][0-9]{0,11})\.[0-9]{2}$'),
    fuel_cost text NOT NULL CHECK (fuel_cost ~ '^(0|[1-9][0-9]{0,11})\.[0-9]{2}$'),
    source_ref text NOT NULL CHECK (char_length(source_ref) BETWEEN 1 AND 200 AND source_ref = btrim(source_ref)),
    recorded_at timestamptz NOT NULL,
    recorded_by uuid NOT NULL,
    recorded_role text NOT NULL CHECK (recorded_role = 'FINANCE_AND_COMMERCIAL_LEAD'),
    recorded_by_script boolean NOT NULL,
    result_at_record text NOT NULL CHECK (result_at_record IN ('MATCHED', 'NOT_MATCHED', 'NOT_COMPARABLE')),
    tolerance_at_record text NOT NULL CHECK (tolerance_at_record ~ '^0\.[0-9]{1,4}$'),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id)
);
CREATE INDEX commercial_accounts_statement_tenant ON commercial_accounts_statement (tenant_id, period, recorded_at);
CREATE TRIGGER commercial_accounts_statement_immutable BEFORE UPDATE OR DELETE ON commercial_accounts_statement
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE TABLE commercial_reconciliation_tolerance (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    tolerance text NOT NULL CHECK (CASE WHEN tolerance ~ '^0\.[0-9]{1,4}$'
                                        THEN tolerance::numeric > 0 AND tolerance::numeric <= 0.05
                                        ELSE false END),
    owner_ref text NOT NULL CHECK (owner_ref ~ '^owner/owner-[a-z0-9-]+\.md$'),
    owner_ref_sha256 text NOT NULL CHECK (owner_ref_sha256 ~ '^[0-9a-f]{64}$'),
    set_at timestamptz NOT NULL
);
CREATE TRIGGER commercial_reconciliation_tolerance_immutable BEFORE UPDATE OR DELETE
    ON commercial_reconciliation_tolerance FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

#: 0065's form: refuse while any statement or tolerance exists.
REFUSE_IF_USED = (
    "LOCK TABLE commercial_accounts_statement, commercial_reconciliation_tolerance IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM commercial_accounts_statement)\n"
    "       OR EXISTS (SELECT 1 FROM commercial_reconciliation_tolerance) THEN\n"
    "        RAISE EXCEPTION 'Downgrade refused: management accounts statements or tolerances exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

#: Reverse order. 0005's `ledger_append_only()` is never dropped.
DOWNGRADE = """
DROP TRIGGER commercial_reconciliation_tolerance_immutable ON commercial_reconciliation_tolerance;
DROP TABLE commercial_reconciliation_tolerance;
DROP TRIGGER commercial_accounts_statement_immutable ON commercial_accounts_statement;
DROP INDEX commercial_accounts_statement_tenant;
DROP TABLE commercial_accounts_statement;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
