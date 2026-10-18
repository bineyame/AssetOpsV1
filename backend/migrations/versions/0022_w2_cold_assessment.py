"""W2-03: cold assessment episodes and the cold_chain Finding domain.

`.agent/W2-03-build-spec.md` "Migration 0022" and `.agent/W2-technical-design-cold.md` section 2
(`D-2026-10-17-w2-02-buildspec`).

Adds three scoped, append-only tables:

- `cold_episode`: one stable EXCURSION or START_RESPONSE episode, identified by `episode_key_sha256`
  (SHA-256 of the canonical `[tenant_id,site_id,kind,subject_asset_id,anchor evidence id]` key), with an
  optional `split_from_episode_id`. `finding_id` stays NULL in this append-only slice: the Finding links
  to its episode through its immutable claim and exact episode revision, never by a later UPDATE.
- `cold_episode_revision`: an immutable bounded result per assessment basis (claim level, ordered
  start/end bounds, nonnegative ordered duration and degree-minute bounds, peak observed, coverage and
  missing steps).
- `cold_episode_evidence`: exact accepted evidence linked as SUPPORT, CONTEXT or EXCLUDED.

Widens the shared Finding tables from `0009_finding_store` for `cold_chain`: `finding.subject_asset_id`
(scoped asset FK), `finding.generator_asset_id` (text, kept) loses NOT NULL, a domain CHECK keeps the
mini-grid shape, and `finding_revision` gains a stored `domain` (old rows backfilled `mini_grid`) whose
parent FK is `(tenant_id,site_id,finding_id,domain)`. Episode bounds and the three candidate-minute
fields become nullable for `cold_chain` only; mini-grid revisions keep both bounds and all three minute
fields required. `recompute_job.domain` is text and needs no change.

Downgrade refuses while any cold episode, revision, evidence link or cold Finding exists; otherwise it
restores the old Finding constraints and columns and drops only the objects this revision created. No
row is deleted to force a downgrade.

Revision ID: 0022_w2_cold_assessment
Revises: 0021_w2_cold_config
Create Date: 2026-10-18
"""

from __future__ import annotations

from alembic import op

revision = "0022_w2_cold_assessment"
down_revision = "0021_w2_cold_config"
branch_labels = None
depends_on = None

COLD_TABLES = ("cold_episode", "cold_episode_revision", "cold_episode_evidence")

FINDING_WIDEN = """
ALTER TABLE finding
    ADD COLUMN subject_asset_id uuid NULL,
    ALTER COLUMN generator_asset_id DROP NOT NULL,
    ADD CONSTRAINT finding_subject_asset_fk FOREIGN KEY (tenant_id, site_id, subject_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    ADD CONSTRAINT finding_domain_subject CHECK (
        (domain = 'mini_grid' AND generator_asset_id IS NOT NULL AND subject_asset_id IS NULL)
        OR (domain = 'cold_chain' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL)),
    ADD CONSTRAINT finding_domain_scope_unique UNIQUE (tenant_id, site_id, id, domain);
CREATE INDEX finding_domain_subject_anchor ON finding (tenant_id, site_id, domain, subject_asset_id, anchor_start);

ALTER TABLE finding_revision ADD COLUMN domain text NOT NULL DEFAULT 'mini_grid';
ALTER TABLE finding_revision ALTER COLUMN domain DROP DEFAULT;
ALTER TABLE finding_revision
    DROP CONSTRAINT finding_revision_finding_fk,
    ADD CONSTRAINT finding_revision_finding_domain_fk FOREIGN KEY (tenant_id, site_id, finding_id, domain)
        REFERENCES finding(tenant_id, site_id, id, domain),
    ALTER COLUMN episode_start DROP NOT NULL,
    ALTER COLUMN episode_end DROP NOT NULL,
    ALTER COLUMN candidate_minutes DROP NOT NULL,
    ALTER COLUMN necessary_minutes DROP NOT NULL,
    ALTER COLUMN indeterminate_minutes DROP NOT NULL,
    DROP CONSTRAINT finding_revision_bounds,
    ADD CONSTRAINT finding_revision_bounds CHECK (
        episode_start IS NULL OR episode_end IS NULL OR episode_start <= episode_end),
    ADD CONSTRAINT finding_revision_minigrid_bounds CHECK (
        domain <> 'mini_grid' OR (episode_start IS NOT NULL AND episode_end IS NOT NULL)),
    ADD CONSTRAINT finding_revision_domain_minutes CHECK (
        (domain = 'mini_grid' AND candidate_minutes IS NOT NULL AND necessary_minutes IS NOT NULL
            AND indeterminate_minutes IS NOT NULL AND candidate_minutes >= 0 AND necessary_minutes >= 0
            AND indeterminate_minutes >= 0)
        OR (domain = 'cold_chain' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL));
"""

