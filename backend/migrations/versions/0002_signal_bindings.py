"""S1-02 versioned signal bindings.

Installs `signal_binding_set_revision` (one time-valid version of a Site's
binding set) and `signal_binding_revision` (one bound device channel of that
version), per the technical design's `signal_binding_revision` row:

* every reference (site, gateway, source, asset, set revision) is a composite
  same-tenant, same-Site foreign key; a source must belong to the named
  gateway and its external ID must be the bound `device_id`;
* no two currently recorded set revisions of one Site and role set overlap in
  valid time, and no channel `(source, signal)` is bound twice in currently
  recorded valid time (GiST exclusions over `btree_gist`, enabled by 0001);
* rows are append-only: content, identity and validity are immutable and
  `superseded_at` may be set once. Closing a set revision closes its rows in
  the same statement, and a row may only be inserted into a current set
  revision with that revision's identity and periods.

Revision ID: 0002_signal_bindings
Revises: 0001_foundation_identity
Create Date: 2026-10-08
"""

from __future__ import annotations

from alembic import op

revision = "0002_signal_bindings"
down_revision = "0001_foundation_identity"
branch_labels = None
depends_on = None


SCHEMA = r"""
ALTER TABLE source ADD CONSTRAINT source_gateway_scope_unique
    UNIQUE (tenant_id, site_id, gateway_id, id, source_external_id);

CREATE TABLE signal_binding_set_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    binding_set_id uuid NOT NULL,
    version integer NOT NULL CHECK (version >= 1),
    role_set text NOT NULL,
    valid_from timestamptz NOT NULL,
    valid_to timestamptz NULL,
    recorded_at timestamptz NOT NULL,
    superseded_at timestamptz NULL,
    bindings_sha256 text NOT NULL CHECK (bindings_sha256 ~ '^[0-9a-f]{64}$'),
    origin text NOT NULL CHECK (origin IN ('CONVERSION','PUBLISH','SPLIT')),
    derived_from_revision_id uuid NULL,
    change_note text NULL,
    CONSTRAINT binding_set_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT binding_set_site_version_unique UNIQUE (site_id, binding_set_id, version),
    CONSTRAINT binding_set_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT binding_set_valid_range CHECK (valid_to IS NULL OR valid_to > valid_from),
    CONSTRAINT binding_set_recorded_range CHECK (superseded_at IS NULL OR superseded_at >= recorded_at),
    CONSTRAINT binding_set_no_current_overlap EXCLUDE USING gist (
        site_id WITH =,
        role_set WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&
    ) WHERE (superseded_at IS NULL)
);
CREATE INDEX binding_set_site_valid ON signal_binding_set_revision (site_id, valid_from DESC);

CREATE TABLE signal_binding_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    binding_set_revision_id uuid NOT NULL,
    binding_set_id uuid NOT NULL,
    version integer NOT NULL,
    gateway_id uuid NOT NULL,
    source_id uuid NOT NULL,
    device_id text NOT NULL,
    signal_id text NOT NULL,
    asset_id uuid NULL,
    role text NOT NULL,
    source_unit text NOT NULL,
    canonical_unit text NOT NULL,
    conversion jsonb NOT NULL,
    valid_from timestamptz NOT NULL,
    valid_to timestamptz NULL,
    recorded_at timestamptz NOT NULL,
    superseded_at timestamptz NULL,
    CONSTRAINT binding_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT binding_set_same_site FOREIGN KEY (tenant_id, site_id, binding_set_revision_id)
        REFERENCES signal_binding_set_revision(tenant_id, site_id, id),
    CONSTRAINT binding_gateway_same_site FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT binding_source_of_gateway FOREIGN KEY (tenant_id, site_id, gateway_id, source_id, device_id)
        REFERENCES source(tenant_id, site_id, gateway_id, id, source_external_id),
    CONSTRAINT binding_asset_same_site FOREIGN KEY (tenant_id, site_id, asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT binding_set_channel_unique UNIQUE (site_id, binding_set_id, version, device_id, signal_id),
    CONSTRAINT binding_valid_range CHECK (valid_to IS NULL OR valid_to > valid_from),
    CONSTRAINT binding_no_current_channel_overlap EXCLUDE USING gist (
        site_id WITH =,
        source_id WITH =,
        signal_id WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&
    ) WHERE (superseded_at IS NULL)
);
CREATE INDEX binding_site_role_valid ON signal_binding_revision (site_id, role, valid_from);
CREATE INDEX binding_channel_valid ON signal_binding_revision (source_id, device_id, signal_id, valid_from);

-- A binding row joins only a current set revision, with its identity and periods.
CREATE FUNCTION signal_binding_matches_set() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    parent signal_binding_set_revision%ROWTYPE;
BEGIN
    SELECT * INTO parent FROM signal_binding_set_revision
        WHERE tenant_id = NEW.tenant_id AND site_id = NEW.site_id AND id = NEW.binding_set_revision_id;
    IF parent.id IS NULL THEN
        RAISE EXCEPTION 'signal_binding_revision names no binding set revision of this Site';
    END IF;
    IF parent.superseded_at IS NOT NULL OR NEW.superseded_at IS NOT NULL THEN
        RAISE EXCEPTION 'a binding row may only join a currently recorded binding set revision';
    END IF;
    IF NEW.binding_set_id IS DISTINCT FROM parent.binding_set_id
       OR NEW.version IS DISTINCT FROM parent.version
       OR NEW.valid_from IS DISTINCT FROM parent.valid_from
       OR NEW.valid_to IS DISTINCT FROM parent.valid_to
       OR NEW.recorded_at IS DISTINCT FROM parent.recorded_at THEN
        RAISE EXCEPTION 'a binding row must carry its set revision''s identity and periods';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER signal_binding_matches_set
    BEFORE INSERT ON signal_binding_revision
    FOR EACH ROW EXECUTE FUNCTION signal_binding_matches_set();

CREATE FUNCTION binding_set_revision_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'signal_binding_set_revision rows are append-only; DELETE refused';
    END IF;
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.site_id IS DISTINCT FROM OLD.site_id
       OR NEW.binding_set_id IS DISTINCT FROM OLD.binding_set_id
       OR NEW.version IS DISTINCT FROM OLD.version
       OR NEW.role_set IS DISTINCT FROM OLD.role_set
       OR NEW.valid_from IS DISTINCT FROM OLD.valid_from
       OR NEW.valid_to IS DISTINCT FROM OLD.valid_to
       OR NEW.recorded_at IS DISTINCT FROM OLD.recorded_at
       OR NEW.bindings_sha256 IS DISTINCT FROM OLD.bindings_sha256
       OR NEW.origin IS DISTINCT FROM OLD.origin
       OR NEW.derived_from_revision_id IS DISTINCT FROM OLD.derived_from_revision_id
       OR NEW.change_note IS DISTINCT FROM OLD.change_note THEN
        RAISE EXCEPTION 'signal_binding_set_revision content, identity and validity are immutable';
    END IF;
    IF OLD.superseded_at IS NOT NULL AND NEW.superseded_at IS DISTINCT FROM OLD.superseded_at THEN
        RAISE EXCEPTION 'signal_binding_set_revision recorded interval is already closed';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER binding_set_revision_immutable
    BEFORE UPDATE OR DELETE ON signal_binding_set_revision
    FOR EACH ROW EXECUTE FUNCTION binding_set_revision_immutable();

-- Closing a set revision closes every one of its rows, in the same statement.
CREATE FUNCTION binding_set_revision_close_rows() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.superseded_at IS NULL AND NEW.superseded_at IS NOT NULL THEN
        UPDATE signal_binding_revision SET superseded_at = NEW.superseded_at
            WHERE tenant_id = NEW.tenant_id AND site_id = NEW.site_id
              AND binding_set_revision_id = NEW.id AND superseded_at IS NULL;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER binding_set_revision_close_rows
    AFTER UPDATE ON signal_binding_set_revision
    FOR EACH ROW EXECUTE FUNCTION binding_set_revision_close_rows();

CREATE FUNCTION signal_binding_revision_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'signal_binding_revision rows are append-only; DELETE refused';
    END IF;
    IF (to_jsonb(NEW) - 'superseded_at') IS DISTINCT FROM (to_jsonb(OLD) - 'superseded_at') THEN
        RAISE EXCEPTION 'signal_binding_revision content, identity and validity are immutable';
    END IF;
    IF OLD.superseded_at IS NOT NULL AND NEW.superseded_at IS DISTINCT FROM OLD.superseded_at THEN
        RAISE EXCEPTION 'signal_binding_revision recorded interval is already closed';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER signal_binding_revision_immutable
    BEFORE UPDATE OR DELETE ON signal_binding_revision
    FOR EACH ROW EXECUTE FUNCTION signal_binding_revision_immutable();
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS signal_binding_revision, signal_binding_set_revision CASCADE;
        DROP FUNCTION IF EXISTS signal_binding_matches_set();
        DROP FUNCTION IF EXISTS binding_set_revision_immutable();
        DROP FUNCTION IF EXISTS binding_set_revision_close_rows();
        DROP FUNCTION IF EXISTS signal_binding_revision_immutable();
        ALTER TABLE source DROP CONSTRAINT IF EXISTS source_gateway_scope_unique;
        """
    )
