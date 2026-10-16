"""S6-02a: frozen `reserve-trial-verification-1` plans, selection bindings, evaluation and outcome rows.

`D-2026-10-16-s6-verification` and `D-2026-10-16-s602-questions`. Every new table is Action-owned, insert-only
(the 0005 `ledger_append_only` trigger) and written only by the ninth writer
`actions/adapters/postgres_action_store.py` (rule 8 of `tools/checks/configuration-persistence.ps1`).

- `verification_plan`: one immutable plan revision per freeze. A replacement is a new row naming
  `supersedes_plan_id` (each plan is superseded at most once). Both windows are half-open 60-minute UTC windows
  aligned to five-minute boundaries, at the same UTC clock time, baseline wholly before the later window.
- `verification_selection_binding`: the later window's selected UTC-day `dispatch-3` revision IDs, appended
  before evaluation; a changed selection is a new row.
- `verification_evaluation_request`, `verification_outcome`, `verification_metric`: phase 2 evaluator rows.
  Outcome values are VERIFIED / INEFFECTIVE / INCONCLUSIVE only (PENDING and REASSESSMENT_PENDING are read
  states, never stored outcomes); GUARDRAIL_FAIL is a reason.
- `action_event` gains RESOLVED and RESOLUTION_WITHDRAWN, appended only by the evaluator SYSTEM job (command
  EVALUATE, channel SYSTEM_JOB, actor `service:verification-evaluator`, basis SYSTEM_VERIFICATION_EVALUATOR,
  non-null `triggering_job`), each citing its plan and outcome.

Revision ID: 0019_verification_core
Revises: 0018_finding_match_deferral
Create Date: 2026-10-16
"""

from __future__ import annotations

from alembic import op

revision = "0019_verification_core"
down_revision = "0018_finding_match_deferral"
branch_labels = None
depends_on = None

SHA = "CHECK ({} ~ '^[0-9a-f]{{64}}$')"
KEY = "CHECK (length({}) BETWEEN 8 AND 128)"
# The S6-01 SYSTEM demonstration actor columns a freeze or evaluation request carries.
DEMO_ACTOR = """
    actor_kind text NOT NULL CHECK (actor_kind = 'SYSTEM'),
    actor_id text NOT NULL CHECK (actor_id ~ '^service:[a-z0-9-]+$'),
    source_channel text NOT NULL CHECK (source_channel = 'SYSTEM_DEMONSTRATION_API'),
    authorization_basis text NOT NULL CHECK (length(authorization_basis) BETWEEN 1 AND 500),
    triggering_service text NOT NULL CHECK (length(triggering_service) BETWEEN 1 AND 128),
    triggering_fixture text NOT NULL CHECK (length(triggering_fixture) BETWEEN 1 AND 128),"""
# Half-open 60-minute UTC window aligned to five-minute boundaries.
WINDOW = ("CHECK ({0}_end - {0}_start = interval '60 minutes' "
          "AND mod(extract(epoch FROM {0}_start)::numeric, 300) = 0)")

