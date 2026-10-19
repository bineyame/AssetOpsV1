"""W2-05a commit 5: the partial EV measurement read index.

`.agent/W2-05a-build-spec.md` (decision D-2026-10-18-w2-05-buildspec) "Q7" and the property paragraph. Adds only the
partial `(site_id, session_id, connector_id, source_time, id)` index over EV interval-delta measurements. Foundation
history and the 0020 family CHECK are retained untouched; EV configuration (properties, bindings) lives in the
existing Foundation/binding tables, so there is no new configuration table. Downgrade refuses while any EV measurement
exists (evidence is never deleted), then drops the index; historical Foundation reads stay safe.

Revision ID: 0024_w2_ev_config
Revises: 0023_w2_cold_consequence
Create Date: 2026-10-19
"""

from __future__ import annotations

from alembic import op

revision = "0024_w2_ev_config"
down_revision = "0023_w2_cold_consequence"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE INDEX accepted_evidence_ev_measurement ON accepted_evidence
    (site_id, session_id, connector_id, source_time, id)
    WHERE family = 'MEASUREMENT' AND measurement = 'INTERVAL_DELTA';
"""

REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM accepted_evidence WHERE measurement = 'INTERVAL_DELTA') THEN
        RAISE EXCEPTION 'Downgrade of 0024_w2_ev_config refused: EV interval-delta measurements exist, and evidence is never deleted.';
    END IF;
END;
$$;
"""

DOWNGRADE = "DROP INDEX accepted_evidence_ev_measurement;"


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
