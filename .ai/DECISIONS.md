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

## 2026-09-13

Decision: Site and Site Foundation configuration is reached only through a
`SiteRepository` port defined in the product domain, with storage technology
supplied by an adapter selected in a single composition root. The port speaks
domain records and port-level errors; it never exposes files, paths, YAML text,
serialization formats, or store-specific exceptions. M1 ships two read adapters
over shipped canonical configuration and user-authored configuration, plus one
write adapter for user-authored configuration. Replacing file storage with any
other mechanism must require a new adapter module and one composition-root
change, and no change to callers.

This supersedes part of the 2026-09-11 decision "M1 keeps canonical
Site/Foundation configuration file-backed in YAML and provides a read-only Site
Configuration UI", specifically its deferral of persistence. Persistence is no
longer deferred for user-authored configuration. Everything else in that
decision still stands: YAML remains the serialization format and the
authoritative representation of Site identity and Foundation content, strict
validation on load is unchanged, and approvals and configuration history
management remain deferred. The read-only-UI clause is addressed separately
below.

Reason: The user requires the persistence mechanism to be replaceable later
without rewriting callers. A naming convention does not deliver that; a port
with a testable dependency direction does. Introducing it before any Site read
model exists is cheap, and retrofitting it after Sites, templates, SLD view
models, and evidence resolution all reach storage directly is expensive and
error-prone. Keeping the port free of file and format vocabulary is what makes
the swap real rather than nominal.

Affected scope: Site read models, Site Configuration UI data path, Site
templates, user-authored Site creation, backend module tree, composition root,
strict boundary parsers, CI architecture guard, future configuration API or
database migration, task sequencing.

## 2026-09-13

Decision: M1 distinguishes shipped canonical configuration templates from
user-created Site instances as separate concepts in separate identity spaces and
separate stores. A template has `template_id` and `template_version`, ships
read-only in the repository, and is not a Site: it has no `site_id`, no
lifecycle status, no location or timezone binding, and it cannot appear in the
Sites index, be targeted by a scenario, be simulated, or receive evidence.
Instantiating a template copies its Foundation content into a new Site document
and records `template_id` and `template_version` as origin provenance; the
created Site does not live-reference the template, and later template changes
never alter existing Sites. Shipped Sites and user-created Sites occupy one
globally unique `site_id` space with no overlay and no precedence: the same
`site_id` present in both stores is a startup-level conflict, and creation
refuses any `site_id` already present in either store. Configuration origin
(`SHIPPED` or `USER`) is provenance about the configuration document and is a
separate concept from `source.mode`, lifecycle status, integration readiness,
and source health.

This refines rather than supersedes the 2026-09-11 "YAML configuration
authority" position. YAML remains authoritative and strictly validated on load
in both stores. What changes is only who may write it: shipped configuration
stays read-only at runtime, and a second writable store holds user-authored
documents.

Reason: The distinction the user asked for only survives if it is structural. If
a user Site were created by copying a shipped Site, shipped Sites would silently
become templates and the precedence, identity, and provenance rules would have
to be retrofitted after user data exists. Overlay resolution was rejected
because a `site_id` that resolves to different content depending on store state
breaks the identity seam that every later run, envelope, evidence record, and
analytic is keyed on. Encoding origin into identity, such as prefixing
user-created `site_id` values, was rejected for the same reason the project
refuses to let a scenario label become a Site name: origin is provenance about a
configuration document and must not be readable out of the identity that
downstream history is keyed on. Copy-on-instantiate was chosen over live
reference because
a shipped template change would otherwise retroactively alter Foundations that
committed simulated history already depends on.

Affected scope: Site identity, template catalog, Site creation, configuration
origin provenance, Sites index, Site Details, Site Configuration UI, store
layout, identity validation, strict parsers, CI architecture guard, scenario
targeting, future template versioning and drift inspection, task sequencing.

## 2026-09-13

