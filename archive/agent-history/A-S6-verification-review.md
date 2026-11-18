# Review - A-S6-verification (D-2026-10-16-s6-verification)

Reviewer: fresh Claude, independent of the Architect. Branch `plan/A-S6-verification`, HEAD `28306474`.
Scope: architecture ruling only. No code. No test suites were run.

## Verdict: RETURN

There are two Medium findings. Each needs a short amendment to the ruling, not a redesign. Everything else holds:

- outcome vocabulary
- fail-closed rules
- append-only history and authority
- the no-savings stance
- demo labelling
- the non-UI-first split
- the registry edit

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 228 nodes, 11 linked pilot panels".
- `--next-work --json`: exit 0, `status: "ranked"`, no global stops, so no refusal. The decision is `stop_owner` for an S6-01b contest at a 0% gap, between `I-action-execution-ui` and `I-action-history-ui`. That contest is unrelated to this change.
- Code read against the ruling:
  - `actions/lifecycle.py`
  - `actions/service.py`
  - `actions/adapters/postgres_action_store.py`
  - migration `0016_action_store.py`
  - `analytics/assessment_worker.py`
  - `analytics/dispatch_v3.py`
  - `sites/binding_roles.py`
  - `evidence/source_provenance.py` (main)
- Decisions read: `D-2026-10-15-s601-reopen` and its answers (via `git show main:` and `plan/S6-01-reopen:`), and the lifecycle decision's S6-02 paragraph.

## What holds

- **Outcomes, consistent with lifecycle L2.** The ruling cites the lifecycle decision and gives the full vocabulary:
  - outcome values `VERIFIED`, `INEFFECTIVE`, `INCONCLUSIVE`
  - read states `PENDING` and `REASSESSMENT_PENDING`
  - reason `GUARDRAIL_FAIL`
  - events `RESOLVED` and `RESOLUTION_WITHDRAWN`

  It also restores the `Ineffective` outcome that L2 flagged as missing. It matches the lifecycle paragraph: missing or conflicting evidence gives INCONCLUSIVE, and a failed guardrail blocks VERIFIED.
- **Fail-closed.** Each of these yields INCONCLUSIVE or a pending read state, never a verdict:
  - unknown, MIXED or crossed source
  - a missing slot or required role
  - an unmeasurable guardrail
  - non-comparability
  - pending S3/S4 work
  - late readings or changed attestation

  A known failure stays visible inside INCONCLUSIVE and does not promote a verdict. No real-source positive verdict is possible before real attestation exists.
- **Append-only history.** Outcomes supersede by link and are never updated. Identical retries return the same outcome. Old outcomes stay addressable.
- **Authority.** The system computes metrics and the verdict. The SYSTEM demonstration command can freeze a plan or request evaluation, but cannot supply a verdict or a metric. It carries a label, and no human author is inferred.
- **No causal or savings claim.** The ruling says "observed policy-trial comparison, not a causal saving". The target is Candidate minutes, never money. Simulated and authored results carry labels.
- **Delivery split.** Non-UI work comes first (store, evaluator, reads, fixtures, race tests). UI follows at desktop and 390 px. The owner walkthrough stays required, and nothing claims owner acceptance.
- **Registry.** The node is resolved with evidence. Follow-on acceptance targets are tightened consistently. The checker passes.

## Findings

### M1 (Medium) - the target metric names an S3 artifact that does not exist

- **Where:** answers, "Window and frozen plan": "the S3 `CANDIDATE_AVOIDABLE` duration in minutes from the selected 60-minute dispatch assessment". The decision text says the same.
- **What is wrong:** S3 has no selected 60-minute assessment.
  - The worker and the DEFAULT selection key on UTC-day windows: `analytics/assessment_worker.py:62` `day_windows`, and `analytics/dispatch_read.py:67` `day_window`.
  - `assess_explicit` exists only as a cohort-override path.
  - Candidate time sits inside the day assessment as time-located segments, under interval `segments` / `portions_minutes` (`analytics/dispatch_v3.py:436-489`).
  - Intervals routinely cross any 60-minute boundary.
- **Why it matters:** the target metric is the core of the verdict. As written, the Planner or Implementer has two options, and both are bad:
  - Add a new 60-minute S3 selection kind. That changes the S3 selection contract and the S4 episode inputs, which is horizontal scope with no ruling behind it.
  - Clip segments, but under an ad hoc boundary rule that can differ between the baseline and the later window. That makes the comparison quietly inconsistent.
- **Fix:** add one paragraph defining the metric as follows:
  - It is the sum of `CANDIDATE_AVOIDABLE` segment seconds, clipped to the plan's half-open window.
  - It is read from the latest selected UTC-day `dispatch-3` revision(s) that cover the window, under S3's existing bracket and continuity selection.
  - No new S3 window kind is added.
  - Say how INDETERMINATE or open-bound segment time inside the window is treated. Suggested: any such time makes the result INCONCLUSIVE.
  - Pin the exact day revision IDs in the plan and in the outcome.

### M2 (Medium) - an INEFFECTIVE guardrail failure releases the hold for a further cut in the same direction

