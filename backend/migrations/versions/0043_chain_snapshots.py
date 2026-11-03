"""CH-1a: graded Site-local day snapshots per measure (build sheet CH-1a §1; design §4.3, §4.3b).

- `site_day_snapshot`: one append-only row per (Site, Site-local day, subject, measure, revision) carrying coverage
  (required/covered seconds, coverage_pct), the grade (COMPLETE/PARTIAL/LOW/NO_DATA/NOT_EXPECTED/PENDING), the value
  and money (jsonb), the evidence class (AG-9), the declared policy, calendar and catalogue versions and the input
  fingerprint. A changed input appends a new revision; an unchanged fingerprint writes nothing.
- Composite FK to `site (tenant_id, id)`; CHECKs tie `expected` to NOT_EXPECTED, NO_DATA to zero coverage, and money to
  a value.
- `site_day_snapshot_read` serves the latest-revision read; `accepted_evidence_site_role_time` serves the per-role
  input read (design §11b P-6: no role index existed).
- The `ledger_append_only()` trigger (0005) refuses UPDATE and DELETE.

Downgrade refuses while any snapshot row exists, then drops the trigger, both indexes and the table.

The `down_revision` follows merge order (Architect ruling: migration split for two lanes): 0041 while CH-2's
0042_chain_threads is not on main; whichever of 0042/0043 merges second points at the first.

Revision ID: 0043_chain_snapshots
Revises: 0041_walk1_objective_min_days
Create Date: 2026-11-03
"""
from alembic import op

revision = "0043_chain_snapshots"
down_revision = "0041_walk1_objective_min_days"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE site_day_snapshot (
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    local_day date NOT NULL,
    subject_kind text NOT NULL DEFAULT 'SITE' CHECK (subject_kind IN ('SITE','ASSET','CONNECTION','CUSTOMER')),
    subject_ref text NOT NULL DEFAULT 'SITE',
    measure text NOT NULL CHECK (measure ~ '^[a-z][a-z0-9_]{1,62}$'),
    evidence_class text NOT NULL CHECK (evidence_class IN ('MEASURED','RECORDED','DECLARED','MODELLED','EXTERNAL')),
    revision int NOT NULL CHECK (revision >= 1),
    expected boolean NOT NULL,
    required_seconds int NOT NULL CHECK (required_seconds >= 0),
    covered_seconds int NOT NULL CHECK (covered_seconds >= 0),
    coverage_pct numeric(5,2) NOT NULL CHECK (coverage_pct BETWEEN 0 AND 100),
    grade text NOT NULL CHECK (grade IN ('COMPLETE','PARTIAL','LOW','NO_DATA','NOT_EXPECTED','PENDING')),
    value jsonb NULL,
    money jsonb NULL,
    policy_version text NOT NULL,
    calendar_version text NOT NULL,
    catalogue_version int NOT NULL,
    input_fp text NOT NULL CHECK (input_fp ~ '^[0-9a-f]{64}$'),
    computed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (tenant_id, site_id, local_day, subject_kind, subject_ref, measure, revision),
    UNIQUE (tenant_id, site_id, local_day, subject_kind, subject_ref, measure, input_fp),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK (NOT expected = (grade = 'NOT_EXPECTED')),
    CHECK (grade <> 'NO_DATA' OR covered_seconds = 0),
    CHECK ((money IS NULL) OR (value IS NOT NULL))
);
CREATE INDEX site_day_snapshot_read
    ON site_day_snapshot (tenant_id, site_id, measure, local_day, subject_kind, subject_ref, revision DESC);
CREATE INDEX accepted_evidence_site_role_time
    ON accepted_evidence (site_id, role, source_time);
CREATE TRIGGER site_day_snapshot_immutable BEFORE UPDATE OR DELETE ON site_day_snapshot
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

REFUSE_IF_USED = (
    "LOCK TABLE site_day_snapshot IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF EXISTS (SELECT 1 FROM site_day_snapshot) THEN\n"
    "        RAISE EXCEPTION 'Downgrade of 0043_chain_snapshots refused: snapshot history exists';\n"
    "    END IF;\nEND;\n$$;\n"
)

DOWNGRADE = """
DROP TRIGGER site_day_snapshot_immutable ON site_day_snapshot;
DROP INDEX accepted_evidence_site_role_time;
DROP INDEX site_day_snapshot_read;
DROP TABLE site_day_snapshot;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
