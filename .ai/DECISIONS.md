# Decisions

## Decision Index For Agent Context

Use this index to find only the decisions relevant to the active task. Keep
newest task-routing state in `.ai/ACTIVE_CONTEXT.md`; keep full decision
rationale in the dated entries below.

| ID | Date | Subject |
| --- | --- | --- |
| `D-2026-09-11-stack` | 2026-09-11 | M1 uses the preferred MVP stack from the product specification. |
| `D-2026-09-11-simulator-gate` | 2026-09-11 | Simulator Lab is gated by `simulator_lab.enabled`. |
| `D-2026-09-11-workflow` | 2026-09-11 | AssetOps uses Architect/Planner, Implementer, Reviewer, and user-review workflow. |
| `D-2026-09-13-site-foundation-persistence` | 2026-09-13 | Persisted Sites, shipped templates, user-created Sites, and a swappable persistence adapter. |
| `D-2026-09-13-site-foundation-resequence` | 2026-09-13 | Site Foundation step 3 is template catalog, create from template, then read-only Site Configuration. |
| `D-2026-09-13-template-and-create-surfaces-gated` | 2026-09-13 | Template browsing and simulated Site creation are Simulator Lab surfaces behind the gate. |
| `D-2026-09-13-canonical-fidelity` | 2026-09-13 | Canonical mockup fidelity is staged after each surface has truthful content. |
| `D-2026-09-13-shared-site-substrate` | 2026-09-13 | Operator and Lab Site pages share one substrate at `frontend/src/sites/`. |
| `D-2026-09-13-provenance-status-vocabulary` | 2026-09-13 | Source mode, lifecycle, configuration origin, evidence readiness, and source health remain separate. |
| `D-2026-09-13-t006-preimplementation` | 2026-09-13 | T006 pre-implementation decisions for runtime gate proof, created Site shape, and non-loosening guard updates. |
| `D-2026-09-17-timezone-validation-timing` | 2026-09-17 | Real IANA timezone membership validation is required before timezone becomes executable behavior. |
| `D-2026-09-17-source-health-backing` | 2026-09-17 | Gateway/source health is backed by source observations, not Site lifecycle or simulator provenance. |
| `D-2026-09-17-site-foundation-fetch-seam` | 2026-09-17 | The Site Foundation frontend/backend fetch seam needs a focused integration test before expansion. |
| `D-2026-09-17-client-demo-readiness` | 2026-09-17 | Client demo readiness begins at the Simulated Evidence Loop; business-outcome demo readiness begins at Evidence-Backed Operational Findings. |
| `D-2026-09-17-foundation-screen-architecture` | 2026-09-17 | The operator Site surface formerly called Site Configuration becomes Foundation, with line-cited Site tabs, filtered Foundation subtabs, route compatibility, and inventory guards. |
| `D-2026-09-20-layout-evidence-standing` | 2026-09-20 | Browser layout evidence is standing closeout evidence for layout-sensitive slices, kept outside the portable architecture runner. |
| `D-2026-09-20-no-merged-task-status-guard` | 2026-09-20 | No guard ties a merged slice's task status to branch state; closeout discipline stays manual until the drift recurs. |
| `D-2026-09-20-breaker-vocabulary` | 2026-09-20 | A breaker is topology and, when instrumented, a reported-about thing; position is evidence, not Foundation configuration. |
| `D-2026-09-20-scenario-definition-model` | 2026-09-20 | ScenarioDefinition is the saved, versioned scenario artifact; events are saved sub-artifacts inside a scenario version. |
| `D-2026-09-20-scenario-definition-storage` | 2026-09-20 | ScenarioDefinitions use composed shipped and writable stores behind a domain port, with one disjoint scenario_id space. |
| `D-2026-09-20-run-scoped-event-injection` | 2026-09-20 | Future event injection is run-scoped intervention history, not authored scenario content. |
| `D-2026-09-20-scenario-detail-affordances` | 2026-09-20 | Scenario detail renders only native controls; Run is disabled with a named prerequisite and downstream controls are absent. |
| `D-2026-09-21-scenario-authoring-semantics` | 2026-09-21 | The T017 checkpoint settles scenario versioning fields, the event taxonomy, and the public/private parameter boundary. |
| `D-2026-09-21-causal-runtime-before-golden-traces` | 2026-09-21 | A minimal executable causal runtime precedes authoritative golden traces; manual traces cannot establish scenario causality. |
| `D-2026-09-21-scenario-execution-contract` | 2026-09-21 | The T018 checkpoint settles execution roles, initialization and cadence ownership, timing and bound semantics, and that an unreached reading is stated rather than resolved. Amended by `D-2026-09-21-scenario-execution-contract-amendment-1`. |
| `D-2026-09-21-scenario-execution-contract-amendment-1` | 2026-09-21 | Amendment 1 to the execution contract: simultaneous causes net rather than order; the contract-version bump policy; run setup stops adjudicating cause-to-observation coupling; a scenario does not author what a device reads; `execution_requirement` is forbidden on a reported observation; a fifth `TRAJECTORY` oracle kind. |
| `D-2026-09-21-run-setup-outcome-vocabulary` | 2026-09-21 | `BLOCKED` is the shipped run-setup outcome, now on three reasons; the Fuel Loss residual splits into two scheduled decisions with different deadlines; `READY` discloses what it does not assert and T021 verifies it against the kernel. Extended 2026-09-22: the refusal line moved to who failed to answer, four location failures block as `INITIAL_VALUE_NOT_RESOLVED`, and the contradiction refuses as `INITIAL_VALUE_ANSWERS_DISAGREE` because the frozen identity can hold no answer and not two. Its one consequence about a Foundation declaring no such property at all is superseded by `D-2026-09-22-foundation-property-absent-blocks`: that case blocks. |
| `D-2026-09-21-projection-versus-composition` | 2026-09-21 | Projecting a document is static validation; composing projections into a value-at-a-time is a kernel, whatever the component is called. |
| `D-2026-09-21-specification-reference-implementation` | 2026-09-21 | A specification's reference implementation is labelled and carries a stated expiry; `reconcile_reported_observations` stops being an authority when a kernel is compared against it, and leaves the repository when its last product-path caller goes. |
| `D-2026-09-21-physical-property-ownership` | 2026-09-21 | Foundation declares what the site is, the model profile how the simulator reasons, the scenario what happens, the publication profile how the reporting installation behaves; two swap tests decide ownership, and a new slice T020A builds the missing carriers. Its template-copy consequence is corrected by `D-2026-09-22-foundation-property-absent-blocks`: a non-re-created MG-001 blocks, it does not refuse. |
| `D-2026-09-22-expiry-follows-the-condition` | 2026-09-22 | A gap-covering artifact names the condition as its expiry, never a slice number; a claim that has become false goes in the slice that falsifies it, and a thing still honest goes when someone decides to remove it. |
| `D-2026-09-22-foundation-value-declaration` | 2026-09-22 | A scenario parameter whose declared owner is Site Foundation has no value position at all. The rule is keyed on the owner, so it reaches `tank-capacity` as well as the coefficient, moves the contract version, and retires `INITIAL_VALUE_ANSWERS_DISAGREE` in T020A. Option C is a named follower. |
| `D-2026-09-22-capacity-bound-source` | 2026-09-22 | A bound's declaration is the document's and its value is the site's. `declared_bounds` reports no upper value for `fuel-tank-volume` after T020A and that is the correct answer; the number lives in the frozen run and the first thing entitled to hold both halves is T021's kernel. |
| `D-2026-09-22-foundation-property-absent-blocks` | 2026-09-22 | A Foundation that declares no such property at all blocks with `INITIAL_VALUE_NOT_RESOLVED`. It is a fifth case of the four, not a refusal, because after T020A the binding names the property and a different profile might name another. |
| `D-2026-09-22-contract-version-scope` | 2026-09-22 | `EXECUTION_CONTRACT_VERSION` moves when a change can alter the outcome for a document that was already valid. A narrowing can; a pure widening off every executable path cannot, so the `TRAJECTORY` oracle kind does not move it. The absolute numbers are unstable and are written relatively. |

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

## 2026-09-13

Decision: `ScreenMockups.png` renders the Simulator Lab developer shell, not the
operator product, and the canonical mockups are read that way from now on.
Consequently the mockups do not place Simulator Lab in operator navigation, and
the T003/T004 position stands unchanged: Simulator Lab is not an operator
navigation item, it is reached from workspace-level chrome, operator navigation
is structurally identical in both gate states, and no T003 or T004 boundary test
may be weakened or removed.

The evidence. v6.9 section 3.9 gives the Simulator Lab its own shell whose
navigation is "Home | Sites | Simulator Lab | Scenarios | Site Templates |
Library | Documentation | Settings". `SimulatorLab1.png` reproduces that list
exactly, and `ScreenMockups.png` reproduces it with Devices, Ingestion and
Events inserted, which v6.9 defines as Simulator Lab run tabs rather than
destinations. v6.9 section 2 fixes operator navigation at ten object classes,
Portfolio, Sites, Assets, Findings, Actions, Incidents, Maintenance, Evidence,
Financials and Reports, and not one of the mockup's rail items beyond Sites
appears in it. The screens diverge the same way: the mockup's Site tabs are
Overview, Configuration, Devices, Gateway, Ingestion, Events, Logs, while v6.9's
canonical Site tabs are Overview, Foundation, Health, Performance, Findings,
Work, Financials, Evidence; the mockup's Sites columns are Name, Type, Location,
Status, Last Data, Actions, while v6.9's are Site, Type, Mode, Assessment, Top
issue, Evidence, Last analysed. v6.9 section 3.1 is headed "Entry points (no new
operator navigation items)" and lists "Workspace utility menu: Open Simulator
Lab", which is what T004 implemented.

This supersedes nothing. It corrects a reading, and it removes the apparent
conflict rather than resolving it in either direction: read correctly, the
mockup agrees with T004.

Reason: The alternative reading, that the mockup is the operator shell and
therefore demands Simulator Lab in operator navigation, would have reversed a
merged and accepted slice whose direction came from an explicit user review at
the T003 checkpoint, on the strength of an illustration that contradicts both
the normative product document and the other mockup. Two images that disagree
with each other about the rail, and an image whose own breadcrumbs read
`Sites > MG-001 > Devices` while its rail shows Devices as a destination, are
illustrative rather than normative. Where they and v6.9 disagree, v6.9 settles
it.

The residual question is not architectural and is recorded as the one open
question in `.ai/FEATURE_MAP.md`: whether the user intends those nine screens as
a single merged shell for M1. That would be a product call the user is entitled
to make and it would supersede this entry. It is not assumed here.

Affected scope: Canonical mockup interpretation, operator navigation, Simulator
Lab shell placement, T003/T004 boundary tests, shell placement of every Site
Foundation surface, UI fidelity targets, feature map open questions.

## 2026-09-13

Decision: Causal Sequencing step 3 is resequenced. The order is now (3a) shipped
Site configuration template catalog, (3b) create a Site from a template, (3c)
read-only Site Configuration presentation. M1 ships zero canonical Sites: the
shipped read-only content is the template catalog, and every Site in the product
is one a user created. First run has a genuinely empty Sites index.

This supersedes the sequencing recorded earlier the same day in
`.ai/FEATURE_MAP.md` Causal Sequencing step 3, which ran (3a) Site repository
port and canonical read path over a shipped canonical Site fixture, (3b) shipped
templates, (3c) create. It also supersedes the slice order in that map's Site
Foundation feature-to-task guidance. It does not disturb the three 2026-09-13
persistence decisions above: the port, the two-store identity rules,
copy-on-instantiate, untrusted-input handling, create-without-edit, and no
removal all stand exactly as recorded.

Reason: The user's correction is right and the earlier ordering was wrong. A
Sites index is a view over Sites somebody configured. Shipping the index first,
populated by a canonical fixture Site, makes the view real before the capability
that fills it, and pushes the milestone's own first clause, "a user can
configure one mini-grid site", to the end of the feature. It also produces a
poor first review surface: a single row that arrived by no product action, from
which the user cannot distinguish a working configuration path from a hardcoded
row.

Where the earlier reasoning was actually wrong, specifically: it argued that the
port needed a real read consumer before it could be trusted, and then assumed
that consumer had to be a shipped Site. The template catalog is also a real read
consumer, and a better one, because it is a complete truthful screen that
requires no Site to exist. Putting a fixture Site on the critical path bought
nothing the template catalog does not buy, and cost the causal order. The one
constraint that made the earlier ordering partly right, that the template
concept must be structural before any write path or the first create copies a
shipped Site and collapses the template/instance distinction, survives untouched
and now orders the sequence on its own.

Alternatives rejected. Keeping a shipped canonical Site so that later steps and
CI have a Site without running the create flow: rejected because it restores
exactly the thing the user objected to, and because the two-store disjointness
seam it was said to protect is testable with a fixture store that is not a
product-visible Site. Shipping list, get and create in one slice so the port
arrives complete: rejected as too large for one review packet; the split is
template catalog, then create, then configuration presentation.

