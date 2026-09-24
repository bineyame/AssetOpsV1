# Architecture

## Source And Implementation Status

Simulator direction is normative in `Docs/simulator_design_v4.md`; demo
sequencing is in `Docs/mini-grid-demo-architecture-and-roadmap.md`.
This file records the protected seams and points to those mechanics, not their
full implementation specification. `.ai/CODE_STATE.md` records what is built.

2026-09-24 correction: component addressing is immediate work after the typed
property carrier, not a late electrical extension. The controller/electrical
world precedes the dispatch Finding. The evidence loop is an internal demo;
full Replay is not a gate on the first Finding. This supersedes the prior
feature-map sequencing, not the built history. See
`D-2026-09-24-v4-roadmap-replan`.

## Durable Boundaries

Simulator does not equal product.

Private simulator truth must not leak into product evidence.

AssetOps should consume site and device evidence, not simulator internals.

Scenario labels must not become site identity.

Domain truth, published evidence, analytics, and presentation should remain
explicitly separated.

External and data contracts should remain strict at boundaries.

Dependency direction should be deliberate and testable.

Demo shortcuts must not silently redefine product semantics.

## Initial Shape

Start with the smallest skeleton required to support vertical slices. Let
product behavior drive architecture rather than pre-designing for hypothetical
scale.

M1 stack:

- Python/FastAPI backend.
- React/TypeScript frontend.
- Python deterministic simulator.
- Modular monolith.
- Strict source/API parsers at boundaries.
- File-backed repositories and artifacts where sufficient for the slice.
- Single-host container deployment.
- CI-enforced architecture guards for protected seams.

Do not add Kubernetes, microservices, Kafka, service mesh, complex distributed
storage, or dedicated time-series infrastructure unless a reviewed slice proves
the need. Technology choices are implementation posture, not product semantics.

Expected direction:

simulated world -> devices/gateway observations -> ingestion -> AssetOps ->
evidence/analytics -> user-visible product

## Evidence Loop Boundaries

The internal architecture demo proves this evidence loop:

simulated runtime -> staged Source Envelopes -> release/commit manifest ->
ingestion -> accepted/rejected records -> accepted Site history and Overview

A Source Envelope carries source identity, timing, sequencing, provenance,
transport structure, and typed record payloads. It is the boundary object
released from Simulator Lab toward AssetOps ingestion; it is not itself an
accepted product fact.

Commit or release is a Simulator Lab state transition. It seals staged Source
Envelopes and releases them to ingestion. It never writes Site history, source
health, analytics, findings, or other derived product objects directly.

Ingestion owns acceptance and rejection. `received_at` belongs to ingestion, not
to the simulator. Product evidence begins only after ingestion accepts records
into the evidence store/read model.

Operator Site views, Replay, evidence drawers, source health, and conclusions
must derive from accepted evidence, not from simulator runtime objects, private
scenario truth, or staged-but-unreleased output.

Later Replay inspects committed accepted history for a Site and time window. It is
not a rerun, not a simulator-truth view, and not a way to bypass ingestion.

Private scenario expectations and simulator truth are test-oracle or Lab-only
context. They must not cross into Source Envelopes, accepted evidence, operator
views, analytics, exports, or findings.

## Causal Runtime Authority

ScenarioDefinition authors causes, conditions, interventions and private test
expectations; the runtime computes trajectories. Frozen run inputs must
reconstruct the Site/Foundation, scenario, initialization, profiles, interval,
timestep, seed and interventions that produced an output. Generated golden
traces bind to that exact identity and kernel version; authored traces cannot
establish causality. v4 sections 2, 9-10 and 21.

Static projection reports declarations. Composing them into values at a time
is kernel work, not validation or run setup. Independent causal, boundary and
metamorphic tests establish execution behavior; schema validity alone cannot.
See `D-2026-09-21-projection-versus-composition` and
`D-2026-09-21-causal-runtime-before-golden-traces`.

