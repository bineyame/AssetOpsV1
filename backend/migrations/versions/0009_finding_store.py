"""S4-01 phase 1: Finding identity and append-only FindingRevision lineage.

`D-2026-10-12-finding-episode-and-revisions`. A `finding` is one stable
candidate generator-support episode (tenant/Site/domain/generator asset) with an
immutable key, anchor, cohort and matcher version; the creation-time links
(`recurs_after_finding_id`, `split_from_finding_id`) are immutable too.
Lifecycle is never a mutable column: it is the latest `finding_revision`.
Each revision cites its exact primary interval `assessment_revision` (the
technical design's FK), every supporting interval and window revision
(`finding_revision_assessment`, with the run that selected it) and the accepted
evidence actually cited by the candidate segments (`finding_revision_evidence`);
the complete analytic input set stays reachable through
`analytic_run_evidence` of the cited runs and is pinned by digest.
A later bridge records `finding_merge` (superseded -> canonical). All tables
are append-only. Idempotency: `(finding_id, basis_sha256, transition)`.

Revision ID: 0009_finding_store
Revises: 0008_assessment_selection
Create Date: 2026-10-12
"""

from __future__ import annotations

from alembic import op

revision = "0009_finding_store"
down_revision = "0008_assessment_selection"
branch_labels = None
depends_on = None


FINDING = """
CREATE TABLE finding (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    finding_key text NOT NULL,
    domain text NOT NULL,
    mechanism text NOT NULL,
    analytic_id text NOT NULL,
    generator_asset_id text NOT NULL,
    anchor_start timestamptz NOT NULL,
    anchor_assessment_revision_id uuid NOT NULL,
    cohort_sha256 text NULL,
    matcher_version text NOT NULL,
    recurs_after_finding_id uuid NULL,
    split_from_finding_id uuid NULL,
    opened_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT finding_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT finding_anchor_fk FOREIGN KEY (tenant_id, site_id, anchor_assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT finding_key_unique UNIQUE (site_id, finding_key),
    CONSTRAINT finding_site_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT finding_recurs_fk FOREIGN KEY (tenant_id, site_id, recurs_after_finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT finding_split_fk FOREIGN KEY (tenant_id, site_id, split_from_finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT finding_one_origin CHECK (recurs_after_finding_id IS NULL OR split_from_finding_id IS NULL)
);
CREATE INDEX finding_site_asset ON finding (site_id, generator_asset_id, anchor_start);
CREATE INDEX finding_tenant_opened ON finding (tenant_id, opened_at DESC);

CREATE TABLE finding_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    finding_id uuid NOT NULL,
    revision_no integer NOT NULL CHECK (revision_no >= 1),
    transition text NOT NULL CHECK (transition IN ('OPENED', 'SUPPORT_CHANGED', 'MODEL_REEVALUATED', 'SPLIT',
        'MERGED', 'MERGED_INTO', 'UNCONFIRMED', 'NO_LONGER_SUPPORTED', 'BASIS_REFRESHED', 'REOPENED')),
    lifecycle text NOT NULL CHECK (lifecycle IN ('SUPPORTED', 'UNCONFIRMED', 'NO_LONGER_SUPPORTED', 'MERGED')),
    claim_level text NOT NULL,
    title text NOT NULL,
    mechanism text NOT NULL,
    matcher_version text NOT NULL,
    analytic_id text NOT NULL,
    model_version text NOT NULL,
    assessment_revision_id uuid NOT NULL,
    analytic_run_id uuid NOT NULL,
    window_assessment_revision_id uuid NULL,
    episode_start timestamptz NOT NULL,
    episode_end timestamptz NOT NULL,
    candidate_minutes numeric(12, 4) NOT NULL,
    necessary_minutes numeric(12, 4) NOT NULL,
    indeterminate_minutes numeric(12, 4) NOT NULL,
    claim jsonb NOT NULL,
    limitations jsonb NOT NULL,
    basis_sha256 text NOT NULL,
    support_sha256 text NOT NULL,
    cited_evidence_sha256 text NOT NULL,
    input_evidence_sha256 text NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT finding_revision_finding_fk FOREIGN KEY (tenant_id, site_id, finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT finding_revision_assessment_fk FOREIGN KEY (tenant_id, site_id, assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT finding_revision_run_fk FOREIGN KEY (tenant_id, site_id, analytic_run_id)
        REFERENCES analytic_run(tenant_id, site_id, id),
    CONSTRAINT finding_revision_window_fk FOREIGN KEY (tenant_id, site_id, window_assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT finding_revision_bounds CHECK (episode_start <= episode_end),
    CONSTRAINT finding_revision_no_unique UNIQUE (finding_id, revision_no),
    CONSTRAINT finding_revision_basis_unique UNIQUE (finding_id, basis_sha256, transition),
    CONSTRAINT finding_revision_site_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX finding_revision_site_created ON finding_revision (site_id, created_at DESC);
CREATE INDEX finding_revision_primary_assessment ON finding_revision (assessment_revision_id);

CREATE TABLE finding_revision_assessment (
    finding_revision_id uuid NOT NULL,
    assessment_revision_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    analytic_run_id uuid NOT NULL,
    scope text NOT NULL CHECK (scope IN ('INTERVAL', 'WINDOW')),
    is_primary boolean NOT NULL,
    PRIMARY KEY (finding_revision_id, assessment_revision_id),
    CONSTRAINT fra_revision_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT fra_assessment_fk FOREIGN KEY (tenant_id, site_id, assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id),
    CONSTRAINT fra_run_fk FOREIGN KEY (tenant_id, site_id, analytic_run_id)
        REFERENCES analytic_run(tenant_id, site_id, id)
);

CREATE TABLE finding_revision_evidence (
    finding_revision_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    PRIMARY KEY (finding_revision_id, evidence_id),
    CONSTRAINT fre_revision_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT fre_evidence_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id)
);

CREATE TABLE finding_merge (
    superseded_finding_id uuid PRIMARY KEY,
    canonical_finding_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    finding_revision_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT finding_merge_superseded_fk FOREIGN KEY (tenant_id, site_id, superseded_finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT finding_merge_canonical_fk FOREIGN KEY (tenant_id, site_id, canonical_finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT finding_merge_revision_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT finding_merge_distinct CHECK (superseded_finding_id <> canonical_finding_id)
);

-- One row per committed matcher pass (S4-01 phase-2 fix, Q18): the selection sequence it matched through,
-- so a window read says NO_FINDING only after a completed match at that exact selection.
CREATE TABLE finding_match_pass (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    analytic_id text NOT NULL,
    selection_seq bigint NOT NULL,
    matcher_version text NOT NULL,
    revisions_written integer NOT NULL,
    completed_at timestamptz NOT NULL
);
CREATE INDEX finding_match_pass_site ON finding_match_pass (tenant_id, site_id, analytic_id, selection_seq DESC);
"""

APPEND_ONLY = "".join(
    f"CREATE TRIGGER {t}_append_only BEFORE UPDATE OR DELETE ON {t} "
    "FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n"
    for t in ("finding", "finding_revision", "finding_revision_assessment", "finding_revision_evidence",
              "finding_merge", "finding_match_pass"))


def upgrade() -> None:
    op.execute(FINDING)
    op.execute(APPEND_ONLY)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS finding_match_pass, finding_merge, finding_revision_evidence, finding_revision_assessment, "
               "finding_revision, finding CASCADE;")
