"""CH-9b2 (build sheet CH-9b R1-R2, CH9b1-R Q1 = B, CH9b2-R): a verification plan for a domain Action.

The mill lever's Action is a MINI `domain_action` raised from an opportunity (0051), APPLIED by its work case's
COMPLETE event. `verification_plan` and its two Action-keyed children now hold either a `reserve-trial-1` plan of a W1
`action` (unchanged) or a `midday-productive-shift-1` plan of a `domain_action`:

- `verification_plan` gains `domain_action_id`, `origin_opportunity_revision_id` and `applied_work_event_id`, each with
  its scoped FK (`domain_action`, `mini_opportunity_revision`, `work_event`). The reserve-shaped columns lose NOT NULL
  only (no row is rewritten). Exactly one of `action_id` / `domain_action_id`, of the applied anchor
  (`applied_event_id` / `applied_work_event_id`) and of the origin (`origin_finding_revision_id` /
  `origin_opportunity_revision_id`) is set (three named CHECKs). `verification_plan_family` couples them to the rule:
  a `reserve-trial-1` row keeps every reserve column NOT NULL, and its 60-minute same-clock window CHECKs keep their
  0019 names (now conditional on the reserve rule, so a reserve refusal names the same constraint); a
  `midday-productive-shift-1` row has the domain columns only, no supersession, the `productive-load-midday@1`
  fixture and 14-day candidate day ranges with the baseline wholly before the later range (the effective day is in
  neither, CH9b2-R Q2). `rule_id` and `plan_version` admit the new family. One plan per domain Action
  (`UNIQUE (domain_action_id)`, Q9).
- `verification_evaluation_request` and `verification_outcome` (Q8, overridden): `action_id` loses NOT NULL, a
  `domain_action_id` is added, exactly one is set, and the `(domain_action_id, plan_id)` FK mirrors the existing
  `(action_id, plan_id)` one. The outcome's supersession gets the same domain twin.
- The 0044 `verification.outcome` producer names `COALESCE(action_id, domain_action_id)` in `action_ids` (a reserve
  outcome's subject is unchanged).

The changed tables already carry their 0047 `chain_input_change` triggers; no new table is added. Downgrade locks the
tables, refuses while any domain-Action plan, request or outcome exists, then restores the 0019 constraints, the NOT
NULLs and the 0044 producer.

Revision ID: 0052_verification_plan_domain
Revises: 0051_action_opportunity_origin
Create Date: 2026-11-05
"""

from alembic import op

revision = "0052_verification_plan_domain"
down_revision = "0051_action_opportunity_origin"
branch_labels = None
depends_on = None

RESERVE, MIDDAY = "reserve-trial-1", "midday-productive-shift-1"
RESERVE_PLAN, MIDDAY_PLAN = "reserve-trial-verification-1", "midday-productive-shift-verification-1"
MIDDAY_FIXTURE = "productive-load-midday@1"
TABLES = ("verification_metric", "verification_outcome", "verification_evaluation_request",
          "verification_selection_binding", "verification_plan")
RESERVE_COLUMNS = ("action_id", "origin_finding_revision_id", "applied_event_id", "change_id",
                   "old_foundation_revision_id", "new_foundation_revision_id", "battery_asset_id", "field",
                   "baseline_candidate_seconds")
REFUSED = "Downgrade of 0052_verification_plan_domain refused: domain-Action verification rows exist."
# The 0019 window CHECKs, verbatim.
WINDOW = ("{0}_end - {0}_start = interval '60 minutes' AND mod(extract(epoch FROM {0}_start)::numeric, 300) = 0")
SAME_CLOCK = ("mod(extract(epoch FROM baseline_start)::numeric, 86400) = "
              "mod(extract(epoch FROM later_start)::numeric, 86400)")


def _all(columns, test: str) -> str:
    return " AND ".join(f"{c} {test}" for c in columns)