The first narrow Fuel Loss kernel is a starter proof, not completion of the
credible mini-grid runtime. Its profile support disclosure expires only when
kernel conformance proves the advertised set. Documentary capability must never
silently become a claim of executed support.

## Execution Composition And Truth Barrier

v4 section 3 supplies the target composition, still unbuilt after T020:

- `simulator/` owns kernel, packs, observation transforms and gateway.
- `backend/` owns product ingestion, Evidence, Findings and financials.
- Neither imports the other's package. In particular, simulator imports no
  `assetops_backend` module, including a convenient shared data type.
- A neutral `host/` composition leaf wires an execution port/adapter and may
  import both; nothing imports host. Move the minimum shared execution and
  envelope schemas to dependency-neutral contracts.
- Lab receives a gated `LabProjection`, which may expose private generated
  observations. `WorldState`, raw `DeviceObservation`, `ControlIntent`,
  `AcceptedFlowSet`, traces and private expectations are never product input.

Only canonical source envelopes cross into normal ingestion. The observation
transform and gateway remain separate components. Sensor sampling/bias/dropout
affects reports; gateway buffering/outage/retry affects publication. Neither
changes the underlying world. Operational records are a separate source family
with their own missing, delayed or contradictory cases (v4 11-12).

## Addressing, Properties And Policy

`state_key` is the semantic name; `StateRef` adds SITE/COMPONENT scope and
component identity. Extend profile support, Foundation bindings, scenario
references and frozen initialization together. Unqualified component bindings
resolve only one candidate; zero or multiple candidates block.
This is immediate contract work under v4 4.2 and 24.

Foundation owns physical properties and baseline time-valid policy.
The model profile owns physical laws; the scenario owns interval causes and
dynamic initial conditions; the publication profile owns reporting behavior.
For example, specific fuel consumption in L/kWh is a generator property;
consumption = coefficient x delivered energy is a model law; dispatched output
is forcing. This corrects the former L/h/runtime example, which conflated the
asset with its operating point. See `D-2026-09-22-consumption-coefficient-unit`.

Keep `ControlAssumption` documentary. Typed component control properties use
the property carrier; typed site-scoped Controls land with the controller that
uses them. Scenarios may change policy at a time, but do not own the baseline.
Run-start SOC, fuel level, physical discrete state and accumulated stress resolve
from explicit scenario/initial-condition inputs. Unknown stress never silently
becomes zero. v4 sections 5.2 and 10.

Preserve both the lexical control-vocabulary guard and its semantic purpose.
Physical state, causes and operator records may be named truthfully; synonyms
for switching-position or controller-mode enums remain deferred until an
explicit topology/evidence contract admits them (v4 5.1).

## Timing And Physical Acceptance

v4 section 6 replaces the old ambiguous "observe after the step" direction:

At T, apply due events/configuration changes, then sample post-event stock and
discrete state. Interval/rate measurements describe [T-dt,T), not the coming
step; the first boundary has none unless initial historical input is declared.
Then build the controller's local view, emit intent, resolve physically accepted
flows, evolve over [T,T+dt) and check bounds/conservation.

Controller observation is distinct from gateway-reported observation.
Controllers do not mutate the world. Only accepted flows evolve it; requested
30 kW and accepted 22 kW remain inspectably different. Use the deterministic
cascade of v4 section 7, with exact source/sink conservation. A future iterative
solver requires an explicit solver/convergence/numeric-policy revision.

Current arithmetic is versioned EXACT_RATIONAL. Authored floats may be
normalized once at the input boundary; no per-step denominator limiting.
Stochastic draws follow v4 section 9's BLAKE2b-256 canonical encoding and
domain-separated stream identity. Adding a stream cannot perturb another.
Typed discrete states declare initialization, allowed transitions, trace and
observation mapping (v4 4.3). Unsupported execution produces a typed failure,
not a silent clamp or successful partial result (v4 8 and 23).

## Interventions, Comparisons And Downstream Claims