COLD_SCHEMA = """
CREATE TABLE cold_episode (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    kind text NOT NULL CHECK (kind IN ('EXCURSION', 'START_RESPONSE')),
    asset_id uuid NOT NULL,
    anchor_time timestamptz NOT NULL,
    episode_key_sha256 char(64) NOT NULL CHECK (episode_key_sha256 ~ '^[0-9a-f]{64}$'),
    split_from_episode_id uuid NULL,
    finding_id uuid NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT cold_episode_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT cold_episode_asset_fk FOREIGN KEY (tenant_id, site_id, asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT cold_episode_split_fk FOREIGN KEY (tenant_id, site_id, split_from_episode_id)
        REFERENCES cold_episode(tenant_id, site_id, id),
    CONSTRAINT cold_episode_finding_fk FOREIGN KEY (tenant_id, site_id, finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT cold_episode_key_unique UNIQUE (tenant_id, site_id, episode_key_sha256),
    CONSTRAINT cold_episode_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT cold_episode_not_own_split CHECK (split_from_episode_id IS NULL OR split_from_episode_id <> id)
);
CREATE INDEX cold_episode_site_kind_anchor ON cold_episode (site_id, kind, anchor_time);

CREATE TABLE cold_episode_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    episode_id uuid NOT NULL,
    revision_no integer NOT NULL CHECK (revision_no > 0),
    assessment_revision_id uuid NOT NULL,
    basis_sha256 char(64) NOT NULL CHECK (basis_sha256 ~ '^[0-9a-f]{64}$'),
    claim_level text NOT NULL CHECK (claim_level IN ('OBSERVED', 'BOUNDED', 'POSSIBLE', 'UNKNOWN', 'CONTRADICTORY')),
    lower_start timestamptz NULL,
    upper_start timestamptz NULL,
    lower_end timestamptz NULL,
    upper_end timestamptz NULL,
    duration_low numeric NULL,
    duration_high numeric NULL,
    degree_minutes_low numeric NULL,
    degree_minutes_high numeric NULL,
    peak_observed numeric NULL,
    coverage numeric(5, 4) NOT NULL CHECK (coverage BETWEEN 0 AND 1),
    missing_steps jsonb NOT NULL DEFAULT '[]',
    created_at timestamptz NOT NULL,
    CONSTRAINT cold_episode_revision_episode_fk FOREIGN KEY (tenant_id, site_id, episode_id)
        REFERENCES cold_episode(tenant_id, site_id, id),
    CONSTRAINT cold_episode_revision_assessment_fk FOREIGN KEY (tenant_id, site_id, assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT cold_episode_revision_no_unique UNIQUE (episode_id, revision_no),
    CONSTRAINT cold_episode_revision_basis_unique UNIQUE (episode_id, basis_sha256),
    CONSTRAINT cold_episode_revision_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT cold_episode_revision_start_order CHECK (
        lower_start IS NULL OR upper_start IS NULL OR lower_start <= upper_start),
    CONSTRAINT cold_episode_revision_end_order CHECK (
        lower_end IS NULL OR upper_end IS NULL OR lower_end <= upper_end),
    CONSTRAINT cold_episode_revision_duration CHECK (
        (duration_low IS NULL OR duration_low >= 0) AND (duration_high IS NULL OR duration_high >= 0)
        AND (duration_low IS NULL OR duration_high IS NULL OR duration_low <= duration_high)),
    CONSTRAINT cold_episode_revision_degree_minutes CHECK (
        (degree_minutes_low IS NULL OR degree_minutes_low >= 0)
        AND (degree_minutes_high IS NULL OR degree_minutes_high >= 0)
        AND (degree_minutes_low IS NULL OR degree_minutes_high IS NULL OR degree_minutes_low <= degree_minutes_high)),
    CONSTRAINT cold_episode_revision_missing_steps_array CHECK (jsonb_typeof(missing_steps) = 'array'),
    CONSTRAINT cold_episode_revision_peak_needs_point CHECK (peak_observed IS NULL OR coverage > 0)
);
CREATE INDEX cold_episode_revision_site_episode ON cold_episode_revision (site_id, episode_id, revision_no DESC);

CREATE TABLE cold_episode_evidence (
    episode_revision_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    use text NOT NULL CHECK (use IN ('SUPPORT', 'CONTEXT', 'EXCLUDED')),
    reason text NULL,
    PRIMARY KEY (episode_revision_id, evidence_id, use),
    CONSTRAINT cold_episode_evidence_revision_fk FOREIGN KEY (tenant_id, site_id, episode_revision_id)
        REFERENCES cold_episode_revision(tenant_id, site_id, id),
    CONSTRAINT cold_episode_evidence_evidence_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id)
);
"""

