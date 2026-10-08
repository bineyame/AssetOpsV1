"""S1-02 pinned acquisition snapshots on Foundation-aligned binding periods.

Decision `D-2026-10-08-s1-bindings-roles-and-snapshot` (Q5, Q6):

* every binding set revision names the one Foundation revision whose valid
  period contains its own (`foundation_revision_id`, same-Site composite FK);
  on insert that Foundation revision must be currently recorded and must
  contain the binding period;
* the publishing transaction persists the snapshot serializer version
  (`snapshot_schema`), the combined SHA-256 of the canonical bytes
  (`snapshot_sha256`) and the gateway the snapshot is for (`gateway_id`,
  same-Site composite FK). All are immutable.

The new columns are NOT NULL. Binding sets published under 0002 alone have no
pinned snapshot and cannot be backfilled honestly, so this migration refuses
to run over them rather than inventing a hash.

Revision ID: 0003_pinned_binding_snapshots
Revises: 0002_signal_bindings
Create Date: 2026-10-08
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0003_pinned_binding_snapshots"
down_revision = "0002_signal_bindings"
branch_labels = None
depends_on = None


SCHEMA = r"""
ALTER TABLE signal_binding_set_revision
    ADD COLUMN foundation_revision_id uuid NOT NULL,
    ADD COLUMN gateway_id uuid NOT NULL,
    ADD COLUMN snapshot_schema text NOT NULL,
    ADD COLUMN snapshot_sha256 text NOT NULL CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    ADD CONSTRAINT binding_set_foundation_same_site FOREIGN KEY (tenant_id, site_id, foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    ADD CONSTRAINT binding_set_gateway_same_site FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id);

-- A binding set revision is published inside one current Foundation period.
CREATE FUNCTION binding_set_within_foundation() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    anchor foundation_revision%ROWTYPE;
BEGIN
    SELECT * INTO anchor FROM foundation_revision
        WHERE tenant_id = NEW.tenant_id AND site_id = NEW.site_id AND id = NEW.foundation_revision_id;
    IF anchor.id IS NULL OR anchor.superseded_at IS NOT NULL THEN
        RAISE EXCEPTION 'a binding set revision must name a currently recorded Foundation revision of its Site';
    END IF;
    IF NEW.valid_from < anchor.valid_from
       OR (anchor.valid_to IS NOT NULL AND (NEW.valid_to IS NULL OR NEW.valid_to > anchor.valid_to)) THEN
        RAISE EXCEPTION 'a binding set revision must lie within its Foundation revision''s valid period';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER binding_set_within_foundation
    BEFORE INSERT ON signal_binding_set_revision
    FOR EACH ROW EXECUTE FUNCTION binding_set_within_foundation();

-- Immutability now covers the pinned snapshot and its references.
CREATE OR REPLACE FUNCTION binding_set_revision_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'signal_binding_set_revision rows are append-only; DELETE refused';
    END IF;
    IF (to_jsonb(NEW) - 'superseded_at') IS DISTINCT FROM (to_jsonb(OLD) - 'superseded_at') THEN
        RAISE EXCEPTION 'signal_binding_set_revision content, identity, validity and snapshot are immutable';
    END IF;
    IF OLD.superseded_at IS NOT NULL AND NEW.superseded_at IS DISTINCT FROM OLD.superseded_at THEN
        RAISE EXCEPTION 'signal_binding_set_revision recorded interval is already closed';
    END IF;
    RETURN NEW;
END;
$$;
"""


def upgrade() -> None:
    existing = op.get_bind().execute(text("SELECT count(*) FROM signal_binding_set_revision")).scalar_one()
    if existing:
        raise RuntimeError(
            f"Migration 0003 found {existing} binding set revision(s) published without a pinned "
            "snapshot. Their snapshot hash cannot be backfilled honestly; this only happens on a "
            "scratch database used during S1-02 development - recreate it and rerun the conversion."
        )
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS binding_set_within_foundation ON signal_binding_set_revision;
        DROP FUNCTION IF EXISTS binding_set_within_foundation();
        ALTER TABLE signal_binding_set_revision
            DROP CONSTRAINT IF EXISTS binding_set_foundation_same_site,
            DROP CONSTRAINT IF EXISTS binding_set_gateway_same_site,
            DROP COLUMN IF EXISTS foundation_revision_id,
            DROP COLUMN IF EXISTS gateway_id,
            DROP COLUMN IF EXISTS snapshot_schema,
            DROP COLUMN IF EXISTS snapshot_sha256;
        """
    )
