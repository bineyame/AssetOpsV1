"""S1-01 Foundation identity and time-valid Foundation revisions.

Installs tenant, site, site_import, asset, gateway, source and
foundation_revision with tenant/site composite references, writer-generated
UUID row identities, immutable revision content and the valid-time /
recorded-time rules of the technical design (section 1, "Conventions" and
"Identity, configuration and acquisition").

The first statement enables `btree_gist`, because the GiST exclusion
constraint on currently recorded Foundation validity needs it. A role that
cannot create the extension fails this migration with a clear message; there
is no silent fallback to an application-only overlap check.

Revision ID: 0001_foundation_identity
Revises:
Create Date: 2026-10-07
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0001_foundation_identity"
down_revision = None
branch_labels = None
depends_on = None


def _enable_btree_gist() -> None:
    bind = op.get_bind()
    present = bind.execute(
        text("SELECT 1 FROM pg_extension WHERE extname = 'btree_gist'")
    ).first()
    if present is not None:
        return
    try:
        with bind.begin_nested():
            bind.execute(text("CREATE EXTENSION btree_gist"))
    except Exception as error:  # noqa: BLE001 - re-raised with the reason
        raise RuntimeError(
            "Migration 0001 requires the PostgreSQL extension btree_gist for the "
            "non-overlapping Foundation validity constraint, and the configured "
            "database role could not create it. Ask a database owner to run "
            "`CREATE EXTENSION btree_gist;` in this database (or grant the role "
            "the privilege), then rerun the migration. There is no fallback. "
            f"Database error: {error}"
        ) from error


SCHEMA = r"""
CREATE TABLE tenant (
    id uuid PRIMARY KEY,
    slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9][a-z0-9-]{0,62}$'),
    name text NOT NULL CHECK (length(name) > 0),
    default_currency text NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE site (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant(id),
    site_code text NOT NULL,
    site_code_key text NOT NULL,
    name text NOT NULL,
    site_type text NOT NULL CHECK (site_type IN ('MINIGRID','COLDCHAIN','EV_CHARGING')),
    timezone text NOT NULL,
    lifecycle text NOT NULL,
    country text NULL,
    locality text NULL,
    origin text NOT NULL,
    proposed_source_mode text NOT NULL CHECK (proposed_source_mode IN ('LIVE','SIMULATED')),
    template_id text NULL,
    template_version integer NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT site_code_key_casefold CHECK (site_code_key = lower(site_code)),
    CONSTRAINT site_tenant_code_unique UNIQUE (tenant_id, site_code_key),
    CONSTRAINT site_tenant_id_unique UNIQUE (tenant_id, id)
);
CREATE INDEX site_tenant_type_lifecycle ON site (tenant_id, site_type, lifecycle);

CREATE TABLE site_import (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    source_path text NOT NULL,
    source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    source_format text NOT NULL,
    imported_at timestamptz NOT NULL,
    CONSTRAINT site_import_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT site_import_one_per_site UNIQUE (tenant_id, site_id)
);
CREATE INDEX site_import_source ON site_import (source_path, source_sha256);

CREATE TABLE asset (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    asset_code text NOT NULL,
    asset_type text NOT NULL,
    parent_asset_id uuid NULL,
    commissioned_at timestamptz NULL,
    retired_at timestamptz NULL,
    attributes jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT asset_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT asset_site_code_unique UNIQUE (site_id, asset_code),
    CONSTRAINT asset_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT asset_parent_same_site FOREIGN KEY (tenant_id, site_id, parent_asset_id)
        REFERENCES asset(tenant_id, site_id, id)
);
CREATE INDEX asset_site_type ON asset (site_id, asset_type);
CREATE INDEX asset_site_retired ON asset (site_id, retired_at);

