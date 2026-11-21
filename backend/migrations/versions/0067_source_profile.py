"""3A6 (`specs/3A6-source-profiles/spec.md` §5; D-3A6.2, D-3A6.8, D-3A6.12): admitted source profiles.

- `commercial_source_profile`: one row per admitted version of a tenant's source profile. It keeps the profile file
  (`profile_json`, checked against `profile_sha256` on every read), the SHA-256 of the sample and of the hand-written
  expected records, and the sample's row count: never a cell of the sample (RC4).
- No column defaults: every value and time comes from the admitting service. The 0005 `ledger_append_only()` trigger
  refuses UPDATE and DELETE. The three unique keys are named, so a refused insert names its key.

Revision ID: 0067_source_profile
Revises: 0066_structure_snapshot
Create Date: 2026-11-21
"""
from alembic import op

revision = "0067_source_profile"
down_revision = "0066_structure_snapshot"
branch_labels = None
depends_on = None

TABLES = ("commercial_source_profile",)

UPGRADE = r"""
CREATE TABLE commercial_source_profile (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    profile_id text NOT NULL CHECK (profile_id ~ '^[a-z][a-z0-9-]{0,47}$'),
    version int NOT NULL CHECK (version BETWEEN 1 AND 9999),
    reader text NOT NULL CHECK (reader = 'profile.' || profile_id || '.v' || version::text),
    status text NOT NULL CHECK (status IN ('ILLUSTRATIVE', 'PINNED')),
    source_type text NOT NULL CHECK (source_type ~ '^[a-z][a-z_]{0,39}$'),
    source_system text NOT NULL CHECK (source_system ~ '^[a-z0-9][a-z0-9.-]{0,79}$'
                                       AND source_system NOT LIKE 'illustrative-%'),
    file_format text NOT NULL CHECK (file_format IN ('csv', 'xlsx')),
    profile_json text NOT NULL CHECK (octet_length(profile_json) BETWEEN 2 AND 65536),
    profile_sha256 text NOT NULL CHECK (profile_sha256 ~ '^[0-9a-f]{64}$'),
    sample_sha256 text NOT NULL CHECK (sample_sha256 ~ '^[0-9a-f]{64}$'),
    expected_sha256 text NOT NULL CHECK (expected_sha256 ~ '^[0-9a-f]{64}$'),
    sample_rows int NOT NULL CHECK (sample_rows BETWEEN 3 AND 200),
    admitted_at timestamptz NOT NULL,
    admitted_by uuid NOT NULL,
    admitted_role text NOT NULL CHECK (admitted_role IN ('ANALYST', 'FINANCE_AND_COMMERCIAL_LEAD')),
    CONSTRAINT commercial_source_profile_version_key UNIQUE (tenant_id, profile_id, version),
    CONSTRAINT commercial_source_profile_reader_key UNIQUE (tenant_id, reader),
    CONSTRAINT commercial_source_profile_sha256_key UNIQUE (tenant_id, profile_id, profile_sha256)
);
CREATE TRIGGER commercial_source_profile_immutable BEFORE UPDATE OR DELETE ON commercial_source_profile
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

#: 0065's form: refuse while any admitted profile exists.
REFUSE_IF_USED = (
    "LOCK TABLE commercial_source_profile IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM commercial_source_profile) THEN\n"
    "        RAISE EXCEPTION 'Downgrade refused: admitted source profiles exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

#: Reverse order. 0005's `ledger_append_only()` is never dropped.
DOWNGRADE = """
DROP TRIGGER commercial_source_profile_immutable ON commercial_source_profile;
DROP TABLE commercial_source_profile;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
