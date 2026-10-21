# W4-03 pending rulings

## PR-1 (raised in unit 1; does not block unit 1; needed before unit 4)

S1 asks the OPPORTUNITY stage to carry "counters", but the S4/closure-1 catalog delta for 0030 lists only the
altered stage CHECK and no `schedule_site_head` columns. W4-02 added `mini_processed/mini_deferred/mini_failed`
as new columns in 0029. Unit 1 added no counter columns.

Question: should 0030 add `opportunity_processed/opportunity_deferred/opportunity_failed` (integer NOT NULL
DEFAULT 0) to `schedule_site_head`, with the downgrade dropping them? Or should unit 4 report OPPORTUNITY
counts without persisted columns? If the answer is columns, unit 4 amends 0030 and its catalog test, which is
possible because the branch is not merged.

## PR-2 (RESOLVED by u2: narrative column landed in c351eed1; readings 1-3 confirmed)

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

## PR-3 (RESOLVED by u2b: count is 45, the 48 was an arithmetic error; no DDL change)

u1/u2 DDL is applied exactly as ruled (three `schedule_site_head` counters, `narrative` column and
`mini_scenario_revision_narrative_check`, downgrade column drop). `pg_catalog` then reports **45** named CHECKs on the
ten new tables (44 at `c3713564` plus the narrative CHECK), and the exact CHECK-name array in
`test_w403_migration_postgres.py` matches that catalog name-for-name. The u2 ruling says **48** (47 before the
narrative CHECK). Per table at head: `mini_scenario` 3 (create_key, create_payload_sha256, create_actor_id);
`mini_scenario_revision` 6 + 6 authored (revision_no, name, kind, narrative, correction_reason, chain);
`mini_alternative_revision` 8 + 6 authored; `mini_opportunity` 1 (window); `mini_opportunity_revision` 2
(revision_no, input_sha256); `mini_decision_work_link` 1 (target) + 6 authored; `mini_opportunity_scenario_link` 6
authored; the other three tables 0. `schedule_site_head` keeps 2 CHECKs at 0029 and at head (net zero, as ruled).

Question: is the count 45 (u2's 47/48 miscounted), or are three named CHECKs missing from 0030 (if so, which tables,
columns and exact names)? Everything else in commit 1 passes: 11 collected, 10 passed, the only failure is
`len(CHECKS) == 48` (actual 45). Commit 1 is on the branch with the ruled 48; unit 2b not started.

## PR-4 (raised in unit 2b; does not block; provisional behaviour implemented)

The spec rules the non-MINIGRID refusal only for physical reads (closure 4 S10: 200 UNKNOWN `SITE_ROLE_UNSUPPORTED`
envelope). Unit 2b took these provisional readings for scenarios (`mini_decisions_api.py`); confirm or replace:
1. `GET .../financials/scenarios` on a non-MINIGRID Site returns 200 with the `mini-scenarios-1` keys, `status`
   UNKNOWN, zero rows, the empty UNKNOWN provenance alias, `selection_token: null`, plus a `limitations` key
   `[{"code":"SITE_ROLE_UNSUPPORTED","evidence_ids":[]}]` (no store consulted).
2. A scenario POST on a non-MINIGRID Site is 422 `DECISION_LINK_SCOPE_INVALID` after the write grant and store
   check, before the principal and body.
3. Read-gate limitation codes on a scenario row: the stored calculation `reason`, then `SELECTION_CHANGED` (pinned
   revision is no longer the day's head), `RECOMPUTE_PENDING`, `SOURCE_STALE`, `SOURCE_CLASS_UNKNOWN|MIXED`
   (W4-02 codes reused), as `{code, evidence_ids: []}`.
4. `gross_sales.amount` is a JSON number on the read wire, like `energy_kwh` (stored as a decimal string).
5. Scenario list `currentness` is the W4-02 aggregate over the union of pinned days; with no pinned day it is
   `CURRENT` (or `HISTORICAL` for an explicit past cutoff) with `job_state: NONE`.
