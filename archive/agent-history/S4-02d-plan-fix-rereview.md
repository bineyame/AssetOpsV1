# S4-02d plan fix round 1: fresh re-review

Reviewer: fresh Claude re-reviewer. I did not write the packet, the first review (`.agent/S4-02d-plan-review.md`) or the fix round. Date 2026-10-14.
Worktree `AssetOpsV1-gap-planning`, branch `plan/S4-02c-architect`. I reviewed `fc874e5e` ("S4-02d plan fix round 1") against its parent `141afe09`. It changes the packet, the planner notes, the README row and `next-work-2026-10-14k.json`, and adds the Codex session log. I also read `66c884fd`, the Architect ratification request. I ignored `.agent/architect-S4-02d-answers.md`, which is being written concurrently.
I judged the round against the RETURN review's H1, H2, M1-M5, L1-L4 and its unnamed risks, and against the built code.

## Verdict: RETURN for a one-sentence Planner amendment (N1)

All eleven RETURN findings are resolved, and I checked each resolution against the code (table below). In particular:

- **H1:** per-window currentness never freezes a Site, and the requeue recovery works with the built `enqueue` and `_LIVE_JOBS`.
- **H2:** the tick-only walkthrough can be reached, and its superseded no-op is deterministic.
- **M2:** the definition of an active Site includes KOBO-001.
- **Rule 8:** the amendment is clearly marked as pending Architect ratification, not assumed.

One new defect came in with the H1 fix. Packet :20 says to run S4 match "**every tick**" for every selected Site. However, `PostgresFindingStore.apply` inserts an append-only `finding_match_pass` row on every pass, including zero-write passes. This is not idempotent: the insert has a fresh `uuid4()`, there is no uniqueness constraint, and migration 0009's `ledger_append_only` trigger forbids deleting rows. At the one-minute cadence that is about 1,440 permanent rows per Site per day for a Site where nothing changed.

This contradicts the packet's own rule at :22: "do not add unbounded tick rows by default". The implementer cannot follow both instructions. The fix is one sentence (N1), and it can go into the same commit as the Architect's storage ratification. A targeted check of that sentence is enough; this does not need a full re-review.

## Checks run (by me)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0. Output: "Registry valid: 224 nodes, 11 linked pilot panels".
- `... --verify-report .agent/next-work-2026-10-14k.json`: exit 0. Decision `select` `I-analytic-finding-worker-schedule` 2.198 vs `I-action-store` 2.016, gap 8.28%, tie-break notice. This is unchanged from 14j.
- `tools/check-architecture.ps1`: "Architecture check passed". `tools/check-agent-workflow.ps1`: "Agent workflow check passed".
- `git diff --check 141afe09 fc874e5e`:
  - It fails only on trailing whitespace inside `.agent/planner-S4-02d-fix-log.txt`, which is the raw Codex transcript.
  - Scoped to `tasks/` and the notes, it is clean.
  - Committed transcript logs are established precedent (`planner-S4-02c-fix-log.txt` and others are tracked), so this is not a finding.
- No backend or frontend suites were run. The change is planning-only.

## Per-finding checks

