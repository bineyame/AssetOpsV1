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

Spec commit 3 (Run 2 ruling Q10-Q12) adds the `ev_charging` enqueue: the deferred constraint trigger
`enqueue_ev_assessment` on `accepted_evidence` and the functions `ev_enqueue_floor`, `ev_enqueue_ceil`,
`ev_enqueue_window` and `ev_enqueue_configuration` (the last called only through
`PostgresAssessmentStore.ev_enqueue_configuration`). The downgrade drops them after its refusal check.

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
    unknown_meter_seconds integer NULL,
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
    CONSTRAINT ev_session_revision_unknown_seconds CHECK
        (unknown_meter_seconds IS NULL OR unknown_meter_seconds >= 0),
    CONSTRAINT ev_session_revision_quantity_state CHECK
        ((state = 'CONTRADICTORY' AND supported_kwh IS NULL AND unknown_meter_seconds IS NULL)
         OR (state <> 'CONTRADICTORY' AND unknown_meter_seconds IS NOT NULL)),
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

# W2-06 Run 2 ruling Q10-Q11 (`.agent/W2-06-build-spec.md` "Q10-Q13: enqueue and worker"): the S2 accepted-evidence
# writer is unchanged; a DEFERRABLE INITIALLY DEFERRED constraint trigger on `accepted_evidence` enqueues
# `recompute_job.domain='ev_charging'` before commit for a newly accepted row bound to an `ev-roles-1` role. A
# duplicate receipt inserts no accepted row, so it fires nothing. Job IDs come from `gen_random_uuid()` so the
# W2-05b pinned Python UUID sequence does not shift. Every enqueue holds the Site/domain advisory transaction lock
# with the exact key of the ledger's and the assessment store's job lock (`<site>:ev_charging`).
#
# Base brackets are five-minute UTC-epoch aligned and half-open: a row spans `[interval_start or source_time,
# interval_end or source_time + 1us)`, bracketed outward. Targets are every selected `ev-session/1` window
# (`analytic_run_selection`) intersecting the dirty span, each enqueued separately, plus each base bracket no selected
# target wholly contains. A target merges into one PENDING `ev_charging` job within the ten-minute bridge, only when
# the merged window stays within 31 days and intersects at most one selected window (disjoint selections are never
# coalesced); widening lifts `available_at` to at least the decision instant (S4-07). LEASED, FAILED and DONE jobs are
# never merge candidates: a new PENDING job is added beside them.
EV_ROLES = ("ev_session_event", "ev_connector_fault", "ev_connector_state", "ev_connector_energy",
            "ev_connector_power", "ev_site_import", "ev_requested_power", "ev_allocated_limit")
EV_ROLE_LIST = ", ".join(f"'{r}'" for r in EV_ROLES)

