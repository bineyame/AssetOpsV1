"""W2-04 commit 1: immutable, unpriced cold consequence history and trigger-only dirty work.

`.agent/W2-04-build-spec.md` "Money schema `0023` and rules" (decision D-2026-10-18-w2-04-buildspec). Four new
tenant/Site-scoped, append-only tables; the mini-grid `financial_*` tables (0010-0012) and their rows are untouched.

- `cold_consequence_revision`: one immutable consequence revision per (FindingRevision, kind, basis). Every amount and
  currency is NULL by DB CHECK: W2 has no approved cold stock value, currency or exposure valuation rule. A later
  approved migration must widen that CHECK, the diesel-only assumption publisher and the dirty-work causes together.
- `cold_consequence_evidence`: the exact accepted evidence a revision cites, with its SUPPORT/CONTEXT/EXCLUDED use.
- `cold_consequence_work`: dirty work inserted only by the triggers below, never by runtime code. A cold
  FindingRevision (`NEW.domain = 'cold_chain'`) or a cold episode revision enqueues its Site/assessment window/room;
  an appended `batch_publication_link` enqueues `SOURCE_GATE_CHANGED` only for cold heads whose linked accepted
  evidence came from that batch. Each trigger takes the Site advisory transaction lock before selecting heads and
  inserts through `cold_consequence_enqueue` with `ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO NOTHING`.
  The dirty key is SHA-256 of the canonical JSON array `[cause, locator, tenant_id, site_id, window_start,
  window_end, room_asset_id]` (sorted-key, no-whitespace JSON; lowercase UUIDs; UTC `Z` instants to the second).
  There is no `ASSUMPTION_PUBLISHED` cause: 0010 is diesel-only in DB and publisher.
- `cold_consequence_work_attempt`: SUCCEEDED (no error, exact revision IDs) or FAILED (typed error, no IDs) attempts.

Upgrade backfills the existing W2-03 cold heads (latest cold FindingRevision per Finding, latest revision per cold
episode) once, idempotently. `batch_publication_link` gains a scoped `(tenant_id, site_id, batch_id)` unique target
for the work FK. Downgrade refuses while any W2-04 row exists; otherwise it drops only W2-04 objects.

Revision ID: 0023_w2_cold_consequence
Revises: 0022_w2_cold_assessment
Create Date: 2026-10-18
"""

from __future__ import annotations

from alembic import op

revision = "0023_w2_cold_consequence"
down_revision = "0022_w2_cold_assessment"
branch_labels = None
depends_on = None

COLD_CONSEQUENCE_TABLES = ("cold_consequence_revision", "cold_consequence_evidence", "cold_consequence_work",
                           "cold_consequence_work_attempt")

# One expression, used verbatim by every enqueue path (a test compares the stored bodies).
ENQUEUE_LOCK = "PERFORM pg_advisory_xact_lock(hashtextextended('cold_consequence_enqueue:' || p_site_id::text, 0));"

