"""S6-01a phase 1: append-only Action, event, policy-change and Action-owned basis rows.

`D-2026-10-15-s601-action-store-and-ui` (`.agent/architect-S6-01-answers.md` Q1-Q5, M1-M3). An Action is created
on acceptance of a server-computed `reserve-trial-1` recommendation for a persisted FindingRevision; it has no
PROPOSED state and no recommendation table (a pre-acceptance proposal is computed from persisted inputs).

- `action`: identity, immutable origin Finding/FindingRevision, primary assessment, the pinned FoundationRevision
  and battery asset, and the immutable accepted-recommendation snapshot (rule id/version, field, percent unit,
  old/proposed values, limitation code/text, input digest, canonical recommendation and acceptance keys).
  `action_code` comes from the `action_code_seq` database sequence and is unique within the tenant.
- `action_basis_assessment` / `action_basis_evidence`: append-only Action-owned children pinning every cited
  Candidate segment and every battery-SOC reading the accepted proposal read (same-Site composite FKs).
- `action_event`: ACCEPTED / APPLIED / FAILED / OBSERVED with occurred/recorded time, SYSTEM actor, source
  channel, authorization basis, triggering service/job/command/fixture, payload digest, idempotency key and typed
  failure code. Only OBSERVED (fixed `DEMO_REVIEW_NOTE`) may carry an `occurred_at` earlier than `recorded_at`,
  by at most 30 days. One ACCEPTED and at most one APPLIED per Action.
- `action_policy_change` / `action_policy_change_binding`: the applied reserve change artifact and every
  superseded/inserted binding-set revision ID (written by S6-01a phase 2 inside the S1 publish transaction).

Written at runtime only by `assetops_backend/actions/adapters/postgres_action_store.py`, the ninth PostgreSQL
writer (rule 8). Every table is append-only (`ledger_append_only`). A `(tenant_id, site_id, finding_id, id)` key
is added to `finding_revision` so the Action's origin revision is proven to belong to its origin Finding.

Revision ID: 0014_action_store
Revises: 0013_schedule_state
Create Date: 2026-10-15
"""

from __future__ import annotations

from alembic import op

revision = "0014_action_store"
down_revision = "0013_schedule_state"
branch_labels = None
depends_on = None

SHA = "CHECK ({} ~ '^[0-9a-f]{{64}}$')"