| Finding | Packet location | Result |
|---|---|---|
| H1 Site freeze | :20, :21, :23, phase 1 | **Resolved and buildable.** See "H1 trace". S4 runs after S3 regardless of S3 state, currentness is per window plus its six-hour bracket, and terminal FAILED has a typed alarm and a real requeue. N1 is the side effect. |
| H2 tick-only Leg A | phase 3 | **Resolved and reachable.** See "H2 trace". Step 1 and every later step are tick-driven, the `FINDING_REVISION_SUPERSEDED` no-op is asserted, and the same-revision state is cited from S4-02c rather than required. |
| M1 storage/guard | :22, phase 1, Status line | **Resolved, with ratification correctly pending.** The packet names migration 0013 (next after 0012), four mutable head/cursor/enrolment tables, the sole writer `scheduling/adapters/postgres_schedule_store.py` and the rule 8 amendment. "this guard change is in scope and awaits Architect ratification, not pre-approved" appears at :22, in the Status line, in the notes ("not yet approved") and in the README row. `66c884fd` asks the Architect to ratify, amend or refuse it. Nothing assumes approval. |
| M2 active Site | :20 | **Resolved.** The predicate is an imported Site with evidence or explicit enrolment and lifecycle not `DECOMMISSIONED`/`ARCHIVED`, and `PLANNED` qualifies. KOBO-001 (`PLANNED`, imported, with accepted evidence) is named and included. Outstanding work keeps a Site selected. Excluded Sites with work are reported. "Newly activated" means newly imported or enrolled. `lease_job` becomes Site-filtered inside the assessment writer, and both of its UPDATEs still match `$assessUpdates` `UPDATE recompute_job SET status =`. `reconcile_all()` keeps running and never-assessed Sites are added. Carry N4 covers the wording "registered evidence". |
| M3 timer/ownership | "Per-environment ownership" | **Resolved.** The per-Site consequence timer is retired on install, the CLI is kept for one-off use, and the false-skip reason is stated. The four-row table matches the review: the demo host stays uninstalled until the F1 node lands, and the pilot is gated by `real_pilot_requires`. |
| M4 `NO_WORK_RECORDED` | :22, :23 | **Resolved.** `STALE_NO_WORK` is a distinct backlog category with Finding/revision IDs. It blocks CURRENT and is not backfilled. The code exists: `consequence_read.py:33` `NO_WORK_RECORDED`. |
| M5 F1 assertion | phase 3 | **Resolved.** The phase records `SEQUENCE_ORDER_INVERTED`/`GENERATOR_SERIES_AMBIGUOUS` and asserts only the seam's true upstream state. Money is left to F1, and the source-ordered variant is the positive path. |
| L1 seam authority | :23 | **Resolved.** The Python port takes `(tenant, site, half-open window)` and its outputs are enumerated. The watermark is the selected input basis plus `analytic_run_selection.seq`. Disposition timestamps and the heartbeat are explicitly not a commit-order fence, which matches `.ai/DECISIONS.md` :4049 ("clock-based `knowledge_cutoff` is not a commit-ordered acceptance fence"). Thresholds use `clock_timestamp()`. The S3 status, `match_state`/`finding_match_pass` and `pending_work` derivations are reused rather than rebuilt. |
| L2 timeouts | :21, phase 1 | **Resolved.** Server-side `statement_timeout`/`lock_timeout` plus a killable child process per stage. Both a DB stall and a stage that never returns are injected, and each gives a typed `TIMEOUT` with work left retryable. The S3 stage bound is shorter than the 5-minute lease, and lease expiry after a kill is exposed rather than asserted away. Carry N2 covers how the timeouts reach the existing stores. |
| L3 fence | :21, risks | **Resolved.** The Site claim serialises S3 and S4 across hosts. `FindingFenceMoved` (`postgres_finding_store.py:43`) is reported as typed `FENCE_MOVED`. The unbounded `string_agg` is named as a risk. Carry N3 covers the one case where it is not retryable. |
| L4 sizing | phase table | **Resolved.** Timer installation and the runbook move to phase 2. Phase 1 still carries the migration, the guard amendment and eight proofs, which is heavy but plausible under ~120k. |
| Unnamed risks | risks | **Resolved.** Three risks are now named: the install gate before F1, `reconcile_all()` and `string_agg` cost, and I3/I4 as still open. |

### H1 trace (against the code)

- **No Site freeze.**
  - `match_state` (`postgres_finding_store.py:400-415`) sets `matched` to latest pass `selection_seq >= window max(seq)`. The pass seq is the Site-wide `max(seq)` (`_fence`).
  - A matcher that runs after each S3 stage therefore keeps every window `matched`, whether or not one window has a FAILED job.
  - `finding_episode.py:12-14` leaves only episodes that touch a non-CURRENT window unchanged.
  - The currentness gate ("no intersecting live S3 job" over the window plus its six-hour bracket) blocks only windows that intersect the failed job. Other windows advance, which is what phase 1 now proves.
- **Requeue is real.**
  - `enqueue` (`postgres_assessment_store.py:255-274`) widens only a `PENDING` overlapping job. With only a FAILED job present it INSERTs a new PENDING job, which `$assessInserts` already allows.
  - The worker processes it with `cohort=None`, which gives selection `DEFAULT` (`assessment_worker.py:115`).
  - `_select` always INSERTs a selection with `selected_at = now`, even when an identical run is reused (`:343-353`). That is later than the FAILED job's `available_at` (its failure instant, `:240-242`).
  - So `_LIVE_JOBS` (`:88-91`) stops counting the failure.
  - `assess` (EXPLICIT) would not do this, and the packet says so.
  - Carry N5: the requeue window must overlap the failed job's window.

### H2 trace (against the walkthrough and recompute)

The released late reading is the withheld GOOD mean itself (`s402c_late_power_walkthrough.py:14-21`). Acceptance writes the 0012 `EVIDENCE_ACCEPTED` work and an S3 job. The pre-tick read is then STALE/`TECHNICAL_INPUT_CHANGED` with the work ID.

The first tick runs these stages in a fixed order:

1. S3 assesses the window including the late ID.
2. S4 appends r2, and the 0011 trigger enqueues r2's work.
3. The drain no-ops r1's work as `NO_OP_SUPERSEDED = "FINDING_REVISION_SUPERSEDED"` (`financials/recompute.py:63`) and prices r2.

The order within a tick is fixed, so the result does not depend on the order in which work is drained. "Drive first delivery and all subsequent steps by full schedule ticks" removes the current step-1 and Leg B CLI calls (`:222`, `:292-296`), and a command-log grep records W4. Carry N6 covers the grep's coverage and the bounded-stage edge.

## New finding

### N1 (Medium, acceptance gap: contradictory instruction; RETURN item): "S4 match every tick" appends an unbounded append-only `finding_match_pass` row per Site per minute

