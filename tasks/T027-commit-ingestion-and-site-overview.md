# T027 - Commit through normal ingestion to Site Overview

Status: planned
USER_REVIEW_REQUIRED: true

Map: B completion; internal architecture demo.
Depends on: T025 and T026.
Next: T028 dispatch Finding.
Branch: task/T027-commit-ingestion-and-site-overview
Sizing: first Commit/ingestion/evidence write path.

## Outcome

Run a mini-grid, inspect truth/readings/stage, Commit, then open a basic operator
Site Overview populated solely by normal ingestion.
Disable Lab and keep viewing the accepted Site history.
Rebuild the same view from committed envelopes and referenced configuration.

This is the internal architecture checkpoint, not the client-demo finish line.

## Read for detail

- v4 sections 3, 11, 21 and 25.
- Roadmap sections 3.2, 7/B and 13.1.
- .ai/ARCHITECTURE.md: Evidence Loop Boundaries and Configuration Persistence.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Seal eligible stage content into an immutable committed artifact/manifest with
content integrity and frozen schema/mapping/configuration references.
Release that artifact through the same normal ingestion interface available to
non-simulator sources. Commit itself writes no Evidence or read model.

Ingestion validates/normalizes accepted records, persists rejections and assigns
received_at. Product evidence/read models use accepted content only.
Retain source_time and gateway/publication time independently.
Telemetry and T026's operational override/command records cross this one path;
an operational record's occurrence and effective time stay distinct from its
publication and receipt times.

Build the minimum selected-window Site Overview and evidence inspector:
served energy where measured, renewable contribution, battery state, generator
runtime and coverage. Unsupported/unobserved metrics are unavailable.

## Acceptance criteria

1. Eligible completed staged content can be committed once with a durable
   manifest identifying its exact envelopes and content integrity.
   Failed/corrupt/incompatible content cannot be labelled fully committed.
2. A sealed artifact is immutable. A retry after release interruption resumes
   safely using the same artifact and identities, rather than editing it.
3. Ingestion accepts only the strict canonical schema and resolves the
   referenced mapping/configuration version and effective time.
   Invalid mapping, unit, identity or content yields an inspectable rejection.
4. Simulated and equivalent ordinary canonical inputs use one validation/
   normalization path. SIMULATED provenance survives as source provenance.
5. received_at is assigned by ingestion. Delayed recovery can therefore show
   distinct source, publication and receipt timestamps.
6. Duplicate identity/content is idempotent across retry and restart.
   Same identity/different content produces a conflict and preserves the
   original accepted content.
7. Accepted records, rejections and release progress survive reload.
   An interrupted mixed batch exposes its actual status and recoverable work;
   it cannot imply that every staged record became accepted.
8. Operator read models include only accepted content, never current stage,
   raw observation, world, LabProjection, private trace or scenario expectation.
9. Define overlapping-record handling explicitly at source identity/time grain:
   distinct conflicting measurements remain inspectable evidence, not silent
   last-write-wins or duplicate energy accumulation.
10. Preserve missingness and quality during normalization. Coverage names the
    required signals and selected window; no sample carry-forward becomes an
    undocumented fresh measurement.
11. Site Overview exposes window/context, metrics with units and evidence links.
    Healthy reference can show no material current Finding without inventing
    an analytic result before T028.
12. Evidence inspection shows source/device/signal, mapping/config version,
    quality, original values/units, normalized values and all three timestamps.
13. Gate off: operator Site history/Overview/Evidence remain accessible, while
    Lab execution, stage and private comparison disappear.
14. Rebuild the Site view in an empty derived store using only committed
    envelopes and referenced immutable configuration. Derived results match
    the original, excluding explicitly nondeterministic receipt audit times.
15. Repeat reconstruction with no private simulator artifacts or installed
    runtime composition. No product dependency on simulator/host is required.
16. Product ingestion attempts with private object payloads are rejected.
    Dependency guards still reject backend/simulator cross-imports.
17. Current Foundation edits cannot rewrite historic interpretation.
    Evidence retains the configuration/time basis originally accepted.

## Proof

Demonstrate the roadmap 13.1 path end to end using the electrical site.
Persist the evidence needed to repeat it without the Lab runtime.

| Case | Expected product behavior |
| --- | --- |
| Stage without Commit | No accepted history change |
| Valid Commit | Accepted evidence populates selected Site window |
| Bad mapping or unit in batch | Rejection visible, valid status accurate |
| Duplicate release after restart | No duplicated metric or history entry |
| Same id, changed content | Conflict; original preserved |
| Gateway outage/recovery | Three distinct timestamp meanings |
| Missing capability/report | Coverage gap, no fabricated value |
| Disable Lab | Operator history and evidence remain |
| Remove private artifacts and rebuild | Same accepted operating result |
| Change current configuration | Historic evidence basis unchanged |

Run ingestion/repository/read-model tests, neutral host integration, frontend
tests, shared checks and layout evidence on populated and empty Overview.

## Scope limits

No dispatch classification yet; T028 owns it.
No full Replay UI or broad source-health dashboard is required for C.
Shared-window paired experiments must wait for T032's separate comparison
history context; ordinary Site history is not a place to merge both sides.

## Review

The owner runs the internal architecture demonstration with Lab disabled for
the final operator inspection. The Reviewer independently exercises recovery,
idempotence and reconstruction without simulator objects.
Review outcome: pending.