SCHEMA = f"""
ALTER TABLE finding_revision
    ADD CONSTRAINT finding_revision_finding_scope_unique UNIQUE (tenant_id, site_id, finding_id, id);

CREATE SEQUENCE action_code_seq AS bigint START WITH 1 INCREMENT BY 1 NO CYCLE;

CREATE TABLE action (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    action_no bigint NOT NULL CHECK (action_no >= 1),
    action_code text NOT NULL CHECK (action_code ~ '^ACT-[0-9]{{6,}}$'),
    recommendation_key text NOT NULL {SHA.format('recommendation_key')},
    acceptance_key text NOT NULL {SHA.format('acceptance_key')},
    acceptance_payload_sha256 text NOT NULL {SHA.format('acceptance_payload_sha256')},
    origin_finding_id uuid NOT NULL,
    origin_finding_revision_id uuid NOT NULL,
    primary_assessment_revision_id uuid NOT NULL,
    foundation_revision_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    rule_id text NOT NULL CHECK (rule_id = 'reserve-trial-1'),
    rule_version integer NOT NULL CHECK (rule_version = 1),
    field text NOT NULL CHECK (field = 'reserve-state-of-charge'),
    unit text NOT NULL CHECK (unit = '%'),
    old_value numeric(9,4) NOT NULL CHECK (old_value BETWEEN 15 AND 90),
    proposed_value numeric(9,4) NOT NULL,
    limitation_code text NOT NULL CHECK (length(limitation_code) BETWEEN 1 AND 64),
    limitation_text text NOT NULL CHECK (length(limitation_text) BETWEEN 1 AND 2000),
    input_sha256 text NOT NULL {SHA.format('input_sha256')},
    snapshot jsonb NOT NULL,
    snapshot_sha256 text NOT NULL {SHA.format('snapshot_sha256')},
    created_at timestamptz NOT NULL,
    CONSTRAINT action_proposal_is_trial CHECK (proposed_value = old_value - 5),
    CONSTRAINT action_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT action_finding_fk FOREIGN KEY (tenant_id, site_id, origin_finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT action_finding_revision_fk FOREIGN KEY (tenant_id, site_id, origin_finding_id, origin_finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, finding_id, id),
    CONSTRAINT action_assessment_fk FOREIGN KEY (tenant_id, site_id, primary_assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT action_foundation_fk FOREIGN KEY (tenant_id, site_id, foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT action_asset_fk FOREIGN KEY (tenant_id, site_id, asset_id) REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT action_code_tenant_unique UNIQUE (tenant_id, action_code),
    CONSTRAINT action_no_unique UNIQUE (action_no),
    CONSTRAINT action_acceptance_unique UNIQUE (tenant_id, site_id, acceptance_key),
    CONSTRAINT action_recommendation_unique UNIQUE (tenant_id, site_id, recommendation_key),
    CONSTRAINT action_site_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX action_origin ON action (tenant_id, site_id, origin_finding_id);

CREATE TABLE action_basis_assessment (
    action_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    assessment_revision_id uuid NOT NULL,
    segment_start timestamptz NOT NULL,
    segment_end timestamptz NOT NULL CHECK (segment_end > segment_start),
    PRIMARY KEY (action_id, assessment_revision_id, segment_start),
    CONSTRAINT action_basis_assessment_action_fk FOREIGN KEY (tenant_id, site_id, action_id)
        REFERENCES action(tenant_id, site_id, id),
    CONSTRAINT action_basis_assessment_fk FOREIGN KEY (tenant_id, site_id, assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id)
);

CREATE TABLE action_basis_evidence (
    action_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    assessment_revision_id uuid NOT NULL,
    segment_start timestamptz NOT NULL,
    role text NOT NULL CHECK (role = 'battery_soc'),
    value_text text NOT NULL,
    PRIMARY KEY (action_id, evidence_id, assessment_revision_id, segment_start),
    CONSTRAINT action_basis_evidence_segment_fk FOREIGN KEY (action_id, assessment_revision_id, segment_start)
        REFERENCES action_basis_assessment(action_id, assessment_revision_id, segment_start),
    CONSTRAINT action_basis_evidence_action_fk FOREIGN KEY (tenant_id, site_id, action_id)
        REFERENCES action(tenant_id, site_id, id),
    CONSTRAINT action_basis_evidence_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id)
);

CREATE TABLE action_event (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    action_id uuid NOT NULL,
    kind text NOT NULL CHECK (kind IN ('ACCEPTED','APPLIED','FAILED','OBSERVED')),
    occurred_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL,
    actor_kind text NOT NULL CHECK (actor_kind = 'SYSTEM'),
    actor_id text NOT NULL CHECK (actor_id ~ '^service:[a-z0-9-]+$'),
    source_channel text NOT NULL CHECK (source_channel = 'SYSTEM_DEMONSTRATION_API'),
    authorization_basis text NOT NULL CHECK (length(authorization_basis) BETWEEN 1 AND 500),
    triggering_service text NOT NULL CHECK (length(triggering_service) BETWEEN 1 AND 128),
    triggering_job text NULL,
    triggering_command text NOT NULL CHECK (triggering_command IN ('ACCEPT','APPLY','OBSERVE')),
    triggering_fixture text NOT NULL CHECK (length(triggering_fixture) BETWEEN 1 AND 128),
    idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 8 AND 128),
    payload jsonb NOT NULL,
    payload_sha256 text NOT NULL {SHA.format('payload_sha256')},
    failure_code text NULL CHECK (failure_code IS NULL OR failure_code ~ '^[A-Z][A-Z0-9_]{{2,63}}$'),
    observation_code text NULL,
    expected_foundation_revision_id uuid NULL,
    current_foundation_revision_id uuid NULL,
    CONSTRAINT action_event_action_fk FOREIGN KEY (tenant_id, site_id, action_id)
        REFERENCES action(tenant_id, site_id, id),
    CONSTRAINT action_event_expected_fk FOREIGN KEY (tenant_id, site_id, expected_foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT action_event_current_fk FOREIGN KEY (tenant_id, site_id, current_foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT action_event_apply_basis CHECK (
        (kind IN ('APPLIED','FAILED')) = (expected_foundation_revision_id IS NOT NULL)),
    CONSTRAINT action_event_failure_code CHECK ((kind = 'FAILED') = (failure_code IS NOT NULL)),
    CONSTRAINT action_event_observation_code CHECK (
        (kind = 'OBSERVED' AND observation_code = 'DEMO_REVIEW_NOTE') OR (kind <> 'OBSERVED' AND observation_code IS NULL)),
    CONSTRAINT action_event_command CHECK (
        (kind = 'ACCEPTED' AND triggering_command = 'ACCEPT') OR (kind IN ('APPLIED','FAILED') AND triggering_command = 'APPLY')
        OR (kind = 'OBSERVED' AND triggering_command = 'OBSERVE')),
    CONSTRAINT action_event_server_time CHECK (
        (kind <> 'OBSERVED' AND occurred_at = recorded_at)
        OR (kind = 'OBSERVED' AND occurred_at <= recorded_at AND occurred_at >= recorded_at - interval '30 days')),
    CONSTRAINT action_event_idempotency_unique UNIQUE (action_id, idempotency_key),
    CONSTRAINT action_event_site_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT action_event_action_unique UNIQUE (action_id, id)
);
CREATE UNIQUE INDEX action_event_one_accepted ON action_event (action_id) WHERE kind = 'ACCEPTED';
CREATE UNIQUE INDEX action_event_one_applied ON action_event (action_id) WHERE kind = 'APPLIED';
CREATE INDEX action_event_order ON action_event (action_id, recorded_at, id);

CREATE TABLE action_policy_change (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    action_id uuid NOT NULL,
    applied_event_id uuid NOT NULL,
    command_idempotency_key text NOT NULL,
    asset_id uuid NOT NULL,
    field text NOT NULL CHECK (field = 'reserve-state-of-charge'),
    unit text NOT NULL CHECK (unit = '%'),
    old_value numeric(9,4) NOT NULL,
    new_value numeric(9,4) NOT NULL,
    expected_foundation_revision_id uuid NOT NULL,
    superseded_foundation_revision_id uuid NOT NULL,
    new_foundation_revision_id uuid NOT NULL,
    split_foundation_revision_id uuid NULL,
    effective_from timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL,
    validity text NOT NULL CHECK (validity IN ('EFFECTIVE_FROM_OPEN_ENDED')),
    CONSTRAINT action_policy_change_effective CHECK (effective_from >= recorded_at),
    CONSTRAINT action_policy_change_action_fk FOREIGN KEY (tenant_id, site_id, action_id)
        REFERENCES action(tenant_id, site_id, id),
    CONSTRAINT action_policy_change_event_fk FOREIGN KEY (tenant_id, site_id, applied_event_id)
        REFERENCES action_event(tenant_id, site_id, id),
    CONSTRAINT action_policy_change_own_event_fk FOREIGN KEY (action_id, applied_event_id)
        REFERENCES action_event(action_id, id),
    CONSTRAINT action_policy_change_asset_fk FOREIGN KEY (tenant_id, site_id, asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT action_policy_change_expected_fk FOREIGN KEY (tenant_id, site_id, expected_foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT action_policy_change_superseded_fk FOREIGN KEY (tenant_id, site_id, superseded_foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT action_policy_change_new_fk FOREIGN KEY (tenant_id, site_id, new_foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT action_policy_change_split_fk FOREIGN KEY (tenant_id, site_id, split_foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT action_policy_change_one_per_action UNIQUE (action_id),
    CONSTRAINT action_policy_change_one_per_event UNIQUE (applied_event_id),
    CONSTRAINT action_policy_change_site_unique UNIQUE (tenant_id, site_id, id)
);

CREATE TABLE action_policy_change_binding (
    change_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    binding_set_revision_id uuid NOT NULL,
    relation text NOT NULL CHECK (relation IN ('SUPERSEDED','INSERTED')),
    PRIMARY KEY (change_id, binding_set_revision_id, relation),
    CONSTRAINT action_policy_change_binding_change_fk FOREIGN KEY (tenant_id, site_id, change_id)
        REFERENCES action_policy_change(tenant_id, site_id, id),
    CONSTRAINT action_policy_change_binding_set_fk FOREIGN KEY (tenant_id, site_id, binding_set_revision_id)
        REFERENCES signal_binding_set_revision(tenant_id, site_id, id)
);
"""

TABLES = ("action", "action_basis_assessment", "action_basis_evidence", "action_event", "action_policy_change",
          "action_policy_change_binding")

APPEND_ONLY = "".join(
    f"CREATE TRIGGER {t}_append_only BEFORE UPDATE OR DELETE ON {t} "
    "FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n"
    for t in TABLES)


def upgrade() -> None:
    op.execute(SCHEMA)
    op.execute(APPEND_ONLY)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS action_policy_change_binding, action_policy_change, action_event, "
               "action_basis_evidence, action_basis_assessment, action CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS action_code_seq;")
    op.execute("ALTER TABLE finding_revision DROP CONSTRAINT IF EXISTS finding_revision_finding_scope_unique;")
