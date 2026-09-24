# T035 - Bahir start failure and evidence-backed service assessment

Status: planned
USER_REVIEW_REQUIRED: true

Map: I prerequisite; explicit owner of the service/start-failure gap.
Depends on: T025 discrete generator world, T027 evidence, C Finding views and
T034's critical-service/unserved-energy guardrail metric.
Delivery order: interchangeable with T033, then T036.
T033 and T035 consume nothing from each other: both depend only on T027's
evidence, T029's assumptions and T034's rule set, and whichever runs second is
unaffected by the choice. Which comes first is a product-priority call taken
from T028/T029 feedback, not a sequencing constraint. If the operator finds
backup failure and unserved customers more pressing than battery degradation,
run this one first and move T033 behind it.
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
    the detailed service view; portfolio can reuse it in T036.
11. Any economic service exposure uses D's labelled assumptions and stays
    separate from measured energy and realized loss.
    A monetary value is optional when no approved basis exists.
12. Accepted assessment survives Lab disable/private artifact removal and
    rebuild from the committed envelope/configuration path.
13. Existing dispatch, fuel and opportunity stories remain derived normally;
    the new recipe cannot directly seed their assessments.

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
layout evidence for the service assessment.

## Scope limits

No generalized incident-management subsystem, alarm inbox, escalation workflow
or outage-ticket lifecycle. One outage chain, assessed.
No reliability forecasting, protection/switching enums or detailed engine model.
No private assertion of starter-relay failure in the operator Finding.
T036 owns multi-site composition and the client walkthrough.

## Review

The owner distinguishes actual unmet service from a telemetry gap and checks
the backup-cause claim against its evidence.
Review outcome: pending.
