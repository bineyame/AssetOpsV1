"""3A1 (spec `specs/3A1-commercial-record-store/spec.md` §2; D-3A1.1 to D-3A1.12): the commercial record store.

- `commercial_intake`: one row per call of `CommercialRecords.ingest`, STORED (processed, its account kept; never
  "accepted", R17) or REFUSED (an envelope or tenant refusal, all counts 0). `batch_sha256` is the SHA-256 of the
  bytes as received; the bytes are never stored (R1). The envelope columns are NULL only on a REFUSED row whose
  envelope did not parse that far.
- `commercial_record`: one row per (tenant, source system, source record ID); its kind and Site never change
  (D-3A1.2).
- `commercial_record_revision`: one row per source version of a record (D-3A1.3); revision n > 1 supersedes the
  previous latest revision of the same record (composite foreign keys, R11). `provenance` is the batch's declared
  one (D-3A1.9). `amount` and `quantity` are unbounded `numeric` (R3).
- `commercial_rejection`: one row per refused record of a STORED intake (D-3A1.4).
- No column defaults: the adapter writes every value and every time from the service clock. The 0005
  `ledger_append_only()` trigger refuses UPDATE and DELETE on all four tables. The tables do not join the chain
  change log (D-3A1.6).

Numbering (D-3A1.12): the first of 3A1 and 3C1a to merge takes 0063 on 0062; the second is renumbered on top of it at
merge preparation. Tests read the head and `down_revision` from the migration modules, never a literal name.

Revision ID: 0063_commercial_records
Revises: 0062_operator_accounts
Create Date: 2026-11-20
"""
from alembic import op

revision = "0063_commercial_records"
down_revision = "0062_operator_accounts"
branch_labels = None
depends_on = None

TABLES = ("commercial_intake", "commercial_record", "commercial_record_revision", "commercial_rejection")

