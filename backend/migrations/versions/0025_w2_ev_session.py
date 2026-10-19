"""W2-06 commit 1: append-only EV session assessment tables and the widened Finding domain checks.

`.agent/W2-06-build-spec.md` (decision D-2026-10-18-w2-06-07-buildspec), "Pre-build closure (2026-10-19)" 0025 DDL,
and `.agent/W2-technical-design-ev.md` section 1. Creates, in order:

- `ev_session`: the scoped session identity `(tenant_id, site_id, charger_asset_id, connector_asset_id,
  external_session_id)`, anchored to the first accepted START evidence ID and its source time.
- `ev_session_revision`: one immutable session assessment snapshot per basis (state, START/terminal instants, ordered
  nullable bounds, exact supported kWh, unknown meter seconds, optional fault evidence, reason codes).
- `ev_session_evidence`: the exact accepted evidence used by a revision (SUPPORT / CONTEXT / EXCLUDED with reason).
- `ev_meter_interval`: the connector `INTERVAL_DELTA` intervals a revision used or excluded; SUPPORT intervals of one
  revision and connector may never overlap (GiST exclusion over half-open ranges).

All four tables are append-only through the repository's `ledger_append_only()` trigger. `finding_domain_subject` and
`finding_revision_domain_minutes` are recreated with their existing mini_grid/cold_chain arms plus an `ev_charging`
arm (connector subject, NULL generator, NULL dispatch minutes). `finding_revision_bounds`,
`finding_revision_minigrid_bounds` and `recompute_job.domain` (text, no CHECK) are unchanged.

Downgrade refuses while any EV session row, EV Finding/revision or `ev_charging` recompute job exists; otherwise it
restores the exact 0022 CHECK definitions and drops only the objects this revision created. No cascade, no deletion.

Revision ID: 0025_w2_ev_session
Revises: 0024_w2_ev_config
Create Date: 2026-10-19
"""

from __future__ import annotations

from alembic import op

revision = "0025_w2_ev_session"
down_revision = "0024_w2_ev_config"
branch_labels = None
depends_on = None

EV_TABLES = ("ev_session", "ev_session_revision", "ev_session_evidence", "ev_meter_interval")

# The 0022 definitions, restored exactly by the downgrade.
DOMAIN_SUBJECT_0022 = """(
        (domain = 'mini_grid' AND generator_asset_id IS NOT NULL AND subject_asset_id IS NULL)
        OR (domain = 'cold_chain' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL))"""
DOMAIN_MINUTES_0022 = """(
        (domain = 'mini_grid' AND candidate_minutes IS NOT NULL AND necessary_minutes IS NOT NULL
            AND indeterminate_minutes IS NOT NULL AND candidate_minutes >= 0 AND necessary_minutes >= 0
            AND indeterminate_minutes >= 0)
        OR (domain = 'cold_chain' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL))"""

DOMAIN_SUBJECT_0025 = """(
        (domain = 'mini_grid' AND generator_asset_id IS NOT NULL AND subject_asset_id IS NULL)
        OR (domain = 'cold_chain' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL)
        OR (domain = 'ev_charging' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL))"""
DOMAIN_MINUTES_0025 = """(
        (domain = 'mini_grid' AND candidate_minutes IS NOT NULL AND necessary_minutes IS NOT NULL
            AND indeterminate_minutes IS NOT NULL AND candidate_minutes >= 0 AND necessary_minutes >= 0
            AND indeterminate_minutes >= 0)
        OR (domain = 'cold_chain' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL)
        OR (domain = 'ev_charging' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL))"""


def _domain_checks(subject: str, minutes: str) -> str:
    return f"""
ALTER TABLE finding
    DROP CONSTRAINT finding_domain_subject,
    ADD CONSTRAINT finding_domain_subject CHECK {subject};
ALTER TABLE finding_revision
    DROP CONSTRAINT finding_revision_domain_minutes,
    ADD CONSTRAINT finding_revision_domain_minutes CHECK {minutes};
"""