A run-scoped intervention is persisted before execution as immutable canonical
content with a content-addressed reference. Ordered intervention-history strings
are sufficient only when they resolve that content. Foundation/scenario versions
plus these artifacts reconstruct effective policy; no extra arbitrary policy
identity field is needed (v4 5.2).

`PairedExperiment` is immutable comparison metadata outside either run's
deterministic identity. Compare resolved effective frozen inputs, excluding only
the exact declared intervention paths/artifact. Any undeclared difference is
`NOT_COMPARABLE`; removing an opaque Foundation/scenario version from a hash
does not prove comparability. A wider bundle is labelled multi-change.
This is a simulated intervention comparison, not proven real-world impact
(v4 15). The comparison history context must preserve independent histories and
prevent the two alternatives from being summed into ordinary Site operation.

Product analytics consumes accepted evidence and time-valid public configuration,
never simulator-private coefficients, truth or scenario labels. Dispatch,
fuel, stress and service conclusions expose their evidence gaps and claim
limits. BusinessContext translates bounded operational quantities downstream
of physics. No money enters the kernel and no monetary translation strengthens
the technical claim (v4 22; roadmap 3).

Interventions modify the world/configuration/reporting first. Work completion
never resolves a Finding; subsequent accepted evidence must satisfy a comparable
verification window with target and guardrails (v4 13; roadmap 3.7).

## Domain Reuse Boundary

Shared time, state, observation and gateway mechanisms do not branch on pack,
site kind or concrete component type. Mini-grid rules live behind the pack
boundary. Cold-chain and e-mobility remain architecture tests, not current
implementation tasks; a generic plugin framework is deferred. v4 16-19 and 28;
roadmap 8 and 10.

## Contract Posture

Data crossing product boundaries should be explicit, validated, and testable.
When evidence is missing or invalid, the product should expose an unavailable or
invalid state rather than inventing a value.

Simulator Lab is gated by `simulator_lab.enabled`. When disabled, simulator
routes, navigation, entry points, execution actions, and truth overlays are not
served. Existing simulated Sites, SIMULATED provenance, accepted evidence,
operator routes, analytics, and Replay remain available because they are product
history, not simulator execution.

## Refusal And Blocking Vocabularies

Setup refusal, persisted BLOCKED and execution failure are distinct outcomes;
comparison can independently fail as NOT_COMPARABLE. Names and ownership must
make their phase and meaning clear (v4 23). The current setup line is implemented
in `backend/assetops_backend/runs/refusals.py`.

The built code still permits a Foundation/scenario value contradiction.
The immediate Foundation-value narrowing removes that duplicate value position
and retires `INITIAL_VALUE_ANSWERS_DISAGREE`; all failures to locate a
Foundation-owned value then block. This is planned, not already implemented.
See `D-2026-09-21-run-setup-outcome-vocabulary`,
`D-2026-09-22-foundation-value-declaration` and
`D-2026-09-22-foundation-property-absent-blocks`.

The former extended naming examples are cut here; their rationale remains in
those decisions. Honest existing names do not require another redesign before
the demo under `D-2026-09-22-milestone-speed-over-purity`.

## Shells And Navigation

Simulator Lab exists to unblock product development before a real site exists.
That purpose is why it is self-contained and gated, and it is also the limit on
what being self-contained may mean: the Lab is a place to work, not a second
product. Its navigation exists only to serve that purpose and is not a second
product information architecture.

The product has two shells with separate navigation: the operator shell and the
Simulator Lab developer workspace. Simulator Lab is not an operator navigation
item; it is reached from workspace-level chrome. Operator navigation is
structurally identical in both gate states.

Simulator authoring and execution surfaces belong to the Lab shell and are
gated. Where a surface's shell is ambiguous, it ships in the Lab shell behind
the gate, because moving a surface out from behind the gate later is cheap and
retrofitting a gate around a shipped ungated surface is not.