Consequences worth naming. `MG-001` becomes the Site the user creates from the
Hybrid Mini-Grid template rather than a Site that ships, which is also what
`SimulatorLab1.png` already shows in its run header as "Template: Hybrid
Mini-Grid (100 kW)", and what v6.9 section 3.5 setup path A describes as
template, then Foundation, then save, then run. Later steps that need a Site
create one. The two user-review checkpoints move: the first to the create slice,
the second to the configuration presentation slice.

Affected scope: Causal Sequencing step 3, Site Foundation feature-to-task
guidance, candidate vertical slices, the product spine, the shipped Site store,
first-run empty state, user-review checkpoint placement, T005-T008 task files,
and every later step that assumed a Site exists without being created.

## 2026-09-13

Decision: Authoring a simulated Site is a Simulator Lab capability and is gated
by `simulator_lab.enabled`. The Site Templates catalog and the create-a-Site
flow live in the Simulator Lab shell, behind the gate. The Sites index, Site
Details, and Site Foundation/Configuration presentation are operator
capabilities and are never gated. A Site created while the Lab was enabled stays
fully visible when the Lab is disabled, because it is product Site history and
not simulator execution. Operator navigation does not grow at all in step 3.

This supersedes the Architect's own contrary guidance, given earlier on
2026-09-13, that Site and template routes must not be gated on
`simulator_lab.enabled`. Half of that guidance stands and is now stated more
precisely: the Sites index, Site Details, and Site Configuration are never
gated, and wiring them to the simulator flag would make Sites vanish when the
Lab is switched off. The half that was wrong is template browsing and Site
creation.

Reason: v6.9 section 3.1 makes `+ Add site` an entry point whose "Create
simulated site" and "Clone site into scenario" options "open the Simulator Lab
workspace", and section 3.9 lists Site Templates in the Lab shell's navigation
and nowhere in the operator's. The only non-simulator creation path v6.9
describes is "Register live site", which depends on backend Site registration
that v6.9 explicitly defers. So a gate-off build with an empty Sites index and
no way to add one is the correct state rather than a defect.

The deciding argument is direction of risk, not only conformance. Moving a
surface out from behind the gate later is a cheap, reversible change.
Retrofitting a gate around a surface that already shipped ungated is precisely
the hidden-but-reachable failure the gate seam exists to prevent. Where a
Site-authoring surface is ambiguous, it ships gated.

Affected scope: `simulator_lab.enabled` reachability list, Site Templates and
create-flow route placement, operator navigation growth, gate-off acceptance
criteria, T003/T004 boundary tests, Site Foundation task shell placement.

## 2026-09-13

Decision: Canonical mockup fidelity is in scope from the Site Configuration
slice onward, staged per surface, and governed by three rules. First, content
before chrome: a surface adopts canonical layout only after that surface's
content is real, and no numeric value, timestamp, status, or label appears
because the mockup shows it. Second, three treatments rather than two, taken
from v6.9's own usage: a gated or decided-against capability is not rendered at
all; a canonical tab that names a real aspect of an entity but has no content
contract yet is labelled in place; a built capability that is not currently
eligible is disabled with its reason stated. Third, fidelity to the mockup is
not fidelity to its errors.

Applied to the deferred affordances the mockups show: `Edit`,
`Edit Configuration`, `Version History`, `Duplicate Site`, `Delete Site`, and
the site image `Change` control are absent from the rendered output, not
disabled. `Open in Simulator Lab`, `Start Simulation`, and `View Live Data` are
present and disabled with their named prerequisite. The Site tabs
`Configuration`, `Devices`, `Gateway`, `Ingestion`, `Events`, and `Logs` are
labelled in place until their causal step lands.

Reason: The three treatments are not invented here. v6.9 gates the Simulator Lab
by not rendering it, "not merely hidden"; it labels a deferred tab in place as
"Warranty (P1)" with "deferred, no content contract yet"; and it disables Commit
on a Draft run with the note "draft envelopes are not released to ingestion
until Commit". Adopting the document's own vocabulary keeps the product
internally consistent and avoids inventing a fourth pattern.

The absent-versus-disabled line falls where it does because disabled reads as
"soon". `Open in Simulator Lab` is genuinely soon and the feature map can name
the step that makes it true, so disabling it is informative. `Edit` is not soon:
M1 has decided configuration is fixed at creation, and greying the control would
make a promise the product has declined to make. `Version History` is worse than
a promise: no configuration-change model exists, and v6.9's eventual form for
that territory is `Foundation > Changes`, an auditable intervention record with
`Retain / Retune / Revert`, which is a different capability from version
history. Shipping the mockup's label would name a future capability wrongly. The
distinction between an action control and a tab is what makes the middle
treatment safe: a tab set describes the aspects of an entity, so naming an
aspect early is honest chrome, while a greyed button describes an action the
user cannot take and should not expect.

