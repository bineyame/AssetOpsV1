"""CH-5c (CH5c-R3 R6, CH5c-R4 W1-W2): stored route responses and the chain input change log.

`chain_response` holds the exact served bytes of a stored route under its watermark and code version
(insert-only, `ON CONFLICT DO NOTHING`; pruned to the latest 3 per route and request key by the pre-build).

`chain_input_change` is the W2 change log, append-only on `ledger_append_only()`. Every input table of a stored
route (`config/chain/watermark-inputs-v1.json`, frozen below) gets statement-level AFTER INSERT, UPDATE and DELETE
triggers with transition tables, writing one row per distinct (tenant, Site) touched, and an AFTER TRUNCATE trigger
writing a tenant-wide NULL row. A table without a Site column writes a NULL-Site row (tenant-wide
over-invalidation, the safe direction); one without a tenant column also writes a NULL tenant. The watermark
(`chain/watermark.py`) is the count of the tenant's rows for the request's Sites or NULL: commit-order monotone,
because the log is append-only and every change commits its rows in its own transaction (W1).

Uniform W2 coverage, including the DB append-only tables, is a simplification of W1: one count statement covers
every input, and no `max(...)` term exists.
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0047_chain_response"
down_revision = "0044_chain_events"
branch_labels = None
depends_on = None

#: Frozen copy of `config/chain/watermark-inputs-v1.json` `tables` (an L0 test keeps them equal). Views are
#: excluded: `chain_action` resolves to `action`, `chain_action_thread` and `domain_action`, all listed.
INPUT_TABLES = (
    "accepted_evidence", "action", "action_basis_assessment", "action_basis_evidence", "action_event",
    "action_policy_change", "analytic_run", "analytic_run_assessment", "analytic_run_evidence",
    "analytic_run_selection", "assessment_revision", "asset", "batch_publication_link", "chain_action_thread",
    "cold_consequence_evidence", "cold_consequence_revision", "cold_consequence_work",
    "cold_consequence_work_attempt", "cold_episode", "cold_episode_revision", "domain_action",
    "domain_action_case_link", "domain_action_intent", "ev_consequence_evidence", "ev_consequence_revision",
    "ev_consequence_session", "ev_meter_interval", "ev_session", "ev_session_evidence", "ev_session_revision",
    "event_consumption", "event_outbox", "evidence_publication", "financial_assumption_assignment",
    "financial_assumption_revision", "financial_consequence_assessment_revision",
    "financial_consequence_assumption_revision", "financial_consequence_power_interval",
    "financial_consequence_revision", "financial_consequence_work", "financial_consequence_work_attempt",
    "finding", "finding_match_pass", "finding_merge", "finding_revision", "finding_revision_assessment",
    "finding_revision_evidence", "finding_thread", "finding_thread_event", "finding_thread_occurrence",
    "foundation_revision", "ingestion_batch", "ingestion_disposition", "maintenance_plan", "maintenance_record",
    "maintenance_work_request", "mini_depth_revision", "mini_depth_revision_evidence", "mini_depth_selection",
    "mini_opportunity", "mini_opportunity_revision", "mini_opportunity_selection", "outcome_objective_revision",
    "recompute_job", "signal_binding_revision", "signal_binding_set_revision", "site", "site_cutover_basis",
    "site_day_snapshot", "site_import", "source_clock_attestation", "tenant", "trial_cost_comparison_revision",
    "verification_metric", "verification_outcome", "verification_plan", "work_case", "work_case_action_link",
    "work_case_evidence", "work_case_finding_link", "work_case_revision", "work_event",
)
#: The tenant and Site columns of the tables that do not carry `tenant_id` / `site_id`.
_TENANT_COLUMN = {"tenant": "id"}
_SITE_COLUMN = {"site": "id"}
#: CH5c-R5 R5-2: a table without its own tenant and Site columns takes them from its parent row. `event_consumption`
#: is read by the stored routes (the settled flags), so it is Site-scoped through its outbox row: one change row per
#: distinct outbox Site, NULL only for an outbox row without a Site. `tenant` (own id, NULL Site) and every TRUNCATE
#: (NULL tenant, NULL Site) stay tenant-wide.
_PARENT = {"event_consumption": ("event_outbox", "event_id")}

_TABLES = """
CREATE TABLE chain_input_change (
    change_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id uuid,
    site_id uuid,
    table_name text NOT NULL,
    xact xid8 NOT NULL DEFAULT pg_current_xact_id(),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX chain_input_change_scope ON chain_input_change (tenant_id, site_id);
CREATE TRIGGER chain_input_change_immutable BEFORE UPDATE OR DELETE ON chain_input_change
  FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE TABLE chain_response (
    tenant_id uuid NOT NULL,
    route text NOT NULL,
    request_key text NOT NULL,
    watermark text NOT NULL,
    code_version text NOT NULL,
    etag text NOT NULL,
    body bytea NOT NULL,
    built_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    build_ms integer NOT NULL,
    UNIQUE (route, request_key, watermark, code_version)
);
CREATE INDEX chain_response_latest ON chain_response (route, request_key, built_at DESC);
"""


def _columns(bind, table: str) -> set[str]:
    return {r[0] for r in bind.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() "
        "AND table_name = :t"), {"t": table})}


def _trigger_sql(table: str, tenant: str | None, site: str | None) -> str:
    parent = _PARENT.get(table)
    if parent:
        t, s = "p.tenant_id", "p.site_id"

        def src(rel: str) -> str:
            return f"{rel} r JOIN {parent[0]} p ON p.{parent[1]} = r.{parent[1]}"
    else:
        t = tenant or "NULL::uuid"
        s = site or "NULL::uuid"

        def src(rel: str) -> str:
            return rel
    pick = f"SELECT DISTINCT {t}, {s}, '{table}'"
    return (
        f"CREATE FUNCTION chain_input_change_{table}() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n"
        f"  IF TG_OP = 'INSERT' THEN\n"
        f"    INSERT INTO chain_input_change (tenant_id, site_id, table_name) {pick} FROM {src('n')};\n"
        f"  ELSIF TG_OP = 'UPDATE' THEN\n"
        f"    INSERT INTO chain_input_change (tenant_id, site_id, table_name) SELECT DISTINCT a, b, '{table}' "
        f"FROM (SELECT {t}, {s} FROM {src('n')} UNION ALL SELECT {t}, {s} FROM {src('o')}) x(a, b);\n"
        f"  ELSIF TG_OP = 'DELETE' THEN\n"
        f"    INSERT INTO chain_input_change (tenant_id, site_id, table_name) {pick} FROM {src('o')};\n"
        f"  ELSE\n"
        f"    INSERT INTO chain_input_change (tenant_id, site_id, table_name) VALUES (NULL, NULL, '{table}');\n"
        f"  END IF;\n  RETURN NULL;\nEND $$;\n"
        f"CREATE TRIGGER {table}_cic_ins AFTER INSERT ON {table} REFERENCING NEW TABLE AS n "
        f"FOR EACH STATEMENT EXECUTE FUNCTION chain_input_change_{table}();\n"
        f"CREATE TRIGGER {table}_cic_upd AFTER UPDATE ON {table} REFERENCING OLD TABLE AS o NEW TABLE AS n "
        f"FOR EACH STATEMENT EXECUTE FUNCTION chain_input_change_{table}();\n"
        f"CREATE TRIGGER {table}_cic_del AFTER DELETE ON {table} REFERENCING OLD TABLE AS o "
        f"FOR EACH STATEMENT EXECUTE FUNCTION chain_input_change_{table}();\n"
        f"CREATE TRIGGER {table}_cic_trunc AFTER TRUNCATE ON {table} "
        f"FOR EACH STATEMENT EXECUTE FUNCTION chain_input_change_{table}();\n")


def upgrade() -> None:
    bind = op.get_bind()
    op.execute(_TABLES)
    for table in INPUT_TABLES:
        cols = _columns(bind, table)
        if not cols:
            raise RuntimeError(f"watermark input table {table!r} does not exist")
        tenant = _TENANT_COLUMN.get(table, "tenant_id" if "tenant_id" in cols else None)
        site = _SITE_COLUMN.get(table, "site_id" if "site_id" in cols else None)
        op.execute(_trigger_sql(table, tenant, site))


def downgrade() -> None:
    for table in INPUT_TABLES:
        for suffix in ("ins", "upd", "del", "trunc"):
            op.execute(f"DROP TRIGGER IF EXISTS {table}_cic_{suffix} ON {table}")
        op.execute(f"DROP FUNCTION IF EXISTS chain_input_change_{table}()")
    op.execute("DROP TABLE chain_response")
    op.execute("DROP TABLE chain_input_change")