# numeric admits 'NaN' and 'Infinity', and NaN sorts above every number, so finite nonnegative needs both bounds
# (the 0010 precedent).
EV_SCHEMA = """
CREATE TABLE ev_session (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    charger_asset_id uuid NOT NULL,
    connector_asset_id uuid NOT NULL,
    external_session_id text NOT NULL,
    first_start_evidence_id uuid NOT NULL,
    anchor_time timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT ev_session_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT ev_session_charger_fk FOREIGN KEY (tenant_id, site_id, charger_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT ev_session_connector_fk FOREIGN KEY (tenant_id, site_id, connector_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT ev_session_start_evidence_fk FOREIGN KEY (tenant_id, site_id, first_start_evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id),
    CONSTRAINT ev_session_external_id CHECK (
        char_length(external_session_id) BETWEEN 1 AND 128 AND btrim(external_session_id) <> ''),
    CONSTRAINT ev_session_identity_unique UNIQUE (tenant_id, site_id, charger_asset_id, connector_asset_id,
        external_session_id),
    CONSTRAINT ev_session_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX ev_session_site_anchor ON ev_session (tenant_id, site_id, anchor_time);
CREATE INDEX ev_session_connector_anchor ON ev_session (tenant_id, site_id, connector_asset_id, anchor_time);

CREATE TABLE ev_session_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    session_id uuid NOT NULL,
    revision_no integer NOT NULL,
    assessment_revision_id uuid NOT NULL,
    analytic_run_id uuid NOT NULL,
    basis_sha256 char(64) NOT NULL,
    state text NOT NULL,
    start_at timestamptz NOT NULL,
    end_at timestamptz NULL,
    start_earliest timestamptz NULL,
    start_latest timestamptz NULL,
    end_earliest timestamptz NULL,
    end_latest timestamptz NULL,
    supported_kwh numeric NULL,
    unknown_meter_seconds integer NOT NULL,
    fault_evidence_id uuid NULL,
    reason_codes jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT ev_session_revision_session_fk FOREIGN KEY (tenant_id, site_id, session_id)
        REFERENCES ev_session(tenant_id, site_id, id),
    CONSTRAINT ev_session_revision_assessment_fk FOREIGN KEY (tenant_id, site_id, assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT ev_session_revision_run_fk FOREIGN KEY (tenant_id, site_id, analytic_run_id)
        REFERENCES analytic_run(tenant_id, site_id, id),
    CONSTRAINT ev_session_revision_fault_fk FOREIGN KEY (tenant_id, site_id, fault_evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id),
    CONSTRAINT ev_session_revision_no_positive CHECK (revision_no > 0),
    CONSTRAINT ev_session_revision_basis_hex CHECK (basis_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ev_session_revision_state CHECK (
        state IN ('COMPLETED', 'OBSERVED_ABORT', 'INCOMPLETE', 'CONTRADICTORY')),
    CONSTRAINT ev_session_revision_end_order CHECK (end_at IS NULL OR end_at >= start_at),
    CONSTRAINT ev_session_revision_state_end CHECK (
        (state IN ('COMPLETED', 'OBSERVED_ABORT') AND end_at IS NOT NULL)
        OR (state = 'INCOMPLETE' AND end_at IS NULL)
        OR state = 'CONTRADICTORY'),
    CONSTRAINT ev_session_revision_start_bounds CHECK (
        start_earliest IS NULL OR start_latest IS NULL OR start_earliest <= start_latest),
    CONSTRAINT ev_session_revision_end_bounds CHECK (
        end_earliest IS NULL OR end_latest IS NULL OR end_earliest <= end_latest),
    CONSTRAINT ev_session_revision_supported_kwh CHECK (
        supported_kwh IS NULL OR (supported_kwh >= 0 AND supported_kwh < 'Infinity'::numeric)),
    CONSTRAINT ev_session_revision_unknown_seconds CHECK (unknown_meter_seconds >= 0),
    CONSTRAINT ev_session_revision_reason_codes_array CHECK (jsonb_typeof(reason_codes) = 'array'),
    CONSTRAINT ev_session_revision_no_unique UNIQUE (tenant_id, site_id, session_id, revision_no),
    CONSTRAINT ev_session_revision_basis_unique UNIQUE (tenant_id, site_id, session_id, basis_sha256),
    CONSTRAINT ev_session_revision_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX ev_session_revision_session_latest ON ev_session_revision
    (tenant_id, site_id, session_id, revision_no DESC);

CREATE TABLE ev_session_evidence (
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    use text NOT NULL,
    reason text NULL,
    PRIMARY KEY (tenant_id, site_id, revision_id, evidence_id),
    CONSTRAINT ev_session_evidence_revision_fk FOREIGN KEY (tenant_id, site_id, revision_id)
        REFERENCES ev_session_revision(tenant_id, site_id, id),
    CONSTRAINT ev_session_evidence_evidence_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id),
    CONSTRAINT ev_session_evidence_use CHECK (use IN ('SUPPORT', 'CONTEXT', 'EXCLUDED')),
    CONSTRAINT ev_session_evidence_reason CHECK (
        (use = 'EXCLUDED' AND reason IS NOT NULL) OR use = 'CONTEXT' OR (use = 'SUPPORT' AND reason IS NULL))
);

CREATE TABLE ev_meter_interval (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    connector_asset_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    start_at timestamptz NOT NULL,
    end_at timestamptz NOT NULL,
    kwh numeric NOT NULL,
    error_bound_kwh numeric NOT NULL,
    use text NOT NULL,
    reason text NULL,
    CONSTRAINT ev_meter_interval_revision_fk FOREIGN KEY (tenant_id, site_id, revision_id)
        REFERENCES ev_session_revision(tenant_id, site_id, id),
    CONSTRAINT ev_meter_interval_connector_fk FOREIGN KEY (tenant_id, site_id, connector_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT ev_meter_interval_evidence_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id),
    CONSTRAINT ev_meter_interval_order CHECK (start_at < end_at),
    CONSTRAINT ev_meter_interval_kwh CHECK (kwh >= 0 AND kwh < 'Infinity'::numeric),
    CONSTRAINT ev_meter_interval_error CHECK (error_bound_kwh >= 0 AND error_bound_kwh < 'Infinity'::numeric),
    CONSTRAINT ev_meter_interval_use CHECK (use IN ('SUPPORT', 'EXCLUDED')),
    CONSTRAINT ev_meter_interval_reason CHECK (
        (use = 'EXCLUDED' AND reason IS NOT NULL) OR (use = 'SUPPORT' AND reason IS NULL)),
    CONSTRAINT ev_meter_interval_evidence_unique UNIQUE (tenant_id, site_id, revision_id, evidence_id),
    CONSTRAINT ev_meter_interval_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT ev_meter_interval_no_support_overlap EXCLUDE USING gist (
        tenant_id WITH =, site_id WITH =, revision_id WITH =, connector_asset_id WITH =,
        tstzrange(start_at, end_at, '[)') WITH &&) WHERE (use = 'SUPPORT')
);
CREATE INDEX ev_meter_interval_bounds ON ev_meter_interval
    (tenant_id, site_id, connector_asset_id, start_at, end_at);
"""

