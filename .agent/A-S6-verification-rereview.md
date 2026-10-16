# Re-review - A-S6-verification (amended ruling, D-2026-10-16-s6-verification)

Reviewer: fresh Claude, independent of the Architect and of the first reviewer. Branch `plan/A-S6-verification`, HEAD `46bb39f5`.
Scope: targeted check of M1, M2 and L1-L5 from `.agent/A-S6-verification-review.md` against the amended answers, the decision text and the registry diff `28306474..HEAD`. No code, no test suites.

## Verdict: ACCEPT

No High or Medium findings remain. Two Low carries for the Planner are listed below; neither blocks.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 228 nodes, 11 linked pilot panels".
- Registry diff `28306474..HEAD`: three node edits, no node added or removed. `A-S6-verification` decision text updated. `I-S6-02` resized S -> M, and its acceptance target now names clipped UTC-day segments, per-window provenance, critical-load role/readiness coverage, evaluator-owned resolution events, the CHECK migration and the guardrail/overlap holds. `I-sim-verification-cases` target now names versioned requested/delivered critical-load roles, the continued guardrail hold and the permanent overlap block. No new node, so `queue_baseline_nodes` needs no change (it already lists `A-S6-verification`, `I-sim-verification-cases`, `I-S6-02`).
- Code read against M1: `analytics/assessment_worker.py:62` (`day_windows`), `analytics/dispatch_read.py:67` (`day_window`), `analytics/dispatch_v3.py:383-489` (`_intervals`, `_interval`, `Segment.payload`), `analytics/dispatch.py:32` (`CANDIDATE = "CANDIDATE_AVOIDABLE"`). Code read against M2: `actions/adapters/postgres_action_store.py:203-235` (accept locks and guard).

## M1 - resolved

The target is now the sum of `CANDIDATE_AVOIDABLE` segment seconds intersecting each plan window, clipped to half-open `[start, end)`, read from the latest selected UTC-day `dispatch-3` revision(s) covering the window under existing bracket and continuity selection. No S3 60-minute kind is added. A segment crossing a bound contributes only its overlap. Indeterminate or open-bound time inside the window makes the target INCONCLUSIVE. The baseline day revision IDs are frozen in the plan, the later ones are appended as an immutable selection binding before evaluation, and both are pinned in the outcome. A changed selection gives a new binding and outcome.

This is implementable against the code. Segments carry `start`, `end`, `classification` and seconds (`Segment.payload`, `dispatch_v3.py:124`), so clipping is direct integer arithmetic. Each interval belongs to exactly one day revision, keyed by `first_on` (`dispatch_v3.py:399`), so summing across covering days does not double count. The integer target comparison `4 * later <= 3 * baseline` is exact. The coverage rule (every five-minute generator-state slot) stops "no segments" from reading as zero Candidate time.

## M2 - resolved

A measured reserve or service `GUARDRAIL_FAIL` on INEFFECTIVE closes the trial but keeps `reserve-trial-1` blocked for that Site, battery asset and reserve field. It carries the typed `PRIOR_TRIAL_GUARDRAIL_FAILED` and the Action/outcome link, and lasts until a future rollback/review contract exists. VERIFIED and target-miss-only INEFFECTIVE release the hold. The evaluation job alone appends `RESOLVED` in the same serialized transaction as the outcome and hold change. The guard and the current outcome are checked atomically, not from a UI projection. The sim-cases target now requires proof of the continued hold.

## L1-L5 - resolved or explicitly scoped

- **L1:** S6-02 adds public, time-valid requested and delivered critical-load power roles to the binding/readiness and five-minute Lab publication profiles, with versioned readiness messages for Lab and real-Site onboarding. Missing roles stay INCONCLUSIVE. `I-S6-02` is resized to M, and both registry targets name the roles. It is folded into S6-02 rather than given a separate node. That is acceptable.
- **L2:** provenance is resolved per window, never over their union. The compatible-pair rule requires the same source class, the same registered scenario/profile lineage, distinct run identity digests and intact links. Both resolutions and digests are pinned. MIXED, UNKNOWN or crossing classes give INCONCLUSIVE.
- **L3:** one append path, the evaluation job, on a SYSTEM job channel. The demo command cannot append resolution events. A migration extends the `action_event` kind, triggering-command, command-key and source-channel CHECKs. `lifecycle.reduce` and `service.is_unresolved` must derive state from the latest resolution or withdrawal event under the trial lock.
- **L4:** a detected late-reading overlap permanently blocks acceptance with typed `PRIOR_TRIAL_REASSESSMENT_OVERLAP` until a future reviewer contract exists, and the sim cases must prove it. A different covering FoundationRevision for either window, backdated included, gives REASSESSMENT_PENDING and then INCONCLUSIVE unless a new comparable plan is frozen.
- **L5:** the "absent from this worktree" sentence is removed. The decision now cites `D-2026-10-15-s601-reopen` directly.

## Low carries for the Planner (non-blocking)

### N1 (Low) - the guardrail block is asset-scoped, but the S6-01a accept serialization is Finding-scoped

- The S6-01a accept takes `pg_advisory_xact_lock` on `action-trial:(Site, Finding, asset, field, rule)` (`postgres_action_store.py:217`), and its guard reads only Actions of the same canonical Finding (`:228-231`).
- The ruling scopes `PRIOR_TRIAL_GUARDRAIL_FAILED` to Site, battery asset and reserve field, so a recurrence that is a new Finding on the same battery must also be refused.
- If the Implementer copies the existing Finding-scoped guard query, the M2 bad recommendation comes back through a new Finding.
- **Carry:** the S6-02 packet should require a guard read at (Site, asset, field, rule) scope for the guardrail and overlap blocks. It should also require one lock at that scope, taken by both accept and the evaluator's resolution transaction. Add a test where a different Finding on the same battery is refused.
- The ruling text already states the scope and atomicity, so this is precision for the packet, not a ruling gap.

### N2 (Low) - "open-bound segment time" is interval-level in code

- `OPEN_BOUND` is recorded as an interval limitation when `off_before` or `off_after` is missing (`dispatch_v3.py:452-455`), not as a segment classification.
- **Carry:** the packet should read the rule as "any segment time, of any class, inside the window from an interval with an OPEN_BOUND limitation makes the target INCONCLUSIVE". The day revision covering the window then needs its bracket to see the bounding OFF readings.
- This fails closed either way.

## Residual risk

- The first review's residuals still stand. The later window is classified against the new, lower reserve, which is conservative but needs explaining in the UI. And a `RESOLVED` presentation can be withdrawn, so demo scripts must not present it as permanent.
- When the later window overlaps an interval that started the previous UTC day, the covering set must include that previous day's revision. "Covering under existing bracket selection" implies this. The packet should state it, to avoid silently dropping Candidate seconds from the later window, which would bias the result toward VERIFIED.

No owner acceptance is claimed or inferred by this review.
