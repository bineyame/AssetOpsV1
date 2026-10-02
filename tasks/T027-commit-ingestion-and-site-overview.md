# T027 - Commit through normal ingestion to Site Overview

Status: planned
USER_REVIEW_REQUIRED: true

Map: B completion; internal architecture demo (demo point 1).
Depends on: T025 and T026.
Next: T028 dispatch Finding (queue order per `D-2026-10-02-demo-led-recommendation`).
Branch: task/T027-commit-ingestion-and-site-overview
Sizing: first Commit/ingestion/evidence write path; two phases in one file.
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).

## Outcome

Run a mini-grid, inspect truth/readings/stage, Commit, then open the Site in
the operator product, populated solely by normal ingestion: first Site >
Evidence (accepted records, their quality and coverage), then a mini-grid Site
Overview. Disable Lab and keep viewing the accepted Site history.
Rebuild the same view from committed envelopes and referenced configuration.

This is the internal architecture checkpoint, not the client-demo finish line.

## Read for detail

- v4 sections 3, 11, 21 and 25.
- Roadmap sections 3.2, 7/B and 13.1.
- `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` 3 "Site Overview"/"Evidence", 5.2, 6.2.
- `.ai/ARCHITECTURE.md`: Evidence Loop Boundaries, Configuration Persistence,
  Presentation Honesty, Shared Presentation Substrate.
- Decisions: `D-2026-10-02-rendered-tabs-per-capability`,
  `D-2026-10-02-presentation-profile-and-capability-declaration`, owner
  disposition D6 in `D-2026-10-02-demo-led-recommendation`.
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

Make Site > Evidence a destination (part A only, per D6; AC20), with the record
inspector as its drill-down, not its body. Build the selected-window mini-grid
Site Overview in the v6.9 8.18 frame: objective strip, one card per profile
domain, measured metrics with coverage, the selected-day timeline and evidence
links. Unsupported/unobserved metrics are unavailable.

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
5. received_at is assigned by ingestion. T026's delayed publication case
   therefore shows three distinct source, publication and receipt timestamps.
   T026A later proves the same under full outage and recovery.
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
    signals the Overview metrics need (not signals an analytic requires; none
    exists before T028) and the selected window; no sample carry-forward
    becomes an undocumented fresh measurement.
11. Site Overview exposes window/context, metrics with units and evidence links
    into the record inspector. With no analytic, every card shows a neutral
    "No assessment yet"; the healthy reference shows no material current
    Finding without inventing an analytic result before T028. "Unknown" is not
    used for lack of an analytic.
12. Evidence inspection shows source/device/signal, mapping/config version,
    quality, original values/units, normalized values and all three timestamps.
    The inspector opens from Site > Evidence source and signal rows (and, in
    phase 2, from Overview evidence links) without changing the root.
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
18. Run status keeps Commit/release and ingestion acceptance separate. After
    Commit, an Open in AssetOps link targets the correct Site, selected window
    and accepted-history context and displays actual release/acceptance outcome;
    it never implies every record was accepted. It lands on Site > Evidence.
19. With Lab gated off, every new Lab history/series route and private payload
    is inaccessible. Rebuild product views with Lab routes and private execution
    artifacts unavailable; accepted evidence alone supplies operator views.
20. Site > Evidence renders source/connector health per source, per-signal
    coverage for the selected window and the mapping/configuration basis, and
    nothing about capability readiness or claim ceilings.
21. Site tabs follow `D-2026-10-02-rendered-tabs-per-capability`: one canonical
    inventory filtered by capability renders Overview, Foundation, Evidence;
    Foundation renders `Definition | Topology | Controls` with no Readiness.
    No operator tab or subtab is labelled in place or disabled; the
    `navigation-truthfulness` check is updated without loosening.
22. The mini-grid presentation profile is substrate data keyed by `site_type`
    and owns only which Overview cards exist and their order (Service,
    Dispatch, Battery, Fuel, Renewable). Card state never comes from it.

## Phases

