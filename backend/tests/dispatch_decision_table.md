# Dispatch analytic decision table (T028, model `dispatch-1`)

Stated before the classifier was written (task "Deliver"). The analytic is
`backend/assetops_backend/analytics/dispatch.py`; every threshold below is a
named constant there and part of model version `dispatch-1`. Changing any of
them is a new model version, and a new model version is a new assessment
revision (AC13). Tests: `backend/tests/test_t028_dispatch_analytic.py`.

## Evidence (accepted records only)

| Role | Device / signal | Required for |
| --- | --- | --- |
| Generator state | `generator-controller/status` (instant), `generator-controller/ac-power` (interval mean) | interval reconstruction (either) |
| Load | `residential-meter`, `clinic-meter`, `mill-meter` `/active-power` (all three) | every classification but a policy-only Necessary |
| PV capability | `pv-inverter-controller/available-power` | every measurement-based classification |
| Battery state | `battery-pcs-controller/state-of-charge` | Candidate; Necessary by reserve |
| Battery capability | `battery-pcs-controller/discharge-capability` | Candidate; Necessary by capability |
| Reserve policy | POLICY `battery-pcs-controller/policy-reserve-soc`, or a reserve OVERRIDE_COMMAND record | Candidate; Necessary by reserve |
| Minimum runtime | POLICY `generator-controller/policy-minimum-runtime` | optional (Necessary by minimum runtime) |
| Stop threshold | POLICY `generator-controller/policy-stop-soc-threshold` | optional (context for the policy alternative only) |
| Operator override | OPERATIONAL_RECORD `*/override-command` | optional (Necessary by operator command) |
| Generator output | `generator-controller/ac-power` | optional (fuel estimate only) |

Never used: observed PV output (`pv-inverter-controller/ac-power`) in place of
available PV capability (AC3); any simulator, Lab, stage or scenario data
(AC14); Foundation ratings except the generator's specific fuel consumption,
which is the fuel model's stated basis (AC10/11).

## Interval reconstruction (AC1)

Report times are the source times of generator state evidence. At each, the
generator is ON (status RUNNING, else output mean > 0), OFF (status STOPPED,
STARTING or FAILED, else output mean = 0) or UNOBSERVED. A DispatchInterval is
a maximal run of ON report times, with UNOBSERVED report times inside it
allowed and named as gaps; an OFF ends it.

- Lower bound: the sum of spans between consecutive ON report times that are
  at most `CONTINUITY_TOLERANCE` (20 min) apart. A longer span, or one
  through an UNOBSERVED time, is a temporal gap and counts in the upper bound
  only.
- Upper bound: from the latest OFF evidence before the interval (a STOPPED
  instant, or the end of a zero-output interval) to the earliest OFF evidence
  after it (a STOPPED instant, or the start of a zero-output interval). With
  no OFF evidence inside the assessed evidence, the bound is open at that side
  and says so; it is never extended to the window edge as assumed operation.
- An output mean > 0 shows running at some time inside its 5-minute span, not
  for all of it (the T027 whole-interval carry is not repeated here).

## Segment evaluation (AC2, AC7)

Each span between consecutive report times in an interval is a segment. Each
end (a report time) is evaluated as a point, from evidence at that time t:
interval means whose interval_end
is t; instants with source time in (t - `INSTANT_TOLERANCE` (10 min), t];
policy and override records effective at t (effective_start <= t, and
effective_end absent or > t; latest effective_start wins). Source time, not
arrival time, places a record (delayed evidence lands where it belongs).
Distinct records at one (signal, time) are conflicting and used by nothing.

`load` = sum of the three feeders; battery support = discharge capability,
counted only when SOC exceeds the effective reserve by more than
`SOC_HEADROOM_POINTS` (10 points): a battery a fraction of a point above
reserve has a capability rating but no energy to carry a deficit (found on the
healthy reference, whose SOC sits at 30.95 % against a 30 % reserve).