Two mockup errors that fidelity work must correct rather than copy. Canonical
screen 1 puts `Simulated` and `Planned` in one `Status` column, collapsing
provenance into status, which v6.9 forbids three separate times, "Mode is
provenance, not status" and "SIMULATED is neutral provenance, not an
assessment", and which the existing vocabulary-separation seam already forbids;
Mode and lifecycle are separate columns. And the mockup's `Last Data` timestamps
are evidence the product does not have; v6.9's equivalent column is `Last
analysed`, rendered `--` when there is no data in the window, and that rendering
is the target. Note also that v6.9 has no `Planned` site status and no site
lifecycle enum at all, so `lifecycle_status` is this project's extension and its
values are fixed by the M1 Site schema, not by the mockup.

Fidelity staging: shared visual vocabulary first, applied only to surfaces that
already have real content; then template catalog, create flow, Sites index, Site
Details, and Site Configuration in that order; then the configured Single Line
Diagram at causal step 4; then canonical screens 4 through 9 as their steps
land. The fidelity slices carry no user-review checkpoint of their own, because
they add no capability and no product language.

Affected scope: Site Details and Site Configuration affordances, Sites index
columns and status vocabulary, tab sets, empty and unavailable states, the new
mockup-fidelity seam and its CI guard, the read-only configuration UI seam, task
count and task shape for the Site Foundation feature.

## 2026-09-13

Decision: Navigation growth is its own concern with its own rule, not a
by-product of any feature slice. A navigation destination appears only when the
route behind it renders a truthful surface. No placeholder destinations, no
disabled navigation items, no "coming soon" routes. When a Site Foundation slice
needs a new surface, whether that surface earns a navigation entry is answered
by this rule and by shell placement, never by the mockup rail.

Two immediate consequences. Operator navigation does not grow during step 3 at
all, because every new step 3 surface is a gated Simulator Lab surface in the
Lab's own shell. And the current parameterless `Site details` and
`Site configuration` operator navigation items are step-1 route placeholders
from before Site identity existed; once Sites are addressed by `site_id` they
must be removed, because a Site Details link that names no Site is not a
destination. Those surfaces are reached from a Sites row.

Reason: Navigation is a stronger claim than a button. A button says an action
exists; navigation says the product has a place. A rail of ten items where six
are dead teaches an operator a product that does not exist, and it does so on
every screen rather than in one panel. This is the same honesty posture the
project already applies to evidence, applied to information architecture. It is
also why the mockup rail is not a build target: the operator rail's real
long-run shape is v6.9 section 2's ten object classes, and nothing from the
mockup rail should be added to operator navigation on the strength of the mockup
alone.

Affected scope: Operator shell navigation, Simulator Lab shell navigation, route
placeholders from T002, navigation-related acceptance criteria in every later
slice, the mockup-fidelity seam, feature-to-task guidance.

## 2026-09-13

Decision: Simulator Lab exists to unblock product development before a real site
exists. Three consequences are now durable rules.

First, a Site the Lab produces is a normal Site. Same identity space, same
model, same repository, same store, same index, carrying simulated source mode
as provenance. It is not a second class of object, it is not Lab-owned, it lives
in no Lab-owned store, and it is never published or promoted into the product,
because it was a product object from the instant it was created. The gate covers
surfaces and execution, never objects or stores.

Second, where both shells present the same object they present it from one
substrate. The operator Site page and the Lab Site page are one presentation
core with shell-specific additions, not two implementations that happen to
agree. The substrate owns the read model, the view model that turns a record
into display, and the presentation components; neither shell may fork any of the
three. Each shell may only compose and add through named slots the substrate
declares: the Lab adds run and execution context, the operator adds a gated way
into the Lab. The substrate carries no shell, mode, or variant discriminant, and
it is a leaf that imports no shell code, no simulator code, and no feature flag.

Third, the Lab's navigation exists only to serve that purpose. It is a developer
workspace menu, not a second product information architecture, and nothing in it
is evidence that the operator product should have a matching destination.

This amends the reason given in the gating decision recorded earlier today. That
decision stands unchanged -- template browsing and Site creation are Lab
surfaces behind `simulator_lab.enabled`, and the Sites index, Site Details and
Site Configuration are never gated -- but its stated reason led with conformance
to v6.9. It should lead with purpose. The Lab is gated and self-contained
because it is a place to work before a real site exists, and that is also the
limit on what self-contained may mean: self-contained describes the workspace,
never the objects the workspace produces. v6.9's placement of Site Templates and
`Create simulated site` in the Lab is corroboration, not the reason.

Reason: The substrate rule is the expensive one to get wrong. The late failure
is not that the two shells look different; it is that they drift into two Site
models. Different labels for the same field, different unavailable states, a
value derived one way here and another there, and eventually two read models
with a translation layer between them. By then both have users and neither can
be changed alone. The cheap-looking variant of the same failure is a
`variant="lab"` branch inside the shared core: it looks shared, and its branches
drift independently anyway. That is why a discriminant inside the substrate is
banned outright and every difference must be expressible as an addition around
the core. If a difference cannot be, it is not a shell difference and belongs in
the substrate for both.

Dependency direction is what lets this coexist with the existing ban on
operator-to-simulator imports. The substrate is a leaf: both shells import it,
neither imports the other, and it imports neither. So the operator shell renders
a Site without any path to simulator code, and the substrate cannot become a
back door into simulator internals because it declares slots and never imports
what fills them. The one operator-to-Lab crossing, Open in Simulator Lab, reuses
the single gated entry-point module that T004 established rather than adding a
chokepoint or routing through the substrate.

Alternatives rejected. Build the Site page operator-first and extract a shared
core when the Lab needs one: rejected because extraction after two pages exist
is the expensive refactor and the drift has already happened by then; the whole
point of the rule is that it costs nothing before the second consumer and a
great deal after. A `variant` prop on shared components: rejected above. Letting
the Lab own its Sites and publish them to the product: rejected because it
contradicts "a normal Site with a simulator tag" and would invent a promotion
step, a second store, and a second identity moment that nothing needs.

On timing, and against the appearance of inconsistency: refusing a port with no
consumer and requiring a substrate with one consumer are not in tension. A
port's shape is unknown until a caller proves it, so shipping one early is
guesswork. The substrate's shape is already known, because it is the Site read
model the create slice must build regardless, and the user has stated a second
consumer is coming. The only decision being made early is which directory the
files go in, and the structural guards that keep them there.

Affected scope: Frontend module tree, Site read model and view model ownership,
operator and Lab Site pages, extension-slot design, the new shared-substrate
seam and its three checks, `Open in Simulator Lab` treatment under the gate,
Site Foundation feature-to-task guidance and file placement, fidelity staging,
and the reason recorded for the gating decision.

## 2026-09-13

Decision: The product has exactly two provenance concepts, not three, and six
independent provenance-and-status concepts in total. The single reference is the
table under "Provenance And Status Concepts" in `.ai/FEATURE_MAP.md` Feature
Area 1; cite it rather than restating it.

The "simulator tag" the product shows on a Lab-produced Site *is*
`source.mode = SIMULATED`. It is not a third field. No `created_in_lab`,
`is_simulator_site`, or equivalent flag exists or may be added, because such a
field records which shell created a Site, which nothing downstream consumes and
which would fork the identity seam.

Configuration origin (`SHIPPED` / `USER`) and source mode (`LIVE` / `SIMULATED`)
are orthogonal and neither may be derived from, defaulted from, or rendered as a
proxy for the other. Configuration origin describes the document and its store;
source mode describes where evidence comes from. Lifecycle status, integration
readiness, evidence availability, and source health remain separate from both
and from each other, as already recorded.

Nothing about "a normal Site with a simulator tag" changes the two-store model.
The shipped and user-authored configuration stores, their disjoint `site_id`
space, copy-on-instantiate, and template provenance are all untouched.

Reason: The user's phrase invites a natural but wrong reading, that being
Lab-produced is a new property of a Site. It is not; it is the existing Mode
concept, which v6.9 already fixes as "provenance, not status" and which the
project's vocabulary-separation seam already protects. Naming that explicitly
now is cheaper than discovering two fields that always agree.

The specific trap worth recording: in M1 the only creation path is the Lab's, so
every `USER`-origin Site also has `source.mode = SIMULATED`. The two coincide in
every row anyone will see this milestone, which is exactly the condition under
which someone collapses them or derives one from the other. They coincide by
circumstance, not by definition. A shipped demo Site would be `SHIPPED` plus
`SIMULATED`; a Site registered for a real integration would be `USER` plus
`LIVE`. Both are meaningful and neither is reachable in M1.

Affected scope: Site model fields, Sites index columns, Site Details and Site
Configuration provenance presentation, badge vocabulary, strict parser and
validation, the vocabulary-separation seam, and every later slice that reads
provenance.

## 2026-09-13

Decision: Before T006 implementation, the disabled-bundle concern is settled as
a runtime gate seam, not a bundle-content seam. A gate-off build must serve no
Lab route, action, API, create flow, simulator URL backdoor, or operator import
path into Lab internals; it does not need to prove that Lab modules are absent
from the frontend bundle.

Decision: The T006 created Site document is not the template document. The
template contributes only a deep-copied Foundation seed. The create flow
collects `site_id`, display name, location identity fields, and timezone. The
create service defaults origin, source mode, lifecycle status, template
provenance, and any initial Foundation version/validity fields required by the
strict parser. Topology, devices, mappings, control assumptions, evidence,
source health, operational status, SLD runtime fields, and simulator/run fields
do not exist in this slice.

Decision: T006 must update architecture guards deliberately rather than making
the T005 checks pass by accident. Adapter isolation and the storage-technology
ban remain, shipped configuration roots remain read-only, writes are allowed
only through the user-store adapter, the user store root has one owner and is
gitignored, and updated checks keep non-vacuity assertions.

Reason: T006 is the first untrusted-input write boundary. The task is still a
coherent vertical slice, but it needs these decisions recorded before
implementation so the write path is strict, the feature gate stays meaningful,
and the guard changes replace prior strength instead of weakening it.

Affected scope: T006 task planning, `.ai/FEATURE_MAP.md`, Simulator Lab gate
tests, Site record shape, user store adapter, architecture guard updates, and
future Site Details/Site Configuration slices.

## 2026-09-17

Decision: T006's shape-only IANA timezone validation stands for current Site
Foundation storage and display. Real IANA timezone membership validation becomes
mandatory before any scenario, SimulationRun window, replay window, evidence
window, scheduling behavior, or analytics bucketing consumes Site timezone as
executable behavior.

Reason: Timezone is currently identity/configuration metadata. Shape validation
keeps Site records coherent without making correctness depend on host-specific
timezone database availability, especially on Windows. Once timezone affects
execution semantics, a structurally plausible but nonexistent zone can distort
run timing, local-day boundaries, evidence windows, replay, and analytics. At
that point invalid zones must be rejected early and deterministically through an
explicit dependency or bundled timezone database.

Affected scope: Site validation, Scenario and SimulationRun planning, replay
and evidence-window semantics, analytics bucketing, future dependency choices,
and task gating before timezone becomes operational.

## 2026-09-17

Decision: Gateway/source health is a separate operational evidence signal
derived from source/gateway observations, heartbeat or arrival evidence, and
expected cadence. It is not derived from Site lifecycle status, from whether a
Site exists, from whether a Site is simulated, or from simulator/run provenance.
Until backed observations exist, Site Foundation and configuration-only screens
must render source health as unknown, not backed, or not recorded rather than as
healthy, online, offline, or stale.

Reason: Site lifecycle answers whether the configured Site is managed or active.
Gateway/source health answers whether AssetOps has recently heard from the
source that claims to represent the Site. Simulation provenance answers where
the evidence came from. Those truths can diverge: an active Site may have a
stale gateway, a simulated run may emit fresh staged observations without
proving any real source is healthy, and historical observations can exist for a
Site whose lifecycle later changes. Keeping the signal separate preserves an
audit path from health badges to observation metadata.

Affected scope: Configuration-only Site UI, future source/gateway health
derivation, ingestion and heartbeat evidence, vocabulary separation, Simulator
Lab provenance, Site lifecycle presentation, and operator monitoring screens.

## 2026-09-17

Decision: The Site Foundation frontend/backend fetch seam now requires a
focused integration test binding the real frontend API clients to
representative backend responses before the shared contract is materially
expanded. The test should cover the Site Foundation clients across the Site
list/detail read path, create success, validation refusal, empty state, and
not-found or store/error envelopes where practical. It does not need to be a
broad browser end-to-end test.

Reason: T006 through T008 created multiple user-visible surfaces over the same
transport contract. Backend tests and isolated frontend rendering tests do not
prove that the real client code understands the backend payload shape, status
codes, and error envelopes. Because the seam is shared, a small mismatch can
silently affect several screens. A focused integration test gives more
confidence than adding page-local tests after visual fidelity accumulates on
top of the same unverified assumption.

Affected scope: T010/T011 planning, frontend API clients, backend response
contracts, Site Foundation regression tests, review packets, and any future
slice that changes the shared Site Foundation frontend/backend contract.

## 2026-09-17

Decision: Client demo readiness begins at `Demo Ready v1: Simulated Evidence
Loop`, after a simulated Site can produce staged gateway/source envelopes,
release them through ingestion, show accepted/rejected records, populate
operator evidence views from accepted evidence only, and replay committed
accepted history with provenance. Business-outcome demo readiness begins at
`Demo Ready v2: Evidence-Backed Operational Findings`, after source/gateway
health and at least one bounded operational finding are derived from accepted
evidence.

Earlier milestones are valid product walkthroughs but not client-ready AssetOps
demos: M0 Site Foundation Fidelity, M1A Topology/Devices/Signals/SLD, M1B
Scenario Catalog/Run Setup, and M1C Prototype Walkthrough Recorded Runtime.

Reason: Before the simulated evidence loop exists, the product can show
configuration, visual fidelity, scenario setup, and simulator behavior, but not
the core AssetOps promise: evidence-backed operational inspection.
Business-outcome claims require an additional conclusion chain over accepted
evidence, with confidence, claim boundaries, and provenance.

Affected scope: Roadmap planning, task sequencing, demo language, Simulator
Lab, Source Envelope, release/ingestion, evidence views, Replay, source health,
operational findings, mini-grid demo readiness, and cold-chain follow-on
planning.

## 2026-09-17

Decision: The operator Site surface previously called `Site Configuration` is
the v6.9 `Foundation` tab named at lines 464, 615 and 2117. User-visible route text, breadcrumb, page heading,
tab label, and Site Details link text become `Foundation`. The canonical route
becomes `/sites/:siteId/foundation`; `/sites/:siteId/configuration` remains only
as a compatibility redirect that preserves `siteId` and is not surfaced,
tabbed, or counted as a navigation destination. Test names, guard messages and
guard-script comments use Foundation unless deliberately asserting the legacy
redirect or the parameterless `/site-configuration` ban. Internal component and
symbol names under `frontend/src/sites/**` may lag for the rename slice if
renaming them would be mechanical churn across the shared substrate; no
user-visible string or route constant may lag.

The operator Site tab set is v6.9's `Overview | Foundation | Health |
Performance | Findings | Work | Financials | Evidence` from lines 464 and 615.
`Overview` and `Foundation` are destination tabs because their identified
routes render truthful current surfaces. The remaining tabs are labelled in
place with no link, button, route, or disabled placeholder until their content
contracts exist. The `ScreenMockups.png` screen 2 tabs `Configuration`, `Devices`, `Gateway`,
`Ingestion`, `Events`, and `Logs` are not the operator Site tab vocabulary for
M1.

The Foundation subtab row uses v6.9 line 2117 as the source:
`Definition | Topology | Controls | Changes | Readiness`. `Definition`,
`Topology`, and `Controls` render with current M1 limits; `Readiness` is
labelled in place until evidence readiness has a source contract. `Changes` is
not rendered until a reviewed configuration-change capability exists, because
v6.9 lines 2149 and 2225-2228 make it a real intervention/change-effect
capability rather than a placeholder or `ScreenMockups.png` screen 3's `Version History`.

This supersedes the forward-looking parts of the 2026-09-13 canonical-fidelity
decision that named the operator Site tabs as `Configuration`, `Devices`,
`Gateway`, `Ingestion`, `Events`, and `Logs`, and the forward-looking parts of
the 2026-09-13 navigation decision that used `Site Configuration` as the
settled surface name. It does not rewrite those dated records. Their
historical facts still stand: canonical fidelity is staged only after content
exists, absent/labelled/disabled treatments remain distinct, parameterless
routes are not destinations, and navigation growth remains governed by
truthful routes.

Sequencing: insert a dedicated Foundation naming and operator Site tab
inventory slice after T011 and before the current T012. T009 remains
chrome-only; T010 and T011 continue in order with wording changes. The inserted
slice carries the user-visible rename, `/foundation` route, `/configuration`
redirect, operator Site tab inventory guard, route-compatibility tests, and
guard-script updates. T012 then dresses Site Details against the settled tab
row, T013 dresses Foundation against the settled name and filtered subtab row,
and T014-T016 remain coherent only after their wording and structure are
updated to render into Foundation.

Guard replacement is replace-never-loosen. The frozen operator-navigation count
may remain during Site Foundation because the operator rail still does not
grow. When a rail or tab set changes, the replacement guard is a single
inventory definition consumed by rendering and tests: every rendered item must
be in the inventory, every destination item must have a real route, labelled
items must not be links/buttons/routes, gated Lab rail items must be absent
when the gate is off, and no unexpected item may render. This is stronger than
a count freeze because it checks identity, route truthfulness, and absence of
extra items rather than only a number.

Reason: v6.9 lines 464, 615 and 2117 are the operator Site vocabulary authority
where they disagree with `ScreenMockups.png` screens 2 and 3, and the accepted T008 checkpoint already settled that this surface
is the read-only Foundation/configuration presentation rather than an editable
configuration workflow. Carrying the old screen name into the canonical tab row
would leave users with two names for one surface, make the `ScreenMockups.png`
screen 2 run-tab vocabulary look like operator navigation, and weaken the audit trail around
why `Changes` and `Version History` are absent. A compatibility redirect keeps
existing addresses from breaking while preserving navigation truthfulness: the
product has one Foundation destination, not two configuration surfaces.

Affected scope: Foundation route and redirect, Site Details link, breadcrumb,
heading and tab labels, operator Site tab row, Foundation subtab row, planned
T009-T016 task wording and sequencing, navigation truthfulness guard,
architecture guard messages, frontend tests, shared Site substrate naming
cleanup, and future Planner rewrites of uncompleted task files.

## 2026-09-20

Decision: `tools/layout-evidence.mjs` becomes standing closeout evidence for
layout-sensitive slices, owned by the Implementer and checked by the Reviewer
from the review packet. It stays out of `tools/check-architecture.ps1`.

A slice is layout-sensitive when it changes shell layout, dense tables,
intrinsic-width drawings, SVG geometry, tab or subtab treatment, or viewport
behaviour. Such a slice names layout evidence in its checks, and its packet
carries the exact command, the base URL when non-default, and the final result
line. A packet that omits it, or records a skipped run as a pass, is a review
finding.

A missing precondition is not a pass. When Chrome, the backend or the dev
server is unavailable, the closeout records `layout evidence: not run` with the
blocking precondition, and the Reviewer treats the affected layout claim as
unverified.

Every new measured claim about overflow, visibility or rendered content must
include at least one measurement proving its set is non-empty, generalising the
640px measurement that exposed T014's dense-table claim passing on an empty
set.

Reason: the tool has found defects no suite on this project can see - T011B's
original shell overflow defect, T014's empty-set dense-table claim, and T016's
connection routed through a component, SVG text leaving its box, and a label
colliding with the name it marks. That is too much signal to leave ad hoc. But
it needs a browser, the backend and a dev server, while the architecture runner
protects seams that must hold anywhere and fails any unwired module. Putting it
in that runner would either make the portable runner non-portable or introduce
skips, and a skipped protection that reports success is the exact failure shape
this project keeps finding.

Affected scope: `.ai/WORKFLOW.md` closeout and review packet, the Implementer
and Reviewer standing briefs, task checks for layout-sensitive slices, and
review packets. No change to `tools/check-architecture.ps1` or its manifest.

## 2026-09-20

Decision: no guard is added to tie a merged slice's task status to its branch
state. Closeout discipline stays manual: before a merge, the Review Outcome is
recorded and the task status is set to complete or explicitly left open.

Reason: branch state is the wrong authority. Branches are deleted, rebased and
renamed, and a fast-forward merge leaves none at all, so a guard built on
`git branch --merged main` would miss normal workflows and overfit the one
failure already seen. `tasks/` is also empty, so a guard written now would
assert over no members - the seventh instance of the family this project keeps
shipping rather than a defence against it. The process-creep rule wants a
second occurrence or an explicit ask, and the user asked for a recommendation
rather than for the guard.

If the drift recurs, the shape to build reads task files rather than branches:
each active task carries a stable id and status, completed work moves to
`tasks/completed/` with `Status: complete` and a Review Outcome before closeout,
and a checked-in deliberately-incomplete sample task proves the guard can fail.
Without that fail-case anchor it would join the dead patterns, the unreachable
caps and the type contract no runtime test could falsify.

Affected scope: `.ai/WORKFLOW.md` closeout, the Implementer and Reviewer
standing briefs. No new tool, no change to `tools/check-agent-workflow.ps1`.

## 2026-09-20

Decision: a breaker is both a topology element and, when the site has
instrumentation for it, something a device may report about - but never both in
one record. Its position is evidence, not Foundation configuration. M1 carries
nothing beyond the declared control assumptions T014 already carries: identity,
name, optional component reference, provenance, and a statement in words.

This keeps two product claims apart:

- "This site is wired with a controllable or protective element between these
  topology nodes" - configuration and topology.
- "This breaker was open, closed, tripped, automatic or manual at this time" -
  evidence.

So `OPEN`, `CLOSED`, `TRIPPED`, `AUTO` and `MANUAL` are not Foundation schema
vocabulary, and `BREAKER` is not a Foundation `DEVICE_TYPE`. The eventual model
separates four things: a topology declaration for where the breaker is; device
and signal mappings for what can report about it; evidence records for what was
observed and when; and declared control policy or assumption for what operation
is intended, in words for M1.

T014's `frozenset` scan in
`backend/tests/test_foundation_content_parsing.py` is kept, not narrowed and not
retired, with its rationale rewritten to this decision. Retiring it would let a
later Foundation change smuggle position vocabulary into configuration before
the evidence model exists. Narrowing it to position words alone would admit
`BREAKER` as a device type and so answer half the question early. It narrows
only when a reviewed slice adds the explicit topology/evidence separation and
tests that position cannot be stored as configuration.

Reason: v6.9 gives the Simulator Lab a truthful runtime breaker state, with
loads and sources connected to the AC bus through named breakers and a legend
carrying breaker open/closed, because the simulator owns physical truth. Where
it gives Foundation control policy it defines no breaker-position schema, no
AssetOps control-state vocabulary, and no rule that configured policy equals
observed state. That silence is the finding: this seam is ours to decide, and
the causal chain the product already commits to - physical/control state
transition, device observation, gateway, source envelopes, AssetOps evidence -
puts position on the evidence side of it.

Carrying nothing more in M1 is the positive answer rather than a deferral. M1
has no evidence object, controller record, runtime overlay or breaker component
model that could truthfully hold a position. Adding the vocabulary now would
unlock no UI-verifiable value; it would teach the product to state an operating
condition without the evidence path that makes such a statement legitimate. A
screen could show a breaker open because a YAML field said so, which collapses
the simulator-truth and AssetOps-evidence boundary and makes Foundation look
like a live operations model.

Left open deliberately, for the first slice that renders or stores a breaker
state, because that slice will have the evidence contract in front of it:
whether canonical topology names breakers as components, connection equipment,
connection attributes or a distinct inline element; the accepted-evidence
vocabulary for positions and control modes; whether `tripped` is a position, an
event, a protection outcome or several of those in different records; and the
symbol set for breaker drawings. Eventually the SLD draws a breaker as an inline
topology element and may overlay an evidence-backed position on it, with
simulator runtime truth and accepted evidence staying separate overlays as
T015's slots already keep them.

Affected scope: `.ai/FEATURE_MAP.md` section 2 semantics, the `frozenset` scan's
rationale and failure message, and any future slice touching breakers, control
policy, or the Foundation control vocabulary. No schema field, model, route, or
rendered surface changes now; T014's `ControlAssumption`, T015's typed empty
slots and T016's presentation all stand as shipped.

## 2026-09-20

Decision: `ScenarioDefinition` is the saved, versioned scenario artifact for
M1B. It has scenario identity, version identity, display metadata, target-site
requirement, public timeline, public parameters, and private expectations in
separate parsed fields. `ScenarioTemplate`, if introduced later, is a reusable
recipe in a separate identity space; it is not executable by itself and does not
live-update existing definitions.

`ScenarioEvent`, authored `Intervention`, and `EvidenceCondition` are ordered
authored items inside a `ScenarioDefinition` version. They are saved
sub-artifacts because they persist inside the definition document, but they are
not top-level stored entities in M1B. Their address is
`(scenario_id, scenario_version, event_id)`. `PrivateExpectation` is
test-oracle metadata only: it is not pipeline input, public authoring data,
product evidence, operator UI, or product provenance.

The exact scenario versioning fields stay provisional until the T017 user
review checkpoint. The invariants are settled now: identity and version are
distinct; a version referenced by a run is immutable; timeline identities are
stable within a version; a future run freezes the concrete scenario version it
used and never follows latest.

Reason: A Fuel Loss Event timeline row has no useful lifecycle without the
scenario's target requirement, interval defaults, seed, public/private boundary,
evidence visibility model, and version identity. Making events a repository
root now would introduce reuse, deletion, lookup, and compatibility semantics
that M1B cannot verify. Keeping templates separate follows the Site
Template/Site distinction and prevents recipe changes from rewriting saved
definitions.

Affected scope: Scenario domain model, scenario parser, Scenario catalog and
detail payloads, future run setup, private expectation isolation, T017
checkpoint content, and T018/T019 task sequencing.

## 2026-09-20

Decision: `ScenarioDefinition` storage uses strict canonical YAML behind a
`ScenarioDefinitionRepository`-style domain port. The shipped Fuel Loss Event is
a read-only tracked definition at `config/scenarios/fuel-loss-event.yaml`, and
writable user or project definitions live under gitignored `var/scenarios/`.
Both roots compose into one repository with one globally unique `scenario_id`
space. Duplicate identities, including case variants, are configuration
conflicts within a store or across stores; there is no overlay and no
precedence.

The port speaks domain records and scenario-domain errors only: not found,
identity conflict, configuration invalid, and store unavailable. YAML, paths,
file handles, parser exceptions, duplicate-file checks, filesystem errors, and
store availability translation stay inside adapters and the composition root.

Reason: T017 has no scenario creation flow, so a fresh checkout needs a tracked
read-only scenario definition for the catalog to show. That is parallel to
shipped configured instances, not to reusable templates. The writable store
still exists because later authoring needs a place to persist user definitions,
but identity must remain disjoint from the beginning or run history will not
have a stable scenario anchor.

Affected scope: Scenario storage layout, scenario repository port, composition
root, strict parser and adapter tests, first-run catalog behavior, future
scenario authoring, and future migration away from file-backed storage.

## 2026-09-20

Decision: Future event injection is modeled as run-scoped
`InjectedRunEvent` / intervention-history records under `SimulationRun`
identity, not as authored `ScenarioEvent` rows and not as top-level scenario
artifacts. Runtime injections are addressed by a run-scoped family such as
`(run_id, injected_event_id)` or `(run_id, intervention_sequence)`. They are
never written back into the selected scenario version, never create an implicit
scenario version, and never become inherited by another run.

Reason: Authored scenario events exist before a run and define reusable
scenario content. Injected events are accepted during one run as deterministic
runtime input. Committed replay needs to save them, but under the run's ordered
intervention history so two runs can start from the same scenario version and
diverge only by run-scoped inputs. Promotion of a useful injection sequence into
authored scenario content is a future authoring capability with explicit UI and
review, not an automatic runtime side effect.

Affected scope: Scenario timeline model, SimulationRun runtime model,
intervention logs, deterministic replay, quick actions, event-log presentation,
and T020+ task planning. M1B names the seam but implements no injection models,
storage, APIs, or controls.

## 2026-09-20

Decision: On the T017 scenario detail screen, a disabled control appears only
when the action is native to the viewed `ScenarioDefinition` and the missing
prerequisite is the next named causal capability. `Run` / `Create Draft Run` is
rendered disabled with visible reason text naming the missing run setup / Draft
`SimulationRun` prerequisite. `Open target Site` is the only product bridge: it
is enabled only when the declared target Site resolves, otherwise absent or
disabled with an accessible reason.

`Commit`, `Open in AssetOps`, runtime controls, gateway output, ingestion,
Replay, Findings, and product analytics are absent from the scenario detail
screen because they belong to `SimulationRun`, ingestion, Replay, or operator
evidence/product surfaces rather than to `ScenarioDefinition`.

Reason: This is a precise application of
`D-2026-09-13-canonical-fidelity`, not an amendment to it. Disabled means "this
action belongs to the object you are viewing, but the current record or
milestone lacks the named prerequisite to perform it." Controls from another
root object or downstream lifecycle teach the wrong object model when shown as
disabled placeholders.

Affected scope: Scenario detail screen actions, accessibility reason text,
mockup-fidelity tests, run setup sequencing, and future control placement on
SimulationRun, ingestion, Replay, and operator evidence surfaces.

## 2026-09-21

Decision: the T017 user-review checkpoint settles the three scenario authoring
semantics M1B was blocked on. All three were accepted as proposed.

A scenario version carries `scenario_id`, `scenario_version`,
`version_valid_from` and `supersedes`.

The event taxonomy is three timeline entry kinds - `EVENT`, `INTERVENTION`,
`EVIDENCE_CONDITION` - and seven categories: `LOAD`, `WEATHER`, `EQUIPMENT`,
`DATA_QUALITY`, `LOSS_OR_FRAUD`, `INTERVENTION`, `MAINTENANCE`. Breaker
position and control mode are excluded by construction, and the vocabulary ban
now reaches identifier-valued schema positions so they cannot arrive as a
`parameter_id` either.

Public authoring parameters may inform future run setup and runtime behaviour.
Private expectations - `DETECTION`, `MAGNITUDE`, `TIMING`, `NO_FALSE_POSITIVE`
- are test-oracle metadata only. The boundary is a parsed-field separation with
separate payload builders, not a presentation choice, and private expectations
never reach product evidence, source envelopes, operator UI, exports or
provenance.

Reason: unlike the M1A checkpoint, each question carried a proposal on screen,
marked provisional, stating what accepting adopts and what redirecting would
mean. The user's verdict was "looks good", so accepting the screen was a
decision rather than ratification of a menu. M1A's breaker question was
presented with candidates the project had considered and not chosen and no
proposal, settled nothing, and had to go to an Architect afterwards; T017 was
planned specifically not to repeat that.

The values are settled. The on-screen provisional marking and the `provisional`
wording on `SCENARIO_VERSION_FIELDS`, `TIMELINE_ENTRY_KINDS` and
`EVENT_CATEGORIES` are not yet removed. Removing them, and the review regions
with them, is a visible product change and belongs to a slice that says so -
the same treatment T016's cold-room marker was given.

Affected scope: `.ai/FEATURE_MAP.md` section 3, T018 and T019 planning, the
scenario domain vocabularies, the scenario detail screen's review regions, and
any future slice that authors, versions, or runs a scenario.

## 2026-09-21

Decision: a minimal executable deterministic causal runtime kernel must precede
any state trace treated as authoritative simulator output. This supersedes
`D-2026-09-11`'s first-execution-mode decision that a recorded-run player would
act as the initial state producer and later be replaced by the real runtime.
The stable clock/state/event, device, gateway, ingestion, and UI seams from that
decision remain required.

`ScenarioDefinition` authors causes and conditions in time, not their resulting
state trajectory. Site Foundation, frozen run inputs, explicit initialization
inputs, and versioned simulator rules initialize private world state. The
runtime applies due events exactly once through an initialization/step contract
and computes subsequent state. For the Fuel Loss Event, the first kernel must
at least resolve the configured tank, account for declared initial fuel,
generator consumption, removal, and delivery inputs, enforce declared bounds,
and make changes to event quantity or timing produce corresponding changes in
the state trajectory.

A state trace may be retained only as a golden trace or playback fixture: it is
generated reproducibly by a named simulator version from a frozen deterministic
identity and used for regression, UI, clock, binding, or downstream contract
proof. A manually authored trace can be schema-valid and internally consistent
while still being causally circular, so it cannot certify simulation. Schema
validation, invariant/consistency validation, and causal correctness are
separate proof obligations. Causal proof requires executable transition rules
plus independent examples, boundary cases, and metamorphic checks such as
removing, retiming, or resizing an event and observing only the corresponding
consequence change.

Runtime provenance binds each result or golden trace to the exact Site and
Foundation version, scenario version and resolved public parameters, interval,
timestep, seed, simulator version, explicit initialization inputs, mappings,
and ordered intervention history. A mismatch refuses playback; it never falls
back to a trace produced for different inputs.

Reason: a fixture written to agree with a scenario proves only agreement
between two authored artifacts. Without an independently executable causal
rule it cannot show that the scenario influenced world state. A narrow real
kernel costs less than carrying that false claim through device, gateway, and
evidence work, and lets later physical realism deepen the producer without
redesigning downstream contracts.

Affected scope: M1B run-setup semantics, T018/T019 planning, M1C task sequence,
runtime initialization and step contracts, event-time semantics, trace
provenance, simulator tests, Simulator Lab claims, and golden-trace use.

## 2026-09-21

Decision: `D-2026-09-21-scenario-execution-contract`. The T018 checkpoint
settles what an authored scenario value means to an executor. The user
reviewed the Fuel Loss Event screen and accepted all four proposals.

**Execution roles: accepted as proposed.** Every public parameter and every
timeline entry carries one machine-readable execution role - `CAUSAL_INPUT`,
`FORCING_INPUT`, `REPORTED_OBSERVATION`, `NON_EXECUTABLE_CONDITION` - on an
axis orthogonal to the T017 entry kinds and categories, which are unchanged.
Only a causal input may reach initialization or a private-state transition,
and that is enforced at two independent layers rather than asserted. A
forcing input names the state it forces and is binding on a later kernel, but
may not declare a starting value: an exogenous state's value at every instant
comes from its profile, including the first, so an initial value beside it
would be a second answer to one question. A reported observation carries no
ownership and no state effect, so there is no field it could arrive in.

**Initialization and cadence ownership: accepted as proposed.** Every initial
world value has exactly one owner - Site Foundation, the scenario, a run
override, or a versioned model rule - and two owners for one value is refused
when the definition is read. The scenario owns no cadence. Foundation declares
that a signal can report and declares its unit, and declares no rate; nothing
derives a cadence from a device name, from displayed text, or from the spacing
between rows. A cadence arrives when a versioned observation profile declares
one. The prohibition is closed at the unit vocabulary rather than per
position: a duration has no authoring unit, so there is no position it can
occupy. A hand-recorded value is a real source with its own identity and no
device identity.

**Timing and bounds: accepted as proposed.** An entry is an instant, a window
with a declared length, or the whole interval, validated as three distinct
shapes; a rate may only be declared over a window. The run interval and every
step are half-open, so a boundary entry is applied by the step that begins
there and by no other, making "applied exactly once" a property of the time
model. Every bound case either refuses the definition, fails the run, or
produces a bounded change recorded with the quantity it refused. There is
deliberately no option meaning clamp quietly or drop the remainder.

**An unreached reading is stated, not resolved: accepted as proposed.** The
Fuel Loss declared causes reach 254 L where the sensor reports 155 L and the
operator records 150 L. Both readings are reported observations from a named
source, so neither prescribes tank state and the contract is coherent; what
the contract must also do is say out loud that its declared causes do not
reach either, with quantity and sign. The residual stands at -99 L and -104 L,
`NOT_ACCOUNTED_FOR`. The three honest ways out - model the missing cause,
declare a reporting behaviour that explains the difference, or accept the
readings and change the causes - remain open and are the user's to choose in a
later slice. Until one is chosen, later run setup treats an unreached reading
as a reason to block rather than as a rounding matter.

Reason: run setup cannot freeze honest inputs while a timeline row can
ambiguously prescribe both a cause and its expected result. Classifying the
values resolves that without editing any authored number, which would have
settled a product question by arithmetic rather than by review.

Affected scope: T019 Draft run setup and its `BLOCKED` computation, T021's
kernel and its initialization/step contract, T022's device observations, the
scenario parser vocabularies and payloads, and any later slice that resolves
the Fuel Loss residual.

Amended by `D-2026-09-21-scenario-execution-contract-amendment-1`, which
withdraws the closing clause about run setup blocking on an unreached reading.

## 2026-09-21

Decision: `D-2026-09-21-scenario-execution-contract-amendment-1`. Amendment 1
to `D-2026-09-21-scenario-execution-contract`. Six changes, accepted by the
user on 2026-09-21 after reading
`Docs/simulator-scenario-authoring-and-runtime.md`, which carries the full
reasoning and is committed alongside this entry. The original decision keeps
its ID and its unamended text; this entry is what it means where the two
differ. The bracketed letters are the labels that document uses.

**(c) Simultaneous causes are a group with a net effect, not a sequence.** The
original decision fixed half-open dispatch and exactly-once application but
left within-instant ordering unspecified, so two conforming kernels could
legitimately disagree at that instant. Transitions on one state completing at
the same offset now form a group with a net effect, and bounds are evaluated on
the group's net rather than between its members. Order-dependence is decided
exactly: apply all increases first to test the upper bound, all decreases first
to test the lower. If neither extreme breaches, no ordering breaches, the net
is unambiguous, and the contract answers. If one extreme breaches and the other
does not, the group is genuinely order-dependent and the contract abstains with
its own reason, saying the scenario must separate the offsets if it wants order
to decide. Order is expressed as time, never as position in a document.

A first draft of this rule declared authored `sequence` order and was reversed
inside T019 before independent review. Authored order is not physics,
serialising simultaneous causes abstains on a level the state is never in, and
declaring it would have obliged T021's kernel to serialise sub-steps inside one
instant, removing the metamorphic invariant
`D-2026-09-21-causal-runtime-before-golden-traces` asks for. Already
implemented on `task/T019-draft-run-setup` as a `DISPATCH_RULES` entry.

**(d) `EXECUTION_CONTRACT_VERSION` moves when the space of conforming
behaviours changes, including when it narrows, and never for wording.** Pinning
a previously unspecified semantic narrows the space and moves the number; a
prose edit does not. The number identifies the space, not the text. (c) moved
it from 1 to 2 because it pinned an instant the first version left open, and
rewriting (c)'s content inside the same slice did not move it again, because
both drafts narrow the same space and no implementation ever conformed to the
first draft. The policy matters because
`D-2026-09-21-causal-runtime-before-golden-traces` makes a provenance mismatch
refuse playback, so a version that moved for prose would force regeneration of
valid golden traces. Already implemented on `task/T019-draft-run-setup`.

**(e) Run setup does not adjudicate cause-to-observation coupling.** This
withdraws the original decision's closing clause, "later run setup treats an
unreached reading as a reason to block rather than as a rounding matter."
Deciding whether declared causes reach a declared reading requires composing
those causes into a value at a time, which is a transition rule, and whatever
owns a transition rule is a kernel. Run setup has no kernel, so the verdict was
never run setup's to reach. `OBSERVATION_NOT_ACCOUNTED_FOR` therefore leaves
the blocking-reason vocabulary and the observation reasons leave the run-setup
service.

The rest of the original fourth proposal stands. Both readings are still
reported observations from a named source, neither prescribes tank state, and
the residual is still real. What changes is where it is stated. Reconciliation
found a genuine defect in the document, and it was wrong only about where it
stood to look: a disagreement between an author's expectation and computed
behaviour is a test failure, not a property of a run that has not happened.
Lands in T019 before merge.

**(f) A scenario does not author what a device reads.** The original decision
left three ways out of the residual open. This takes the third and narrows it.
The authored 155 L at offset 1590 and 150 L at offset 1800 are removed. What a
run reports is generated by the observation transform from private state, at
the cadence the frozen publication profile declares, perturbed only by declared
reporting-path forcings. The 155 L value was a hand-simulation of exactly the
sample the transform will generate at 1590, and it was wrong by 99 L.

The `REPORTED_OBSERVATION` role survives unchanged and becomes more necessary,
not less: it is precisely what stops an authored reading reaching a transition.
Its meaning sharpens from "a value the contract checks the causes against" to
"an expectation about what a run should produce, which no executable path may
read." The entry at 1590 survives as an evidence condition asserting that a
reading arrives there and is materially below what dispatch accounts for; the
operator's inspection at 1800 keeps the act and loses the number. Lands in
T022, and the replacement numbers are derived during T021 from what the kernel
computes rather than chosen before it.

**(g) `execution_requirement` is forbidden on a `REPORTED_OBSERVATION`.**
Closed structurally at the parser, the way the original decision closed
duration units: there is no position the field can occupy, rather than a rule
someone has to remember. With (e) in place, `REQUIRED` on a value no executor
reads is either vacuous or a category error, and the meaning it was carrying,
"this run must produce such a reading", already has a home in the private
expectations under `DETECTION` and `TIMING`. This narrows the space of
conforming behaviours, so `EXECUTION_CONTRACT_VERSION` moves by one under (d).
(This read "2 to 3" as written, and two later narrowings now land before it;
the count is in `.ai/FEATURE_MAP.md` under *The execution-contract version
ledger*.)
It is free now and will not be once a golden trace exists. The user placed it
in its own slice, **T021A**, on 2026-09-22: T022 is the slice that first
produces a golden trace, so burying the version move inside it would make that
slice's internal ordering load-bearing and would close the free window if T022
were ever split. It sits after T021 because the kernel never reads
`execution_requirement` on a reported observation.

**(i) A fifth oracle kind, `TRAJECTORY`.** The four accepted oracle kinds are
all about analysis outcomes. None is about world trajectory, so the author's
most immediate and most confident expectation, what the tank does, had nowhere
falsifiable to go and ended up as a `REPORTED_OBSERVATION` value, which is a
load-bearing position. A `TRAJECTORY` oracle asserts a private-state value at
an offset, is checked by the kernel in tests, and is never published and never
read by any executable path.

It is not a manually authored trace under another name. A trace as input is
read and reported as the state, so being wrong causes agreement; an oracle is
compared against an independently computed value, so being wrong causes a
failure. Two guards keep it on the right side of that line. It must be sparse
and purposeful, one or two points the scenario is about, because a dense set is
a trace in the oracle position and fits the kernel to the author's arithmetic.
And it must be stated as weak proof: if the author and the kernel perform the
same arithmetic and agree, what is proven is that two implementations agree,
which catches unit, dispatch and half-open errors and does not prove the
physics. It is a regression guard, not a correctness proof. Lands in T021,
which is what can check it. Without it, (f) deletes the author's expectation
instead of relocating it.

Reason: five of the six changes withdraw or narrow a claim the contract was
making without the machinery to back it, and the sixth gives the withdrawn
expectation a position where being wrong causes a failure. The rule underneath
all of them, and the reason they are one amendment rather than six: an
expectation is legitimate when it occupies a position where being wrong causes
a failure, and circular when it occupies a position where being wrong causes
agreement.

Affected scope: `backend/assetops_backend/scenarios/execution.py` dispatch
rules and the contract-version constant, `runs/service.py` blocking reasons,
`runs/models.py` blocking vocabulary, the parser rule for
`execution_requirement`, `EXPECTATION_KINDS`,
`config/scenarios/fuel-loss-event.yaml`, the scenario detail screen's
reconciliation panel, T019's narrowing before merge, T021's oracle check and
document correction, and T022's observation transform.

## 2026-09-21

Decision: `D-2026-09-21-run-setup-outcome-vocabulary`. The T019 checkpoint
settles what a run-setup outcome asserts and when the Fuel Loss residual is
due. Accepted by the user on 2026-09-21. The first two parts were taken at the
checkpoint itself and had until now been recorded only in a local handoff note;
the third comes from the Architect read that followed.

**(a) `BLOCKED` is the shipped run-setup outcome.** Setting up a run for the
shipped Fuel Loss Event against the shipped `minimal-fuel-tank` model profile
produces a persisted Draft that cannot execute. That is accepted as correct
behaviour rather than treated as a defect to design around: a structurally
valid, fully frozen request whose executable inputs the selected profile cannot
consume is inspectable history, not a refusal. Under amendment 1's (e) the
count drops from five reasons to three, all `STATE_NOT_SUPPORTED`, for
`site-load-demand`, `plane-of-array-irradiance` and
`fuel-level-reporting-availability`. The outcome does not change; only the
reason count does. `READY` remains unreachable for the shipped document in this
build and is proved against fixtures. T019 does not widen the shipped model
profile and does not resolve the residual.

**(b) The residual is a scheduled decision, and it splits.** The checkpoint
treated it as one decision with two halves, both due before T021's task file.
It is now two decisions with different deadlines, because (e) moved one of them
out of run setup.

- The `REQUIRED` forcing states the first kernel does not model stay due
  **before T021's task file is written**, because they decide what the first
  kernel must model. Either the scenario lowers their requirement level, or the
  model profile grows to model them, or the authority for the reporting-path
  one moves to the publication profile. If `dispatched-output` is promoted to a
  forcing input, it joins this list. Deadline unchanged.
- The two unreached readings stop being a run-setup blocker under (e) and
  become a scenario-authoring question, due **before T022** and answered
  **during T021** from what the kernel computes. The right removal magnitude
  depends on what the kernel computes and on what the product can recover from
  published evidence, so deciding the number first and then building the kernel
  would fit the kernel to an authored expectation.

**(l) `READY` discloses what it does not assert, and T021 verifies it.**
`ModelProfile.supported_states` is a hand-written tuple that nothing checks
against a kernel, because no kernel exists. `READY` therefore means every
required executable input names a state that appears in that tuple with a
matching role, and every frozen value resolved. It does not mean the model can
execute them. If the shipped profile claims a state the eventual kernel does
not implement, the Draft is `READY` anyway, and being wrong causes agreement.

The remedy is disclosure now and structural closure later, not a rename. T020
states on the run record and on screen what `READY` does not assert. T021 adds
a conformance test asserting that the shipped profile's supported set equals
the set of states the kernel actually implements, derived from the kernel
rather than hand-maintained, which is the treatment this project already gives
the cadence and duration-unit prohibitions. The word becomes correct when that
test lands, and renaming it would ripple through the API payload, the
frontend, the tests and T020's screens to fix a word that is about to become
true. The disclosure becomes false at the same moment, so **T021 retires it in
the slice that lands the conformance test**, under
`D-2026-09-22-expiry-follows-the-condition`; this entry originally left the
retirement to an unnamed later slice and nothing owned it.

This is deliberately not treated the way `RUNNING` was. `RUNNING` could never
be reached in this build, so it was pure fiction and deletion was the only
honest move. `READY` is reached and does assert something true, just less than
its name suggests. Absence and overstatement warrant different remedies.

**Extended 2026-09-22 at the T019 user review: the refusal line moved.** The
user accepted the reviewer's principle and chose to align T019 to T020A rather
than the reverse. The discriminator is **who failed to answer**:

> The scenario's **declared owner** has no answer -> **refuse**, because no
> profile helps.
> The **selected profile** cannot answer -> **block**, because a different
> profile fixes it and the person gets a persisted Draft to inspect.

**Four cases moved from refusal to blocking.** A profile declaring no
`foundation_binding`; a binding matching nothing; a binding matching more than
one thing; and a binding whose unit is not the scenario's. What decides them:
a Foundation's answer is only locatable *through* the selected profile's
binding, so failing to locate it is a joint fact about the pair, and the
profile is the half a person can change on the setup form.

**A Foundation that declares no such property at all is not one of the four.**
There the declared owner itself has no answer, no binding reaches a value that
is not there, and no profile on the form would help, so it refuses. That is
the case that governs T020A's template-copy consequence, and the two must not
be collapsed: *the profile's binding could not locate an answer* blocks, *the
declared owner has no answer to locate* refuses.

> **Superseded 2026-09-22 by `D-2026-09-22-foundation-property-absent-blocks`:
> that case blocks.** This paragraph was the one part of this extension the
> code did not implement, and the discriminator above does not support it.
> `_resolve_foundation_value` reaches a refusal down one path only,
> `rating.value != declared`; every not-found blocks. For the refusal to have
> held, run setup would have had to establish that the declared owner has no
> answer without going through the profile's binding, and this entry says a
> Foundation's answer is locatable only through that binding - which after
> T020A names the property as well as the component type, so a different
> profile naming a different property may find something the Foundation does
> declare. Nothing else in this extension changes: the four blocking cases,
> the absent value on `FrozenInitializationInput` and the three invariants
> stand, and so does the structural argument for the contradiction refusal,
> whose case `D-2026-09-22-foundation-value-declaration` removes the ability
> to author at all.

**`FrozenInitializationInput` gained an absent case.** `value` and
`canonical_value` are nullable and absent together; the unit is not, because
the scenario declares it whether or not anything answers. The invariants live
on the record rather than in the service, because the service cannot produce a
violation and a hand-edited document can: a run is `READY` exactly when it
carries no blocking reason, **a `READY` run may not carry an absent value**,
and **every unresolved state must be named by a blocking reason's subject** -
the same state, not merely some reason somewhere on the same run.

**The new blocking kind is `INITIAL_VALUE_NOT_RESOLVED`.** It is named for the
state the value is left in rather than for the cause, so one name carries all
four cases, and **T020A reuses it for its `MODEL_RULE` carrier case** rather
than introducing a second kind for the same fact.

**The contradiction stays a refusal, for a structural reason worth carrying
into the record.** Foundation and scenario both answer and disagree. Every
blocking case leaves the value with **no** answer, which the frozen identity
can represent as absent; a contradiction leaves it with **two**, which the
identity has no shape for at all. A blocked Draft would have to freeze one of
the two numbers, and choosing one is the thing refusing exists to prevent.
This is not a judgement about which failure is easier to fix - the earlier
version of that argument, that a profile finding another matching component
would be shopping for a value, falls to a site declaring a second matching
component whose rating happens to equal the scenario's, and is kept only as
the intuition.

**So the contradiction is its own refusal kind,**
**`INITIAL_VALUE_ANSWERS_DISAGREE`,** split out of
`INITIALIZATION_INPUT_MISSING`, which now covers only a declared owner that did
not answer. Sharing one kind made it wrong about the case it mostly covered and
left it one word from the blocking `INITIAL_VALUE_NOT_RESOLVED` with nothing in
either name saying which side of the line it was on. The new name is the mirror of the blocking side - a run can
carry "no answer" and cannot carry "answers disagree" - so the vocabulary
carries the structural fact instead of a comment.

Reason: a persisted `BLOCKED` Draft is the honest product of a run setup that
can freeze everything and execute nothing, and it is more useful than a refusal
because it can be inspected. The residual split follows from where each half
can actually be answered. And an execution status is the one place in this
build that makes a claim about executability, so what it does not claim has to
be said in the same place.

Affected scope: T019's blocking-reason set and its fixtures, T020's run-detail
disclosure and Runs inventory language, T021's task file scope and its
`supported_states` conformance test, T022's ability to execute the shipped
scenario, `runs/profiles.py`, and the shipped Fuel Loss document. The 2026-09-22
extension adds `runs/refusals.py`, `runs/models.py`'s blocking vocabulary and
`FrozenInitializationInput`, `runs/service.py`'s freeze and blocking split,
T020A's model-rule carrier and its consequence prose, and the naming rule in
`.ai/ARCHITECTURE.md`.

## 2026-09-21

Decision: `D-2026-09-21-projection-versus-composition`. Projecting a document
is static validation. Composing projections into a value-at-a-time is a kernel.
A component that owns a transition rule is a kernel regardless of what it is
called, how narrow it is, or whether it emits a trajectory.

This is the general form of
`D-2026-09-21-causal-runtime-before-golden-traces` with one word changed. That
decision says a kernel precedes any authoritative trace; this one says a kernel
precedes any verdict that depends on composing causes. It is recorded as a
durable rule in `.ai/ARCHITECTURE.md` under Causal Runtime Authority.

Reason: the rule is what distinguishes the parts of T018's execution contract
that are sound from the part amendment 1 withdraws. `declared_bounds` reports
what a document declares and evolves nothing, so it is a projection and it
stays. The bound walk inside `reconcile_reported_observations` applies bounds to
a running value, which is a transition rule, so it was a kernel living in the
validation layer under another name. Without a stated rule that distinction has
to be rediscovered every time a validator is asked one more question, and three
review rounds on reconciliation is what rediscovering it costs.

The rule also names a live instance that predates it and is not yet fixed.
`IMPLICIT_LOWER_BOUND_DIMENSIONS` in `scenarios/execution.py` gives every
volume state a lower bound of zero whether or not the document declares one.
The asserted fact is true, but "volume is non-negative" is a model rule, not a
projection of the document, and the validation layer is injecting it. Where it
belongs is settled by `D-2026-09-21-physical-property-ownership`; when it moves
is not yet scheduled.

Affected scope: `.ai/ARCHITECTURE.md`, the scenario execution/validation layer,
run setup's blocking computation, T021's kernel boundary, and any future
component asked to decide something about a document by composing its
declarations.

## 2026-09-21

Decision: `D-2026-09-21-specification-reference-implementation`. A
specification's reference implementation belongs in the test suite, explicitly
labelled as a reference implementation and carrying a stated expiry. It does
not belong in the product path.

`reconcile_reported_observations` is the instance. Amendment 1's (e) removes
the feature it became. It does not remove the arithmetic: that moves out of the
product path rather than out of the repository, where it exercises the
execution contract against the shipped document until a kernel exists.
`declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` have exactly one
non-test caller today, which is reconciliation, so they move with it.

**Its expiry is a condition, not a slice number.** Two distinct events, and an
earlier draft of this entry collapsed them into "the expiry is T021", which the
sequence cannot deliver. It **stops being an authority** when the kernel lands:
T021 runs the two against the shipped document, compares them, and the kernel
is what survives any disagreement. It **leaves the repository** when its last
remaining caller goes, which is a different event on a different clock. See
`D-2026-09-22-expiry-follows-the-condition`.

**The removal happens in two steps, and the second is gated on an open
question.** The function has two product-path uses, not one. T019's blocking
reason is the first and it goes now. The second is the
`observation_reconciliation` payload built at
`backend/assetops_backend/simulator_lab_api.py:435` and rendered as a panel at
`frontend/src/shell/ScenarioFrame.tsx:767`, which is T018 work already merged
to `main`. The function cannot leave the repository while that caller exists,
so T019 removes the blocking use and labels the function as a reference
implementation, and removal follows the last remaining caller.

**When that caller goes is Open Question 5 in
`Docs/simulator-scenario-authoring-and-runtime.md`, it is still open, and this
decision does not settle it.** Removing a visible panel from merged work is a
product change belonging to a slice that says so, and the Architect read's
recommendation — that it goes with (f) in T022, because that is when the
authored readings disappear and the panel has nothing left to reconcile — is a
recommendation, not part of what the user accepted. Until then the panel is
honest: it describes a real property of a document that does still contain two
authored readings, so it is removed when someone decides to remove it rather
than because it has become false. No slice before that decision may treat the
removal as in scope, and T021 in particular performs the comparison and not the
removal.

Reason: `EXECUTION_CONTRACT_VERSION` versions a set of rules, and a
specification with zero implementations is under-tested. The standard remedy is
a reference implementation, and that is what reconciliation accidentally
became. The defect was never that it existed; it was that it shipped as product
behaviour, as a run-setup blocking reason and a user-facing panel. Three review
rounds on it, a simultaneity rule reversed after its first attempt, and four
still-unpinned kernel semantics are not four unrelated incidents. They are one
specification discovering it was underspecified by trying to implement itself,
and the cheap version of that discovery is a labelled spike in the test suite.

The generalisation, which is why this has its own ID: where a contract in this
project needs exercising before its real implementation exists, the exercise is
a test-suite artifact with a named expiry and a named successor, never a
product surface. A product surface acquires users, screens and acceptance
criteria, and then the throwaway cannot be thrown away.

Affected scope: `backend/assetops_backend/scenarios/execution.py`, the
`observation_reconciliation` API payload and the scenario-detail panel that
renders it, T019's narrowing before merge, T021's comparison against the
kernel, and any future contract that ships ahead of its implementation.

## 2026-09-21

Decision: `D-2026-09-21-physical-property-ownership`. Four owners are in play
for any value a simulated run needs, and two swap tests decide which one owns a
given value.

> Foundation declares what the site **is**. The model profile declares how the
> simulator **reasons** about things of that kind. The scenario declares what
> **happens** during one interval. The publication profile declares how the
> reporting installation **behaves**.
>
> Swap the asset for another of the same type and the value changes:
> **Foundation**. Swap the scenario and it changes: **scenario**. Neither, but a
> better simulator would change it: **model profile**. Neither, ever: a
> universal constant, and it belongs in code.

Fuel consumption looked ambiguous until the tests separated two things wearing
one name. *This* generator burns 14 L/h at its dispatch point changes when the
genset is swapped and not when the scenario is, so it is Foundation.
*Consumption is proportional to runtime* changes under neither swap and would
change under a better simulator, so it is a model rule. A coefficient and the
law that consumes it are different objects with different owners. The shipped
Fuel Loss document puts the coefficient in the scenario, which fails the first
test decisively: run the same scenario against a different generator and 14 L/h
would follow the story rather than the machine, which would mean the story had
replaced the asset.

**The vocabulary of owners is complete; the plumbing that carries their values
is not.** Three holes, and they must move together or not at all.
`SiteComponent` and `TemplateComponent` carry one optional scalar `rating` per
component, so Foundation cannot express a second physical property at all.
`FoundationBinding` can address only that scalar by `component_type` and
`rating_unit`, so even if Foundation grew a property no binding could reach it.
`SupportedState` carries no field a model-rule value could live in, so a
scenario may declare `owner: MODEL_RULE`, run setup will correctly name
`MODEL_PROFILE` as the answerer, and there is nowhere for the answer to come
from. That is the T019 review's L9 finding.

**A third thing was missed, and it is the subject of a decision due before
T020A's task file.** The three holes below are carriers for a *value*. None of
them declares the *need*: initialization inputs are enumerated from scenario
parameters, and this entry has the coefficient leaving the scenario. See
`Docs/simulator-scenario-authoring-and-runtime.md`, *What declares the need,
once the scenario stops declaring it*.

**A new slice, T020A, closes them, after T020 and before T021.** It is the one
change in this sequence that is an insertion rather than a narrowing: you
cannot narrow your way into a field that is not there. Nothing moves relative
to anything else and nothing in front of it is blocked. Its minimum set is the
generator's specific fuel consumption as a named property with a unit, and a
`SupportedState` carrier for model-rule values. The fuel tank's minimum usable
level is the honest home for the floor `IMPLICIT_LOWER_BOUND_DIMENSIONS`
currently invents, but it does not block T021 and can follow. Efficiency
curves, minimum load, ramp rate, tank geometry, sensor placement, battery
chemistry and PV tilt are all absent from Foundation and none of them blocks
T021, because the first kernel models none of the things they affect. The
minimum set is not a wish list.

**Templates instantiate by copy, so MG-001 must be re-created.** Adding the
consumption property to `config/site-templates/hybrid-mini-grid-100kw.yaml`
will not give it to MG-001, which was created by copy and lives in
`var/sites/mg-001.yaml`; `.ai/ARCHITECTURE.md` is explicit that a later
template change never alters an already-created instance. The demo site must be
re-created from the updated template, or the property hand-added to the
instance. Both are cheap, because it is a development fixture, but neither is
automatic, and a slice that adds the field without doing this produces a site
whose runs never resolve the coefficient.

> **Corrected 2026-09-22 by `D-2026-09-22-foundation-property-absent-blocks`:
> those runs block.** This sentence said they are refused. The code blocks,
> and this entry was written the day before the user moved the refusal line,
> so the claim was re-asserted in the 2026-09-22 extension to
> `D-2026-09-21-run-setup-outcome-vocabulary` rather than re-derived against
> the new discriminator. The obligation to re-create MG-001 is unchanged; what
> changes is the warning. Without it the slice's own UI-verifiable outcome
> never appears, which is a weaker consequence than a refusal and a sufficient
> one. Nothing else in this entry is affected.

The four failures that block are the ones where the profile's binding cannot
locate an answer that exists. See
`D-2026-09-21-run-setup-outcome-vocabulary`.

Reason: the coefficient does not merely belong somewhere tidier. The kernel
needs it at T021 to move the tank at all, and a first kernel whose physics
arrive from the scenario teaches every kernel after it to do the same. The
separation this whole sequence exists to defend would be violated at the exact
moment it first becomes testable. An earlier Architect read placed this with
the product slices T034-T038, as something only the product needs in order to
form an expectation; that was wrong by one milestone and is corrected here.

The seam that holds whatever else is decided later: the consumption coefficient
the product uses to form an expectation comes from Foundation configuration,
never from the scenario's private rate. A product reading the number the
simulator used would compute the Finding from the cause and get the right
answer for the wrong reason.

Affected scope: `backend/assetops_backend/sites/models.py` `SiteComponent` and
`TemplateComponent`, the shipped site template and the strict parser's
per-component-type property vocabulary, `runs/profiles.py` `FoundationBinding`
and `SupportedState`, run setup's frozen-inputs resolution and its blocking
reasons, `config/scenarios/fuel-loss-event.yaml`, `var/sites/mg-001.yaml`,
Site Configuration's Key Parameters panel, the M1C task sequence, and T021's
initialization.

## 2026-09-22

Decision: `D-2026-09-22-expiry-follows-the-condition`. A thing that exists only
because a condition holds names **the condition** as its expiry, never a slice
number. Two artifacts in the M1C sequence exist for exactly that reason, they
were each given a slice number, and in both cases the number was wrong.

**The rule.** When something is created to cover a gap — a reference
implementation standing in for a missing kernel, a disclosure standing in for a
missing verifier — the thing that ends it is the condition closing, not a
calendar position in a plan. A slice number is a guess about when the condition
will close, and a guess written into a record is read later as a commitment.
State the condition; let the slice that ends it be whichever slice ends it.

**And what happens then depends on whether the thing has become false.** This
is the part that separates the two instances and it is the useful half of the
rule:

- A claim that has become **false** goes in the same slice that falsifies it.
  Leaving it is not caution, it is shipping a false statement, and no
  "visible product change belongs to a slice that says so" argument applies to
  a sentence that is no longer true.
- A thing that is still **honest** but no longer needed goes when someone
  decides to remove it. That is the case the existing precedent covers — T016's
  cold-room marker, T017's provisional markings — and it is a product decision
  with its own slice.

**Instance one: the `READY` disclosure.**
`D-2026-09-21-run-setup-outcome-vocabulary` has T020 disclose that `READY` does
not assert the model can execute its inputs, and T021 close the gap with a
conformance test deriving `supported_states` from the kernel. The condition the
disclosure names is *nothing verifies the supported set against a kernel*. The
conformance test ends that condition, so the disclosure becomes false in the
slice that lands it, and **T021 retires it**. It is not a later slice's to pick
up, and until now no slice owned it at all: T020's task file said the slice
landing the conformance test would retire it and T021's said retirement
belonged to a slice that says it is doing that, which between them left it
homeless. T021 says it is doing it. `BLOCKED` never carried an equivalent claim
and nothing about it changes.

**Instance two: the reconciliation reference implementation.**
`D-2026-09-21-specification-reference-implementation` said its expiry was T021.
It cannot be. Two events, on two clocks. It stops being an **authority** when
the kernel lands and the two are compared, which is T021. It leaves the
**repository** when its last remaining product-path caller goes, and that
caller is the `observation_reconciliation` panel, whose removal is Open
Question 5 and is undecided. The reference implementation is still honest in
the meantime: it describes a real property of a document that does still
contain two authored readings. So it waits for a decision rather than for a
slice, and T021 compares without removing.

Reason: both artifacts were recorded with a slice number because the slice was
the nearest visible landmark, and in both cases the landmark was not the thing
that actually ends them. The cost is not symmetric, which is why the rule
carries the false-versus-honest distinction rather than just "name the
condition": a disclosure left past its condition is a false statement on a
screen, and a reference implementation removed before its callers is a broken
build. Erring the same way on both would be wrong in one of them.

Affected scope: `D-2026-09-21-run-setup-outcome-vocabulary`,
`D-2026-09-21-specification-reference-implementation`, T020's disclosure and
its stated expiry, T021's conformance test and its comparison against the
reference implementation, Open Question 5, `.ai/ARCHITECTURE.md` under
Presentation Honesty, and any future artifact created to cover a gap.

## 2026-09-22

Decision: `D-2026-09-22-contract-version-scope`. Adding the `TRAJECTORY`
oracle kind in T021 does **not** move `EXECUTION_CONTRACT_VERSION`. The move
that T021A carries for (g) stands, and this entry says why the two are
different rather than leaving the next reader to re-derive it. Two readers
raised the question independently within a day, which is the signal that the
policy in (d) is answerable but not yet answered in writing.

**The question.** (d) says the number moves when the space of conforming
behaviours changes, including when it narrows, and never for wording. (g)
moved it for a change that alters no executor behaviour at all:
`execution_requirement` on a `REPORTED_OBSERVATION` is read by nothing, which
is the whole argument for removing it. Adding `TRAJECTORY` to
`EXPECTATION_KINDS` also alters no executor behaviour, because no executable
path reads any oracle. If document shape alone was enough to move the number
for (g), the same reasoning reaches `TRAJECTORY`, and T021 moves it too.

**Following (g) would bump on everything, so the test has to be sharper.**
`scenarios/parsing.py` validates both vocabularies strictly. Under a strict
parser every vocabulary change alters what an executor does with *some*
document - refuse becomes run, or run becomes refuse - so "does executor
behaviour change on some document" is satisfied by every change of either
kind and separates nothing. It cannot be the test.

**The axis that does separate them is direction, measured against the
documents that already exist.**

- (g) **narrows**: a document that was valid is now refused. A run could
  already have been frozen against such a document, and after the move that
  document no longer parses, so the artifact cannot be re-derived. That is
  exactly the situation
  `D-2026-09-21-causal-runtime-before-golden-traces` makes a provenance
  mismatch refuse playback for, and it is what the number exists to signal.
- `TRAJECTORY` **widens**: every document valid before is valid now and means
  the same thing, and every artifact frozen before regenerates identically.
  Nothing that exists is affected. Only documents that could not previously
  have been written are, and no artifact was ever frozen against one.

**So the policy, stated the way it is meant to be applied: the number moves
when the change can alter the outcome for a document that was already valid.**
A narrowing can. A pure widening cannot. "Including when it narrows" in (d)
was written to catch the case a reader would otherwise forget, not to make
widening a move; this entry says so rather than leaving it to be read either
way.

**One carve-out, kept deliberately.** A widening whose new construct sits on
an executable path can change how an existing construct is interpreted beside
it, and that reaches documents that already exist. This entry does not cover
that case. `TRAJECTORY` is not it: no executable path reads any oracle, under
`D-2026-09-21-scenario-authoring-semantics`, and
`D-2026-09-21-scenario-execution-contract-amendment-1`'s (i) keeps it that
way by construction.

**Why the forward direction is not the number's job here.** A scenario
document declares no contract version; the constant lives in code and is
stamped onto a frozen run. Parser and constant ship together, so "a version-2
executor meets a version-3 document" is not a state this product can be in.
The only comparison the number ever serves is an older frozen run replayed
against a newer build, which is the backward direction, and a widening is
invisible in it.

**This is distinguishing (g), not overruling it.** (g)'s move is correct and
stays. What changes is that the reason for it is now recorded as its
direction rather than as "the document shape changed", so the next vocabulary
addition does not inherit a move it has not earned.

**What each slice leaves the number at, and why the literals should go.**
T021 leaves it at its current value. T021A moves it by one. The absolute
numbers should not be written as literals anywhere, for two reasons already
in the record and neither of them hypothetical:

- Pinning the four unpinned kernel semantics is a narrowing and moves the
  number. That declaration is due before T021's task file, so if it lands
  before T021A, T021A's move is not `2` to `3`.
- The constant's own docstring carries an unreleased-version doctrine: a
  narrowing that never leaves the branch it was made on does not spend a
  number, because nothing ever conformed to the version it would have
  replaced. Two amendments have already been absorbed that way.

`tasks/T021A-reported-observation-requirement-closure.md` hard-codes "2 to 3"
and T022's guidance says "already under version 3". Both should say the move
and the ordering rather than the values. That is the Planner's edit and it is
unblocked by this entry.

**The count itself is stated once**, in `.ai/FEATURE_MAP.md` under *The
execution-contract version ledger*, because it is a property of the sequence
and moves when the sequence does. Added 2026-09-22 once
`D-2026-09-22-foundation-value-declaration` put a third narrowing in flight.

Reason: the policy in (d) is sound and was stated against the case in front
of it. Applied literally to a widening it spends a version number to buy
nothing, which is precisely the cost (d) names when it explains why wording
must not move the number - a version that moves for a change that invalidates
nothing forces regeneration of golden traces that were never invalid. The
refinement keeps (d)'s purpose rather than its sentence.

Affected scope: `backend/assetops_backend/scenarios/execution.py`'s
`EXECUTION_CONTRACT_VERSION` and the policy comment beside it, which states
(d) correctly and is incomplete rather than wrong; T021's `TRAJECTORY` oracle;
T021A's version move and the literals in its task file; T022's statement about
which version it edits under; the slice that declares the four unpinned kernel
semantics; and the carrier decision due before T020A, whose option B is a
narrowing and would move the number if it is chosen.

## 2026-09-22

Decision: `D-2026-09-22-foundation-value-declaration`. **A scenario parameter
whose declared owner is Site Foundation has no value position at all.** It
declares the need - the state, the unit, that Foundation answers - and states
no number. Option B of the three worked up in
`Docs/simulator-scenario-authoring-and-runtime.md`, *What declares the need,
once the scenario stops declaring it*, accepted by the user on 2026-09-22.

Closed at the structure, the way
`D-2026-09-21-scenario-execution-contract-amendment-1`'s (g) closes
`execution_requirement` and T018 closed duration units: there is no position
the number can occupy, rather than a rule someone has to remember not to
break.

**Why not the other two.** Option A kept the parameter and its stated value as
a requirement Foundation is checked against, which is the `tank-capacity`
pattern already shipped. It costs least and it preserves exactly the seam (k)
exists to remove: run the same scenario against a different generator and
14 L/h still follows the story, now as a requirement that fails the run. A
scenario that cannot run against a 12 L/h genset has a machine's physical
property in it. Option C moved the need to the model profile, which is where
it conceptually belongs, and spends two protected-seam changes in one slice;
it is a follower, below.

**What this reaches, and it is more than the coefficient.** The rule is keyed
on the **owner**, because the owner is the only thing the scenario document
carries that distinguishes these parameters: the binding that addresses a
Foundation property lives in the model profile, and the scenario parser sees
no profile at all. So the rule reaches every `owner: SITE_FOUNDATION`
parameter. The shipped document has exactly one besides the coefficient -
`tank-capacity`, which states 500 L for `fuel-tank-capacity` - and **T020A
edits it too**.

That is not a widening chosen for tidiness. Exempting one parameter needs a
field invented for the exemption, which is a rule with an exception, and this
project has paid for that shape twice already - the bound guessed from a
shared prefix, and the unit case that was left a refusal while the cases
either side of it moved. It is also the better outcome: `tank-capacity` has
option A's defect today, so the seam repair lands complete rather than half.

**It moves `EXECUTION_CONTRACT_VERSION`.** Under
`D-2026-09-22-contract-version-scope` this is a narrowing that reaches a
document which already exists: the shipped Fuel Loss document as it stands is
refused by the new parser. The sequence-wide count is in `.ai/FEATURE_MAP.md`
under *The execution-contract version ledger*, which is the one place it is
stated.

**And it retires `INITIAL_VALUE_ANSWERS_DISAGREE`, in T020A rather than
later.** That refusal kind has exactly one producer, `rating.value !=
declared` in `_resolve_foundation_value`, and after this decision no document
can state a `declared` for a Foundation-owned value. Nothing can produce it.
Two ways out were identified and the first is rejected: keeping a
Foundation-owned parameter able to state a cross-check re-introduces the
number in the scenario that this decision exists to remove. So the kind is
**retired in the slice that removes its last producer**, under
`D-2026-09-22-expiry-follows-the-condition`. A refusal kind nothing can
produce is the `RUNNING` case one layer down - a vocabulary claiming a failure
mode that cannot occur - and for pure absence deletion is the honest move.

Two consequences of that worth carrying. With the contradiction gone and
`D-2026-09-22-foundation-property-absent-blocks` settling the other side,
**every failure of a Foundation-owned value now blocks and none refuses**; a
reader meeting that should not take it for an oversight. And the naming rule
in `.ai/ARCHITECTURE.md` still holds with one fewer pair to keep legible:
`INITIAL_VALUE_NOT_RESOLVED` carries the whole Foundation side, and
`INITIALIZATION_INPUT_MISSING` keeps its own producer, a `RUN_OVERRIDE` the
request did not supply.

**What does not change.** T021 reads the coefficient out of the frozen
identity exactly as it would have. The three carriers (k) names are unchanged
and still move together. MG-001 must still be re-created from the updated
template.

**Follower, with its trigger: option C.** The model profile declaring the need
is where the need belongs - *consumption is proportional to runtime* is the
model rule, and the law is the thing that knows it needs a coefficient. It was
not taken because it changes the shape of the frozen deterministic identity,
a protected seam, in the same slice that changes Foundation's schema, and
because it puts frozen rows behind no scenario parameter. **Trigger: the first
model rule that needs a Foundation value without a scenario asking for it.**
Until then the scenario declares the need and this decision is how.

Reason: the coefficient does not merely need somewhere to live, it needs
somewhere the story cannot reach. A value position that an author may fill is
a value position an author will fill, and the seam `D-2026-09-21-physical-
property-ownership` defends is exactly the one that fails quietly - the
document stays valid, the run still executes, and the physics follow the
story to whichever machine the scenario is pointed at next.

Affected scope: `backend/assetops_backend/scenarios/parsing.py` and the
`InitializationInput` shape, `scenarios/execution.py`'s
`initialization_inputs()` float filter and `EXECUTION_CONTRACT_VERSION`,
`runs/service.py` `_resolve_foundation_value`'s `declared` argument and the
retirement of `INITIAL_VALUE_ANSWERS_DISAGREE` from `runs/refusals.py`,
`config/scenarios/fuel-loss-event.yaml` for both `generator-fuel-rate` and
`tank-capacity`, T020A's scope and its task file, and the version ledger.

It also reaches a second float filter this entry did not name, in
`declared_bounds`, and that consequence is settled separately by
`D-2026-09-22-capacity-bound-source`: the `fuel-tank-volume` upper bound stops
being something the document can state. The constraint that falls out and
belongs to T020A: **the `bounds` declaration must survive the value's
removal.** A bound's `state_key` and `bound_kind` say which world state caps
which, which is a relationship between two states and not a property of a
machine, so it stays in the document when the number goes. A parser that
rejected `bounds` on a parameter stating no value would take the relationship
out with the number and leave the kernel nothing saying what caps what.

And `.ai/ARCHITECTURE.md` under Refusal And Blocking Vocabularies, which the
slice retiring the kind has to touch: the durable naming rule there uses
`INITIAL_VALUE_NOT_RESOLVED` against `INITIAL_VALUE_ANSWERS_DISAGREE` as its
worked example of *within one subject, the shape must carry it*. The rule is
general and survives; its illustration stops existing, and a rule illustrated
by a vocabulary member nobody can find reads as a rule that was not followed.
Either re-illustrate it from the pair that remains or say the example is
historical.

## 2026-09-22

Decision: `D-2026-09-22-foundation-property-absent-blocks`. **A Foundation
that declares no such property at all blocks**, with
`INITIAL_VALUE_NOT_RESOLVED`. It is a fifth case alongside the four, not a
refusal. Accepted by the user on 2026-09-22. This corrects six statements in
the record and supersedes the contrary paragraph in the 2026-09-22 extension
to `D-2026-09-21-run-setup-outcome-vocabulary`.

**Why.** The discriminator the user chose at the T019 review asks *would a
different model profile fix this?* After T020A the `FoundationBinding` names
the component type, **the property** and the unit, so the property name is as
much the profile's aim as the component type is. A different profile naming a
different property may well find something this Foundation does declare. That
is a joint fact about the pair, the profile is the half a person can change on
the setup form, and under the discriminator it blocks.

For the refusal to have held, run setup would have had to establish that the
declared owner has no answer **without** going through the profile's binding,
and the same extension that asserted the refusal also says a Foundation's
answer is locatable only through that binding. The two could not both be true.

**Where the wrong claim came from, because the shape of the mistake is worth
keeping.** It was written in `D-2026-09-21-physical-property-ownership` on
2026-09-21, one day before the refusal line moved. When the line moved it was
re-asserted in the extension rather than re-derived against the new
discriminator, and five further documents and one task file copied it. A
statement carried through a change that should have overturned it reads,
afterwards, exactly like a statement that survived review.

**What survives untouched.** The discriminator itself. The other four blocking
cases. The absent case on `FrozenInitializationInput` and its three
invariants. And the structural argument for why a contradiction could not be
blocked - absence and contradiction are different shapes, and only one of them
is something a frozen identity can hold. That argument is still correct;
`D-2026-09-22-foundation-value-declaration` simply removes the only way to
author two answers, so the case it described can no longer arise.

**MG-001 still has to be re-created.** What changes is the warning, not the
obligation: a slice that adds the property to the template without re-creating
the instance produces Drafts that **block** on the missing coefficient, so the
slice's own UI-verifiable outcome - the Key Parameters row, and the
frozen-inputs row resolving from *site foundation* - never appears. A blocked
Draft naming the missing property is also the more useful failure, because it
is inspectable, where a refusal leaves nothing behind to look at.

Reason: a persisted Draft the person can read is worth more than an error, and
the discriminator already said so. The only thing holding the refusal up was a
sentence written before the rule it was supposed to follow.

Affected scope: the 2026-09-22 extension to
`D-2026-09-21-run-setup-outcome-vocabulary`,
`D-2026-09-21-physical-property-ownership`, `.ai/FEATURE_MAP.md`'s M1C
sequencing revision, `.ai/PLANNING_HANDOFF_T019_T022.md` T020A,
`.ai/ACTIVE_CONTEXT.md`, `Docs/simulator-scenario-authoring-and-runtime.md`,
`tasks/T020A-foundation-physical-properties.md` which is the Planner's, and
T020A's blocking-reason coverage.

## 2026-09-22

Decision: `D-2026-09-22-capacity-bound-source`. **A bound's declaration is the
document's; a bound's value is the site's.** After
`D-2026-09-22-foundation-value-declaration`, `declared_bounds` reports no
upper value for `fuel-tank-volume`, and that is the correct answer rather than
a hole to be plugged.

**What was found.** `declared_bounds` skips any parameter whose value is not a
float. After option B, `tank-capacity` states no number, the loop skips it, and
the `fuel-tank-volume` bound becomes `(0.0, None)` with no error and no
refusal. `backend/tests/test_scenario_execution_contract.py` asserts
`(0.0, 500.0)` and goes red.

**Why nothing sources the value back into the document.** A projection of a
document cannot report a number the document does not carry, and after option B
the document genuinely does not know how big the tank is - that is the whole
of what option B moved. Sourcing the bound from the resolved Foundation value
would make `declared_bounds` a function of document **and** Site. That does not
make it a kernel, because it composes nothing over time, but it stops it being
a projection of the document, and the scenario domain deliberately does not
resolve a target Site: T017 split the parser from the service over exactly that.
Sourcing it from the model profile's binding is worse, because the binding is
the profile's and the scenario domain has no business reading a profile at all.
The component entitled to hold a document and a resolved Site together is run
setup, which freezes; and the component entitled to walk a bound against a
running value is the kernel. Putting the walk in run setup is
`reconcile_reported_observations` again under a different name.

**And the number does not go anywhere.** `tank-capacity` is
`owner: SITE_FOUNDATION` with `initializes: true`, so run setup already
resolves it through the profile's binding and freezes it as
`FrozenInitializationInput` for `fuel-tank-capacity`. The capacity moves from
the document to the frozen run, which is where a machine's physical property
belongs and is the same relocation option B performs for the coefficient.
T021's kernel reads it there.

**The consumer was already scheduled to leave.**
`D-2026-09-21-specification-reference-implementation` records that
`declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` have exactly one
non-test caller, reconciliation, "so they move with it". Verified: the only
non-test caller of `declared_bounds` is `reconcile_reported_observations`. A
mechanism teaching `declared_bounds` to reach Foundation would build a
cross-domain capability for a function already on its way to the test suite.
The shipped document's own comment on the `bounds` block says its purpose is
letting the contract "notice that a declared cause would take the tank past
its capacity" - which is the bound walk, the kernel that was living in the
validation layer, and the thing (h) and (j) removed.

**What is lost, priced.** Nothing can notice the shipped document's 300 L
delivery overfilling a 500 L tank from the document alone any more. That was
never a projection: knowing the tank holds 254 L at offset 2400 requires
composing the declared causes, which is a kernel. So this is (h) being
applied, not a regression introduced here.
`BOUND_CASES["fuel-tank-capacity"]` is a policy rather than a number and
survives untouched; T021's kernel applies it against the frozen capacity, so
the document correction T021 owes still has something to check against.

**What is gained, and it is not nothing.** A capacity that cannot be found
used to leave a document-level bound that might not match the site. It now
blocks the run: a binding that cannot locate the Foundation rating produces
`INITIAL_VALUE_NOT_RESOLVED`, a `READY` run may not carry an absent value, and
every absent value must be named by a blocking reason for the same state. A
silent `(0.0, None)` in a retiring validator is replaced by a run that will
not claim to be ready.

**The test, and why the cheap fix is worse than it looks.**
`test_the_declared_bound_is_declared_rather_than_guessed` proves the bound is
declared rather than inferred from two state keys sharing a prefix: it removes
the `bounds` block and watches the upper bound vanish. After option B **both
halves of that test return `(0.0, None)`**. Weakening the assertion to match
does not merely lose a number - it leaves a test whose control and whose case
are identical, passing while proving nothing. That is the failure T019 met
three times and named: an assertion that holds against a value the product
cannot make proves nothing about the product.

So the property is re-proved where the distinction still exists, and it exists
in two places, neither of them retiring. The **relationship** is in the parsed
document and in the scenario-detail payload, which publishes
`bounds: {state_key, bound_kind}` and never a number - so removing the `bounds`
block is still an observable change and still a real control. The **value** is
in the frozen identity, where run setup resolves 500 L from MG-001's Foundation
and names `SITE_FOUNDATION` as the answerer. The test splits along the same
seam the decision does, and the 500.0 keeps a home.

**A rider that sharpens an existing open question.** After option B,
`declared_bounds("fuel-tank-volume")` returns `(0.0, None)` where the `0.0` is
`IMPLICIT_LOWER_BOUND_DIMENSIONS` - so the function's entire answer for that
state becomes the validation layer's own injected model rule, with the
document supplying neither number. Open Question 11 had a destination and no
slice; it now has a second reason and a sharper statement of itself.

Reason: the question looked like "where does the bound come from now" and the
answer is that it comes from where it always should have: a document says
which state caps which, and a site says how big the tank is. The only thing
that made the old arrangement look coherent was a validator composing the two,
which is the component this sequence has spent three decisions removing.

Affected scope: `backend/assetops_backend/scenarios/execution.py`
`declared_bounds` and its float filter,
`backend/tests/test_scenario_execution_contract.py`'s bound test and wherever
the 500 L assertion lands in `backend/tests/test_run_setup.py`,
`config/scenarios/fuel-loss-event.yaml`'s `tank-capacity` `bounds` block and
the parser rule that must keep accepting it without a value, T020A's criterion
for the bound, T021's kernel reading the capacity from the frozen identity,
and Open Question 11.
