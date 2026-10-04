# T028 independent Codex review

Reviewer: **Codex**, 2026-10-04, independent of the Claude implementers.
Verdict: **RETURN — five blocking correctness findings.**

Reviewed `38177b3..3e75a54` on `task/T028-dispatch-finding-and-evidence`.
Checkout HEAD is `3a0603e`; its only addition after the requested target is
the review brief. No implementation changes, merges, suite reruns or changes
to user data were made. This report does not record owner acceptance.

## Blocking findings

### R1 — P1: Include interval-bound and alternative evidence in revision identity

Anchors: `backend/assetops_backend/analytics/dispatch.py:806`;
`backend/assetops_backend/analytics/service.py:181`.

The evidence digest includes running observations and segment inputs, but
omits the stopped observations used to bound the interval and records used
only by alternatives. Reconciliation treats an unchanged digest/model as an
unchanged assessment, even when the newly computed payload differs.

**Executed reproduction:** assess the existing hand-built world through
minute 120, with RUNNING reports from 15 through 120. Then append STOPPED
status and zero output at minute 135. A fresh calculation closes the interval
at 02:10 and changes fuel from UNAVAILABLE to BOUNDED. The service retains
revision 1, open end 02:00 and UNAVAILABLE fuel. Its digest is unchanged.
The same result survives a new `JsonAssessmentStore` instance reading a
temporary store. Alternative-only evidence also leaves the digest unchanged
(the override in R2 demonstrates this).

**Blocks:** AC13 is not met; accepted evidence can change the conclusion
without an inspectable revision, and subsequent reads persistently serve the
old explanation. This is an expensive history/provenance defect before T029
builds on these quantities. Fingerprint every dependency of the assessment,
including bounds, alternatives and configured fuel basis; retain the old
revision and add regression coverage for late stop/alternative evidence.

### R2 — P1: Evaluate effective policy changes between generator report times

Anchor: `backend/assetops_backend/analytics/dispatch.py:764`.

Only `run.on_times` become evaluation points. A policy/override effective
entirely inside a report-to-report segment is never assessed, even though
the alternatives code finds it and claims it was included at its time.

**Executed reproduction:** add a generator stop-SOC override of 95%, effective
01:05–01:10, to the normal fixture with 15-minute reports and SOC 60%.
The 01:00–01:15 segment stays Candidate avoidable with no binding constraint;
all 15 minutes remain in the candidate fuel duration. The alternative says
the override is observed and “included in the constraint assessment at its
time.” It is not. This occurs in a fresh calculation independently of R1.

**Blocks:** AC2 and AC7 require known commands to affect assessment at their
effective time. The candidate includes evidenced commanded operation and
its explanation is false. Account for effective-start/end boundaries when
segmenting or conservatively limit the affected span; do not invent new
measurements at those boundaries. Cover commands wholly between reports.

### R3 — P1: Enforce SOC headroom in the battery-supported candidate branch

Anchor: `backend/assetops_backend/analytics/dispatch.py:447`.

The near-reserve rejection only applies when load exceeds PV. If PV equals
load, or exceeds it by less than the required 10% margin, execution reaches
the battery-supported branch without checking SOC against reserve plus
10 points. It counts discharge capability as available support regardless.

**Executed reproduction:** load 20 kW, PV capability 20 kW, discharge
capability 30 kW, SOC 30%, reserve 30%. After minimum runtime, the result is
Candidate avoidable with BOUNDED fuel. Its reason explicitly says “SOC 30 %,
more than 10 points above its 30 % reserve.”

**Blocks:** AC2/4 and decision-table row 5b are violated, producing a false
constraint explanation and fuel consequence. Require the declared SOC
headroom before counting battery support. Under the current decision table,
PV at load with no battery support does not meet the 10% candidate margin;
this finding does not imply that such an interval must instead be Necessary.
Cover equality and the range between load and load times 1.1.

### R4 — P1: Do not silently select one of conflicting effective policy records

Anchor: `backend/assetops_backend/analytics/dispatch.py:204`.

`_Evidence.effective` selects the first record at the greatest effective-start
and policy-version rank. Equal-rank contradictory records are not reported
as conflicting. This differs from measurement lookups and from the decision
table's promise that distinct conflicting records are used by nothing.
Accepted evidence can contain distinct message IDs from different gateways
at the same signal/time (`evidence/models.py:7`).

**Executed reproduction:** give the fixture PV 10 kW, load 20 kW and SOC 60%.
Add a second gateway's reserve policy with the same effective start/version
but value 70%, alongside the existing 30% record. The analytic selects 30%,
returns Candidate avoidable, reports no missing/conflicting evidence and
omits the contradictory record from its basis. The 70% reserve would bind.

