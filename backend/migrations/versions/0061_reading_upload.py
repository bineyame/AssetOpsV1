"""UP-1 (rev 7 section 7.5, D-17N.5): one row per confirmed reading upload of a Site.

- `reading_upload`: written once, after the whole file was checked and (unless refused) sent through the demo upload
  gateway. `state` is what the API knew when it wrote the row: SENT (every reading admitted or already admitted),
  HELD (some readings held at the gateway, `held_count` > 0) or REFUSED (`refusal_code`, nothing admitted). The later
  states (Accepted n of m, Still processing, Analysed) are read from the ledger at GET, never stored.
- `message_ids` are the gateway's message IDs of the admitted readings, so "Accepted n of m" counts the Site's
  `accepted_evidence` rows by message ID. `period_start`/`period_end` bound the file's intervals.
- `entered_by` is the server-configured entry service (`service:operator-entry`, D-PRICE.1 precedent), labelled
  "Uploaded by site admin"; the browser never names an actor. A dry run writes no row.
- The `ledger_append_only()` trigger (0005) refuses UPDATE and DELETE.

Numbering: 0060 is PR-3's `0060_site_admin_price_entry`. Until PR-3 merges, this revision follows 0059 so the branch
migrates on its own; when PR-3 is on main, `down_revision` is repointed to `0060_site_admin_price_entry` at merge.

Revision ID: 0061_reading_upload
Revises: 0059_site_period_read
Create Date: 2026-11-12
"""
from alembic import op

revision = "0061_reading_upload"
down_revision = "0059_site_period_read"
branch_labels = None
depends_on = None

TABLES = ("reading_upload",)

UPGRADE = """
CREATE TABLE reading_upload (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    file_name text NOT NULL CHECK (char_length(file_name) BETWEEN 1 AND 255),
    file_sha256 text NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    profile_sha256 text NOT NULL CHECK (profile_sha256 ~ '^[0-9a-f]{64}$'),
    state text NOT NULL CHECK (state IN ('SENT', 'HELD', 'REFUSED')),
    refusal_code text NULL CHECK (refusal_code ~ '^[A-Z][A-Z_]{0,39}$'),
    refusal_field text NULL,
    refusal_detail text NULL,
    period_start timestamptz NULL,
    period_end timestamptz NULL,
    row_count int NOT NULL DEFAULT 0 CHECK (row_count >= 0),
    reading_count int NOT NULL DEFAULT 0 CHECK (reading_count >= 0),
    blank_count int NOT NULL DEFAULT 0 CHECK (blank_count >= 0),
    admitted_count int NOT NULL DEFAULT 0 CHECK (admitted_count >= 0),
    held_count int NOT NULL DEFAULT 0 CHECK (held_count >= 0),
    message_ids text[] NOT NULL DEFAULT '{}',
    session_ref text NULL,
    entered_by text NOT NULL CHECK (entered_by <> ''),
    entered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK ((state = 'REFUSED') = (refusal_code IS NOT NULL)),
    CHECK ((state = 'HELD') = (held_count > 0)),
    CHECK (state = 'REFUSED' OR (period_start IS NOT NULL AND period_end > period_start)),
    CHECK (state <> 'REFUSED' OR (admitted_count = 0 AND held_count = 0 AND cardinality(message_ids) = 0))
);
CREATE INDEX reading_upload_site ON reading_upload (tenant_id, site_id, entered_at DESC);
CREATE TRIGGER reading_upload_immutable BEFORE UPDATE OR DELETE ON reading_upload
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

REFUSE_IF_USED = (
    "LOCK TABLE reading_upload IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM reading_upload) THEN\n"
    "        RAISE EXCEPTION 'Downgrade of 0061_reading_upload refused: reading uploads exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

DOWNGRADE = """
DROP TRIGGER reading_upload_immutable ON reading_upload;
DROP INDEX reading_upload_site;
DROP TABLE reading_upload;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
