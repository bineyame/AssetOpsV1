"""W4-02 unit 1: mini-grid depth revisions, selections and per-hour enqueue.

`D-2026-10-20-w4-02-buildspec` (base DDL; closure 1 Q3/Q26; closure 2 "Enqueue, selection and registration";
closure 3; closure 4 B1/B2/N5). Reserved `0028` is unused, so this chains to `0027_w4_work_cases`.

- `mini_depth_revision`: one immutable assessment of one Site, domain and window over an exact input digest.
- `mini_depth_revision_evidence`: the exact accepted evidence IDs a revision cites.
- `mini_depth_selection`: append-only selection events; `seq` is the stable persisted order and `job_id` the
  recompute job the selection settled (null only for an explicitly recorded backfill selection).

Enqueue: a DEFERRABLE INITIALLY DEFERRED constraint trigger on `accepted_evidence` enqueues one PENDING
`mini_*` job per affected Site-local clock hour (renewable: only the local 12:00-13:00 hour) for the domains the
row's role maps to (closure 4 B1), on MINIGRID Sites only, and requires the same-transaction ACCEPTED disposition
(closure 3). `mini_enqueue_configuration` is called by the Foundation/binding publication writer on its own
connection. `mini_enqueue_hour` coalesces per exact hour under an advisory transaction lock; no uniqueness key is
added to `recompute_job` (zero DDL there). q8 ruling 1: `mini_enqueue_hour` is the common final gate; it inserts or
lifts work only when exactly one current `minigrid-roles-4` binding set is in force for the whole hour, else no-op. The one other DDL (q7 ruling 1) replaces the existing
`schedule_site_head_stage_check` to admit the tick's `MINI` stage and adds three integer counters
(`mini_processed`, `mini_deferred`, `mini_failed`, NOT NULL DEFAULT 0) to `schedule_site_head`.

Catalog: three new tables, three mini append-only triggers, two explicit mini indexes, one selection job FK,
three SQL functions, one accepted-evidence constraint trigger, one replaced existing Site-stage CHECK and three
added `schedule_site_head` integer columns (net: +3 tables, +3 functions, +4 user triggers, +2 explicit indexes,
+1 job FK, +3 Site-head columns, zero net CHECK constraints on `schedule_site_head`).

Downgrade refuses while any mini-depth row or any `mini_*` recompute job exists, under locks taken before counting,
then refuses an active `MINI` Site stage, restores the four-stage CHECK and drops the three counters, then drops
the trigger and functions before the tables, all in one transaction. No cascade, no deletion.
"""

from alembic import op

revision = "0029_w4_mini_depth"
down_revision = "0027_w4_work_cases"
branch_labels = None
depends_on = None

MINI_TABLES = ("mini_depth_revision", "mini_depth_revision_evidence", "mini_depth_selection")
MINI_JOB_DOMAINS = ("mini_renewable", "mini_service", "mini_fuel", "mini_backup")

#: Closure 3 item 3 as amended by closure 4 B2: the 17 `MINIGRID_ROLES_4` channel names (every role except the
#: Foundation-control `battery_reserve`). This is the gate; the mapped subset is `DOMAIN_ROLES`.
GATE_ROLES = (
    "generator_state", "generator_power", "feeder_demand", "battery_soc", "pv_power", "pv_irradiance",
    "battery_power", "fuel_level", "pv_available_power", "pcs_discharge_capability",
    "critical_load_requested_power", "critical_load_delivered_power", "storage_charge_requested_power",
    "feeder_requested_power", "site_supply_state", "mini_backup_start_event", "mini_backup_bus_state",
)

#: Closure 4 B1: the frozen (job domain, role) relation. `pv_irradiance`, `battery_power` and
#: `pcs_discharge_capability` are in the gate but map to nothing.
DOMAIN_ROLES = (
    ("mini_renewable", ("pv_available_power", "pv_power", "feeder_demand", "battery_soc",
                        "storage_charge_requested_power", "critical_load_requested_power",
                        "critical_load_delivered_power")),
    ("mini_service", ("feeder_demand", "feeder_requested_power", "critical_load_requested_power",
                      "critical_load_delivered_power")),
    ("mini_fuel", ("generator_power", "fuel_level")),
    ("mini_backup", ("site_supply_state", "mini_backup_start_event", "generator_state", "generator_power",
                     "mini_backup_bus_state", "critical_load_requested_power", "critical_load_delivered_power",
                     "feeder_demand")),
)

#: Closure 2: the configured mini-depth retention a publication enqueues within; older hours need explicit backfill.
RETENTION = "5 days"

#: q8 ruling 1: the only binding role set that makes an hour eligible for mini work (frozen literal; migrations do
#: not import application code).
ROLE_SET_4 = "minigrid-roles-4"

