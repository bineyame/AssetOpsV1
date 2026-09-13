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

## Contract Posture

Data crossing product boundaries should be explicit, validated, and testable.
When evidence is missing or invalid, the product should expose an unavailable or
invalid state rather than inventing a value.

Simulator Lab is gated by `simulator_lab.enabled`. When disabled, simulator
routes, navigation, entry points, execution actions, and truth overlays are not
served. Existing simulated Sites, SIMULATED provenance, accepted evidence,
operator routes, analytics, and Replay remain available because they are product
history, not simulator execution.

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
