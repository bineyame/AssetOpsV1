# S4-02c plan fix round 1: fresh re-review

Reviewer: a fresh Claude re-reviewer. I did not write the packet, the first review (`.agent/S4-02c-plan-review.md`) or the fix round. Date 2026-10-14.
Branch `plan/A-S5-overview`, worktree `AssetOpsV1-gap-planning`, diff `3838a506..0b49c5bf`. I reviewed `0b49c5bf`, which changes the packet, notes, README row and `next-work-2026-10-14g.json`. I ignored the owner-autonomy and brief commits as instructed.
The judgment is against the RETURN review's H1-H3, M1-M5, L1-L5, I1, C1-C5 and R1-R2, and against the built code named in the packet.

## Verdict: ACCEPT

Every RETURN finding is resolved in the packet text. I checked each resolution against the actual code, and each is buildable. The two-leg walkthrough can be reached under the reviewed `fuel-cost-1` contract. The migration SQL shape is valid PostgreSQL and keeps 0011 FindingRevision enqueue working. Placing the trigger in a migration passes guard rule 8 without amending it. The Site enqueue lock closes the M4 lost-work race, and it adds no deadlock cycle with the existing locks.

The residuals below are Low or Info implementer carries. None needs a Planner round, an Architect ruling or the owner. `USER_REVIEW_REQUIRED: false` holds under the packet's two stated conditions.

## Checks run (by me)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0. Output: "Registry valid: 222 nodes, 11 linked pilot panels".
- `... --verify-report .agent/next-work-2026-10-14g.json`: exit 0. The decision is `stop_owner`, with `I-evidence-acceptance-consequence-work` at 2.02 against `I-action-store` at 2.016, a gap of 0.20%. The tie-break recommends the same node. This is the near-tie the Architect already settled under delegation (`architect-contest-2026-10-14d-answers.md`).
- `tools/check-architecture.ps1`: "Architecture check passed". `tools/check-agent-workflow.ps1`: "Agent workflow check passed".
- I did not run the backend or frontend suites, because the change is planning-only and touches no product code.

## Per-finding checks

| Finding | Packet location | Result |
|---|---|---|
| H1 two legs | :12, :34, README row | **Resolved and reachable.** See "H1 trace" below. The README row now says "after the Finding is re-evaluated". |
| H2 constraints | :20 | **Resolved; the SQL shape is valid.** See "H2 shape" below. |
| H3 placement | :21 | **Resolved; rule 8 passes unchanged.** See "H3 and rule 8" below. |
| M1 claim and retry | :23 | **Resolved.** Claims use a session `pg_try_advisory_lock('financial_consequence_runner:'+site)`. No mutable lease or due column is added. Retry is derived from the last FAILED attempt's `finished_at` and `attempt_no`, on a 1/2/4/8/16-minute schedule with no terminal cap. The clock is injectable. The index on attempts `(work_id, attempt_no DESC)` is named, and the "due time" index wording is gone. Carries N3 and N4 below. |
| M2 read change | :24, phase 1 :32 | **Resolved.** `chain()` matches unsucceeded `EVIDENCE_ACCEPTED` rows by `finding_id`, the typed reason code is `NO_WORK_RECORDED`, and no new `REASONS` sentence is added. Phase 1 owns the change. |
| M3 definition | :21 | **Resolved.** The definition is the highest `revision_no` in the same tenant/Site, and enqueue and worker share it. It matches `latest_revisions_overlapping` and the `episodes()` selector in `postgres_finding_store.py`. |
| M4 race | :21 | **Resolved.** See "M4 lock" below. |
| M5 downgrade | :20 | **Resolved.** Downgrade refuses when any `EVIDENCE_ACCEPTED` row exists, and otherwise restores the 0011 function body, the two-arm CHECK and `UNIQUE (finding_revision_id)`. Both paths are proved, and nothing is deleted. The restore is sound: with no evidence rows, only `FINDING_REVISION_APPENDED` rows carry a `finding_revision_id`, so the restored UNIQUE holds. |
| L1 anchor | :16 | **Resolved.** The anchor is now `decide_chunk`/`_persist` (`postgres_evidence_ledger.py:242`, `:309`). |
| L2 no-op storage | :20, :22 | **Resolved.** The no-op is a `SUCCEEDED` attempt with empty IDs and a nullable typed `no_op_reason`, under a CHECK. The one-success index is kept. |
| L3 fallthrough | :22, :32 | **Resolved.** All three causes are dispatched explicitly, and phase 1 guards against an unknown cause before phase 2. This closes the `recompute.py:96-100` `else` fallthrough. |
| L4 backfill | :47 | **Resolved.** The packet decides on no speculative backfill: pre-0012 stale heads report `NO_WORK_RECORDED`, and repair waits for a separate review. |
| L5 runner shape | :23 | **Resolved.** The runner is a one-shot `run --tenant --site --limit N` under an external one-minute timer. It does not claim an all-Site iterator, and the development-tenant restriction is stated. |
| I1 Depends | :6, README | **Resolved.** The Depends line now separates the registry `requires` from built context. |
| C1-C5 | :40-44 | Carried verbatim in substance. |
| R1, R2 | :45-46, notes "For the Architect batch" | R1 is named as an Architect-batch question and does not block this packet. R2 has a required bounded-batch test. |