_GATE_LIST = ", ".join(f"'{r}'" for r in GATE_ROLES)
_PAIRS = ",\n            ".join(f"('{d}', '{r}')" for d, roles in DOMAIN_ROLES for r in roles)
_DOMAIN_LIST = ", ".join(f"'{d}'" for d in MINI_JOB_DOMAINS)

SCHEMA = r"""
CREATE TABLE mini_depth_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    domain text NOT NULL CHECK (domain IN ('renewable','service','fuel','backup')),
    model_version text NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    knowledge_cutoff timestamptz NOT NULL,
    input_sha256 text NOT NULL CHECK (input_sha256 ~ '^sha256:[0-9a-f]{64}$'),
    foundation_revision_ids jsonb NOT NULL,
    binding_set_revision_ids jsonb NOT NULL,
    result jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT mini_depth_window CHECK (window_start < window_end),
    CONSTRAINT mini_depth_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT mini_depth_site_id_uq UNIQUE (tenant_id, site_id, id),
    CONSTRAINT mini_depth_basis_uq UNIQUE (tenant_id, site_id, domain, model_version, window_start, window_end,
                                           input_sha256)
);
CREATE TABLE mini_depth_revision_evidence (
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    PRIMARY KEY (revision_id, evidence_id),
    CONSTRAINT mini_depth_evidence_revision_fk FOREIGN KEY (tenant_id, site_id, revision_id)
        REFERENCES mini_depth_revision(tenant_id, site_id, id),
    CONSTRAINT mini_depth_evidence_accepted_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id)
);
CREATE TABLE mini_depth_selection (
    seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    domain text NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    revision_id uuid NOT NULL,
    selected_at timestamptz NOT NULL,
    CONSTRAINT mini_depth_selection_revision_fk FOREIGN KEY (tenant_id, site_id, revision_id)
        REFERENCES mini_depth_revision(tenant_id, site_id, id),
    CONSTRAINT mini_depth_selection_window CHECK (window_start < window_end),
    CONSTRAINT mini_depth_selection_domain CHECK (domain IN ('renewable','service','fuel','backup'))
);
ALTER TABLE mini_depth_selection ADD COLUMN job_id uuid NULL;
ALTER TABLE mini_depth_selection ADD CONSTRAINT mini_depth_selection_job_fk
    FOREIGN KEY (job_id) REFERENCES recompute_job(id);
CREATE INDEX mini_depth_selection_head ON mini_depth_selection
    (tenant_id, site_id, domain, window_start, window_end, seq DESC);
-- q12-6: an explicit cutover basis for an import that has no legacy evidence to migrate. Written only by the
-- W4-02 installer with its empty-legacy import (never inferred from a missing comparison); it names the exact
-- site_import row and digest, so a different import no longer matches.
CREATE TABLE site_cutover_basis (
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    site_import_id uuid NOT NULL REFERENCES site_import(id),
    source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    basis text NOT NULL CHECK (basis = 'NO_LEGACY_EVIDENCE'),
    recorded_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, site_id),
    CONSTRAINT site_cutover_basis_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id)
);
CREATE INDEX mini_depth_revision_evidence_lookup ON mini_depth_revision_evidence
    (tenant_id, site_id, evidence_id);
CREATE TRIGGER mini_depth_revision_immutable BEFORE UPDATE OR DELETE ON mini_depth_revision
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER mini_depth_evidence_immutable BEFORE UPDATE OR DELETE ON mini_depth_revision_evidence
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER mini_depth_selection_immutable BEFORE UPDATE OR DELETE ON mini_depth_selection
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
ALTER TABLE schedule_site_head DROP CONSTRAINT schedule_site_head_stage_check;
ALTER TABLE schedule_site_head ADD CONSTRAINT schedule_site_head_stage_check
  CHECK (stage IN ('IDLE', 'S3', 'MINI', 'S4', 'CONSEQUENCE'));
ALTER TABLE schedule_site_head
  ADD COLUMN mini_processed integer NOT NULL DEFAULT 0,
  ADD COLUMN mini_deferred integer NOT NULL DEFAULT 0,
  ADD COLUMN mini_failed integer NOT NULL DEFAULT 0;
"""

