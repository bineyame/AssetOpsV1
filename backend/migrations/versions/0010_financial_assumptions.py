"""S4-02a phase 1: Site financial assumption revisions and bitemporal assignments.

`D-2026-10-13-s4-bounded-financial-basis`; packet `tasks/S4-02a-site-assumptions.md`
"Persistence, publication and read contract" items 1-2.

`financial_assumption_revision` is one immutable, explicitly authored Site price
(value, currency, unit, basis, source, authored `[valid_from, valid_to)` intent,
server `recorded_at`, server actor, channel, authorization basis, provenance,
publication `change_kind` and idempotency key). It is append-only: a price row is
never rewritten.

Effective validity lives in `financial_assumption_assignment` (review carry M1):
each row assigns one revision to `[valid_from, valid_to)` over recorded time
`[recorded_from, recorded_to)`. Rows are immutable except a set-once
`recorded_to` (as `foundation_revision.superseded_at`). The GiST exclusion over
both axes means no two assignments of a Site/key ever overlap in valid time at
any recorded instant, so a superseded row stays selectable at older cutoffs. A
two-table trigger requires every assignment's valid range to lie inside its
revision's authored range, and its recorded start to be no earlier than the
revision's `recorded_at` nor than the series' latest `recorded_from`.

Revision ID: 0010_financial_assumptions
Revises: 0009_finding_store
Create Date: 2026-10-13
"""

from __future__ import annotations

from alembic import op

revision = "0010_financial_assumptions"
down_revision = "0009_finding_store"
branch_labels = None
depends_on = None