One file (it fits 220 lines; phase 1 need not merge alone), one branch. Each
phase ends with committed work, an owner UI check and
`.agent/T027-phase-N-handoff.md` (`.ai/ROLE_CONFIG.md` "Build large slices in
phases"). Full suites and the packet belong to phase 2.

**Phase 1: Commit, ingestion, Site > Evidence (part A), tab rule.**
ACs 1-9, 12, 16-18, 20, 21 in full; 10, 13, 14, 15, 19 for evidence and
Site > Evidence (coverage per signal; Evidence survives gate-off and rebuild).
AC18 lands on Site > Evidence for the committed window, because that page is
where actual accepted coverage and rejections are visible and the Overview
frame does not exist until phase 2; it stays there in phase 2.
Tab-rule anchors (in `frontend/src/`): `shell/operatorSiteTabs.tsx`
(`labelled_in_place` entries, `OperatorSiteLabelledTab`,
`labelledAspectsSentence`, module comment), `sites/FoundationSubtabs.tsx`
(Readiness), tests `shell/__tests__/operatorSiteTabs.test.tsx`,
`sites/__tests__/foundationScreen.test.tsx`,
`ui/__tests__/overflowContainment.test.tsx`; comments in
`shell/simulatorLabRoutes.tsx` and `ui/DataTable.tsx`; and
`tools/checks/navigation-truthfulness.ps1`, whose "labelled in place, never
disabled" messages become: not rendered, never disabled, never labelled in
place in operator views.
*UI check:* Lab run -> Commit -> Open in AssetOps -> Site > Evidence shows
source health, coverage and a record drill-down with three timestamps; Lab
off, it stays.

**Phase 2: the mini-grid Site Overview.**
ACs 11 and 22 in full; 10 (each card names its coverage), 12 (Overview
evidence links), 13, 14, 15, 19 extended to the Overview read model.
Card metrics from Kobo template v3 signals: Service (served energy, three
feeder meters), Dispatch (generator runtime), Battery (SOC), Fuel (tank level
only; no consumption or loss inference, T030), Renewable (PV inverter output).
An uncovered card names its coverage gap, never a fabricated value. The
timeline (demand, PV, generator, SOC) is context, not a status source.
*UI check:* the internal architecture demo, recommendation 5.2 row 1:
Lab run -> stage -> Commit -> Sites -> Kobo Overview -> Evidence -> Lab off,
history stays.

Rendered after each phase: rail Sites, no group header (T002 `Operator home`
in `frontend/src/shell/OperatorShellLayout.tsx` stays until T029B; rec. 2.1);
Site tabs Overview, Foundation, Evidence. Run `node tools/layout-evidence.mjs`
per phase (Evidence, then Overview; populated and empty).

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
| Delayed publication | Three distinct timestamp meanings |
| Missing capability/report | Coverage gap, no fabricated value |
| Disable Lab | Operator history and evidence remain |
| Remove private artifacts and rebuild | Same accepted operating result |
| Change current configuration | Historic evidence basis unchanged |
| Commit with partial rejection; follow Open in AssetOps | Correct Site/window, actual accepted coverage |

Run ingestion/repository/read-model tests, neutral host integration, frontend
tests, shared checks and layout evidence (per phase, above).

## Scope limits

**Do the minimum robust implementation necessary to prove source-envelope ->
normal ingestion -> persistent Site Overview. Do not turn this into a
generalized ingestion reliability project.** Resumability, for example, can be
simple and correct rather than production-scale.

The acceptance criteria above are kept in substance and none of them is
optional: they sit on a protected seam, which is why this slice is watched for
scope growth rather than trimmed. Satisfy each one at the smallest honest
implementation that holds, and stop there. Round two of
`Docs/queue-review-feedback-verbatim.md` is the source of this instruction.

No dispatch classification, capability declaration, capability table or claim
ceiling yet; T028 owns them.
No full Replay UI and no broad (cross-site) source-health dashboard. The
site-scoped source-health section of Site > Evidence is in scope (AC20).
Sites columns (Last analysed, Evidence coverage) and Sites as the landing page
are T029B, per the point-2 protection rule; the Sites index is unchanged here.
No seed: demo point 1 is a live run (`D-2026-10-02-demo-point-seed-rule`).
Shared-window paired experiments must wait for T032's separate comparison
history context; ordinary Site history is not a place to merge both sides.
Gateway outage, buffering, retry and out-of-order recovery are T026A and are
not prerequisites for this checkpoint.

## Review

The owner runs the internal architecture demonstration with Lab disabled for
the final operator inspection. The Reviewer independently exercises recovery,
idempotence and reconstruction without simulator objects.
Review outcome: pending.