SCHEMA = f"""
CREATE TABLE verification_plan (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    action_id uuid NOT NULL,
    plan_version text NOT NULL CHECK (plan_version = 'reserve-trial-verification-1'),
    supersedes_plan_id uuid NULL,
    origin_finding_revision_id uuid NOT NULL,
    applied_event_id uuid NOT NULL,
    change_id uuid NOT NULL,
    old_foundation_revision_id uuid NOT NULL,
    new_foundation_revision_id uuid NOT NULL,
    battery_asset_id uuid NOT NULL,
    field text NOT NULL CHECK (field = 'reserve-state-of-charge'),
    rule_id text NOT NULL CHECK (rule_id = 'reserve-trial-1'),
    effective_from timestamptz NOT NULL,
    baseline_start timestamptz NOT NULL,
    baseline_end timestamptz NOT NULL,
    later_start timestamptz NOT NULL,
    later_end timestamptz NOT NULL,
    baseline_candidate_seconds integer NOT NULL CHECK (baseline_candidate_seconds > 0),
    baseline_selection jsonb NOT NULL,
    baseline_evidence_ids jsonb NOT NULL,
    basis jsonb NOT NULL,
    target jsonb NOT NULL,
    guardrails jsonb NOT NULL,
    bands jsonb NOT NULL,
    coverage jsonb NOT NULL,
    later_selection_rule jsonb NOT NULL,
    plan_sha256 text NOT NULL {SHA.format('plan_sha256')},
    {DEMO_ACTOR}
    idempotency_key text NOT NULL {KEY.format('idempotency_key')},
    payload jsonb NOT NULL,
    payload_sha256 text NOT NULL {SHA.format('payload_sha256')},
    recorded_at timestamptz NOT NULL,
    CONSTRAINT verification_plan_baseline_window {WINDOW.format('baseline')},
    CONSTRAINT verification_plan_later_window {WINDOW.format('later')},
    CONSTRAINT verification_plan_window_order CHECK (
        baseline_end <= effective_from AND later_start >= effective_from),
    CONSTRAINT verification_plan_same_clock CHECK (
        mod(extract(epoch FROM baseline_start)::numeric, 86400) = mod(extract(epoch FROM later_start)::numeric, 86400)),
    CONSTRAINT verification_plan_not_self CHECK (supersedes_plan_id IS NULL OR supersedes_plan_id <> id),
    CONSTRAINT verification_plan_action_fk FOREIGN KEY (tenant_id, site_id, action_id)
        REFERENCES action(tenant_id, site_id, id),
    CONSTRAINT verification_plan_finding_revision_fk FOREIGN KEY (tenant_id, site_id, origin_finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT verification_plan_applied_fk FOREIGN KEY (action_id, applied_event_id)
        REFERENCES action_event(action_id, id),
    CONSTRAINT verification_plan_change_fk FOREIGN KEY (tenant_id, site_id, change_id)
        REFERENCES action_policy_change(tenant_id, site_id, id),
    CONSTRAINT verification_plan_old_foundation_fk FOREIGN KEY (tenant_id, site_id, old_foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT verification_plan_new_foundation_fk FOREIGN KEY (tenant_id, site_id, new_foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT verification_plan_asset_fk FOREIGN KEY (tenant_id, site_id, battery_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT verification_plan_action_unique UNIQUE (action_id, id),
    CONSTRAINT verification_plan_site_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT verification_plan_idempotency_unique UNIQUE (action_id, idempotency_key),
    CONSTRAINT verification_plan_supersedes_once UNIQUE (supersedes_plan_id),
    CONSTRAINT verification_plan_supersedes_fk FOREIGN KEY (action_id, supersedes_plan_id)
        REFERENCES verification_plan(action_id, id)
);
CREATE UNIQUE INDEX verification_plan_one_root ON verification_plan (action_id) WHERE supersedes_plan_id IS NULL;
CREATE INDEX verification_plan_order ON verification_plan (action_id, recorded_at, id);

CREATE TABLE verification_selection_binding (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    plan_id uuid NOT NULL,
    window_name text NOT NULL CHECK (window_name = 'LATER'),
    selection jsonb NOT NULL,
    selection_sha256 text NOT NULL {SHA.format('selection_sha256')},
    actor_kind text NOT NULL CHECK (actor_kind = 'SYSTEM'),
    actor_id text NOT NULL CHECK (actor_id ~ '^service:[a-z0-9-]+$'),
    triggering_service text NOT NULL CHECK (length(triggering_service) BETWEEN 1 AND 128),
    triggering_job text NULL CHECK (triggering_job IS NULL OR length(triggering_job) BETWEEN 1 AND 128),
    triggering_fixture text NOT NULL CHECK (length(triggering_fixture) BETWEEN 1 AND 128),
    idempotency_key text NOT NULL {KEY.format('idempotency_key')},
    payload_sha256 text NOT NULL {SHA.format('payload_sha256')},
    recorded_at timestamptz NOT NULL,
    CONSTRAINT verification_selection_binding_idempotency_unique UNIQUE (plan_id, idempotency_key),
    CONSTRAINT verification_selection_binding_plan_fk FOREIGN KEY (tenant_id, site_id, plan_id)
        REFERENCES verification_plan(tenant_id, site_id, id),
    CONSTRAINT verification_selection_binding_site_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT verification_selection_binding_plan_unique UNIQUE (plan_id, id)
);
CREATE INDEX verification_selection_binding_order ON verification_selection_binding (plan_id, recorded_at, id);

CREATE TABLE verification_evaluation_request (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    action_id uuid NOT NULL,
    plan_id uuid NOT NULL,
    {DEMO_ACTOR}
    idempotency_key text NOT NULL {KEY.format('idempotency_key')},
    payload jsonb NOT NULL,
    payload_sha256 text NOT NULL {SHA.format('payload_sha256')},
    recorded_at timestamptz NOT NULL,
    CONSTRAINT verification_evaluation_request_plan_fk FOREIGN KEY (action_id, plan_id)
        REFERENCES verification_plan(action_id, id),
    CONSTRAINT verification_evaluation_request_site_fk FOREIGN KEY (tenant_id, site_id, plan_id)
        REFERENCES verification_plan(tenant_id, site_id, id),
    CONSTRAINT verification_evaluation_request_site_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT verification_evaluation_request_idempotency_unique UNIQUE (plan_id, idempotency_key)
);

CREATE TABLE verification_outcome (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    action_id uuid NOT NULL,
    plan_id uuid NOT NULL,
    selection_binding_id uuid NULL,
    evaluation_request_id uuid NULL,
    supersedes_outcome_id uuid NULL,
    outcome text NOT NULL CHECK (outcome IN ('VERIFIED','INEFFECTIVE','INCONCLUSIVE')),
    reasons text[] NOT NULL,
    basis jsonb NOT NULL,
    basis_sha256 text NOT NULL {SHA.format('basis_sha256')},
    details jsonb NOT NULL,
    actor_kind text NOT NULL CHECK (actor_kind = 'SYSTEM'),
    actor_id text NOT NULL CHECK (actor_id = 'service:verification-evaluator'),
    triggering_job text NOT NULL CHECK (length(triggering_job) BETWEEN 1 AND 128),
    idempotency_key text NOT NULL {KEY.format('idempotency_key')},
    recorded_at timestamptz NOT NULL,
    CONSTRAINT verification_outcome_guardrail_reason CHECK (
        NOT ('GUARDRAIL_FAIL' = ANY (reasons)) OR outcome = 'INEFFECTIVE'),
    CONSTRAINT verification_outcome_plan_fk FOREIGN KEY (action_id, plan_id)
        REFERENCES verification_plan(action_id, id),
    CONSTRAINT verification_outcome_site_fk FOREIGN KEY (tenant_id, site_id, plan_id)
        REFERENCES verification_plan(tenant_id, site_id, id),
    CONSTRAINT verification_outcome_binding_fk FOREIGN KEY (plan_id, selection_binding_id)
        REFERENCES verification_selection_binding(plan_id, id),
    CONSTRAINT verification_outcome_request_fk FOREIGN KEY (tenant_id, site_id, evaluation_request_id)
        REFERENCES verification_evaluation_request(tenant_id, site_id, id),
    CONSTRAINT verification_outcome_site_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT verification_outcome_action_unique UNIQUE (action_id, id),
    CONSTRAINT verification_outcome_idempotency_unique UNIQUE (plan_id, idempotency_key),
    CONSTRAINT verification_outcome_supersedes_once UNIQUE (supersedes_outcome_id),
    CONSTRAINT verification_outcome_supersedes_fk FOREIGN KEY (action_id, supersedes_outcome_id)
        REFERENCES verification_outcome(action_id, id)
);
CREATE INDEX verification_outcome_order ON verification_outcome (action_id, recorded_at, id);

CREATE TABLE verification_metric (
    outcome_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    metric_key text NOT NULL CHECK (metric_key ~ '^[a-z][a-z0-9_]{{2,63}}$'),
    window_name text NOT NULL CHECK (window_name IN ('BASELINE','LATER','COMPARISON')),
    state text NOT NULL CHECK (state IN ('PASS','FAIL','UNKNOWN')),
    value_text text NULL,
    threshold_text text NULL,
    unit text NULL,
    reason text NULL,
    evidence_ids jsonb NOT NULL,
    PRIMARY KEY (outcome_id, metric_key, window_name),
    CONSTRAINT verification_metric_outcome_fk FOREIGN KEY (tenant_id, site_id, outcome_id)
        REFERENCES verification_outcome(tenant_id, site_id, id)
);

ALTER TABLE action_event
    ADD COLUMN verification_plan_id uuid NULL,
    ADD COLUMN verification_outcome_id uuid NULL,
    DROP CONSTRAINT action_event_kind_check,
    DROP CONSTRAINT action_event_source_channel_check,
    DROP CONSTRAINT action_event_triggering_command_check,
    DROP CONSTRAINT action_event_command,
    ADD CONSTRAINT action_event_kind_check CHECK (
        kind IN ('ACCEPTED','APPLIED','FAILED','OBSERVED','RESOLVED','RESOLUTION_WITHDRAWN')),
    ADD CONSTRAINT action_event_source_channel_check CHECK (
        source_channel IN ('SYSTEM_DEMONSTRATION_API','SYSTEM_JOB')),
    ADD CONSTRAINT action_event_triggering_command_check CHECK (
        triggering_command IN ('ACCEPT','APPLY','OBSERVE','EVALUATE')),
    ADD CONSTRAINT action_event_command CHECK (
        (kind = 'ACCEPTED' AND triggering_command = 'ACCEPT') OR (kind IN ('APPLIED','FAILED') AND triggering_command = 'APPLY')
        OR (kind = 'OBSERVED' AND triggering_command = 'OBSERVE')
        OR (kind IN ('RESOLVED','RESOLUTION_WITHDRAWN') AND triggering_command = 'EVALUATE')),
    ADD CONSTRAINT action_event_evaluator_job CHECK (
        (kind IN ('RESOLVED','RESOLUTION_WITHDRAWN')) = (source_channel = 'SYSTEM_JOB')
        AND (source_channel <> 'SYSTEM_JOB' OR (
            actor_id = 'service:verification-evaluator'
            AND authorization_basis = 'SYSTEM_VERIFICATION_EVALUATOR'
            AND triggering_job IS NOT NULL AND length(triggering_job) BETWEEN 1 AND 128
            AND verification_plan_id IS NOT NULL AND verification_outcome_id IS NOT NULL))
        AND (source_channel = 'SYSTEM_JOB' OR (verification_plan_id IS NULL AND verification_outcome_id IS NULL))),
    ADD CONSTRAINT action_event_plan_fk FOREIGN KEY (action_id, verification_plan_id)
        REFERENCES verification_plan(action_id, id),
    ADD CONSTRAINT action_event_outcome_fk FOREIGN KEY (action_id, verification_outcome_id)
        REFERENCES verification_outcome(action_id, id);
"""

