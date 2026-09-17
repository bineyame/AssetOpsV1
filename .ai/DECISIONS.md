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
