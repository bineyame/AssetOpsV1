"""W4-03 unit 1: mini-grid decisions (scenarios, alternatives, five-day opportunities) and their work links.

`.agent/W4-03-build-spec.md`: original "Migration `0030_w4_mini_decisions`" DDL, closure 1 catalog/lock paragraph,
closure 4 S3 (job reference), S4 (consolidated contract and exact names), S18 (head) and S19 (downgrade job/stage
refusal). Chains to `0029_w4_mini_depth`. No `known_at`, `finding`, W4-01 work or 0029 schema modification beyond
the one replaced Site-stage CHECK.

Catalog delta: ten tables, ten primary keys (`<table>_pkey`), 22 named UNIQUE constraints beyond the PKs, 20 named
foreign keys (19 tenant/Site-scoped plus the one ordinary, unscoped `mini_opportunity_selection_job_id_fk` to
`recompute_job(id)`, S3), five explicit indexes, ten `<table>_immutable` append-only triggers on the existing
`ledger_append_only()`, one shared `mini_decision_public_no_seq`, the replaced `schedule_site_head_stage_check`
admitting the tick's `OPPORTUNITY` stage after `MINI` (S1), three `schedule_site_head` integer counters
`opportunity_processed|deferred|failed` NOT NULL DEFAULT 0 (u1 PR-1), and the `mini_scenario_revision.narrative` text
column with `mini_scenario_revision_narrative_check` (u2 PR-2): 45 named CHECKs (u2b) on the ten new tables. `mini_opportunity_revision.source_job_id` is a validated
UUID column, not a foreign key. Relationship rules SQL cannot state (finding/revision pair, selected revision Site,
job tenant/Site/domain/study) are checked by `mini_decisions/store.py` in the writing transaction.

Downgrade takes ACCESS EXCLUSIVE locks on the ten tables in closure 1's child-to-parent order, then EXCLUSIVE on
`recompute_job` and `schedule_site_head`, and refuses (in this order) any decision row, any `mini_opportunity`
recompute job of any status, or an active `OPPORTUNITY` Site stage. Otherwise it restores the five-stage CHECK, drops
the three counter columns, then drops triggers, indexes, tables in that order and the sequence last. No cascade, no deletion, no relabelling.
"""

from alembic import op

revision = "0030_w4_mini_decisions"
down_revision = "0029_w4_mini_depth"
branch_labels = None
depends_on = None

#: Closure 1: the downgrade's exact child-to-parent lock, refusal and drop order.
TABLES = (
    "mini_decision_work_link", "mini_opportunity_scenario_link", "mini_opportunity_evidence",
    "mini_alternative_evidence", "mini_opportunity_selection", "mini_opportunity_revision",
    "mini_alternative_revision", "mini_scenario_revision", "mini_opportunity", "mini_scenario",
)
INDEXES = ("mini_scenario_site_order", "mini_alternative_selected", "mini_opportunity_head",
           "mini_decision_work_case", "mini_opportunity_scenario_order")
OPPORTUNITY_JOB_DOMAIN = "mini_opportunity"

# Authored metadata bounds follow the merged W4-01 work tables (0027): actor 1-128, grant 1-500, attestation
# 1-1000 non-blank characters; idempotency/create keys 8-128 characters; hashes are 64 lowercase hex.
def _authored(table: str) -> str:
    return f"""
 CONSTRAINT {table}_actor_kind_check CHECK (actor_kind IN ('SERVICE','USER')),
 CONSTRAINT {table}_actor_id_check CHECK (length(btrim(actor_id)) BETWEEN 1 AND 128),
 CONSTRAINT {table}_authorization_basis_check CHECK (length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 CONSTRAINT {table}_attestation_check CHECK (length(btrim(attestation)) BETWEEN 1 AND 1000),
 CONSTRAINT {table}_idempotency_key_check CHECK (length(idempotency_key) BETWEEN 8 AND 128),
 CONSTRAINT {table}_payload_sha256_check CHECK (payload_sha256 ~ '^[0-9a-f]{{64}}$'),"""