UPGRADE = r"""
CREATE TABLE commercial_intake (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    source_type text NULL CHECK (source_type ~ '^[a-z][a-z_]{0,39}$'),
    source_system text NULL CHECK (char_length(source_system) BETWEEN 1 AND 200),
    provenance text NULL CHECK (provenance IN ('demo-simulated', 'source-emulated', 'bench-tested',
                                               'field-integrated', 'observed-financial')),
    produced_at timestamptz NULL,
    batch_sha256 text NOT NULL CHECK (batch_sha256 ~ '^[0-9a-f]{64}$'),   -- SHA-256 of the bytes as received (R1)
    state text NOT NULL CHECK (state IN ('STORED', 'REFUSED')),
    refusal_code text NULL CHECK (refusal_code ~ '^[A-Z][A-Z_]{0,39}$'),
    refusal_path text NULL CHECK (refusal_path IS NULL OR char_length(refusal_path) <= 300),
    record_count int NOT NULL CHECK (record_count >= 0),
    new_count int NOT NULL CHECK (new_count >= 0),
    revised_count int NOT NULL CHECK (revised_count >= 0),
    unchanged_count int NOT NULL CHECK (unchanged_count >= 0),
    refused_count int NOT NULL CHECK (refused_count >= 0),
    entered_by text NOT NULL CHECK (entered_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'),
    entered_at timestamptz NOT NULL,
    CHECK ((state = 'REFUSED') = (refusal_code IS NOT NULL)),
    CHECK (state = 'REFUSED' OR (source_type IS NOT NULL AND source_system IS NOT NULL AND provenance IS NOT NULL
                                AND produced_at IS NOT NULL)),
    CHECK (new_count + revised_count + unchanged_count + refused_count = record_count),
    UNIQUE (tenant_id, id)
);
CREATE INDEX commercial_intake_tenant_at ON commercial_intake (tenant_id, entered_at DESC);
CREATE TABLE commercial_record (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NULL,
    kind text NOT NULL CHECK (kind IN ('CHARGE', 'RECEIPT', 'SETTLEMENT', 'ADJUSTMENT', 'EXPENSE', 'BUDGET_LINE',
        'STORAGE_MOVEMENT', 'CUSTOMER_METER_READ', 'METER_ASSIGNMENT', 'FLEET_ROSTER', 'DEPARTURE',
        'TARIFF_SCHEDULE', 'CONTRACT_DOCUMENT')),
    source_system text NOT NULL CHECK (char_length(source_system) BETWEEN 1 AND 200),
    source_record_id text NOT NULL CHECK (char_length(source_record_id) BETWEEN 1 AND 200),
    first_recorded_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK (site_id IS NOT NULL OR kind IN ('BUDGET_LINE', 'CONTRACT_DOCUMENT')),
    UNIQUE (tenant_id, source_system, source_record_id),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, id, kind)
);
CREATE TABLE commercial_record_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    record_id uuid NOT NULL,
    site_id uuid NULL,
    kind text NOT NULL,
    revision_no int NOT NULL CHECK (revision_no >= 1),
    source_version text NOT NULL CHECK (char_length(source_version) BETWEEN 1 AND 64),
    intake_id uuid NOT NULL,
    record_sha256 text NOT NULL CHECK (record_sha256 ~ '^[0-9a-f]{64}$'),
    canonical text NOT NULL,
    provenance text NOT NULL CHECK (provenance IN ('demo-simulated', 'source-emulated', 'bench-tested',
                                                   'field-integrated', 'observed-financial')),
    recognition_period text NULL CHECK (recognition_period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    occurred_at timestamptz NULL,
    settled_at timestamptz NULL,
    effective_from date NULL,
    effective_to date NULL,
    amount numeric NULL,
    currency text NULL CHECK (currency ~ '^[A-Z]{3}$'),
    quantity numeric NULL,
    unit text NULL CHECK (unit IN ('kWh', 'kW', 'L', 'crate', 'crate_day')),
    status text NULL CHECK (status ~ '^[A-Z][A-Z_]{0,39}$'),
    supersedes_revision_id uuid NULL,
    recorded_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, record_id, kind) REFERENCES commercial_record (tenant_id, id, kind),
    FOREIGN KEY (record_id, supersedes_revision_id) REFERENCES commercial_record_revision (record_id, id),
    FOREIGN KEY (tenant_id, intake_id) REFERENCES commercial_intake (tenant_id, id),
    CHECK ((amount IS NULL) = (currency IS NULL)),
    CHECK ((quantity IS NULL) = (unit IS NULL)),
    CHECK ((revision_no = 1) = (supersedes_revision_id IS NULL)),
    CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from),
    UNIQUE (record_id, source_version),
    UNIQUE (record_id, revision_no),
    UNIQUE (record_id, id)
);
CREATE INDEX commercial_revision_read ON commercial_record_revision
    (tenant_id, site_id, kind, recognition_period, record_id, revision_no DESC);
CREATE TABLE commercial_rejection (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    intake_id uuid NOT NULL,
    record_index int NOT NULL CHECK (record_index >= 0),
    source_record_id text NULL CHECK (source_record_id IS NULL OR char_length(source_record_id) BETWEEN 1 AND 200),
    code text NOT NULL CHECK (code ~ '^[A-Z][A-Z_]{0,39}$'),
    path text NOT NULL CHECK (char_length(path) BETWEEN 1 AND 300),
    recorded_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, intake_id) REFERENCES commercial_intake (tenant_id, id),
    UNIQUE (intake_id, record_index)
);
CREATE TRIGGER commercial_intake_immutable BEFORE UPDATE OR DELETE ON commercial_intake
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER commercial_record_immutable BEFORE UPDATE OR DELETE ON commercial_record
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER commercial_record_revision_immutable BEFORE UPDATE OR DELETE ON commercial_record_revision
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER commercial_rejection_immutable BEFORE UPDATE OR DELETE ON commercial_rejection
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

REFUSE_IF_USED = (
    "LOCK TABLE " + ", ".join(TABLES) + " IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM commercial_intake) OR EXISTS (SELECT 1 FROM commercial_record)\n"
    "            OR EXISTS (SELECT 1 FROM commercial_record_revision) OR EXISTS (SELECT 1 FROM commercial_rejection) THEN\n"
    "        RAISE EXCEPTION 'Downgrade refused: commercial records exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

#: Reverse order. 0005's `ledger_append_only()` is never dropped.
DOWNGRADE = """
DROP TRIGGER commercial_rejection_immutable ON commercial_rejection;
DROP TABLE commercial_rejection;
DROP TRIGGER commercial_record_revision_immutable ON commercial_record_revision;
DROP INDEX commercial_revision_read;
DROP TABLE commercial_record_revision;
DROP TRIGGER commercial_record_immutable ON commercial_record;
DROP TABLE commercial_record;
DROP TRIGGER commercial_intake_immutable ON commercial_intake;
DROP INDEX commercial_intake_tenant_at;
DROP TABLE commercial_intake;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