Decision: M1 makes Site creation a real product capability while keeping the
Site Configuration UI read-only. A user may create a Site by choosing a shipped
template and supplying identity and required identity-level fields; the
resulting Site is validated as a complete document and persisted through the
write adapter. In-place editing of an existing Site Foundation remains
unavailable, as do Save, Publish, approval, rename, delete, `site_id` change,
Foundation version bump in place, configuration diff, history, and rollback.
`site_id` is immutable after creation. The Site Configuration UI renders every
Site read-only regardless of origin and must state that configuration is fixed
at creation in M1, rather than implying an editing workflow that does not exist.
User-authored configuration is untrusted input: it crosses the same strict
parser as shipped configuration, with no lenient path, and the fully
materialized document is validated before anything is written.

This supersedes part of the 2026-09-11 decision "M1 keeps canonical
Site/Foundation configuration file-backed in YAML and provides a read-only Site
Configuration UI", and correspondingly narrows the "Read-only configuration UI"
enforceable seam. Superseded: the blanket deferral of in-product authoring and
of save semantics, which now exist for creation. Still standing in full:
in-place Foundation editing, Save and Publish over an existing Foundation,
approvals, configuration history and rollback are deferred; the Site
Configuration UI itself remains read-only and offers no edit affordance; strict
validation on load is unchanged; YAML remains the authoritative representation.

Reason: Creating a Site and editing a Site are different capabilities with
different risk. Creation writes a new `site_id` that no run, envelope, evidence
record, mapping version, or committed history depends on yet, so its blast
radius is bounded by validation of one new document. In-place editing mutates a
Foundation that later slices bind evidence and committed simulated history to,
and raises Foundation re-versioning, effective dating, revalidation against
existing evidence, and the question of what happens to committed history when a
mapping changes. M1 needs the first capability and has no answer for the second,
so shipping creation now and deferring editing keeps the milestone honest
instead of implying a configuration lifecycle the product does not have.

Affected scope: Site Configuration UI language and affordances, Site creation
flow, identity validation, untrusted-input handling, write-path atomicity,
Foundation versioning, deferred editing and history semantics, protected seams,
task sequencing, user-review checkpoints.

## 2026-09-13

Decision: M1 offers no user-facing way to remove a user-created Site. The
`SiteRepository` port exposes no `delete`, no archive, and no tombstone, and no
UI affordance or route removes a Site. Removing a user-created Site is a
developer action on the store for the whole of M1. If removal is wanted later it
becomes its own slice with explicit archive, tombstone, or hard-delete
semantics, and it is never folded into Site creation.

Reason: The Architect raised removal as the one product call it could not make.
Later slices key committed simulated history, envelopes, and evidence records to
`site_id`, so delete-then-recreate under the same identity would resurrect
orphaned history under a different Foundation. The cost of deferring is that
demo Sites accumulate and can only be cleared from disk, which is acceptable
while the store is file-backed and the audience is developers. The cost of
shipping removal early is an identity and history question of the same family as
in-place editing, which M1 has deliberately deferred.

Affected scope: `SiteRepository` port surface, Site creation slice scope, Sites
List affordances, user store lifecycle, future archive/tombstone semantics,
feature map open questions, task sequencing.

## 2026-09-13

Decision: The Architect's extended working notes for a feature are local-only
process material. Durable architectural context belongs in `.ai/DECISIONS.md`,
`.ai/ARCHITECTURE.md`, and `.ai/FEATURE_MAP.md`, and the tracked task files must
be sufficient on their own to implement a slice. Tracked documents must not
direct a reader to a `.agent/` file as required reading.

Reason: `.agent/` is gitignored and absent on a fresh clone, so a tracked
pointer into it is a broken dependency and contradicts the existing instruction
to normally ignore local-only files. The balance being struck is between context
bloat and provenance: promoting every line of an Architect handoff into tracked
governance would bloat the documents every session loads, while leaving the
reasoning only in a local file loses the provenance behind decisions that
supersede earlier ones. Recording the decision, its reason, what it supersedes,
and the alternatives rejected is enough provenance; the long-form derivation is
not.

Affected scope: Architect handoff artifacts, `.ai/START_HERE.md` references,
`.ai/ARTIFACT_INDEX.md` artifact states, what the Implementer is required to
read, future Architect and Planner output conventions.
