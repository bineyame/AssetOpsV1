"""OPS-02 rule 8 writer-guard mutation corpus: the statement-level writer guard must refuse each negative probe for its
ownership reason and accept the controls. Every mutation appends module-level code to one backend module, runs the
guard, and restores the module with `git checkout --`, so run it only on a clean, committed tree.

    python tools/writer_guard_probes.py [--seam] [probe-name ...]

The default runner is `tools/check-architecture.ps1` (about 70 s a probe). `--seam` runs only the configuration-
persistence module that holds rule 8 (about 14 s a probe); use it while iterating and the default for evidence.
The guard's Python is this interpreter (passed as ASSETOPS_GUARD_PYTHON).

Sets:
- `F-B n`: the 11 forms `.agent/S4-02d-phase-2-review.md` F-B recorded as missed by the line-based guard.
- `split <writer>`: a two-line UPDATE of a table the writer does not own (S4-05a phase-1 review L1), one per writer.
- `reverse <table family>`: a two-line write by the Foundation store into another writer's table.
- `dynamic ...` / `core ...` / `fragment` / `cte` / `upsert` / `second writer`: unresolved or non-text forms.
- `attestation ...` / `action ...` / `provenance ...` / `reverse attestation|action|provenance ...`: the writer
  policy merged from main 0d3114a3 (LR-01, S6-01a, S4-05a): UPDATE/DELETE/TRUNCATE/upsert, split, schema-qualified
  and quoted forms, and reverse ownership from another module.
- `w200 ...`: W2-00 event evidence (design section 7): an event partial-index or event-constraint conflict target,
  DO UPDATE on accepted evidence, an accepted-evidence INSERT without the message arbiter, foreign writers of the
  ledger-owned tables, and the two double-collision orders (message+event must resolve to message: event before
  message is refused; event+session with a free message must resolve to event: session before event is refused).
  The order probes REPLACE the pinned `_REREAD_ORDER` line rather than append a second one.
- `cold <table> ...`: W2-03 (migration 0022) cold episode and cold Finding tables: a foreign INSERT from the cold
  worker (`assessment_worker.py`, which owns the shared transaction but writes no table) and an UPDATE, DELETE and
  DO UPDATE from the owning store; `controls cold <table> insert` is the allowed INSERT. Rule 8 fails closed when
  any of these names is missing.
- `cold cold_consequence_* ...`: W2-04 (migration 0023) cold consequence tables: a foreign INSERT from the Finding store
  and an UPDATE, DELETE and DO UPDATE from the consequence store (sole INSERT-only owner); `cold cold_consequence_work
  runtime <verb>`: any runtime INSERT/UPDATE/DELETE/TRUNCATE/MERGE/COPY of the trigger-only work table;
  `cold work migration ...`: mutations of the 0023 migration text (rule 8 reads it on its own, since its runtime scan
  skips migrations): DO UPDATE, another arbiter, no arbiter, no work INSERT and a second INSERT without the arbiter.
  `controls cold <table> insert` and `controls cold work migration trigger insert` must pass. Rule 8 fails closed when
  any of these names is missing.
- `cold <cold consequence table> owner insert unseen`: W2-04 Q10, the store's one INSERT into that table replaced by a
  SELECT; rule 8's per-table inserts-seen assertion must report the check vacuous.
- `ev <EV consequence table> owner insert unseen`: W2-07 commit 2, the same vacuity probe for each EV consequence
  table (rule 8 requires each name).
- `work <table> ...`: W4-01 commit 2 (migration 0027) work tables: a foreign INSERT from the Finding store, an UPDATE,
  DELETE and DO UPDATE from the work store (sole INSERT-only owner), and `owner insert unseen` (the store's one INSERT
  replaced by a SELECT; rule 8's per-table inserts-seen assertion must report the check vacuous); `work truncate|merge|
  copy` from the work store; `controls work <table> insert` must pass. Rule 8 fails closed when any name is missing.
- `mini <table> ...`: W4-02 unit 1 (migration 0029) mini-depth tables, the same family as `work`, owned by
  `mini_depth/store.py`; `mini truncate`; `mini enqueue foreign call` (the assessment store calling the 0029 enqueue
  SQL) and `mini enqueue hour from publication` (the Foundation store calling anything but
  `mini_enqueue_configuration`). Rule 8 fails closed when any name is missing.
- `decision <table> ...`: W4-03 unit 1 (migration 0030) ten mini-decision tables, the same family as `work`, owned
  by `mini_decisions/store.py`; `decision truncate`; `controls decision <table> insert` must pass.
- `cold-scenario <table> ...`: W5-01b C4 (migration 0032) two cold scenario tables, the same family as `decision`,
  owned by `cold_scenarios/store.py`; `cold-scenario truncate`; `controls cold-scenario <table> insert` must pass.
- `cutover site_cutover_basis ...`: W4-02 q12-6 (B-L1) cutover basis table of migration 0029, owned INSERT-only by
  the Foundation store (its ON CONFLICT DO NOTHING is allowed): foreign INSERT, UPDATE, DELETE, DO UPDATE, TRUNCATE
  and `owner insert unseen`; `controls cutover site_cutover_basis insert` must pass.
- `controls`: allowed multiline SQL, case, aliases, reads, docstrings and comments in one run, which must pass,
  plus one allowed multiline insert per merged writer table family.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = "backend/assetops_backend"
SCHEDULE = f"{B}/scheduling/adapters/postgres_schedule_store.py"
FOUNDATION = f"{B}/sites/adapters/postgres_foundation_store.py"
LEDGER = f"{B}/evidence/adapters/postgres_evidence_ledger.py"
ACCESS = f"{B}/evidence/adapters/postgres_gateway_access.py"
ASSESS = f"{B}/analytics/adapters/postgres_assessment_store.py"
FINDING = f"{B}/analytics/adapters/postgres_finding_store.py"
ASSUMPTION = f"{B}/financials/adapters/postgres_assumption_store.py"
CONSEQUENCE = f"{B}/financials/adapters/postgres_consequence_store.py"
ACTION = f"{B}/actions/adapters/postgres_action_store.py"
WORK = f"{B}/work/adapters/postgres_work_store.py"
MINI = f"{B}/mini_depth/store.py"
DECISION = f"{B}/mini_decisions/store.py"
COLD_SCENARIO = f"{B}/cold_scenarios/store.py"
TICK = f"{B}/scheduling/tick.py"
WORKER = f"{B}/analytics/assessment_worker.py"
COLD_MIGRATION = "backend/migrations/versions/0023_w2_cold_consequence.py"
EV_MIGRATION = "backend/migrations/versions/0026_w2_ev_money.py"

NEVER = "never deletes, truncates, upserts or runs DDL"
SCHED_TABLES = "The schedule store updates only"
MERGE_COPY = "No product writer runs MERGE or COPY"
LITERAL_TARGET = "names its target table literally"
ASSESS_ONLY = "The assessment store inserts only"
FINDING_ONLY = "The Finding store only inserts into"
WORKER_WRITER = "A second product database writer in backend/assetops_backend/analytics/assessment_worker.py"
ACTION_NEVER = "The Action store never updates, deletes, truncates, upserts or runs DDL"
ACTION_ONLY = "The Action store only inserts"
PROV = "Source provenance is insert-only"
UPSERT = "is never upserted (no ON CONFLICT DO UPDATE)"
COLD_INSERT_ONLY = "is insert-only: no UPDATE, DELETE, TRUNCATE, MERGE or COPY from any module"
COLD_WORK = "Cold consequence work is written only by the migration 0023 triggers"
COLD_ARBITER = "keeps exactly the ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO NOTHING arbiter"
COLD_NO_INSERT = "Rule 8 found no INSERT INTO cold_consequence_work"
COLD_ARBITER_LINE = "ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO NOTHING;"
EV_WORK = "EV consequence work is written only by the migration 0026 triggers"
EV_ARBITER = ("keeps exactly the ON CONFLICT (tenant_id, site_id, window_start, window_end, dirty_basis_sha256) "
              "DO NOTHING arbiter")
EV_NO_INSERT = "Rule 8 found no INSERT INTO ev_consequence_work"
EV_ARBITER_LINE = "ON CONFLICT (tenant_id,site_id,window_start,window_end,dirty_basis_sha256) DO NOTHING;"
W200_ARBITER = "ON CONFLICT is allowed only as its three"
W200_MESSAGE = "keeps the accepted_evidence_message_unique DO NOTHING arbiter"
W200_ORDER = "rereads collisions in the fixed order message, event, session"
WORK_NEVER = "The work store never updates, deletes, truncates, upserts or runs DDL"
REREAD = "_REREAD_ORDER = (_REREAD_MESSAGE_SQL, _REREAD_EVENT_SQL, _REREAD_SESSION_SQL)"


def split(table: str, rest: str) -> str:
    """A two-line UPDATE: implicit concatenation across lines, the ordinary formatting of a long statement."""
    return f'_OPS02 = (\n    "UPDATE {table} "\n    "SET {rest}"\n)\n'


# (name, module, appended source, expected failure text)
NEGATIVE: list[tuple[str, str, str, str]] = [
    ("F-B 1 split other-table update", SCHEDULE, split("site", "lifecycle = :l WHERE tenant_id = :t"), SCHED_TABLES),
    ("F-B 2 split unlisted schedule column", SCHEDULE,
     split("schedule_site_head", "created_at = now() WHERE tenant_id = :t"),
     "may not update schedule_site_head.created_at"),
    ("F-B 3 split lowercase delete", SCHEDULE,
     '_OPS02 = (\n    "delete "\n    "from schedule_cursor where environment = :e"\n)\n', NEVER),
    ("F-B 4 triple-quoted update", SCHEDULE,
     '_OPS02 = """\nUPDATE site\nSET lifecycle = :l\nWHERE tenant_id = :t\n"""\n', SCHED_TABLES),
    ("F-B 5 escaped newline", SCHEDULE,
     '_OPS02 = "UPDATE site\\nSET lifecycle = :l WHERE tenant_id = :t"\n', SCHED_TABLES),
    ("F-B 6 comment-separated update", SCHEDULE,
     '_OPS02 = "UPDATE/**/site/**/SET lifecycle = :l WHERE tenant_id = :t"\n', SCHED_TABLES),
    ("F-B 7 comment-separated delete", SCHEDULE, '_OPS02 = "delete/**/from site where tenant_id = :t"\n', NEVER),
    ("F-B 8 merge", SCHEDULE,
     '_OPS02 = "MERGE INTO site s USING (SELECT 1) x ON true WHEN MATCHED THEN UPDATE SET lifecycle = \'x\'"\n',
     MERGE_COPY),
    ("F-B 9 core update", SCHEDULE,
     'from sqlalchemy import table, update\n_OPS02 = update(table("site")).values(lifecycle="x").where(True)\n',
     SCHED_TABLES),
    ("F-B 10 core delete", SCHEDULE,
     'from sqlalchemy import delete, table\n_OPS02 = delete(table("schedule_cursor"))\n', NEVER),
    ("F-B 11 lowercase copy", SCHEDULE, '_OPS02 = "copy site from stdin"\n', MERGE_COPY),
    # S4-05a phase-1 review L1: a two-line UPDATE is checked for every writer, not only the schedule store.
    ("split foundation", FOUNDATION, split("ingestion_batch", "processed_count = 0 WHERE id = :i"),
     "The Foundation store must not write ledger table 'ingestion_batch'"),
    ("split ledger", LEDGER, split("site", "lifecycle = :l WHERE id = :i"), "The evidence ledger writes only"),
    ("split access", ACCESS, split("gateway", "name = :n WHERE id = :g"), "The gateway access store inserts only"),
    ("split assessment", ASSESS, split("recompute_job", "site_id = :s WHERE id = :id"),
     "The assessment store inserts only"),
    ("split finding", FINDING, split("finding", "lifecycle = :l WHERE id = :i"), "The Finding store only inserts"),
    ("split assumption", ASSUMPTION, split("financial_assumption_revision", "value = :v WHERE id = :i"),
     "The assumption store only inserts"),
    ("split consequence", CONSEQUENCE, split("financial_consequence_revision", "amount = :a WHERE id = :i"),
     "The consequence store only inserts"),
    ("reverse finding", FOUNDATION, split("finding_revision", "lifecycle = :l WHERE id = :i"),
     "writes Finding table 'finding_revision'"),
    ("reverse assessment", FOUNDATION, split("assessment_revision", "scope = :s WHERE id = :i"),
     "writes assessment table 'assessment_revision'"),
    ("reverse access", FOUNDATION, split("gateway_credential", "revoked_at = now() WHERE id = :i"),
     "writes gateway access table 'gateway_credential'"),
    ("reverse assumption", FOUNDATION, split("financial_assumption_assignment", "recorded_to = now() WHERE id = :i"),
     "writes assumption table 'financial_assumption_assignment'"),
    ("reverse consequence", FOUNDATION, split("financial_consequence_revision", "amount = 0 WHERE id = :i"),
     "writes consequence table 'financial_consequence_revision'"),
    ("reverse schedule", FOUNDATION, split("schedule_cursor", "after_site_id = NULL WHERE environment = :e"),
     "writes schedule table 'schedule_cursor'"),
    ("reverse consequence work", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO financial_consequence_work "\n    "(id) VALUES (:i)"\n)\n',
     "Dirty consequence work is inserted only by the migration"),
    ("second writer split", TICK, split("schedule_tick_head", "heartbeat_at = now() WHERE environment = 'x'"),
     "A second product database writer"),
    ("q7 unlisted mini Site-head column", SCHEDULE, split("schedule_site_head", "mini_total = 1 WHERE tenant_id = :t"),
     "may not update schedule_site_head.mini_total"),
    ("q7 mini counter outside the schedule store", TICK,
     split("schedule_site_head", "mini_processed = 1 WHERE tenant_id = :t"), "A second product database writer"),
    ("dynamic f-string target", SCHEDULE,
     '_T = "site"\n_OPS02 = f"UPDATE {_T} SET stage = :s WHERE tenant_id = :t"\n', LITERAL_TARGET),
    ("dynamic percent target", FOUNDATION, '_T = "site"\n_OPS02 = "DELETE FROM %s WHERE id = :i" % _T\n',
     LITERAL_TARGET),
    ("dynamic format target", FOUNDATION, '_T = "site"\n_OPS02 = "INSERT INTO {} (id) VALUES (:i)".format(_T)\n',
     LITERAL_TARGET),
    ("dynamic set list", SCHEDULE,
     '_C = "created_at = now()"\n_OPS02 = "UPDATE schedule_site_head SET " + _C + " WHERE tenant_id = :t"\n',
     "names its SET columns literally"),
    ("fragment augmented assignment", FOUNDATION,
     '_OPS02 = "UPDATE site"\n_OPS02 += " SET lifecycle = :l WHERE id = :i"\n', "ends before its SET, VALUES or WHERE clause"),
    ("core aliased postgres insert", SCHEDULE,
     'from sqlalchemy import table\nfrom sqlalchemy.dialects.postgresql import insert as pg_insert\n'
     '_OPS02 = pg_insert(table("finding")).values(id=1)\n', "The schedule store only inserts into"),
    ("core dynamic table", FOUNDATION,
     'from sqlalchemy import update\n_T = None\n_OPS02 = update(_T).values(lifecycle="x")\n', LITERAL_TARGET),
    ("core table method", SCHEDULE, 'from sqlalchemy import table\n_OPS02 = table("schedule_cursor").delete()\n',
     NEVER),
    ("core module attribute", FINDING,
     'import sqlalchemy as sa\n_OPS02 = sa.update(sa.table("finding")).values(lifecycle="x")\n',
     "The Finding store only inserts"),
    ("core module postgresql insert", FINDING,
     'from sqlalchemy.dialects import postgresql\nfrom sqlalchemy import table\n'
     '_OPS02 = postgresql.insert(table("site")).values(id=1)\n', "The Finding store only inserts"),
    ("core module sql delete", FINDING,
     'from sqlalchemy import sql, table\n_OPS02 = sql.delete(table("finding"))\n', "The Finding store only inserts"),
    ("core fully dotted insert", FINDING,
     'import sqlalchemy\n_OPS02 = sqlalchemy.dialects.postgresql.insert(sqlalchemy.table("site")).values(id=1)\n',
     "The Finding store only inserts"),
    ("L1 keyword alias update", FINDING, '_OPS02 = "UPDATE site AS copy SET lifecycle = :l WHERE id = :i"\n',
     "The Finding store only inserts"),
    ("L2 quoted comment marker", FINDING,
     '_OPS02 = "SELECT \'--\' AS x; DELETE FROM site WHERE id = 1"\n', "The Finding store only inserts"),
    ("L2 bytes delete", FINDING, '_OPS02 = b"DELETE FROM site WHERE id = 1"\n', "The Finding store only inserts"),
    ("L3 lowercase fragment", FINDING, '_OPS02 = "update site"\n_OPS02 += " set lifecycle = :l"\n',
     "ends before its SET, VALUES or WHERE clause"),
    ("cte delete in finding", FINDING,
     '_OPS02 = "WITH x AS (DELETE FROM finding WHERE id = :i RETURNING id) SELECT 1"\n',
     "The Finding store only inserts"),
    ("split upsert", SCHEDULE,
     '_OPS02 = (\n    "INSERT INTO schedule_cursor (environment) VALUES (:e) "\n'
     '    "ON CONFLICT (environment) DO UPDATE SET after_site_id = NULL"\n)\n', NEVER),
    ("copy in foundation", FOUNDATION, '_OPS02 = "COPY site (id) FROM STDIN"\n', MERGE_COPY),
    # Merge with main 0d3114a3: LR-01 source_clock_attestation (assessment store, INSERT-only), S6-01a Action tables
    # (ninth writer, INSERT-only) and S4-05a provenance tables (ledger, INSERT-only, three DO NOTHING arbiters).
    ("attestation split update", ASSESS, split("source_clock_attestation", "proof_class = :p WHERE id = :i"),
     ASSESS_ONLY),
    ("attestation split lowercase delete", ASSESS,
     '_OPS02 = (\n    "delete from "\n    "source_clock_attestation where id = :i"\n)\n', ASSESS_ONLY),
    ("attestation qualified quoted truncate", ASSESS, '_OPS02 = "TRUNCATE public.\\"source_clock_attestation\\""\n',
     ASSESS_ONLY),
    ("attestation split upsert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO source_clock_attestation (id) VALUES (:i) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET proof_class = :p"\n)\n', UPSERT),
    ("reverse attestation update", FOUNDATION, split("source_clock_attestation", "proof_class = :p WHERE id = :i"),
     "writes assessment table 'source_clock_attestation'"),
    ("reverse attestation insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO source_clock_attestation "\n    "(id) VALUES (:i)"\n)\n',
     "writes assessment table 'source_clock_attestation'"),
    ("action split update", ACTION, split("action_event", "kind = :k WHERE id = :i"), ACTION_NEVER),
    ("action split lowercase delete", ACTION, '_OPS02 = (\n    "delete "\n    "from action where id = :i"\n)\n',
     ACTION_NEVER),
    ("action qualified quoted update", ACTION,
     '_OPS02 = (\n    "UPDATE public.\\"action\\" "\n    "SET status = :s WHERE id = :i"\n)\n', ACTION_ONLY),
    ("action truncate", ACTION, '_OPS02 = "truncate table action_policy_change"\n', ACTION_NEVER),
    ("action split upsert", ACTION,
     '_OPS02 = (\n    "INSERT INTO action_event (id) VALUES (:i) "\n    "ON CONFLICT (id) DO UPDATE SET kind = :k"\n)\n',
     UPSERT),
    ("action core delete", ACTION, 'import sqlalchemy as sa\n_OPS02 = sa.delete(sa.table("action_event"))\n',
     ACTION_ONLY),
    ("verification plan split update", ACTION, split("verification_plan", "later_start = :l WHERE id = :i"),
     ACTION_NEVER),
    ("verification outcome delete", ACTION, '_OPS02 = (\n    "DELETE "\n    "FROM verification_outcome WHERE id = :i"\n)\n',
     ACTION_NEVER),
    ("verification binding upsert", ACTION,
     '_OPS02 = (\n    "INSERT INTO verification_selection_binding (id) VALUES (:i) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET selection = :x"\n)\n', UPSERT),
    ("reverse verification insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO verification_metric "\n    "(outcome_id) VALUES (:i)"\n)\n',
     "writes Action table 'verification_metric'"),
    ("reverse action update", FOUNDATION, split("action", "status = :s WHERE id = :i"), "writes Action table 'action'"),
    ("reverse action insert", LEDGER,
     '_OPS02 = (\n    "INSERT INTO action_basis_evidence "\n    "(id) VALUES (:i)"\n)\n',
     "writes Action table 'action_basis_evidence'"),
    ("provenance split update", LEDGER, split("evidence_publication", "source_kind = :k WHERE id = :i"), PROV),
    ("provenance split qualified quoted update", LEDGER,
     '_OPS02 = (\n    "UPDATE public.\\"batch_publication_link\\" "\n    "SET batch_id = :b WHERE id = :i"\n)\n', PROV),
    ("provenance split lowercase delete", LEDGER,
     '_OPS02 = (\n    "delete from "\n    "evidence_publication where id = :i"\n)\n', PROV),
    ("provenance quoted truncate", LEDGER, '_OPS02 = "TRUNCATE TABLE ONLY \\"evidence_publication\\""\n', PROV),
    ("provenance split upsert", LEDGER,
     '_OPS02 = (\n    "INSERT INTO evidence_publication (id) VALUES (:i) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET source_kind = :k"\n)\n', UPSERT),
    ("provenance unlisted arbiter", LEDGER,
     '_OPS02 = (\n    "INSERT INTO batch_publication_link (id) VALUES (:i) "\n    "ON CONFLICT (id) DO NOTHING"\n)\n',
     "ON CONFLICT is allowed only as its three"),
    ("provenance core update", LEDGER,
     'import sqlalchemy as sa\n_OPS02 = sa.update(sa.table("evidence_publication")).values(source_kind="x")\n', PROV),
    ("reverse provenance insert", FOUNDATION,
     '_OPS02 = (\n    "INSERT INTO batch_publication_link "\n    "(id) VALUES (:i)"\n)\n',
     "writes source provenance table 'batch_publication_link'"),
    ("reverse provenance update", FINDING, split("evidence_publication", "source_kind = :k WHERE id = :i"), PROV),
    ("w200 event partial-index target", LEDGER,
     '_OPS02 = (\n    "INSERT INTO accepted_evidence (id) VALUES (:i) ON CONFLICT "\n'
     '    "(tenant_id, site_id, source_id, record_kind, event_id) WHERE family = \'EVENT\' DO NOTHING"\n)\n',
     W200_ARBITER),
    ("w200 event constraint target", LEDGER,
     '_OPS02 = (\n    "INSERT INTO accepted_evidence (id) VALUES (:i) ON CONFLICT ON CONSTRAINT "\n'
     '    "accepted_event_identity_unique DO NOTHING"\n)\n', W200_ARBITER),
    ("w200 accepted evidence do update", LEDGER,
     '_OPS02 = (\n    "INSERT INTO accepted_evidence (id) VALUES (:i) ON CONFLICT ON CONSTRAINT "\n'
     '    "accepted_evidence_message_unique DO UPDATE SET outcome = :o"\n)\n', "The evidence ledger never upserts"),
    ("w200 accepted evidence without message arbiter", LEDGER,
     '_OPS02 = (\n    "INSERT INTO accepted_evidence (id, record_kind, event_id) "\n    "VALUES (:i, :k, :e)"\n)\n',
     W200_MESSAGE),
    ("w200 foreign event evidence writer", FINDING,
     '_OPS02 = (\n    "INSERT INTO accepted_evidence "\n    "(id, record_kind) VALUES (:i, :k)"\n)\n',
     "writes ledger table 'accepted_evidence'"),
    ("w200 foreign rejection writer", ASSESS,
     '_OPS02 = (\n    "INSERT INTO evidence_rejection "\n    "(id, kind) VALUES (:i, :k)"\n)\n',
     "writes ledger table 'evidence_rejection'"),
    ("w200 foreign disposition writer", ACTION,
     '_OPS02 = (\n    "INSERT INTO ingestion_disposition "\n    "(batch_id, ordinal) VALUES (:b, :o)"\n)\n',
     "writes ledger table 'ingestion_disposition'"),
    ("w200 message+event order: event before message", LEDGER,
     ("replace", REREAD, "_REREAD_ORDER = (_REREAD_EVENT_SQL, _REREAD_MESSAGE_SQL, _REREAD_SESSION_SQL)"), W200_ORDER),
    ("w200 event+session order: session before event", LEDGER,
     ("replace", REREAD, "_REREAD_ORDER = (_REREAD_MESSAGE_SQL, _REREAD_SESSION_SQL, _REREAD_EVENT_SQL)"), W200_ORDER),
    ("w200 second reread order", LEDGER, REREAD + "\n", W200_ORDER),
    ("w200 real accepted insert loses its arbiter", LEDGER,
     ("replace", "ON CONFLICT ON CONSTRAINT accepted_evidence_message_unique DO NOTHING RETURNING id", "RETURNING id"),
     W200_MESSAGE),
    # W2-03 (migration 0022): the assessment store alone INSERTs the cold episode tables and the Finding store alone
    # INSERTs the cold Finding tables; the cold worker owns their shared transaction but writes no table. Each table
    # gets a foreign INSERT from the worker and an UPDATE, DELETE and DO UPDATE from its own owner. Rule 8 requires
    # every one of these names (configuration-persistence.ps1 fails closed when one is missing).
    ("cold cold_episode foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO cold_episode "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("cold cold_episode update", ASSESS, split("cold_episode", "site_id = :s WHERE id = :i"), ASSESS_ONLY),
    ("cold cold_episode delete", ASSESS, '_OPS02 = (\n    "delete from "\n    "cold_episode where id = :i"\n)\n', ASSESS_ONLY),
    ("cold cold_episode upsert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO cold_episode (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("cold cold_episode_revision foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO cold_episode_revision "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("cold cold_episode_revision update", ASSESS, split("cold_episode_revision", "site_id = :s WHERE id = :i"), ASSESS_ONLY),
    ("cold cold_episode_revision delete", ASSESS, '_OPS02 = (\n    "delete from "\n    "cold_episode_revision where id = :i"\n)\n', ASSESS_ONLY),
    ("cold cold_episode_revision upsert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO cold_episode_revision (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("cold cold_episode_evidence foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO cold_episode_evidence "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("cold cold_episode_evidence update", ASSESS, split("cold_episode_evidence", "site_id = :s WHERE id = :i"), ASSESS_ONLY),
    ("cold cold_episode_evidence delete", ASSESS, '_OPS02 = (\n    "delete from "\n    "cold_episode_evidence where id = :i"\n)\n', ASSESS_ONLY),
    ("cold cold_episode_evidence upsert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO cold_episode_evidence (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    # W2-06 (migration 0025): the assessment store alone INSERTs the four EV session tables; each gets a foreign
    # INSERT from the worker and an UPDATE, DELETE and DO UPDATE from its own owner (rule 8 fails closed without them).
    ("ev ev_session foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO ev_session "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("ev ev_session update", ASSESS, split("ev_session", "site_id = :s WHERE id = :i"), ASSESS_ONLY),
    ("ev ev_session delete", ASSESS, '_OPS02 = (\n    "delete from "\n    "ev_session where id = :i"\n)\n', ASSESS_ONLY),
    ("ev ev_session upsert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO ev_session (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("ev ev_session_revision foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO ev_session_revision "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("ev ev_session_revision update", ASSESS, split("ev_session_revision", "site_id = :s WHERE id = :i"), ASSESS_ONLY),
    ("ev ev_session_revision delete", ASSESS, '_OPS02 = (\n    "delete from "\n    "ev_session_revision where id = :i"\n)\n', ASSESS_ONLY),
    ("ev ev_session_revision upsert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO ev_session_revision (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("ev ev_session_evidence foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO ev_session_evidence "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("ev ev_session_evidence update", ASSESS, split("ev_session_evidence", "site_id = :s WHERE id = :i"), ASSESS_ONLY),
    ("ev ev_session_evidence delete", ASSESS, '_OPS02 = (\n    "delete from "\n    "ev_session_evidence where id = :i"\n)\n', ASSESS_ONLY),
    ("ev ev_session_evidence upsert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO ev_session_evidence (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("ev ev_meter_interval foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO ev_meter_interval "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("ev ev_meter_interval update", ASSESS, split("ev_meter_interval", "site_id = :s WHERE id = :i"), ASSESS_ONLY),
    ("ev ev_meter_interval delete", ASSESS, '_OPS02 = (\n    "delete from "\n    "ev_meter_interval where id = :i"\n)\n', ASSESS_ONLY),
    ("ev ev_meter_interval upsert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO ev_meter_interval (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    # W2-06: another product writer inserting an EV session table is caught as a cross-writer write, which holds
    # only because rule 8 lists the four tables in $assessTables.
    ("ev ev_session reverse update", FOUNDATION, split("ev_session", "site_id = :s WHERE id = :i"),
     "writes assessment table 'ev_session'"),
    ("ev ev_session_revision reverse update", FOUNDATION, split("ev_session_revision", "site_id = :s WHERE id = :i"),
     "writes assessment table 'ev_session_revision'"),
    ("ev ev_session_evidence reverse update", FOUNDATION, split("ev_session_evidence", "site_id = :s WHERE id = :i"),
     "writes assessment table 'ev_session_evidence'"),
    ("ev ev_meter_interval reverse update", FOUNDATION, split("ev_meter_interval", "site_id = :s WHERE id = :i"),
     "writes assessment table 'ev_meter_interval'"),
    ("cold finding foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO finding "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("cold finding update", FINDING, split("finding", "site_id = :s WHERE id = :i"), FINDING_ONLY),
    ("cold finding delete", FINDING, '_OPS02 = (\n    "delete from "\n    "finding where id = :i"\n)\n', FINDING_ONLY),
    ("cold finding upsert", FINDING,
     '_OPS02 = (\n    "INSERT INTO finding (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("cold finding_revision foreign insert", WORKER,
     '_OPS02 = (\n    "INSERT INTO finding_revision "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     WORKER_WRITER),
    ("cold finding_revision update", FINDING, split("finding_revision", "site_id = :s WHERE id = :i"), FINDING_ONLY),
    ("cold finding_revision delete", FINDING, '_OPS02 = (\n    "delete from "\n    "finding_revision where id = :i"\n)\n', FINDING_ONLY),
    ("cold finding_revision upsert", FINDING,
     '_OPS02 = (\n    "INSERT INTO finding_revision (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
]

# W2-04 (migration 0023): the consequence store alone INSERTs each cold consequence table, which no module updates,
# deletes or upserts; cold_consequence_work has no runtime writer at all, and its one migration INSERT keeps the
# dirty-key DO NOTHING arbiter. Rule 8 requires every one of these names.
NEGATIVE += [
    ("cold cold_consequence_revision foreign insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_revision "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     "writes consequence table 'cold_consequence_revision'"),
    ("cold cold_consequence_revision update", CONSEQUENCE, split("cold_consequence_revision", "state = :s WHERE id = :i"), COLD_INSERT_ONLY),
    ("cold cold_consequence_revision delete", CONSEQUENCE, '_OPS02 = (\n    "delete from "\n    "cold_consequence_revision where id = :i"\n)\n',
     COLD_INSERT_ONLY),
    ("cold cold_consequence_revision upsert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_revision (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("cold cold_consequence_evidence foreign insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_evidence "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     "writes consequence table 'cold_consequence_evidence'"),
    ("cold cold_consequence_evidence update", CONSEQUENCE, split("cold_consequence_evidence", "state = :s WHERE id = :i"), COLD_INSERT_ONLY),
    ("cold cold_consequence_evidence delete", CONSEQUENCE, '_OPS02 = (\n    "delete from "\n    "cold_consequence_evidence where id = :i"\n)\n',
     COLD_INSERT_ONLY),
    ("cold cold_consequence_evidence upsert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_evidence (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("cold cold_consequence_work_attempt foreign insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_work_attempt "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     "writes consequence table 'cold_consequence_work_attempt'"),
    ("cold cold_consequence_work_attempt update", CONSEQUENCE, split("cold_consequence_work_attempt", "state = :s WHERE id = :i"), COLD_INSERT_ONLY),
    ("cold cold_consequence_work_attempt delete", CONSEQUENCE, '_OPS02 = (\n    "delete from "\n    "cold_consequence_work_attempt where id = :i"\n)\n',
     COLD_INSERT_ONLY),
    ("cold cold_consequence_work_attempt upsert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_work_attempt (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("cold cold_consequence_work runtime insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_work (id, tenant_id) "\n    "VALUES (:i, :t) ON CONFLICT '
     '(tenant_id, site_id, dirty_key_sha256) DO NOTHING"\n)\n', COLD_WORK),
    ("cold cold_consequence_work runtime update", CONSEQUENCE,
     split("cold_consequence_work", "enqueued_at = now() WHERE id = :i"), COLD_WORK),
    ("cold cold_consequence_work runtime delete", CONSEQUENCE,
     '_OPS02 = (\n    "delete from "\n    "cold_consequence_work where id = :i"\n)\n', COLD_WORK),
    ("cold cold_consequence_work runtime truncate", CONSEQUENCE, '_OPS02 = "TRUNCATE cold_consequence_work"\n',
     COLD_WORK),
    ("cold cold_consequence_work runtime merge", CONSEQUENCE,
     '_OPS02 = "MERGE INTO cold_consequence_work w USING (SELECT 1) x ON true WHEN MATCHED THEN DELETE"\n',
     COLD_WORK),
    ("cold cold_consequence_work runtime copy", CONSEQUENCE, '_OPS02 = "copy cold_consequence_work from stdin"\n',
     COLD_WORK),
    ("cold work migration do update", COLD_MIGRATION,
     ("replace", COLD_ARBITER_LINE,
      "ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO UPDATE SET enqueued_at = clock_timestamp();"),
     COLD_ARBITER),
    ("cold work migration other arbiter", COLD_MIGRATION, ("replace", COLD_ARBITER_LINE, "ON CONFLICT (id) DO NOTHING;"),
     COLD_ARBITER),
    ("cold work migration no arbiter", COLD_MIGRATION, ("replace", COLD_ARBITER_LINE, ";"), COLD_ARBITER),
    ("cold work migration no insert", COLD_MIGRATION,
     ("replace", "    INSERT INTO cold_consequence_work (", "    INSERT INTO cold_consequence_work_attempt ("),
     COLD_NO_INSERT),
    ("cold work migration second insert without arbiter", COLD_MIGRATION,
     '_OPS02 = """\nINSERT INTO cold_consequence_work (id) VALUES (gen_random_uuid());\n"""\n', COLD_ARBITER),
]

# W2-04 Q10 (spec commit 2): the per-table "inserts seen" assertion is nonvacuous. Each probe turns the store's one
# real INSERT into a cold consequence table into a SELECT; rule 8 must then report that table's check as vacuous.
NEGATIVE += [
    (f"cold {table} owner insert unseen", CONSEQUENCE,
     ("replace", f'"INSERT INTO {table} ({columns}', f'"SELECT * FROM {table} WHERE ({columns}'),
     f"Rule 8 found no INSERT INTO {table} in ")
    for table, columns in (("cold_consequence_revision", "id, tenant_id, site_id, finding_revision_id, "),
                           ("cold_consequence_evidence", "consequence_revision_id, tenant_id, site_id, "),
                           ("cold_consequence_work_attempt", "id, tenant_id, site_id, work_id, "))
]

# W2-07 (enabled in spec commit 2): the same per-table vacuity probe for each EV consequence table.
def _ev_unseen(table: str, columns: str) -> tuple:
    return (CONSEQUENCE, ("replace", f'"INSERT INTO {table} ({columns}', f'"SELECT * FROM {table} WHERE ({columns}'),
            f"Rule 8 found no INSERT INTO {table} in ")


NEGATIVE += [
    ("ev ev_consequence_revision owner insert unseen",
     *_ev_unseen("ev_consequence_revision", "id, tenant_id, site_id, finding_revision_id, ")),
    ("ev ev_consequence_session owner insert unseen",
     *_ev_unseen("ev_consequence_session", "tenant_id, site_id, consequence_revision_id, ")),
    ("ev ev_consequence_evidence owner insert unseen",
     *_ev_unseen("ev_consequence_evidence", "tenant_id, site_id, consequence_revision_id, ")),
    ("ev ev_consequence_work_attempt owner insert unseen",
     *_ev_unseen("ev_consequence_work_attempt", "id, tenant_id, site_id, work_id, ")),
]

# W2-07 (migration 0026): the consequence store alone INSERTs each EV consequence table, which no module updates,
# deletes or upserts; ev_consequence_work has no runtime writer at all, and every 0026 INSERT into it keeps the
# exact scoped dirty-basis DO NOTHING arbiter. Rule 8 requires every one of these names.
NEGATIVE += [
    ("ev ev_consequence_revision foreign insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_revision "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     "writes consequence table 'ev_consequence_revision'"),
    ("ev ev_consequence_revision update", CONSEQUENCE, split("ev_consequence_revision", "state = :s WHERE id = :i"),
     "EV consequence table 'ev_consequence_revision' is insert-only"),
    ("ev ev_consequence_revision delete", CONSEQUENCE,
     '_OPS02 = (\n    "delete from "\n    "ev_consequence_revision where id = :i"\n)\n',
     "EV consequence table 'ev_consequence_revision' is insert-only"),
    ("ev ev_consequence_revision upsert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_revision (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("ev ev_consequence_session foreign insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_session "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     "writes consequence table 'ev_consequence_session'"),
    ("ev ev_consequence_session update", CONSEQUENCE, split("ev_consequence_session", "state = :s WHERE id = :i"),
     "EV consequence table 'ev_consequence_session' is insert-only"),
    ("ev ev_consequence_session delete", CONSEQUENCE,
     '_OPS02 = (\n    "delete from "\n    "ev_consequence_session where id = :i"\n)\n',
     "EV consequence table 'ev_consequence_session' is insert-only"),
    ("ev ev_consequence_session upsert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_session (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("ev ev_consequence_evidence foreign insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_evidence "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     "writes consequence table 'ev_consequence_evidence'"),
    ("ev ev_consequence_evidence update", CONSEQUENCE, split("ev_consequence_evidence", "state = :s WHERE id = :i"),
     "EV consequence table 'ev_consequence_evidence' is insert-only"),
    ("ev ev_consequence_evidence delete", CONSEQUENCE,
     '_OPS02 = (\n    "delete from "\n    "ev_consequence_evidence where id = :i"\n)\n',
     "EV consequence table 'ev_consequence_evidence' is insert-only"),
    ("ev ev_consequence_evidence upsert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_evidence (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
    ("ev ev_consequence_work_attempt foreign insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_work_attempt "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n',
     "writes consequence table 'ev_consequence_work_attempt'"),
    ("ev ev_consequence_work_attempt update", CONSEQUENCE, split("ev_consequence_work_attempt", "state = :s WHERE id = :i"),
     "EV consequence table 'ev_consequence_work_attempt' is insert-only"),
    ("ev ev_consequence_work_attempt delete", CONSEQUENCE,
     '_OPS02 = (\n    "delete from "\n    "ev_consequence_work_attempt where id = :i"\n)\n',
     "EV consequence table 'ev_consequence_work_attempt' is insert-only"),
    ("ev ev_consequence_work_attempt upsert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_work_attempt (id, tenant_id) VALUES (:i, :t) "\n'
     '    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n', UPSERT),
]
NEGATIVE += [
    ("ev ev_consequence_work runtime insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_work (id, tenant_id) "\n    "VALUES (:i, :t) ON CONFLICT '
     '(tenant_id, site_id, window_start, window_end, dirty_basis_sha256) DO NOTHING"\n)\n', EV_WORK),
    ("ev ev_consequence_work runtime update", CONSEQUENCE,
     split("ev_consequence_work", "created_at = now() WHERE id = :i"), EV_WORK),
    ("ev ev_consequence_work runtime delete", CONSEQUENCE,
     '_OPS02 = (\n    "delete from "\n    "ev_consequence_work where id = :i"\n)\n', EV_WORK),
    ("ev ev_consequence_work runtime truncate", CONSEQUENCE, '_OPS02 = "TRUNCATE ev_consequence_work"\n', EV_WORK),
    ("ev ev_consequence_work runtime merge", CONSEQUENCE,
     '_OPS02 = "MERGE INTO ev_consequence_work w USING (SELECT 1) x ON true WHEN MATCHED THEN DELETE"\n', EV_WORK),
    ("ev ev_consequence_work runtime copy", CONSEQUENCE, '_OPS02 = "copy ev_consequence_work from stdin"\n', EV_WORK),
    ("ev work migration do update", EV_MIGRATION,
     ("replace", EV_ARBITER_LINE,
      "ON CONFLICT (tenant_id,site_id,window_start,window_end,dirty_basis_sha256) DO UPDATE SET created_at=now();"),
     EV_ARBITER),
    ("ev work migration other arbiter", EV_MIGRATION, ("replace", EV_ARBITER_LINE, "ON CONFLICT (id) DO NOTHING;"),
     EV_ARBITER),
    ("ev work migration unscoped arbiter", EV_MIGRATION,
     ("replace", EV_ARBITER_LINE, "ON CONFLICT (site_id,window_start,window_end,dirty_basis_sha256) DO NOTHING;"),
     EV_ARBITER),
    ("ev work migration no arbiter", EV_MIGRATION, ("replace", EV_ARBITER_LINE, ";"), EV_ARBITER),
    ("ev work migration no insert", EV_MIGRATION,
     ("replace", " INSERT INTO ev_consequence_work(", " INSERT INTO ev_consequence_work_attempt("), EV_NO_INSERT),
    ("ev work migration second insert without arbiter", EV_MIGRATION,
     '_OPS02 = """\nINSERT INTO ev_consequence_work (id) VALUES (gen_random_uuid());\n"""\n', EV_ARBITER),
]

CONTROLS = (
    '_OPS02_A = """\nUPDATE schedule_site_head\nSET stage = :st,\n    stage_started_at = clock_timestamp()\n'
    'WHERE tenant_id = :t\n"""\n'
    '_OPS02_B = "update schedule_cursor set after_tenant_id = :t where environment = :e"\n'
    '_OPS02_C = (\n    "UPDATE schedule_enrolment "\n    "SET enrolled = :n, changed_at = clock_timestamp() "\n'
    '    "WHERE tenant_id = :t"\n)\n'
    '_OPS02_M = "UPDATE schedule_site_head SET mini_processed = :p, mini_deferred = :d, mini_failed = :f '
    'WHERE tenant_id = :t AND site_id = :s AND claim_token = :k RETURNING site_id"\n'
    '_OPS02_D = "UPDATE schedule_cursor AS c SET after_site_id = :s WHERE c.environment = :e"\n'
    '_OPS02_E = "Update Schedule_Cursor Set after_site_id = :s Where environment = :e"\n'
    '_OPS02_F = "SELECT h.stage FROM schedule_site_head h JOIN site s ON s.id = h.site_id WHERE h.tenant_id = :t '
    'FOR UPDATE OF h SKIP LOCKED"\n'
    '_OPS02_G = "SELECT updated_at FROM site WHERE lifecycle = \'update\'"\n'
    '_OPS02_H = "INSERT INTO schedule_cursor (environment, updated_at) VALUES (:e, now()) ON CONFLICT DO NOTHING"\n'
    '# DELETE FROM site WHERE id = 1 (a comment is not executed)\n'
    'def _ops02_doc():\n    """UPDATE site SET lifecycle = :l WHERE id = :i is documented here, never executed."""\n'
)