- **Where:** packet :20 ("run S3, then S4 match **every tick**, even with due, leased or FAILED S3 work") against :22 ("do not add unbounded tick rows by default").
- **Code:**
  - `postgres_finding_store.py:132-137` INSERTs `finding_match_pass (id = uuid4(), ...)` on every `apply`, including zero-write passes (Q18).
  - Migration 0009 :157-174 has no uniqueness on `(site, selection_seq, matcher_version)`, and its `ledger_append_only` trigger forbids UPDATE or DELETE.
  - At a one-minute tick, an unchanged Site therefore gains about 1,440 permanent rows per day. Every pass also replans the whole Site, the matcher scan named in the risks.
  - Nothing in the packet bounds this, and the Finding writer is INSERT-only under rule 8, so the rows can never be pruned.
- **Why it matters:** an implementer who follows :20 literally builds permanent, unbounded growth in an evidence-lineage table that `match_state` and the S5 seam read. An implementer who follows :22 instead has to invent a skip rule under pressure, and a naive skip ("skip when `matched`") could miss a status-only change that the matcher must observe.
- **Fix (Planner, one sentence at :20):** run S4 for a selected Site when there is no pass for the current `MATCHER_VERSION`, or when the Site's matcher fence (`_fence`: selection seq, job count/marker, revision count) differs from the fence recorded in `schedule_site_head` at its last completed pass.
  - Otherwise record "S4 skipped: unchanged fence" in the mutable head, and append no `finding_match_pass` row.
  - This keeps the H1 property: a FAILED window never blocks matching when other windows get new selections, because any new selection moves the fence.
  - Add a phase-1 proof: N idle ticks append zero `finding_match_pass` rows, and a new selection triggers exactly one pass.
  - Because it touches `schedule_site_head` content, the Architect's storage ratification can carry it.

## Implementer carries (assuming N1 is applied; no further Planner round)

- **N2 (Low): how the timeouts reach the existing stores.** The S3, Finding and consequence adapters each build their own engine. Apply `statement_timeout`/`lock_timeout` per stage child, for example through libpq `options=-c statement_timeout=...` on the child's `DATABASE_URL`, `PGOPTIONS`, or role-level settings on the schedule credential. Do not edit the other writers' engine construction. `SET` is not matched by rule 8's `$sqlWrite`, but any new SQL or driver import outside the eight writers still fails the guard. The orchestrator and the S5 seam must reach the database only through writer or store modules.
- **N3 (Low): not every `FindingFenceMoved` is retryable.** `_insert_revision` also raises `FindingFenceMoved("a cited evidence ID is not accepted in this Site")` (`postgres_finding_store.py:173`), which is deterministic. Report it separately, by message or as a distinct type in the writer, or alarm on repeated `FENCE_MOVED` for one Site. Otherwise a permanent matcher defect retries forever and looks transient.
- **N4 (Low): define "registered evidence" in the active-Site predicate.** It should mean at least one `accepted_evidence` row, or explicitly also a registered gateway/source. Test a newly imported Site with neither, which must not be selected unless enrolled, and one with a gateway but no evidence.
- **N5 (Low): `assess_dispatch requeue` must overlap the failed job's window.** Superseding a failure is overlap-based in `_LIVE_JOBS`. Prefer `--job-id`, or validate that `--start/--end` covers the FAILED job's window. A requeue elsewhere would leave the failure live and be easy to misread as recovered. Keep the CLI's tenant handling by UUID. It must not inherit the consequence CLI's `demo`-only refusal, and nor may the stage children: the consequence stage calls the worker by IDs, never `recompute_consequences run`.
- **N6 (Low): walkthrough grep and the bounded-stage edge.**
  - Extend the W4 grep to `recompute_consequences run` as well as `process-jobs`/`match-findings`.
  - Configure per-tick limits so the first post-release tick completes S3 and S4 for KOBO-001.
  - If the S3 stage times out in that tick, the drain would instead produce the S4-02c same-revision state. The tool must then report the actual outcome, not assert either.
- **N7 (Info):** carries 1-4 of the RETURN review still apply: real IDs only, skipped distinguished from zero-work, the CLI kept, and the new rule 8 guard comment quoted in the implementation packet.

## Residual risk not already named

- `lease_job`'s expire-to-FAILED UPDATE becomes Site-scoped together with leasing. A Site that drops out of the predicate, with no live work, keeps an expired last-attempt LEASED job LEASED until it is selected again. The "remains selected while live S3 work exists" rule covers this only if LEASED counts as live work in the predicate, which it does under `_LIVE_JOBS`. The implementer should test it.
- Ratification is pending. If the Architect refuses or narrows the eighth writer, the packet's phase 1 storage text needs a matching edit before implementation. The Status line already says so.

## USER_REVIEW_REQUIRED

False still holds: operator CLI and report, backend read seam and runbook only. S5-01 keeps the owner checkpoint.
