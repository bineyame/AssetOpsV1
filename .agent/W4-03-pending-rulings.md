# W4-03 pending rulings

## PR-1 (raised in unit 1; does not block unit 1; needed before unit 4)

S1 asks the OPPORTUNITY stage to carry "counters", but the S4/closure-1 catalog delta for 0030 lists only the
altered stage CHECK and no `schedule_site_head` columns. W4-02 added `mini_processed/mini_deferred/mini_failed`
as new columns in 0029. Unit 1 added no counter columns.

Question: should 0030 add `opportunity_processed/opportunity_deferred/opportunity_failed` (integer NOT NULL
DEFAULT 0) to `schedule_site_head`, with the downgrade dropping them? Or should unit 4 report OPPORTUNITY
counts without persisted columns? If the answer is columns, unit 4 amends 0030 and its catalog test, which is
possible because the branch is not merged.

## PR-2 (raised in unit 2b; blocks unit 2b; amends 0030)

The scenario command carries a required `narrative` (closure 1 Q1-Q3 literal request shapes; original Scenario
domain paragraph: "typed quantities/units, narrative, assumption source"). Neither the original
`mini_scenario_revision` DDL (spec lines 84-101) nor the closure 4 S4 amendment matrix has a column for it, so unit
1's 0030 cannot persist it. Unit 2b stopped before the scenario store/POST rather than hash a field it then drops.

Question: should 0030 add `narrative text NOT NULL` to `mini_scenario_revision` with
`CONSTRAINT mini_scenario_revision_narrative_check CHECK (length(btrim(narrative)) BETWEEN 1 AND 2000)` (closure 1
bound "explanation/narrative/reason 1-2000"), with the catalog test updated? Or is `narrative` hash-only (in the
payload digest, not stored)? Should the scenario row wire then expose `narrative`? (Its closure-1 row shape does not.)

Confirmations requested in the same ruling (unit 2b would otherwise take these readings):
1. A pinned tuple whose `mini_revision_id` is not a W4-02 renewable revision of this tenant/Site is 422
   `DECISION_LINK_SCOPE_INVALID`; a same-Site tuple that is not the selected head at command DB time (seq or revision
   differs) is 409 `DECISION_BASIS_CHANGED`. Pins are 0-5 distinct consecutive Site-local days.
2. Scenario `selected_source_provenance` (S20) is resolved per row for the read gate (MIXED/UNKNOWN withholds the
   calculation); the list envelope's blocks use the union over all eligible rows' pins, not the page. No per-row
   provenance key is added to the closure-1 row shape.
3. `scenario_state` is `HISTORICAL` for an explicit past `known_at`, else `DEFINED`.
