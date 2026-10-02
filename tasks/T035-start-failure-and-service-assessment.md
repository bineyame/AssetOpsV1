# T035 - Bahir start failure and evidence-backed service assessment

Status: planned
USER_REVIEW_REQUIRED: true
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).

Map: I prerequisite; explicit owner of the service/start-failure gap.
Depends on: T025 discrete generator world, T027 evidence, C Finding views,
T034's critical-service/unserved-energy guardrail metric and T034A Portfolio
and seed.
Delivery order: after T030; next T033, then T025i and T036. Interchangeable
with T033; the default is service before battery (`tasks/README.md`).
T033 and T035 consume nothing from each other: both depend only on T027's
evidence, T029's assumptions, T034's rule set and T034A's Portfolio, and
whichever runs second is unaffected by the choice. Which comes first is a
product-priority call taken from T028/T029 feedback, not a sequencing
constraint. If feedback finds battery degradation more pressing than backup
failure and unserved customers, run T033 first and move this one behind it.
Branch: task/T035-start-failure-and-service-assessment
Sizing: one reliability story across causal world and product assessment.

## Outcome

A Bahir-like Site requests backup generation that physically fails to start.
Lab shows the failed transition and unmet critical demand.
The operator sees a ServiceWindow, unserved energy and a bounded backup/service
Finding derived from accepted evidence, with evidence gaps clearly separated.

The other five portfolio stories do not supply this reliability assessment.

## Leanness standard

`Docs/queue-review-feedback-verbatim.md` sets the bar this slice is judged by:
one credible outage -> backup response -> unserved-energy chain, without
building a generalized incident-management subsystem. If a criterion below
cannot be traced to that chain, cut it rather than implement it.

## Read for detail

- v4 sections 4.3, 13, 17, 20 and 25.
- Roadmap sections 4, 5.1 and 7/I.
- Shared checks and exclusions: tasks/README.md.

## Deliver and acceptance

1. Add a cause-authored generator start-failure recipe using the existing
   discrete-state contract, requested control and physical acceptance.
   Author the failure cause, not a service Finding.
2. A failed start produces no generator power. Battery/PV limits and critical
   priority determine accepted service and unserved load.
3. A healthy variant with the failure removed restores physically available
   backup response under the same demands and initial inputs.
4. Publish the ordinary generator state/power, load/service meter, battery and
   any supported alarm/command evidence through canonical envelopes.
   Private failure cause and trace stay private.
5. Reconstruct ServiceWindow from accepted evidence with duration, served/
   unserved energy, critical-service basis and coverage. Extend T034's
   critical-service/unserved-energy metric rather than introducing a second
   measurement basis for the same quantity.
6. State the demand/service measurement basis. Missing demand or served-load
   evidence limits unserved-energy calculation instead of importing private
   requested demand or treating absent telemetry as service failure.
7. Back a generator start-failure interpretation only with accepted observable
   failure/status/command evidence. Otherwise report a bounded backup/service
   issue and the missing evidence needed to identify cause.
8. Finding/Evidence links explain operating context, service consequence,
   alternative explanations and confidence/claim limits.
9. Distinguish a device/gateway outage from measured service loss.
   Evidence degradation changes claim capability, not the private outage.
10. Site Overview shows service attention using the same assessed object as
    the detailed service view; Portfolio reuses it (AC17).
11. Any economic service exposure uses D's labelled assumptions and stays
    separate from measured energy and realized loss.
    A monetary value is optional when no approved basis exists.
12. Accepted assessment survives Lab disable/private artifact removal and
    rebuild from the committed envelope/configuration path.
13. Existing dispatch, fuel and opportunity stories remain derived normally;
    the new recipe cannot directly seed their assessments.
14. After reload, the existing gated transition/timeline display shows the
    physical start-failure cause and state, reported generator status separately,
    and each addressed load's service deficit. Physical generator FAILED is
    distinct from execution FAILED and from a sensor/reporting outage.
15. Performance renders Service (unserved energy and coverage) and Backup (the
    event chain with missing links stated), per recommendation section 3 Site
    Performance. The backup failure stands as a Finding; no incident object.
16. The service and backup analytics join the capability declaration
    (`D-2026-10-02-presentation-profile-and-capability-declaration`), giving
    them Site > Evidence capability rows, their Performance subtabs and the
    Service Overview card's assessment slot.
17. Bahir joins the Portfolio: Bahir's reproducible recipe and seed (T036
    AC1's Bahir recipe, pulled forward) under
    `D-2026-10-02-demo-point-seed-rule`, its own Site through normal
    ingestion, extending the point-3 seed command. Service exposure stays a
    separate consequence type (T034A AC5).

## Proof

| Case | Required result |
| --- | --- |
| Requested start fails with inadequate alternative supply | Physical unmet load |
| Remove start-failure cause | Backup/service changes causally |
| Failure status and service evidence accepted | Bounded service/backup Finding |
| Service measured but failure cause unobserved | Service claim, limited cause |
| Missing meter/status due to reporting outage | Data gap, not invented outage |
| Demand evidence absent | Unserved quantity limited/unavailable |
| Remove private trace after Commit | Same product assessment |

Check a hand-derived short service deficit and critical-load allocation.
Demonstrate the healthy and failed cases through normal ingestion.
Run simulator/host, evidence/analytic/frontend tests, shared checks and
`node tools/layout-evidence.mjs` on Service, Backup and Portfolio. Rail
unchanged; Site tabs unchanged at seven, with Performance gaining Service and
Backup subtabs.

*UI check:* on the seed with Lab off, Portfolio shows Bahir's service Finding;
open Bahir > Performance > Service and Backup, and tell measured unmet service
from a telemetry gap.

## Scope limits

No generalized incident-management subsystem, alarm inbox, escalation workflow
or outage-ticket lifecycle. One outage chain, assessed.
No reliability forecasting, protection/switching enums or detailed engine model.
No private assertion of starter-relay failure in the operator Finding.
T036 owns the client walkthrough.

## Review

The owner distinguishes actual unmet service from a telemetry gap and checks
the backup-cause claim against its evidence.
Review outcome: pending.