APPEND_ONLY = "".join(
    f"CREATE TRIGGER {t}_append_only BEFORE UPDATE OR DELETE ON {t} "
    "FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n"
    for t in COLD_TABLES)

REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cold_episode) OR EXISTS (SELECT 1 FROM cold_episode_revision)
       OR EXISTS (SELECT 1 FROM cold_episode_evidence)
       OR EXISTS (SELECT 1 FROM finding WHERE domain = 'cold_chain')
       OR EXISTS (SELECT 1 FROM finding_revision WHERE domain = 'cold_chain') THEN
        RAISE EXCEPTION 'Downgrade of 0022_w2_cold_assessment refused: cold episodes, episode revisions, episode evidence links or cold_chain Findings exist. 0021 cannot represent them, and no row is deleted to force a downgrade.';
    END IF;
END;
$$;
"""

DOWNGRADE = """
DROP TABLE cold_episode_evidence;
DROP TABLE cold_episode_revision;
DROP TABLE cold_episode;

ALTER TABLE finding_revision
    DROP CONSTRAINT finding_revision_domain_minutes,
    DROP CONSTRAINT finding_revision_minigrid_bounds,
    DROP CONSTRAINT finding_revision_bounds,
    ALTER COLUMN episode_start SET NOT NULL,
    ALTER COLUMN episode_end SET NOT NULL,
    ALTER COLUMN candidate_minutes SET NOT NULL,
    ALTER COLUMN necessary_minutes SET NOT NULL,
    ALTER COLUMN indeterminate_minutes SET NOT NULL,
    ADD CONSTRAINT finding_revision_bounds CHECK (episode_start <= episode_end),
    DROP CONSTRAINT finding_revision_finding_domain_fk,
    ADD CONSTRAINT finding_revision_finding_fk FOREIGN KEY (tenant_id, site_id, finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    DROP COLUMN domain;

DROP INDEX finding_domain_subject_anchor;
ALTER TABLE finding
    DROP CONSTRAINT finding_domain_scope_unique,
    DROP CONSTRAINT finding_domain_subject,
    DROP CONSTRAINT finding_subject_asset_fk,
    DROP COLUMN subject_asset_id,
    ALTER COLUMN generator_asset_id SET NOT NULL;
"""


# D-2026-10-18-w2-03-answers Q1: the 0012 fuel-consequence trigger fires only for mini-grid revisions.
# The 0012 function body is unchanged; W2-04 (0023) owns any cold consequence work.
NARROW_FUEL_TRIGGER = """
DROP TRIGGER financial_consequence_dirty_on_finding_revision ON finding_revision;
CREATE TRIGGER financial_consequence_dirty_on_finding_revision AFTER INSERT ON finding_revision
    FOR EACH ROW WHEN (NEW.domain = 'mini_grid')
    EXECUTE FUNCTION financial_consequence_dirty_on_finding_revision();
"""

RESTORE_FUEL_TRIGGER = """
DROP TRIGGER financial_consequence_dirty_on_finding_revision ON finding_revision;
CREATE TRIGGER financial_consequence_dirty_on_finding_revision AFTER INSERT ON finding_revision
    FOR EACH ROW EXECUTE FUNCTION financial_consequence_dirty_on_finding_revision();
"""


def upgrade() -> None:
    op.execute(FINDING_WIDEN)
    op.execute(NARROW_FUEL_TRIGGER)
    op.execute(COLD_SCHEMA)
    op.execute(APPEND_ONLY)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(RESTORE_FUEL_TRIGGER)
    op.execute(DOWNGRADE)