### H1 trace (Leg A and Leg B against the code)

- **The pre-late state of the variant.** P01-power has no generator status context (`"only": ["load","pv","dis","soc"]`), so the generator state comes from power alone (`dispatch_v3._state`). Withholding the mean that ends at 07:05 removes one state point and leaves a 07:00 to 07:10 gap. That gap is shorter than `CONTINUITY_TOLERANCE = 20 min` (`dispatch_v3.py:41`), so the gap branch at `:411` should keep the segment observed. `limited()` concerns cohort ambiguity, not missing readings. The Candidate time should therefore still cover 07:00-07:05, and `quantify` should end in `POWER_COVERAGE_GAP` (`fuel_cost.py`, the union check). The packet correctly makes this a recorded result rather than an assumption; see N5.
- **Leg A, before drain.** `load_input` loads every accepted generator-power reading of the generator that overlaps the episode live, not only the run inputs. The late mean therefore enters `examined_evidence_ids`, and `quantify` returns `POWER_NOT_IN_ASSESSMENT_INPUTS`, because the late ID is not in `run_inputs` and that check runs before the coverage check. The technical digest changes, so `consequence_read` returns `STALE/TECHNICAL_INPUT_CHANGED`. Once M2's `chain()` match exists, `pending_work` is non-empty and the bridge picks `STALE_QUEUED` (`finding_api.py`).
- **Leg A, after drain.** The drain appends revision n+1 on the same FindingRevision with `QUANTITY_UNAVAILABLE/POWER_NOT_IN_ASSESSMENT_INPUTS`, and the re-read derives the same basis, so the state is `CURRENT`. The owner sees the existing reviewed copy: `REASONS["QUANTITY_UNAVAILABLE"]` plus `FindingConsequence.tsx:48`.
- **Leg B.** The same acceptance already called `_coalesce_job`, so `process-jobs` builds a run whose inputs include the late ID. The new assessment changes the FindingRevision basis, and `finding_episode.py` appends a new revision on a basis change (`SUPPORT_CHANGED`/`BASIS_REFRESHED`, `:689-696`). Its 0011 insert work then drains with 24 contiguous in-run means, full coverage and no overlap, which gives `AVAILABLE`. It is `PRICED` once a window price exists; see N2.

### H2 shape

- `ON CONFLICT (finding_revision_id) WHERE cause = 'FINDING_REVISION_APPENDED' DO NOTHING` is valid PostgreSQL index-inference syntax for a partial unique index with an identical predicate. The function is resolved at execution time, so the index must exist before the next FindingRevision insert, and any migration order within 0012 satisfies that.
- The scoped FK target exists as `accepted_evidence_scope_unique (tenant_id, site_id, id)` (0005).
- The three-arm CHECK requires the other causes' locators to be null, which keeps the assumption and Finding arms free of an `accepted_evidence_id`. `UNIQUE (assumption_revision_id)` is unaffected, because NULLs are distinct.
- `affected_from` is NOT NULL. Readings with a null `interval_start` cannot satisfy strict overlap, so they select nothing and cannot violate it.

### H3 and rule 8

- Rule 8 scans only `$backendRoot = "backend/assetops_backend"` (`configuration-persistence.ps1:43`), and migrations live outside the package (`:585`). A 0012 trigger that inserts `financial_consequence_work` adds no Python writer, so the guard passes as written.
- In `decide_chunk`, `_persist` inserts `accepted_evidence` before the `ingestion_disposition` insert, in the same transaction. An `AFTER INSERT` trigger on the disposition with `WHEN (NEW.decision = 'ACCEPTED')` can therefore join its stored `accepted_evidence_id`. DUPLICATE dispositions carry an evidence ID but fail the `WHEN` (0005 `:264`), so they never enqueue.
- `load_input` itself filters on `d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id`, so the trigger and the worker agree on what "accepted" means.

### M4 lock

