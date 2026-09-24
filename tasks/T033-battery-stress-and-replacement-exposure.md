# T033 - Battery stress trajectory and bounded replacement exposure

Status: planned
USER_REVIEW_REQUIRED: true

Map: G.
Depends on: A battery model, T027 evidence, T029 assumptions, C Finding views
and T034's versioned verification rule set.
Delivery order: after T032; next T035. Under schedule pressure this is the
first major story to move behind early client feedback - see
`Docs/queue-review-feedback-verbatim.md` and
`D-2026-09-24-queue-resequenced-for-demo`. Deferring it does not weaken the
core proposition.
Branch: task/T033-battery-stress-and-replacement-exposure
Sizing: causal stress and evidence-derived lifecycle interpretation.

## Outcome

Battery Health, Site Overview and Financials show current state where evidenced,
stress recurrence/trajectory, a reference band and bounded replacement exposure.
The owner can distinguish a synthetic aged asset from an asset whose historical
stress is unknown.

This adds the slow-burn lifecycle story. T034 already verifies without it;
this slice adds battery stress to H's existing versioned guardrail set.

## Read for detail

- v4 sections 10.2, 14, 17 and 22.
- Roadmap sections 3.6, 7/G and 12.3.
- Shared checks and exclusions: tasks/README.md.

## Deliver and acceptance

1. Add a simple declared battery stress model from accepted physical operation:
   throughput plus at least one relevant exposure such as high SOC, high power
   or temperature. State the model/basis and reference envelope.
2. Every run-start accumulated stress value has an explicit dynamic initial
   condition and basis: synthetic-new zero, authored aged, historical snapshot
   or unknown. Foundation ownership is reserved for asset properties.
3. Unknown historical stress remains unknown. A capability needing lifetime
   accumulation is unavailable/limited, while observable window stress can
   still be assessed with its separate start/window basis.
4. Private stress evolves causally from power/SOC/temperature exposure as
   declared; different operation produces different accumulation.
5. Provide accepted SOC, battery power, temperature and capability evidence
   through the normal device/gateway/Commit/ingestion path.
   Any modelled temperature profile/thermal simplification is explicit.
6. The product derives its trajectory from accepted evidence and its analytic
   version/reference basis, never from the private stress accumulator.
7. Evidence-derived stress identifies dimensions, units/window and coverage.
   Gaps bound or interrupt accumulation rather than implying zero stress.
8. Current SoH/state is shown only where its evidence supports it; a stress
   index cannot silently become measured SoH.
9. Compare recurring stress against an inspectable expected/reference band.
   Distinguish observed history from any modelled projection.
10. Battery Health links trajectory points and limitations to source evidence.
    Overview references the same assessment rather than a separate score.
11. BusinessContext supplies replacement value and a labelled scenario exposure
    assumption. Technical trajectory and monetary basis remain separate.
12. A price change alters replacement exposure, not stress or technical confidence.
    Financials avoids adding full replacement value to OPEX as realized loss.
13. Show no exact remaining-life/replacement date from this simple model.
14. Internally use roadmap 12.3's trajectory/replacement-value/scenario-exposure
    default. Obtain the user's lifecycle monetization choice before external
    exposure; retain an honest technical-only view if not approved.
15. Arsi-like stress and healthy reference recipes author operation/initial
    conditions only. Their product trajectories survive removal of private data.
16. Add battery stress to T034's verification guardrail set as a new rule
    version. Earlier verification results keep their original rule version and
    outcome and are not retroactively re-judged.

## Proof

| Case | Required behavior |
| --- | --- |
| Synthetic new asset with explicit zero | Zero basis visible |
| Synthetic aged initial condition | Authored prior stress retained |
| Unknown prior stress | Lifetime claim limited, not zero-filled |
| Same initial asset, increased throughput/exposure | Increased private stress |
| Same accepted evidence, different private accumulator | Same product trajectory |
| Missing telemetry interval | Coverage limitation, no fabricated exposure |
| Healthy versus stress recipe | Explainable recurrence/reference difference |
| Replacement price change | Money changes, technical result fixed |
| Re-verify an earlier action under the new rule version | Original result preserved |

Use independently calculated throughput and one exposure-window case.
Check that product queries cannot access private accumulator objects.
Run simulator/host, publication/ingestion, analytic/financial and UI tests,
shared checks and layout evidence for Battery Health and Financials.

## Scope limits

No electrochemical model, exact RUL, warranty adjudication or asset-management
suite. A stress proxy is not a calibrated failure prediction.
Generator wear sophistication remains deferred.

## Review

The owner reviews the unknown-stress case, reference band and scenario
replacement exposure. The Reviewer checks evidence-derived reconstruction.
Review outcome: pending.