ENQUEUE = rf"""
-- One exact Site-local clock hour into the PENDING queue of one mini domain (closure 2). Serialized per exact hour by
-- the advisory transaction lock; a PENDING job of the same hour only has its available_at lifted, LEASED/DONE/FAILED
-- jobs are never turned back into new work.
CREATE FUNCTION mini_enqueue_hour(p_tenant uuid, p_site uuid, p_domain text, p_lo timestamptz, p_hi timestamptz,
                                  p_cause uuid, p_at timestamptz) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    tz text;
    local_lo timestamp;
    job_id uuid;
    sets bigint;
    covers boolean;
BEGIN
    IF p_domain IS NULL OR p_domain NOT IN ({_DOMAIN_LIST}) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'mini_enqueue_hour: unknown mini-depth domain';
    END IF;
    SELECT s.timezone INTO tz FROM site s
    WHERE s.tenant_id = p_tenant AND s.id = p_site AND s.site_type = 'MINIGRID';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'mini_enqueue_hour: not a MINIGRID Site of this tenant';
    END IF;
    local_lo := p_lo AT TIME ZONE tz;
    IF p_lo IS NULL OR p_hi IS NULL OR p_hi - p_lo <> interval '1 hour'
       OR date_trunc('hour', local_lo) <> local_lo THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'mini_enqueue_hour: window is not one Site-local clock hour';
    END IF;
    IF p_domain = 'mini_renewable' AND extract(hour FROM local_lo) <> 12 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'mini_enqueue_hour: renewable work is the local 12:00 hour only';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(p_tenant::text || ':' || p_site::text || ':' || p_domain || ':'
                                                   || p_lo::text, 0));
    -- q8 ruling 1: the common final gate, rechecked under the lock (also before lifting a PENDING job). Work exists
    -- only when exactly one current `minigrid-roles-4` binding set overlaps the hour and it is in force for the whole
    -- hour (the `load_hour_inputs` rule); otherwise this is a no-op, never a CONFIGURATION_MISSING job.
    SELECT count(*), bool_and(b.valid_from <= p_lo AND (b.valid_to IS NULL OR b.valid_to >= p_hi))
      INTO sets, covers
    FROM signal_binding_set_revision b
    WHERE b.tenant_id = p_tenant AND b.site_id = p_site AND b.role_set = '{ROLE_SET_4}'
      AND b.superseded_at IS NULL AND b.valid_from < p_hi AND (b.valid_to IS NULL OR b.valid_to > p_lo);
    IF sets <> 1 OR NOT covers THEN
        RETURN;
    END IF;
    SELECT j.id INTO job_id FROM recompute_job j
    WHERE j.tenant_id = p_tenant AND j.site_id = p_site AND j.domain = p_domain AND j.window_start = p_lo
      AND j.window_end = p_hi AND j.status = 'PENDING'
    ORDER BY j.id LIMIT 1 FOR UPDATE;
    IF FOUND THEN
        UPDATE recompute_job SET available_at = greatest(available_at, p_at) WHERE id = job_id;
        RETURN;
    END IF;
    INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, cause_evidence_id, status,
                               available_at, created_at)
    VALUES (gen_random_uuid(), p_tenant, p_site, p_domain, p_lo, p_hi, p_cause, 'PENDING', p_at, p_at);
END;
$$;

-- Accepted-row enqueue (closure 3, closure 4 B1). Gate: a closed 17-name channel-role list and a MINIGRID Site;
-- then the same-transaction ACCEPTED disposition is required, else the whole transaction fails (23514). Every
-- intersected Site-local clock hour of [coalesce(interval_start, source_time), coalesce(interval_end,
-- source_time + 1us)) is enqueued for each mapped domain; renewable only for the local 12:00 hour.
CREATE FUNCTION mini_enqueue_accepted() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    tz text;
    decided timestamptz;
    lo timestamptz;
    hi timestamptz;
    h timestamp;
    m record;
BEGIN
    IF NOT (NEW.role IN ({_GATE_LIST})) THEN
        RETURN NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM site s WHERE s.tenant_id = NEW.tenant_id AND s.id = NEW.site_id
                   AND s.site_type = 'MINIGRID') THEN
        RETURN NULL;
    END IF;
    SELECT d.decided_at INTO decided FROM ingestion_disposition d
    WHERE d.tenant_id = NEW.tenant_id AND d.site_id = NEW.site_id AND d.batch_id = NEW.batch_id
      AND d.ordinal = NEW.ordinal AND d.accepted_evidence_id = NEW.id AND d.decision = 'ACCEPTED';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'mini-depth accepted evidence requires same-transaction ACCEPTED disposition';
    END IF;
    SELECT s.timezone INTO tz FROM site s WHERE s.tenant_id = NEW.tenant_id AND s.id = NEW.site_id;
    lo := coalesce(NEW.interval_start, NEW.source_time);
    hi := coalesce(NEW.interval_end, NEW.source_time + interval '1 microsecond');
    FOR m IN SELECT pairs.domain FROM (VALUES
            {_PAIRS}
        ) AS pairs(domain, role)
        WHERE pairs.role = NEW.role ORDER BY pairs.domain LOOP
        h := date_trunc('hour', lo AT TIME ZONE tz);
        WHILE (h AT TIME ZONE tz) < hi LOOP
            IF m.domain <> 'mini_renewable' OR extract(hour FROM h) = 12 THEN
                PERFORM mini_enqueue_hour(NEW.tenant_id, NEW.site_id, m.domain, h AT TIME ZONE tz,
                                          (h AT TIME ZONE tz) + interval '1 hour', NEW.id, decided);
            END IF;
            h := h + interval '1 hour';
        END LOOP;
    END LOOP;
    RETURN NULL;
END;
$$;

-- Publication enqueue (closure 2): every Site-local clock hour of the changed effective interval within the
-- configured {RETENTION} retention ending at p_at, for all four domains (renewable: local noon only). Called by the
-- Foundation/binding publication writer on its own connection after a successful publish; a non-MINIGRID Site
-- enqueues nothing. Older hours are explicit backfill only.
CREATE FUNCTION mini_enqueue_configuration(p_tenant uuid, p_site uuid, p_effective_from timestamptz,
                                           p_effective_to timestamptz, p_at timestamptz) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    tz text;
    lo timestamptz;
    hi timestamptz;
    h timestamp;
    d text;
BEGIN
    SELECT s.timezone INTO tz FROM site s
    WHERE s.tenant_id = p_tenant AND s.id = p_site AND s.site_type = 'MINIGRID';
    IF NOT FOUND THEN
        RETURN;
    END IF;
    lo := greatest(p_effective_from, p_at - interval '{RETENTION}');
    hi := least(coalesce(p_effective_to, p_at), p_at);
    IF lo >= hi THEN
        RETURN;
    END IF;
    FOREACH d IN ARRAY ARRAY[{_DOMAIN_LIST}] LOOP
        h := date_trunc('hour', lo AT TIME ZONE tz);
        WHILE (h AT TIME ZONE tz) < hi LOOP
            IF d <> 'mini_renewable' OR extract(hour FROM h) = 12 THEN
                PERFORM mini_enqueue_hour(p_tenant, p_site, d, h AT TIME ZONE tz,
                                          (h AT TIME ZONE tz) + interval '1 hour', NULL, p_at);
            END IF;
            h := h + interval '1 hour';
        END LOOP;
    END LOOP;
END;
$$;

CREATE CONSTRAINT TRIGGER enqueue_mini_depth AFTER INSERT ON accepted_evidence
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
    EXECUTE FUNCTION mini_enqueue_accepted();
"""

