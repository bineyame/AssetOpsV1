# T032 - Frozen load addition and isolated paired comparison

Status: planned
USER_REVIEW_REQUIRED: true

Map: F completion.
Depends on: T031, T027 evidence path, T029 BusinessContext and T029A
immutable intervention artifacts.
Delivery order: after T031; next T033. T034 no longer waits on this slice:
`D-2026-09-24-queue-resequenced-for-demo` moved the mechanism into T029A.
Branch: task/T032-paired-load-addition-comparison
Sizing: comparison-history boundary over an existing intervention mechanism.

## Outcome

From a productive-use opportunity, evaluate a scheduled load addition.
Inspect the frozen intervention content and compare baseline against
intervention on one screen: PV use, curtailment, diesel, energy served and
scenario revenue.

Both worlds may use the same Site/time window. Their accepted evidence remains
separate from ordinary Site history and from each other.

## Build exactly this comparison

Same site, same window, same forcing, same initial conditions, same policy.
One declared difference: the added productive load. Then show the five
quantities above, side by side, with their comparability proof.

The rigorous frozen-input machinery below exists to make that one comparison
trustworthy. Implement exactly enough of it for this scenario. A generalized
experimentation platform is not in scope and is the main way this slice fails.

## Read for detail

- v4 sections 5.2, 13 and 15.
- Roadmap sections 3.5, 4, 7/F and 12.2.
- tasks/T029A-immutable-intervention-artifacts.md for the artifact mechanism.
- .ai/ARCHITECTURE.md: Evidence Loop Boundaries. The comparison contexts are
  accepted evidence reached through normal ingestion, not a parallel store.
- FEATURE_MAP F's comparison-history requirement.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Add a LOAD_ADDITION kind to T029A's immutable artifact mechanism. Its
immutability, digest enforcement, declared-boundary application and
reset/frozen-history rules apply unchanged and are not re-proved here.

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
2. The paired record includes both run ids, comparison kind, exact declared
   delta, shared effective-input digest, provenance and status.
   Pairing does not alter either run's deterministic identity.
3. Compare resolved initialization keyed by StateRef, component/Site controls,
   forcing identities/parameters, observation/publication/cadence bindings,
   mappings, topology/properties, numeric/model/kernel/contract versions,
   seed/RNG contract and ordered intervention content.
4. Exclude only the exact declared load-addition artifact/affected paths.
   Additional hidden changes yield NOT_COMPARABLE with the differing paths.
5. Foundation/scenario version changes retain provenance and trigger effective
   input comparison; omitting an opaque version field alone proves nothing.
6. Wider intentional bundles may be labelled multi-change scenario comparisons,
   but cannot claim single-variable/all-else-equal status.
7. Allocate both comparison history contexts before either side is released.
   Reject a comparison release with missing/ambiguous context; do not fall back
   to ordinary Site history.
8. Normal ingestion owns acceptance/rejection and received_at in both contexts.
   Strict envelope validation, idempotence and conflict handling still apply.
9. Overlapping timestamps and original Site identities can coexist across the
   two contexts. A retry within one side cannot duplicate its accepted facts.
10. Ordinary Site history and portfolio totals remain unchanged after both
    releases. No deletion/overwrite of baseline records is used for comparison.
11. Comparison contexts stay excluded from T034's operational verification and
    cannot be relabelled as post-action observations.
12. Comparison metrics use each side's accepted evidence/read models with
    matched windows, units, coverage and BusinessContext assumptions.
13. Present served/used energy, scenario sales basis, PV use, curtailment and
    diesel deltas. Missing inputs limit individual metrics and comparisons.
14. Tariff/revenue values are visibly scenario-based; physical headroom and
    simulated sales do not establish local market demand.
15. A changed intervention creates a new identity and therefore a new pair
    rather than mutating the previous comparison.
16. Comparison reload/rebuild works from sealed envelopes, referenced
    configuration and immutable artifacts without private simulator state.
17. UI says simulated intervention comparison and exposes delta/comparability
    proof and evidence. It cannot claim verified real-world impact.
18. Before external demo recording, obtain the user's recognizable load choice
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
| Attach pair metadata after freezing | Run identities/trajectories unchanged |
| Commit both sides at same Site/time | Separate accepted contexts |
| Retry one release | Same side's totals unchanged |
| Query ordinary Site/portfolio | Neither side added or overwritten |
| Query T034 verification windows | Comparison contexts absent |
| Remove private truth and rebuild | Same comparison from accepted evidence |

Test exact-path comparison with unrelated changes hidden in the same version
update. A test comparing only version ids does not satisfy this slice.

Run simulator/host, ingestion-context, comparison and UI tests, shared checks
and layout evidence on the comparison.
The review packet records the selected history context in every release/query
path so isolation is demonstrated beyond a UI filter.

## Scope limits

Implement load addition only; generic intervention-category authoring can wait.
Do not build a generalized experimentation platform, scenario matrix or
experiment dashboard. One load-addition comparison is the deliverable.
A cold-room electrical load is not a cold-chain physical model.
T029A owns artifact immutability and reset behavior; T034 owns operational
verification. No automatic promotion of scenario-comparison evidence into
ordinary history.

## Review

The owner inspects the immutable delta, rejects a secretly changed pair and
verifies that normal Site totals did not change.
The Reviewer checks context isolation before both sides are released.
Review outcome: pending.
