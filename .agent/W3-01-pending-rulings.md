# W3-01 pending rulings (q2, Lane B run 2, 2026-10-20)

q1 items 1-7 are answered by "Run 1 rulings (q1)" in `.agent/W3-01-build-spec.md`. Lane B's part of commit 1 is
complete at `2951b66c`; nothing below was built on an assumed answer. Both items affect Lane A's envelope work.

1. **No selected row and no pending set (ruling 5 gap).** A cold/EV read with no selected revision and no newer
   accepted set (e.g. an empty window) has `selected_source_provenance:null` and `pending_source_provenance:null`,
   but ruling 5 says `source_provenance` equals one of them, and the six public keys are required. Is
   `source_provenance` then (a) `cited_set(t, s, [], [])` = UNKNOWN/`EMPTY_CITATION_SET`/`basis_sha256:null`, (b)
   `null`, or (c) today's shape (`classification:null`, empty lists)? `dual_blocks(None, None)` currently raises.
2. **Cold "full newer accepted set" (ruling 5).** EV has `_ev_rows(c, ...)` for the window's accepted set at the
   cutoff. Which exact query defines the cold pending set (the window's accepted probe rows at `known_at` for the
   requested analytics, or the rows after `pending_since`)? Also confirm EV computes the pending DTO on every
   pending read, not only when `_unassessable` finds a non-positive class as today.

## Readings made this run (for confirmation)
1. Ruling 2's W1 sets are derived inside `finding_revision`/`consequence_revision` by default; callers with a
   cold/EV/estate row pass their own ruling-2 set explicitly.
2. `ev_selected` lowercases and dedupes the cited set before resolving; the mismatch reason carries that set.
3. "No selected row" in ruling 4 is expressed as empty `selected_revision_ids` (no comparison, null digest).
4. `LinkRowsReads` (set-only reads on a caller connection) is a Lane B convenience so Lane A can stay inside its
   snapshot transaction without the private `_run` override; it adds no semantics.
5. The pure `dual_blocks` test is named `test_pending_dual_blocks`; the named envelope test
   `test_pending_envelope_does_not_relabel_selected_row` is left to Lane A's integration commit.