# Allowed multiline inserts into the tables main added, each in its owning writer (must pass).
# W4-01 commit 2 (migration 0027): the work store alone INSERTs each work table, which no module updates, deletes,
# upserts, truncates, merges or copies; each table keeps at least one owner INSERT in the store.
def _work_foreign(table: str) -> str:
    return f'_OPS02 = (\n    "INSERT INTO {table} "\n    "(id, tenant_id) VALUES (:i, :t)"\n)\n'


def _work_only(table: str) -> str:
    return f"Work table '{table}' is insert-only"


def _work_delete(table: str) -> str:
    return f'_OPS02 = (\n    "delete from "\n    "{table} where id = :i"\n)\n'


def _work_upsert(table: str) -> str:
    return (f'_OPS02 = (\n    "INSERT INTO {table} (id, tenant_id) VALUES (:i, :t) "\n'
            f'    "ON CONFLICT (id) DO UPDATE SET tenant_id = :t"\n)\n')


def _work_unseen(table: str) -> tuple:
    return (WORK, ("replace", f'"INSERT INTO {table} (', f'"SELECT * FROM {table} WHERE ('),
            f"Rule 8 found no INSERT INTO {table} in ")


# Rule 8 requires each probe name literally, so every entry is spelled out.
NEGATIVE += [
    ("work work_case foreign insert", FINDING, _work_foreign("work_case"), "writes work table 'work_case'"),
    ("work work_case update", WORK, split("work_case", "site_id = :s WHERE id = :i"), _work_only("work_case")),
    ("work work_case delete", WORK, _work_delete("work_case"), _work_only("work_case")),
    ("work work_case upsert", WORK, _work_upsert("work_case"), UPSERT),
    ("work work_case owner insert unseen", *_work_unseen("work_case")),
    ("work incident foreign insert", FINDING, _work_foreign("incident"), "writes work table 'incident'"),
    ("work incident update", WORK, split("incident", "site_id = :s WHERE id = :i"), _work_only("incident")),
    ("work incident delete", WORK, _work_delete("incident"), _work_only("incident")),
    ("work incident upsert", WORK, _work_upsert("incident"), UPSERT),
    ("work incident owner insert unseen", *_work_unseen("incident")),
    ("work maintenance_work_request foreign insert", FINDING, _work_foreign("maintenance_work_request"), "writes work table 'maintenance_work_request'"),
    ("work maintenance_work_request update", WORK, split("maintenance_work_request", "site_id = :s WHERE id = :i"), _work_only("maintenance_work_request")),
    ("work maintenance_work_request delete", WORK, _work_delete("maintenance_work_request"), _work_only("maintenance_work_request")),
    ("work maintenance_work_request upsert", WORK, _work_upsert("maintenance_work_request"), UPSERT),
    ("work maintenance_work_request owner insert unseen", *_work_unseen("maintenance_work_request")),
    ("work work_case_revision foreign insert", FINDING, _work_foreign("work_case_revision"), "writes work table 'work_case_revision'"),
    ("work work_case_revision update", WORK, split("work_case_revision", "site_id = :s WHERE id = :i"), _work_only("work_case_revision")),
    ("work work_case_revision delete", WORK, _work_delete("work_case_revision"), _work_only("work_case_revision")),
    ("work work_case_revision upsert", WORK, _work_upsert("work_case_revision"), UPSERT),
    ("work work_case_revision owner insert unseen", *_work_unseen("work_case_revision")),
    ("work work_case_finding_link foreign insert", FINDING, _work_foreign("work_case_finding_link"), "writes work table 'work_case_finding_link'"),
    ("work work_case_finding_link update", WORK, split("work_case_finding_link", "site_id = :s WHERE id = :i"), _work_only("work_case_finding_link")),
    ("work work_case_finding_link delete", WORK, _work_delete("work_case_finding_link"), _work_only("work_case_finding_link")),
    ("work work_case_finding_link upsert", WORK, _work_upsert("work_case_finding_link"), UPSERT),
    ("work work_case_finding_link owner insert unseen", *_work_unseen("work_case_finding_link")),
    ("work work_case_action_link foreign insert", FINDING, _work_foreign("work_case_action_link"), "writes work table 'work_case_action_link'"),
    ("work work_case_action_link update", WORK, split("work_case_action_link", "site_id = :s WHERE id = :i"), _work_only("work_case_action_link")),
    ("work work_case_action_link delete", WORK, _work_delete("work_case_action_link"), _work_only("work_case_action_link")),
    ("work work_case_action_link upsert", WORK, _work_upsert("work_case_action_link"), UPSERT),
    ("work work_case_action_link owner insert unseen", *_work_unseen("work_case_action_link")),
    ("work work_case_evidence foreign insert", FINDING, _work_foreign("work_case_evidence"), "writes work table 'work_case_evidence'"),
    ("work work_case_evidence update", WORK, split("work_case_evidence", "site_id = :s WHERE id = :i"), _work_only("work_case_evidence")),
    ("work work_case_evidence delete", WORK, _work_delete("work_case_evidence"), _work_only("work_case_evidence")),
    ("work work_case_evidence upsert", WORK, _work_upsert("work_case_evidence"), UPSERT),
    ("work work_case_evidence owner insert unseen", *_work_unseen("work_case_evidence")),
    ("work work_event foreign insert", FINDING, _work_foreign("work_event"), "writes work table 'work_event'"),
    ("work work_event update", WORK, split("work_event", "site_id = :s WHERE id = :i"), _work_only("work_event")),
    ("work work_event delete", WORK, _work_delete("work_event"), _work_only("work_event")),
    ("work work_event upsert", WORK, _work_upsert("work_event"), UPSERT),
    ("work work_event owner insert unseen", *_work_unseen("work_event")),
    ("work maintenance_plan foreign insert", FINDING, _work_foreign("maintenance_plan"), "writes work table 'maintenance_plan'"),
    ("work maintenance_plan update", WORK, split("maintenance_plan", "site_id = :s WHERE id = :i"), _work_only("maintenance_plan")),
    ("work maintenance_plan delete", WORK, _work_delete("maintenance_plan"), _work_only("maintenance_plan")),
    ("work maintenance_plan upsert", WORK, _work_upsert("maintenance_plan"), UPSERT),
    ("work maintenance_plan owner insert unseen", *_work_unseen("maintenance_plan")),
    ("work maintenance_record foreign insert", FINDING, _work_foreign("maintenance_record"), "writes work table 'maintenance_record'"),
    ("work maintenance_record update", WORK, split("maintenance_record", "site_id = :s WHERE id = :i"), _work_only("maintenance_record")),
    ("work maintenance_record delete", WORK, _work_delete("maintenance_record"), _work_only("maintenance_record")),
    ("work maintenance_record upsert", WORK, _work_upsert("maintenance_record"), UPSERT),
    ("work maintenance_record owner insert unseen", *_work_unseen("maintenance_record")),
    ("work operational_record foreign insert", FINDING, _work_foreign("operational_record"), "writes work table 'operational_record'"),
    ("work operational_record update", WORK, split("operational_record", "site_id = :s WHERE id = :i"), _work_only("operational_record")),
    ("work operational_record delete", WORK, _work_delete("operational_record"), _work_only("operational_record")),
    ("work operational_record upsert", WORK, _work_upsert("operational_record"), UPSERT),
    ("work operational_record owner insert unseen", *_work_unseen("operational_record")),
]
NEGATIVE += [
    ("work truncate", WORK, '_OPS02 = "TRUNCATE work_case"\n', WORK_NEVER),
    ("work merge", WORK, '_OPS02 = "MERGE INTO work_case USING site ON true WHEN MATCHED THEN DO NOTHING"\n',
     MERGE_COPY),
    ("work copy", WORK, '_OPS02 = "COPY work_event FROM STDIN"\n', MERGE_COPY),
]

