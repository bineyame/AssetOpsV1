# T032 - Frozen load addition and isolated paired comparison

Status: planned
USER_REVIEW_REQUIRED: true

Map: F completion; intervention machinery reused by H.
Depends on: T031, T027 evidence path and T029 BusinessContext.
Next: T033, then T034 reuses immutable interventions.
Branch: task/T032-paired-load-addition-comparison
Sizing: first intervention artifact and comparison-history boundary.

## Outcome

From a productive-use opportunity, evaluate a scheduled load addition.
Inspect frozen intervention content and compare baseline/intervention energy
use/sales, PV use, curtailment and diesel from newly ingested evidence.

Both worlds may use the same Site/time window. Their accepted evidence remains
separate from ordinary Site history and from each other.

## Read for detail

- v4 sections 5.2, 13 and 15.
- Roadmap sections 3.5, 4, 7/F and 12.2.
- .ai/ARCHITECTURE.md: Evidence Loop Boundaries. The comparison contexts are
  accepted evidence reached through normal ingestion, not a parallel store.
- FEATURE_MAP F's comparison-history requirement.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Materialize each run-scoped change before execution as immutable canonical
FrozenInterventionArtifact content. Its reference is a content digest; the run
persists the content and ordered references required to reconstruct it.

Introduce immutable PairedExperiment metadata once both identities are frozen.
Compare resolved effective inputs at field/path grain, retaining the original
Foundation/scenario versions as provenance rather than using them as proof.

Use a dedicated accepted comparison-history context keyed by experiment and
side, retaining original Site identity/provenance.
Route each side's committed envelopes through normal validation/normalization
into that context. Ordinary Site Overview/Financials/portfolio queries exclude
these contexts; the comparison explicitly selects baseline and intervention.
Context routing belongs to release/ingestion metadata, not simulator truth.

## Acceptance criteria

1. LOAD_ADDITION freezes component identity, connection, rated power, schedule,
   load characteristics and provenance sufficient to reconstruct the new world.
   Choose a small milling/cold-room electrical load for the internal example.
2. Intervention references resolve only immutable content-addressed artifacts
   persisted with the run; a mutable external identifier cannot stand in for one.
3. Tampering, missing artifact content or digest mismatch blocks execution/
   comparison with an inspectable reason.
4. Dynamic changes are applied at the declared boundary through world inputs;
   the action cannot assign a Finding or economic result.
5. The paired record includes both run ids, comparison kind, exact declared
   delta, shared effective-input digest, provenance and status.
   Pairing does not alter either run's deterministic identity.
6. Compare resolved initialization keyed by StateRef, component/Site controls,
   forcing identities/parameters, observation/publication/cadence bindings,
   mappings, topology/properties, numeric/model/kernel/contract versions,
   seed/RNG contract and ordered intervention content.
7. Exclude only the exact declared load-addition artifact/affected paths.
   Additional hidden changes yield NOT_COMPARABLE with the differing paths.
8. Foundation/scenario version changes retain provenance and trigger effective
   input comparison; omitting an opaque version field alone proves nothing.
9. Wider intentional bundles may be labelled multi-change scenario comparisons,
   but cannot claim single-variable/all-else-equal status.
10. Allocate both comparison history contexts before either side is released.
    Reject a comparison release with missing/ambiguous context; do not fall back
    to ordinary Site history.
11. Normal ingestion owns acceptance/rejection and received_at in both contexts.
    Strict envelope validation, idempotence and conflict handling still apply.
12. Overlapping timestamps and original Site identities can coexist across the
    two contexts. A retry within one side cannot duplicate its accepted facts.
13. Ordinary Site history and portfolio totals remain unchanged after both
    releases. No deletion/overwrite of baseline records is used for comparison.
14. Comparison metrics use each side's accepted evidence/read models with
    matched windows, units, coverage and BusinessContext assumptions.
15. Present served/used energy, scenario sales basis, PV use, curtailment and
    diesel deltas. Missing inputs limit individual metrics and comparisons.
16. Tariff/revenue values are visibly scenario-based; physical headroom and
    simulated sales do not establish local market demand.
17. First intervention control owns reset/history behavior:
    resetting an editable setup creates a fresh Draft from declared baseline;
    frozen runs/artifacts/pair history are preserved, not cleared or rewritten.
    Re-execution uses the frozen ordered history; a changed intervention creates
    a new identity/pair rather than mutating the previous comparison.
18. Comparison reload/rebuild works from sealed envelopes, referenced
    configuration and immutable artifacts without private simulator state.
19. UI says simulated intervention comparison and exposes delta/comparability
    proof and evidence. It cannot claim verified real-world impact.
20. Before external demo recording, obtain the user's recognizable load choice
    under roadmap 12.2. This does not block the underlying internal example.

## Proof

Start with a valid scheduled load-addition pair and compare accepted results.
Independently calculate one simple added-load energy window.

| Mutation | Required result |
| --- | --- |
| Change only declared load artifact | Comparable |
| Also change reserve inside new Foundation version | NOT_COMPARABLE |
| Also change forcing/initial SOC/seed | NOT_COMPARABLE |
| Also change publication cadence or mapping | NOT_COMPARABLE |
| Missing/tampered intervention artifact | Honest execution/comparison failure |
| Attach pair metadata after freezing | Run identities/trajectories unchanged |
| Commit both sides at same Site/time | Separate accepted contexts |
| Retry one release | Same side's totals unchanged |
| Query ordinary Site/portfolio | Neither side added or overwritten |
| Reset/edit an intervention setup | New Draft; old artifact/history intact |
| Remove private truth and rebuild | Same comparison from accepted evidence |

Test exact-path comparison with unrelated changes hidden in the same version
update. A test comparing only version ids does not satisfy this slice.

Run simulator/host, artifact persistence, ingestion-context, comparison and UI
tests, shared checks and layout evidence on the comparison.
The review packet records the selected history context in every release/query
path so isolation is demonstrated beyond a UI filter.

## Scope limits

Implement load addition only; generic intervention-category authoring can wait.
A cold-room electrical load is not a cold-chain physical model.
T034 owns policy/configuration action and operational verification.
No automatic promotion of scenario-comparison evidence into ordinary history.

## Review

The owner inspects the immutable delta, rejects a secretly changed pair and
verifies that normal Site totals did not change.
The Reviewer checks context isolation before both sides are released.
Review outcome: pending.