SCHEMA = r"""
ALTER TABLE batch_publication_link
    ADD CONSTRAINT batch_publication_link_scope_unique UNIQUE (tenant_id, site_id, batch_id);

CREATE TABLE cold_consequence_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    finding_revision_id uuid NOT NULL,
    episode_revision_id uuid NOT NULL,
    assessment_revision_id uuid NOT NULL,
    revision_no integer NOT NULL CHECK (revision_no > 0),
    prior_revision_id uuid NULL,
    kind text NOT NULL CHECK (kind IN ('PRODUCT_EXPOSURE', 'RECORDED_REPAIR')),
    state text NOT NULL CHECK (state IN ('UNPRICED', 'WITHHELD')),
    reason text NOT NULL CHECK (length(btrim(reason)) > 0),
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    room_asset_id uuid NOT NULL,
    overlap_group text NOT NULL CHECK (overlap_group ~ '^cold:[0-9a-f]{64}$'),
    quantity_unit text NOT NULL CHECK (quantity_unit IN ('degC_min', 'none')),
    quantity_low numeric NULL,
    quantity_high numeric NULL,
    amount_low numeric NULL,
    amount_high numeric NULL,
    currency char(3) NULL,
    finding_basis_sha256 char(64) NOT NULL CHECK (finding_basis_sha256 ~ '^[0-9a-f]{64}$'),
    consequence_basis_sha256 char(64) NOT NULL CHECK (consequence_basis_sha256 ~ '^[0-9a-f]{64}$'),
    model_id text NOT NULL CHECK (model_id IN ('cold-exposure/1', 'cold-repair/1')),
    source_classification text NOT NULL CHECK (length(btrim(source_classification)) > 0),
    source_gate_sha256 char(64) NOT NULL CHECK (source_gate_sha256 ~ '^[0-9a-f]{64}$'),
    assumption_revision_ids jsonb NOT NULL,
    limitation text NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT cold_consequence_revision_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT cold_consequence_revision_finding_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_revision_episode_fk FOREIGN KEY (tenant_id, site_id, episode_revision_id)
        REFERENCES cold_episode_revision(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_revision_assessment_fk FOREIGN KEY (tenant_id, site_id, assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_revision_room_fk FOREIGN KEY (tenant_id, site_id, room_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_revision_prior_fk FOREIGN KEY (tenant_id, site_id, prior_revision_id)
        REFERENCES cold_consequence_revision(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_revision_no_unique UNIQUE (finding_revision_id, kind, revision_no),
    CONSTRAINT cold_consequence_revision_basis_unique UNIQUE (finding_revision_id, kind, consequence_basis_sha256),
    CONSTRAINT cold_consequence_revision_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT cold_consequence_revision_prior_chain CHECK ((revision_no = 1) = (prior_revision_id IS NULL)),
    CONSTRAINT cold_consequence_revision_kind_model CHECK (
        (kind = 'PRODUCT_EXPOSURE' AND model_id = 'cold-exposure/1')
        OR (kind = 'RECORDED_REPAIR' AND model_id = 'cold-repair/1')),
    CONSTRAINT cold_consequence_revision_window CHECK (window_start < window_end),
    CONSTRAINT cold_consequence_revision_quantity CHECK (
        (quantity_low IS NULL OR quantity_low >= 0) AND (quantity_high IS NULL OR quantity_high >= 0)
        AND (quantity_low IS NULL OR quantity_high IS NULL OR quantity_low <= quantity_high)),
    CONSTRAINT cold_consequence_revision_unit_none CHECK (
        quantity_unit <> 'none' OR (quantity_low IS NULL AND quantity_high IS NULL)),
    CONSTRAINT cold_consequence_revision_null_bound_limited CHECK (
        quantity_unit <> 'degC_min' OR (quantity_low IS NOT NULL AND quantity_high IS NOT NULL)
        OR state = 'WITHHELD' OR limitation IS NOT NULL),
    CONSTRAINT cold_consequence_revision_unpriced CHECK (
        amount_low IS NULL AND amount_high IS NULL AND currency IS NULL),
    CONSTRAINT cold_consequence_revision_assumptions_array CHECK (jsonb_typeof(assumption_revision_ids) = 'array')
);
CREATE INDEX cold_consequence_revision_site_window
    ON cold_consequence_revision (site_id, window_start, window_end, room_asset_id);

CREATE TABLE cold_consequence_evidence (
    consequence_revision_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    use text NOT NULL CHECK (use IN ('SUPPORT', 'CONTEXT', 'EXCLUDED')),
    reason text NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (consequence_revision_id, evidence_id, use),
    CONSTRAINT cold_consequence_evidence_revision_fk FOREIGN KEY (tenant_id, site_id, consequence_revision_id)
        REFERENCES cold_consequence_revision(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_evidence_evidence_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id)
);

CREATE TABLE cold_consequence_work (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    cause text NOT NULL CHECK (cause IN ('FINDING_REVISION_APPENDED', 'EPISODE_REVISION_APPENDED',
                                         'SOURCE_GATE_CHANGED')),
    finding_revision_id uuid NULL,
    episode_revision_id uuid NULL,
    publication_batch_id uuid NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    room_asset_id uuid NOT NULL,
    dirty_key_sha256 char(64) NOT NULL CHECK (dirty_key_sha256 ~ '^[0-9a-f]{64}$'),
    enqueued_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT cold_consequence_work_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT cold_consequence_work_finding_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_work_episode_fk FOREIGN KEY (tenant_id, site_id, episode_revision_id)
        REFERENCES cold_episode_revision(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_work_batch_fk FOREIGN KEY (tenant_id, site_id, publication_batch_id)
        REFERENCES batch_publication_link(tenant_id, site_id, batch_id),
    CONSTRAINT cold_consequence_work_room_fk FOREIGN KEY (tenant_id, site_id, room_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_work_cause_shape CHECK (
        (cause = 'FINDING_REVISION_APPENDED' AND finding_revision_id IS NOT NULL
            AND episode_revision_id IS NULL AND publication_batch_id IS NULL)
        OR (cause = 'EPISODE_REVISION_APPENDED' AND episode_revision_id IS NOT NULL
            AND finding_revision_id IS NULL AND publication_batch_id IS NULL)
        OR (cause = 'SOURCE_GATE_CHANGED' AND publication_batch_id IS NOT NULL
            AND finding_revision_id IS NULL AND episode_revision_id IS NULL)),
    CONSTRAINT cold_consequence_work_window CHECK (window_start < window_end),
    CONSTRAINT cold_consequence_work_dirty_unique UNIQUE (tenant_id, site_id, dirty_key_sha256),
    CONSTRAINT cold_consequence_work_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX cold_consequence_work_site_enqueued ON cold_consequence_work (site_id, enqueued_at);

CREATE TABLE cold_consequence_work_attempt (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    work_id uuid NOT NULL,
    attempt_no integer NOT NULL CHECK (attempt_no > 0),
    outcome text NOT NULL CHECK (outcome IN ('SUCCEEDED', 'FAILED')),
    error_code text NULL,
    consequence_revision_ids jsonb NOT NULL,
    finished_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT cold_consequence_attempt_work_fk FOREIGN KEY (tenant_id, site_id, work_id)
        REFERENCES cold_consequence_work(tenant_id, site_id, id),
    CONSTRAINT cold_consequence_attempt_no_unique UNIQUE (work_id, attempt_no),
    CONSTRAINT cold_consequence_attempt_ids_array CHECK (jsonb_typeof(consequence_revision_ids) = 'array'),
    CONSTRAINT cold_consequence_attempt_outcome_shape CHECK (
        (outcome = 'SUCCEEDED' AND error_code IS NULL)
        OR (outcome = 'FAILED' AND error_code IS NOT NULL AND length(btrim(error_code)) > 0
            AND consequence_revision_ids = '[]'::jsonb))
);
CREATE INDEX cold_consequence_attempt_latest ON cold_consequence_work_attempt (work_id, attempt_no DESC);
"""