# W4-02 unit 1 (migration 0029): the mini-depth store alone INSERTs each mini table, which no module updates,
# deletes, upserts, truncates, merges or copies; each table keeps at least one owner INSERT in the store. Only the
# Foundation store calls the 0029 enqueue SQL, and only `mini_enqueue_configuration`.
def _mini_only(table: str) -> str:
    return f"Mini-depth table '{table}' is insert-only"


def _mini_unseen(table: str) -> tuple:
    return (MINI, ("replace", f'"INSERT INTO {table} (', f'"SELECT * FROM {table} WHERE ('),
            f"Rule 8 found no INSERT INTO {table} in ")


MINI_ENQUEUE = "calls the 0029 mini enqueue SQL"
NEGATIVE += [
    ("mini mini_depth_revision foreign insert", FINDING, _work_foreign("mini_depth_revision"),
     "writes mini-depth table 'mini_depth_revision'"),
    ("mini mini_depth_revision update", MINI, split("mini_depth_revision", "site_id = :s WHERE id = :i"),
     _mini_only("mini_depth_revision")),
    ("mini mini_depth_revision delete", MINI, _work_delete("mini_depth_revision"), _mini_only("mini_depth_revision")),
    ("mini mini_depth_revision upsert", MINI, _work_upsert("mini_depth_revision"), _mini_only("mini_depth_revision")),
    ("mini mini_depth_revision owner insert unseen", *_mini_unseen("mini_depth_revision")),
    ("mini mini_depth_revision_evidence foreign insert", FINDING, _work_foreign("mini_depth_revision_evidence"),
     "writes mini-depth table 'mini_depth_revision_evidence'"),
    ("mini mini_depth_revision_evidence update", MINI,
     split("mini_depth_revision_evidence", "site_id = :s WHERE revision_id = :i"),
     _mini_only("mini_depth_revision_evidence")),
    ("mini mini_depth_revision_evidence delete", MINI, _work_delete("mini_depth_revision_evidence"),
     _mini_only("mini_depth_revision_evidence")),
    ("mini mini_depth_revision_evidence upsert", MINI, _work_upsert("mini_depth_revision_evidence"),
     _mini_only("mini_depth_revision_evidence")),
    ("mini mini_depth_revision_evidence owner insert unseen", *_mini_unseen("mini_depth_revision_evidence")),
    ("mini mini_depth_selection foreign insert", FINDING, _work_foreign("mini_depth_selection"),
     "writes mini-depth table 'mini_depth_selection'"),
    ("mini mini_depth_selection update", MINI, split("mini_depth_selection", "site_id = :s WHERE seq = :i"),
     _mini_only("mini_depth_selection")),
    ("mini mini_depth_selection delete", MINI, _work_delete("mini_depth_selection"), _mini_only("mini_depth_selection")),
    ("mini mini_depth_selection upsert", MINI, _work_upsert("mini_depth_selection"), _mini_only("mini_depth_selection")),
    ("mini mini_depth_selection owner insert unseen", *_mini_unseen("mini_depth_selection")),
    ("mini truncate", MINI, '_OPS02 = "TRUNCATE mini_depth_selection"\n',
     "The mini-depth store never updates, deletes, truncates, upserts or runs DDL"),
    ("mini enqueue foreign call", ASSESS,
     '_OPS02 = "SELECT mini_enqueue_configuration(:t, :s, :f, :to, :at)"\n', MINI_ENQUEUE),
    ("mini enqueue hour from publication", FOUNDATION,
     '_OPS02 = "SELECT mini_enqueue_hour(:t, :s, :d, :lo, :hi, NULL, :at)"\n', MINI_ENQUEUE),
]

