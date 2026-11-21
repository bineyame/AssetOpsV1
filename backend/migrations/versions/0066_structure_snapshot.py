"""3B7a (`specs/3B7a-structure-snapshot/spec.md` §4.1; D-3B7A.1, D-3B7A.9, D-3B7A.11, D-3B7A.12): the structure snapshot.

- `structure_snapshot`: one row per Site-month build (`site_id` set) and one per portfolio build (`site_id` NULL,
  `site_snapshot_ids` naming its Site rows). Each row freezes the payload (canonical JSON, `payload_sha256` checked on
  every decode), the instant it was built at (`as_of`), the 3A4 month stamps it rests on, the code digest that built it
  and, on a Site row, the record kinds the Site held.
- No column defaults: every value and time comes from the builder. The 0005 `ledger_append_only()` trigger refuses
  UPDATE and DELETE; partial unique indexes allow one row per scope and instant. Not in the chain change log.

Numbering: renumbered at merge preparation if another migration lands first; tests read the head and `down_revision`
from the migration modules.

Revision ID: 0066_structure_snapshot
Revises: 0065_commercial_upload
Create Date: 2026-11-20
"""
from alembic import op

revision = "0066_structure_snapshot"
down_revision = "0065_commercial_upload"
branch_labels = None
depends_on = None

TABLES = ("structure_snapshot",)

UPGRADE = r"""
CREATE TABLE structure_snapshot (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NULL,                                        -- NULL: the portfolio row
    period text NOT NULL CHECK (period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    rules_digest text NOT NULL CHECK (rules_digest ~ '^[0-9a-f]{64}$'),
    held_kinds text[] NOT NULL,                               -- '{}' on the portfolio row
    structure_key text NOT NULL CHECK (structure_key ~ '^[A-Z][A-Z_]{0,39}$'),
    structure_version int NOT NULL CHECK (structure_version >= 1),
    format int NOT NULL CHECK (format >= 1),
    as_of timestamptz NOT NULL,
    built_by text NOT NULL CHECK (built_by ~ '^(person:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|service:[a-z][a-z0-9._-]{0,63})$'),
    closed_at_build boolean NOT NULL,
    stamps text NOT NULL,                                     -- canonical JSON array of STAMP
    payload text NOT NULL,
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    site_snapshot_ids uuid[] NULL,
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK ((site_id IS NULL) = (site_snapshot_ids IS NOT NULL)),
    UNIQUE (tenant_id, id)
);
CREATE UNIQUE INDEX structure_snapshot_site_at ON structure_snapshot (tenant_id, site_id, period, as_of)
    WHERE site_id IS NOT NULL;
CREATE UNIQUE INDEX structure_snapshot_portfolio_at ON structure_snapshot (tenant_id, period, as_of)
    WHERE site_id IS NULL;
CREATE TRIGGER structure_snapshot_immutable BEFORE UPDATE OR DELETE ON structure_snapshot
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

#: 0065's form: refuse while any snapshot exists.
REFUSE_IF_USED = (
    "LOCK TABLE structure_snapshot IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM structure_snapshot) THEN\n"
    "        RAISE EXCEPTION 'Downgrade refused: structure snapshots exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

#: Reverse order. 0005's `ledger_append_only()` is never dropped.
DOWNGRADE = """
DROP TRIGGER structure_snapshot_immutable ON structure_snapshot;
DROP INDEX structure_snapshot_portfolio_at;
DROP INDEX structure_snapshot_site_at;
DROP TABLE structure_snapshot;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