APPEND_ONLY = "".join(
    f"CREATE TRIGGER {t}_append_only BEFORE UPDATE OR DELETE ON {t} "
    "FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n"
    for t in EV_TABLES)

REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM ev_session) OR EXISTS (SELECT 1 FROM ev_session_revision)
       OR EXISTS (SELECT 1 FROM ev_session_evidence) OR EXISTS (SELECT 1 FROM ev_meter_interval)
       OR EXISTS (SELECT 1 FROM finding WHERE domain = 'ev_charging')
       OR EXISTS (SELECT 1 FROM finding_revision WHERE domain = 'ev_charging')
       OR EXISTS (SELECT 1 FROM recompute_job WHERE domain = 'ev_charging') THEN
        RAISE EXCEPTION 'Downgrade of 0025_w2_ev_session refused: EV sessions, session revisions, session evidence links, meter intervals, ev_charging Findings or ev_charging recompute jobs exist. 0024 cannot represent them, and no row is deleted to force a downgrade.';
    END IF;
END;
$$;
"""

DOWNGRADE = """
DROP TABLE ev_meter_interval;
DROP TABLE ev_session_evidence;
DROP TABLE ev_session_revision;
DROP TABLE ev_session;
"""


def upgrade() -> None:
    op.execute(EV_SCHEMA)
    op.execute(APPEND_ONLY)
    op.execute(_domain_checks(DOMAIN_SUBJECT_0025, DOMAIN_MINUTES_0025))


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(_domain_checks(DOMAIN_SUBJECT_0022, DOMAIN_MINUTES_0022))
    op.execute(DOWNGRADE)
