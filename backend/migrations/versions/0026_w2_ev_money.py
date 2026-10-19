"""W2-07 commit 1: authored EV tariff and append-only Site gross scenario.

`.agent/W2-07-build-spec.md` "Concrete-artifact closure (2026-10-19)" section 1, as confirmed by its "Post-W2-06
reconciliation (2026-10-20)" (decision D-2026-10-18-w2-06-07-buildspec). The body below is the spec's literal 0026.

- `financial_assumption_revision` widens only its key/unit CHECKs for `ev_gross_tariff_per_kwh` (`currency/kWh`) and
  adds an EV-only strictly positive value CHECK. Diesel `currency/L`, the finite nonnegative value CHECK, currency,
  author, assignment and idempotency rules are untouched. No tariff row is inserted here.
- `ev_consequence_revision`, `ev_consequence_session`, `ev_consequence_evidence`: tenant/Site-scoped, append-only Site
  gross tariff scenario history and its exact session-revision and accepted-evidence links. ESTIMATED requires every
  quantity/tariff/currency field and `amount = quantity_kwh * tariff_value` exactly (unscaled numeric).
- `ev_consequence_work`: dirty work inserted only by the triggers below, through `ev_consequence_enqueue` with
  `ON CONFLICT (tenant_id,site_id,window_start,window_end,dirty_basis_sha256) DO NOTHING`; never by runtime code.
- `ev_consequence_work_attempt`: append-only SUCCEEDED/FAILED attempts, one success per work row.

Upgrade backfills one work row per existing `ev-session/1` assessment window. Downgrade refuses while any EV tariff or
any 0026 row exists (including backfilled work); otherwise it drops only 0026 objects and restores the diesel-only
CHECKs. 0025's EV session tables, functions and triggers are untouched.

Revision ID: 0026_w2_ev_money
Revises: 0025_w2_ev_session
Create Date: 2026-10-20
"""
from alembic import op

revision = "0026_w2_ev_money"
down_revision = "0025_w2_ev_session"
branch_labels = None
depends_on = None