ENQUEUE = rf"""
CREATE FUNCTION ev_enqueue_floor(p timestamptz) RETURNS timestamptz
LANGUAGE sql IMMUTABLE AS $$
    SELECT 'epoch'::timestamptz + floor(extract(epoch FROM p) / 300) * interval '300 seconds'
$$;

CREATE FUNCTION ev_enqueue_ceil(p timestamptz) RETURNS timestamptz
LANGUAGE sql IMMUTABLE AS $$
    SELECT 'epoch'::timestamptz + ceil(extract(epoch FROM p) / 300) * interval '300 seconds'
$$;

-- One target window into the PENDING ev_charging queue (caller holds the Site/domain lock; taking it again is a
-- no-op within the transaction).
CREATE FUNCTION ev_enqueue_window(p_tenant_id uuid, p_site_id uuid, p_lo timestamptz, p_hi timestamptz,
                                  p_cause uuid, p_at timestamptz) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    job record;
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || ':' || 'ev_charging', 0));
    SELECT j.id, j.window_start, j.window_end INTO job FROM recompute_job j
    WHERE j.site_id = p_site_id AND j.tenant_id = p_tenant_id AND j.domain = 'ev_charging' AND j.status = 'PENDING'
      AND j.window_start <= p_hi + interval '10 minutes' AND j.window_end >= p_lo - interval '10 minutes'
      AND greatest(j.window_end, p_hi) - least(j.window_start, p_lo) <= interval '31 days'
      AND (SELECT count(*) FROM (SELECT DISTINCT s.window_start, s.window_end FROM analytic_run_selection s
                                 WHERE s.tenant_id = p_tenant_id AND s.site_id = p_site_id
                                   AND s.analytic_id = 'ev-session/1'
                                   AND s.window_start < greatest(j.window_end, p_hi)
                                   AND s.window_end > least(j.window_start, p_lo)) AS sel) <= 1
    ORDER BY j.window_start, j.id LIMIT 1 FOR UPDATE;
    IF NOT FOUND THEN
        INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, cause_evidence_id,
                                   status, available_at, created_at)
        VALUES (gen_random_uuid(), p_tenant_id, p_site_id, 'ev_charging', p_lo, p_hi, p_cause, 'PENDING', p_at, p_at);
        RETURN;
    END IF;
    UPDATE recompute_job SET window_start = least(job.window_start, p_lo), window_end = greatest(job.window_end, p_hi),
        available_at = greatest(available_at, p_at)
    WHERE id = job.id;
END;
$$;

-- Configuration change (Q12): every already selected ev-session/1 window intersecting the change's validity, each
-- separately; if none exists, the change instant's (valid_from) five-minute bracket. No cause evidence.
CREATE FUNCTION ev_enqueue_configuration(p_tenant_id uuid, p_site_id uuid, p_from timestamptz, p_to timestamptz,
                                         p_at timestamptz) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    w record;
    seen boolean := false;
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || ':' || 'ev_charging', 0));
    FOR w IN SELECT DISTINCT s.window_start, s.window_end FROM analytic_run_selection s
             WHERE s.tenant_id = p_tenant_id AND s.site_id = p_site_id AND s.analytic_id = 'ev-session/1'
               AND s.window_end > p_from AND (p_to IS NULL OR s.window_start < p_to)
             ORDER BY s.window_start, s.window_end LOOP
        PERFORM ev_enqueue_window(p_tenant_id, p_site_id, w.window_start, w.window_end, NULL, p_at);
        seen := true;
    END LOOP;
    IF NOT seen THEN
        PERFORM ev_enqueue_window(p_tenant_id, p_site_id, ev_enqueue_floor(p_from),
                                  ev_enqueue_ceil(p_from + interval '1 microsecond'), NULL, p_at);
    END IF;
END;
$$;

CREATE FUNCTION enqueue_ev_assessment() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    decided timestamptz;
    start_time timestamptz;
    r_lo timestamptz := ev_enqueue_floor(coalesce(NEW.interval_start, NEW.source_time));
    r_hi timestamptz := ev_enqueue_ceil(coalesce(NEW.interval_end, NEW.source_time + interval '1 microsecond'));
    s_lo timestamptz;
    s_hi timestamptz;
    span_lo timestamptz;
    span_hi timestamptz;
    w record;
BEGIN
    -- The disposition FK references this accepted row, which is uncommitted until this deferred firing, so a
    -- matching ACCEPTED disposition can only come from the same transaction. Without one (no S2 decision) the
    -- row enqueues nothing.
    SELECT d.decided_at INTO decided FROM ingestion_disposition d
    WHERE d.batch_id = NEW.batch_id AND d.ordinal = NEW.ordinal AND d.decision = 'ACCEPTED'
      AND d.tenant_id = NEW.tenant_id AND d.site_id = NEW.site_id AND d.accepted_evidence_id = NEW.id;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.site_id::text || ':' || 'ev_charging', 0));
    span_lo := r_lo;
    span_hi := r_hi;
    IF NEW.session_id IS NOT NULL THEN
        -- The accepted START by its exact indexed key (accepted_ev_start_unique), then the session's accepted extent.
        SELECT e.source_time INTO start_time FROM accepted_evidence e
        WHERE e.tenant_id = NEW.tenant_id AND e.site_id = NEW.site_id AND e.asset_id = NEW.asset_id
          AND e.session_id = NEW.session_id AND e.family = 'EVENT' AND e.record_kind = 'EV_SESSION_START';
        IF FOUND THEN
            s_lo := ev_enqueue_floor(start_time);
            s_hi := ev_enqueue_ceil(start_time + interval '1 microsecond');
        END IF;
        SELECT least(span_lo, ev_enqueue_floor(min(coalesce(e.interval_start, e.source_time)))),
               greatest(span_hi, ev_enqueue_ceil(max(coalesce(e.interval_end,
                                                              e.source_time + interval '1 microsecond'))))
        INTO span_lo, span_hi FROM accepted_evidence e
        WHERE e.site_id = NEW.site_id AND e.asset_id = NEW.asset_id AND e.session_id = NEW.session_id
          AND e.tenant_id = NEW.tenant_id;
    END IF;
    FOR w IN SELECT DISTINCT s.window_start, s.window_end FROM analytic_run_selection s
             WHERE s.tenant_id = NEW.tenant_id AND s.site_id = NEW.site_id AND s.analytic_id = 'ev-session/1'
               AND s.window_start < span_hi AND s.window_end > span_lo
             ORDER BY s.window_start, s.window_end LOOP
        PERFORM ev_enqueue_window(NEW.tenant_id, NEW.site_id, w.window_start, w.window_end, NEW.id, decided);
    END LOOP;
    IF NOT EXISTS (SELECT 1 FROM analytic_run_selection s
                   WHERE s.tenant_id = NEW.tenant_id AND s.site_id = NEW.site_id AND s.analytic_id = 'ev-session/1'
                     AND s.window_start < span_hi AND s.window_end > span_lo
                     AND s.window_start <= r_lo AND s.window_end >= r_hi) THEN
        PERFORM ev_enqueue_window(NEW.tenant_id, NEW.site_id, r_lo, r_hi, NEW.id, decided);
    END IF;
    IF s_lo IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM analytic_run_selection s
            WHERE s.tenant_id = NEW.tenant_id AND s.site_id = NEW.site_id AND s.analytic_id = 'ev-session/1'
              AND s.window_start < span_hi AND s.window_end > span_lo
              AND s.window_start <= s_lo AND s.window_end >= s_hi) THEN
        PERFORM ev_enqueue_window(NEW.tenant_id, NEW.site_id, s_lo, s_hi, NEW.id, decided);
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER enqueue_ev_assessment AFTER INSERT ON accepted_evidence
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
    WHEN (NEW.role IN ({EV_ROLE_LIST}))
    EXECUTE FUNCTION enqueue_ev_assessment();
"""

DROP_ENQUEUE = """
DROP TRIGGER enqueue_ev_assessment ON accepted_evidence;
DROP FUNCTION enqueue_ev_assessment();
DROP FUNCTION ev_enqueue_configuration(uuid, uuid, timestamptz, timestamptz, timestamptz);
DROP FUNCTION ev_enqueue_window(uuid, uuid, timestamptz, timestamptz, uuid, timestamptz);
DROP FUNCTION ev_enqueue_ceil(timestamptz);
DROP FUNCTION ev_enqueue_floor(timestamptz);
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
    op.execute(ENQUEUE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DROP_ENQUEUE)
    op.execute(_domain_checks(DOMAIN_SUBJECT_0022, DOMAIN_MINUTES_0022))
    op.execute(DOWNGRADE)
