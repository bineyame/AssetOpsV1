"""6h (`specs/6h-named-option-levers/spec.md` §3.4, §6.1; D-P6.51 to D-P6.67): named-option levers.

- `decision_option.generator` admits `STATED_OPTIONS`; `option_evaluation_run.outcome` admits `BOUNDS_NOT_CHECKED`
  (a protective lever: no recommendation until 6b's bounds). The two checks keep 0072's live names
  (`decision_option_generator_check`, `option_evaluation_run_outcome_check`; H4).
- `option_record`: a person states a document's term for a named option's leaf (6h4). Immutable and untruncatable by
  0005's `ledger_append_only()`, as 0072's tables; the newest record per (option, factor) is the one read.
- `downgrade` refuses while a row holds a new value (a `STATED_OPTIONS` option, a `BOUNDS_NOT_CHECKED` run, or any
  option record), then restores both checks and drops `option_record`.

Numbering (spec §2 G1): `main`'s head was `0072_decision_records` at build time.

Revision ID: 0073_named_option_levers
Revises: 0072_decision_records
Create Date: 2026-11-22
"""
from alembic import op

revision = "0073_named_option_levers"
down_revision = "0072_decision_records"
branch_labels = None
depends_on = None

ID_RE = "'^[a-z][a-z0-9_]{0,63}$'"
RECORD_TABLE = "option_record"


def _ws(col: str) -> str:
    """0070's whole-second check."""
    return f"CHECK (date_trunc('second', {col} AT TIME ZONE 'UTC') = {col} AT TIME ZONE 'UTC')"


UPGRADE = f"""
ALTER TABLE decision_option DROP CONSTRAINT decision_option_generator_check;
ALTER TABLE decision_option ADD CONSTRAINT decision_option_generator_check
    CHECK (generator IN ('NO_ACTION', 'SETTING_GRID', 'STATED_OPTIONS'));
ALTER TABLE option_evaluation_run DROP CONSTRAINT option_evaluation_run_outcome_check;
ALTER TABLE option_evaluation_run ADD CONSTRAINT option_evaluation_run_outcome_check
    CHECK (outcome IN ('RECOMMENDED', 'NO_ACTION_BEST', 'RANKING_INCOMPLETE', 'NOTHING_ADMITTED',
                       'BOUNDS_NOT_CHECKED'));

CREATE TABLE option_record (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    option_id uuid NOT NULL,
    factor_id text NOT NULL CHECK (factor_id ~ {ID_RE}),
    value numeric(20, 6) NOT NULL,
    unit text NOT NULL CHECK (char_length(unit) BETWEEN 1 AND 32),
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{{3}}$'),
    origin text NOT NULL CHECK (origin IN ('observed-financial', 'source-emulated')),
    document text NOT NULL CHECK (char_length(document) BETWEEN 1 AND 200 AND document = btrim(document)),
    basis text NOT NULL CHECK (char_length(basis) BETWEEN 1 AND 200 AND basis = btrim(basis)),
    declared_by_person_id uuid NOT NULL,
    declared_role text NOT NULL CHECK (declared_role IN ('SITE_MANAGER', 'FINANCE_AND_COMMERCIAL_LEAD')),
    declared_by_script boolean NOT NULL,
    declared_at timestamptz NOT NULL {_ws('declared_at')},
    CONSTRAINT option_record_tenant_id_unique UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, option_id) REFERENCES decision_option (tenant_id, id),
    FOREIGN KEY (tenant_id, declared_by_person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX option_record_latest ON option_record (tenant_id, option_id, factor_id, declared_at DESC, id DESC);
CREATE TRIGGER option_record_immutable BEFORE UPDATE OR DELETE ON option_record
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER option_record_no_truncate BEFORE TRUNCATE ON option_record
    FOR EACH STATEMENT EXECUTE FUNCTION ledger_append_only();
"""

DOWNGRADE_REFUSED = f"Downgrade of {revision} refused: named-option rows exist"

REFUSE_IF_USED = f"""
LOCK TABLE decision_option IN ACCESS EXCLUSIVE MODE;
LOCK TABLE option_evaluation_run IN ACCESS EXCLUSIVE MODE;
LOCK TABLE option_record IN ACCESS EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM decision_option WHERE generator = 'STATED_OPTIONS')
       OR EXISTS (SELECT 1 FROM option_evaluation_run WHERE outcome = 'BOUNDS_NOT_CHECKED')
       OR EXISTS (SELECT 1 FROM option_record) THEN
        RAISE EXCEPTION '{DOWNGRADE_REFUSED}';
    END IF;
END;
$$;
"""

#: 0005's `ledger_append_only()` is never dropped.
DOWNGRADE = """
DROP TRIGGER option_record_no_truncate ON option_record;
DROP TRIGGER option_record_immutable ON option_record;
DROP INDEX option_record_latest;
DROP TABLE option_record;
ALTER TABLE option_evaluation_run DROP CONSTRAINT option_evaluation_run_outcome_check;
ALTER TABLE option_evaluation_run ADD CONSTRAINT option_evaluation_run_outcome_check
    CHECK (outcome IN ('RECOMMENDED', 'NO_ACTION_BEST', 'RANKING_INCOMPLETE', 'NOTHING_ADMITTED'));
ALTER TABLE decision_option DROP CONSTRAINT decision_option_generator_check;
ALTER TABLE decision_option ADD CONSTRAINT decision_option_generator_check
    CHECK (generator IN ('NO_ACTION', 'SETTING_GRID'));
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