SCHEMA = r"""
DO $$ BEGIN
 IF (SELECT count(*) FROM pg_constraint WHERE conrelid='financial_assumption_revision'::regclass
     AND conname IN ('financial_assumption_revision_assumption_key_check','financial_assumption_revision_unit_check'))<>2 THEN
   RAISE EXCEPTION '0026_w2_ev_money: the 0010 assumption key/unit CHECK names are not installed';
 END IF;
END $$;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_assumption_key_check;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_unit_check;
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_assumption_key_check
  CHECK (assumption_key IN ('diesel_price_per_litre','ev_gross_tariff_per_kwh'));
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_unit_check
  CHECK ((assumption_key='diesel_price_per_litre' AND unit='currency/L') OR
         (assumption_key='ev_gross_tariff_per_kwh' AND unit='currency/kWh'));
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_ev_positive
  CHECK (assumption_key <> 'ev_gross_tariff_per_kwh' OR value > 0);

CREATE TABLE ev_consequence_revision (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 finding_revision_id uuid NULL, assessment_revision_id uuid NOT NULL,
 revision_no integer NOT NULL CHECK (revision_no > 0),
 basis_sha256 text NOT NULL CHECK (basis_sha256 ~ '^[0-9a-f]{64}$'),
 technical_input_sha256 text NOT NULL CHECK (technical_input_sha256 ~ '^[0-9a-f]{64}$'),
 formula_version text NOT NULL DEFAULT 'ev-gross-tariff/1' CHECK (formula_version='ev-gross-tariff/1'),
 window_start timestamptz NOT NULL, window_end timestamptz NOT NULL,
 quantity_kwh numeric NULL, tariff_revision_id uuid NULL,
 tariff_assumption_key text GENERATED ALWAYS AS ('ev_gross_tariff_per_kwh') STORED,
 tariff_value numeric NULL,
 currency text NULL, amount numeric NULL,
 state text NOT NULL CHECK (state IN ('ESTIMATED','UNPRICED','WITHHELD')),
 reason text NOT NULL CHECK (length(btrim(reason))>0),
 source_gate text NOT NULL CHECK (source_gate IN ('AUTHORED_DEMONSTRATION','REGISTERED_SIMULATION','MIXED','UNKNOWN')),
 overlap_group text NOT NULL CHECK (length(btrim(overlap_group))>0), recorded_at timestamptz NOT NULL,
 CONSTRAINT ev_consequence_revision_site_fk FOREIGN KEY (tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT ev_consequence_revision_finding_fk FOREIGN KEY (tenant_id,site_id,finding_revision_id) REFERENCES finding_revision(tenant_id,site_id,id),
 CONSTRAINT ev_consequence_revision_assessment_fk FOREIGN KEY (tenant_id,site_id,assessment_revision_id) REFERENCES assessment_revision(tenant_id,site_id,id),
 CONSTRAINT ev_consequence_revision_tariff_fk FOREIGN KEY (tenant_id,site_id,tariff_assumption_key,tariff_revision_id) REFERENCES financial_assumption_revision(tenant_id,site_id,assumption_key,id),
 CONSTRAINT ev_consequence_revision_scope_unique UNIQUE (tenant_id,site_id,id),
 CONSTRAINT ev_consequence_revision_basis_unique UNIQUE (tenant_id,site_id,window_start,window_end,basis_sha256),
 CONSTRAINT ev_consequence_revision_number_unique UNIQUE (tenant_id,site_id,window_start,window_end,revision_no),
 CONSTRAINT ev_consequence_revision_window CHECK (window_start<window_end),
 CONSTRAINT ev_consequence_revision_quantity CHECK (quantity_kwh IS NULL OR (quantity_kwh>=0 AND quantity_kwh<'Infinity'::numeric)),
 CONSTRAINT ev_consequence_revision_tariff_value CHECK (tariff_value IS NULL OR (tariff_value>0 AND tariff_value<'Infinity'::numeric)),
 CONSTRAINT ev_consequence_revision_amount CHECK (amount IS NULL OR (amount>=0 AND amount<'Infinity'::numeric)),
 CONSTRAINT ev_consequence_revision_currency CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
 CONSTRAINT ev_consequence_revision_state CHECK
  ((state='ESTIMATED' AND quantity_kwh IS NOT NULL AND tariff_revision_id IS NOT NULL
     AND tariff_value IS NOT NULL AND currency IS NOT NULL AND amount IS NOT NULL
     AND amount=quantity_kwh*tariff_value)
   OR (state IN ('UNPRICED','WITHHELD') AND amount IS NULL AND currency IS NULL))
);
CREATE INDEX ev_consequence_revision_recorded ON ev_consequence_revision(site_id,recorded_at DESC,id);
CREATE INDEX ev_consequence_revision_window_head ON ev_consequence_revision(site_id,window_start,window_end,revision_no DESC);
CREATE TABLE ev_consequence_session (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, consequence_revision_id uuid NOT NULL,
 session_revision_id uuid NOT NULL, included_kwh numeric NOT NULL,
 PRIMARY KEY (tenant_id,site_id,consequence_revision_id,session_revision_id),
 CONSTRAINT ev_consequence_session_consequence_fk FOREIGN KEY (tenant_id,site_id,consequence_revision_id) REFERENCES ev_consequence_revision(tenant_id,site_id,id),
 CONSTRAINT ev_consequence_session_session_fk FOREIGN KEY (tenant_id,site_id,session_revision_id) REFERENCES ev_session_revision(tenant_id,site_id,id),
 CONSTRAINT ev_consequence_session_quantity CHECK (included_kwh>=0 AND included_kwh<'Infinity'::numeric)
);
CREATE INDEX ev_consequence_session_session ON ev_consequence_session(tenant_id,site_id,session_revision_id);
CREATE TABLE ev_consequence_evidence (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, consequence_revision_id uuid NOT NULL, evidence_id uuid NOT NULL,
 PRIMARY KEY (tenant_id,site_id,consequence_revision_id,evidence_id),
 CONSTRAINT ev_consequence_evidence_consequence_fk FOREIGN KEY (tenant_id,site_id,consequence_revision_id) REFERENCES ev_consequence_revision(tenant_id,site_id,id),
 CONSTRAINT ev_consequence_evidence_accepted_fk FOREIGN KEY (tenant_id,site_id,evidence_id) REFERENCES accepted_evidence(tenant_id,site_id,id)
);
CREATE INDEX ev_consequence_evidence_evidence ON ev_consequence_evidence(tenant_id,site_id,evidence_id);
CREATE TABLE ev_consequence_work (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 window_start timestamptz NOT NULL, window_end timestamptz NOT NULL,
 dirty_basis_sha256 text NOT NULL CHECK (dirty_basis_sha256 ~ '^[0-9a-f]{64}$'),
 created_at timestamptz NOT NULL,
 CONSTRAINT ev_consequence_work_site_fk FOREIGN KEY (tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT ev_consequence_work_window CHECK (window_start<window_end),
 CONSTRAINT ev_consequence_work_scope_unique UNIQUE (tenant_id,site_id,id),
 CONSTRAINT ev_consequence_work_dirty_unique UNIQUE (tenant_id,site_id,window_start,window_end,dirty_basis_sha256)
);
CREATE INDEX ev_consequence_work_pending ON ev_consequence_work(site_id,created_at,id);
CREATE TABLE ev_consequence_work_attempt (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, work_id uuid NOT NULL,
 attempt_no integer NOT NULL CHECK (attempt_no>0),
 outcome text NOT NULL CHECK (outcome IN ('SUCCEEDED','FAILED')),
 error_code text NULL, started_at timestamptz NOT NULL, finished_at timestamptz NOT NULL,
 CONSTRAINT ev_consequence_attempt_work_fk FOREIGN KEY (tenant_id,site_id,work_id) REFERENCES ev_consequence_work(tenant_id,site_id,id),
 CONSTRAINT ev_consequence_attempt_no_unique UNIQUE (tenant_id,site_id,work_id,attempt_no),
 CONSTRAINT ev_consequence_attempt_error CHECK ((outcome='FAILED')=(error_code IS NOT NULL AND length(btrim(error_code))>0)),
 CONSTRAINT ev_consequence_attempt_time CHECK (started_at<=finished_at)
);
CREATE UNIQUE INDEX ev_consequence_attempt_one_success ON ev_consequence_work_attempt(tenant_id,site_id,work_id) WHERE outcome='SUCCEEDED';
CREATE INDEX ev_consequence_attempt_work ON ev_consequence_work_attempt(tenant_id,site_id,work_id,attempt_no DESC);
CREATE TRIGGER ev_consequence_revision_append_only BEFORE UPDATE OR DELETE ON ev_consequence_revision FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER ev_consequence_session_append_only BEFORE UPDATE OR DELETE ON ev_consequence_session FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER ev_consequence_evidence_append_only BEFORE UPDATE OR DELETE ON ev_consequence_evidence FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER ev_consequence_work_append_only BEFORE UPDATE OR DELETE ON ev_consequence_work FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER ev_consequence_work_attempt_append_only BEFORE UPDATE OR DELETE ON ev_consequence_work_attempt FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE FUNCTION ev_consequence_tariff_key() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.tariff_revision_id IS NOT NULL AND NOT EXISTS
  (SELECT 1 FROM financial_assumption_revision r WHERE r.tenant_id=NEW.tenant_id
   AND r.site_id=NEW.site_id AND r.id=NEW.tariff_revision_id
   AND r.assumption_key='ev_gross_tariff_per_kwh' AND r.value=NEW.tariff_value
   AND (NEW.currency IS NULL OR r.currency=NEW.currency)) THEN
   RAISE EXCEPTION 'EV consequence tariff must be a same-Site EV tariff revision';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER ev_consequence_tariff_key BEFORE INSERT ON ev_consequence_revision FOR EACH ROW EXECUTE FUNCTION ev_consequence_tariff_key();

CREATE FUNCTION ev_consequence_enqueue(p_tenant uuid,p_site uuid,p_from timestamptz,p_to timestamptz,p_cause text,p_id uuid)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE d text;
BEGIN
 IF p_from IS NULL OR p_to IS NULL OR p_from>=p_to THEN RETURN; END IF;
 -- The worker recalculates from the selected heads; this SHA identifies a dirtiness event, not a money basis.
 d := encode(sha256(convert_to(jsonb_build_array(p_tenant::text,p_site::text,p_from,p_to,p_cause,p_id::text)::text,'UTF8')),'hex');
 INSERT INTO ev_consequence_work(id,tenant_id,site_id,window_start,window_end,dirty_basis_sha256,created_at)
 VALUES (gen_random_uuid(),p_tenant,p_site,p_from,p_to,d,clock_timestamp())
 ON CONFLICT (tenant_id,site_id,window_start,window_end,dirty_basis_sha256) DO NOTHING;
END $$;
CREATE FUNCTION ev_consequence_on_session() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE w record;
BEGIN
 SELECT a.window_start,a.window_end INTO w FROM assessment_revision a
 WHERE a.tenant_id=NEW.tenant_id AND a.site_id=NEW.site_id AND a.id=NEW.assessment_revision_id;
 PERFORM ev_consequence_enqueue(NEW.tenant_id,NEW.site_id,w.window_start,w.window_end,'SESSION_REVISION',NEW.id);
 RETURN NEW;
END $$;
CREATE TRIGGER ev_consequence_dirty_session AFTER INSERT ON ev_session_revision FOR EACH ROW EXECUTE FUNCTION ev_consequence_on_session();
CREATE FUNCTION ev_consequence_on_assessment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.analytic_id='ev-session/1' THEN
  PERFORM ev_consequence_enqueue(NEW.tenant_id,NEW.site_id,NEW.window_start,NEW.window_end,'ASSESSMENT_REVISION',NEW.id);
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER ev_consequence_dirty_assessment AFTER INSERT ON assessment_revision FOR EACH ROW EXECUTE FUNCTION ev_consequence_on_assessment();
CREATE FUNCTION ev_consequence_on_tariff() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE w record;
BEGIN
 IF NEW.assumption_key='ev_gross_tariff_per_kwh' THEN
  FOR w IN SELECT DISTINCT a.window_start,a.window_end FROM assessment_revision a
   WHERE a.tenant_id=NEW.tenant_id AND a.site_id=NEW.site_id AND a.analytic_id='ev-session/1'
    AND a.window_start < coalesce(NEW.valid_to,'infinity'::timestamptz) AND NEW.valid_from < a.window_end LOOP
    PERFORM ev_consequence_enqueue(NEW.tenant_id,NEW.site_id,w.window_start,w.window_end,'TARIFF_REVISION',NEW.id);
  END LOOP;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER ev_consequence_dirty_tariff AFTER INSERT ON financial_assumption_revision FOR EACH ROW EXECUTE FUNCTION ev_consequence_on_tariff();
CREATE FUNCTION ev_consequence_on_source_gate() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE w record;
BEGIN
 IF NOT EXISTS (SELECT 1 FROM accepted_evidence e WHERE e.tenant_id=NEW.tenant_id
  AND e.site_id=NEW.site_id AND e.batch_id=NEW.batch_id
  AND ((e.family='EVENT' AND e.record_kind LIKE 'EV_%')
    OR (e.family='MEASUREMENT' AND e.measurement='INTERVAL_DELTA' AND e.connector_id IS NOT NULL))) THEN
  RETURN NEW;
 END IF;
 FOR w IN SELECT DISTINCT a.window_start,a.window_end FROM assessment_revision a
  WHERE a.tenant_id=NEW.tenant_id AND a.site_id=NEW.site_id AND a.analytic_id='ev-session/1' LOOP
  PERFORM ev_consequence_enqueue(NEW.tenant_id,NEW.site_id,w.window_start,w.window_end,'SOURCE_GATE',NEW.batch_id);
 END LOOP;
 RETURN NEW;
END $$;
CREATE TRIGGER ev_consequence_dirty_source_gate AFTER INSERT ON batch_publication_link FOR EACH ROW EXECUTE FUNCTION ev_consequence_on_source_gate();
CREATE FUNCTION ev_consequence_on_accepted() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE w record;
BEGIN
 IF (NEW.family='EVENT' AND NEW.record_kind LIKE 'EV_%')
    OR (NEW.family='MEASUREMENT' AND NEW.measurement='INTERVAL_DELTA' AND NEW.connector_id IS NOT NULL) THEN
  FOR w IN SELECT DISTINCT a.window_start,a.window_end FROM assessment_revision a
   WHERE a.tenant_id=NEW.tenant_id AND a.site_id=NEW.site_id AND a.analytic_id='ev-session/1'
    AND a.window_start<=NEW.source_time AND NEW.source_time<a.window_end LOOP
    PERFORM ev_consequence_enqueue(NEW.tenant_id,NEW.site_id,w.window_start,w.window_end,'ACCEPTED_EV',NEW.id);
  END LOOP;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER ev_consequence_dirty_accepted AFTER INSERT ON accepted_evidence FOR EACH ROW EXECUTE FUNCTION ev_consequence_on_accepted();
-- Existing 0025 windows receive work even if their session rows preceded this migration.
SELECT ev_consequence_enqueue(a.tenant_id,a.site_id,a.window_start,a.window_end,'BACKFILL',a.id)
FROM assessment_revision a WHERE a.analytic_id='ev-session/1';
"""