SCHEMA = r"""
CREATE TABLE financial_assumption_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    assumption_key text NOT NULL CHECK (assumption_key IN ('diesel_price_per_litre')),
    revision_no integer NOT NULL CHECK (revision_no >= 1),
    prior_revision_id uuid NULL,
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    unit text NOT NULL CHECK (unit = 'currency/L'),
    -- Explicitly authored, nonnegative and finite: numeric admits 'NaN' and
    -- 'Infinity', and NaN sorts above every number, so both bounds are needed.
    value numeric NOT NULL CHECK (value >= 0 AND value < 'Infinity'::numeric),
    basis text NOT NULL CHECK (basis IN ('AUTHORED_ESTIMATE','CONTRACT_RATE','RECORDED_PURCHASE')),
    source_reference text NOT NULL CHECK (length(btrim(source_reference)) > 0),
    valid_from timestamptz NOT NULL,
    valid_to timestamptz NULL,
    recorded_at timestamptz NOT NULL,
    change_kind text NOT NULL CHECK (change_kind IN ('INITIAL','SUCCESSION','CORRECTION')),
    correction_reason text NULL,
    actor_kind text NOT NULL CHECK (actor_kind IN ('SYSTEM','HUMAN')),
    actor_id text NOT NULL CHECK (length(btrim(actor_id)) > 0),
    author_id uuid NULL,
    channel text NOT NULL CHECK (channel IN ('SYSTEM_CLI','SYSTEM_FIXTURE','HUMAN_API')),
    authorization_basis text NOT NULL CHECK (length(btrim(authorization_basis)) > 0),
    provenance jsonb NOT NULL,
    idempotency_key text NOT NULL CHECK (length(btrim(idempotency_key)) > 0),
    request_sha256 text NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT financial_assumption_revision_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT financial_assumption_revision_no_unique UNIQUE (tenant_id, site_id, assumption_key, revision_no),
    CONSTRAINT financial_assumption_publication_key_unique UNIQUE (tenant_id, site_id, assumption_key, idempotency_key),
    CONSTRAINT financial_assumption_revision_scope_unique UNIQUE (tenant_id, site_id, assumption_key, id),
    CONSTRAINT financial_assumption_revision_prior_fk FOREIGN KEY (tenant_id, site_id, assumption_key, prior_revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, assumption_key, id),
    CONSTRAINT financial_assumption_revision_first CHECK ((revision_no = 1) = (prior_revision_id IS NULL)),
    CONSTRAINT financial_assumption_revision_valid_range CHECK (valid_to IS NULL OR valid_from < valid_to),
    CONSTRAINT financial_assumption_revision_correction_reason CHECK (
        (change_kind = 'CORRECTION') = (correction_reason IS NOT NULL AND length(btrim(correction_reason)) > 0)),
    -- No client-supplied author: a human author exists only with a verified human principal.
    CONSTRAINT financial_assumption_revision_actor CHECK (
        (actor_kind = 'HUMAN') = (author_id IS NOT NULL)
        AND (actor_kind = 'HUMAN') = (channel = 'HUMAN_API'))
);
CREATE INDEX financial_assumption_revision_recorded
    ON financial_assumption_revision (tenant_id, site_id, assumption_key, recorded_at);

CREATE TABLE financial_assumption_assignment (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    assumption_key text NOT NULL,
    revision_id uuid NOT NULL,
    -- The publication that recorded this assignment (a remainder keeps its old
    -- revision_id but names the correction/succession that re-assigned it).
    publication_revision_id uuid NOT NULL,
    valid_from timestamptz NOT NULL,
    valid_to timestamptz NULL,
    recorded_from timestamptz NOT NULL,
    recorded_to timestamptz NULL,
    CONSTRAINT financial_assumption_assignment_revision_fk FOREIGN KEY (tenant_id, site_id, assumption_key, revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, assumption_key, id),
    CONSTRAINT financial_assumption_assignment_publication_fk
        FOREIGN KEY (tenant_id, site_id, assumption_key, publication_revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, assumption_key, id),
    CONSTRAINT financial_assumption_assignment_valid_range CHECK (valid_to IS NULL OR valid_from < valid_to),
    CONSTRAINT financial_assumption_assignment_recorded_range CHECK (recorded_to IS NULL OR recorded_from < recorded_to),
    CONSTRAINT financial_assumption_assignment_no_overlap EXCLUDE USING gist (
        tenant_id WITH =, site_id WITH =, assumption_key WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(recorded_from, recorded_to, '[)') WITH &&)
);
CREATE INDEX financial_assumption_assignment_valid
    ON financial_assumption_assignment (tenant_id, site_id, assumption_key, valid_from, valid_to);
CREATE INDEX financial_assumption_assignment_recorded
    ON financial_assumption_assignment (tenant_id, site_id, assumption_key, recorded_from, recorded_to);
CREATE INDEX financial_assumption_assignment_current
    ON financial_assumption_assignment (tenant_id, site_id, assumption_key, valid_from) WHERE recorded_to IS NULL;
CREATE INDEX financial_assumption_assignment_revision
    ON financial_assumption_assignment (revision_id);

CREATE TRIGGER financial_assumption_revision_append_only BEFORE UPDATE OR DELETE ON financial_assumption_revision
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

-- Assignment rows: everything immutable except a set-once recorded_to.
CREATE FUNCTION financial_assumption_assignment_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'financial_assumption_assignment rows are append-only; DELETE refused';
    END IF;
    IF (to_jsonb(NEW) - 'recorded_to') IS DISTINCT FROM (to_jsonb(OLD) - 'recorded_to') THEN
        RAISE EXCEPTION 'financial_assumption_assignment identity, validity and recorded start are immutable';
    END IF;
    IF OLD.recorded_to IS NOT NULL AND NEW.recorded_to IS DISTINCT FROM OLD.recorded_to THEN
        RAISE EXCEPTION 'financial_assumption_assignment recorded interval is already closed';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER financial_assumption_assignment_immutable
    BEFORE UPDATE OR DELETE ON financial_assumption_assignment
    FOR EACH ROW EXECUTE FUNCTION financial_assumption_assignment_immutable();

-- Two-table containment (not expressible as a CHECK): the assignment's valid
-- range lies inside its revision's authored range, it is recorded no earlier
-- than the revision, and recorded time only moves forward within a series.
CREATE FUNCTION financial_assumption_assignment_contained() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    rev financial_assumption_revision%ROWTYPE;
    latest timestamptz;
BEGIN
    SELECT * INTO rev FROM financial_assumption_revision
        WHERE tenant_id = NEW.tenant_id AND site_id = NEW.site_id
          AND assumption_key = NEW.assumption_key AND id = NEW.revision_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'financial_assumption_assignment names no revision of this Site/key';
    END IF;
    IF NOT (tstzrange(rev.valid_from, rev.valid_to, '[)') @> tstzrange(NEW.valid_from, NEW.valid_to, '[)')) THEN
        RAISE EXCEPTION 'financial_assumption_assignment valid range lies outside its revision''s authored range';
    END IF;
    IF NEW.recorded_from < rev.recorded_at THEN
        RAISE EXCEPTION 'financial_assumption_assignment is recorded before its revision';
    END IF;
    SELECT max(recorded_from) INTO latest FROM financial_assumption_assignment
        WHERE tenant_id = NEW.tenant_id AND site_id = NEW.site_id AND assumption_key = NEW.assumption_key;
    IF latest IS NOT NULL AND NEW.recorded_from < latest THEN
        RAISE EXCEPTION 'financial_assumption_assignment recorded time moves backward in its series';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER financial_assumption_assignment_contained
    BEFORE INSERT ON financial_assumption_assignment
    FOR EACH ROW EXECUTE FUNCTION financial_assumption_assignment_contained();
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS financial_assumption_assignment, financial_assumption_revision CASCADE;
        DROP FUNCTION IF EXISTS financial_assumption_assignment_immutable();
        DROP FUNCTION IF EXISTS financial_assumption_assignment_contained();
    """)