**The gate covers surfaces and execution, never objects or stores.** A Site the
Lab produces is a normal Site: same identity space, same model, same repository,
same index, carrying simulated source mode as provenance. It is not a Lab-owned
object, it lives in no Lab-owned store, and it is never published or promoted
into the product, because it was a product object from the moment it was
created. It stays fully visible when the Lab is disabled.

A navigation destination appears only when the route behind it renders a
truthful surface. No placeholder destinations, no disabled navigation items, no
routes that exist to be filled in later.

## Shared Presentation Substrate

Where both shells present the same object, they present it from one substrate.
The operator Site page and the Lab Site page are one presentation core with
shell-specific additions, not two implementations that happen to agree.

The substrate owns the read model, the view model that turns a record into
display, and the presentation components. Neither shell may fork any of the
three. Vocabulary, unavailable and empty states, identity and provenance
rendering, and field derivation all live in the substrate and nowhere else.

Each shell may only compose and add: the Lab adds run and execution context, the
operator adds a way into the Lab. Additions attach through named extension slots
the substrate declares. The substrate never imports what fills a slot.

The substrate carries no shell, mode, or variant discriminant. A branch inside
the shared core is a fork with extra steps, and its branches drift
independently. If a difference cannot be expressed as an addition around the
core, it is not a shell difference and belongs in the substrate for both.

Dependency direction: the substrate is a leaf. It depends on the domain read
model and shared UI primitives only. It must not import shell code, simulator
code, or the feature flag. Each shell imports the substrate; neither shell
imports the other. This is what keeps the operator shell free of simulator
imports while both render the same Site.

Crossings from the operator shell into the Lab, such as an Open in Simulator Lab
action, go through the existing single gated entry-point module, not through the
substrate and not through a new chokepoint.

## Presentation Honesty

A screen adopts a layout only for content the product can source. Design
references are authoritative about information architecture, never about
capability inventory, status vocabulary, or navigation; a value, timestamp,
status, or label never appears on a screen because a reference shows it there.

Three treatments, never blurred:

- Not rendered at all: a gated capability, or one the product has decided not to
  have. Absence is the honest signal, because a disabled control reads as soon.
- Labelled in place: a canonical tab that names a real aspect of an entity but
  has no content contract yet.
- Disabled with an explicit reason: a built capability that is not currently
  eligible.

The test for an action control is whether the feature map can name the causal
step that makes it true. If it can, disable it and name that prerequisite. If
the answer is a decision to defer, do not render it.

A status may be weaker than its name. Where it is, the record and the screen
say what the status does not assert, and the disclosure is a property of the
status rather than a note on a screen, so it travels wherever the status
travels.

Anything that exists only because a condition holds names the condition as its
expiry, never a slice number, because a slice number is a guess about when the
condition closes and a guess written down is read later as a commitment. What
happens when the condition closes depends on whether the thing has become
false. A claim that has become false goes in the same slice that falsifies it;
leaving it is not caution, it is shipping a false statement. A thing that is
still honest but no longer needed goes when someone decides to remove it,
which is the case the three treatments already cover.

## Configuration Persistence

Persisted configuration is reached through a port defined by the product domain.
Storage technology lives in an adapter, and exactly one composition root chooses
which adapter is used. Port signatures and port errors speak domain records; a
path, file handle, serialization format, or store-specific exception in a port
signature means the store is not actually replaceable.

Shipped canonical configuration and user-authored configuration are separate
stores. Shipped configuration is read-only at runtime and lives outside the
writable store. Identity is globally unique across both stores; there is no
overlay and no precedence, because an identity that resolves differently
depending on store state cannot anchor downstream history.

Configuration templates are instantiated by copy, with the template identity and
version recorded as provenance on the instance. A template identity never
becomes an instance identity, and a later template change never alters an
already-created instance.

User-authored configuration is untrusted input. It crosses the same strict
parser as shipped configuration with no lenient path, the fully materialized
document is validated before anything is written, and writes are atomic so a
failed write leaves the store unchanged.

## Change Rule

Add durable architecture rules only when a current slice requires them or when
repeated task experience shows the rule is worth preserving.