def upgrade() -> None:
    op.execute(SCHEMA)

def downgrade() -> None:
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM financial_assumption_revision WHERE assumption_key='ev_gross_tariff_per_kwh')
         OR EXISTS (SELECT 1 FROM financial_assumption_assignment WHERE assumption_key='ev_gross_tariff_per_kwh')
         OR EXISTS (SELECT 1 FROM ev_consequence_revision) OR EXISTS (SELECT 1 FROM ev_consequence_session)
         OR EXISTS (SELECT 1 FROM ev_consequence_evidence) OR EXISTS (SELECT 1 FROM ev_consequence_work)
         OR EXISTS (SELECT 1 FROM ev_consequence_work_attempt) THEN
        RAISE EXCEPTION 'Downgrade of 0026_w2_ev_money refused: EV tariff or consequence history exists';
      END IF;
    END $$;
    DROP TRIGGER ev_consequence_dirty_accepted ON accepted_evidence;
    DROP TRIGGER ev_consequence_dirty_source_gate ON batch_publication_link;
    DROP TRIGGER ev_consequence_dirty_tariff ON financial_assumption_revision;
    DROP TRIGGER ev_consequence_dirty_assessment ON assessment_revision;
    DROP TRIGGER ev_consequence_dirty_session ON ev_session_revision;
    DROP FUNCTION ev_consequence_on_accepted(); DROP FUNCTION ev_consequence_on_source_gate();
    DROP FUNCTION ev_consequence_on_tariff(); DROP FUNCTION ev_consequence_on_assessment();
    DROP FUNCTION ev_consequence_on_session();
    DROP FUNCTION ev_consequence_enqueue(uuid,uuid,timestamptz,timestamptz,text,uuid);
    DROP TABLE ev_consequence_work_attempt; DROP TABLE ev_consequence_work;
    DROP TABLE ev_consequence_evidence; DROP TABLE ev_consequence_session; DROP TABLE ev_consequence_revision;
    DROP FUNCTION ev_consequence_tariff_key();
    ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_ev_positive;
    ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_assumption_key_check;
    ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_unit_check;
    ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_assumption_key_check
      CHECK (assumption_key IN ('diesel_price_per_litre'));
    ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_unit_check
      CHECK (unit='currency/L');
    """)