TABLES = ("verification_plan", "verification_selection_binding", "verification_evaluation_request",
          "verification_outcome", "verification_metric")

APPEND_ONLY = "".join(
    f"CREATE TRIGGER {t}_append_only BEFORE UPDATE OR DELETE ON {t} "
    "FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n"
    for t in TABLES)

REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM verification_plan)
       OR EXISTS (SELECT 1 FROM action_event WHERE kind IN ('RESOLVED','RESOLUTION_WITHDRAWN')) THEN
        RAISE EXCEPTION 'Downgrade of 0019_verification_core refused: verification plans or resolution events exist. 0018 cannot represent them.';
    END IF;
END;
$$;
"""


def upgrade() -> None:
    op.execute(SCHEMA)
    op.execute(APPEND_ONLY)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute("""
ALTER TABLE action_event
    DROP CONSTRAINT action_event_outcome_fk,
    DROP CONSTRAINT action_event_plan_fk,
    DROP CONSTRAINT action_event_evaluator_job,
    DROP CONSTRAINT action_event_command,
    DROP CONSTRAINT action_event_triggering_command_check,
    DROP CONSTRAINT action_event_source_channel_check,
    DROP CONSTRAINT action_event_kind_check,
    DROP COLUMN verification_outcome_id,
    DROP COLUMN verification_plan_id,
    ADD CONSTRAINT action_event_kind_check CHECK (kind IN ('ACCEPTED','APPLIED','FAILED','OBSERVED')),
    ADD CONSTRAINT action_event_source_channel_check CHECK (source_channel = 'SYSTEM_DEMONSTRATION_API'),
    ADD CONSTRAINT action_event_triggering_command_check CHECK (triggering_command IN ('ACCEPT','APPLY','OBSERVE')),
    ADD CONSTRAINT action_event_command CHECK (
        (kind = 'ACCEPTED' AND triggering_command = 'ACCEPT') OR (kind IN ('APPLIED','FAILED') AND triggering_command = 'APPLY')
        OR (kind = 'OBSERVED' AND triggering_command = 'OBSERVE'));
""")
    op.execute("DROP TABLE IF EXISTS verification_metric, verification_outcome, verification_evaluation_request, "
               "verification_selection_binding, verification_plan CASCADE;")
