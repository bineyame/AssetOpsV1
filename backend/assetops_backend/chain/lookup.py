"""CH-2: the thread lookup shared by the read adapters (estate snapshot, board thread port): one statement giving
each listed Finding's thread (id, occurrence number, occurrence count) and each listed Action's thread. No cutoff:
a thread's occurrences are read as stored now (packet residual risk R-2). Pure: no database driver here."""

from __future__ import annotations

from typing import Any, Sequence

#: One statement: the Finding rows (occurrence number and count) and the Action rows (thread only).
LOOKUP = (
    "SELECT 'F' AS kind, CAST(o.finding_id AS text) AS ref, CAST(o.thread_id AS text) AS thread_id, "
    "o.occurrence_no, (SELECT count(*) FROM finding_thread_occurrence x WHERE x.thread_id = o.thread_id) "
    "AS occurrences FROM finding_thread_occurrence o WHERE o.tenant_id = :t "
    "AND CAST(o.finding_id AS text) = ANY(CAST(:f AS text[])) "
    "UNION ALL SELECT 'A', CAST(l.action_id AS text), CAST(l.thread_id AS text), NULL, NULL "
    "FROM chain_action_thread l WHERE l.tenant_id = :t AND CAST(l.action_id AS text) = ANY(CAST(:a AS text[]))")


def thread_lookup(rows: Sequence[Any]) -> dict[str, dict[str, Any]]:
    """`LOOKUP` rows -> `{"findings": {finding_id: {id, occurrence_no, occurrences}}, "actions": {action_id: id}}`."""
    findings: dict[str, Any] = {}
    actions: dict[str, Any] = {}
    for kind, ref, thread_id, no, count in rows:
        if kind == "F":
            findings[ref.lower()] = {"id": thread_id, "occurrence_no": int(no), "occurrences": int(count)}
        else:
            actions[ref.lower()] = thread_id
    return {"findings": findings, "actions": actions}
