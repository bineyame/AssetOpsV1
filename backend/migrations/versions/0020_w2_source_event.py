"""W2-00: ordinary source events and EV interval deltas in accepted evidence.

`.agent/W2-technical-design-cold.md` sections 1-2 and `D-2026-10-17-w2-00-answers` ruling 2.

- `accepted_evidence` gains seven nullable typed event columns (`record_kind`, `event_id`, `correlation_id`,
  `session_id`, `connector_id`, `actor`, `outcome`); `measurement`, `conversion_kind`, `original_unit` and
  `normalized_unit` become nullable for EVENT rows only (CHECKs keep the old MEASUREMENT shape); `quality`
  stays NOT NULL. `family` is MEASUREMENT or EVENT.
- The delta CHECK keys on `measurement='INTERVAL_DELTA'`; `conversion_kind` remains the binding conversion.
- Partial unique indexes `accepted_event_identity_unique` and `accepted_ev_start_unique` arbitrate event and
  EV START races; the ledger keeps the message DO NOTHING target and handles these by savepoint and reread.
- `evidence_rejection_conflict_kind` covers MESSAGE_CONFLICT, EVENT_ID_CONFLICT and SESSION_ID_CONFLICT.
- The existing `ledger_append_only()` triggers already cover the new columns. No backfill.

Downgrade refuses while any accepted event or delta, new conflict kind or `cold_chain` recompute job exists,
and never deletes evidence; otherwise it restores the 0019 checks and nullability.

Revision ID: 0020_w2_source_event
Revises: 0019_verification_core
Create Date: 2026-10-17
"""

from __future__ import annotations

from alembic import op

revision = "0020_w2_source_event"
down_revision = "0019_verification_core"
branch_labels = None
depends_on = None

KIND_OUTCOMES = (
    ("DOOR_OPEN", "OPEN"), ("DOOR_CLOSE", "CLOSED"), ("START_REQUEST", "REQUESTED"),
    ("START_RESULT", "SUCCEEDED"), ("START_RESULT", "FAILED"), ("TRANSFER_RESULT", "SUCCEEDED"),
    ("TRANSFER_RESULT", "FAILED"), ("POWER_LOSS", "LOST"), ("POWER_RESTORED", "RESTORED"),
    ("MANUAL_LOG", "OBSERVED"), ("EV_SESSION_START", "STARTED"), ("EV_SESSION_END", "COMPLETED"),
    ("EV_SESSION_ABORT", "ABORTED"), ("EV_CONNECTOR_FAULT", "FAULTED"), ("EV_CONNECTOR_CLEAR", "CLEARED"),
)
PAIRS = " OR ".join(f"(record_kind = '{k}' AND outcome = '{o}')" for k, o in KIND_OUTCOMES)
DECIMAL_NONNEG = r"'^(0|[1-9][0-9]*)(\.[0-9]*[1-9])?$'"
ID_LENGTH = " AND ".join(f"({c} IS NULL OR length({c}) BETWEEN 1 AND 128)"
                         for c in ("event_id", "correlation_id", "session_id", "connector_id"))