_FAMILY = f"""(
    (rule_id = '{RESERVE}' AND plan_version = '{RESERVE_PLAN}' AND {_all(RESERVE_COLUMNS, 'IS NOT NULL')}
     AND {_all(('domain_action_id', 'origin_opportunity_revision_id', 'applied_work_event_id'), 'IS NULL')})
    OR (rule_id = '{MIDDAY}' AND plan_version = '{MIDDAY_PLAN}' AND {_all(RESERVE_COLUMNS, 'IS NULL')}
     AND {_all(('domain_action_id', 'origin_opportunity_revision_id', 'applied_work_event_id'), 'IS NOT NULL')}
     AND supersedes_plan_id IS NULL AND triggering_fixture = '{MIDDAY_FIXTURE}'
     AND baseline_end - baseline_start = interval '14 days' AND later_end - later_start = interval '14 days'
     AND baseline_end <= later_start))"""


def _one(a: str, b: str) -> str:
    return f"CHECK (({a} IS NULL) <> ({b} IS NULL))"


_PRODUCER = """
CREATE OR REPLACE FUNCTION chain_event_verification_outcome() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO event_outbox (type, schema_version, occurred_at, source, tenant_id, site_id, subject, idempotency_key)
    SELECT 'verification.outcome', 1, min(n.recorded_at), 'verification_outcome', n.tenant_id, n.site_id, jsonb_build_object('ids', jsonb_agg(DISTINCT n.id::text), 'action_ids', jsonb_agg(DISTINCT {action}::text)), min(n.id::text) || '|' || max(n.id::text) || '|' || count(*)
    FROM n GROUP BY n.tenant_id, n.site_id
    ON CONFLICT (source, idempotency_key) DO NOTHING;
    RETURN NULL;
END;
$$;
"""

UPGRADE = f"""
ALTER TABLE verification_plan
    ADD COLUMN domain_action_id uuid NULL,
    ADD COLUMN origin_opportunity_revision_id uuid NULL,
    ADD COLUMN applied_work_event_id uuid NULL,
    {", ".join(f"ALTER COLUMN {c} DROP NOT NULL" for c in RESERVE_COLUMNS)},
    DROP CONSTRAINT verification_plan_plan_version_check,
    DROP CONSTRAINT verification_plan_rule_id_check,
    DROP CONSTRAINT verification_plan_baseline_window,
    DROP CONSTRAINT verification_plan_later_window,
    DROP CONSTRAINT verification_plan_same_clock,
    ADD CONSTRAINT verification_plan_plan_version_check CHECK (plan_version IN ('{RESERVE_PLAN}', '{MIDDAY_PLAN}')),
    ADD CONSTRAINT verification_plan_rule_id_check CHECK (rule_id IN ('{RESERVE}', '{MIDDAY}')),
    ADD CONSTRAINT verification_plan_baseline_window CHECK (rule_id <> '{RESERVE}' OR ({WINDOW.format('baseline')})),
    ADD CONSTRAINT verification_plan_later_window CHECK (rule_id <> '{RESERVE}' OR ({WINDOW.format('later')})),
    ADD CONSTRAINT verification_plan_same_clock CHECK (rule_id <> '{RESERVE}' OR ({SAME_CLOCK})),
    ADD CONSTRAINT verification_plan_one_action {_one('action_id', 'domain_action_id')},
    ADD CONSTRAINT verification_plan_one_anchor {_one('applied_event_id', 'applied_work_event_id')},
    ADD CONSTRAINT verification_plan_one_origin {_one('origin_finding_revision_id', 'origin_opportunity_revision_id')},
    ADD CONSTRAINT verification_plan_family CHECK {_FAMILY},
    ADD CONSTRAINT verification_plan_domain_action_fk FOREIGN KEY (tenant_id, site_id, domain_action_id)
        REFERENCES domain_action(tenant_id, site_id, id),
    ADD CONSTRAINT verification_plan_opportunity_revision_fk
        FOREIGN KEY (tenant_id, site_id, origin_opportunity_revision_id)
        REFERENCES mini_opportunity_revision(tenant_id, site_id, id),
    ADD CONSTRAINT verification_plan_work_event_fk FOREIGN KEY (tenant_id, site_id, applied_work_event_id)
        REFERENCES work_event(tenant_id, site_id, id),
    ADD CONSTRAINT verification_plan_domain_one UNIQUE (domain_action_id),
    ADD CONSTRAINT verification_plan_domain_unique UNIQUE (domain_action_id, id);

ALTER TABLE verification_evaluation_request
    ADD COLUMN domain_action_id uuid NULL,
    ALTER COLUMN action_id DROP NOT NULL,
    ADD CONSTRAINT verification_evaluation_request_one_action {_one('action_id', 'domain_action_id')},
    ADD CONSTRAINT verification_evaluation_request_domain_plan_fk FOREIGN KEY (domain_action_id, plan_id)
        REFERENCES verification_plan(domain_action_id, id);

ALTER TABLE verification_outcome
    ADD COLUMN domain_action_id uuid NULL,
    ALTER COLUMN action_id DROP NOT NULL,
    ADD CONSTRAINT verification_outcome_one_action {_one('action_id', 'domain_action_id')},
    ADD CONSTRAINT verification_outcome_domain_plan_fk FOREIGN KEY (domain_action_id, plan_id)
        REFERENCES verification_plan(domain_action_id, id),
    ADD CONSTRAINT verification_outcome_domain_unique UNIQUE (domain_action_id, id),
    ADD CONSTRAINT verification_outcome_domain_supersedes_fk FOREIGN KEY (domain_action_id, supersedes_outcome_id)
        REFERENCES verification_outcome(domain_action_id, id);
CREATE INDEX verification_outcome_domain_order ON verification_outcome (domain_action_id, recorded_at, id);
""" + _PRODUCER.format(action="COALESCE(n.action_id, n.domain_action_id)")

