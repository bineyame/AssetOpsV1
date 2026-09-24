# T028 - First dispatch Finding with challengeable evidence

Status: planned
USER_REVIEW_REQUIRED: true

Map: C; earliest domain-expert feedback checkpoint.
Depends on: T027, T025 healthy/prolonged-runtime recipes and T026 evidence.
Next: T029 after this checkpoint; reassess later work from feedback.
Branch: task/T028-dispatch-finding-and-evidence
Sizing: first analytics/Finding semantics.

## Outcome

Site Overview -> Performance/Dispatch -> Finding Detail -> Evidence explains a
generator interval classified Necessary, Candidate Avoidable or Indeterminate.
The practitioner can inspect constraints, coverage, confidence, alternatives,
claim limits and an indicative bounded fuel quantity.

This is the first valuable Finding. It precedes fuel reconciliation and does
not require priced Financials or a portfolio.

## Read for detail

- Roadmap sections 3.3, 4, 7/C and 13.2.
- FEATURE_MAP C.
- v4 sections 3, 11-12, 17 and 25 for evidence/recipe boundaries.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Reconstruct DispatchInterval from accepted generator, PV, BMS, meter and
time-valid policy evidence. Evaluate whether the observed operating constraints
support generator necessity or a bounded candidate-avoidable interpretation.

Build one canonical Finding presentation with supporting evidence, competing
explanations, confidence and claim ceiling, reused from Overview and Dispatch.
Keep analytic/model version, source evidence references and assessed window.

Before implementing classifications, state the minimal decision table beside
the analytic tests: evidence required, constraints evaluated, coverage rule and
what makes each classification available. Keep thresholds explicit and
versioned; do not seek a general optimization framework.

## Acceptance criteria

1. Generator intervals are reconstructed from accepted timestamped evidence.
   Gaps and uncertain transition times bound interval duration rather than
   becoming continuous assumed operation.
2. Evaluate load, PV capability, battery SOC/discharge capability, reserve,
   generator constraints and effective policy at the interval's time.
3. Observed PV output alone cannot stand in for available PV capability.
   Missing battery capability cannot be replaced from simulator truth.
4. Necessary has an inspectable binding constraint.
   Candidate Avoidable is a bounded candidate under declared evidence/model
   assumptions, not a claim of proven waste or optimal dispatch.
5. Indeterminate identifies which missing/conflicting evidence prevents the
   decision. One weak portion cannot be hidden inside a high-confidence total.
6. Coverage identifies signal coverage and temporal gaps; confidence states its
   basis separately from coverage. Neither is a fabricated precision score.
7. Missing operator-commanded override evidence is shown as none observed,
   not proof that an override did not exist. Known override records affect
   constraint assessment at their effective time.
8. Include alternatives such as unavailable PCS capability, policy constraints
   or unobserved override; evidence links let a reviewer challenge them.
9. The prolonged-runtime recipe produces a candidate interval through normal
   ingestion; the healthy reference does not receive a scripted Finding.
10. Show indicative associated fuel quantity as a bounded estimate with duration,
    power/consumption inputs, model basis and uncertainty.
    If those inputs cannot support a bound, show unavailable with the reason.
11. Quantity basis is measured/modelled/scenario as applicable.
    This fuel estimate does not imply a reconciled tank loss or financial saving.
12. Finding Detail and Dispatch refer to the same assessed object and evidence.
    Overview links to that Finding instead of recomputing a separate claim.
13. Rerunning on the same accepted evidence/model version yields the same
    assessment without duplicate active Findings.
    Changed accepted evidence creates an inspectable assessment revision.
14. Removing private recipes, world state and oracles does not change the
    analytic result or remove its ability to explain the conclusion.
15. The screen path exposes context, selected window, classification, supporting
    facts, gaps, confidence, alternatives and bounded fuel without requiring Lab.

## Proof

| Evidence case | Required assessment |
| --- | --- |
| Healthy supported-demand interval | Necessary where constrained; no false candidate |
| Prolonged-runtime interval, adequate capability | Candidate Avoidable with reasons |
| PCS capability missing for part of interval | Segmented/limited claim and named gap |
| Insufficient capability throughout | Indeterminate, not fabricated avoidance |
| Time-valid reserve prevents battery support | Necessity/limit explained |
| Override record present | Constraint included |
| Override absent | Absence limitation explicit |
| Delayed/out-of-order evidence | Source-time reconstruction with provenance |
| Remove private simulator data | Same product assessment |
| Hand-calculated bounded fuel example | Matching range and displayed basis |

Tests must check classification/limits and evidence references, not just the
presence of a Finding card. Run backend analytic/read-model tests, frontend
navigation tests, shared checks and populated layout evidence.

## Scope limits

T029 adds priced consequence. T030 adds FuelBalanceWindow.
No financial ranking, optimal-dispatch solver or portfolio readiness claim.
Full Replay and broad source-health UI are not prerequisites.

## Review

Walk roadmap 13.2 with the owner and prepare a compact expert-feedback example:
one candidate interval, one constraint, one gap and its bounded fuel estimate.
Record expert feedback when obtained; do not mark practitioner usefulness as
automatically proven by tests or contact anyone without authorization.

Practitioner usefulness has no automated proof, so the checkpoint needs
questions it can fail. Ask whether the expert can challenge the classification
from what the screen shows, whether the evidence they would want before acting
is either present or named as missing, and whether the claim ceiling is one
they would repeat to an operator. Three yeses is the pass; anything else is
feedback that redirects later work rather than a defect list for this slice.
Review outcome: pending.