SCHEMA = f"""
CREATE SEQUENCE mini_decision_public_no_seq;
CREATE TABLE mini_scenario (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 public_no bigint NOT NULL DEFAULT nextval('mini_decision_public_no_seq'),
 create_key text NOT NULL, create_payload_sha256 text NOT NULL, create_actor_id text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT mini_scenario_pkey PRIMARY KEY (id),
 CONSTRAINT mini_scenario_create_key_check CHECK (length(create_key) BETWEEN 8 AND 128),
 CONSTRAINT mini_scenario_create_payload_sha256_check CHECK (create_payload_sha256 ~ '^[0-9a-f]{{64}}$'),
 CONSTRAINT mini_scenario_create_actor_id_check CHECK (length(btrim(create_actor_id)) BETWEEN 1 AND 128),
 CONSTRAINT mini_scenario_site_fk FOREIGN KEY (tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT mini_scenario_scope_uk UNIQUE (tenant_id,site_id,id),
 CONSTRAINT mini_scenario_public_no_uk UNIQUE (tenant_id,public_no),
 CONSTRAINT mini_scenario_create_key_uk UNIQUE (tenant_id,site_id,create_key)
);
CREATE TABLE mini_scenario_revision (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL, scenario_id uuid NOT NULL,
 revision_no integer NOT NULL, supersedes_revision_id uuid NULL,
 name text NOT NULL, kind text NOT NULL, narrative text NOT NULL,
 assumptions jsonb NOT NULL, pinned_mini_revision_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
 pinned_selection_hours jsonb NOT NULL DEFAULT '[]'::jsonb,
 calculation jsonb NOT NULL, correction_reason text NULL,
 actor_kind text NOT NULL, actor_id text NOT NULL, authorization_basis text NOT NULL, attestation text NOT NULL,
 idempotency_key text NOT NULL, payload_sha256 text NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT mini_scenario_revision_pkey PRIMARY KEY (id),
 CONSTRAINT mini_scenario_revision_revision_no_check CHECK (revision_no>0),
 CONSTRAINT mini_scenario_revision_name_check CHECK (length(btrim(name)) BETWEEN 1 AND 160),
 CONSTRAINT mini_scenario_revision_kind_check CHECK (kind IN ('STOP_SOC','PRODUCTIVE_LOAD','TARIFF_ONLY','OTHER')),
 CONSTRAINT mini_scenario_revision_narrative_check
   CHECK (length(btrim(narrative)) BETWEEN 1 AND 2000),
 CONSTRAINT mini_scenario_revision_correction_reason_check
   CHECK (correction_reason IS NULL OR length(btrim(correction_reason)) BETWEEN 1 AND 2000),
 CONSTRAINT mini_scenario_revision_chain_check
   CHECK ((revision_no=1 AND supersedes_revision_id IS NULL AND correction_reason IS NULL)
       OR (revision_no>1 AND supersedes_revision_id IS NOT NULL AND length(btrim(correction_reason))>0)),{_authored("mini_scenario_revision")}
 CONSTRAINT mini_scenario_revision_scenario_fk FOREIGN KEY (tenant_id,site_id,scenario_id)
   REFERENCES mini_scenario(tenant_id,site_id,id),
 CONSTRAINT mini_scenario_revision_previous_fk FOREIGN KEY (tenant_id,site_id,supersedes_revision_id)
   REFERENCES mini_scenario_revision(tenant_id,site_id,id),
 CONSTRAINT mini_scenario_revision_scope_uk UNIQUE (tenant_id,site_id,id),
 CONSTRAINT mini_scenario_revision_no_uk UNIQUE (scenario_id,revision_no),
 CONSTRAINT mini_scenario_revision_previous_uk UNIQUE (scenario_id,supersedes_revision_id),
 CONSTRAINT mini_scenario_revision_key_uk UNIQUE (scenario_id,idempotency_key)
);
CREATE INDEX mini_scenario_site_order ON mini_scenario_revision(tenant_id,site_id,recorded_at DESC,id);
CREATE TABLE mini_alternative_revision (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 finding_id uuid NOT NULL, finding_revision_id uuid NOT NULL,
 alternative_key text NOT NULL, version_no integer NOT NULL,
 supersedes_revision_id uuid NULL, rank smallint NOT NULL,
 explanation text NOT NULL, evidence_summary text NOT NULL,
 missing_evidence_reason text NULL, disposition text NOT NULL,
 reason text NOT NULL, actor_kind text NOT NULL, actor_id text NOT NULL, authorization_basis text NOT NULL,
 attestation text NOT NULL, idempotency_key text NOT NULL, payload_sha256 text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT mini_alternative_revision_pkey PRIMARY KEY (id),
 CONSTRAINT mini_alternative_revision_version_no_check CHECK (version_no>0),
 CONSTRAINT mini_alternative_revision_rank_check CHECK (rank BETWEEN 1 AND 3),
 CONSTRAINT mini_alternative_revision_rank_key_check
   CHECK ((alternative_key, rank) IN (('POLICY',1),('UNCERTAINTY',2),('CAPABILITY',3))),
 CONSTRAINT mini_alternative_revision_disposition_check
   CHECK (disposition IN ('PLAUSIBLE','CANNOT_EXCLUDE','INDETERMINATE','RULED_OUT')),
 CONSTRAINT mini_alternative_revision_explanation_check CHECK (length(btrim(explanation)) BETWEEN 1 AND 2000),
 CONSTRAINT mini_alternative_revision_evidence_summary_check
   CHECK (length(btrim(evidence_summary)) BETWEEN 1 AND 2000),
 CONSTRAINT mini_alternative_revision_missing_evidence_reason_check
   CHECK (missing_evidence_reason IS NULL OR length(btrim(missing_evidence_reason)) BETWEEN 1 AND 500),
 CONSTRAINT mini_alternative_revision_reason_check CHECK (length(btrim(reason)) BETWEEN 1 AND 2000),{_authored("mini_alternative_revision")}
 CONSTRAINT mini_alternative_revision_finding_fk FOREIGN KEY (tenant_id,site_id,finding_id)
   REFERENCES finding(tenant_id,site_id,id),
 CONSTRAINT mini_alternative_revision_finding_revision_fk FOREIGN KEY (tenant_id,site_id,finding_revision_id)
   REFERENCES finding_revision(tenant_id,site_id,id),
 CONSTRAINT mini_alternative_revision_previous_fk FOREIGN KEY (tenant_id,site_id,supersedes_revision_id)
   REFERENCES mini_alternative_revision(tenant_id,site_id,id),
 CONSTRAINT mini_alternative_revision_scope_uk UNIQUE (tenant_id,site_id,id),
 CONSTRAINT mini_alternative_revision_version_uk UNIQUE (finding_id,alternative_key,version_no),
 CONSTRAINT mini_alternative_revision_previous_uk UNIQUE (supersedes_revision_id),
 CONSTRAINT mini_alternative_revision_key_uk UNIQUE (finding_id,idempotency_key)
);
CREATE INDEX mini_alternative_selected
  ON mini_alternative_revision(tenant_id,site_id,finding_revision_id,rank,created_at,id);
CREATE TABLE mini_alternative_evidence (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, alternative_revision_id uuid NOT NULL, evidence_id uuid NOT NULL,
 CONSTRAINT mini_alternative_evidence_pkey PRIMARY KEY (alternative_revision_id,evidence_id),
 CONSTRAINT mini_alternative_evidence_revision_fk FOREIGN KEY (tenant_id,site_id,alternative_revision_id)
   REFERENCES mini_alternative_revision(tenant_id,site_id,id),
 CONSTRAINT mini_alternative_evidence_accepted_fk FOREIGN KEY (tenant_id,site_id,evidence_id)
   REFERENCES accepted_evidence(tenant_id,site_id,id)
);
CREATE TABLE mini_opportunity (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 public_no bigint NOT NULL DEFAULT nextval('mini_decision_public_no_seq'),
 first_day date NOT NULL, last_day date NOT NULL, model_version text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT mini_opportunity_pkey PRIMARY KEY (id),
 CONSTRAINT mini_opportunity_window_check CHECK (last_day>=first_day AND last_day-first_day BETWEEN 0 AND 4),
 CONSTRAINT mini_opportunity_site_fk FOREIGN KEY (tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT mini_opportunity_scope_uk UNIQUE (tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_public_no_uk UNIQUE (tenant_id,public_no),
 CONSTRAINT mini_opportunity_study_uk UNIQUE (tenant_id,site_id,first_day,last_day,model_version)
);
CREATE TABLE mini_opportunity_revision (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 opportunity_id uuid NOT NULL, revision_no integer NOT NULL,
 selected_hours jsonb NOT NULL, result jsonb NOT NULL, input_sha256 text NOT NULL,
 producer_id text NOT NULL, source_job_id uuid NULL, model_version text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT mini_opportunity_revision_pkey PRIMARY KEY (id),
 CONSTRAINT mini_opportunity_revision_revision_no_check CHECK (revision_no>0),
 CONSTRAINT mini_opportunity_revision_input_sha256_check CHECK (input_sha256 ~ '^sha256:[0-9a-f]{{64}}$'),
 CONSTRAINT mini_opportunity_revision_opportunity_fk FOREIGN KEY (tenant_id,site_id,opportunity_id)
   REFERENCES mini_opportunity(tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_revision_scope_uk UNIQUE (tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_revision_no_uk UNIQUE (opportunity_id,revision_no),
 CONSTRAINT mini_opportunity_revision_input_uk UNIQUE (opportunity_id,input_sha256)
);
CREATE TABLE mini_opportunity_evidence (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, opportunity_revision_id uuid NOT NULL, evidence_id uuid NOT NULL,
 CONSTRAINT mini_opportunity_evidence_pkey PRIMARY KEY (opportunity_revision_id,evidence_id),
 CONSTRAINT mini_opportunity_evidence_revision_fk FOREIGN KEY (tenant_id,site_id,opportunity_revision_id)
   REFERENCES mini_opportunity_revision(tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_evidence_accepted_fk FOREIGN KEY (tenant_id,site_id,evidence_id)
   REFERENCES accepted_evidence(tenant_id,site_id,id)
);
CREATE TABLE mini_opportunity_selection (
 seq bigint GENERATED ALWAYS AS IDENTITY,
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, opportunity_id uuid NOT NULL,
 revision_id uuid NOT NULL, job_id uuid NULL, selected_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT mini_opportunity_selection_pkey PRIMARY KEY (seq),
 CONSTRAINT mini_opportunity_selection_opportunity_fk FOREIGN KEY (tenant_id,site_id,opportunity_id)
   REFERENCES mini_opportunity(tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_selection_revision_fk FOREIGN KEY (tenant_id,site_id,revision_id)
   REFERENCES mini_opportunity_revision(tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_selection_job_id_fk FOREIGN KEY (job_id) REFERENCES recompute_job(id)
);
CREATE INDEX mini_opportunity_head
  ON mini_opportunity_selection(tenant_id,site_id,opportunity_id,selected_at DESC,seq DESC);
CREATE TABLE mini_decision_work_link (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 case_id uuid NOT NULL, scenario_id uuid NULL, opportunity_id uuid NULL,
 actor_kind text NOT NULL, actor_id text NOT NULL, authorization_basis text NOT NULL, attestation text NOT NULL,
 idempotency_key text NOT NULL, payload_sha256 text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT mini_decision_work_link_pkey PRIMARY KEY (id),
 CONSTRAINT mini_decision_work_link_target_check CHECK ((scenario_id IS NULL) <> (opportunity_id IS NULL)),{_authored("mini_decision_work_link")}
 CONSTRAINT mini_decision_work_link_case_fk FOREIGN KEY (tenant_id,site_id,case_id)
   REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT mini_decision_work_link_scenario_fk FOREIGN KEY (tenant_id,site_id,scenario_id)
   REFERENCES mini_scenario(tenant_id,site_id,id),
 CONSTRAINT mini_decision_work_link_opportunity_fk FOREIGN KEY (tenant_id,site_id,opportunity_id)
   REFERENCES mini_opportunity(tenant_id,site_id,id),
 CONSTRAINT mini_decision_work_link_case_scenario_uk UNIQUE (case_id,scenario_id),
 CONSTRAINT mini_decision_work_link_case_opportunity_uk UNIQUE (case_id,opportunity_id),
 CONSTRAINT mini_decision_work_link_key_uk UNIQUE (tenant_id,site_id,idempotency_key)
);
CREATE INDEX mini_decision_work_case ON mini_decision_work_link(tenant_id,site_id,case_id,created_at,id);
CREATE TABLE mini_opportunity_scenario_link (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 opportunity_id uuid NOT NULL, scenario_id uuid NOT NULL,
 actor_kind text NOT NULL, actor_id text NOT NULL, authorization_basis text NOT NULL, attestation text NOT NULL,
 idempotency_key text NOT NULL, payload_sha256 text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT mini_opportunity_scenario_link_pkey PRIMARY KEY (id),{_authored("mini_opportunity_scenario_link")}
 CONSTRAINT mini_opportunity_scenario_link_opportunity_fk FOREIGN KEY (tenant_id,site_id,opportunity_id)
   REFERENCES mini_opportunity(tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_scenario_link_scenario_fk FOREIGN KEY (tenant_id,site_id,scenario_id)
   REFERENCES mini_scenario(tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_scenario_link_scope_uk UNIQUE (tenant_id,site_id,id),
 CONSTRAINT mini_opportunity_scenario_link_key_uk UNIQUE (tenant_id,site_id,idempotency_key)
);
CREATE INDEX mini_opportunity_scenario_order
  ON mini_opportunity_scenario_link(tenant_id,site_id,opportunity_id,created_at DESC,id);
""" + "".join(
    f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON {t}\n"
    "    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n" for t in reversed(TABLES)
) + """
ALTER TABLE schedule_site_head DROP CONSTRAINT schedule_site_head_stage_check;
ALTER TABLE schedule_site_head ADD CONSTRAINT schedule_site_head_stage_check
  CHECK (stage IN ('IDLE', 'S3', 'MINI', 'OPPORTUNITY', 'S4', 'CONSEQUENCE'));
ALTER TABLE schedule_site_head
  ADD COLUMN opportunity_processed integer NOT NULL DEFAULT 0,
  ADD COLUMN opportunity_deferred integer NOT NULL DEFAULT 0,
  ADD COLUMN opportunity_failed integer NOT NULL DEFAULT 0;
"""

