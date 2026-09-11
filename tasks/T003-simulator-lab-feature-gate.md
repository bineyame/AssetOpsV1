# T003 - Simulator Lab Feature Gate

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T003-simulator-lab-feature-gate`

## Feature

Stack, Shell, And Gate.

## UI-Verifiable Screen Behavior

`simulator_lab.enabled` controls Simulator Lab routes, navigation, entry
points, execution actions, and truth overlays at serving boundaries. With the
flag off, operator routes still work and Simulator Lab URLs/entry points are
unreachable. With the flag on, the empty Simulator Lab shell can be reached.

## Why This Is Next

This is Causal Sequencing step 2 and completes the first review-bounded
feature. Once simulator routes exist, gating must be enforced immediately so
truth and execution surfaces are not left reachable by direct URL or API calls.

## Acceptance Criteria

- Configuration includes `simulator_lab.enabled` with tested enabled and
  disabled behavior.
- With the flag disabled, Simulator Lab navigation and entry points are absent
  from the UI.
- With the flag disabled, direct Simulator Lab routes and execution-related API
  paths return a served-unavailable/not-found state.
- With the flag disabled, operator routes from T002 still render.
- With the flag enabled, an empty Simulator Lab shell route renders without run
  execution, truth overlays, ingestion, analytics, or Findings.
- The UI makes runs unavailable when disabled: runs cannot be started,
  inspected, rerun, or compared to truth.
- The gate is enforced at route/API serving boundaries, not only hidden in
  navigation.

## Required Product And Domain Semantics

- Simulator Lab gating controls simulator surfaces and execution only.
- Existing or future product Site history, simulated provenance, accepted
  evidence, operator routes, analytics, and Replay must remain separate from
  simulator execution gating.
- Simulator truth overlays are not product evidence and must not be reachable
  when the gate is disabled.

## Protected Seams

- Simulator feature gate: CI guard.
  `simulator_lab.enabled=false` must mean simulator routes, entry points,
  execution APIs, and truth overlays are not served while operator routes still
  work.
- Simulator/product boundary: CI guard.
  Simulator Lab owns world/truth/execution/staging; AssetOps owns evidence,
  analytics, findings, and operator presentation.
- Stack and module direction: CI guard.
  Gate implementation must preserve modular roots and avoid UI-to-simulator
  imports or simulator-to-product writes.

## Focused Tests And Checks

- Route/API/navigation test with `simulator_lab.enabled=false` for absent
  navigation, unreachable direct routes, unreachable execution APIs, and working
  operator routes.
- Route/API/navigation test with `simulator_lab.enabled=true` for reachable
  empty Simulator Lab shell.
- UI test that disabled mode exposes no run start, inspect, rerun, truth
  comparison, or execution action.
- Architecture/import check for simulator/product boundary.
- Run `tools/check-agent-workflow.ps1`.

## Scope Limits

- Do not add Site schema, simulator execution, run setup, recorded playback,
  gateway staging, ingestion, analytics, Replay, source health, configuration
  editing, or Findings.
- With the flag off, the UI has no simulator entry points and direct routes
  return unavailable/not-found.
- With the flag on, the Simulator Lab shell is empty and explicitly has no run
  behavior yet.

## User Review

User review is required because this completes the first checkpoint named by the
Architect: shell information hierarchy and enabled/disabled Simulator Lab
surface. Planning stops here until the user approves or redirects this product
direction and UI/UX expectation.
