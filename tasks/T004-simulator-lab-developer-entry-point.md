# T004 - Simulator Lab Developer Entry Point

Status: in_review
USER_REVIEW_REQUIRED: true

Intended branch: `task/T004-simulator-lab-developer-entry-point`

## Feature

Stack, Shell, And Gate.

## UI-Verifiable Screen Behavior

When `simulator_lab.enabled` is true, a developer can open the empty Simulator
Lab shell from a workspace-level or utility entry point outside the operator
route navigation. Operator navigation remains unchanged in both flag states.
When the flag is false, no Simulator Lab route, workspace entry point, operator
entry point, execution action, or truth overlay is reachable.

## Why This Is Next

T003 implemented and verified the serving-boundary feature gate, but user
review compared the enabled entry point with the v6.9 product document and
identified a shell hierarchy correction: Simulator Lab is a separate developer
workspace, not an operator navigation item.

This is the smallest follow-up before Site Foundation work because later Site,
Replay, and Simulator Lab bridges should attach to the correct shell boundary.
It preserves the T003 gate while aligning the visible entry point with the
documented workspace model.

## Acceptance Criteria

- With `simulator_lab.enabled=false`, the UI exposes no Simulator Lab workspace
  entry point, operator navigation entry, route content, run action, truth
  overlay, or simulator hint.
- With `simulator_lab.enabled=true`, the operator route navigation remains the
  same as the disabled state and does not include Simulator Lab.
- With `simulator_lab.enabled=true`, a workspace-level or utility entry point
  outside operator navigation links to the Simulator Lab.
- Following the enabled workspace entry point renders the empty Simulator Lab
  shell outside the operator route layout.
- The empty Simulator Lab shell makes clear that it is a developer/simulator
  workspace surface, not an operator product page, while still exposing no run
  execution, run setup, truth overlay, gateway staging, ingestion, analytics,
  Replay, Site schema, Findings, or product conclusions.
- Direct Simulator Lab URLs and API paths remain governed by the existing T003
  route/API boundary tests in both flag states.
- Tests assert that the enabled entry point is outside the operator navigation
  landmark or operator route list, so this cannot regress into an operator
  left-nav item.

## Required Product And Domain Semantics

- Simulator Lab is a gated developer workspace surface. It may own simulator
  world, truth, execution, staging, and publication surfaces only when enabled.
- Operator routes, operator navigation, product Site history, simulated
  provenance, accepted evidence, analytics, and Replay remain separate from
  simulator execution gating.
- `Open in Simulator Lab` bridges from product screens are deferred until a
  real Site/run/provenance context exists. This task adds only the global
  developer access path needed for the empty gated shell.

## Protected Seams

- Simulator feature gate: CI guard.
  `simulator_lab.enabled=false` must mean simulator routes, workspace entry
  points, operator entry points, execution APIs, and truth overlays are not
  served while operator routes still work.
- Operator shell versus Simulator Lab workspace: UI test.
  Simulator Lab access must not appear as an operator route navigation item.
  The enabled entry point belongs to a workspace/utility boundary outside the
  operator route list.
- Simulator/product boundary: CI guard.
  Simulator Lab owns world/truth/execution/staging; AssetOps owns evidence,
  analytics, findings, and operator presentation.
- Stack and module direction: CI guard.
  The correction must preserve modular roots and avoid UI-to-simulator imports
  or simulator-to-product writes.

## Focused Tests And Checks

- UI routing/navigation test with `simulator_lab.enabled=false` for no
  workspace entry point, no operator entry point, unreachable direct Simulator
  Lab routes, and working operator routes.
- UI routing/navigation test with `simulator_lab.enabled=true` proving:
  operator navigation labels are unchanged, the workspace/utility entry point
  appears outside operator navigation, and following it opens the empty
  Simulator Lab shell.
- UI test that the enabled Simulator Lab shell still exposes no run start,
  inspect, rerun, truth comparison, staging, ingestion, analytics, Replay, or
  Findings controls.
- Backend gate tests from T003 continue to pass unchanged.
- Architecture/import check for simulator/product boundary.
- Run `tools/check-agent-workflow.ps1`.

## Scope Limits

- Do not add Site schema, Site fixtures, Site Foundation, simulator execution,
  run setup, recorded playback, gateway staging, ingestion, analytics, Replay,
  source health, configuration editing, or Findings.
- Do not add contextual `Open in Simulator Lab` product bridges yet; those need
  real Site/run/provenance context from later slices.
- Do not implement the full Simulator Lab navigation set beyond what is needed
  to establish the separate empty workspace shell. Stub labels are acceptable
  only if they are inert, clearly unavailable, and covered by tests that no
  run/truth/product behavior exists.
- Do not weaken T003's route/API boundary tests or the carried-forward
  "replace, never loosen" instruction for fabricated-value assertions.

## User Review

User review is required because this task resolves the T003 checkpoint
redirection: whether the shell hierarchy and enabled/disabled Simulator Lab
surface match the v6.9 workspace model. After this task is accepted, planning
may proceed to Site Foundation slices unless the user redirects again.
