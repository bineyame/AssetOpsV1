# Decisions

## 2026-09-11

Decision: M1 uses the preferred MVP stack from the product specification:
Python/FastAPI backend, React/TypeScript frontend, Python deterministic
simulator, modular monolith, strict boundary parsers, file-backed repositories
where sufficient, single-host container deployment, and CI-enforced architecture
guards.

Reason: The first tasks need a concrete, production-compatible but simple
technical direction before backend, frontend, simulator, parser, repository, and
CI boundaries can be planned.

Affected scope: Architecture, implementation stack, local development,
deployment, parser contracts, repository choices, CI guard planning.

## 2026-09-11

Decision: Simulator Lab is gated by `simulator_lab.enabled`, deployment-wide for
M1 and shaped for future per-tenant gating. When disabled, simulator routes,
navigation, entry points, execution actions, and truth overlays are not served,
while existing simulated Sites, SIMULATED provenance, operator routes,
analytics, and Replay remain unchanged.

Reason: Simulator execution and truth surfaces must be removable without
changing the normal AssetOps product model or leaking simulator-only capability
through hidden-but-reachable routes.

Affected scope: Simulator Lab routing, navigation, feature flags, truth overlay,
operator shell, simulated Site provenance, Replay, architecture guards,
acceptance testing.

## 2026-09-11

Decision: Start AssetOps with a lightweight Architect/Planner, Implementer,
Reviewer workflow and vertical-slice tasks.

Reason: The repository needs low context cost, frequent human review, independent
review, and protection against speculative architecture.

Affected scope: Repository governance, feature planning, task planning, review
model.

## 2026-09-11

Decision: Treat private simulator truth as separate from product-visible
evidence from the first slice.

Reason: AssetOps should learn from realistic site/device observations without
accidentally depending on privileged simulator internals.

Affected scope: Simulator, ingestion, analytics, evidence, UI claims.

## 2026-09-11

Decision: Treat UI-verifiable outcomes as the default standard for vertical
slice development.

Reason: The first useful AssetOps learning should come from screens the user can
inspect, especially the Simulator Lab and site operations screens in
`Docs/UI Design/Motivation`.

Affected scope: Task planning, backend scope, frontend scope, acceptance
criteria, review packets.

## 2026-09-11

Decision: Treat Architect, Planner, Implementer, and Reviewer as configurable
roles with default agent bindings.

Reason: Planner and Architect should default to Codex agents, Implementer should
default to a Claude agent, and future projects should be able to change those
bindings without redefining role responsibilities.

Affected scope: Role configuration, Claude Code commands, skills, workflow
handoffs.

## 2026-09-11

Decision: M1 will use a narrowed canonical Site Foundation schema with stable
Site identity plus versioned Site Foundation, stored in YAML for the initial
slice.

Reason: The first milestone needs canonical Site semantics that support
arbitrary Sites without hard-coding MG-001, while avoiding the scope of the full
future AssetOps Site schema before the simulator, gateway, and ingestion path is
proven.

Affected scope: Site configuration, Site identity, SimulatorRun references,
topology, devices, mappings, ratings, control assumptions, ingestion
provenance, UI task breakdown.

## 2026-09-11

Decision: The first Simulator Lab vertical slice will use a deterministic
recorded-run player instead of implementing the complete physical runtime.

Reason: The recorded player gives the first UI slice truthful simulation time,
world state, events, device reporting, and gateway publication while preserving
the intended runtime, ingestion, and AssetOps contracts. It is a bootstrap state
producer only, and must not introduce a demo-only ingestion path or precomputed
AssetOps conclusions.

Affected scope: Simulator runtime contract, Simulator Lab UI, recorded world
state, device reporting, gateway staging, ingestion boundary, deterministic
runtime migration, task sequencing.

## 2026-09-11

Decision: M1 will separate the canonical Source Envelope from typed AssetOps
evidence contracts.

Reason: Source envelopes should provide strict identity, timing, sequencing,
publication, provenance, and transport structure while typed evidence contracts
carry family-specific semantics. This avoids both demo-only ingestion shortcuts
and a permissive `{type, payload}` model, while supporting gateway/source
health, generator runtime, and fuel reconciliation from evidence a real device,
controller, operator, import, or external source could publish.

Affected scope: Ingestion contract, evidence contracts, telemetry, events,
alarms, operational records, controller records, validation, source health,
simulator publication, analytics, provenance, task sequencing.

## 2026-09-11

Decision: M1 Commit is a state transition that releases a completed Draft
SimulationRun's immutable staged Source Envelopes for AssetOps ingestion.

Reason: Commit must preserve the authored evidence publications exactly, avoid
copy/regeneration semantics, and keep ownership clear: Simulator Lab owns
`STAGED -> RELEASED`; AssetOps ingestion owns `RELEASED -> ACCEPTED | REJECTED`.
Commit is atomic and idempotent at the SimulationRun release scope, and it never
creates Site history, health state, findings, incidents, analytics, or other
derived product objects directly.

