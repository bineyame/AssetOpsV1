# Planning Guidance

## Purpose

Before implementation tasks are defined, the Architect should create a feature
map for the first AssetOps product sequence. The feature map should explain how
visible UI capabilities depend on product, domain, data, and architecture
capabilities.

Do not start by listing implementation tasks. Start by understanding the screens
and the causal prerequisites that make them truthful.

## Source Material

Use these UI references as the initial planning anchor:

- `Docs/UI Design/Motivation/SimulatorLab1.png`
- `Docs/UI Design/Motivation/ScreenMockups.png`
- `Docs/Product/AssetOps_Integrated_Product_Experience_and_Canonical_Screens_v6_9.pdf`

## Architect Hats

The Architect may wear these hats as needed:

- Product: define what user-visible capability each feature provides.
- Architecture: identify durable boundaries, contracts, and dependency
  direction.
- UI/UX: identify screen flows, information hierarchy, and user-verifiable
  states.
- Domain: identify site, component, device, simulator, gateway, evidence, and
  operational semantics.

These are hats for analysis, not separate standing roles.

## Core Planning Principle

Plan features in causal order.

If a screen displays a fact, state, or diagram, identify what must exist before
that display can be meaningful. Then decide whether that prerequisite should be
its own UI-verifiable slice or part of a larger slice.

For example, the Simulator Lab screen shows site information, a single-line
diagram, devices and sensors, gateway output, events, run state, and simulation
controls. Those features imply earlier or parallel capabilities:

- Sites must be managed before a simulator run can target a site.
- Site components must be configured before a single-line diagram can be shown.
- Devices and sensors must be defined before device tables or gateway output can
  be meaningful.
- Scenario and event definitions must exist before scheduled events or injected
  events can be shown.
- Simulator run state must remain separate from product evidence until an
  observation is published through a boundary.
- Site Details can show operational evidence only after the evidence contract
  exists.

## Feature Versus Task

A feature is a complete product function or capability that a user can recognize
across one or more screens. A feature may require several tasks before it is
complete.

A task is a reviewable implementation slice that delivers or materially advances
one UI-verifiable part of a feature. A task should be small enough to implement
and review independently, but it does not need to complete the whole feature.

Feature examples:

- Site management and configuration.
- Simulator Lab run setup and execution.
- Device and sensor management.
- Gateway publishing and ingestion visibility.
- Evidence-backed operational findings.

Task examples:

- Add basic site identity and parameters to the Site Configuration screen.
- Show configured site components in the single-line diagram area.
- Let Simulator Lab select a configured site for a run.
- Publish one simulator observation into Site Details.
- Show one finding with supporting evidence.

Do not use tasks as the first planning object. Start with features and their
causal prerequisites, then break each feature into tasks only when the feature
sequence is understood.

## Feature Map Output

The Architect's first output should be a concise feature map, not a task list.
It should include:

- Feature areas visible in the canonical screens.
- Causal prerequisites for each feature area.
- Candidate tasks under each feature, only after the feature boundary and
  dependencies are clear.
- Product/domain semantics that must be decided before implementation.
- Architecture seams and contracts that must be protected.
- UI-verifiable outcomes that could become vertical slices.
- Open questions that should be resolved before task breakdown.

## From Feature Map To Tasks

After the feature map is reviewed, the Architect or Implementer may break
features into tasks. Each task should:

- Produce or heavily contribute to a UI-verifiable outcome.
- Identify the feature it contributes to.
- Name the screen behavior it enables.
- Include only the minimum backend, domain, data, UI, and tests needed for that
  outcome.
- Preserve simulator/product/evidence boundaries.
- Mark user-review checkpoints where product direction, UI/UX, domain
  semantics, or evidence interpretation changes.

Do not treat later capabilities as out of scope for the product. Treat them as
sequenced features whose prerequisites must be made real in the right order.
