# Product

## Purpose

AssetOps helps operators use simulator and site operations screens to inspect
distributed energy site evidence, understand site operating state, and
investigate evidence-backed operational findings.

## Target Users

Initial users are operators, asset managers, and technical reviewers responsible
for understanding mini-grid site performance and reliability.

## Current Demo Wedge

The first demo wedge should be planned from the canonical screens in
`Docs/UI Design/Motivation`, especially `SimulatorLab1.png` and
`ScreenMockups.png`. The sequence should follow causal product dependencies:
site information, components, devices, configured single-line diagrams, and
related setup must exist before Simulator Lab can truthfully show those details.

Initial implementation slices should make these screens incrementally real, with
backend work tied to behavior the user can verify in the UI. The Architect must
create the feature map and task sequence before Implementer work begins.

## Product Principles

- User-visible claims must be backed by evidence.
- Missing evidence should be explicit, not silently fabricated.
- Demo behavior should teach product and architecture assumptions quickly.
- Product slices should be inspectable by the user in the UI after each
  meaningful step.
- The system should explain what is known, what is inferred, and what is
  unavailable.

## Evidence Philosophy

AssetOps should present site and device observations as product evidence.
Private simulator truth may support testing and evaluation, but it must not
become product-visible evidence.

## Current Milestone

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.