| Order | Classification | Condition (all evidence named must be usable at t) | Binding constraint |
| --- | --- | --- | --- |
| 1 | Necessary | a generator override record is effective and SOC is below its value or unknown | `OPERATOR_OVERRIDE` |
| 2 | Necessary | t is within the effective minimum runtime of the interval's first ON time | `MINIMUM_RUNTIME` |
| 3 | Necessary | load, PV available, SOC, reserve: SOC <= reserve + 10 points and load > PV available | `BATTERY_AT_RESERVE` (SOC <= reserve) or `BATTERY_NEAR_RESERVE` |
| 4 | Necessary | load, PV available, discharge capability: load > PV available + discharge capability | `CAPABILITY_SHORTFALL` |
| 5a | Candidate avoidable | load, PV available, discharge capability usable; PV available alone >= load x (1 + `CAPABILITY_HEADROOM` 10 %). SOC and reserve are not needed: the battery carries nothing, but its PCS must be evidenced available | none |
| 5b | Candidate avoidable | load, PV available, discharge capability, SOC, reserve usable; SOC > reserve + 10 points; PV available + discharge capability >= load x 1.1 | none (the candidate is the absence of one) |
| 6 | Indeterminate | anything else; names each missing or conflicting input, or "capability margin inside the declared headroom" | - |

A segment is Candidate only when both of its ends are Candidate, Necessary
when either end is Necessary (that end's binding constraint is shown), and
otherwise Indeterminate, so a transition inside a segment never becomes
candidate time. A one-observation interval is evaluated at that point.
A segment whose generator state is UNOBSERVED is Indeterminate ("generator
state not observed") and counts in the upper bound only.

## Interval classification and claim (AC4, AC5)

| Segments | Interval claim level |
| --- | --- |
| all Necessary | Necessary (binding constraints listed per segment) |
| at least one Candidate | Candidate avoidable, bounded to the candidate segments' duration; Necessary and Indeterminate portions are listed with their own durations, never folded into the candidate total |
| otherwise | Indeterminate (missing/conflicting evidence named) |

A Finding (type `generator-dispatch-interval`) is emitted for an interval whose
claim level is Candidate avoidable or Indeterminate. A Necessary interval is an
assessment without a Finding (it is shown by Dispatch, not raised as
something to act on). Open for owner review: whether Necessary intervals should
be Findings too.

## Coverage, confidence (AC6)

Coverage: per required input, segments where it was usable out of segments
evaluated, and the temporal spans where it was not; the share of time the
5-minute means measure (5 of 15 minutes) is stated, not hidden.

Confidence is a level with its basis, not a score. Candidate avoidable or
Necessary starts High and drops one level (to Medium, then Low) for each of:
an Indeterminate portion inside the interval; the smallest candidate margin
below `STRONG_MARGIN` (25 % of load) (Candidate only); transition uncertainty
(upper minus lower bound) above `TRANSITION_LIMIT` (15 min). Indeterminate has
no confidence level (`NOT_APPLICABLE`).

## Override absence (AC7)

No override record in an interval is stated as "no operator-commanded override
record observed", and listed as an alternative that cannot be excluded. It is
never evidence that no override existed, and it does not change confidence.

## Indicative fuel (AC10, AC11)

Only for Candidate avoidable: candidate duration [lower, upper] x generator
output [min, max of usable means in candidate segments] x the Foundation's
generator specific fuel consumption x (1 -/+ `SFC_UNCERTAINTY` 10 %).
Duration and output are measured, consumption is configured, so the quantity
is `modelled`. Unavailable (with the reason) when no output mean is usable in
a candidate segment, the upper duration bound is open, or no specific fuel
consumption is configured. It is not a reconciled tank loss and not a saving.

## Carried question: stop-60's policy record (backlog "For T028")

Answer: the analytic does not need it, and the honest publication would need a
change this slice may not make.

- The stop threshold is not a classification input above. It is context for
  the "policy constraint" alternative only: a generator held on below its stop
  threshold is consistent with that policy, and the candidate is about the
  policy, not a controller fault. Stop-60 classifies the same with or without
  a stop-threshold record.
- Under profile 5 stop-60 publishes the Foundation's 90 % stop threshold as
  its only stop policy record, while the world stops at 60 %. When the
  interval's observed stop happens with SOC below the published stop
  threshold (and no override record explains it), the alternative says the
  published policy does not explain the stop and the effective policy may
  differ, instead of quoting 90 % as effective.
- Should stop-60's change surface as a policy record (version, effective
  interval, source)? Per `D-2026-10-02-scenario-states-override-issuer` a
  change with no issuer is not an operator command, so it is a configuration
  fact; publishing it as a POLICY record needs a scenario or publication
  change (the record source is the Foundation today). That is outside T028:
  recorded as an owner question in the phase handoff, not made here.