REFUSE_IF_USED = rf"""
LOCK TABLE mini_depth_selection, mini_depth_revision_evidence, mini_depth_revision IN ACCESS EXCLUSIVE MODE;
LOCK TABLE recompute_job IN EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM mini_depth_selection) OR EXISTS (SELECT 1 FROM mini_depth_revision_evidence)
       OR EXISTS (SELECT 1 FROM mini_depth_revision)
       OR EXISTS (SELECT 1 FROM recompute_job WHERE domain IN ({_DOMAIN_LIST})) THEN
        RAISE EXCEPTION 'Downgrade of 0029_w4_mini_depth refused: mini-depth history exists';
    END IF;
END;
$$;
"""

SITE_STAGE_DOWN = """
LOCK TABLE schedule_site_head IN EXCLUSIVE MODE;
DO $$ BEGIN IF EXISTS (SELECT 1 FROM schedule_site_head WHERE stage = 'MINI') THEN RAISE EXCEPTION 'Downgrade of 0029_w4_mini_depth refused: MINI stage active'; END IF; END $$;
ALTER TABLE schedule_site_head DROP CONSTRAINT schedule_site_head_stage_check;
ALTER TABLE schedule_site_head ADD CONSTRAINT schedule_site_head_stage_check
  CHECK (stage IN ('IDLE', 'S3', 'S4', 'CONSEQUENCE'));
ALTER TABLE schedule_site_head
  DROP COLUMN mini_processed,
  DROP COLUMN mini_deferred,
  DROP COLUMN mini_failed;
"""

DROP = """
DROP TRIGGER enqueue_mini_depth ON accepted_evidence;
DROP FUNCTION mini_enqueue_accepted();
DROP FUNCTION mini_enqueue_configuration(uuid, uuid, timestamptz, timestamptz, timestamptz);
DROP FUNCTION mini_enqueue_hour(uuid, uuid, text, timestamptz, timestamptz, uuid, timestamptz);
DROP TRIGGER mini_depth_selection_immutable ON mini_depth_selection;
DROP TRIGGER mini_depth_evidence_immutable ON mini_depth_revision_evidence;
DROP TRIGGER mini_depth_revision_immutable ON mini_depth_revision;
DROP INDEX mini_depth_selection_head;
DROP INDEX mini_depth_revision_evidence_lookup;
DROP TABLE mini_depth_selection;
DROP TABLE mini_depth_revision_evidence;
DROP TABLE mini_depth_revision;
DROP TABLE site_cutover_basis;
"""


def upgrade() -> None:
    op.execute(SCHEMA)
    op.execute(ENQUEUE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(SITE_STAGE_DOWN)
    op.execute(DROP)
