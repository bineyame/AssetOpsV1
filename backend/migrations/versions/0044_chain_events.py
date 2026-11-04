"""CH-1b (build sheet CH-1b §1): the event outbox, its consumption record and the snapshot dirty queue.

- `event_outbox` (AG-7, a broker-ready envelope): one row per (Site, statement, event type), written ONLY by the
  statement-level AFTER triggers below, in the same transaction as the fact (design A0; precedent
  `enqueue_mini_depth`, 0029). Append-only on `ledger_append_only()`. A duplicate `(source, idempotency_key)` is
  a no-op.
- `event_consumption`: `processed(consumer, event_id)`, append-only.
- `snapshot_dirty`: the rebuild queue (a mutable queue, like `recompute_job`): upserted by the snapshots consumer,
  compare-and-deleted by the drain.

The producers aggregate each statement's transition table (`REFERENCING NEW TABLE AS n FOR EACH STATEMENT`), so a
batch of readings costs one event row per Site. `recompute_job` has the one non-insert producer: PostgreSQL refuses a
column list (`UPDATE OF status`) and more than one event on a trigger with transition tables, so it has an INSERT
trigger and an UPDATE trigger that compares the old and new rows and emits only when the status or the window
changed (a coalescing `available_at` update emits nothing).

Downgrade refuses while `event_outbox` has a row; otherwise it drops the triggers, the functions and the tables.
"""

from alembic import op

revision = "0044_chain_events"
down_revision = "0045_thread_known_at"
branch_labels = None
depends_on = None

TABLES = ("event_outbox", "event_consumption", "snapshot_dirty")

_KEY_IDS = "min(n.id::text) || '|' || max(n.id::text) || '|' || count(*)"
_KEY_SEQ = "min(n.seq)::text || '|' || max(n.seq)::text || '|' || count(*)"
_IDS = "jsonb_agg(DISTINCT n.id::text)"

# source table -> (event type, occurred_at expression, subject expression, idempotency key, extra GROUP BY)
PRODUCERS = {
    "accepted_evidence": (
        "reading.accepted", "min(COALESCE(n.interval_start, n.source_time))",
        "jsonb_build_object('roles', jsonb_agg(DISTINCT n.role), "
        "'asset_ids', COALESCE(jsonb_agg(DISTINCT n.asset_id::text) FILTER (WHERE n.asset_id IS NOT NULL), "
        "'[]'::jsonb), 'span', jsonb_build_array(min(COALESCE(n.interval_start, n.source_time)), "
        "max(COALESCE(n.interval_end, n.source_time))))",
        _KEY_IDS, ""),
    "analytic_run_selection": (
        "assessment.revised", "min(n.window_start)",
        "jsonb_build_object('analytic_ids', jsonb_agg(DISTINCT n.analytic_id), "
        "'windows', jsonb_agg(DISTINCT jsonb_build_array(n.window_start, n.window_end)))",
        _KEY_SEQ, ""),
    "mini_depth_selection": (
        "assessment.revised", "min(n.window_start)",
        "jsonb_build_object('domain', n.domain, "
        "'windows', jsonb_agg(DISTINCT jsonb_build_array(n.window_start, n.window_end)))",
        _KEY_SEQ, ", n.domain"),
    "recompute_job": (
        "job.changed", "min(n.window_start)",
        "jsonb_build_object('domain', n.domain, 'status', n.status, "
        "'window', jsonb_build_array(min(n.window_start), max(n.window_end)))",
        "'insert|' || n.domain || '|' || n.status || '|' || " + _KEY_IDS, ", n.domain, n.status"),
    "financial_assumption_revision": (
        "price.revised", "min(n.valid_from)",
        "jsonb_build_object('key', n.assumption_key, 'valid', jsonb_build_array(min(n.valid_from), "
        "CASE WHEN bool_or(n.valid_to IS NULL) THEN NULL ELSE max(n.valid_to) END))",
        _KEY_IDS, ", n.assumption_key"),
    "foundation_revision": (
        "foundation.revised", "min(n.valid_from)", "jsonb_build_object('valid_from', min(n.valid_from))",
        _KEY_IDS, ""),
    "finding_revision": (
        "finding.revised", "min(n.created_at)", f"jsonb_build_object('ids', {_IDS})", _KEY_IDS, ""),
    "mini_opportunity_revision": (
        "opportunity.revised", "min(n.created_at)", f"jsonb_build_object('ids', {_IDS})", _KEY_IDS, ""),
    "action_event": (
        "action.event", "min(n.occurred_at)",
        f"jsonb_build_object('ids', {_IDS}, 'action_ids', jsonb_agg(DISTINCT n.action_id::text))", _KEY_IDS, ""),
    "domain_action": (
        "action.event", "min(n.recorded_at)", f"jsonb_build_object('ids', {_IDS}, 'action_ids', {_IDS})",
        _KEY_IDS, ""),
    "verification_outcome": (
        "verification.outcome", "min(n.recorded_at)",
        f"jsonb_build_object('ids', {_IDS}, 'action_ids', jsonb_agg(DISTINCT n.action_id::text))", _KEY_IDS, ""),
    "outcome_objective_revision": (
        "objective.revised", "min(n.recorded_at)", f"jsonb_build_object('ids', {_IDS})", _KEY_IDS, ""),
}