# W4-02 q12-6 (final review B-L1): the Foundation store alone INSERTs `site_cutover_basis`, which no module
# updates, deletes, upserts or truncates; the store keeps its one owner INSERT.
CUTOVER_ONLY = "Cutover basis table 'site_cutover_basis' is insert-only"
NEGATIVE += [
    ("cutover site_cutover_basis foreign insert", FINDING, _work_foreign("site_cutover_basis"),
     "writes cutover basis table 'site_cutover_basis'"),
    ("cutover site_cutover_basis update", FOUNDATION,
     split("site_cutover_basis", "source_sha256 = :s WHERE site_id = :i"), CUTOVER_ONLY),
    ("cutover site_cutover_basis delete", FOUNDATION, _work_delete("site_cutover_basis"), CUTOVER_ONLY),
    ("cutover site_cutover_basis upsert", FOUNDATION, _work_upsert("site_cutover_basis"), CUTOVER_ONLY),
    ("cutover site_cutover_basis truncate", FOUNDATION, '_OPS02 = "TRUNCATE site_cutover_basis"\n', CUTOVER_ONLY),
    ("cutover site_cutover_basis owner insert unseen", FOUNDATION,
     ("replace", '"INSERT INTO site_cutover_basis (', '"SELECT * FROM site_cutover_basis WHERE ('),
     "Rule 8 found no INSERT INTO site_cutover_basis in "),
]

