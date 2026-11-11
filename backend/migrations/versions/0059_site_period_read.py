"""ANY-1 AR-1: stored read periods and immutable revision provenance (architect answer 2026-11-10 §4).

- `site_period_read`: a sibling of `site_day_snapshot` (0043) on its rules - one append-only row per (Site, kind,
  period, revision), revisioned by input fingerprint, `computed_at` for "as known at k", `builder_version` so a row of
  an older builder reads as PENDING until the backfill rebuilds it. `kind` is '<area>.<name>' (e.g.
  `mini_depth.renewable`, `dispatch.day`, `money.lines`); `period_start`/`period_end` are the kind's native grain and
  `local_day` its Site-local day (the register's day). `state` is the kind's own code; `body` the exact fragment
  today's compose builds for the period, words as `{key, params}` (D-I18N.1) and money lines with their receipts in
  the original currency (D-MONEY.1-4: no new columns, no totals).
- `revision_provenance`: the provenance block of a selected assessment revision, computed once per builder version.
- `site_period_read_day` serves the one-statement read per Sites x days x kinds; the primary key serves the
  builder's latest-revision lookup per (Site, kind, period).
- The `ledger_append_only()` trigger (0005) refuses UPDATE and DELETE on both tables.

Downgrade refuses while either table holds a row, then drops the triggers, the index and the tables.

Revision ID: 0059_site_period_read
Revises: 0058_fuel_watermark_inputs
Create Date: 2026-11-11
"""
from alembic import op

revision = "0059_site_period_read"
down_revision = "0058_fuel_watermark_inputs"
branch_labels = None
depends_on = None

TABLES = ("site_period_read", "revision_provenance")

UPGRADE = """
CREATE TABLE site_period_read (
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    kind text NOT NULL CHECK (kind ~ '^[a-z][a-z0-9_]{1,40}\\.[a-z][a-z0-9_]{1,40}$'),
    period_start timestamptz NOT NULL,
    period_end timestamptz NOT NULL,
    local_day date NOT NULL,
    revision int NOT NULL CHECK (revision >= 1),
    builder_version text NOT NULL CHECK (builder_version <> ''),
    input_fp text NOT NULL CHECK (input_fp ~ '^[0-9a-f]{64}$'),
    state text NOT NULL CHECK (state ~ '^[A-Z][A-Z_]{0,39}$'),
    body jsonb NOT NULL CHECK (jsonb_typeof(body) = 'object'),
    computed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (tenant_id, site_id, kind, period_start, revision),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK (period_end > period_start)
);
CREATE INDEX site_period_read_day
    ON site_period_read (tenant_id, site_id, kind, local_day, period_start, revision DESC);
CREATE TRIGGER site_period_read_immutable BEFORE UPDATE OR DELETE ON site_period_read
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE TABLE revision_provenance (
    assessment_revision_id uuid NOT NULL,
    builder_version text NOT NULL CHECK (builder_version <> ''),
    tenant_id uuid NOT NULL,
    block jsonb NOT NULL CHECK (jsonb_typeof(block) = 'object'),
    computed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (assessment_revision_id, builder_version)
);
CREATE TRIGGER revision_provenance_immutable BEFORE UPDATE OR DELETE ON revision_provenance
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

REFUSE_IF_USED = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM site_period_read) OR EXISTS (SELECT 1 FROM revision_provenance) THEN\n"
    "        RAISE EXCEPTION 'Downgrade of 0059_site_period_read refused: stored read periods exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

DOWNGRADE = """
DROP TRIGGER revision_provenance_immutable ON revision_provenance;
DROP TABLE revision_provenance;
DROP TRIGGER site_period_read_immutable ON site_period_read;
DROP INDEX site_period_read_day;
DROP TABLE site_period_read;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