_INSERT = (
    "INSERT INTO event_outbox (type, schema_version, occurred_at, source, tenant_id, site_id, subject, "
    "idempotency_key)\n"
    "    SELECT '{type}', 1, {occurred}, '{source}', n.tenant_id, n.site_id, {subject}, {key}\n"
    "    FROM {rows} GROUP BY n.tenant_id, n.site_id{group}\n"
    "    ON CONFLICT (source, idempotency_key) DO NOTHING;\n")


def _producer(table: str) -> str:
    type_, occurred, subject, key, group = PRODUCERS[table]
    body = _INSERT.format(type=type_, occurred=occurred, source=table, subject=subject, key=key, group=group,
                          rows="n")
    return (f"CREATE FUNCTION chain_event_{table}() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n    {body}"
            f"    RETURN NULL;\nEND;\n$$;\n"
            f"CREATE TRIGGER {table}_chain_event AFTER INSERT ON {table} REFERENCING NEW TABLE AS n "
            f"FOR EACH STATEMENT EXECUTE FUNCTION chain_event_{table}();\n")


# recompute_job UPDATE: only a changed status or window is an event; the key carries the transaction id, so a later
# re-lease to the same status is a new event, while a repeat inside one transaction is the same fact.
_JOB_UPDATE = _INSERT.format(
    type="job.changed", occurred="min(n.window_start)", source="recompute_job",
    subject=PRODUCERS["recompute_job"][2],
    key="'update|' || pg_current_xact_id()::text || '|' || n.domain || '|' || n.status || '|' || "
        + _KEY_IDS + " || '|' || sum(n.attempts)",
    group=", n.domain, n.status",
    rows="n JOIN o ON o.id = n.id WHERE o.status IS DISTINCT FROM n.status "
         "OR o.window_start IS DISTINCT FROM n.window_start OR o.window_end IS DISTINCT FROM n.window_end")

UPGRADE = """
CREATE TABLE event_outbox (
  event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type text NOT NULL CHECK (type ~ '^[a-z]+\\.[a-z_]+$'),
  schema_version int NOT NULL CHECK (schema_version >= 1),
  occurred_at timestamptz NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  source text NOT NULL,
  tenant_id uuid NOT NULL, site_id uuid NULL,
  subject jsonb NOT NULL,
  idempotency_key text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT event_outbox_idem UNIQUE (source, idempotency_key));
CREATE INDEX event_outbox_site_type_order ON event_outbox (site_id, type, recorded_at, event_id);
CREATE TRIGGER event_outbox_immutable BEFORE UPDATE OR DELETE ON event_outbox
  FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE TABLE event_consumption (
  consumer text NOT NULL CHECK (consumer IN ('snapshots','threads','lifecycle')),
  event_id uuid NOT NULL REFERENCES event_outbox (event_id),
  processed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (consumer, event_id));
CREATE TRIGGER event_consumption_immutable BEFORE UPDATE OR DELETE ON event_consumption
  FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE TABLE snapshot_dirty (
  tenant_id uuid NOT NULL, site_id uuid NOT NULL, local_day date NOT NULL, measure text NOT NULL,
  first_event_id uuid NOT NULL REFERENCES event_outbox (event_id),
  marked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (tenant_id, site_id, local_day, measure),
  FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id));
""" + "".join(_producer(t) for t in PRODUCERS) + (
    "CREATE FUNCTION chain_event_recompute_job_update() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n    "
    + _JOB_UPDATE + "    RETURN NULL;\nEND;\n$$;\n"
    "CREATE TRIGGER recompute_job_chain_event_update AFTER UPDATE ON recompute_job "
    "REFERENCING OLD TABLE AS o NEW TABLE AS n FOR EACH STATEMENT "
    "EXECUTE FUNCTION chain_event_recompute_job_update();\n")

REFUSE_IF_USED = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF EXISTS (SELECT 1 FROM event_outbox) THEN\n"
    "        RAISE EXCEPTION 'Downgrade of 0044_chain_events refused: event history exists';\n"
    "    END IF;\nEND;\n$$;\n"
)

DROP = (
    "DROP TRIGGER recompute_job_chain_event_update ON recompute_job;\n"
    "DROP FUNCTION chain_event_recompute_job_update();\n"
    + "".join(f"DROP TRIGGER {t}_chain_event ON {t};\nDROP FUNCTION chain_event_{t}();\n" for t in PRODUCERS)
    + "DROP TABLE snapshot_dirty;\n"
    "DROP TRIGGER event_consumption_immutable ON event_consumption;\nDROP TABLE event_consumption;\n"
    "DROP TRIGGER event_outbox_immutable ON event_outbox;\nDROP TABLE event_outbox;\n"
)


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED + DROP)