- **Isolation.** Both writers run at READ COMMITTED: the ledger uses `engine.begin()` and the Finding `apply` uses `self._connect().begin()`, neither with an isolation override. A plpgsql `SELECT` after `pg_advisory_xact_lock` takes a fresh snapshot, so acceptance sees a FindingRevision committed by the holder it waited on.
- **The reverse order.** Acceptance takes the lock first, and the FindingRevision trigger waits. The new revision then commits after the reading, so its own drain sees the reading. The new revision's consequence is honest: `POWER_NOT_IN_ASSESSMENT_INPUTS` until S3 re-runs.
- **Deadlock.** The ledger order is batch row lock, then enqueue lock, then the recompute `_coalesce_job` lock. Matching takes `'finding:'||site`, then the enqueue lock. Neither path takes the other's earlier lock, so there is no cycle.

## USER_REVIEW_REQUIRED: false

The flag holds. `currentness_reasons` reaches the client type (`financialsClient.ts:103`), but no component renders it (grep of `frontend/src`). `NO_WORK_RECORDED` is therefore a typed code with no owner-facing text. Leg A's end state uses the existing reviewed `QUANTITY_UNAVAILABLE` text and the `POWER_NOT_IN_ASSESSMENT_INPUTS` sentence. Both conditions are written into the packet at :4.

## Residual implementer carries (no Planner round needed)

- **N1 (Low): the no-op predicate must not be broader than `quantify`'s examined filter.** If the drain no-ops a reading that `quantify` would examine, the head goes `STALE` with its only work already SUCCEEDED, and it is then reported as `NO_WORK_RECORDED` indefinitely. That filter is `asset_id == generator_asset_id`, a non-null interval, and overlap with the merged Candidate components. A no-op is safe only for the wrong Site, role or asset, no overlap with the episode, or a superseded revision. Never no-op on quality: a non-GOOD same-asset mean in Candidate time changes `examined_evidence_ids`. Test: a non-GOOD same-asset mean inside Candidate time yields revision n+1, not a no-op. The simplest safe form is to always derive for the latest revision and let basis replay be the "unchanged" outcome, keeping `no_op_reason` for the superseded and out-of-scope cases.
- **N2 (Low): Leg B `PRICED` needs a price.** Publish the SYSTEM price fixture (`publish_assumption fixture ... --step v1`, the same producer S4-02b used) in the variant database before the Leg B drain, and record its revision ID. Otherwise the honest result is `UNPRICED/NO_PRICE`.
- **N3 (Low): the runner claim is a session-level lock on a pooled engine.** The current stores open a new pooled connection per operation (`_run`). Hold one dedicated connection for `pg_try_advisory_lock` for the whole run, and `pg_advisory_unlock` in `finally`, so a lock never returns to the pool still held. Test that a killed runner's lock is released when its connection closes, and that a second runner reports the Site as skipped.
- **N4 (Low): one clock for retry eligibility.** `finished_at` is the database's `clock_timestamp()`. Compare it with a `now` passed in from the injected clock, not with the database's `now()`, or the "no sleep" tests cannot control it. Apply the same `now` to the deferred and backlog counts.
- **N5 (Low): Leg A precondition.** Assert, not merely record, that before the late mean arrives the withheld `[07:00, 07:05)` lies inside an observed CANDIDATE span of the initial FindingRevision. If S3 leaves the gap unobserved, the late mean is not examined and Leg A cannot show `TECHNICAL_INPUT_CHANGED`. In that case stop and report; do not change the fixture to force the result.
- **N6 (Low): one lock key.** Both trigger functions must use the identical expression, for example `pg_advisory_xact_lock(hashtextextended('financial_consequence_enqueue:' || site_id::text, 0))`. A unit test should assert that the key text matches. Optionally, take the lock in the disposition trigger only after the cheap `role = 'generator_power'` check, so non-power ingestion does not serialize with matching.
- **N7 (Low): the Leg B "unrelated accepted input as typed no-op".** P01's episode equals its Candidate range, so the only enqueued-but-irrelevant reading is a generator-power mean of another asset. If the variant Site binds no second generator, prove this case in the phase 2 Postgres tests and say so in the walkthrough artifact rather than inventing a binding.
- **N8 (Info): a stale guard comment.** The rule 8 comment (`configuration-persistence.ps1`, "inserted only by migration 0011 triggers") will be stale once 0012 exists. The guard logic needs no change. A comment-only edit is optional, and if it is made, the implementation packet should state it rather than present it as a rule amendment.

## Residual risk not already named

- The extra Site-wide enqueue lock serializes ingestion chunks that carry accepted dispositions with `match-findings` for the same Site, for the length of a chunk. This is acceptable at the current scale, and R2's bounded-batch test should log chunk latency under a backfill.
