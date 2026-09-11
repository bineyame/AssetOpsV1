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

## Change Rule

Add durable architecture rules only when a current slice requires them or when
repeated task experience shows the rule is worth preserving.