UPGRADE = f"""
ALTER TABLE accepted_evidence
    ADD COLUMN record_kind text NULL,
    ADD COLUMN event_id text NULL,
    ADD COLUMN correlation_id text NULL,
    ADD COLUMN session_id text NULL,
    ADD COLUMN connector_id text NULL,
    ADD COLUMN actor text NULL,
    ADD COLUMN outcome text NULL,
    ALTER COLUMN measurement DROP NOT NULL,
    ALTER COLUMN conversion_kind DROP NOT NULL,
    ALTER COLUMN original_unit DROP NOT NULL,
    ALTER COLUMN normalized_unit DROP NOT NULL,
    ADD CONSTRAINT accepted_evidence_family CHECK (family IN ('MEASUREMENT','EVENT')),
    ADD CONSTRAINT accepted_evidence_measurement_shape CHECK (family <> 'MEASUREMENT' OR (
        measurement IS NOT NULL AND conversion_kind IS NOT NULL AND original_unit IS NOT NULL
        AND normalized_unit IS NOT NULL AND record_kind IS NULL AND event_id IS NULL AND correlation_id IS NULL
        AND actor IS NULL AND outcome IS NULL)),
    ADD CONSTRAINT accepted_evidence_ev_delta_shape CHECK (measurement IS DISTINCT FROM 'INTERVAL_DELTA' OR (
        family = 'MEASUREMENT' AND original_unit = 'kWh' AND normalized_unit = 'kWh'
        AND original_value_text IS NOT NULL AND normalized_value_text IS NOT NULL
        AND original_value_text ~ {DECIMAL_NONNEG} AND normalized_value_text ~ {DECIMAL_NONNEG}
        AND interval_start IS NOT NULL AND interval_end IS NOT NULL AND interval_start < interval_end
        AND interval_end = source_time AND session_id IS NOT NULL AND connector_id IS NOT NULL)),
    ADD CONSTRAINT accepted_evidence_measurement_ids CHECK (family <> 'MEASUREMENT' OR (
        (measurement = 'INTERVAL_DELTA' AND session_id IS NOT NULL AND connector_id IS NOT NULL)
        OR (measurement IS DISTINCT FROM 'INTERVAL_DELTA' AND session_id IS NULL AND connector_id IS NULL))),
    ADD CONSTRAINT accepted_evidence_event_shape CHECK (family <> 'EVENT' OR (
        record_kind IS NOT NULL AND event_id IS NOT NULL AND correlation_id IS NOT NULL AND actor IS NOT NULL
        AND outcome IS NOT NULL AND measurement IS NULL AND conversion_kind IS NULL
        AND quality IN ('GOOD','SUSPECT') AND unavailable_reason IS NULL
        AND interval_start IS NULL AND interval_end IS NULL
        AND ((record_kind = 'MANUAL_LOG' AND original_unit = 'degC' AND original_value_text IS NOT NULL
              AND normalized_unit IS NOT NULL AND normalized_value_text IS NOT NULL)
          OR (record_kind <> 'MANUAL_LOG' AND original_unit IS NULL AND original_value_text IS NULL
              AND normalized_unit IS NULL AND normalized_value_text IS NULL)))),
    ADD CONSTRAINT accepted_evidence_event_kind_outcome CHECK (family <> 'EVENT' OR ({PAIRS})),
    ADD CONSTRAINT accepted_evidence_event_actor CHECK (actor IS NULL OR actor IN ('CONTROLLER','SENSOR','OPERATOR')),
    ADD CONSTRAINT accepted_evidence_event_id_length CHECK ({ID_LENGTH});

CREATE UNIQUE INDEX accepted_event_identity_unique ON accepted_evidence
    (tenant_id, site_id, source_id, record_kind, event_id) WHERE family = 'EVENT';
CREATE UNIQUE INDEX accepted_ev_start_unique ON accepted_evidence
    (tenant_id, site_id, asset_id, session_id) WHERE family = 'EVENT' AND record_kind = 'EV_SESSION_START';
CREATE INDEX accepted_evidence_correlation ON accepted_evidence (site_id, correlation_id, source_time)
    WHERE correlation_id IS NOT NULL;
CREATE INDEX accepted_evidence_session ON accepted_evidence (site_id, asset_id, session_id, source_time)
    WHERE session_id IS NOT NULL;

ALTER TABLE evidence_rejection DROP CONSTRAINT evidence_rejection_conflict_kind;
ALTER TABLE evidence_rejection ADD CONSTRAINT evidence_rejection_conflict_kind CHECK (
    (kind IN ('MESSAGE_CONFLICT','EVENT_ID_CONFLICT','SESSION_ID_CONFLICT')) = (conflicts_with_evidence_id IS NOT NULL)
);
"""

REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM accepted_evidence WHERE family = 'EVENT' OR measurement = 'INTERVAL_DELTA')
       OR EXISTS (SELECT 1 FROM evidence_rejection WHERE kind IN ('EVENT_ID_CONFLICT','SESSION_ID_CONFLICT'))
       OR EXISTS (SELECT 1 FROM recompute_job WHERE domain = 'cold_chain') THEN
        RAISE EXCEPTION 'Downgrade of 0020_w2_source_event refused: accepted events or interval deltas, event/session conflicts or cold_chain recompute jobs exist. 0019 cannot represent them, and evidence is never deleted.';
    END IF;
END;
$$;
"""

DOWNGRADE = """
ALTER TABLE evidence_rejection DROP CONSTRAINT evidence_rejection_conflict_kind;
ALTER TABLE evidence_rejection ADD CONSTRAINT evidence_rejection_conflict_kind CHECK (
    (kind = 'MESSAGE_CONFLICT') = (conflicts_with_evidence_id IS NOT NULL)
);
DROP INDEX accepted_evidence_session;
DROP INDEX accepted_evidence_correlation;
DROP INDEX accepted_ev_start_unique;
DROP INDEX accepted_event_identity_unique;
ALTER TABLE accepted_evidence
    DROP CONSTRAINT accepted_evidence_event_id_length,
    DROP CONSTRAINT accepted_evidence_event_actor,
    DROP CONSTRAINT accepted_evidence_event_kind_outcome,
    DROP CONSTRAINT accepted_evidence_event_shape,
    DROP CONSTRAINT accepted_evidence_measurement_ids,
    DROP CONSTRAINT accepted_evidence_ev_delta_shape,
    DROP CONSTRAINT accepted_evidence_measurement_shape,
    DROP CONSTRAINT accepted_evidence_family,
    ALTER COLUMN measurement SET NOT NULL,
    ALTER COLUMN conversion_kind SET NOT NULL,
    ALTER COLUMN original_unit SET NOT NULL,
    ALTER COLUMN normalized_unit SET NOT NULL,
    DROP COLUMN outcome,
    DROP COLUMN actor,
    DROP COLUMN connector_id,
    DROP COLUMN session_id,
    DROP COLUMN correlation_id,
    DROP COLUMN event_id,
    DROP COLUMN record_kind;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