APPEND_ONLY = "".join(
    f"CREATE TRIGGER {t}_append_only BEFORE UPDATE OR DELETE ON {t} "
    "FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n"
    for t in COLD_CONSEQUENCE_TABLES)

TRIGGERS = rf"""
CREATE FUNCTION cold_consequence_dirty_key(p_cause text, p_locator uuid, p_tenant_id uuid, p_site_id uuid,
                                           p_window_start timestamptz, p_window_end timestamptz,
                                           p_room_asset_id uuid) RETURNS char(64)
LANGUAGE sql STABLE STRICT AS $$
    SELECT encode(sha256(convert_to('[' || concat_ws(',',
        to_json(p_cause)::text,
        to_json(p_locator::text)::text,
        to_json(p_tenant_id::text)::text,
        to_json(p_site_id::text)::text,
        to_json(to_char(p_window_start AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'))::text,
        to_json(to_char(p_window_end AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'))::text,
        to_json(p_room_asset_id::text)::text) || ']', 'UTF8')), 'hex')
$$;

-- The one runtime-free INSERT into cold_consequence_work. Callers hold the Site enqueue lock.
CREATE FUNCTION cold_consequence_enqueue(p_cause text, p_locator uuid, p_tenant_id uuid, p_site_id uuid,
                                         p_window_start timestamptz, p_window_end timestamptz,
                                         p_room_asset_id uuid) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO cold_consequence_work (tenant_id, site_id, cause, finding_revision_id, episode_revision_id,
                                       publication_batch_id, window_start, window_end, room_asset_id,
                                       dirty_key_sha256)
    VALUES (p_tenant_id, p_site_id, p_cause,
            CASE WHEN p_cause = 'FINDING_REVISION_APPENDED' THEN p_locator END,
            CASE WHEN p_cause = 'EPISODE_REVISION_APPENDED' THEN p_locator END,
            CASE WHEN p_cause = 'SOURCE_GATE_CHANGED' THEN p_locator END,
            p_window_start, p_window_end, p_room_asset_id,
            cold_consequence_dirty_key(p_cause, p_locator, p_tenant_id, p_site_id, p_window_start, p_window_end,
                                       p_room_asset_id))
    ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO NOTHING;
END;
$$;

-- A cold FindingRevision enqueues its Site, its primary assessment window and its Finding's subject room.
CREATE FUNCTION cold_consequence_dirty_on_finding_revision() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    p_site_id uuid := NEW.site_id;
    w record;
BEGIN
    {ENQUEUE_LOCK}
    SELECT a.window_start, a.window_end, f.subject_asset_id AS room INTO STRICT w
    FROM assessment_revision a, finding f
    WHERE a.tenant_id = NEW.tenant_id AND a.site_id = NEW.site_id AND a.id = NEW.assessment_revision_id
      AND f.tenant_id = NEW.tenant_id AND f.site_id = NEW.site_id AND f.id = NEW.finding_id;
    PERFORM cold_consequence_enqueue('FINDING_REVISION_APPENDED', NEW.id, NEW.tenant_id, NEW.site_id,
                                     w.window_start, w.window_end, w.room);
    RETURN NULL;
END;
$$;
CREATE TRIGGER cold_consequence_dirty_on_finding_revision AFTER INSERT ON finding_revision
    FOR EACH ROW WHEN (NEW.domain = 'cold_chain')
    EXECUTE FUNCTION cold_consequence_dirty_on_finding_revision();

-- A cold episode revision (warranted Finding or not) enqueues its Site, assessment window and episode room.
CREATE FUNCTION cold_consequence_dirty_on_episode_revision() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    p_site_id uuid := NEW.site_id;
    w record;
BEGIN
    {ENQUEUE_LOCK}
    SELECT a.window_start, a.window_end, e.asset_id AS room INTO STRICT w
    FROM assessment_revision a, cold_episode e
    WHERE a.tenant_id = NEW.tenant_id AND a.site_id = NEW.site_id AND a.id = NEW.assessment_revision_id
      AND e.tenant_id = NEW.tenant_id AND e.site_id = NEW.site_id AND e.id = NEW.episode_id;
    PERFORM cold_consequence_enqueue('EPISODE_REVISION_APPENDED', NEW.id, NEW.tenant_id, NEW.site_id,
                                     w.window_start, w.window_end, w.room);
    RETURN NULL;
END;
$$;
CREATE TRIGGER cold_consequence_dirty_on_episode_revision AFTER INSERT ON cold_episode_revision
    FOR EACH ROW EXECUTE FUNCTION cold_consequence_dirty_on_episode_revision();

-- An appended source-publication link changes the source gate of the cold heads (latest episode revision per
-- episode, latest cold FindingRevision per Finding) whose linked accepted evidence came from that batch; only
-- those heads' Site/window/room are enqueued. A link before any acceptance finds no heads and enqueues nothing.
CREATE FUNCTION cold_consequence_dirty_on_source_gate() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    p_site_id uuid := NEW.site_id;
    h record;
BEGIN
    {ENQUEUE_LOCK}
    FOR h IN
        SELECT DISTINCT a.window_start, a.window_end, e.asset_id AS room
        FROM cold_episode_revision r
        JOIN cold_episode e ON e.tenant_id = r.tenant_id AND e.site_id = r.site_id AND e.id = r.episode_id
        JOIN assessment_revision a ON a.tenant_id = r.tenant_id AND a.site_id = r.site_id
            AND a.id = r.assessment_revision_id
        WHERE r.tenant_id = NEW.tenant_id AND r.site_id = NEW.site_id
          AND r.revision_no = (SELECT max(x.revision_no) FROM cold_episode_revision x
                               WHERE x.episode_id = r.episode_id)
          AND EXISTS (SELECT 1 FROM cold_episode_evidence l
                      JOIN accepted_evidence ev ON ev.tenant_id = l.tenant_id AND ev.site_id = l.site_id
                          AND ev.id = l.evidence_id
                      WHERE l.episode_revision_id = r.id AND ev.batch_id = NEW.batch_id)
        UNION
        SELECT DISTINCT a.window_start, a.window_end, f.subject_asset_id AS room
        FROM finding_revision r
        JOIN finding f ON f.tenant_id = r.tenant_id AND f.site_id = r.site_id AND f.id = r.finding_id
        JOIN assessment_revision a ON a.tenant_id = r.tenant_id AND a.site_id = r.site_id
            AND a.id = r.assessment_revision_id
        WHERE r.tenant_id = NEW.tenant_id AND r.site_id = NEW.site_id AND r.domain = 'cold_chain'
          AND r.revision_no = (SELECT max(x.revision_no) FROM finding_revision x
                               WHERE x.finding_id = r.finding_id)
          AND EXISTS (SELECT 1 FROM finding_revision_evidence l
                      JOIN accepted_evidence ev ON ev.tenant_id = l.tenant_id AND ev.site_id = l.site_id
                          AND ev.id = l.evidence_id
                      WHERE l.finding_revision_id = r.id AND ev.batch_id = NEW.batch_id)
        ORDER BY 1, 2, 3
    LOOP
        PERFORM cold_consequence_enqueue('SOURCE_GATE_CHANGED', NEW.batch_id, NEW.tenant_id, NEW.site_id,
                                         h.window_start, h.window_end, h.room);
    END LOOP;
    RETURN NULL;
END;
$$;
CREATE TRIGGER cold_consequence_dirty_on_source_gate AFTER INSERT ON batch_publication_link
    FOR EACH ROW EXECUTE FUNCTION cold_consequence_dirty_on_source_gate();
"""

