"""S4-02b phase 1: append-only financial consequence revisions, lineage links and durable dirty work.

`D-2026-10-13-s4-bounded-financial-basis` (and its `fuel-cost-1` addendum); packet
`tasks/S4-02b-fuel-consequence.md` "Migration, recompute and reads". This supersedes the technical design's
single-assessment / single-assumption / scalar-quantity sketch (review carry L1): rows carry explicit
`quantity_low/high`, a separate technical-input digest and consequence basis digest, and multi-row links.

- `financial_consequence_revision`: one immutable `POTENTIAL_FUEL_COST` consequence of one exact
  FindingRevision, `MODELLED_CONDITIONAL`, with the `fuel-cost-1` parameter version, quantity bounds, the
  whole-window price selection and nullable amount bounds. CHECKs make an unavailable quantity carry no
  number, an unpriced consequence carry no amount and a priced one carry exactly `0 .. quantity_high x price`.
  UNIQUE `(finding_revision_id, consequence_type, revision_no)` and `(finding_revision_id, consequence_type,
  consequence_basis_sha256)` (idempotent append).
- Links: `financial_consequence_assessment_revision` (primary plus every supporting exact assessment, each
  required to be linked by the FindingRevision itself), `financial_consequence_assumption_revision` (every
  exact price revision used) and `financial_consequence_power_interval` (each counted accepted power mean once,
  with power, duration, SFC revision, covered Candidate spans and containment result).
- Dirty/outbox: `financial_consequence_work` rows are inserted only by triggers, in the same transaction as an
  assumption publication or a FindingRevision append, keyed by Site, key/revision or FindingRevision and the
  affected valid range. `financial_consequence_work_attempt` records each recompute attempt (phase 2a worker);
  work without a SUCCEEDED attempt is pending.

Revision ID: 0011_financial_consequences
Revises: 0010_financial_assumptions
Create Date: 2026-10-14
"""

from __future__ import annotations

from alembic import op

revision = "0011_financial_consequences"
down_revision = "0010_financial_assumptions"
branch_labels = None
depends_on = None