- **Where:** answers, "Verdict, history and hold": "A final current VERIFIED or INEFFECTIVE outcome appends a `RESOLVED` ActionEvent ... closes that trial for the prior-Action acceptance guard". The only other gate is "fresh current supported FindingRevision and current Foundation basis".
- **What is wrong:**
  - `D-2026-10-15-s601-reopen` asked S6-02 for an explicit closed transition "and its eligibility rule".
  - Under this ruling, a trial that is INEFFECTIVE because of a *measured reserve or service guardrail failure* releases the hold.
  - `reserve-trial-1` always proposes `old_value - 5` from the current Foundation (`0016_action_store.py:72`).
  - There is no rollback contract.
  - So the next fresh supported revision would show an enabled Accept to cut the reserve by another 5 points, on top of a change that has just been recorded as breaching reserve or service.
- **Why it matters:** this is a visible bad recommendation in the demo's Recommendation panel. It is also the eligibility rule the reopen ruling deferred to S6-02.
- **Fix:** amend the eligibility rule in one of two ways:
  - Preferred: a `RESOLVED` event whose outcome is INEFFECTIVE with `GUARDRAIL_FAIL` keeps `reserve-trial-1` blocked for that Site, asset and field. It carries a typed reason distinct from `PRIOR_ACTION_UNRESOLVED`, and the block lasts until a future rollback or review contract exists. VERIFIED, and a target-miss-only INEFFECTIVE, release the hold as ruled.
  - Alternative: state the risk explicitly and accept it, with a rationale.

### L1 (Low) - the service guardrail needs public roles that do not exist yet

- `MINIGRID_ROLES` and `MINIGRID_ROLES_2` (`sites/binding_roles.py:49-71`) have no role for requested or delivered critical-load power, and no equivalent service signal.
- The ruling does tell the Planner to version the publication profile. But no registry node or dependency carries the new role set, the binding, the readiness messages or the Lab channels.
- `I-S6-02` stays at effort S, and the `I-sim-verification-cases` target does not mention the new roles.
- Without the new roles, every case fails closed to INCONCLUSIVE, so the "complete pass" demo case cannot exist.
- **Carry for the Planner:** name the role set or the reviewed equivalent in the S6-02 packet, add it to the sim-cases acceptance target, and resize the task.

### L2 (Low) - "compatible pair" is the record S4-05 says does not exist

- On main, `evidence/source_provenance.py:20-23` returns `MIXED` for several run IDs, because "no compatible-run-basis record exists".
- Resolution therefore has to run per window. Resolving the union of both windows would make every case MIXED, and so INCONCLUSIVE.
- The plan's "compatible pair" declaration is that missing record, but the ruling gives no criteria for it. Candidate criteria:
  - the same source class
  - the same registered scenario and profile lineage
  - distinct run identity digests
- **Carry for the Planner.**

### L3 (Low) - the resolution events need a schema change and one actor path

- `RESOLVED` and `RESOLUTION_WITHDRAWN` break the current `action_event` CHECKs (`0016_action_store.py:128-162`):
  - `kind`
  - `triggering_command`
  - `action_event_command`
  - `source_channel = 'SYSTEM_DEMONSTRATION_API'`
- The ruling says both that an outcome "appends" `RESOLVED` and that a SYSTEM command "may ... append the resolution event". Pick one actor path, worker or command, with its channel.
- Two pieces of current code also have to change:
  - `lifecycle.reduce` hard-codes outcome `PENDING`.
  - `service.is_unresolved` treats `APPLIED` as unresolved.

  Both must derive the state from the latest `RESOLVED` / `RESOLUTION_WITHDRAWN` events, read under the trial lock.
- **Carry for the Planner.**

### L4 (Low) - two race and scope residuals the ruling should make explicit

- **Late reading before withdrawal.** Late-reading ingestion does not take the trial advisory lock (`postgres_action_store.py:217`). So an accept can pass between a late acceptance and the asynchronous `RESOLUTION_WITHDRAWN`.
  - The ruling's overlap rule covers this: "flag the overlap and prevent another acceptance until reviewed".
  - But S6-02 has no reviewer authority, since it is SYSTEM-only with no human principal.
  - State that the block is a permanent typed block until a future contract exists, and test it.
- **The hold is Finding-scoped.** In code the hold keys on the canonical Finding, so a recurrence that is a new Finding on the same battery is not held.
  - Verdict validity then rests on the plan's pinned covering Foundation revision.
  - Say explicitly that a different covering FoundationRevision for either window (an intervening or backdated publication) makes the result `REASSESSMENT_PENDING` or `INCONCLUSIVE`.

### L5 (Low) - the citation note will read stale on main

- The decision text says the `D-2026-10-15-s601-reopen` text "is absent from this worktree's decision log".
- On main both decisions are present: reopen at line 4152, this decision at line 4155. The sentence will mislead readers on main.
- Fix: cite the reopen decision directly and drop the sentence.

## Residual risk not named in the ruling

- Candidate classification depends on the reserve control, so the later window is classified against the *new*, lower reserve. That direction is conservative, because it makes the target harder to meet, not easier. The UI should still explain why the two windows are measured against different reserves.
- "Final current" can always be reopened by later evidence. Demo scripts must not present `RESOLVED` as permanent.

No owner acceptance is claimed or inferred by this review.
