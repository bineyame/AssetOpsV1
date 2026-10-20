"""W4-01: immutable authored work identities and history."""
from alembic import op
from sqlalchemy import text

revision = "0027_w4_work_cases"
down_revision = "0026_w2_ev_money"
branch_labels = None
depends_on = None

SCHEMA = r"""
CREATE SEQUENCE work_public_no_seq AS bigint START 1 NO CYCLE;
CREATE TABLE work_case (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 kind text NOT NULL CHECK (kind IN ('INCIDENT','MAINTENANCE_REQUEST')),
 public_no bigint NOT NULL UNIQUE CHECK (public_no>0),
 public_code text NOT NULL CHECK ((kind='INCIDENT' AND public_code ~ '^INC-[0-9]{6,}$') OR
                                  (kind='MAINTENANCE_REQUEST' AND public_code ~ '^WR-[0-9]{6,}$')),
 asset_id uuid NULL,
 occurred_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_kind text NOT NULL CHECK (actor_kind IN ('USER','SERVICE')),
 actor_id text NOT NULL CHECK (length(btrim(actor_id)) BETWEEN 1 AND 128),
 authorization_basis text NOT NULL CHECK (length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK (length(btrim(attestation)) BETWEEN 1 AND 1000),
 create_key text NOT NULL CHECK (length(create_key) BETWEEN 8 AND 128),
 create_payload_sha256 text NOT NULL CHECK(create_payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT work_case_site_fk FOREIGN KEY(tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT work_case_asset_fk FOREIGN KEY(tenant_id,site_id,asset_id) REFERENCES asset(tenant_id,site_id,id),
 CONSTRAINT work_case_scope UNIQUE(tenant_id,site_id,id),
 CONSTRAINT work_case_kind_scope UNIQUE(tenant_id,site_id,id,kind),
 CONSTRAINT work_case_code UNIQUE(tenant_id,public_code),
 CONSTRAINT work_case_create_once UNIQUE(tenant_id,site_id,create_key)
);
CREATE INDEX work_case_site_window ON work_case(tenant_id,site_id,occurred_at DESC,id);
CREATE INDEX work_case_site_kind ON work_case(tenant_id,site_id,kind,created_at DESC,id);
CREATE TABLE incident (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, id uuid NOT NULL,
 kind text NOT NULL DEFAULT 'INCIDENT' CHECK(kind='INCIDENT'),
 incident_key text NOT NULL CHECK(length(btrim(incident_key)) BETWEEN 8 AND 128),
 PRIMARY KEY(tenant_id,site_id,id),
 CONSTRAINT incident_case_fk FOREIGN KEY(tenant_id,site_id,id,kind) REFERENCES work_case(tenant_id,site_id,id,kind),
 CONSTRAINT incident_key_once UNIQUE(tenant_id,site_id,incident_key)
);
CREATE TABLE maintenance_work_request (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, id uuid NOT NULL,
 kind text NOT NULL DEFAULT 'MAINTENANCE_REQUEST' CHECK(kind='MAINTENANCE_REQUEST'),
 request_key text NOT NULL CHECK(length(btrim(request_key)) BETWEEN 8 AND 128),
 incident_id uuid NULL,
 PRIMARY KEY(tenant_id,site_id,id),
 CONSTRAINT maintenance_request_case_fk FOREIGN KEY(tenant_id,site_id,id,kind) REFERENCES work_case(tenant_id,site_id,id,kind),
 CONSTRAINT maintenance_request_incident_fk FOREIGN KEY(tenant_id,site_id,incident_id) REFERENCES incident(tenant_id,site_id,id),
 CONSTRAINT maintenance_request_key_once UNIQUE(tenant_id,site_id,request_key)
);
CREATE TABLE work_case_revision (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_id uuid NOT NULL,
 revision_no integer NOT NULL CHECK(revision_no>0), supersedes_revision_id uuid NULL,
 title text NOT NULL CHECK(length(btrim(title)) BETWEEN 1 AND 200),
 narrative text NOT NULL CHECK(length(btrim(narrative)) BETWEEN 1 AND 4000),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 occurred_at timestamptz NOT NULL,
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 reason text NULL CHECK(reason IS NULL OR length(btrim(reason)) BETWEEN 1 AND 500),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT work_revision_case_fk FOREIGN KEY(tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT work_revision_prev_fk FOREIGN KEY(case_id,supersedes_revision_id) REFERENCES work_case_revision(case_id,id),
 CONSTRAINT work_revision_number UNIQUE(case_id,revision_no),
 CONSTRAINT work_revision_once UNIQUE(case_id,idempotency_key),
 CONSTRAINT work_revision_one_successor UNIQUE(supersedes_revision_id),
 CONSTRAINT work_revision_case_id UNIQUE(case_id,id),
 CONSTRAINT work_revision_scope UNIQUE(tenant_id,site_id,id)
);
CREATE INDEX work_revision_head ON work_case_revision(case_id,revision_no DESC);
CREATE TABLE work_case_finding_link (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_revision_id uuid NOT NULL,
 finding_id uuid NOT NULL, finding_revision_id uuid NOT NULL,
 PRIMARY KEY(case_revision_id,finding_id,finding_revision_id),
 CONSTRAINT work_finding_case_fk FOREIGN KEY(tenant_id,site_id,case_revision_id) REFERENCES work_case_revision(tenant_id,site_id,id),
 CONSTRAINT work_finding_revision_fk FOREIGN KEY(tenant_id,site_id,finding_id,finding_revision_id) REFERENCES finding_revision(tenant_id,site_id,finding_id,id)
);
CREATE TABLE work_case_action_link (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_revision_id uuid NOT NULL,
 action_id uuid NOT NULL, action_event_id uuid NOT NULL,
 PRIMARY KEY(case_revision_id,action_id,action_event_id),
 CONSTRAINT work_action_case_fk FOREIGN KEY(tenant_id,site_id,case_revision_id) REFERENCES work_case_revision(tenant_id,site_id,id),
 CONSTRAINT work_action_fk FOREIGN KEY(tenant_id,site_id,action_id) REFERENCES action(tenant_id,site_id,id),
 CONSTRAINT work_action_event_fk FOREIGN KEY(tenant_id,site_id,action_event_id) REFERENCES action_event(tenant_id,site_id,id)
);
CREATE TABLE work_case_evidence (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_revision_id uuid NOT NULL,
 evidence_id uuid NOT NULL,
 PRIMARY KEY(case_revision_id,evidence_id),
 CONSTRAINT work_case_evidence_revision_fk FOREIGN KEY(tenant_id,site_id,case_revision_id)
   REFERENCES work_case_revision(tenant_id,site_id,id),
 CONSTRAINT work_case_evidence_accepted_fk FOREIGN KEY(tenant_id,site_id,evidence_id)
   REFERENCES accepted_evidence(tenant_id,site_id,id)
);
CREATE TABLE work_event (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_id uuid NOT NULL,
 kind text NOT NULL CHECK(kind IN ('CREATED','ASSIGN','CLOSE','REOPEN','CANCEL','COMPLETE','OPEN_VERIFICATION','COMMENT')),
 payload jsonb NOT NULL DEFAULT '{}'::jsonb,
 occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT work_event_case_fk FOREIGN KEY(tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT work_event_once UNIQUE(case_id,idempotency_key),
 CONSTRAINT work_event_scope UNIQUE(tenant_id,site_id,id)
);
CREATE INDEX work_event_order ON work_event(case_id,recorded_at,id);
CREATE TABLE maintenance_plan (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, asset_id uuid NULL,
 public_no bigint NOT NULL UNIQUE CHECK(public_no>0),
 public_code text NOT NULL CHECK(public_code ~ '^PM-[0-9]{6,}$'),
 canonical_plan_id uuid NOT NULL,
 title text NOT NULL CHECK(length(btrim(title)) BETWEEN 1 AND 200),
 trigger_kind text NOT NULL CHECK(trigger_kind IN ('CALENDAR','RUN_HOURS')),
 next_due_at timestamptz NULL, next_due_hours numeric NULL,
 state text NOT NULL CHECK(state IN ('DRAFT','ACTIVE','PAUSED','CANCELLED')),
 supersedes_plan_id uuid NULL, actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 occurred_at timestamptz NOT NULL, correction_reason text NULL CHECK(correction_reason IS NULL OR length(btrim(correction_reason)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT maintenance_plan_site_fk FOREIGN KEY(tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT maintenance_plan_asset_fk FOREIGN KEY(tenant_id,site_id,asset_id) REFERENCES asset(tenant_id,site_id,id),
 CONSTRAINT maintenance_plan_prev_fk FOREIGN KEY(tenant_id,site_id,supersedes_plan_id) REFERENCES maintenance_plan(tenant_id,site_id,id),
 CONSTRAINT maintenance_plan_canonical_fk FOREIGN KEY(tenant_id,site_id,canonical_plan_id) REFERENCES maintenance_plan(tenant_id,site_id,id),
 CONSTRAINT maintenance_plan_root CHECK((supersedes_plan_id IS NULL AND canonical_plan_id=id) OR supersedes_plan_id IS NOT NULL),
 CONSTRAINT maintenance_plan_due CHECK ((trigger_kind='CALENDAR' AND next_due_hours IS NULL) OR (trigger_kind='RUN_HOURS' AND next_due_at IS NULL AND (next_due_hours IS NULL OR next_due_hours>=0))),
 CONSTRAINT maintenance_plan_scope UNIQUE(tenant_id,site_id,id),
 CONSTRAINT maintenance_plan_code UNIQUE(tenant_id,public_code),
 CONSTRAINT maintenance_plan_once UNIQUE(tenant_id,site_id,idempotency_key),
 CONSTRAINT maintenance_plan_one_successor UNIQUE(supersedes_plan_id)
);
CREATE INDEX maintenance_plan_site ON maintenance_plan(tenant_id,site_id,recorded_at DESC,id);
CREATE TABLE maintenance_record (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_id uuid NOT NULL,
 supersedes_record_id uuid NULL, activity text NOT NULL CHECK(length(btrim(activity)) BETWEEN 1 AND 4000),
 outcome_note text NULL CHECK(outcome_note IS NULL OR length(btrim(outcome_note)) BETWEEN 1 AND 2000),
 occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT maintenance_record_case_fk FOREIGN KEY(tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT maintenance_record_prev_fk FOREIGN KEY(tenant_id,site_id,supersedes_record_id) REFERENCES maintenance_record(tenant_id,site_id,id),
 CONSTRAINT maintenance_record_scope UNIQUE(tenant_id,site_id,id),
 CONSTRAINT maintenance_record_once UNIQUE(case_id,idempotency_key),
 CONSTRAINT maintenance_record_one_successor UNIQUE(supersedes_record_id)
);
CREATE INDEX maintenance_record_case ON maintenance_record(case_id,recorded_at DESC,id);
CREATE TABLE operational_record (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 public_no bigint NOT NULL UNIQUE CHECK(public_no>0),
 public_code text NOT NULL CHECK(public_code ~ '^REC-[0-9]{6,}$'),
 canonical_record_id uuid NOT NULL,
 kind text NOT NULL CHECK(kind IN ('OPERATOR_LOG','MANUAL_READING','SHIFT_NOTE','SITE_VISIT')),
 body text NOT NULL CHECK(length(btrim(body)) BETWEEN 1 AND 4000),
 period_end timestamptz NULL, unit text NULL CHECK(unit IS NULL OR length(btrim(unit)) BETWEEN 1 AND 32),
 quantity numeric NULL CHECK(quantity IS NULL OR (quantity >= 0 AND quantity < 'Infinity'::numeric)),
 source_document_sha256 text NULL CHECK(source_document_sha256 IS NULL OR source_document_sha256 ~ '^[0-9a-f]{64}$'),
 correction_reason text NULL CHECK(correction_reason IS NULL OR length(btrim(correction_reason)) BETWEEN 1 AND 500),
 state text NOT NULL CHECK(state IN ('SUBMITTED','ACCEPTED','REJECTED')),
 supersedes_record_id uuid NULL, case_id uuid NULL,
 occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT operational_record_site_fk FOREIGN KEY(tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT operational_record_case_fk FOREIGN KEY(tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT operational_record_prev_fk FOREIGN KEY(tenant_id,site_id,supersedes_record_id) REFERENCES operational_record(tenant_id,site_id,id),
 CONSTRAINT operational_record_canonical_fk FOREIGN KEY(tenant_id,site_id,canonical_record_id) REFERENCES operational_record(tenant_id,site_id,id),
 CONSTRAINT operational_record_root CHECK((supersedes_record_id IS NULL AND canonical_record_id=id) OR supersedes_record_id IS NOT NULL),
 CONSTRAINT operational_record_period CHECK(period_end IS NULL OR period_end >= occurred_at),
 CONSTRAINT operational_record_quantity CHECK((quantity IS NULL)=(unit IS NULL)),
 CONSTRAINT operational_record_scope UNIQUE(tenant_id,site_id,id),
 CONSTRAINT operational_record_code UNIQUE(tenant_id,public_code),
 CONSTRAINT operational_record_once UNIQUE(tenant_id,site_id,idempotency_key),
 CONSTRAINT operational_record_one_successor UNIQUE(supersedes_record_id)
);
CREATE INDEX operational_record_site ON operational_record(tenant_id,site_id,occurred_at DESC,id);
CREATE FUNCTION w4_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'W4 work history is append only' USING ERRCODE='23514'; END $$;
CREATE TRIGGER work_case_immutable BEFORE UPDATE OR DELETE ON work_case FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER incident_immutable BEFORE UPDATE OR DELETE ON incident FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER maintenance_work_request_immutable BEFORE UPDATE OR DELETE ON maintenance_work_request FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_case_finding_link_immutable BEFORE UPDATE OR DELETE ON work_case_finding_link FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_case_action_link_immutable BEFORE UPDATE OR DELETE ON work_case_action_link FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_revision_immutable BEFORE UPDATE OR DELETE ON work_case_revision FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_case_evidence_immutable BEFORE UPDATE OR DELETE ON work_case_evidence FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_event_immutable BEFORE UPDATE OR DELETE ON work_event FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER maintenance_plan_immutable BEFORE UPDATE OR DELETE ON maintenance_plan FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER maintenance_record_immutable BEFORE UPDATE OR DELETE ON maintenance_record FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER operational_record_immutable BEFORE UPDATE OR DELETE ON operational_record FOR EACH ROW EXECUTE FUNCTION w4_append_only();
"""

def upgrade():
    op.execute(SCHEMA)

def downgrade():
    bind = op.get_bind()
    for table in ("operational_record", "maintenance_record", "maintenance_plan", "work_event", "work_case_evidence", "work_case_action_link", "work_case_finding_link", "work_case_revision", "maintenance_work_request", "incident", "work_case"):
        if bind.execute(text(f"SELECT 1 FROM {table} LIMIT 1")).first():
            raise RuntimeError("0027 downgrade requires empty W4 work tables")
    for table in ("operational_record", "maintenance_record", "maintenance_plan", "work_event", "work_case_evidence", "work_case_action_link", "work_case_finding_link", "work_case_revision", "maintenance_work_request", "incident", "work_case"):
        op.execute(f"DROP TABLE {table}")
    op.execute("DROP FUNCTION w4_append_only()")
    op.execute("DROP SEQUENCE work_public_no_seq")