Affected scope: SimulationRun lifecycle, staged publication storage, release
manifest, message identity, ingestion validation, source timestamps,
`received_at`, UI task breakdown, audit and replay semantics.

## 2026-09-11

Decision: M1 will implement the Single-Line Diagram using a reusable hybrid
mini-grid archetype template with data bindings, rather than a fully automatic
topology-layout engine.

Reason: The first milestone needs a truthful diagram that can be implemented in
a reviewable slice without treating layout as canonical topology. Site
Foundation remains the source of truth for components, topology, connectivity,
ratings, devices, and signal availability; the archetype owns only presentation
and validates compatibility explicitly.

Affected scope: Site Foundation topology, SLD view model, Site Configuration,
Simulator Lab SLD, runtime overlays, evidence overlays, topology compatibility,
future graph/layout migration.

## 2026-09-11

Decision: M1 will implement product conclusions in causal order:
Gateway/Source Health, Generator Runtime Assessment, then Fuel
Reconciliation/Fuel Discrepancy.

Reason: Downstream analytics first need evidence coverage, timeliness, and
validity. Generator runtime must be established before fuel movement can be
reconciled, and a fuel discrepancy becomes a Finding only when materiality and
confidence criteria warrant operator attention. The product must use bounded
language such as unexplained fuel variance and must not infer theft or hidden
cause from discrepancy alone.

Affected scope: Source health, evidence availability, generator runtime
assessment, fuel reconciliation, findings, confidence/materiality criteria,
claim language, cold-room follow-on sequencing, UI task breakdown.

## 2026-09-11

Decision: M1 will use progressive disclosure for provenance: primary product
screens show decision-relevant provenance, while detailed technical provenance
is available through Evidence/Provenance inspection drawers and ingestion/log
views.

Reason: Operators need to see source mode, time window, freshness,
completeness, and claim limitations immediately, but low-level transport detail
should not crowd normal product screens. Provenance visibility should increase
with consequence: raw measurements need minimal provenance, assessments need
evidence sufficiency, and Findings or recommendations need inspectable evidence
basis. Scenario/private-truth causes remain outside product evidence provenance.

Affected scope: Site headers, source-mode display, evidence summaries,
Gateway/source health, Findings, recommendations, Evidence/Provenance drawer,
ingestion/log views, Simulator Lab reproducibility metadata, UI task breakdown.

## 2026-09-11

Decision: M1 allows canonical Sites to exist before they have live integrations
or SimulationRun evidence. Such Sites are valid configuration-only Sites.

Reason: A Site may be meaningfully configured before operational evidence
exists. AssetOps must show declared identity, lifecycle, location, timezone,
Foundation, topology, devices, mappings, ratings, control assumptions, and
intended source/integration configuration without fabricating operational
evidence, health, analytics, charts, or conclusions.

Affected scope: Sites List, Site Details, Site Configuration, configuration-only
Sites, source mode, lifecycle state, integration readiness, evidence
availability, gateway/source health, SLD runtime overlays, simulator exercises
of intended-live Site Foundations, UI task breakdown.

## 2026-09-11

Decision: M1 keeps canonical Site/Foundation configuration file-backed in YAML
and provides a read-only Site Configuration UI.

Reason: YAML should remain the authoritative source of truth for Site identity,
Foundation version, components, topology, devices, mappings, ratings, control
assumptions, and related configuration while the simulator, gateway, ingestion,
and evidence path is proven. The UI can render and explain configuration,
Foundation version, effective dates, SLD, and device/signal relationships, but
in-product editing, persistence, save/publish, approvals, and configuration
history management are deferred.

Affected scope: YAML Site/Foundation configuration, configuration validation,
Site Configuration UI, edit affordances, Foundation version/validity display,
SLD configuration display, device/signal relationship display, future
configuration API migration, task sequencing.

## 2026-09-11

Decision: M1 allows overlapping Draft SimulationRuns, but blocks Commit when a
Draft interval overlaps already committed simulated history for the same
`site_id`.

Reason: Simulator Lab needs Draft overlap for scenario experimentation, reruns,
and deterministic comparison, while AssetOps needs unambiguous committed Site
history until explicit branch/context selection exists. Simulation intervals use
half-open semantics `[start_time, end_time)`. Committed source evidence is
immutable; rerun creates a new Draft `run_id`, and replay inspects committed
persisted evidence without rerunning.

Affected scope: SimulationRun lifecycle, Commit eligibility, half-open interval
validation, run management UI, rerun/replay semantics, deterministic identity,
committed evidence immutability, future branch/context selection, admin reset
boundaries, task sequencing.
