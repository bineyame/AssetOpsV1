# Architecture

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

The client-demo evidence loop follows this direction:

simulated runtime -> staged Source Envelopes -> release/commit manifest ->
ingestion -> accepted/rejected evidence -> operator evidence views -> Replay
and conclusions

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

Replay inspects committed accepted history for a Site and time window. It is
not a rerun, not a simulator-truth view, and not a way to bypass ingestion.

Private scenario expectations and simulator truth are test-oracle or Lab-only
context. They must not cross into Source Envelopes, accepted evidence, operator
views, analytics, exports, or findings.

## Causal Runtime Authority

`ScenarioDefinition` authors time-bound causes, external conditions,
interventions, and evidence conditions. It does not author the resulting world
state trajectory. Site Foundation supplies physical/configuration facts; a
frozen `SimulationRun` supplies interval, timestep, seed, selected Site and
Foundation version, selected scenario version, simulator version, resolved
initialization inputs, and ordered run-scoped interventions. The runtime owns
initialization and the causal transition from one private world state to the
next.

The first executable Fuel Loss path therefore requires a minimal deterministic
causal kernel before any trace may be treated as simulator output. Its runtime
contract must express initialization plus a step operation over current state,
simulation time, timestep, and events due in that step. Event-boundary
semantics must make each authored cause apply exactly once. The kernel may be
deliberately narrow, but changing or removing a supported cause must change or
remove its consequence while all unrelated frozen inputs remain fixed.

A manually authored state trace can prove UI, clock, binding, and downstream
contract behaviour; it cannot prove that a scenario caused the states it
contains. Golden traces are permitted only as reproducible outputs of a named
causal runtime version and frozen deterministic identity. They are regression
or playback artifacts, not an independent source of simulator truth. Schema
validation proves shape, invariant validation proves internal consistency, and
causal correctness requires execution by the kernel plus independent example,
boundary, and metamorphic tests. These three claims must not be collapsed.

Initial conditions must be explicit and attributable. They may come from Site
Foundation, versioned simulator initialization rules, or declared supported
scenario/run inputs; a trace may not hide or invent them. Runtime provenance
binds outputs to the exact Site/Foundation version, scenario version, resolved
public parameters, interval, timestep, seed, simulator version, initialization
inputs, and intervention history that produced them.

Projecting a document is static validation. Composing projections into a
value-at-a-time is a kernel. A component that owns a transition rule is a
kernel regardless of what it is called, how narrow it is, or whether it emits a
trajectory. Reporting what a document declares is always allowed; deciding what
those declarations reach is not, until the thing that owns transition rules
exists. This is the same rule as the golden-trace rule with one word changed: a
kernel precedes any authoritative trace, and a kernel precedes any verdict that
depends on composing causes.

The author's side of that line is the same rule seen from the other end. An
expectation is legitimate when it occupies a position where being wrong causes
a failure, and circular when it occupies a position where being wrong causes
agreement. An authored value the system reads as fact is load-bearing; the same
value compared against an independently computed one is an oracle. A scenario
may carry oracles and may not carry consequences.

## Physical Property Ownership

Four owners, and two swap tests that decide between them.

Site Foundation declares what the site *is*. The model profile declares how the
simulator *reasons* about things of that kind. The scenario declares what
*happens* during one interval. The publication profile declares how the
reporting installation *behaves*.

Swap the asset for another of the same type and the value changes: Foundation.
Swap the scenario and it changes: scenario. Neither, but a better simulator
would change it: model profile. Neither, ever: a universal constant, and it
belongs in code.

A coefficient and the law that consumes it are different objects with different
owners, and a name that covers both hides the seam. *This generator burns
14 L/h at its dispatch point* is Foundation. *Consumption is proportional to
runtime* is a model rule. *The generator ran from this offset for this long* is
the scenario. A physical property of a machine that lives in a scenario means
the story has replaced the asset, and the same scenario run against a different
machine would carry the first machine's physics with it.

Declaring an owner is not the same as being able to carry its value. A
vocabulary of owners with no field for one of them produces a correct answerer
and no answer. Where an owner is declarable, something must be able to hold
what it declares and something must be able to address it.

The coefficient a product uses to form an expectation comes from Foundation
configuration, never from the scenario's private rate. A product that reads the
number the simulator used computes its conclusion from the cause and gets the
right answer for the wrong reason.

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

Where a request can be refused outright or persisted in a state that says it
must not proceed, the two outcomes have disjoint vocabularies of kinds. The
line between them is stated once, in
`backend/assetops_backend/runs/refusals.py`, and is not restated here. What is
stated here is the rule the names follow, so the line survives the vocabulary
growing.

**A kind's name must make its side derivable without reading a docstring.** A
kind string reaches a client, a log and a screen with no comment attached, so
whatever tells a reader which side it is on has to be in the name itself. Two
things can carry that, and which one applies depends on the subject.

- **Across different subjects, the subject carries it, and a shared verb is
  not a collision.** `COMPONENT_OR_SIGNAL_UNRESOLVED` refuses while
  `INITIAL_VALUE_NOT_RESOLVED` blocks. An observation source the Foundation
  does not configure and an initial world value the selected profile could not
  locate are different things with different fixes, and a reader who reads the
  subject is not misled. Reserving words to one side would have cost a good
  name and prevented neither collision this rule comes from.
- **Within one subject, the shape must carry it, and shape means what the
  frozen record can hold.** `INITIAL_VALUE_NOT_RESOLVED` and
  `INITIAL_VALUE_ANSWERS_DISAGREE` share a subject, so the difference between
  them has to be legible from the names: no answer is something the record can
  represent as absent, so the request freezes and blocks; two answers is
  something the record has no shape for, so nothing can be frozen and it
  refuses. Names that differ by degree rather than by shape do not satisfy
  this.

The review question, for any kind added later: **from the name alone, which
side of the line is it on?** If answering it needs the docstring, the name is
wrong. A test asserting the two sets of strings are disjoint is the mechanical
half and does not catch this.

The rule is recorded because the experience repeated rather than because a
slice required it: one vocabulary produced two near-collisions in a single
slice, the dangerous one was caught by a reviewer and the surviving one by the
implementer, and neither was caught by anything durable. See
`D-2026-09-21-run-setup-outcome-vocabulary`.

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