# W4-03 unit 1 (migration 0030): the mini-decision store alone INSERTs each of the ten decision tables, which no
# module updates, deletes, upserts, truncates, merges or copies; each table keeps at least one owner INSERT.

def _decision_only(table: str) -> str:
    return f"Mini-decision table '{table}' is insert-only"


def _decision_unseen(table: str) -> tuple:
    return (DECISION, ("replace", f'"INSERT INTO {table} (', f'"SELECT * FROM {table} WHERE ('),
            f"Rule 8 found no INSERT INTO {table} in ")


NEGATIVE += [
    ("decision mini_scenario foreign insert", FINDING, _work_foreign("mini_scenario"), "writes mini-decision table 'mini_scenario'"),
    ("decision mini_scenario update", DECISION, split("mini_scenario", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_scenario")),
    ("decision mini_scenario delete", DECISION, _work_delete("mini_scenario"), _decision_only("mini_scenario")),
    ("decision mini_scenario upsert", DECISION, _work_upsert("mini_scenario"), _decision_only("mini_scenario")),
    ("decision mini_scenario owner insert unseen", *_decision_unseen("mini_scenario")),
    ("decision mini_scenario_revision foreign insert", FINDING, _work_foreign("mini_scenario_revision"), "writes mini-decision table 'mini_scenario_revision'"),
    ("decision mini_scenario_revision update", DECISION, split("mini_scenario_revision", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_scenario_revision")),
    ("decision mini_scenario_revision delete", DECISION, _work_delete("mini_scenario_revision"), _decision_only("mini_scenario_revision")),
    ("decision mini_scenario_revision upsert", DECISION, _work_upsert("mini_scenario_revision"), _decision_only("mini_scenario_revision")),
    ("decision mini_scenario_revision owner insert unseen", *_decision_unseen("mini_scenario_revision")),
    ("decision mini_alternative_revision foreign insert", FINDING, _work_foreign("mini_alternative_revision"), "writes mini-decision table 'mini_alternative_revision'"),
    ("decision mini_alternative_revision update", DECISION, split("mini_alternative_revision", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_alternative_revision")),
    ("decision mini_alternative_revision delete", DECISION, _work_delete("mini_alternative_revision"), _decision_only("mini_alternative_revision")),
    ("decision mini_alternative_revision upsert", DECISION, _work_upsert("mini_alternative_revision"), _decision_only("mini_alternative_revision")),
    ("decision mini_alternative_revision owner insert unseen", *_decision_unseen("mini_alternative_revision")),
    ("decision mini_alternative_evidence foreign insert", FINDING, _work_foreign("mini_alternative_evidence"), "writes mini-decision table 'mini_alternative_evidence'"),
    ("decision mini_alternative_evidence update", DECISION, split("mini_alternative_evidence", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_alternative_evidence")),
    ("decision mini_alternative_evidence delete", DECISION, _work_delete("mini_alternative_evidence"), _decision_only("mini_alternative_evidence")),
    ("decision mini_alternative_evidence upsert", DECISION, _work_upsert("mini_alternative_evidence"), _decision_only("mini_alternative_evidence")),
    ("decision mini_alternative_evidence owner insert unseen", *_decision_unseen("mini_alternative_evidence")),
    ("decision mini_opportunity foreign insert", FINDING, _work_foreign("mini_opportunity"), "writes mini-decision table 'mini_opportunity'"),
    ("decision mini_opportunity update", DECISION, split("mini_opportunity", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_opportunity")),
    ("decision mini_opportunity delete", DECISION, _work_delete("mini_opportunity"), _decision_only("mini_opportunity")),
    ("decision mini_opportunity upsert", DECISION, _work_upsert("mini_opportunity"), _decision_only("mini_opportunity")),
    ("decision mini_opportunity owner insert unseen", *_decision_unseen("mini_opportunity")),
    ("decision mini_opportunity_revision foreign insert", FINDING, _work_foreign("mini_opportunity_revision"), "writes mini-decision table 'mini_opportunity_revision'"),
    ("decision mini_opportunity_revision update", DECISION, split("mini_opportunity_revision", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_opportunity_revision")),
    ("decision mini_opportunity_revision delete", DECISION, _work_delete("mini_opportunity_revision"), _decision_only("mini_opportunity_revision")),
    ("decision mini_opportunity_revision upsert", DECISION, _work_upsert("mini_opportunity_revision"), _decision_only("mini_opportunity_revision")),
    ("decision mini_opportunity_revision owner insert unseen", *_decision_unseen("mini_opportunity_revision")),
    ("decision mini_opportunity_evidence foreign insert", FINDING, _work_foreign("mini_opportunity_evidence"), "writes mini-decision table 'mini_opportunity_evidence'"),
    ("decision mini_opportunity_evidence update", DECISION, split("mini_opportunity_evidence", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_opportunity_evidence")),
    ("decision mini_opportunity_evidence delete", DECISION, _work_delete("mini_opportunity_evidence"), _decision_only("mini_opportunity_evidence")),
    ("decision mini_opportunity_evidence upsert", DECISION, _work_upsert("mini_opportunity_evidence"), _decision_only("mini_opportunity_evidence")),
    ("decision mini_opportunity_evidence owner insert unseen", *_decision_unseen("mini_opportunity_evidence")),
    ("decision mini_opportunity_selection foreign insert", FINDING, _work_foreign("mini_opportunity_selection"), "writes mini-decision table 'mini_opportunity_selection'"),
    ("decision mini_opportunity_selection update", DECISION, split("mini_opportunity_selection", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_opportunity_selection")),
    ("decision mini_opportunity_selection delete", DECISION, _work_delete("mini_opportunity_selection"), _decision_only("mini_opportunity_selection")),
    ("decision mini_opportunity_selection upsert", DECISION, _work_upsert("mini_opportunity_selection"), _decision_only("mini_opportunity_selection")),
    ("decision mini_opportunity_selection owner insert unseen", *_decision_unseen("mini_opportunity_selection")),
    ("decision mini_decision_work_link foreign insert", FINDING, _work_foreign("mini_decision_work_link"), "writes mini-decision table 'mini_decision_work_link'"),
    ("decision mini_decision_work_link update", DECISION, split("mini_decision_work_link", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_decision_work_link")),
    ("decision mini_decision_work_link delete", DECISION, _work_delete("mini_decision_work_link"), _decision_only("mini_decision_work_link")),
    ("decision mini_decision_work_link upsert", DECISION, _work_upsert("mini_decision_work_link"), _decision_only("mini_decision_work_link")),
    ("decision mini_decision_work_link owner insert unseen", *_decision_unseen("mini_decision_work_link")),
    ("decision mini_opportunity_scenario_link foreign insert", FINDING, _work_foreign("mini_opportunity_scenario_link"), "writes mini-decision table 'mini_opportunity_scenario_link'"),
    ("decision mini_opportunity_scenario_link update", DECISION, split("mini_opportunity_scenario_link", "site_id = :s WHERE tenant_id = :i"), _decision_only("mini_opportunity_scenario_link")),
    ("decision mini_opportunity_scenario_link delete", DECISION, _work_delete("mini_opportunity_scenario_link"), _decision_only("mini_opportunity_scenario_link")),
    ("decision mini_opportunity_scenario_link upsert", DECISION, _work_upsert("mini_opportunity_scenario_link"), _decision_only("mini_opportunity_scenario_link")),
    ("decision mini_opportunity_scenario_link owner insert unseen", *_decision_unseen("mini_opportunity_scenario_link")),
]
NEGATIVE += [
    ("decision truncate", DECISION, '_OPS02 = "TRUNCATE mini_scenario"\n',
     "The mini-decision store never updates, deletes, truncates, upserts or runs DDL"),
]

# W5-01b C4 (migration 0032): the cold scenario store alone INSERTs both cold scenario tables, which no module
# updates, deletes, upserts, truncates, merges or copies; each table keeps at least one owner INSERT.

def _cold_scenario_only(table: str) -> str:
    return f"Cold scenario table '{table}' is insert-only"


def _cold_scenario_unseen(table: str) -> tuple:
    return (COLD_SCENARIO, ("replace", f'"INSERT INTO {table} (', f'"SELECT * FROM {table} WHERE ('),
            f"Rule 8 found no INSERT INTO {table} in ")


NEGATIVE += [
    ("cold-scenario cold_scenario foreign insert", FINDING, _work_foreign("cold_scenario"), "writes cold scenario table 'cold_scenario'"),
    ("cold-scenario cold_scenario update", COLD_SCENARIO, split("cold_scenario", "site_id = :s WHERE tenant_id = :i"), _cold_scenario_only("cold_scenario")),
    ("cold-scenario cold_scenario delete", COLD_SCENARIO, _work_delete("cold_scenario"), _cold_scenario_only("cold_scenario")),
    ("cold-scenario cold_scenario upsert", COLD_SCENARIO, _work_upsert("cold_scenario"), _cold_scenario_only("cold_scenario")),
    ("cold-scenario cold_scenario owner insert unseen", *_cold_scenario_unseen("cold_scenario")),
    ("cold-scenario cold_scenario_revision foreign insert", FINDING, _work_foreign("cold_scenario_revision"), "writes cold scenario table 'cold_scenario_revision'"),
    ("cold-scenario cold_scenario_revision update", COLD_SCENARIO, split("cold_scenario_revision", "site_id = :s WHERE tenant_id = :i"), _cold_scenario_only("cold_scenario_revision")),
    ("cold-scenario cold_scenario_revision delete", COLD_SCENARIO, _work_delete("cold_scenario_revision"), _cold_scenario_only("cold_scenario_revision")),
    ("cold-scenario cold_scenario_revision upsert", COLD_SCENARIO, _work_upsert("cold_scenario_revision"), _cold_scenario_only("cold_scenario_revision")),
    ("cold-scenario cold_scenario_revision owner insert unseen", *_cold_scenario_unseen("cold_scenario_revision")),
    ("cold-scenario truncate", COLD_SCENARIO, '_OPS02 = "TRUNCATE cold_scenario"\n',
     "The cold scenario store never updates, deletes, truncates, upserts or runs DDL"),
]

WRITER_CONTROLS: list[tuple[str, str, str]] = [
    ("controls attestation insert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO source_clock_attestation (id, proof_class) "\n    "VALUES (:i, :p)"\n)\n'),
    ("controls action insert", ACTION,
     '_OPS02 = (\n    "INSERT INTO action_event (id, kind) "\n    "VALUES (:i, :k)"\n)\n'),
    ("controls verification plan insert", ACTION,
     '_OPS02 = (\n    "INSERT INTO verification_plan (id, action_id) "\n    "VALUES (:i, :a)"\n)\n'),
    ("controls provenance insert and arbiter", LEDGER,
     '_OPS02_A = (\n    "INSERT INTO evidence_publication (id) "\n    "VALUES (:i)"\n)\n'
     '_OPS02_B = (\n    "INSERT INTO ingestion_batch (id) VALUES (:i) ON CONFLICT ON CONSTRAINT "\n'
     '    "ingestion_batch_external_unique DO NOTHING"\n)\n'),
    ("controls w200 event insert with message arbiter", LEDGER,
     '_OPS02 = (\n    "INSERT INTO accepted_evidence (id, record_kind, event_id, session_id) "\n'
     '    "VALUES (:i, :k, :e, :s) ON CONFLICT ON CONSTRAINT accepted_evidence_message_unique DO NOTHING"\n)\n'),
    # W2-03: one allowed multiline INSERT per cold table in its owning writer (must pass).
    ("controls cold cold_episode insert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO cold_episode (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls cold cold_episode_revision insert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO cold_episode_revision (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls cold cold_episode_evidence insert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO cold_episode_evidence (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    # W2-06: one allowed multiline INSERT per EV session table in the assessment store (must pass).
    ("controls ev ev_session insert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO ev_session (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls ev ev_session_revision insert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO ev_session_revision (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls ev ev_session_evidence insert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO ev_session_evidence (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls ev ev_meter_interval insert", ASSESS,
     '_OPS02 = (\n    "INSERT INTO ev_meter_interval (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls cold finding insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO finding (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls cold finding_revision insert", FINDING,
     '_OPS02 = (\n    "INSERT INTO finding_revision (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    # W2-04: one allowed multiline INSERT per cold consequence table in the consequence store, and a second
    # arbitrated work INSERT in the 0023 migration text (must pass).
    ("controls cold cold_consequence_revision insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_revision (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls cold cold_consequence_evidence insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_evidence (consequence_revision_id, evidence_id) "\n'
     '    "VALUES (:c, :e)"\n)\n'),
    ("controls cold cold_consequence_work_attempt insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO cold_consequence_work_attempt (id, work_id) "\n    "VALUES (:i, :w)"\n)\n'),
    ("controls cold work migration trigger insert", COLD_MIGRATION,
     '_OPS02 = """\nINSERT INTO cold_consequence_work (id) VALUES (gen_random_uuid())\n'
     'ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO NOTHING;\n"""\n'),
    # W2-07: one allowed multiline INSERT per EV consequence table in the consequence store, and a second
    # arbitrated work INSERT in the 0026 migration text (must pass).
    ("controls ev ev_consequence_revision insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_revision (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls ev ev_consequence_session insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_session (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls ev ev_consequence_evidence insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_evidence (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls ev ev_consequence_work_attempt insert", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO ev_consequence_work_attempt (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'),
    ("controls ev work migration trigger insert", EV_MIGRATION,
     '_OPS02 = """\nINSERT INTO ev_consequence_work (id) VALUES (gen_random_uuid())\n'
     'ON CONFLICT (tenant_id, site_id, window_start, window_end, dirty_basis_sha256) DO NOTHING;\n"""\n'),
]

# W4-01 commit 2: one allowed multiline INSERT per work table in the work store (must pass).
def _work_control(table: str) -> str:
    return f'_OPS02 = (\n    "INSERT INTO {table} (id, tenant_id, site_id) "\n    "VALUES (:i, :t, :s)"\n)\n'


WRITER_CONTROLS += [
    ("controls work work_case insert", WORK, _work_control("work_case")),
    ("controls work incident insert", WORK, _work_control("incident")),
    ("controls work maintenance_work_request insert", WORK, _work_control("maintenance_work_request")),
    ("controls work work_case_revision insert", WORK, _work_control("work_case_revision")),
    ("controls work work_case_finding_link insert", WORK, _work_control("work_case_finding_link")),
    ("controls work work_case_action_link insert", WORK, _work_control("work_case_action_link")),
    ("controls work work_case_evidence insert", WORK, _work_control("work_case_evidence")),
    ("controls work work_event insert", WORK, _work_control("work_event")),
    ("controls work maintenance_plan insert", WORK, _work_control("maintenance_plan")),
    ("controls work maintenance_record insert", WORK, _work_control("maintenance_record")),
    ("controls work operational_record insert", WORK, _work_control("operational_record")),
]


WRITER_CONTROLS += [
    ("controls mini mini_depth_revision insert", MINI, _work_control("mini_depth_revision")),
    ("controls mini mini_depth_revision_evidence insert", MINI, _work_control("mini_depth_revision_evidence")),
    ("controls mini mini_depth_selection insert", MINI, _work_control("mini_depth_selection")),
    ("controls cutover site_cutover_basis insert", FOUNDATION, _work_control("site_cutover_basis")),
]
WRITER_CONTROLS += [
    ("controls decision mini_scenario insert", DECISION, _work_control("mini_scenario")),
    ("controls decision mini_scenario_revision insert", DECISION, _work_control("mini_scenario_revision")),
    ("controls decision mini_alternative_revision insert", DECISION, _work_control("mini_alternative_revision")),
    ("controls decision mini_alternative_evidence insert", DECISION, _work_control("mini_alternative_evidence")),
    ("controls decision mini_opportunity insert", DECISION, _work_control("mini_opportunity")),
    ("controls decision mini_opportunity_revision insert", DECISION, _work_control("mini_opportunity_revision")),
    ("controls decision mini_opportunity_evidence insert", DECISION, _work_control("mini_opportunity_evidence")),
    ("controls decision mini_opportunity_selection insert", DECISION, _work_control("mini_opportunity_selection")),
    ("controls decision mini_decision_work_link insert", DECISION, _work_control("mini_decision_work_link")),
    ("controls decision mini_opportunity_scenario_link insert", DECISION, _work_control("mini_opportunity_scenario_link")),
]
WRITER_CONTROLS += [
    ("controls cold-scenario cold_scenario insert", COLD_SCENARIO, _work_control("cold_scenario")),
    ("controls cold-scenario cold_scenario_revision insert", COLD_SCENARIO, _work_control("cold_scenario_revision")),
]


# W4-03 closure 4 S2: the assessment store's one coalescing UPDATE of a PENDING mini_opportunity job is allowed only
# in its exact text; another domain, status or column, a widened predicate, a foreign writer and a missing UPDATE fail.
_OPP_COALESCE = ("UPDATE recompute_job SET available_at = greatest(available_at, :at) WHERE id = :pending_id "
                 "AND domain = 'mini_opportunity' AND status = 'PENDING'")
NEGATIVE += [
    ("opportunity coalesce other domain", ASSESS,
     '_OPS02 = "' + _OPP_COALESCE.replace("'mini_opportunity'", "'mini_renewable'") + '"\n', ASSESS_ONLY),
    ("opportunity coalesce other status", ASSESS,
     '_OPS02 = "' + _OPP_COALESCE.replace("'PENDING'", "'DONE'") + '"\n', ASSESS_ONLY),
    ("opportunity coalesce widened", ASSESS, '_OPS02 = "' + _OPP_COALESCE + ' OR true"\n', ASSESS_ONLY),
    ("opportunity coalesce plain set", ASSESS,
     '_OPS02 = "UPDATE recompute_job SET available_at = :at WHERE id = :pending_id"\n', ASSESS_ONLY),
    ("opportunity coalesce foreign writer", DECISION, '_OPS02 = "' + _OPP_COALESCE + '"\n',
     "The mini-decision store never updates, deletes, truncates, upserts or runs DDL"),
    ("opportunity coalesce unseen", ASSESS,
     ("replace", '"UPDATE recompute_job SET available_at = greatest(available_at, :at) WHERE id = :pending_id "',
      '"SELECT 1 FROM recompute_job WHERE id = :pending_id "'),
     "Rule 8 found no opportunity coalescing UPDATE"),
]
WRITER_CONTROLS += [
    ("controls opportunity coalesce", ASSESS, '_OPS02 = "' + _OPP_COALESCE + '"\n'),
]


def restore(path: str) -> None:
    subprocess.run(["git", "checkout", "--", path], cwd=ROOT, check=True)


def run_guard(seam: bool) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, ASSETOPS_GUARD_PYTHON=sys.executable)
    if seam:
        script = ('$ErrorActionPreference = "Stop"; . (Join-Path $PWD "tools/checks/_common.ps1"); '
                  '. (Join-Path $PWD "tools/checks/configuration-persistence.ps1"); '
                  '$f = @(Invoke-ConfigurationPersistenceCheck); '
                  'if ($f.Count -gt 0) { $f | ForEach-Object { Write-Output "- $_" }; exit 1 }; Write-Output "passed"')
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script]
    else:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "tools/check-architecture.ps1"]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)


def probe(path: str, appended, seam: bool) -> subprocess.CompletedProcess[str]:
    """Append module-level code, or (W2-00) apply `("replace", old, new)` to one exact existing line."""
    file = ROOT / path
    original = file.read_text(encoding="utf-8")
    try:
        if isinstance(appended, tuple):
            _, old, new = appended
            if original.count(old) != 1:
                raise SystemExit(f"replace probe: {old!r} is not exactly once in {path}")
            file.write_text(original.replace(old, new), encoding="utf-8")
        else:
            file.write_text(original.rstrip("\n") + "\n\n\n" + appended, encoding="utf-8")
        return run_guard(seam)
    finally:
        restore(path)


def main(argv: list[str]) -> int:
    seam = "--seam" in argv
    only = [a for a in argv if a != "--seam"]
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "backend"], cwd=ROOT, capture_output=True,
                           text=True).stdout.strip()
    if dirty:
        print(f"refusing to run on a dirty backend tree:\n{dirty}", file=sys.stderr)
        return 2
    failed = 0
    for name, path, appended, expect in NEGATIVE:
        if only and name not in only:
            continue
        out = probe(path, appended, seam)
        text = out.stdout + out.stderr
        ok = out.returncode != 0 and expect in text
        failed += not ok
        print(f"{'CAUGHT' if ok else 'MISSED'}  {name}", flush=True)
        if not ok:
            print("    expected: " + expect + "\n    " + "\n    ".join(text.strip().splitlines()[-6:]), flush=True)
    if not only or "controls" in only:
        out = probe(SCHEDULE, CONTROLS, seam)
        ok = out.returncode == 0
        failed += not ok
        print(f"{'ALLOWED' if ok else 'REFUSED'}  controls", flush=True)
        if not ok:
            print("    " + "\n    ".join((out.stdout + out.stderr).strip().splitlines()[-10:]), flush=True)
    for name, path, appended in WRITER_CONTROLS:
        if only and name not in only and "controls" not in only:
            continue
        out = probe(path, appended, seam)
        ok = out.returncode == 0
        failed += not ok
        print(f"{'ALLOWED' if ok else 'REFUSED'}  {name}", flush=True)
        if not ok:
            print("    " + "\n    ".join((out.stdout + out.stderr).strip().splitlines()[-10:]), flush=True)
    clean = subprocess.run(["git", "status", "--porcelain", "--", "backend", "tools"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    print("tree restored" if not clean else f"tree NOT clean:\n{clean}")
    return 1 if failed or clean else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
