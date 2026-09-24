# T034 - Policy action followed by evidence-based verification

Status: planned
USER_REVIEW_REQUIRED: true

Map: H; the strong product demo point - Finding -> action -> verification.
Depends on: T028-T029 and T029A immutable interventions.
Delivery order: after T029A; next T030. Moved ahead of T030-T033 by
`Docs/queue-review-feedback-verbatim.md`; see
`D-2026-09-24-queue-resequenced-for-demo`.
Branch: task/T034-policy-action-and-verification
Sizing: configuration/action write path and verification semantics.

## Outcome

Accept a configuration/policy change from a dispatch Finding, inspect its frozen
world input, simulate the later operating window and ingest the new evidence.
Action/Maintenance Verification reports Verified, Ineffective or Inconclusive
from the target and guardrails together, with later reopening when warranted.

Completing the work item alone leaves the Finding unresolved.

This closes the shortest honest product story AssetOps has: detect, explain,
monetize, intervene, verify. It does not need fuel reconciliation, productive-use
opportunity or battery lifecycle to be worth showing.

## Read for detail

- v4 sections 5.2, 13 and 15.
- Roadmap sections 3.7, 7/H and 4.
- tasks/T029A-immutable-intervention-artifacts.md for the artifact mechanism.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Reuse T029A's immutable artifact mechanism for the time-valid policy/
configuration change, extending it with the accepted-action record: accepted
action, actor, target component/Site control, before/after values, effective
time and provenance.
Create a narrow Action/Maintenance link to the originating Finding.

Define the verification target, comparable windows and guardrails before
judging the result. Use accepted post-action evidence, not simulator event
success or the Action's completion status.

## Acceptance criteria

1. Accepting a change persists an inspectable configuration/action record and
   immutable world-change artifact. Editing the proposal creates a new version;
   frozen content and prior accepted state remain reconstructible.
2. Resolve baseline and post-change policy by effective time. Earlier Site
   evidence retains its original configuration basis.
3. Run setup freezes the intervention's materialized content and ordered history;
   missing or altered content fails honestly.
4. Simulated application changes controller/world behavior at the declared time
   and publishes observations/configuration evidence through the normal path.
5. Use a later post-action Site window in ordinary accepted history for
   operational verification. A same-window simulated comparison is not
   post-action evidence and cannot be relabelled as one.
6. Verification declares target runtime/fuel metric, improvement criterion,
   comparable-window rule, coverage requirement and guardrail thresholds before
   evaluating the new evidence. Version these rules with the assessment.
7. The guardrail set for this first verification story is battery reserve
   discipline, critical-load service and unserved energy over the window,
   computed from accepted meter, SOC and policy evidence with explicit coverage.
   Battery stress is deliberately not a guardrail here; T033 adds it to this
   same versioned rule set later. T035 extends the critical-service and
   unserved-energy metric into its ServiceWindow assessment rather than
   introducing a second basis.
8. Comparability accounts for relevant load/irradiance/capability and duration
   differences. Missing or incompatible context yields Inconclusive with reasons.
9. Verified requires the declared target and guardrails to pass with sufficient
   evidence; a target improvement with unacceptable guardrail trade-off is not
   Verified.
10. Adequately observed failure of the target/guardrails yields Ineffective with
    a reason; insufficient evidence yields Inconclusive rather than assumed
    success or failure.
11. Recording work completion without accepted post-action evidence cannot
    resolve the Finding or imply verification.
12. Preserve each verification attempt's windows, evidence references, rule
    version, outcome and Action/Finding linkage.
13. Later qualifying evidence can reopen the Finding under an explicit
    recurrence/guardrail rule; the prior Verified result remains in history.
14. Display target and guardrail outcomes together, with coverage, comparability
    limits and links to underlying evidence.
15. Operational verification carries a distinct claim label from any simulated
    comparison, and the simulated provenance of the post-action Site history
    stays visible. T032 must not relabel its comparison contexts as
    post-action observations.
16. Repeated evaluation of the same evidence/rules does not duplicate actions,
    histories or financial improvement. Any consequence uses D's separate bases.
17. API and UI enforce eligible state transitions; retry/reload preserves the
    accepted action and verification record without applying the change twice.

## Proof

| Case | Required outcome |
| --- | --- |
| Mark work completed, no later evidence | Finding unresolved; verification unavailable |
| Target improves, all guardrails pass | Verified with supporting references |
| Target unchanged despite adequate coverage | Ineffective |
| Runtime falls, critical service deteriorates | Not Verified; failed guardrail visible |
| Runtime falls, reserve breached | Not Verified; failed guardrail visible |
| Missing capability or meter coverage | Inconclusive where required |
| Materially different comparison conditions | Inconclusive/comparability limitation |
| Later recurrence after Verified | Reopened with preserved history |
| Retry accepted action/re-evaluate | No duplicated application or history |

Use a healthy post-change case, an ineffective change and a degraded-evidence
case, all generated by world causes and normal ingestion.
Run simulator/host, configuration/action, verification and UI tests,
shared checks and layout evidence for the full Finding-to-verification path.

## Scope limits

No generalized CMMS, work scheduling, approval hierarchy or maintenance catalog.
Implement the one policy/configuration intervention needed for the dispatch
story; preserve the category seam for later physical maintenance.
Battery stress guardrails, paired comparison and fuel reconciliation are not
prerequisites and must not be pulled in here.
Verification does not claim field-proven causal impact from a synthetic demo.

## Review

The owner completes an action without evidence, then compares the three
verification outcomes and a reopened case.
The Reviewer checks that no work-item transition bypasses evidence.

This is a demo checkpoint as well as a review: the owner judges whether the
detect -> explain -> monetize -> intervene -> verify path is showable to a
prospect as it stands, and what the answer implies for T030-T033 ordering.
Review outcome: pending.