**Blocks:** AC5 requires conflicting evidence that prevents a decision to be
named. A gateway/message ordering cannot settle an operational policy and
support a candidate fuel claim. Detect conflicting top-rank effective records
and expose the conflict; an independent binding constraint may still support
a narrower assessment. Cover both policy and override lookup ambiguity.

### R5 — P2: Include generator-state gaps in capability readiness

Anchor: `backend/assetops_backend/analytics/declaration.py:201`.

`_coverage_gaps` reads only `coverage.inputs`, which contains load, PV, SOC,
reserve and discharge capability. It never reads
`coverage.unobserved_generator_state`. Generator gaps therefore disappear
from readiness even when they explicitly made an assessed segment Indeterminate.

**Executed reproduction:** use the existing AC1 gap fixture: omit generator
records strictly between minutes 90 and 150 while retaining the other
signals. The analytic reports a 60-minute generator gap and one hour
Indeterminate. Readiness nevertheless returns FULL, `missing_evidence: []`
and one assessed interval. The screen consequently says no claim-limiting
gaps were identified.

**Blocks:** AC20 and `D-2026-10-04-analytic-readiness-scope-and-gap-impact`
explicitly require claim-limiting gaps to lower readiness. This is a false
Full claim under the adopted interim rule, not a request to implement T028A
or to change site-wide scope. Include these gaps in scoring and disclosure,
with a read-model regression and a screen assertion for the resulting row.

## Carries and existing residuals

- **C1 — P3, carry: unknown Finding types lose the backend display name.**
  `frontend/src/sites/FindingDetail.tsx:136` and
  `frontend/src/sites/FindingsIndexes.tsx:91` call `findingTypeLabel` without
  the backend display name. The fallback in `presentationProfile.ts:167`
  therefore shows the raw ID even though the declaration provides a display
  name. AC18's Finding-type fallback is only partially met. Carry because the
  ID still renders and the sole shipped type is mapped; this is a cheap
  presentation repair, not lost evidence or a changed claim. The coordinator
  should add this new carry to `.ai/MILESTONE_REVIEW_BACKLOG.md`; this review
  brief authorizes writing the review only.
- **Existing layout residual — carry, not independently diagnosed.**
  `.agent/T028-layout-evidence.txt:393` records the profile-4 observed/not-staged
  failure. The reviewed diff does not change the Lab run/status implementation;
  the packet also reports a prior occurrence. That supports carrying it
  separately from T028, but does not prove it is a flake. Retain it for a
  focused Lab check rather than report the entire layout run as green.
  The other failures at lines 124, 135, 146 and 559 are the documented blocked
  fixture and performance carries. All recorded T028 layout claims pass.
- **Existing runtime metric and read cost — carry.** The Overview runtime
  metric's different duration basis is already recorded in
  `.ai/MILESTONE_REVIEW_BACKLOG.md:1724`. Assessment work on global Findings
  reads (`analytics_api.py:64`) and declaration reads (`analytics_api.py:88`)
  remains a demo-scale performance risk, not a reason to add a caching project
  to this correction round.

## Review coverage and validation limits

Read the task, packet, all three handoffs, owner rulings, readiness Architect
record, applicable project rules/decisions, decision table, analytic/service/
store/API implementation, declaration guard, screen composition and relevant
tests. Static inspection supports the accepted-evidence/private-truth boundary,
shared assessment identity across Overview/Dispatch/Finding, persisted prior
revision structure, and backend ownership of readiness. The five findings
above qualify the packet's corresponding “met” claims.

The brief's recorded results are accepted as supplied, **not rerun**: at
`3e75a54`, backend 1468, host 616, frontend 1098, TypeScript and both shared
checks pass. Simulator 244, production build and layout 560 PASS / 5 FAIL
were measured at `9524382`. No fresh browser or gate-closed browser pass was
performed by this reviewer.

Independent execution was limited to small stdin Python probes using the
existing accepted-record fixture helpers in
`backend/tests/test_t028_dispatch_analytic.py`, `dispatch.assess`, readiness
scoring, `AssessmentService`, an in-memory store and a temporary JSON store.
These were not suite reruns or new end-to-end ingestion proofs. Reproduction
inputs and actual outputs are recorded under each finding. No probe files
were added to the repository.

The approved choices remain accepted: Necessary assessments need not raise
Findings; stop-60 needs no new policy publication in T028; readiness stays
site-wide with an explicit interim claim-dependent gap rule; configurable
gap impacts remain T028A. None of the blockers requires reopening those choices.

Return to implementation for R1–R5, meaningful regression checks and the
appropriate analytic/readiness version changes while preserving prior
history. Independent re-review and the task's owner UI check still follow.
Practitioner usefulness has not been established by this review or by tests;
the expert-feedback checkpoint remains outstanding.