SCHEMA = r"""
ALTER TABLE financial_assumption_revision
    ADD CONSTRAINT financial_assumption_revision_site_unique UNIQUE (tenant_id, site_id, id);

CREATE TABLE financial_consequence_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    finding_id uuid NOT NULL,
    finding_revision_id uuid NOT NULL,
    consequence_type text NOT NULL CHECK (consequence_type IN ('POTENTIAL_FUEL_COST')),
    revision_no integer NOT NULL CHECK (revision_no >= 1),
    prior_consequence_revision_id uuid NULL REFERENCES financial_consequence_revision(id),
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    overlap_group text NOT NULL CHECK (length(btrim(overlap_group)) > 0),
    basis_kind text NOT NULL CHECK (basis_kind IN ('MODELLED_CONDITIONAL')),
    model_id text NOT NULL CHECK (model_id IN ('fuel-cost-1')),
    formula_version text NOT NULL CHECK (length(btrim(formula_version)) > 0),
    parameter_version text NOT NULL CHECK (length(btrim(parameter_version)) > 0),
    parameter_sha256 text NOT NULL CHECK (parameter_sha256 ~ '^[0-9a-f]{64}$'),
    sfc_upper_multiplier numeric NOT NULL CHECK (sfc_upper_multiplier > 0 AND sfc_upper_multiplier < 'Infinity'::numeric),
    state text NOT NULL CHECK (state IN ('PRICED','UNPRICED','QUANTITY_UNAVAILABLE')),
    quantity_state text NOT NULL CHECK (quantity_state IN ('AVAILABLE','QUANTITY_UNAVAILABLE')),
    quantity_reason text NULL,
    quantity_detail text NULL,
    quantity_unit text NOT NULL CHECK (quantity_unit = 'L'),
    quantity_low numeric NULL,
    quantity_high numeric NULL,
    quantity_high_exact text NULL CHECK (quantity_high_exact IS NULL OR quantity_high_exact ~ '^[0-9]+/[1-9][0-9]*$'),
    price_state text NOT NULL CHECK (price_state IN ('PRICED','UNPRICED','NOT_EVALUATED')),
    price_reason text NULL,
    price_revision_id uuid NULL,
    price_value numeric NULL,
    price_currency text NULL CHECK (price_currency IS NULL OR price_currency ~ '^[A-Z]{3}$'),
    amount_low numeric NULL,
    amount_high numeric NULL,
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    limitations jsonb NOT NULL CHECK (jsonb_typeof(limitations) = 'array' AND jsonb_array_length(limitations) > 0),
    technical_input_sha256 text NOT NULL CHECK (technical_input_sha256 ~ '^[0-9a-f]{64}$'),
    consequence_basis_sha256 text NOT NULL CHECK (consequence_basis_sha256 ~ '^[0-9a-f]{64}$'),
    actor_id text NOT NULL CHECK (length(btrim(actor_id)) > 0),
    recorded_at timestamptz NOT NULL,
    CONSTRAINT financial_consequence_window_ordered CHECK (window_start <= window_end),
    CONSTRAINT financial_consequence_prior_iff_not_first CHECK ((revision_no = 1) = (prior_consequence_revision_id IS NULL)),
    -- An unavailable quantity carries no number, no price and no amount.
    CONSTRAINT financial_consequence_unavailable_has_no_number CHECK (
        (state = 'QUANTITY_UNAVAILABLE') = (quantity_state = 'QUANTITY_UNAVAILABLE')
        AND (quantity_state = 'AVAILABLE' OR (quantity_reason IS NOT NULL AND quantity_low IS NULL
             AND quantity_high IS NULL AND quantity_high_exact IS NULL AND price_state = 'NOT_EVALUATED'))),
    CONSTRAINT financial_consequence_available_bounds CHECK (
        quantity_state = 'QUANTITY_UNAVAILABLE' OR (quantity_reason IS NULL AND quantity_low = 0
            AND quantity_high >= 0 AND quantity_high < 'Infinity'::numeric AND quantity_high_exact IS NOT NULL)),
    -- Unpriced is never zero: no amount, no currency.
    CONSTRAINT financial_consequence_unpriced_has_no_amount CHECK (
        state = 'PRICED' OR (amount_low IS NULL AND amount_high IS NULL AND currency IS NULL)),
    CONSTRAINT financial_consequence_unpriced_reason CHECK (
        state <> 'UNPRICED' OR (price_state = 'UNPRICED' AND price_reason IS NOT NULL AND price_revision_id IS NULL
            AND price_value IS NULL)),
    CONSTRAINT financial_consequence_not_evaluated_has_no_price CHECK (
        price_state <> 'NOT_EVALUATED' OR (price_revision_id IS NULL AND price_value IS NULL AND price_currency IS NULL)),
    -- Priced: one exact price revision, amount exactly 0 .. quantity_high x price, unrounded.
    CONSTRAINT financial_consequence_priced_amount CHECK (
        state <> 'PRICED' OR (price_state = 'PRICED' AND price_reason IS NULL AND price_revision_id IS NOT NULL
            AND price_value >= 0 AND price_value < 'Infinity'::numeric AND price_currency IS NOT NULL
            AND currency = price_currency AND amount_low = 0 AND amount_high = quantity_high * price_value)),
    CONSTRAINT financial_consequence_finding_fk FOREIGN KEY (tenant_id, site_id, finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_finding_revision_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_price_fk FOREIGN KEY (tenant_id, site_id, price_revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_revision_no_unique UNIQUE (finding_revision_id, consequence_type, revision_no),
    CONSTRAINT financial_consequence_basis_unique
        UNIQUE (finding_revision_id, consequence_type, consequence_basis_sha256),
    CONSTRAINT financial_consequence_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX financial_consequence_site_window
    ON financial_consequence_revision (tenant_id, site_id, window_start, window_end);
CREATE INDEX financial_consequence_finding
    ON financial_consequence_revision (tenant_id, site_id, finding_id, finding_revision_id, revision_no);

CREATE TABLE financial_consequence_assessment_revision (
    consequence_revision_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    assessment_revision_id uuid NOT NULL,
    analytic_run_id uuid NOT NULL,
    is_primary boolean NOT NULL,
    PRIMARY KEY (consequence_revision_id, assessment_revision_id),
    CONSTRAINT financial_consequence_assessment_consequence_fk FOREIGN KEY (tenant_id, site_id, consequence_revision_id)
        REFERENCES financial_consequence_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_assessment_revision_fk FOREIGN KEY (tenant_id, site_id, assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_assessment_run_fk FOREIGN KEY (tenant_id, site_id, analytic_run_id)
        REFERENCES analytic_run(tenant_id, site_id, id)
);
CREATE UNIQUE INDEX financial_consequence_assessment_one_primary
    ON financial_consequence_assessment_revision (consequence_revision_id) WHERE is_primary;

CREATE TABLE financial_consequence_assumption_revision (
    consequence_revision_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    assumption_revision_id uuid NOT NULL,
    assignment_id uuid NOT NULL REFERENCES financial_assumption_assignment(id),
    role text NOT NULL CHECK (role IN ('PRICE')),
    PRIMARY KEY (consequence_revision_id, assumption_revision_id),
    CONSTRAINT financial_consequence_assumption_consequence_fk FOREIGN KEY (tenant_id, site_id, consequence_revision_id)
        REFERENCES financial_consequence_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_assumption_revision_fk FOREIGN KEY (tenant_id, site_id, assumption_revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, id)
);

CREATE TABLE financial_consequence_power_interval (
    consequence_revision_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    interval_start timestamptz NOT NULL,
    interval_end timestamptz NOT NULL,
    mean_kw numeric NOT NULL CHECK (mean_kw >= 0 AND mean_kw < 'Infinity'::numeric),
    duration_seconds integer NOT NULL CHECK (duration_seconds > 0),
    sfc_l_per_kwh numeric NOT NULL CHECK (sfc_l_per_kwh > 0 AND sfc_l_per_kwh < 'Infinity'::numeric),
    foundation_revision_id uuid NOT NULL,
    binding_revision_id uuid NOT NULL,
    envelope_sha256 text NOT NULL,
    covered_spans jsonb NOT NULL CHECK (jsonb_typeof(covered_spans) = 'array' AND jsonb_array_length(covered_spans) > 0),
    containment text NOT NULL CHECK (containment IN ('CONTAINED')),
    PRIMARY KEY (consequence_revision_id, evidence_id),
    CONSTRAINT financial_consequence_interval_duration CHECK (
        interval_start < interval_end
        AND duration_seconds = extract(epoch FROM interval_end - interval_start)::integer),
    CONSTRAINT financial_consequence_interval_consequence_fk FOREIGN KEY (tenant_id, site_id, consequence_revision_id)
        REFERENCES financial_consequence_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_interval_evidence_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_interval_foundation_fk FOREIGN KEY (tenant_id, site_id, foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_interval_binding_fk FOREIGN KEY (tenant_id, site_id, binding_revision_id)
        REFERENCES signal_binding_revision(tenant_id, site_id, id)
);

-- Durable dirty/outbox work. Inserted only by the triggers below, in the writer's own transaction.
CREATE TABLE financial_consequence_work (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    cause text NOT NULL CHECK (cause IN ('ASSUMPTION_PUBLISHED','FINDING_REVISION_APPENDED')),
    assumption_key text NULL,
    assumption_revision_id uuid NULL,
    finding_id uuid NULL,
    finding_revision_id uuid NULL,
    affected_from timestamptz NOT NULL,
    affected_to timestamptz NULL,
    enqueued_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT financial_consequence_work_cause_shape CHECK (
        (cause = 'ASSUMPTION_PUBLISHED' AND assumption_key IS NOT NULL AND assumption_revision_id IS NOT NULL
            AND finding_id IS NULL AND finding_revision_id IS NULL)
        OR (cause = 'FINDING_REVISION_APPENDED' AND finding_id IS NOT NULL AND finding_revision_id IS NOT NULL
            AND assumption_key IS NULL AND assumption_revision_id IS NULL)),
    CONSTRAINT financial_consequence_work_range CHECK (affected_to IS NULL OR affected_from < affected_to),
    CONSTRAINT financial_consequence_work_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT financial_consequence_work_assumption_fk FOREIGN KEY (tenant_id, site_id, assumption_revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_work_finding_revision_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_work_assumption_once UNIQUE (assumption_revision_id),
    CONSTRAINT financial_consequence_work_finding_revision_once UNIQUE (finding_revision_id),
    CONSTRAINT financial_consequence_work_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX financial_consequence_work_site ON financial_consequence_work (tenant_id, site_id, enqueued_at);

CREATE TABLE financial_consequence_work_attempt (
    id uuid PRIMARY KEY,
    work_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    attempt_no integer NOT NULL CHECK (attempt_no >= 1),
    outcome text NOT NULL CHECK (outcome IN ('SUCCEEDED','FAILED')),
    error_code text NULL,
    error_detail text NULL,
    consequence_revision_ids jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(consequence_revision_ids) = 'array'),
    actor_id text NOT NULL CHECK (length(btrim(actor_id)) > 0),
    finished_at timestamptz NOT NULL,
    CONSTRAINT financial_consequence_attempt_error_iff_failed CHECK ((outcome = 'FAILED') = (error_code IS NOT NULL)),
    CONSTRAINT financial_consequence_attempt_work_fk FOREIGN KEY (tenant_id, site_id, work_id)
        REFERENCES financial_consequence_work(tenant_id, site_id, id),
    CONSTRAINT financial_consequence_attempt_no_unique UNIQUE (work_id, attempt_no)
);
CREATE UNIQUE INDEX financial_consequence_attempt_one_success
    ON financial_consequence_work_attempt (work_id) WHERE outcome = 'SUCCEEDED';

CREATE TRIGGER financial_consequence_revision_append_only BEFORE UPDATE OR DELETE ON financial_consequence_revision
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER financial_consequence_assessment_revision_append_only
    BEFORE UPDATE OR DELETE ON financial_consequence_assessment_revision
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER financial_consequence_assumption_revision_append_only
    BEFORE UPDATE OR DELETE ON financial_consequence_assumption_revision
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER financial_consequence_power_interval_append_only
    BEFORE UPDATE OR DELETE ON financial_consequence_power_interval
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER financial_consequence_work_append_only BEFORE UPDATE OR DELETE ON financial_consequence_work
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER financial_consequence_work_attempt_append_only
    BEFORE UPDATE OR DELETE ON financial_consequence_work_attempt
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

-- A consequence names its own FindingRevision's Finding and window, and extends its chain by exactly one.
CREATE FUNCTION financial_consequence_revision_lineage() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    fr finding_revision%ROWTYPE;
    prior financial_consequence_revision%ROWTYPE;
    latest integer;
BEGIN
    SELECT * INTO fr FROM finding_revision
        WHERE tenant_id = NEW.tenant_id AND site_id = NEW.site_id AND id = NEW.finding_revision_id;
    IF fr.finding_id IS DISTINCT FROM NEW.finding_id THEN
        RAISE EXCEPTION 'financial_consequence_revision names a FindingRevision of another Finding';
    END IF;
    IF fr.episode_start IS DISTINCT FROM NEW.window_start OR fr.episode_end IS DISTINCT FROM NEW.window_end THEN
        RAISE EXCEPTION 'financial_consequence_revision window is not its FindingRevision window';
    END IF;
    SELECT max(revision_no) INTO latest FROM financial_consequence_revision
        WHERE finding_revision_id = NEW.finding_revision_id AND consequence_type = NEW.consequence_type;
    IF NEW.revision_no <> coalesce(latest, 0) + 1 THEN
        RAISE EXCEPTION 'financial_consequence_revision revision_no must extend its chain by one';
    END IF;
    IF NEW.prior_consequence_revision_id IS NOT NULL THEN
        SELECT * INTO prior FROM financial_consequence_revision WHERE id = NEW.prior_consequence_revision_id;
        IF prior.finding_revision_id IS DISTINCT FROM NEW.finding_revision_id
           OR prior.consequence_type IS DISTINCT FROM NEW.consequence_type
           OR prior.revision_no IS DISTINCT FROM NEW.revision_no - 1 THEN
            RAISE EXCEPTION 'financial_consequence_revision prior is not the previous revision of its chain';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER financial_consequence_revision_lineage BEFORE INSERT ON financial_consequence_revision
    FOR EACH ROW EXECUTE FUNCTION financial_consequence_revision_lineage();

-- A consequence may cite only assessments its FindingRevision itself links.
CREATE FUNCTION financial_consequence_assessment_linked() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM financial_consequence_revision c
        JOIN finding_revision_assessment a ON a.finding_revision_id = c.finding_revision_id
        WHERE c.id = NEW.consequence_revision_id AND a.assessment_revision_id = NEW.assessment_revision_id
          AND a.analytic_run_id = NEW.analytic_run_id AND a.scope = 'INTERVAL' AND a.is_primary = NEW.is_primary) THEN
        RAISE EXCEPTION 'financial_consequence_assessment_revision is not an INTERVAL assessment of its FindingRevision';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER financial_consequence_assessment_linked BEFORE INSERT ON financial_consequence_assessment_revision
    FOR EACH ROW EXECUTE FUNCTION financial_consequence_assessment_linked();

-- Transactional dirty work: an assumption publication dirties its affected valid range (a SUCCESSION also
-- changes everything after its start, because it closes the prior open-ended assignment there).
CREATE FUNCTION financial_consequence_dirty_on_assumption() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO financial_consequence_work (tenant_id, site_id, cause, assumption_key, assumption_revision_id,
                                            affected_from, affected_to)
    VALUES (NEW.tenant_id, NEW.site_id, 'ASSUMPTION_PUBLISHED', NEW.assumption_key, NEW.id, NEW.valid_from,
            CASE WHEN NEW.change_kind = 'SUCCESSION' THEN NULL ELSE NEW.valid_to END)
    ON CONFLICT (assumption_revision_id) DO NOTHING;
    RETURN NULL;
END;
$$;
CREATE TRIGGER financial_consequence_dirty_on_assumption AFTER INSERT ON financial_assumption_revision
    FOR EACH ROW EXECUTE FUNCTION financial_consequence_dirty_on_assumption();

CREATE FUNCTION financial_consequence_dirty_on_finding_revision() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO financial_consequence_work (tenant_id, site_id, cause, finding_id, finding_revision_id,
                                            affected_from, affected_to)
    VALUES (NEW.tenant_id, NEW.site_id, 'FINDING_REVISION_APPENDED', NEW.finding_id, NEW.id, NEW.episode_start,
            NEW.episode_end)
    ON CONFLICT (finding_revision_id) DO NOTHING;
    RETURN NULL;
END;
$$;
CREATE TRIGGER financial_consequence_dirty_on_finding_revision AFTER INSERT ON finding_revision
    FOR EACH ROW EXECUTE FUNCTION financial_consequence_dirty_on_finding_revision();
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS financial_consequence_dirty_on_finding_revision ON finding_revision;
        DROP TRIGGER IF EXISTS financial_consequence_dirty_on_assumption ON financial_assumption_revision;
        DROP TABLE IF EXISTS financial_consequence_work_attempt, financial_consequence_work,
            financial_consequence_power_interval, financial_consequence_assumption_revision,
            financial_consequence_assessment_revision, financial_consequence_revision CASCADE;
        DROP FUNCTION IF EXISTS financial_consequence_dirty_on_finding_revision();
        DROP FUNCTION IF EXISTS financial_consequence_dirty_on_assumption();
        DROP FUNCTION IF EXISTS financial_consequence_assessment_linked();
        DROP FUNCTION IF EXISTS financial_consequence_revision_lineage();
        ALTER TABLE financial_assumption_revision DROP CONSTRAINT IF EXISTS financial_assumption_revision_site_unique;
    """)