REFUSE_IF_USED = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF EXISTS (SELECT 1 FROM verification_plan WHERE domain_action_id IS NOT NULL)\n"
    "       OR EXISTS (SELECT 1 FROM verification_evaluation_request WHERE domain_action_id IS NOT NULL)\n"
    "       OR EXISTS (SELECT 1 FROM verification_outcome WHERE domain_action_id IS NOT NULL) THEN\n"
    f"        RAISE EXCEPTION '{REFUSED}';\n    END IF;\nEND;\n$$;\n"
)

RESTORE = f"""
DROP INDEX verification_outcome_domain_order;
ALTER TABLE verification_outcome
    DROP CONSTRAINT verification_outcome_domain_supersedes_fk,
    DROP CONSTRAINT verification_outcome_domain_unique,
    DROP CONSTRAINT verification_outcome_domain_plan_fk,
    DROP CONSTRAINT verification_outcome_one_action,
    DROP COLUMN domain_action_id,
    ALTER COLUMN action_id SET NOT NULL;
ALTER TABLE verification_evaluation_request
    DROP CONSTRAINT verification_evaluation_request_domain_plan_fk,
    DROP CONSTRAINT verification_evaluation_request_one_action,
    DROP COLUMN domain_action_id,
    ALTER COLUMN action_id SET NOT NULL;
ALTER TABLE verification_plan
    DROP CONSTRAINT verification_plan_domain_unique,
    DROP CONSTRAINT verification_plan_domain_one,
    DROP CONSTRAINT verification_plan_work_event_fk,
    DROP CONSTRAINT verification_plan_opportunity_revision_fk,
    DROP CONSTRAINT verification_plan_domain_action_fk,
    DROP CONSTRAINT verification_plan_family,
    DROP CONSTRAINT verification_plan_one_origin,
    DROP CONSTRAINT verification_plan_one_anchor,
    DROP CONSTRAINT verification_plan_one_action,
    DROP CONSTRAINT verification_plan_rule_id_check,
    DROP CONSTRAINT verification_plan_plan_version_check,
    DROP CONSTRAINT verification_plan_baseline_window,
    DROP CONSTRAINT verification_plan_later_window,
    DROP CONSTRAINT verification_plan_same_clock,
    DROP COLUMN applied_work_event_id,
    DROP COLUMN origin_opportunity_revision_id,
    DROP COLUMN domain_action_id,
    {", ".join(f"ALTER COLUMN {c} SET NOT NULL" for c in RESERVE_COLUMNS)},
    ADD CONSTRAINT verification_plan_plan_version_check CHECK (plan_version = '{RESERVE_PLAN}'),
    ADD CONSTRAINT verification_plan_rule_id_check CHECK (rule_id = '{RESERVE}'),
    ADD CONSTRAINT verification_plan_baseline_window CHECK ({WINDOW.format('baseline')}),
    ADD CONSTRAINT verification_plan_later_window CHECK ({WINDOW.format('later')}),
    ADD CONSTRAINT verification_plan_same_clock CHECK ({SAME_CLOCK});
""" + _PRODUCER.format(action="n.action_id")


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED + RESTORE)