# Existing W2-03 cold heads are enqueued once; ON CONFLICT DO NOTHING makes a repeat a no-op.
BACKFILL = r"""
SELECT cold_consequence_enqueue('FINDING_REVISION_APPENDED', r.id, r.tenant_id, r.site_id, a.window_start,
                                a.window_end, f.subject_asset_id)
FROM finding_revision r
JOIN finding f ON f.tenant_id = r.tenant_id AND f.site_id = r.site_id AND f.id = r.finding_id
JOIN assessment_revision a ON a.tenant_id = r.tenant_id AND a.site_id = r.site_id AND a.id = r.assessment_revision_id
WHERE r.domain = 'cold_chain'
  AND r.revision_no = (SELECT max(x.revision_no) FROM finding_revision x WHERE x.finding_id = r.finding_id)
ORDER BY r.site_id, r.id;

SELECT cold_consequence_enqueue('EPISODE_REVISION_APPENDED', r.id, r.tenant_id, r.site_id, a.window_start,
                                a.window_end, e.asset_id)
FROM cold_episode_revision r
JOIN cold_episode e ON e.tenant_id = r.tenant_id AND e.site_id = r.site_id AND e.id = r.episode_id
JOIN assessment_revision a ON a.tenant_id = r.tenant_id AND a.site_id = r.site_id AND a.id = r.assessment_revision_id
WHERE r.revision_no = (SELECT max(x.revision_no) FROM cold_episode_revision x WHERE x.episode_id = r.episode_id)
ORDER BY r.site_id, r.id;
"""

REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cold_consequence_revision) OR EXISTS (SELECT 1 FROM cold_consequence_evidence)
       OR EXISTS (SELECT 1 FROM cold_consequence_work) OR EXISTS (SELECT 1 FROM cold_consequence_work_attempt) THEN
        RAISE EXCEPTION 'Downgrade of 0023_w2_cold_consequence refused: cold consequence revisions, evidence links, work or attempts exist. 0022 cannot represent them, and no row is deleted to force a downgrade.';
    END IF;
END;
$$;
"""

DOWNGRADE = """
DROP TRIGGER cold_consequence_dirty_on_source_gate ON batch_publication_link;
DROP TRIGGER cold_consequence_dirty_on_episode_revision ON cold_episode_revision;
DROP TRIGGER cold_consequence_dirty_on_finding_revision ON finding_revision;
DROP FUNCTION cold_consequence_dirty_on_source_gate();
DROP FUNCTION cold_consequence_dirty_on_episode_revision();
DROP FUNCTION cold_consequence_dirty_on_finding_revision();
DROP TABLE cold_consequence_work_attempt;
DROP TABLE cold_consequence_work;
DROP TABLE cold_consequence_evidence;
DROP TABLE cold_consequence_revision;
DROP FUNCTION cold_consequence_enqueue(text, uuid, uuid, uuid, timestamptz, timestamptz, uuid);
DROP FUNCTION cold_consequence_dirty_key(text, uuid, uuid, uuid, timestamptz, timestamptz, uuid);
ALTER TABLE batch_publication_link DROP CONSTRAINT batch_publication_link_scope_unique;
"""


def upgrade() -> None:
    op.execute(SCHEMA)
    op.execute(APPEND_ONLY)
    op.execute(TRIGGERS)
    op.execute(BACKFILL)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