REFUSE_IF_USED = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "LOCK TABLE recompute_job IN EXCLUSIVE MODE;\n"
    "LOCK TABLE schedule_site_head IN EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF "
    + "\n       OR ".join(f"EXISTS (SELECT 1 FROM {t})" for t in TABLES)
    + " THEN\n        RAISE EXCEPTION 'Downgrade of 0030_w4_mini_decisions refused: decision history exists';\n"
    f"    END IF;\n    IF EXISTS (SELECT 1 FROM recompute_job WHERE domain = '{OPPORTUNITY_JOB_DOMAIN}') THEN\n"
    "        RAISE EXCEPTION 'Downgrade of 0030_w4_mini_decisions refused: opportunity jobs exist';\n"
    "    END IF;\n    IF EXISTS (SELECT 1 FROM schedule_site_head WHERE stage = 'OPPORTUNITY') THEN\n"
    "        RAISE EXCEPTION 'Downgrade of 0030_w4_mini_decisions refused: OPPORTUNITY stage active';\n"
    "    END IF;\nEND;\n$$;\n"
)

DROP = (
    "ALTER TABLE schedule_site_head DROP CONSTRAINT schedule_site_head_stage_check;\n"
    "ALTER TABLE schedule_site_head ADD CONSTRAINT schedule_site_head_stage_check\n"
    "  CHECK (stage IN ('IDLE', 'S3', 'MINI', 'S4', 'CONSEQUENCE'));\n"
    "ALTER TABLE schedule_site_head\n"
    "  DROP COLUMN opportunity_processed,\n"
    "  DROP COLUMN opportunity_deferred,\n"
    "  DROP COLUMN opportunity_failed;\n"
    + "".join(f"DROP TRIGGER {t}_immutable ON {t};\n" for t in TABLES)
    + "".join(f"DROP INDEX {i};\n" for i in INDEXES)
    + "".join(f"DROP TABLE {t};\n" for t in TABLES)
    + "DROP SEQUENCE mini_decision_public_no_seq;\n"
)


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DROP)
