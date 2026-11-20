"""3A2 (`specs/3A2-commercial-file-intake/spec.md` §2; D-3A2.4, D-3A2.10, D-3A2.12 to D-3A2.15): commercial uploads.

- `commercial_upload`: one row per submitted operator export (state WAITING until a decision exists). It keeps the
  file's name, SHA-256 and size, never its bytes (D-3A2.10); `batch` is the envelope plus the records 2a accepted,
  pseudonymised (D-3A2.14), and `kept_index` maps each kept record to its file index. `basis_sha256` is the store state
  the check decided against (D-3A2.13). The refusal arrays are the only account of a dropped record.
- `commercial_upload_decision`: at most one ACCEPTED or DECLINED decision per upload. An ACCEPTED decision names the
  intake written in the same transaction (D-3A2.4).
- No column defaults: every value and time comes from the service clock. The 0005 `ledger_append_only()` trigger
  refuses UPDATE and DELETE on both tables. Not in the chain change log (D-3A1.6).

Numbering (D-3A2.11): renumbered at merge preparation if another migration lands first; tests read the head and
`down_revision` from the migration modules.

Revision ID: 0065_commercial_upload
Revises: 0064_person_on_work
Create Date: 2026-11-20
"""
from alembic import op

revision = "0065_commercial_upload"
down_revision = "0064_person_on_work"
branch_labels = None
depends_on = None

TABLES = ("commercial_upload", "commercial_upload_decision")

UPGRADE = r"""
CREATE TABLE commercial_upload (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NULL,                                   -- NULL: the organisation path
    file_name text NOT NULL CHECK (char_length(file_name) BETWEEN 1 AND 200
                                   AND strpos(file_name, '/') = 0 AND strpos(file_name, chr(92)) = 0),
    file_sha256 text NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),   -- of the bytes as received; bytes never kept
    file_bytes int NOT NULL CHECK (file_bytes BETWEEN 0 AND 8388608),
    reader text NOT NULL CHECK (reader ~ '^[a-z][a-z0-9.:@_-]{0,99}$'),
    source_type text NOT NULL CHECK (source_type ~ '^[a-z][a-z_]{0,39}$'),
    source_system text NOT NULL CHECK (char_length(source_system) BETWEEN 1 AND 200),
    provenance text NOT NULL CHECK (provenance IN ('demo-simulated', 'source-emulated', 'bench-tested',
                                                   'field-integrated', 'observed-financial')),
    batch text NOT NULL,                                 -- envelope + the records 2a accepted, pseudonymised (UTF-8 JSON)
    batch_sha256 text NOT NULL CHECK (batch_sha256 ~ '^[0-9a-f]{64}$'),
    kept_index int[] NOT NULL,                           -- file record index of each kept record, ascending
    basis_sha256 text NOT NULL CHECK (basis_sha256 ~ '^[0-9a-f]{64}$'),  -- store state the check decided against
    row_map int[] NULL,                                  -- file row per file record index; NULL: row = index + 1
    record_count int NOT NULL CHECK (record_count >= 0),
    new_count int NOT NULL CHECK (new_count >= 0),
    revised_count int NOT NULL CHECK (revised_count >= 0),
    unchanged_count int NOT NULL CHECK (unchanged_count >= 0),
    refused_count int NOT NULL CHECK (refused_count >= 0),
    refusal_index int[] NOT NULL,
    refusal_code text[] NOT NULL,
    refusal_path text[] NOT NULL,
    month_site_code text[] NOT NULL,                     -- NULL element: portfolio level
    month_period text[] NOT NULL,
    submitted_by uuid NOT NULL,
    submitted_role text NOT NULL CHECK (submitted_role IN ('ANALYST', 'FINANCE_AND_COMMERCIAL_LEAD')),
    submitted_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    FOREIGN KEY (tenant_id, submitted_by) REFERENCES operator_account (tenant_id, id),
    CHECK (new_count + revised_count + unchanged_count + refused_count = record_count),
    CHECK (new_count + revised_count >= 1),
    CHECK (cardinality(refusal_index) = refused_count AND cardinality(refusal_code) = refused_count
           AND cardinality(refusal_path) = refused_count),
    CHECK (cardinality(month_site_code) = cardinality(month_period)),
    CHECK (row_map IS NULL OR cardinality(row_map) = record_count),
    CHECK (cardinality(kept_index) BETWEEN new_count + revised_count + unchanged_count AND record_count),
    UNIQUE (tenant_id, id)
);
CREATE INDEX commercial_upload_tenant_at ON commercial_upload (tenant_id, submitted_at DESC);
CREATE TABLE commercial_upload_decision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    upload_id uuid NOT NULL UNIQUE,
    decision text NOT NULL CHECK (decision IN ('ACCEPTED', 'DECLINED')),
    reason text NULL CHECK (reason IS NULL OR (char_length(reason) BETWEEN 1 AND 500 AND reason = btrim(reason))),
    intake_id uuid NULL,
    decided_by uuid NOT NULL,
    decided_role text NOT NULL CHECK (decided_role IN ('FINANCE_AND_COMMERCIAL_LEAD', 'OPERATOR_EXECUTIVE')),
    decided_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, upload_id) REFERENCES commercial_upload (tenant_id, id),
    FOREIGN KEY (tenant_id, intake_id) REFERENCES commercial_intake (tenant_id, id),
    FOREIGN KEY (tenant_id, decided_by) REFERENCES operator_account (tenant_id, id),
    CHECK ((decision = 'ACCEPTED') = (intake_id IS NOT NULL)),
    CHECK ((decision = 'DECLINED') = (reason IS NOT NULL))
);
CREATE TRIGGER commercial_upload_immutable BEFORE UPDATE OR DELETE ON commercial_upload
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER commercial_upload_decision_immutable BEFORE UPDATE OR DELETE ON commercial_upload_decision
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

REFUSE_IF_USED = (
    "LOCK TABLE " + ", ".join(TABLES) + " IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM commercial_upload) OR EXISTS (SELECT 1 FROM commercial_upload_decision) THEN\n"
    "        RAISE EXCEPTION 'Downgrade refused: commercial uploads exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

#: Reverse order. 0005's `ledger_append_only()` is never dropped.
DOWNGRADE = """
DROP TRIGGER commercial_upload_decision_immutable ON commercial_upload_decision;
DROP TABLE commercial_upload_decision;
DROP TRIGGER commercial_upload_immutable ON commercial_upload;
DROP INDEX commercial_upload_tenant_at;
DROP TABLE commercial_upload;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
