# Product

## Purpose

AssetOps helps operators use simulator and site operations screens to inspect
distributed energy site evidence, understand site operating state, and
investigate evidence-backed operational findings.

## Target Users

Initial users are operators, asset managers, and technical reviewers responsible
for understanding mini-grid site performance and reliability.

## Current Product Walkthrough Wedge

The first product walkthrough wedge should be planned from the canonical
screens in `Docs/UI Design/Motivation`, especially `SimulatorLab1.png` and
`ScreenMockups.png`. The sequence should follow causal product dependencies:
site information, components, devices, configured single-line diagrams, and
related setup must exist before Simulator Lab can truthfully show those details.

Client-demo readiness is defined separately under Demo Readiness Milestones.

Initial implementation slices should make these screens incrementally real, with
backend work tied to behavior the user can verify in the UI. The Architect must
create the feature map and task sequence before Implementer work begins.

## Demo Readiness Milestones

AssetOps distinguishes product walkthroughs from client-ready demos.

`M0: Site Foundation Fidelity` covers faithful Site Foundation screens and
configuration-only Site views. It may be shown as a prototype walkthrough
foundation, but it must not claim operational evidence, health, analytics,
Replay, or findings.

`M1A: Topology, Devices, Signals, And SLD` makes the configured physical model
real: topology, devices, signals, ratings, control assumptions, and the
configured Single Line Diagram.

`M1B: Scenario Catalog And Run Setup` makes simulation selection and setup real
against configured Site anchors.

`M1C: Prototype Walkthrough: Causal Runtime` makes Simulator Lab resemble the
canonical runtime mockscreen with run state, controls, runtime panels, timeline,
and overlays driven by a minimal deterministic causal kernel. Reproducible
golden traces may support regression and playback, but are not the authority
for world-state causality. Runtime truth is still simulator behavior, not
AssetOps product evidence.

`Demo Ready v1: Simulated Evidence Loop` is the earliest honest client-ready
mini-grid demo. The product can show a simulated Site producing staged
gateway/source envelopes, releasing them through ingestion, accepted/rejected
ingestion logs, operator evidence views populated from accepted evidence only,
provenance inspection, and Replay over committed accepted history.

`Demo Ready v2: Evidence-Backed Operational Findings` adds source/gateway
health, evidence readiness, bounded assessments, and at least one operational
Finding with confidence, claim boundary, and evidence basis.

`Demo Ready v2.5: Cold-Chain Evidence Loop` applies the same evidence loop to a
real cold-chain domain model, after the mini-grid conclusion chain rather than
before it. Every commercially meaningful finish line is on the mini-grid path,
and a second vertical proves that the operating model transfers rather than
proving the proposition itself - so it follows the first Finding instead of
delaying it. Cold-chain is not a label swap over mini-grid; it needs cold room
assets, temperature sensors, compressor/refrigeration state, door events, power
dependency, temperature excursions, and careful exposure/risk language.

## Product Principles

- User-visible claims must be backed by evidence.
- Missing evidence should be explicit, not silently fabricated.
- Demo behavior should teach product and architecture assumptions quickly.
- Product slices should be inspectable by the user in the UI after each
  meaningful step.
- The system should explain what is known, what is inferred, and what is
  unavailable.

## Prohibited Demo Claims

Before accepted evidence exists, do not claim source health, operational status,
charts, `Last analysed` timestamps, Replay history, analytics, findings, asset
condition, recommendations, fuel variance, spoilage risk, or business impact.

Before the conclusion chain exists, do not claim generator runtime assessment,
fuel reconciliation, theft, compressor failure, spoilage, asset degradation, or
operational recommendations.

Private simulator truth may appear inside Simulator Lab for development and
testing context, but it must not be presented as AssetOps product evidence.

## Evidence Philosophy

AssetOps should present site and device observations as product evidence.
Private simulator truth may support testing and evaluation, but it must not
become product-visible evidence.

## Current Milestone

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.
