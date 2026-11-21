"""3C2 (`specs/3C2-agreed-change-action/spec.md` §2.1; D-3C2.1, D-3C2.3, D-3C2.7, D-3C2.9, D-3C2.13): the change
agreed at the end of the deep-dive, recorded by people as an Action with its owner and due date.

- `agreed_action`: one row per agreed change, kept as written. Its own table, apart from the S6-01a finding Actions.
- No column defaults: the adapter writes every column. The 0005 `ledger_append_only()` trigger refuses UPDATE and
  DELETE, and a statement trigger refuses TRUNCATE (0050's precedent). `agreed_action_once` is the identity of a
  re-run (NULLS NOT DISTINCT for the Site and the factor).

Numbering (D-3C2.9, renumbered 2026-11-21 at the merge of main `e5a283228`): main ends at `0068_structure_finding`;
`0069` is taken by 3A7 (`0069_commercial_reconciliation`), which merges first. Until then this file revises
`0068_structure_finding`; at 3A7's merge it revises `0069_commercial_reconciliation` (or the live head then), and
test 6's hand pair moves with it.

Revision ID: 0070_agreed_action
Revises: 0068_structure_finding
Create Date: 2026-11-21
"""
from alembic import op

revision = "0070_agreed_action"
down_revision = "0068_structure_finding"
branch_labels = None
depends_on = None

TABLES = ("agreed_action",)

UPGRADE = r"""
CREATE TABLE agreed_action (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200 AND title = btrim(title)),
    site_id uuid NULL,
    factor_id text NULL CHECK (factor_id IS NULL OR factor_id ~ '^[a-z][a-z0-9_]{0,63}$'),
    owner_person_id uuid NOT NULL,
    created_by_person_id uuid NOT NULL,
    created_role text NOT NULL CHECK (created_role = 'OPERATOR_EXECUTIVE'),
    created_by_script boolean NOT NULL,
    created_at timestamptz NOT NULL
        CHECK (date_trunc('second', created_at AT TIME ZONE 'UTC') = created_at AT TIME ZONE 'UTC'),
    due_on date NOT NULL,
    origin text NOT NULL CHECK (origin = 'DEEP_DIVE'),
    FOREIGN KEY (tenant_id, owner_person_id) REFERENCES operator_account (tenant_id, id),
    FOREIGN KEY (tenant_id, created_by_person_id) REFERENCES operator_account (tenant_id, id),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK (factor_id IS NULL OR site_id IS NOT NULL),
    CHECK (due_on >= (created_at AT TIME ZONE 'UTC')::date)
);
CREATE UNIQUE INDEX agreed_action_once ON agreed_action
    (tenant_id, created_by_person_id, owner_person_id, title, due_on, site_id, factor_id) NULLS NOT DISTINCT;
CREATE INDEX agreed_action_tenant ON agreed_action (tenant_id, created_at DESC, id DESC);
CREATE TRIGGER agreed_action_immutable BEFORE UPDATE OR DELETE ON agreed_action
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER agreed_action_no_truncate BEFORE TRUNCATE ON agreed_action
    FOR EACH STATEMENT EXECUTE FUNCTION ledger_append_only();
"""

REFUSE_IF_USED = (
    "LOCK TABLE agreed_action IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM agreed_action) THEN\n"
    "        RAISE EXCEPTION 'Downgrade of 0070_agreed_action refused: agreed Actions exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

#: Reverse order. 0005's `ledger_append_only()` is never dropped.
DOWNGRADE = """
DROP TRIGGER agreed_action_no_truncate ON agreed_action;
DROP TRIGGER agreed_action_immutable ON agreed_action;
DROP INDEX agreed_action_tenant;
DROP INDEX agreed_action_once;
DROP TABLE agreed_action;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
