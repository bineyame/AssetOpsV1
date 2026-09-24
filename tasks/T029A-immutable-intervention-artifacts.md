# T029A - Immutable run-scoped intervention artifacts

Status: planned
USER_REVIEW_REQUIRED: true

Map: H prerequisite, reused by F.
Depends on: T025 typed Controls and generator policy, T022 frozen execution.
Delivery order: after T029; next T034. Only T025 and T022 are technical
prerequisites, so the T028 feedback checkpoint may move it.
Branch: task/T029A-immutable-intervention-artifacts
Sizing: first intervention write path and world-input boundary.

## Why this exists separately

T032 owned this mechanism, which put the first verification story behind a
productive-use analytic and a paired-comparison platform.
`Docs/queue-review-feedback-verbatim.md` asked for the minimal immutable
policy-intervention mechanism to be extracted so verification can happen
shortly after T029. See `D-2026-09-24-queue-resequenced-for-demo`.

This is the mechanism only. Paired comparison, effective-input diffing and
isolated comparison history stay in T032.

## Outcome

In Lab, declare a time-valid policy or control change on a run setup, freeze it,
inspect the immutable artifact and its content digest, then execute and see
generator runtime and battery behavior change at the declared effective time.
The pre-change run, its artifacts and its history remain intact and re-runnable.

## Read for detail

- v4 sections 5.2, 13 and 15.
- Roadmap sections 3.7 and 7/H.
- .ai/ARCHITECTURE.md: Evidence Loop Boundaries.
- FEATURE_MAP H's intervention machinery.
- Shared checks and exclusions: tasks/README.md.

## Deliver and acceptance

1. Materialize each run-scoped change before execution as immutable canonical
   FrozenInterventionArtifact content. Its reference is a content digest; the
   run persists the content and the ordered references needed to reconstruct it.
2. Implement one kind, POLICY_CHANGE: a time-valid component or Site Control
   change carrying before/after values, target address, effective time and
   provenance. LOAD_ADDITION is T032; no generic category authoring here.
3. Intervention references resolve only immutable content-addressed artifacts
   persisted with the run. A mutable external identifier cannot stand in for one.
4. Tampering, missing artifact content or digest mismatch blocks execution with
   an inspectable reason rather than a silent fallback to baseline.
5. The change is applied at its declared boundary through world inputs.
   The intervention cannot assign a Finding, verification outcome or economic
   result, and cannot write accepted evidence directly.
6. Resetting an editable setup creates a fresh Draft from the declared baseline.
   Frozen runs, artifacts and their ordered history are preserved, never
   cleared or rewritten.
7. Re-execution uses the frozen ordered history and reproduces the same
   trajectory. A changed intervention creates a new run identity rather than
   mutating the previous one.
8. Reload and rebuild the intervention content from sealed persistence without
   live world objects or private simulator state.
9. The Lab control is utilitarian: declare, freeze, inspect, run, compare to the
   baseline run by identity. No experiment dashboard, template library or
   scheduling UI.

## Proof

| Case | Required result |
| --- | --- |
| Declare policy change, freeze, run | Behavior changes at the declared time |
| Same frozen content re-executed | Identical trajectory |
| Tampered or missing artifact content | Honest execution failure with reason |
| Mutable reference in place of digest | Rejected |
| Edit the intervention | New run identity; prior run and artifact intact |
| Reset the setup | Fresh Draft; frozen history preserved |
| Remove live world objects and reload | Same artifact content and digest |
| Baseline run with no intervention | Unchanged from T025 behavior |

Hand-check one interval where the changed control alters generator runtime.
Run simulator/host, artifact persistence, run-setup and Lab UI tests, shared
checks and layout evidence for the intervention control.

## Scope limits

No PairedExperiment metadata, effective-input comparison, NOT_COMPARABLE rule
or comparison history context; all four are T032.
No Action/Maintenance record, Finding link or verification semantics; T034.
No CMMS, approval hierarchy or maintenance catalog.

## Review

The owner declares a policy change, inspects the frozen delta and confirms the
baseline run is untouched. The Reviewer checks immutability, digest enforcement
and that the intervention writes no evidence or conclusion.
Review outcome: pending.