CREATE TABLE gateway (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_external_id text NOT NULL,
    mode text NOT NULL CHECK (mode IN ('LIVE','SIMULATED')),
    credential_ref text NULL,
    registered_at timestamptz NOT NULL,
    disabled_at timestamptz NULL,
    CONSTRAINT gateway_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT gateway_tenant_external_unique UNIQUE (tenant_id, gateway_external_id),
    CONSTRAINT gateway_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX gateway_site_disabled ON gateway (site_id, disabled_at);

CREATE TABLE source (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    source_external_id text NOT NULL,
    device_kind text NOT NULL,
    asset_id uuid NOT NULL,
    registered_at timestamptz NOT NULL,
    disabled_at timestamptz NULL,
    CONSTRAINT source_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT source_gateway_same_site FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT source_asset_same_site FOREIGN KEY (tenant_id, site_id, asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT source_gateway_external_unique UNIQUE (gateway_id, source_external_id)
);
CREATE INDEX source_site_gateway ON source (site_id, gateway_id);

CREATE TABLE foundation_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    version integer NOT NULL CHECK (version >= 1),
    valid_from timestamptz NOT NULL,
    valid_to timestamptz NULL,
    recorded_at timestamptz NOT NULL,
    superseded_at timestamptz NULL,
    schema_version integer NOT NULL,
    content jsonb NOT NULL,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    origin text NOT NULL CHECK (origin IN ('IMPORT','PUBLISH','SPLIT')),
    derived_from_revision_id uuid NULL,
    change_note text NULL,
    CONSTRAINT foundation_revision_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT foundation_revision_site_version_unique UNIQUE (site_id, version),
    CONSTRAINT foundation_revision_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT foundation_revision_valid_range CHECK (valid_to IS NULL OR valid_to > valid_from),
    CONSTRAINT foundation_revision_recorded_range CHECK (superseded_at IS NULL OR superseded_at >= recorded_at),
    CONSTRAINT foundation_revision_no_current_overlap EXCLUDE USING gist (
        site_id WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&
    ) WHERE (superseded_at IS NULL)
);
CREATE INDEX foundation_revision_site_valid ON foundation_revision (site_id, valid_from DESC);

-- Immutable rows: content, identity and validity never change. The only
-- mutable column is superseded_at, and it may only be set once.
CREATE FUNCTION foundation_revision_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'foundation_revision rows are append-only; DELETE refused';
    END IF;
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.site_id IS DISTINCT FROM OLD.site_id
       OR NEW.version IS DISTINCT FROM OLD.version
       OR NEW.valid_from IS DISTINCT FROM OLD.valid_from
       OR NEW.valid_to IS DISTINCT FROM OLD.valid_to
       OR NEW.recorded_at IS DISTINCT FROM OLD.recorded_at
       OR NEW.schema_version IS DISTINCT FROM OLD.schema_version
       OR NEW.content IS DISTINCT FROM OLD.content
       OR NEW.content_sha256 IS DISTINCT FROM OLD.content_sha256
       OR NEW.origin IS DISTINCT FROM OLD.origin
       OR NEW.derived_from_revision_id IS DISTINCT FROM OLD.derived_from_revision_id
       OR NEW.change_note IS DISTINCT FROM OLD.change_note THEN
        RAISE EXCEPTION 'foundation_revision content, identity and validity are immutable';
    END IF;
    IF OLD.superseded_at IS NOT NULL AND NEW.superseded_at IS DISTINCT FROM OLD.superseded_at THEN
        RAISE EXCEPTION 'foundation_revision recorded interval is already closed';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER foundation_revision_immutable
    BEFORE UPDATE OR DELETE ON foundation_revision
    FOR EACH ROW EXECUTE FUNCTION foundation_revision_immutable();

-- Registration rows are identity: no deletion in S1.
CREATE FUNCTION registration_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '% rows are registration identity; DELETE refused', TG_TABLE_NAME;
END;
$$;
CREATE TRIGGER site_append_only BEFORE DELETE ON site
    FOR EACH ROW EXECUTE FUNCTION registration_append_only();
CREATE TRIGGER site_import_append_only BEFORE DELETE ON site_import
    FOR EACH ROW EXECUTE FUNCTION registration_append_only();
CREATE TRIGGER asset_append_only BEFORE DELETE ON asset
    FOR EACH ROW EXECUTE FUNCTION registration_append_only();
CREATE TRIGGER gateway_append_only BEFORE DELETE ON gateway
    FOR EACH ROW EXECUTE FUNCTION registration_append_only();
CREATE TRIGGER source_append_only BEFORE DELETE ON source
    FOR EACH ROW EXECUTE FUNCTION registration_append_only();
"""


def upgrade() -> None:
    _enable_btree_gist()
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS foundation_revision, source, gateway, asset,
            site_import, site, tenant CASCADE;
        DROP FUNCTION IF EXISTS foundation_revision_immutable();
        DROP FUNCTION IF EXISTS registration_append_only();
        """
    )
